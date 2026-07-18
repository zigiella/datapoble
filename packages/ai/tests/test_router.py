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
    # The minimum rtc_total in the fixtures is la Nou de Berguedà (7). The data
    # rows keep the mart's register spelling (byte-faithful trace)…
    assert ans.data[0]["municipi"] == "Nou de Berguedà, la"
    # …while the prose says the name the natural way.
    assert "la Nou de Berguedà" in ans.text
    assert "Nou de Berguedà, la" not in ans.text


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


# ---------------------------------------------------------------------------
# B3 — the three router holes found while proving the /pregunta-li chips
# resolve for real (fixtures AND production marts).


def test_article_toponym_resolves_lookup(agent):
    """F2: register-style names («Pobla de Lillet, la») must match the natural
    question form («la Pobla de Lillet») — the demo municipality refused on
    every mart_municipi lookup before the per-table variant index."""
    ans = agent.ask("Quants habitants té la Pobla de Lillet?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "poblacio"
    # The SQL bound the name as the table spells it (trace stays exact)…
    assert ans.data[0]["municipi"] == "Pobla de Lillet, la"
    # …and the prose says it the natural way.
    assert "la Pobla de Lillet" in ans.text
    assert "Pobla de Lillet, la" not in ans.text


def test_muni_name_variants_apostrophe_article():
    """F2 unit: the apostrophe article hugs the noun («l'Espunyola»)."""
    from datapoble_ai.router import _muni_name_variants, natural_muni_name

    assert natural_muni_name("Espunyola, l'") == "l'Espunyola"
    assert natural_muni_name("Pobla de Lillet, la") == "la Pobla de Lillet"
    assert natural_muni_name("Berga") == "Berga"          # untouched
    assert "l'espunyola" in _muni_name_variants("Espunyola, l'")


def test_monthly_mart_lookup_pins_latest_month(agent):
    """F1: a dated mart must answer with MAX(date), never an arbitrary row.

    The fixture carries two real months with the stale one first in the file
    (la Pobla: 27 al maig, 31 al juny): an unpinned lookup would answer 27.
    In production the series runs 2006→today, and the naive lookup served a
    2006 figure as current.
    """
    ans = agent.ask("Quantes persones hi ha a l'atur a la Pobla de Lillet?",
                    locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "atur_registrat"
    assert "31" in ans.text
    assert len(ans.data) == 1                 # one month, not the whole series
    assert 'MAX("date")' in ans.provenance.query


def test_monthly_mart_ranking_pins_latest_month(agent):
    # Berga is the fixture's top in both months; the value must be June's
    # (760), not May's (776).
    ans = agent.ask("Quin municipi té més atur registrat?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "atur_registrat"
    assert "760" in ans.text
    assert "776" not in ans.text


def test_qualifier_variant_does_not_steal_the_metric(agent):
    """F3: «residus per habitant» must answer kg_hab_any, not hab_per_hab.

    «Habitatges per habitant» minus its lead word used to leave the bare
    qualifier «per habitant», which outscored the «residus» synonym on length
    — the live residus chip was answering the wrong metric in production.
    """
    ans = agent.ask("Quants quilos de residus per habitant genera Bagà?",
                    locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "kg_hab_any"


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
