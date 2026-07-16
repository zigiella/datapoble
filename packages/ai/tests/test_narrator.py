"""The generative layer (X1 / contract C5) — gated, caged, and always floored.

Every test here is offline: the redactor and the blind validator are scripted
stand-ins, so no test needs a key or a network. The property under test is that
**the deterministic answer is the floor** — whatever goes wrong, the reader gets
the traceable answer rather than an uncertified one.
"""

from __future__ import annotations

import json

import pytest

from datapoble_ai import Agent, SpendGuard
from datapoble_ai.narrator import Narrator, ScriptedBackend

OK = '{"compleix": true, "problemes": [], "motiu": "correcte"}'


def _fail(problemes):
    return json.dumps({"compleix": False, "problemes": problemes,
                       "motiu": "test"}, ensure_ascii=False)


def _narrator(catalog, redactor: list[str], validator: list[str],
              spend_guard=None):
    return Narrator(
        catalog,
        redactor_backend=ScriptedBackend(redactor),
        validator_backend=ScriptedBackend(validator),
        spend_guard=spend_guard,
    )


def _agent(catalog, narrator) -> Agent:
    return Agent(mode="offline", use_fixtures=True, narrator=narrator)


# --- politics.py rules over the generative layer (C5 §4) ----------------------


def test_no_generative_answer_about_a_vote_metric(catalog, monkeypatch):
    """The gate holds *before* any model is asked to write about a vote.

    The unlock opens the deterministic answer; it never opens a model's prose
    about how a municipality voted. `politics.py` is untouched and wins.
    """
    monkeypatch.setenv("AI_POLITICS_UNLOCK", "obrelaporta")
    redactor = ScriptedBackend(["ACCIO: RESPONDRE\nprosa que no s'ha d'escriure"])
    validator = ScriptedBackend([OK])
    narrator = Narrator(catalog, redactor_backend=redactor,
                        validator_backend=validator)
    with Agent(mode="offline", use_fixtures=True, narrator=narrator) as a:
        ans = a.ask("Quin municipi té més vot independentista? obrelaporta",
                    locale="ca")

    # The unlock worked (the deterministic answer exists)...
    assert ans.is_answer
    assert ans.metric_key == "pct_indep"
    # ...but nothing generative was produced, and no model was even called.
    assert ans.narration["status"] == "fallback_political_gate"
    assert redactor.calls == [], "a model was asked to write about a vote"
    assert validator.calls == []


def test_political_gate_still_refuses_without_the_unlock(catalog):
    """The ordinary path: a vote question is refused, and refusals are not dressed."""
    narrator = _narrator(catalog, [], [])
    with _agent(catalog, narrator) as a:
        ans = a.ask("Quin municipi té més vot independentista?", locale="ca")
    assert ans.is_refusal
    assert ans.refusal_reason.value == "political_gated"
    assert ans.narration["status"] == "fallback_refusal"


def test_the_gate_reads_the_second_metric_of_a_correlation(catalog):
    """A correlation cites only metric A in `metric_key`; a vote metric could ride
    in as B. The gate must read both — asserted directly, so it cannot pass by
    the router happening to match something else.
    """
    from datapoble_ai.types import Answer, AnswerKind

    narrator = _narrator(catalog, [], [])
    sneaky = Answer(
        kind=AnswerKind.ANSWER, locale="ca", question="q", backend="offline",
        text="…", metric_key="hab_noprincipal", metric_b_key="pct_indep",
    )
    allowed, why = narrator.can_narrate(sneaky)
    assert allowed is False
    assert why == "fallback_political_gate"


def test_a_non_political_correlation_is_narratable(catalog):
    """The converse, so the test above is not passing for a trivial reason."""
    from datapoble_ai.types import Answer, AnswerKind

    narrator = _narrator(catalog, [], [])
    ordinary = Answer(
        kind=AnswerKind.ANSWER, locale="ca", question="q", backend="offline",
        text="…", metric_key="hab_noprincipal", metric_b_key="hab_principal",
    )
    assert narrator.can_narrate(ordinary)[0] is True


# --- a refusal is never dressed up -------------------------------------------


def test_a_refusal_is_never_narrated(catalog):
    narrator = _narrator(catalog, [], [])
    with _agent(catalog, narrator) as a:
        ans = a.ask("Quin és el PIB de Berga?", locale="ca")
    assert ans.is_refusal
    assert ans.narration["status"] == "fallback_refusal"


# --- the happy path -----------------------------------------------------------


def test_a_certified_narration_is_served_with_its_provenance(catalog):
    narrator = _narrator(
        catalog,
        ["ACCIO: RESPONDRE\nA Castellar de n'Hug, 205 dels habitatges no són principals."],
        [OK],
    )
    with _agent(catalog, narrator) as a:
        ans = a.ask("Quants habitatges no principals té Castellar de n'Hug?",
                    locale="ca")
    assert ans.narration["status"] == "clean"
    assert "205 dels habitatges" in ans.text
    # The prose is the model's; the provenance tail is ours, always.
    assert "Font:" in ans.text and "Fórmula:" in ans.text
    assert ans.provenance is not None


def test_the_redactor_never_sees_our_deterministic_prose(catalog):
    """The model gets cells, not our sentences — as in the experiment."""
    redactor = ScriptedBackend(["ACCIO: RESPONDRE\n205 habitatges."])
    narrator = Narrator(catalog, redactor_backend=redactor,
                        validator_backend=ScriptedBackend([OK]))
    with _agent(catalog, narrator) as a:
        a.ask("Quants habitatges no principals té Castellar de n'Hug?", locale="ca")
    sent = redactor.calls[0]["user"]
    assert "Font:" not in sent, "the deterministic prose leaked into the prompt"
    assert "205" in sent  # the cell did travel


# --- the floor: every failure lands on the deterministic answer ---------------


def test_a_text_that_fails_re_validation_falls_back_to_deterministic(catalog):
    """The contract's fallback, proven: uncertified prose is not served."""
    narrator = _narrator(
        catalog,
        ["ACCIO: RESPONDRE\nSón 205 habitatges, i el 99,9% del poble."],
        [_fail(["caveat_esborrat"]), _fail(["xifra_inventada"])],
    )
    with _agent(catalog, narrator) as a:
        deterministic = Agent(mode="offline", use_fixtures=True).ask(
            "Quants habitatges no principals té Castellar de n'Hug?", locale="ca")
        ans = a.ask("Quants habitatges no principals té Castellar de n'Hug?",
                    locale="ca")
    assert ans.narration["status"] == "fallback_revalidation_failed"
    assert ans.text == deterministic.text, "the deterministic floor did not hold"
    assert "99,9" not in ans.text


def test_a_malformed_redactor_output_falls_back(catalog):
    narrator = _narrator(catalog, ["no action tag here"], [])
    with _agent(catalog, narrator) as a:
        ans = a.ask("Quants habitatges no principals té Castellar de n'Hug?",
                    locale="ca")
    assert ans.narration["status"] == "fallback_format"
    assert "205" in ans.text  # the deterministic answer still served


def test_a_backend_that_explodes_falls_back(catalog):
    class Exploding:
        name = "boom"

        def complete(self, **kwargs):
            raise RuntimeError("upstream 500")

    narrator = Narrator(catalog, redactor_backend=Exploding(),
                        validator_backend=ScriptedBackend([OK]))
    with _agent(catalog, narrator) as a:
        ans = a.ask("Quants habitatges no principals té Castellar de n'Hug?",
                    locale="ca")
    assert ans.narration["status"] == "fallback_error"
    assert "205" in ans.text


# --- the budget covers the *whole* cage, or there is no narration -------------


def test_no_narration_when_the_ceiling_cannot_cover_the_full_cage(catalog):
    """C5: never serve generative without a complete cage — so never start one."""
    guard = SpendGuard(daily_usd=0.0001, monthly_usd=1.0)
    redactor = ScriptedBackend(["ACCIO: RESPONDRE\nprosa"])
    narrator = Narrator(catalog, redactor_backend=redactor,
                        validator_backend=ScriptedBackend([OK]),
                        spend_guard=guard)
    with _agent(catalog, narrator) as a:
        ans = a.ask("Quants habitatges no principals té Castellar de n'Hug?",
                    locale="ca")
    assert ans.narration["status"] == "fallback_budget_exceeded"
    assert redactor.calls == [], "we paid for a narration we could not certify"
    assert "205" in ans.text


def test_the_budget_prices_the_re_validation_call_too(catalog):
    """The extra blind read is inside the ceiling, not outside it (C5 §2)."""
    narrator = _narrator(catalog, [], [], spend_guard=SpendGuard())
    priced = narrator._narration_budget_usd()
    from datapoble_ai.pricing import estimate_call_usd

    redactor_only = estimate_call_usd(narrator.redactor_model)
    validator = estimate_call_usd(narrator.validator_model)
    assert priced == pytest.approx(redactor_only + 2 * validator)
    assert validator is not None, "the validator model must be priced, not guessed"


def test_every_call_the_cage_makes_is_recorded(catalog):
    guard = SpendGuard(daily_usd=10.0, monthly_usd=100.0)
    narrator = _narrator(
        catalog,
        ["ACCIO: RESPONDRE\nSón 205 habitatges."],
        [_fail(["caveat_esborrat"]), OK],
        spend_guard=guard,
    )
    with _agent(catalog, narrator) as a:
        a.ask("Quants habitatges no principals té Castellar de n'Hug?", locale="ca")
    # 1 redactor + 2 validator judgements (the second is the re-validation).
    assert guard.stats()["calls_day"] == 3


# --- the doctrine reaches the generative layer -------------------------------


def test_a_low_confidence_cell_reaches_the_redactor_as_soroll(catalog):
    """Castellar de n'Hug is `confianca: baixa` in the fixture (diverging signals)."""
    redactor = ScriptedBackend(["ACCIO: ABSTENIR\nNo puc afirmar la xifra."])
    narrator = Narrator(catalog, redactor_backend=redactor,
                        validator_backend=ScriptedBackend([OK]))
    with _agent(catalog, narrator) as a:
        a.ask("Quina població real estimada té Castellar de n'Hug?", locale="ca")
    sent = redactor.calls[0]["user"]
    assert '"registre":"soroll"' in sent.replace(", ", ",")
    assert "caveat_obligat" in sent


def test_an_official_cell_reaches_the_redactor_as_oficial(catalog):
    redactor = ScriptedBackend(["ACCIO: RESPONDRE\n17.160 habitants."])
    narrator = Narrator(catalog, redactor_backend=redactor,
                        validator_backend=ScriptedBackend([OK]))
    with _agent(catalog, narrator) as a:
        a.ask("Quina població té Berga?", locale="ca")
    assert '"registre":"oficial"' in redactor.calls[0]["user"].replace(", ", ",")


def test_without_a_narrator_the_agent_is_unchanged(agent):
    """The generative layer is opt-in; the default path never narrates."""
    ans = agent.ask("Quants habitatges no principals té Castellar de n'Hug?",
                    locale="ca")
    assert ans.narration is None
    assert "205" in ans.text
