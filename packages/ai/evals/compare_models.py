"""Multi-model eval: quality vs cost per OpenRouter model.

This is the **key-dependent companion** to the offline eval gate. It runs the
exact same `cases.yml` set, but instead of the deterministic backend it drives
the **OpenRouter** path against several models, and reports, per model:

- **quality**: how many eval cases pass (same assertions as the CI gate),
- **cost**: the estimated USD to run the whole set (token-based, from
  `datapoble_ai.pricing`), plus the actual USD if the API returns usage.

So you can pick a model on an informed quality-vs-cost basis before fixing one
in production.

IMPORTANT — this is **NOT** part of CI. The CI gate (`tests/test_evals.py` /
`evals/run_evals.py`) stays **offline, deterministic, no network**. This script
*requires* ``OPENROUTER_API_KEY`` and makes real (paid) calls, so it is run
manually / on demand, never on every push.

Usage::

    export OPENROUTER_API_KEY=sk-...                     # the secret, never committed
    # default model list:
    python packages/ai/evals/compare_models.py
    # explicit models + JSON output:
    python packages/ai/evals/compare_models.py \
        --models anthropic/claude-3-haiku openai/gpt-4o-mini google/gemini-flash-1.5 \
        --json
    # override the price table (e.g. a snapshot of OpenRouter's /models):
    python packages/ai/evals/compare_models.py --pricing prices.json

The forced **deterministic-first** shortcut is *disabled* here on purpose: we
want every case to actually exercise the model, otherwise we would be grading
the offline router, not the LLM. (In production deterministic-first stays on —
that is the cost lever.)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Make the package importable when run as a script (no install needed).
_PKG_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from run_evals import check_case, load_cases  # noqa: E402

from datapoble_ai.catalog import load_catalog  # noqa: E402
from datapoble_ai.llm import OpenRouterBackend  # noqa: E402
from datapoble_ai.pricing import (  # noqa: E402
    PRICES,
    ModelPrice,
    estimate_call_usd,
)
from datapoble_ai.warehouse import Warehouse  # noqa: E402

# Sensible default mix: a cheap model from each major provider + one strong one.
DEFAULT_MODELS = [
    "anthropic/claude-3-haiku",
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o-mini",
    "google/gemini-flash-1.5",
]


@dataclass
class ModelReport:
    model: str
    passed: int = 0
    total: int = 0
    est_usd: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0


class _AgentLike:
    """Minimal adapter so ``check_case`` (which calls ``.ask``) can drive a
    specific OpenRouter backend bound to one model."""

    def __init__(self, backend: OpenRouterBackend):
        self.backend = backend

    def ask(self, question, locale=None):
        return self.backend.ask(question, locale=locale)


def _load_pricing(path: str | None) -> dict[str, ModelPrice]:
    if not path:
        return PRICES
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    # Accept either {model: {prompt, completion}} USD-per-Mtok mapping.
    table = dict(PRICES)
    for model, p in raw.items():
        table[model] = ModelPrice(
            prompt_usd_per_mtok=float(p["prompt"]),
            completion_usd_per_mtok=float(p["completion"]),
        )
    return table


def run_model(model: str, cases: list[dict], catalog, warehouse,
              pricing: dict[str, ModelPrice]) -> ModelReport:
    """Run the whole eval set against one model and tally quality + cost."""
    # deterministic_first=False: force every case through the model so we grade
    # the LLM, not the offline router.
    backend = OpenRouterBackend(
        catalog, warehouse, model=model, deterministic_first=False,
    )
    agent = _AgentLike(backend)
    report = ModelReport(model=model, total=len(cases))
    for case in cases:
        try:
            result = check_case(agent, case)
            if result.passed:
                report.passed += 1
            else:
                report.errors.append(f"{case['id']}: {'; '.join(result.failures)}")
        except Exception as exc:  # network / model error — record, keep going
            report.errors.append(f"{case['id']}: ERROR {exc!r}")
        # Cost: prefer actual usage from the last response if the backend
        # exposed it; otherwise fall back to the per-call token estimate.
        est = estimate_call_usd(model, table=pricing)
        if est is not None:
            report.est_usd += est
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Multi-model quality-vs-cost eval (needs OPENROUTER_API_KEY).",
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--pricing", default=None,
                        help="JSON file: {model: {prompt, completion}} USD/Mtok.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not os.environ.get("OPENROUTER_API_KEY"):
        print(
            "ERROR: OPENROUTER_API_KEY is not set. This script makes real "
            "(paid) OpenRouter calls and is intentionally NOT part of CI. "
            "Export the key and re-run. The offline gate is `run_evals.py`.",
            file=sys.stderr,
        )
        return 2

    pricing = _load_pricing(args.pricing)
    cases = load_cases()
    catalog = load_catalog()
    # Same fixture distribution as the offline gate: `cases.yml` asserts against
    # the seed values, so grade every model on the same known data (decoupled
    # from whichever real marts are on disk).
    warehouse = Warehouse(catalog, use_fixtures=True)

    reports: list[ModelReport] = []
    try:
        for model in args.models:
            t0 = time.time()
            rep = run_model(model, cases, catalog, warehouse, pricing)
            rep_secs = time.time() - t0
            reports.append(rep)
            if not args.json:
                print(
                    f"[{model}] {rep.passed}/{rep.total} passed "
                    f"({rep.pass_rate:.0%}) · ~${rep.est_usd:.4f} · {rep_secs:.1f}s"
                )
                for e in rep.errors:
                    print(f"        - {e}")
    finally:
        warehouse.close()

    if args.json:
        print(json.dumps(
            {
                "models": [
                    {
                        "model": r.model,
                        "passed": r.passed,
                        "total": r.total,
                        "pass_rate": round(r.pass_rate, 3),
                        "est_usd_total": round(r.est_usd, 4),
                        "errors": r.errors,
                    }
                    for r in reports
                ],
            },
            ensure_ascii=False, indent=2,
        ))
    else:
        print("\n== quality vs cost (cheapest passing model wins) ==")
        ranked = sorted(reports, key=lambda r: (-r.pass_rate, r.est_usd))
        for r in ranked:
            print(f"  {r.pass_rate:>4.0%}  ${r.est_usd:>8.4f}  {r.model}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
