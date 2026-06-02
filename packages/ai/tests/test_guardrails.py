"""The hard guardrails: read-only, contract tables only, no raw, refuse-with-reason."""

from __future__ import annotations

import duckdb
import pytest

from datapoble_ai.types import AnswerKind, RefusalReason
from datapoble_ai.warehouse import WarehouseError

# ---- SQL-level guardrails (warehouse) ----------------------------------------

@pytest.mark.parametrize("bad_sql", [
    "INSERT INTO mart_municipi VALUES (1)",
    "UPDATE mart_municipi SET poblacio = 0",
    "DELETE FROM mart_municipi",
    "DROP TABLE mart_municipi",
    "ALTER TABLE mart_municipi ADD COLUMN x INT",
    "CREATE TABLE evil AS SELECT 1",
    "ATTACH 'x.db' AS y",
    "COPY mart_municipi TO 'out.csv'",
    "PRAGMA database_list",
    "INSTALL spatial",
    "SELECT 1; DROP TABLE mart_municipi",          # statement stacking
    "SELECT * FROM mart_municipi; SELECT 2",        # multiple statements
    "",                                             # empty
])
def test_write_and_multistatement_blocked(warehouse, bad_sql):
    with pytest.raises(WarehouseError):
        warehouse.validate(bad_sql)


def test_comment_smuggling_blocked(warehouse):
    # A second statement hidden after a comment must still be rejected.
    with pytest.raises(WarehouseError):
        warehouse.validate("SELECT 1 -- ok\n; DROP TABLE mart_municipi")


def test_raw_table_is_not_registered(warehouse):
    # `raw` tables simply do not exist in the read-only warehouse -> fail closed.
    with pytest.raises(duckdb.Error):
        warehouse.query("SELECT * FROM raw_idescat_emex")


def test_select_is_allowed(warehouse):
    rows = warehouse.query('SELECT municipi FROM "mart_municipi" LIMIT 1')
    assert rows and "municipi" in rows[0]


def test_params_are_bound_not_interpolated(warehouse):
    # A value that would be dangerous if string-formatted is safely bound.
    rows = warehouse.query(
        'SELECT municipi FROM "mart_municipi" WHERE municipi = $m',
        {"m": "Berga'; DROP TABLE mart_municipi; --"},
    )
    assert rows == []  # no such municipality, and nothing dropped
    # Table still intact:
    assert warehouse.query('SELECT count(*) AS n FROM "mart_municipi"')[0]["n"] > 0


# ---- agent-level guardrails (refusals) ---------------------------------------

def test_out_of_catalog_is_refused_with_reason(agent):
    ans = agent.ask("Quin és el PIB de Berga?", locale="ca")
    assert ans.kind == AnswerKind.REFUSAL
    assert ans.refusal_reason == RefusalReason.OUT_OF_CATALOG


def test_planned_metric_is_refused_as_planned(agent):
    ans = agent.ask("On creix més l'extrema dreta?", locale="ca")
    assert ans.kind == AnswerKind.REFUSAL
    assert ans.refusal_reason == RefusalReason.METRIC_PLANNED


def test_unknown_municipality_refused(agent):
    ans = agent.ask("Quants habitatges no principals té Barcelona?", locale="ca")
    assert ans.kind == AnswerKind.REFUSAL
    assert ans.refusal_reason == RefusalReason.UNKNOWN_MUNICIPALITY


def test_answers_always_carry_provenance(agent):
    ans = agent.ask("Quina població té Berga?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.provenance is not None
    assert ans.provenance.source and ans.provenance.formula and ans.provenance.query
