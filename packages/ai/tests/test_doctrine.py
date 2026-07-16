"""The doctrine, harvested in X1 (contract C5) — registers, tie rule, caveats.

All offline: no network, no key. The subject under test is the doctrine itself,
so the data is pinned to the seed fixtures.
"""

from __future__ import annotations

import pytest

from datapoble_ai import Agent
from datapoble_ai.doctrine import (
    OFICIAL,
    SENYAL,
    SOROLL,
    build_context,
    distinguishable,
    is_inference,
    obligated_caveat,
    register_for,
    takes_confidence_flag,
    tied_names,
)

# --- the registers ------------------------------------------------------------


def test_measured_metric_is_oficial(catalog):
    """A padró count is not an inference, whatever the confidence flag says."""
    poblacio = catalog.metric("poblacio")
    assert not is_inference(poblacio)
    assert register_for(poblacio, None) == OFICIAL
    # Even handed a 'baixa' flag: the flag does not grade a measured figure.
    assert register_for(poblacio, "baixa") == OFICIAL


def test_inference_without_low_flag_is_senyal(catalog):
    pernocta = catalog.metric("poblacio_pernocta_est")
    assert is_inference(pernocta)
    assert register_for(pernocta, "alta") == SENYAL
    assert register_for(pernocta, None) == SENYAL


def test_inference_with_low_flag_is_soroll(catalog):
    """The loud silence: we have the estimate and we disown it, with a reason."""
    pernocta = catalog.metric("poblacio_pernocta_est")
    assert register_for(pernocta, "baixa") == SOROLL
    assert register_for(pernocta, "BAIXA") == SOROLL  # case-folded


def test_confidence_flag_only_grades_the_dimension_it_declares(catalog):
    """The flag grades pressure estimates; it does not lend authority elsewhere."""
    assert takes_confidence_flag(catalog.metric("poblacio_pernocta_est"))
    # IETR is an index, not a pressure estimate: the flag does not apply.
    assert not takes_confidence_flag(catalog.metric("IETR"))
    assert not takes_confidence_flag(catalog.metric("poblacio"))


# --- the obligated caveat (the bug the harvest exposed) -----------------------


@pytest.mark.parametrize(
    "key", ["poblacio_pernocta_est", "gap_pernocta", "gap_pernocta_pct",
            "confianca", "carrega_total_est", "poblacio_real_est"],
)
def test_inference_metrics_surface_their_declared_caveat(catalog, key):
    """The contract declares these under `caveat:`; they must reach the reader.

    Regression: `Metric.note` read only `nota:`, so every one of these — the
    metrics whose own text says "INFERÈNCIA, no cens" — was served with no caveat
    at all. See `Metric.note`.
    """
    caveat = obligated_caveat(catalog.metric(key), "ca")
    assert caveat, f"{key} declares a caveat in the contract but surfaces none"


def test_nota_still_wins_where_the_contract_uses_it(catalog):
    """The other key keeps working (IETR declares `nota:`)."""
    assert "exposició" in obligated_caveat(catalog.metric("IETR"), "ca").lower()


def test_caveat_reaches_the_served_answer(agent):
    """End to end: the caveat is in the text, not just in the catalog."""
    ans = agent.ask("Quina població real estimada té Berga?", locale="ca")
    assert ans.is_answer
    assert ans.provenance.note, "provenance carries no caveat"
    assert "INFERÈNCIA" in ans.text


# --- the tie rule -------------------------------------------------------------


def test_distinguishable_separates_a_clear_leader():
    assert distinguishable([100.0, 88.1, 72.4]) is True


def test_distinguishable_refuses_a_shared_top():
    assert distinguishable([100.0, 100.0, 72.4]) is False


def test_distinguishable_single_and_empty():
    assert distinguishable([42]) is True
    assert distinguishable([]) is False
    assert distinguishable([None]) is False


def test_tied_names_lists_the_shared_top():
    rows = [{"municipi": "A", "value": 100.0}, {"municipi": "B", "value": 100.0},
            {"municipi": "C", "value": 9.0}]
    assert tied_names(rows) == ["A", "B"]


def test_tied_names_empty_when_leader_is_alone():
    rows = [{"municipi": "A", "value": 100.0}, {"municipi": "B", "value": 9.0}]
    assert tied_names(rows) == ["A"]


def test_ranking_names_a_winner_when_the_data_singles_one_out(agent):
    """The fixture has no IETR tie, so the ordinary ranking still answers."""
    ans = agent.ask("Quin municipi té més exposició turística-residencial?",
                    locale="ca")
    assert ans.is_answer
    assert "Castellar" in ans.text


def test_ranking_refuses_to_order_a_shared_top(tmp_path, catalog):
    """A tie must not be broken by row order — the doctrine's `empat`.

    Built on its own mart so the tie is the only thing under test. Live on the
    real mart this is not hypothetical: 47 municipalities share
    `index_turisme = 100` and 6 share `IETR = 100`.
    """
    (tmp_path / "mart_municipi.csv").write_text(
        "ine5,municipi,poblacio,IETR\n"
        "08001,Alfa,100,100.0\n"
        "08002,Bravo,200,100.0\n"
        "08003,Charlie,300,50.0\n",
        encoding="utf-8",
    )
    (tmp_path / "mart_electoral.csv").write_text(
        "ine5,municipi,pct_indep_A20241,guanya_A20241\n"
        "08001,Alfa,50.0,X\n",
        encoding="utf-8",
    )
    with Agent(mode="offline", marts_dir=tmp_path) as a:
        ans = a.ask("Quin municipi té més exposició turística-residencial?",
                    locale="ca")
    assert ans.is_answer
    assert "No puc dir quin municipi" in ans.text
    assert "Alfa" in ans.text and "Bravo" in ans.text
    assert "Charlie" not in ans.text


# --- the context handed to the generative layer ------------------------------


def test_context_carries_register_and_obligated_caveat(catalog):
    metric = catalog.metric("poblacio_pernocta_est")
    ctx = build_context(
        catalog, metric, "ca",
        [{"municipi": "Castellar de n'Hug", "value": 133}],
        "valor_municipi",
        confidence_by_muni={"Castellar de n'Hug": "baixa"},
    )
    assert ctx["cel·les"][0]["registre"] == SOROLL
    assert "INFERÈNCIA" in ctx["caveat_obligat"]
    assert ctx["metrica"]["clau"] == "poblacio_pernocta_est"


def test_context_marks_not_found_when_there_are_no_cells(catalog):
    ctx = build_context(catalog, catalog.metric("poblacio"), "ca", [],
                        "valor_municipi")
    assert ctx["not_found"] is True
    assert "cel·les" not in ctx
