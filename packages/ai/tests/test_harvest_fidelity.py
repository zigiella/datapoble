"""The harvest is faithful, and the annex stayed frozen (X1 · contract C5).

C5 §2 pins the blind validator to **v2** and says the system prompt is not
edited: when the mart context differs, the *user* message adapts. So the prompt
this package ships must be the frozen instrument, byte for byte.

C5 §3 makes ``packages/geo-rag`` a research annex — its findings are cited, not
rewritten — so the check reads it read-only and skips if it is not on disk (the
wheel does not ship it).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from datapoble_ai.doctrine import (
    REDACTOR_PROMPT_PATH,
    VALIDATOR_PROMPT_PATH,
    load_prompt,
)

_REPO = Path(__file__).resolve().parents[3]
_FROZEN = _REPO / "packages" / "geo-rag" / "prompts" / "validador-cec-v2-CONGELAT.md"


def test_the_harvested_validator_is_the_frozen_instrument_byte_for_byte():
    if not _FROZEN.is_file():
        pytest.skip("geo-rag annex not on disk (installed wheel)")
    assert VALIDATOR_PROMPT_PATH.read_bytes() == _FROZEN.read_bytes(), (
        "the blind validator drifted from the frozen v2 instrument"
    )


def test_the_validator_prompt_is_v2_not_v1():
    """v1 had the documented unequal-comparison flaw; C5 §2 pins v2."""
    text = load_prompt(VALIDATOR_PROMPT_PATH)
    assert "v2" in text
    assert "distinguishable: true" in text
    # The v2 correction: with disjoint bands the order IS affirmable.
    assert "afirmar l'ORDRE no és aquest error" in text


def test_the_redactor_prompt_does_not_promise_fields_the_marts_lack():
    """Adapted, not copied: asking for absent fields is asking for inventions.

    The experiment's substrate had `rang_baix`/`rang_alt`/`padro`/`etca_oficial`/
    `collision_group`; the marts have none of them.
    """
    text = load_prompt(REDACTOR_PROMPT_PATH)
    body = text.split("-->", 1)[-1]  # the provenance comment may name them
    for absent in ("rang_baix", "rang_alt", "etca_oficial", "collision_group"):
        assert absent not in body, f"the redactor is told about `{absent}`, absent from the marts"


def test_the_redactor_keeps_the_doctrine_that_did_survive():
    body = load_prompt(REDACTOR_PROMPT_PATH).split("-->", 1)[-1]
    for kept in ("ACCIO: RESPONDRE", "ACCIO: ABSTENIR", "soroll", "senyal",
                 "oficial", "distinguishable", "caveat_obligat"):
        assert kept in body


def test_the_two_silences_are_still_distinguished():
    """The distinction the experiment paid for: `soroll` is not `no ho tinc`."""
    body = load_prompt(REDACTOR_PROMPT_PATH).split("-->", 1)[-1]
    assert "silenci **diferent**" in body
    # soroll: the estimate exists and is disowned with a reason...
    assert "NO és «no tinc dada»" in body
    # ...whereas out-of-catalog is the empty silence.
    assert "«no ho tinc»" in body
