"""ANNEX DE RE-VALIDACIÓ de la capa generativa — punt 2 de l'auditoria (2026-07-10).

Dues preguntes que la passada oficial v3 va deixar obertes, respostes SENSE regenerar res
(els outputs són els MATEIXOS del log cru de la passada v3; aquí només es re-VALIDEN):

(1) LA GÀBIA, VERIFICADA DE VERITAT. L'acta oficial puntua la gàbia per comptabilitat
    (doc 10): cada intervenció es CONSIDERA arreglada. Aquí el text engabiat REAL
    (reconstruït deterministament amb apply_cage sobre la prosa del log) es torna a
    passar pel validador cec → «gàbia comptable» vs «gàbia re-validada».

(2) LA DOBLE LECTURA DE L'INSTRUMENT. El validador v1 té un fall conceptual documentat
    (en comparacions amb `distinguishable: true` castiga afirmar l'ordre si un municipi
    és soroll — contradiu la regla de distingibilitat congelada de la Fase 2). El v1 no
    es toca i el seu número oficial NO es reescriu (era estricte EN CONTRA nostra). El
    validador v2 (validador-cec-v2-CONGELAT.md) corregeix NOMÉS aquest punt, i aquí es
    reporta la lectura dels mateixos outputs amb ELS DOS instruments — el quadre 2x2
    (instrument × condició) sencer, les dues lectures publicades.

HONESTEDAT DE L'ANNEX:
- Cap output nou del generador: només re-validació (Haiku, temperature=0).
- INTEGRITAT verificada abans de cap crida: l'ACCIO reconstruïda del log ha de coincidir
  trial a trial amb data/generativa-oficial-trials.jsonl (l'acta versionada), i el
  NU-v1 recomputat ha de REPRODUIR el 160/170 de l'acta oficial. Si no quadra → error.
- El resultat va a data/generativa-annex-revalidacio.txt (+ .jsonl) com a ANNEX: l'acta
  oficial v3 queda tal qual.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from .build import build
from .generativa import (
    LOGS_DIR,
    MAX_TOKENS_VALIDADOR,
    MODEL_VALIDADOR,
    PRICES,
    Budget,
    JsonlLog,
    _call_llm,
    _load_items,
    _one_line,
    apply_cage,
    content_check,
    hard_validation,
    make_client,
    parse_output,
    parse_verdict,
    score_trial,
)

_PKG_ROOT = Path(__file__).resolve().parents[2]
LOG_V3_PATH = _PKG_ROOT / "data" / "generativa-logs" / "20260704T100036Z-oficial.jsonl"
TRIALS_OFICIALS_PATH = _PKG_ROOT / "data" / "generativa-oficial-trials.jsonl"
VALIDADOR_V1_PATH = _PKG_ROOT / "prompts" / "validador-cec-v1-CONGELAT.md"
VALIDADOR_V2_PATH = _PKG_ROOT / "prompts" / "validador-cec-v2-CONGELAT.md"
ANNEX_PATH = _PKG_ROOT / "data" / "generativa-annex-revalidacio.txt"
ANNEX_TRIALS_PATH = _PKG_ROOT / "data" / "generativa-annex-revalidacio.jsonl"


def _parse_user(user: str) -> tuple[str, dict]:
    """Del `user` del log: la PREGUNTA i el CONTEXT (el json EXACTE que va veure el model)."""
    head, _, ctx_raw = user.partition("\nCONTEXT: ")
    q = head[len("PREGUNTA: "):].strip()
    return q, json.loads(ctx_raw)


def reconstruct(log_path: Path) -> list[dict]:
    """Reconstrueix els 170 trials del log cru: (id, pass, golden, q, ctx, prose, accio,
    verdict_v1_nu) — emparellant gen→val per ordre estricte i cotejant amb l'acta."""
    rows = [json.loads(x) for x in log_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    gens = [r for r in rows if r["role"] == "generador"]
    vals = [r for r in rows if r["role"] == "validador"]
    if len(gens) != len(vals):
        raise SystemExit(f"log desaparellat: {len(gens)} generador vs {len(vals)} validador")

    oficials = [json.loads(x) for x in TRIALS_OFICIALS_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]
    if len(oficials) != len(gens):
        raise SystemExit(f"acta ({len(oficials)}) i log ({len(gens)}) no quadren en nombre de trials")

    items = {f"Q{e['id'].lstrip('Q')}": e for e in _load_items("oficial")}

    trials: list[dict] = []
    for i, (g, v) in enumerate(zip(gens, vals, strict=True)):
        q, ctx = _parse_user(g["request"]["user"])
        raw = (g["response"].get("choices") or [{}])[0].get("message", {}).get("content") or ""
        accio, prose = parse_output(raw)
        verdict_nu = parse_verdict(
            (v["response"].get("choices") or [{}])[0].get("message", {}).get("content") or ""
        )
        acta = oficials[i]
        # INTEGRITAT trial a trial: l'acció reconstruïda == la de l'acta versionada.
        if accio != acta.get("accio"):
            raise SystemExit(
                f"INTEGRITAT: trial #{i} ({acta['id']} p{acta['pass']}) accio del log "
                f"«{accio}» != acta «{acta.get('accio')}» — reconstrucció invàlida."
            )
        item = items.get(acta["id"])
        if item is None or item["query"] != q:
            raise SystemExit(f"INTEGRITAT: trial #{i} pregunta del log no és la del banc ({acta['id']}).")
        trials.append(
            {
                "id": acta["id"], "pass": acta["pass"], "golden": item["golden"],
                "q": q, "ctx": ctx, "prose": prose, "accio": accio,
                "verdict_v1_nu": verdict_nu,
            }
        )
    return trials


def _vmsg(q: str, ctx: dict, text: str) -> str:
    return (
        f"PREGUNTA: {q}\n"
        f"DADES: {json.dumps(ctx, ensure_ascii=False, separators=(',', ':'))}\n"
        f"RESPOSTA: {text}"
    )


def run(log_path: Path | None = None, max_calls: int = 600, dry: bool = False) -> dict:
    log_path = Path(log_path) if log_path else LOG_V3_PATH
    trials = reconstruct(log_path)
    conn = build(None)

    # Recompute determinista + text engabiat + comprovació que el NU-v1 REPRODUEIX l'acta.
    for t in trials:
        t["violations"] = hard_validation(t["prose"], t["ctx"])
        t["content"] = content_check(conn, t["golden"], t["prose"])
        s = score_trial(t["golden"]["action"], t["accio"], t["violations"], t["verdict_v1_nu"], t["content"])
        t["naked_ok_v1"] = s["naked_ok"]
        t["caged_ok_comptable"] = s["caged_ok"]
        t["caged_text"], t["interventions"] = apply_cage(
            t["prose"], t["ctx"], t["violations"], t["verdict_v1_nu"]["problemes"]
        )
        t["action_ok"] = t["accio"] == t["golden"]["action"]
    conn.close()

    nu_v1 = sum(1 for t in trials if t["naked_ok_v1"])
    comptable = sum(1 for t in trials if t["caged_ok_comptable"])
    if nu_v1 != 160 or comptable != 170:
        raise SystemExit(
            f"INTEGRITAT: recompute NU-v1={nu_v1} (acta: 160) · gàbia comptable={comptable} "
            f"(acta: 170) — el pipeline no reprodueix l'acta oficial; s'atura sense cap crida."
        )
    print(f"[annex] integritat OK: 170 trials · NU-v1 recomputat {nu_v1}/170 · comptable {comptable}/170")
    if dry:
        return {"trials": trials, "dry": True}

    # Re-validacions: v1(gàbia) · v2(nu) · v2(gàbia) — 3 crides/trial, temperature=0.
    system_v1 = VALIDADOR_V1_PATH.read_text(encoding="utf-8")
    system_v2 = VALIDADOR_V2_PATH.read_text(encoding="utf-8")
    client = make_client()
    budget = Budget(max_calls)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log = JsonlLog(LOGS_DIR / f"{stamp}-annex.jsonl")
    tokens_in = tokens_out = 0

    def _validate(system: str, t: dict, text: str, role: str) -> dict:
        nonlocal tokens_in, tokens_out
        raw, info = _call_llm(
            client, model=MODEL_VALIDADOR, system=system, user=_vmsg(t["q"], t["ctx"], text),
            temperature=0, max_tokens=MAX_TOKENS_VALIDADOR, budget=budget, log=log, role=role,
        )
        tokens_in += info["prompt_tokens"]
        tokens_out += info["completion_tokens"]
        return parse_verdict(raw)

    try:
        for n, t in enumerate(trials, 1):
            t["verdict_v1_gabia"] = _validate(system_v1, t, t["caged_text"], "v1_gabia")
            t["verdict_v2_nu"] = _validate(system_v2, t, t["prose"], "v2_nu")
            t["verdict_v2_gabia"] = _validate(system_v2, t, t["caged_text"], "v2_gabia")
            s2 = score_trial(t["golden"]["action"], t["accio"], t["violations"], t["verdict_v2_nu"], t["content"])
            t["naked_ok_v2"] = s2["naked_ok"]
            # Gàbia RE-VALIDADA: acció + contingut + el text engabiat REAL passa el validador.
            t["caged_reval_v1"] = t["action_ok"] and t["content"] is not False and t["verdict_v1_gabia"]["compleix"]
            t["caged_reval_v2"] = t["action_ok"] and t["content"] is not False and t["verdict_v2_gabia"]["compleix"]
            if n % 17 == 0:
                print(f"[annex] {n}/170 trials re-validats ({budget.used} crides)")
    finally:
        log.close()

    cost = tokens_in / 1e6 * PRICES[MODEL_VALIDADOR][0] + tokens_out / 1e6 * PRICES[MODEL_VALIDADOR][1]

    # ——— Acta de l'annex ———
    def _count(key: str) -> int:
        return sum(1 for t in trials if t.get(key))

    compleix = {
        "v1_nu": sum(1 for t in trials if t["verdict_v1_nu"]["compleix"]),
        "v1_gabia": sum(1 for t in trials if t["verdict_v1_gabia"]["compleix"]),
        "v2_nu": sum(1 for t in trials if t["verdict_v2_nu"]["compleix"]),
        "v2_gabia": sum(1 for t in trials if t["verdict_v2_gabia"]["compleix"]),
    }
    naked_v2 = _count("naked_ok_v2")
    reval_v1 = _count("caged_reval_v1")
    reval_v2 = _count("caged_reval_v2")

    with ANNEX_TRIALS_PATH.open("w", encoding="utf-8") as f:
        for t in trials:
            f.write(json.dumps({
                "id": t["id"], "pass": t["pass"], "golden": t["golden"]["action"],
                "accio": t["accio"], "naked_ok_v1": t["naked_ok_v1"], "naked_ok_v2": t["naked_ok_v2"],
                "caged_comptable": t["caged_ok_comptable"],
                "caged_reval_v1": t["caged_reval_v1"], "caged_reval_v2": t["caged_reval_v2"],
                "interventions": len(t["interventions"]),
                "compleix": {k: t[f"verdict_{k}"]["compleix"] for k in
                             ("v1_nu", "v1_gabia", "v2_nu", "v2_gabia")},
            }, ensure_ascii=False) + "\n")

    L: list[str] = []
    L.append("=" * 98)
    L.append("ANNEX · RE-VALIDACIÓ de la passada oficial v3 (2026-07-10) — CAP output regenerat")
    L.append(f"Font: {log_path.name} (els MATEIXOS 170 outputs de l'acta oficial). Validadors: v1")
    L.append("(l'instrument oficial, intacte) i v2 (fall de la comparació desnivellada corregit,")
    L.append("validador-cec-v2-CONGELAT.md). L'acta oficial NO es reescriu: això és un annex.")
    L.append("=" * 98)
    L.append("")
    L.append("VERDICTE «compleix» DEL VALIDADOR (quadre instrument × condició, /170)")
    L.append("-" * 98)
    L.append(f"  v1 × nu     : {compleix['v1_nu']}/170   (lectura de la passada oficial)")
    L.append(f"  v1 × gàbia  : {compleix['v1_gabia']}/170")
    L.append(f"  v2 × nu     : {compleix['v2_nu']}/170")
    L.append(f"  v2 × gàbia  : {compleix['v2_gabia']}/170")
    L.append("")
    L.append("(1) LA GÀBIA, VERIFICADA (comptabilitat vs re-validació del text engabiat real)")
    L.append("-" * 98)
    L.append("  gàbia COMPTABLE (acta oficial)        : 170/170")
    L.append(f"  gàbia RE-VALIDADA amb v1 (estricte)   : {reval_v1}/170")
    L.append(f"  gàbia RE-VALIDADA amb v2 (corregit)   : {reval_v2}/170")
    L.append("  (re-validada = acció daurada ∧ contingut ∧ el text engabiat passa el validador)")
    L.append("")
    L.append("(2) LA DOBLE LECTURA DEL NU (el mateix trial-correcte, amb els dos instruments)")
    L.append("-" * 98)
    L.append(f"  NU amb v1 (oficial)  : 160/170 = {160 / 170:.3f}")
    L.append(f"  NU amb v2 (corregit) : {naked_v2}/170 = {naked_v2 / 170:.3f}")
    L.append("")
    fails_v2 = [t for t in trials if not t["naked_ok_v2"]]
    L.append(f"TRIALS QUE ENCARA FALLEN EL NU AMB v2 ({len(fails_v2)})")
    L.append("-" * 98)
    if not fails_v2:
        L.append("  (cap)")
    for t in fails_v2:
        L.append(f"  {t['id']} p{t['pass']}: {_one_line(t['verdict_v2_nu'].get('motiu', ''), 84)}")
    L.append("")
    disc = [t for t in trials if t["caged_ok_comptable"] and not t["caged_reval_v2"]]
    L.append(f"GÀBIA: COMPTAT-ARREGLAT PERÒ EL TEXT REAL NO PASSA NI EL v2 ({len(disc)})")
    L.append("-" * 98)
    if not disc:
        L.append("  (cap)")
    for t in disc:
        L.append(f"  {t['id']} p{t['pass']}: {_one_line(t['verdict_v2_gabia'].get('motiu', ''), 84)}")
    L.append("")
    L.append(f"  crides: {budget.used} · tokens {MODEL_VALIDADOR.split('/')[-1]} in={tokens_in} "
             f"out={tokens_out} · cost estimat ${cost:.4f}")
    L.append("=" * 98)
    report = "\n".join(L)
    ANNEX_PATH.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\n[annex escrit a {ANNEX_PATH} · trials a {ANNEX_TRIALS_PATH}]")
    return {"trials": trials, "compleix": compleix, "naked_v2": naked_v2,
            "reval_v1": reval_v1, "reval_v2": reval_v2, "cost": cost}


def main(argv: list[str] | None = None) -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(
        prog="datapoble_geo_rag.revalidacio",
        description="Annex de re-validació de la passada oficial v3 (cap output regenerat).",
    )
    ap.add_argument("--log", default=str(LOG_V3_PATH), help="log cru de la passada oficial v3")
    ap.add_argument("--max-calls", type=int, default=600, help="fre dur de crides d'API")
    ap.add_argument("--dry", action="store_true",
                    help="només reconstrucció + comprovacions d'integritat (0 crides)")
    args = ap.parse_args(argv)
    run(log_path=Path(args.log), max_calls=args.max_calls, dry=args.dry)


if __name__ == "__main__":
    main()
