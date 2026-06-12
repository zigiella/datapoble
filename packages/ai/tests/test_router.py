"""Router behaviour: lookup / ranking / correlation, ca + es, provenance."""

from __future__ import annotations

from datapoble_ai import Agent
from datapoble_ai.types import AnswerKind


def test_lookup_returns_verified_value_ca(agent):
    ans = agent.ask("Quants habitatges no principals té Castellar de n'Hug?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "hab_noprincipal"
    assert "205" in ans.text                      # verified fact
    assert ans.provenance.date == "2021"
    assert ans.provenance.is_fixture is True       # answered from seed fixtures


def test_lookup_es_locale(agent):
    ans = agent.ask("¿Cuántas viviendas no principales tiene Castellar de n'Hug?", locale="es")
    assert ans.kind == AnswerKind.ANSWER
    assert "205" in ans.text
    # Spanish phrasing: "Fuente:" not "Font:".
    assert "Fuente:" in ans.text


def test_ranking_top_picks_max(agent):
    ans = agent.ask("Quin municipi té més exposició turística-residencial?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "IETR"
    assert ans.data[0]["municipi"] == "Castellar de n'Hug"  # IETR 100 in fixtures


def test_ranking_min_direction(agent):
    ans = agent.ask("Quin municipi té menys establiments turístics?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "rtc_total"
    # The minimum rtc_total in the fixtures is La Nou de Berguedà (7).
    assert ans.data[0]["municipi"] == "La Nou de Berguedà"


def test_ranking_list_returns_multiple_rows(agent):
    ans = agent.ask("Fes-me un rànquing dels municipis per IETR", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert len(ans.data) > 1


def test_correlation_two_metrics(agent):
    ans = agent.ask("Quina relació hi ha entre l'índex i els residus?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "IETR"
    assert "Spearman" in ans.text
    # The provenance formula reflects the relationship, not a single metric.
    assert ans.provenance.formula.startswith("spearman(")


def test_provenance_includes_query_and_source(agent):
    ans = agent.ask("Quina població té Berga?", locale="ca")
    assert ans.provenance.query.lower().startswith("select")
    assert "Idescat" in (ans.provenance.source or "")


def test_derived_metric_cites_origin_source(agent):
    # pct_noprincipal is source: datapoble with origin_source: idescat_emex.
    # El bloc de procedència `datapoble` es retola en públic com a «indicador derivat»
    # (renom de l'spec de consultora 2 §1.4); la clau interna del contracte segueix sent
    # `datapoble`, però la cadena visible marca la capa derivada amb «indicador derivat».
    ans = agent.ask("Quin municipi té més % habitatge no principal?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "pct_noprincipal"
    assert "Idescat" in (ans.provenance.source or "")   # upstream origin surfaced
    assert "indicador derivat" in (ans.provenance.source or "").lower()  # via the derived layer


def test_note_caveat_surfaced_for_political_metric(monkeypatch):
    # pct_indep carries an "ecological reading" caveat note in the contract.
    # Vote metrics are gated off by default (see test_politics.py), so to reach
    # the answer (and its note) we must unlock the gate with the secret word.
    monkeypatch.setenv("AI_POLITICS_UNLOCK", "obretesim")
    with Agent(mode="offline", use_fixtures=True) as a:
        ans = a.ask("obretesim Quin municipi té més % vot independentista?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert "ecol" in ans.text.lower() or "ECOL" in ans.text   # nota present
    # The secret word must never echo back in the answer or the question.
    assert "obretesim" not in ans.text.lower()
    assert "obretesim" not in ans.question.lower()
