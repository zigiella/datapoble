"""The cage (X1 / contract C5) — hard validation, and the re-validation law.

The lesson this file exists to keep: the experiment's annex (#238) showed the
cage scored 170/170 by *counting* interventions and only 163/170 when the caged
text was actually re-read. So an intervention is never considered fixed — it is
re-checked, and a text that still fails is not served.

Offline throughout: the blind validator is a scripted stand-in, so the cage is
the subject under test rather than the weather.
"""

from __future__ import annotations

import pytest

from datapoble_ai.cage import (
    Cage,
    apply_cage,
    cell_values,
    hard_validation,
    number_spans,
    parse_output,
    parse_verdict,
    validator_message,
)
from datapoble_ai.narrator import ScriptedBackend

CTX = {
    "intent": "valor_municipi",
    "metrica": {"clau": "pct_noprincipal", "etiqueta": "% habitatge no principal"},
    "caveat_obligat": "Lectura ecològica: sobre el municipi, mai sobre individus.",
    "cel·les": [{"municipi": "Castellar de n'Hug", "value": 74.28,
                 "registre": "senyal"}],
}

OK = '{"compleix": true, "problemes": [], "motiu": "correcte"}'


def _verdict(problemes, compleix=False):
    import json
    return json.dumps({"compleix": compleix, "problemes": problemes,
                       "motiu": "test"}, ensure_ascii=False)


# --- the number grammar (the marts' decimals, not the experiment's integers) ---


def test_reads_catalan_decimals_as_one_figure():
    """`74,28` is one number. Read as two ints, the cage would cut its own data."""
    spans = number_spans("El valor és 74,28% i el padró 1.234.")
    assert [(v, tok) for _, _, v, tok in spans] == [(74.28, "74,28"), (1234.0, "1.234")]


def test_reads_thousands_with_decimals():
    spans = number_spans("Són 16.669,50 habitants.")
    assert [v for _, _, v, _ in spans] == [16669.5]


def test_decimal_from_the_mart_traces_and_is_not_cut():
    assert hard_validation("El valor és 74,28%.", CTX) == []


def test_rounded_forms_of_a_cell_trace():
    """A cell of 74.28 justifies 74,3 and 74 — the same figure, rounded."""
    assert hard_validation("Ronda el 74%.", CTX) == []
    assert hard_validation("Ronda el 74,3%.", CTX) == []


def test_a_figure_that_is_not_in_the_data_is_caught():
    assert hard_validation("El valor és 91,5%.", CTX) == ["91,5"]


def test_rounding_does_not_launder_a_different_number():
    """75 is not 74.28 rounded: near-misses are still inventions."""
    assert hard_validation("Ronda el 75%.", CTX) == ["75"]


def test_list_counts_trace():
    ctx = {"cel·les": [{"municipi": "A", "value": 1}, {"municipi": "B", "value": 2}]}
    assert hard_validation("Els 2 municipis.", ctx) == []


def test_booleans_are_not_figures():
    assert 1.0 not in cell_values({"distinguishable": True})


# --- parsing ------------------------------------------------------------------


def test_parse_output_reads_the_action_tag():
    assert parse_output("ACCIO: RESPONDRE\nEl valor és 74,28%.") == (
        "respondre", "El valor és 74,28%.")
    assert parse_output("ACCIO: ABSTENIR\nNo ho puc afirmar.")[0] == "abstenir"


def test_parse_output_rejects_a_missing_tag():
    assert parse_output("El valor és 74,28%.")[0] == "error_format"


def test_parse_verdict_tolerates_code_fences():
    v = parse_verdict('```json\n{"compleix": true, "problemes": [], "motiu": "ok"}\n```')
    assert v["compleix"] is True


def test_unreadable_verdict_fails_closed():
    """A validator we cannot read is not a validator that approved."""
    v = parse_verdict("the model rambled")
    assert v["compleix"] is False
    assert v["problemes"] == ["validador_illegible"]


# --- the cage's edits ---------------------------------------------------------


def test_apply_cage_cuts_the_untraceable_figure_visibly():
    caged, interventions = apply_cage("El valor és 91,5%.", CTX, ["91,5"], [])
    assert "⟦91,5: xifra no verificada⟧" in caged
    assert interventions == ["xifra_tallada(91,5)"]


def test_apply_cage_appends_the_contract_caveat_not_its_own_words():
    caged, interventions = apply_cage("El valor és 74,28%.", CTX, [],
                                      ["caveat_esborrat"])
    assert "Lectura ecològica" in caged
    assert interventions == ["postdata(caveat_esborrat)"]


def test_apply_cage_does_not_repair_a_collision_it_cannot_express():
    """The marts carry no collision groups: there is nothing truthful to append.

    Unfixable means the text goes on to fail re-validation, not that we invent a
    postscript. See `datapoble_ai.doctrine` on what did not survive the harvest.
    """
    caged, interventions = apply_cage("Text.", CTX, [], ["collisio_amagada"])
    assert interventions == []
    assert caged == "Text."


# --- the law: re-validate, or fall back ---------------------------------------


def test_clean_text_is_served_without_a_second_call():
    backend = ScriptedBackend([OK])
    cage = Cage("SYSTEM", backend)
    result = cage.run("Quant?", CTX, "El valor és 74,28%.")
    assert result.served is True
    assert result.status == "clean"
    assert len(backend.calls) == 1  # nothing was touched: no re-read needed


def test_a_caged_text_is_re_read_before_being_served():
    """The annex's lesson: counting the fix is not the same as checking it."""
    backend = ScriptedBackend([_verdict(["caveat_esborrat"]), OK])
    cage = Cage("SYSTEM", backend)
    result = cage.run("Quant?", CTX, "El valor és 74,28%.")
    assert result.served is True
    assert result.status == "caged_revalidated"
    assert len(backend.calls) == 2, "the caged text was not re-validated"
    # The second call judged the *caged* text, not the naked prose.
    assert "Lectura ecològica" in backend.calls[1]["user"]


def test_a_text_that_still_fails_after_caging_is_not_served():
    """163/170, not 170/170: the cage does not get to mark its own homework."""
    backend = ScriptedBackend([_verdict(["caveat_esborrat"]),
                               _verdict(["to_ferm_sobre_soroll"])])
    cage = Cage("SYSTEM", backend)
    result = cage.run("Quant?", CTX, "El valor és 74,28%.")
    assert result.served is False
    assert result.status == "fallback_revalidation_failed"
    assert result.text is None


def test_an_invented_figure_forces_a_re_read_even_if_the_judge_passed_it():
    """Hard validation is deterministic and does not defer to the model.

    The blind validator missed the invented figure; the cage cut it anyway, and
    that edit is what gets re-read.
    """
    backend = ScriptedBackend([OK, OK])
    cage = Cage("SYSTEM", backend)
    result = cage.run("Quant?", CTX, "El valor és 91,5%.")
    assert result.violations == ["91,5"]
    assert len(backend.calls) == 2
    assert result.served is True
    assert "⟦91,5: xifra no verificada⟧" in result.text


# --- the blind validator is blind ---------------------------------------------


def test_the_validator_sees_only_question_data_and_answer():
    """No reasoning, no generator scratchpad — that is what makes it blind."""
    msg = validator_message("Quant?", CTX, "El valor és 74,28%.")
    assert msg.startswith("PREGUNTA: Quant?")
    assert "DADES:" in msg and "RESPOSTA:" in msg
    assert "registre" in msg  # the frozen prompt keys off this field


def test_scripted_backend_refuses_to_invent_a_call():
    backend = ScriptedBackend([])
    with pytest.raises(AssertionError):
        backend.complete(system="s", user="u", max_tokens=1)
