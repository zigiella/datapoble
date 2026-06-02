"""CI gate: the whole eval set must pass offline.

Wraps ``evals/run_evals.py`` so the contract's own ``sample_questions`` (and the
guardrail cases) are exercised on every push. Each case is a parametrized test
so a failure names the exact case.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_EVALS = Path(__file__).resolve().parents[1] / "evals"
if str(_EVALS) not in sys.path:
    sys.path.insert(0, str(_EVALS))

from run_evals import check_case, load_cases  # noqa: E402

CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_eval_case(agent, case):
    result = check_case(agent, case)
    assert result.passed, "; ".join(result.failures)


def test_all_sample_questions_from_contract_covered():
    """Every sample_question in metrics.yml must appear as an eval case."""
    import yaml

    from datapoble_ai.catalog import default_metrics_path

    with open(default_metrics_path(), encoding="utf-8") as fh:
        contract = yaml.safe_load(fh)
    sample = contract.get("sample_questions", {})
    contract_qs = {q for qs in sample.values() for q in qs}
    eval_qs = {c["question"] for c in CASES}
    missing = contract_qs - eval_qs
    assert not missing, f"sample_questions not covered by evals: {missing}"
