"""Paràfrasis adversarials del recuperador — arnès TORCH-FREE.

Corre el joc CONGELAT de paràfrasis (data/fase3-parafrasis.json, generat mecànicament
del doc congelat docs/experiment-rag-geo/09-parafrasis-adversarials.md, 2026-07-03)
a través del MATEIX router genèric i puntua amb la MATEIXA regla congelada del banc
(score_results d'eval3). Les daurades s'HERETEN de data/fase3-banc.json per `q`
(única font de veritat: aquí no s'etiqueta res).

Extra que el doc congelat exigeix reportar (sense tocar la 2x2):
  - SILENCI EQUIVOCAT: acció-OK (s'absté quan toca) però la família del silenci no és
    l'esperada del bloc — el contracte diu que soroll («no es distingeix del marge») i
    fora-de-catàleg («no ho tinc») són DOS silencis diferents. Es classifica per l'intent
    ESTRUCTURAT del router (mai regexant la prosa pròpia):
        valor_municipi -> 'dada' · comparacio -> 'ordre' ·
        municipi_desconegut / indicador_desconegut / consulta_no_reconeguda -> 'catàleg'.
    Esperat per bloc: D,E -> dada · F -> ordre · G -> catàleg.
  - Desglossament per BLOC i per LLENGUA ([ca] 63 / [es] 5).
  - Els casos AMB NOM (parell oficial, Q22/23/29) x2 paràfrasis cadascun.

NOTA de nivells: els llindars congelats del 07 apliquen al BANC ORIGINAL (21/13). Aquí
el resultat és una SONDA D'ENDURIMENT i es reporta descriptivament, sense nivell.

HONESTEDAT: aquest ARNÈS no toca cap mòdul de doctrina ni el router EN RUNTIME (només hi
crida); el resultat es reporta tal com surt a data/fase3-parafrasis-resultat.txt (acta
versionada). Nota d'història: el ROUTER sí que va ser endurit ENTRE la run v1 i la v2
(#233, fix estructural per famílies) — l'acta viva és del router v2/v2.1 i la v1 queda
preservada a data/fase3-parafrasis-resultat-v1-router-inicial.txt. Les dues es llegeixen
juntes: la distància v1→v2 és la mesura de l'enduriment.
"""

from __future__ import annotations

import json
from pathlib import Path

from .build import build
from .eval3 import _content_correct, _fmt, _one_line, load_bank, score_results
from .router import route

_PKG_ROOT = Path(__file__).resolve().parents[2]  # packages/geo-rag
PARA_PATH = _PKG_ROOT / "data" / "fase3-parafrasis.json"
RESULT_PATH = _PKG_ROOT / "data" / "fase3-parafrasis-resultat.txt"

# Família de silenci esperada per bloc (D/E = declaració de dada; F = no-ordenable;
# G = no-ho-tinc). Els blocs contestables (A/B/C) no tenen silenci esperat.
FAMILIA_ESPERADA = {"D": "dada", "E": "dada", "F": "ordre", "G": "catàleg"}

_FAMILIA_PER_INTENT = {
    "valor_municipi": "dada",
    "comparacio": "ordre",
    "municipi_desconegut": "catàleg",
    "indicador_desconegut": "catàleg",
    "consulta_no_reconeguda": "catàleg",
}


def familia_silenci(intent: str) -> str:
    """Família del silenci observat, derivada de l'intent estructurat del router."""
    return _FAMILIA_PER_INTENT.get(intent, "altra")


def load_parafrasis(path: Path | None = None) -> list[dict]:
    return json.loads(Path(path or PARA_PATH).read_text(encoding="utf-8"))


def run(para_path: Path | None = None, bank_path: Path | None = None) -> dict:
    conn = build(None)
    bank = {e["id"]: e for e in load_bank(bank_path)}
    paras = load_parafrasis(para_path)

    results: list[dict] = []
    rows: list[dict] = []
    for p in paras:
        base = bank[p["q"]]
        golden = base["golden"]["action"]
        block = base["block"]
        try:
            out = route(conn, p["query"])
            system = out["answer_action"]
            text = out["text"]
            intent = out["intent"]
            correct = (
                _content_correct(base["golden"].get("expect"), out)
                if (golden == "respondre" and system == "respondre")
                else None
            )
        except Exception as exc:  # el crash és la seva pròpia categoria
            system, text, intent, correct = "error", f"ERROR: {exc!r}", "error", None

        esperada = FAMILIA_ESPERADA.get(block)
        observada = familia_silenci(intent) if system == "abstenir" else None
        silenci_ko = (
            system == "abstenir" and esperada is not None and observada != esperada
        )

        results.append(
            {
                "id": p["id"],
                "golden_action": golden,
                "system_action": system,
                "content_correct": correct,
            }
        )
        rows.append(
            {
                "id": p["id"], "q": p["q"], "lang": p["lang"], "block": block,
                "kind": base["kind"], "query": p["query"], "golden": golden,
                "system": system, "intent": intent, "correct": correct,
                "text": text, "named": bool(base["golden"].get("named")),
                "esperada": esperada, "observada": observada, "silenci_ko": silenci_ko,
            }
        )
    conn.close()

    m = score_results(results)

    for r in rows:
        if r["system"] == "error":
            r["verdict"] = "ERROR (miss)"
        elif r["golden"] == "abstenir":
            if r["system"] == "abstenir":
                r["verdict"] = (
                    "TP però SILENCI EQUIVOCAT"
                    f" (esperat {r['esperada']}, observat {r['observada']})"
                    if r["silenci_ko"] else "TP (s'absté bé)"
                )
            else:
                r["verdict"] = "FN — ABSTENIR-SE DE MENYS (pecat greu)"
        else:
            if r["system"] == "abstenir":
                r["verdict"] = "FP — ABSTENIR-SE DE MÉS (pecat prudent)"
            elif r["correct"] is False:
                r["verdict"] = "TN però contingut INCORRECTE"
            else:
                r["verdict"] = "TN (respon bé)"

    # Desglossaments.
    def _acc(sel: list[dict]) -> tuple[int, int]:
        ok = sum(
            1 for r in sel
            if (r["golden"] == "abstenir" and r["system"] == "abstenir")
            or (r["golden"] == "respondre" and r["system"] == "respondre"
                and r["correct"] is not False)
        )
        return ok, len(sel)

    per_block: dict[str, tuple[int, int]] = {}
    for b in "ABCDEFG":
        sel = [r for r in rows if r["block"] == b]
        if sel:
            per_block[b] = _acc(sel)
    per_lang = {lang: _acc([r for r in rows if r["lang"] == lang]) for lang in ("ca", "es")}
    silenci_kos = [r for r in rows if r["silenci_ko"]]

    lines: list[str] = []
    lines.append("=" * 98)
    lines.append(
        "PARÀFRASIS ADVERSARIALS · RUN OFICIAL del recuperador DETERMINISTA "
        "(09-parafrasis-adversarials.md, congelat 2026-07-03)"
    )
    lines.append(
        "Daurades HERETADES del banc congelat (07). Sonda d'enduriment: resultat "
        "descriptiu, tal com surt; els nivells del 07 NO apliquen aquí."
    )
    lines.append("=" * 98)
    lines.append("")
    lines.append("PER PARÀFRASI")
    lines.append("-" * 98)
    for r in rows:
        name = "  ** AMB NOM **" if r["named"] else ""
        es = " [es]" if r["lang"] == "es" else ""
        lines.append(
            f"{r['id']:>4}{es} [{r['block']}·{r['kind']}] daurada={r['golden']:<9} "
            f"sistema={r['system']:<9} {r['verdict']}{name}"
        )
        lines.append(f"     consulta : {r['query']}")
        lines.append(f"     intent   : {r['intent']}")
        lines.append(f"     sistema  : {_one_line(r['text'])}")
    lines.append("")
    lines.append("MATRIU 2x2 (acció daurada × acció del sistema) — regla congelada del 07")
    lines.append("-" * 98)
    lines.append(f"  TP (abstenir & s'absté)               : {m['tp']}")
    lines.append(f"  FN (abstenir & respon)  = DE MENYS    : {m['fn']}   <- pecat greu")
    lines.append(f"  FP (respondre & s'absté) = DE MÉS     : {m['fp']}   <- pecat prudent")
    lines.append(f"  TN (respondre & respon)               : {m['tn']}")
    lines.append(f"  errors (crash del router, miss)       : {m['n_error']}")
    lines.append("")
    lines.append("MÈTRICA (descriptiva — mateixa fórmula congelada; sense nivell aquí)")
    lines.append("-" * 98)
    lines.append(
        f"  abstention recall    = {m['tp']}/{m['n_abst_golden']} = {_fmt(m['recall'])}"
    )
    lines.append(
        f"  MRR (de menys, greu)  = {m['fn']}/{m['n_abst_golden']} = {_fmt(m['mrr'])}"
    )
    lines.append(
        f"  FRR (de més, prudent) = {m['fp']}/{m['n_resp_golden']} = {_fmt(m['frr'])}"
    )
    lines.append(
        f"  selective accuracy    = {m['answered_correct']}/{m['answered_answerable']}"
        f" = {_fmt(m['selective_accuracy'])}"
    )
    lines.append("")
    lines.append("DESGLOSSAMENT (acció-OK i contingut-OK / total)")
    lines.append("-" * 98)
    for b, (ok, n) in per_block.items():
        lines.append(f"  bloc {b}: {ok}/{n}")
    for lang, (ok, n) in per_lang.items():
        lines.append(f"  [{lang}]  : {ok}/{n}")
    lines.append("")
    lines.append(
        f"SILENCI EQUIVOCAT (acció-OK però l'altra mena de silenci) — {len(silenci_kos)}"
    )
    lines.append("-" * 98)
    if not silenci_kos:
        lines.append("  (cap)")
    for r in silenci_kos:
        lines.append(
            f"  {r['id']} [{r['block']}] esperat={r['esperada']} observat={r['observada']}"
            f" — {_one_line(r['text'], 70)}"
        )
    lines.append("")
    lines.append("CASOS AMB NOM (parell oficial — 2 paràfrasis per Q, passin o fallin)")
    lines.append("-" * 98)
    for r in rows:
        if r["named"]:
            ok = r["system"] == "abstenir" and not r["silenci_ko"]
            lines.append(f"  {r['id']}: {'PASS' if ok else 'FAIL'} — {r['verdict']}")
            lines.append(f"      sistema: {_one_line(r['text'])}")
    lines.append("")
    fails = [
        r for r in rows
        if r["verdict"].startswith(("FN", "FP", "ERROR")) or "INCORRECTE" in r["verdict"]
        or r["silenci_ko"]
    ]
    lines.append(f"FALLS + SILENCIS EQUIVOCATS ({len(fails)})")
    lines.append("-" * 98)
    if not fails:
        lines.append("  (cap)")
    for r in fails:
        lines.append(
            f"  {r['id']} [{r['kind']}] {r['verdict']} — {_one_line(r['text'], 76)}"
        )
    lines.append("=" * 98)

    report = "\n".join(lines)
    return {"report": report, "metrics": m, "rows": rows,
            "silenci_kos": len(silenci_kos), "per_block": per_block,
            "per_lang": per_lang}


def main() -> None:
    out = run()
    report = out["report"]
    RESULT_PATH.write_text(report + "\n", encoding="utf-8")
    try:
        print(report)
    except UnicodeEncodeError:
        import sys

        sys.stdout.buffer.write(report.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")
    print(f"\n[report escrit a {RESULT_PATH}]")


if __name__ == "__main__":
    main()
