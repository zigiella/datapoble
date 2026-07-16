"""CI gate: the end-to-end narration eval must pass offline (X1 · C5 §5).

Wraps ``evals/run_narration_eval.py`` so the whole chain — deterministic answer,
redactor, cage, re-validation, fallback — is exercised on every push, with the
model pinned to fixtures. Each case is a parametrized test so a failure names it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_EVALS = Path(__file__).resolve().parents[1] / "evals"
if str(_EVALS) not in sys.path:
    sys.path.insert(0, str(_EVALS))

from run_narration_eval import check_case, load_cases  # noqa: E402

CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_narration_case(case):
    result = check_case(case)
    assert result.passed, "; ".join(result.failures)


def test_the_eval_covers_the_fallback():
    """A cage eval without a provoked failure would be marking its own homework."""
    statuses = {c["expect"] for c in CASES}
    assert "fallback_revalidation_failed" in statuses, (
        "no case proves the deterministic fallback"
    )
    assert {"clean", "caged_revalidated"} <= statuses
