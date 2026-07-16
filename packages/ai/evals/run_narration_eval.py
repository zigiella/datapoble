"""End-to-end eval of the generative layer, offline (X1 · contract C5 §5).

Runs the whole chain against the seed fixtures with a **fixed** model:

    question -> Router (SQL + provenance) -> redactor -> cage
             -> RE-VALIDATION of the caged text -> served | deterministic fallback

The redactor's prose and the blind validator's verdicts come from
``narration_cases.yml``, so this is a real end-to-end run of *our* code with the
model pinned — no network, no key, deterministic. Wired into CI via
``tests/test_narration_eval.py``.

Usage::

    python packages/ai/evals/run_narration_eval.py          # human report
    python packages/ai/evals/run_narration_eval.py --json   # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_PKG_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from datapoble_ai import Agent  # noqa: E402
from datapoble_ai.catalog import load_catalog  # noqa: E402
from datapoble_ai.narrator import Narrator, ScriptedBackend  # noqa: E402

CASES_PATH = Path(__file__).resolve().parent / "narration_cases.yml"


@dataclass
class CaseResult:
    id: str
    passed: bool
    status: str = ""
    failures: list[str] = field(default_factory=list)
    text: str = ""


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["cases"]


def deterministic_text(question: str, locale: str) -> str:
    """What the reader gets when the generative layer declines — the floor."""
    with Agent(mode="offline", use_fixtures=True) as agent:
        return agent.ask(question, locale=locale).text


def check_case(case: dict) -> CaseResult:
    """Run one case end-to-end and collect every failure (not just the first)."""
    failures: list[str] = []
    catalog = load_catalog()
    narrator = Narrator(
        catalog,
        redactor_backend=ScriptedBackend([case["redactor"]]),
        validator_backend=ScriptedBackend(list(case.get("validator") or [])),
    )
    with Agent(mode="offline", use_fixtures=True, narrator=narrator) as agent:
        ans = agent.ask(case["question"], locale=case.get("locale"))

    status = (ans.narration or {}).get("status", "")
    if status != case["expect"]:
        failures.append(f"expected narration status {case['expect']!r}, got {status!r}")

    # Provenance is mandatory on every answer, narrated or not.
    if ans.is_answer and ans.provenance is None:
        failures.append("answer is missing provenance")

    for needle in case.get("contains", []):
        if needle not in ans.text:
            failures.append(f"served text missing {needle!r}")
    for needle in case.get("excludes", []):
        if needle in ans.text:
            failures.append(f"served text must not contain {needle!r}")

    if case.get("deterministic_floor"):
        floor = deterministic_text(case["question"], case.get("locale"))
        if ans.text != floor:
            failures.append(
                "fallback did not land on the deterministic answer "
                f"(got {ans.text[:70]!r})"
            )

    return CaseResult(id=case["id"], passed=not failures, status=status,
                      failures=failures, text=ans.text)


def run(cases: list[dict] | None = None) -> list[CaseResult]:
    return [check_case(c) for c in (cases if cases is not None else load_cases())]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="End-to-end eval of the caged generative layer (offline).")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    results = run()
    passed = sum(r.passed for r in results)
    total = len(results)

    if args.json:
        print(json.dumps(
            {"passed": passed, "total": total,
             "results": [{"id": r.id, "passed": r.passed, "status": r.status,
                          "failures": r.failures} for r in results]},
            ensure_ascii=False, indent=2))
    else:
        for r in results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"[{mark}] {r.id} -> {r.status}")
            for f in r.failures:
                print(f"        - {f}")
        print(f"\n{passed}/{total} passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
