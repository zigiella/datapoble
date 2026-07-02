"""Fase 3 · el KPI d'abstenció — arnès de mesura TORCH-FREE.

Corre el banc CONGELAT (data/fase3-banc.json, transcripció literal de
docs/experiment-rag-geo/07-fase3-banc.md, congelat 2026-07-02) a través del router
genèric i puntua EXACTAMENT amb la mètrica congelada al contracte
(06-fase3-kpi-abstencio.md + regla de puntuació del banc):

  - 2x2 sobre l'acció daurada: TP (daurada abstenir & el sistema s'absté),
    FN (daurada abstenir & respon) = ABSTENIR-SE DE MENYS (pecat greu),
    FP (daurada respondre & s'absté) = ABSTENIR-SE DE MÉS (pecat prudent),
    TN (daurada respondre & respon).
  - recall d'abstenció = TP/21 · precision = TP/(TP+FP) · F1 · MRR = FN/21 · FRR = FP/13.
  - coverage + selective accuracy sobre els contestables respostos (correcte NOMÉS si
    coincideix amb l'expect daurat: guanyador / llista (igualtat de conjunts d'ine5) /
    valor (la xifra daurada de l'estimació)).
  - Nivell (llindars congelats abans de córrer): honest = TP>=19 i FP<=2;
    decebedor = TP en 15..18; no funciona = TP<=14.
  - Q22/Q23/Q29 (el parell oficial) es reporten AMB NOM, passin o fallin.
  - Un crash del router és la seva pròpia categoria 'error': MISS per a la daurada que
    tingués (ni TP ni TN), reportat honestament a la taula.

HONESTEDAT: aquest mòdul no toca cap mòdul de doctrina i no codifica cap resposta del
banc — les daurades es llegeixen del JSON congelat. El número es reporta tal com surt;
el report oficial s'escriu a data/fase3-resultat.txt i es versiona com a acta.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from .build import build
from .router import route

_PKG_ROOT = Path(__file__).resolve().parents[2]  # packages/geo-rag
BANK_PATH = _PKG_ROOT / "data" / "fase3-banc.json"
RESULT_PATH = _PKG_ROOT / "data" / "fase3-resultat.txt"


def load_bank(path: Path | None = None) -> list[dict]:
    return json.loads(Path(path or BANK_PATH).read_text(encoding="utf-8"))


# --- Puntuació d'un contestable respost contra l'expect daurat ----------------------


def _content_correct(expect: dict | None, out: dict) -> bool | None:
    """True/False si hi ha expect i el sistema ha respost; None si no és avaluable."""
    if not expect:
        return None
    meta = out.get("meta", {})
    if "winner" in expect:
        return meta.get("winner") == expect["winner"]
    if "list" in expect:
        got = meta.get("ine5_list")
        return got is not None and set(got) == set(expect["list"])
    if "value" in expect:
        est = meta.get("estimacio")
        if est is not None and int(round(float(est))) == int(expect["value"]):
            return True
        return str(int(expect["value"])) in (out.get("text") or "")
    return None


# --- La mètrica congelada (funció pura, testejable en sintètic) ----------------------


def score_results(results: list[dict]) -> dict:
    """Computa la mètrica congelada sobre una llista de resultats.

    Cada resultat: {id, golden_action ('respondre'|'abstenir'),
    system_action ('respondre'|'abstenir'|'error'), content_correct (bool|None)}.
    Pura (cap accés al sistema) perquè el test la pugui verificar en sintètic.
    """
    tp = fn = fp = tn = 0
    err_abst = err_resp = 0
    answered_answerable = 0
    answered_correct = 0

    for r in results:
        g, s = r["golden_action"], r["system_action"]
        if g == "abstenir":
            if s == "abstenir":
                tp += 1
            elif s == "respondre":
                fn += 1
            else:
                err_abst += 1  # error: MISS (ni TP ni TN)
        else:  # golden respondre
            if s == "abstenir":
                fp += 1
            elif s == "respondre":
                tn += 1
                answered_answerable += 1
                if r.get("content_correct"):
                    answered_correct += 1
            else:
                err_resp += 1

    n_abst = sum(1 for r in results if r["golden_action"] == "abstenir")
    n_resp = len(results) - n_abst

    recall = Fraction(tp, n_abst) if n_abst else None
    precision = Fraction(tp, tp + fp) if (tp + fp) else None
    f1 = None
    if recall is not None and precision is not None and (recall + precision) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    mrr = Fraction(fn, n_abst) if n_abst else None  # abstenir-se de menys (pecat greu)
    frr = Fraction(fp, n_resp) if n_resp else None  # abstenir-se de més (pecat prudent)
    coverage = Fraction(answered_answerable, n_resp) if n_resp else None
    sel_acc = (
        Fraction(answered_correct, answered_answerable) if answered_answerable else None
    )

    # Nivells congelats (07-fase3-banc.md, confirmats per Bea abans de córrer).
    if tp >= 19 and fp <= 2:
        level = "HONEST"
    elif 15 <= tp <= 18:
        level = "DECEBEDOR"
    elif tp <= 14:
        level = "LA IDEA NO FUNCIONA"
    else:
        # tp >= 19 però fp > 2: recall en nivell honest, sobre-abstenció per sobre del
        # llindar — fora dels nivells definits; NO s'assoleix Honest.
        level = "RECALL HONEST PERÒ SOBRE-ABSTENCIÓ > LLINDAR (no assoleix Honest)"

    return {
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        "n_error": err_abst + err_resp,
        "n_abst_golden": n_abst, "n_resp_golden": n_resp,
        "recall": recall, "precision": precision, "f1": f1,
        "mrr": mrr, "frr": frr,
        "coverage": coverage, "selective_accuracy": sel_acc,
        "answered_answerable": answered_answerable,
        "answered_correct": answered_correct,
        "level": level,
    }


def _fmt(x: Fraction | None) -> str:
    if x is None:
        return "n/a"
    return f"{float(x):.3f}"


def _one_line(text: str, width: int = 96) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= width else t[: width - 1] + "…"


# --- L'arnès ------------------------------------------------------------------------


def run(bank_path: Path | None = None) -> dict:
    conn = build(None)
    bank = load_bank(bank_path)

    results: list[dict] = []
    rows: list[dict] = []
    for e in bank:
        golden = e["golden"]["action"]
        try:
            out = route(conn, e["query"])
            system = out["answer_action"]
            text = out["text"]
            intent = out["intent"]
            correct = (
                _content_correct(e["golden"].get("expect"), out)
                if (golden == "respondre" and system == "respondre")
                else None
            )
        except Exception as exc:  # el crash és la seva pròpia categoria
            system, text, intent, correct = "error", f"ERROR: {exc!r}", "error", None
        results.append(
            {
                "id": e["id"],
                "golden_action": golden,
                "system_action": system,
                "content_correct": correct,
            }
        )
        rows.append(
            {
                "id": e["id"], "block": e["block"], "kind": e["kind"],
                "query": e["query"], "golden": golden, "system": system,
                "intent": intent, "correct": correct, "text": text,
                "named": bool(e["golden"].get("named")),
            }
        )
    conn.close()

    m = score_results(results)

    # Veredicte per pregunta.
    for r in rows:
        if r["system"] == "error":
            r["verdict"] = "ERROR (miss)"
        elif r["golden"] == "abstenir":
            r["verdict"] = "TP (s'absté bé)" if r["system"] == "abstenir" \
                else "FN — ABSTENIR-SE DE MENYS (pecat greu)"
        else:
            if r["system"] == "abstenir":
                r["verdict"] = "FP — ABSTENIR-SE DE MÉS (pecat prudent)"
            elif r["correct"] is False:
                r["verdict"] = "TN però contingut INCORRECTE"
            else:
                r["verdict"] = "TN (respon bé)"

    lines: list[str] = []
    lines.append("=" * 98)
    lines.append(
        "FASE 3 · KPI d'abstenció — RUN OFICIAL sobre el banc congelat "
        "(07-fase3-banc.md, 2026-07-02)"
    )
    lines.append(
        "El banc no s'ha retocat; el número es reporta tal com surt "
        "(contracte 06-fase3-kpi-abstencio.md)."
    )
    lines.append("=" * 98)
    lines.append("")
    lines.append("PER PREGUNTA")
    lines.append("-" * 98)
    for r in rows:
        name = "  ** AMB NOM **" if r["named"] else ""
        lines.append(
            f"Q{r['id']:>2} [{r['block']}·{r['kind']}] daurada={r['golden']:<9} "
            f"sistema={r['system']:<9} {r['verdict']}{name}"
        )
        lines.append(f"     consulta : {r['query']}")
        lines.append(f"     intent   : {r['intent']}")
        lines.append(f"     sistema  : {_one_line(r['text'])}")
    lines.append("")
    lines.append("MATRIU 2x2 (acció daurada × acció del sistema)")
    lines.append("-" * 98)
    lines.append(f"  TP (abstenir & s'absté)               : {m['tp']}")
    lines.append(f"  FN (abstenir & respon)  = DE MENYS    : {m['fn']}   <- pecat greu")
    lines.append(f"  FP (respondre & s'absté) = DE MÉS     : {m['fp']}   <- pecat prudent")
    lines.append(f"  TN (respondre & respon)               : {m['tn']}")
    lines.append(f"  errors (crash del router, miss)       : {m['n_error']}")
    lines.append("")
    lines.append("MÈTRICA CONGELADA")
    lines.append("-" * 98)
    lines.append(
        f"  abstention recall    = TP/{m['n_abst_golden']} = {m['tp']}/{m['n_abst_golden']}"
        f" = {_fmt(m['recall'])}"
    )
    lines.append(
        f"  abstention precision = TP/(TP+FP) = {m['tp']}/{m['tp'] + m['fp']}"
        f" = {_fmt(m['precision'])}"
    )
    lines.append(f"  abstention F1        = {_fmt(m['f1'])}")
    lines.append(
        f"  MRR (de menys, greu)  = FN/{m['n_abst_golden']} = {m['fn']}/"
        f"{m['n_abst_golden']} = {_fmt(m['mrr'])}"
    )
    lines.append(
        f"  FRR (de més, prudent) = FP/{m['n_resp_golden']} = {m['fp']}/"
        f"{m['n_resp_golden']} = {_fmt(m['frr'])}"
    )
    lines.append(
        f"  coverage (contestables respostos)     = {m['answered_answerable']}/"
        f"{m['n_resp_golden']} = {_fmt(m['coverage'])}"
    )
    lines.append(
        f"  selective accuracy (respostos i bé)   = {m['answered_correct']}/"
        f"{m['answered_answerable']} = {_fmt(m['selective_accuracy'])}"
    )
    lines.append("")
    lines.append(
        "NIVELL (llindars congelats: honest = TP>=19/21 i FP<=2/13 · decebedor = TP 15–18 "
        "· no funciona = TP<=14)"
    )
    lines.append(f"  >>> {m['level']} <<<")
    lines.append("")
    lines.append("CASOS AMB NOM (el parell oficial — es reporten passin o fallin)")
    lines.append("-" * 98)
    for r in rows:
        if r["named"]:
            ok = r["system"] == "abstenir"
            lines.append(f"  Q{r['id']}: {'PASS' if ok else 'FAIL'} — {r['verdict']}")
            lines.append(f"      sistema: {_one_line(r['text'])}")
    lines.append("")
    fails = [r for r in rows if r["verdict"].startswith(("FN", "FP", "ERROR"))
             or "INCORRECTE" in r["verdict"]]
    lines.append(f"FALLS ({len(fails)})")
    lines.append("-" * 98)
    if not fails:
        lines.append("  (cap)")
    for r in fails:
        lines.append(f"  Q{r['id']} [{r['kind']}] {r['verdict']} — {_one_line(r['text'], 80)}")
    lines.append("=" * 98)

    report = "\n".join(lines)
    return {"report": report, "metrics": m, "rows": rows}


def main() -> None:
    out = run()
    report = out["report"]
    RESULT_PATH.write_text(report + "\n", encoding="utf-8")
    try:
        print(report)
    except UnicodeEncodeError:
        # Consoles Windows en cp1252: sortida UTF-8 crua perquè el report es vegi sempre.
        import sys

        sys.stdout.buffer.write(report.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")
    print(f"\n[report escrit a {RESULT_PATH}]")


if __name__ == "__main__":
    main()
