"""B3 gate — the /pregunta-li example chips must RESOLVE, never refuse.

The chips are the shop window of the chat: a chip that leads to a refusal
frustrates, and a chip that answers the wrong metric lies. This suite reads
the REAL chip copy from the web's i18n catalogs (`packages/web/messages/`),
so the text users click is exactly the text graded here — if anyone rewrites
a chip into a question the router cannot resolve, this goes red.

Every chip is an OFFICIAL KPI of the government board
(docs/ajuntaments/gorra-alcalde-pobla.md §3) — no parked inference (gap/IETR
left the chips with the #256 aparcaments. `index_envelliment`, KPI 1, stays
`status: planned` in the contract, so it cannot be a chip yet).

The honest refusal is a FEATURE and must keep working for free-form
questions outside the catalog — graded here too, as the chips' counterpart.
"""

from __future__ import annotations

import json

import pytest

from datapoble_ai.catalog import default_metrics_path
from datapoble_ai.types import AnswerKind, RefusalReason

# packages/web/messages/{locale}.json, resolved from the repo root (the same
# root the catalog loader walks to; keeps the test worktree/CI agnostic).
_MESSAGES_DIR = default_metrics_path().parents[1] / "packages" / "web" / "messages"

# Chip i18n key -> contract metric the answer must cite. Mirrors
# `cannedExamples` in packages/web/src/routes/pregunta-li/+page.svelte.
CHIP_METRICS: dict[str, str] = {
    "pl_ex_poblacio": "poblacio",              # KPI 2 · padró
    "pl_ex_noprincipal": "pct_noprincipal",    # KPI 5 · % habitatge no principal
    "pl_ex_rtc": "rtc_total",                  # KPI 6 · turisme reglat (RTC)
    "pl_ex_atur": "atur_registrat",            # KPI 8 · atur mensual (el pols)
    "pl_ex_renda": "renda_neta_persona",       # KPI 9 · renda neta per persona
    "pl_ex_residus": "kg_hab_any",             # KPI 12 · residus per habitant
}

LOCALES = ("ca", "es")


def _chip_text(locale: str, key: str) -> str:
    path = _MESSAGES_DIR / f"{locale}.json"
    with open(path, encoding="utf-8") as fh:
        messages = json.load(fh)
    assert key in messages, f"chip key {key!r} missing from {path.name}"
    return messages[key]


@pytest.mark.parametrize("key,metric", CHIP_METRICS.items())
@pytest.mark.parametrize("locale", LOCALES)
def test_chip_resolves_to_its_official_kpi(agent, locale, key, metric):
    question = _chip_text(locale, key)
    ans = agent.ask(question, locale=locale)
    assert ans.kind == AnswerKind.ANSWER, (
        f"chip {key!r} ({locale}) must answer, got refusal "
        f"({ans.refusal_reason}): {question!r}"
    )
    assert ans.metric_key == metric, (
        f"chip {key!r} ({locale}) cited {ans.metric_key!r}, "
        f"expected the official KPI {metric!r}"
    )
    # Every chip answer carries the project's core promise: provenance.
    assert ans.provenance is not None
    assert ans.provenance.source
    assert ans.provenance.query


@pytest.mark.parametrize(
    "locale,question",
    [
        ("ca", "Quina és l'esperança de vida a la Pobla de Lillet?"),
        ("es", "¿Cuál es la esperanza de vida en la Pobla de Lillet?"),
    ],
)
def test_free_question_outside_catalog_still_refuses_honestly(
    agent, locale, question
):
    """The chips' counterpart: out-of-catalog questions keep the honest no."""
    ans = agent.ask(question, locale=locale)
    assert ans.kind == AnswerKind.REFUSAL
    assert ans.refusal_reason == RefusalReason.OUT_OF_CATALOG


def test_no_chip_cites_a_parked_inference():
    """Chips are official KPIs only: no gap/IETR/pernocta family (#256)."""
    parked_prefixes = ("gap_", "IETR", "poblacio_pernocta", "poblacio_real",
                       "carrega_", "index_turisme")
    for key, metric in CHIP_METRICS.items():
        assert not metric.startswith(parked_prefixes), (
            f"chip {key!r} cites {metric!r}, a parked inference"
        )
