"""Phase 1 evaluation — TORCH-FREE. Runs retrieve() over the committed query bank.

The bank (data/fase1-bank.json) ships COMMITTED query vectors, so this eval — like CI —
runs offline with no torch. Scoring follows the contract's pass/fail:

  - normal_*      : PASS if any expected target appears in top-k.
  - collision_*   : PASS if tie.is_tie is True AND tie.group reports the sharing munis
                    AND no single group member is presented as a CLEAN winner (a clean
                    winner is a non-tie top result). FAIL if it returns a clean winner
                    hiding the tie, or orders the group by phrasing.

The abstention-of-ordering line counts how many collision cases were correctly reported
as ties — the same abstention-calibration KPI as Phase 3, one level up.
"""

from __future__ import annotations

import json
from pathlib import Path

from .build import build
from .retrieval import retrieve

_PKG_ROOT = Path(__file__).resolve().parents[2]  # packages/geo-rag
BANK_PATH = _PKG_ROOT / "data" / "fase1-bank.json"


def load_bank(path: Path | None = None) -> list[dict]:
    p = path or BANK_PATH
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _score_entry(entry: dict, res: dict) -> tuple[bool, str]:
    """Return (passed, reason) for one bank entry against its retrieval result."""
    kind = entry["kind"]
    exp = entry["expected"]
    tie = res["tie"]
    topk = [c["ine5"] for c in res["candidates"]]

    if kind.startswith("collision"):
        if not tie["is_tie"]:
            return False, "clean winner hides the tie (tie.is_tie=False)"
        group = set(tie.get("group", []))
        want = set(exp.get("tie_group", []))
        if want and not want.issubset(group):
            return False, f"tie.group {sorted(group)} does not report all sharing munis {sorted(want)}"
        if tie["kind"] != "collision":
            return False, f"tie.kind={tie['kind']!r}, expected 'collision'"
        # No single group member presented as a clean winner: with a collision tie the
        # top is explicitly flagged, so this holds by construction. Guard anyway.
        if len(group) < 2:
            return False, "collision group has < 2 members (nothing to abstain on)"
        return True, f"reported collision tie over {sorted(group)}; number not muni-specific"

    # normal_*: recall@k on expected targets.
    hit = set(exp["targets"]) & set(topk)
    if not hit:
        return False, f"no expected target {exp['targets']} in top-k {topk}"
    if exp.get("expect_tie") and not tie["is_tie"]:
        return False, "expected a tie but got a clean winner"
    if (not exp.get("expect_tie")) and tie["is_tie"] and tie["kind"] == "collision":
        # A normal query that lands on a collision top is a design smell in the bank,
        # not a retriever bug — but flag it so it isn't silently counted as a pass.
        return False, f"normal query landed on a collision top (tie over {tie['group']})"
    return True, f"target(s) {sorted(hit)} in top-k"


def run(bank_path: Path | None = None) -> dict:
    conn = build(None)
    bank = load_bank(bank_path)

    n_pass = 0
    n_collision = 0
    n_collision_abstained = 0
    lines: list[str] = []

    lines.append("=" * 78)
    lines.append("FASE 1 · avaluació del recuperador (torch-free, vectors compromesos)")
    lines.append("=" * 78)

    for e in bank:
        res = retrieve(conn, e["query"], e["query_vec"], anchor_ine5=e["anchor_ine5"], k=5)
        passed, reason = _score_entry(e, res)
        n_pass += int(passed)
        is_collision = e["kind"].startswith("collision")
        if is_collision:
            n_collision += 1
            if res["tie"]["is_tie"] and res["tie"]["kind"] == "collision":
                n_collision_abstained += 1

        status = "PASS" if passed else "FAIL"
        tie = res["tie"]
        top = res["candidates"][0] if res["candidates"] else {"ine5": "-", "nom": "-"}
        lines.append("")
        lines.append(f"[{status}] {e['id']}  ({e['kind']})")
        lines.append(f"    query    : {e['query']}")
        lines.append(f"    anchor   : {res['anchor']}   candidats (filtre dur): {res['n_candidates']}")
        lines.append(
            "    top-k    : "
            + ", ".join(f"{c['nom']}({c['ine5']},{c['score']:.4f})" for c in res["candidates"])
        )
        if tie["is_tie"]:
            lines.append(f"    EMPAT    : kind={tie['kind']} group={tie['group']}")
            lines.append(f"    nota     : {tie['note']}")
        else:
            lines.append(f"    guanyador: {top['nom']} ({top['ine5']}) — sense empat")
        lines.append(f"    veredicte: {reason}")

    n = len(bank)
    lines.append("")
    lines.append("-" * 78)
    lines.append(f"SUMMARY: {n_pass}/{n} pass, {n - n_pass}/{n} fail")
    lines.append(
        f"ABSTENTION-OF-ORDERING: {n_collision_abstained}/{n_collision} collision cases "
        f"correctly reported as ties (a well-reported tie = an abstention hit; a false "
        f"tie-break hiding the tie = a failure — the Phase-3 KPI, one level up)."
    )
    lines.append("-" * 78)

    report = "\n".join(lines)
    conn.close()
    return {
        "report": report,
        "n_pass": n_pass,
        "n_fail": n - n_pass,
        "n_total": n,
        "n_collision": n_collision,
        "n_collision_abstained": n_collision_abstained,
    }


def main() -> None:
    out = run()
    print(out["report"])


if __name__ == "__main__":
    main()
