"""Fase 2 avaluació — TORCH-FREE. Corre el banc de distingibilitat.

El banc (data/fase2-bank.json) no necessita vectors de consulta: la comparació és per
banda i la modulació per σ és sobre un municipi. Puntuació segons el contracte
(04-fase2-distingibilitat.md):

  - compare_separated       : PASS si compare() ordena (distinguishable=True) amb l'ordre esperat.
  - compare_overlap         : PASS si compare() s'ABSTÉ (distinguishable=False, sense guanyador).
  - sigma_small             : PASS si answer() dona el to esperat ('ferm').
  - sigma_large             : PASS si answer() dona el to esperat ('prudent').
  - exact_collision_limit   : PASS si compare() s'absté (distinguishable=False) — la col·lisió
                              exacta resolta per la MATEIXA regla, a distància zero.

La línia d'abstenció-d'ordenar compta quants casos de bandes no distingibles (overlap +
col·lisió exacta) s'han reportat correctament com a no ordenables — el KPI d'abstenció de
la Fase 3, un nivell avall.
"""

from __future__ import annotations

import json
from pathlib import Path

from .build import build
from .compare import answer, compare

_PKG_ROOT = Path(__file__).resolve().parents[2]  # packages/geo-rag
BANK_PATH = _PKG_ROOT / "data" / "fase2-bank.json"

_ABSTAIN_KINDS = {"compare_overlap", "exact_collision_limit"}
_COMPARE_KINDS = {"compare_separated", "compare_overlap", "exact_collision_limit"}


def load_bank(path: Path | None = None) -> list[dict]:
    p = path or BANK_PATH
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _score_entry(conn, entry: dict) -> tuple[bool, str, dict]:
    """Return (passed, reason, detail) for one bank entry."""
    kind = entry["kind"]
    exp = entry["expected"]

    if kind in _COMPARE_KINDS:
        a, b = entry["munis"][0], entry["munis"][1]
        res = compare(conn, a, b)
        if exp["distinguishable"]:
            if not res["distinguishable"]:
                return False, "hauria d'ordenar-los però s'ha abstingut", res
            if res["higher"] != exp["higher"] or res["lower"] != exp["lower"]:
                return False, f"ordre erroni: higher={res['higher']} lower={res['lower']}", res
            return True, "ordena amb l'ordre esperat", res
        # abstention expected
        if res["distinguishable"]:
            return False, "guanyador inventat sobre bandes solapades", res
        return True, "s'absté d'ordenar (bandes solapades / col·lisió)", res

    if kind in ("sigma_small", "sigma_large"):
        res = answer(conn, entry["munis"][0])
        if res.get("tone") != exp["tone"]:
            return False, f"to={res.get('tone')!r}, esperat {exp['tone']!r}", res
        return True, f"to {res['tone']!r} reflecteix σ", res

    return False, f"kind desconegut {kind!r}", {}


def run(bank_path: Path | None = None) -> dict:
    conn = build(None)
    bank = load_bank(bank_path)

    n_pass = 0
    n_abstain = 0
    n_abstained_ok = 0
    lines: list[str] = []

    lines.append("=" * 78)
    lines.append("FASE 2 · avaluació de la distingibilitat (torch-free; comparació per banda)")
    lines.append("=" * 78)

    for e in bank:
        passed, reason, detail = _score_entry(conn, e)
        n_pass += int(passed)
        if e["kind"] in _ABSTAIN_KINDS:
            n_abstain += 1
            if isinstance(detail, dict) and detail.get("distinguishable") is False:
                n_abstained_ok += 1

        status = "PASS" if passed else "FAIL"
        lines.append("")
        lines.append(f"[{status}] {e['id']}  ({e['kind']})")
        lines.append(f"    nota banc : {e.get('note', '')}")
        if e["kind"] in _COMPARE_KINDS:
            lines.append(
                f"    resultat  : distingibles={detail.get('distinguishable')} "
                f"higher={detail.get('higher')} lower={detail.get('lower')}"
            )
            lines.append(f"    missatge  : {detail.get('note', '')}")
        else:
            lines.append(
                f"    resultat  : to={detail.get('tone')} "
                f"s_score={detail.get('s_score'):.1f} banda={detail.get('band')}"
            )
            lines.append(f"    missatge  : {detail.get('text', '')}")
        lines.append(f"    veredicte : {reason}")

    n = len(bank)
    lines.append("")
    lines.append("-" * 78)
    lines.append(f"SUMMARY: {n_pass}/{n} pass, {n - n_pass}/{n} fail")
    lines.append(
        f"ABSTENTION-OF-ORDERING: {n_abstained_ok}/{n_abstain} casos de bandes no "
        f"distingibles (overlap + col·lisió exacta) reportats correctament com a no "
        f"ordenables — el KPI d'abstenció de la Fase 3, un nivell avall."
    )
    lines.append("-" * 78)

    report = "\n".join(lines)
    conn.close()
    return {
        "report": report,
        "n_pass": n_pass,
        "n_fail": n - n_pass,
        "n_total": n,
        "n_abstain": n_abstain,
        "n_abstained_ok": n_abstained_ok,
    }


def main() -> None:
    out = run()
    report = out["report"]
    try:
        print(report)
    except UnicodeEncodeError:
        # Windows consoles default to cp1252; fall back to ASCII-safe output so the
        # summary is always readable (the report content itself is UTF-8 throughout).
        import sys

        sys.stdout.buffer.write(report.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
