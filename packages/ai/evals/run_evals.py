"""Eval runner — executes the offline agent against ``cases.yml``.

This is the anti-regression gate (also wired into CI via
``tests/test_evals.py``). It runs entirely **offline / deterministic**, so it
needs no OpenRouter key. Each case asserts the shape of a correct answer:
answer-vs-refusal, the cited metric, the municipality in the rows, required
substrings, and — crucially — that **every answer carries provenance** and
every refusal carries a machine-readable reason.

Usage::

    python packages/ai/evals/run_evals.py            # human report, exit code = pass/fail
    python packages/ai/evals/run_evals.py --json     # machine-readable summary
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Make the package importable when run as a script (no install needed).
_PKG_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from datapoble_ai import Agent  # noqa: E402
from datapoble_ai.types import AnswerKind  # noqa: E402

CASES_PATH = Path(__file__).resolve().parent / "cases.yml"


@dataclass
class CaseResult:
    id: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    answer_text: str = ""
    backend: str = ""


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["cases"]


def check_case(agent: Agent, case: dict) -> CaseResult:
    """Run one case and collect every assertion failure (not just the first)."""
    failures: list[str] = []
    ans = agent.ask(case["question"], locale=case.get("locale"))

    expect = case["expect"]
    if expect == "answer":
        if ans.kind != AnswerKind.ANSWER:
            failures.append(
                f"expected answer, got refusal ({ans.refusal_reason}): {ans.text!r}"
            )
        else:
            # Provenance is mandatory on every answer (the project's core rule).
            if ans.provenance is None:
                failures.append("answer is missing provenance")
            else:
                for fld in ("source", "formula", "query"):
                    if not getattr(ans.provenance, fld):
                        failures.append(f"provenance.{fld} is empty")
            if "metric" in case and ans.metric_key != case["metric"]:
                failures.append(
                    f"expected metric {case['metric']!r}, cited {ans.metric_key!r}"
                )
            if "municipality" in case:
                names = {r.get("municipi") for r in ans.data}
                if case["municipality"] not in names:
                    failures.append(
                        f"expected municipality {case['municipality']!r} "
                        f"in rows, got {sorted(n for n in names if n)}"
                    )
    elif expect == "refusal":
        if ans.kind != AnswerKind.REFUSAL:
            failures.append(f"expected refusal, got answer: {ans.text!r}")
        elif "reason" in case and (
            ans.refusal_reason is None
            or ans.refusal_reason.value != case["reason"]
        ):
            failures.append(
                f"expected refusal reason {case['reason']!r}, "
                f"got {ans.refusal_reason}"
            )
    else:
        failures.append(f"unknown expect value: {expect!r}")

    for needle in case.get("contains", []):
        if needle not in ans.text:
            failures.append(f"answer text missing substring {needle!r}")

    return CaseResult(
        id=case["id"], passed=not failures, failures=failures,
        answer_text=ans.text, backend=ans.backend,
    )


def run(cases: list[dict] | None = None) -> list[CaseResult]:
    cases = cases if cases is not None else load_cases()
    # Force offline (no key / no network) AND pin the seed fixtures, so the gate
    # is deterministic and decoupled from whichever marts are on disk: it grades
    # the router logic against a known distribution, not the live data.
    with Agent(mode="offline", use_fixtures=True) as agent:
        return [check_case(agent, c) for c in cases]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Brúixola evals (offline).")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results = run()
    passed = sum(r.passed for r in results)
    total = len(results)

    if args.json:
        print(json.dumps(
            {
                "passed": passed, "total": total,
                "results": [
                    {"id": r.id, "passed": r.passed, "failures": r.failures}
                    for r in results
                ],
            },
            ensure_ascii=False, indent=2,
        ))
    else:
        for r in results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"[{mark}] {r.id} ({r.backend})")
            if not r.passed:
                for f in r.failures:
                    print(f"        - {f}")
        print(f"\n{passed}/{total} passed.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
