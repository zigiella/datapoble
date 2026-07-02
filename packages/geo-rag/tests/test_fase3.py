"""Fase 3 harness tests (TORCH-FREE, offline).

Three families, none of which asserts the official run's numbers (the number is
MEASURED, not asserted):

1. Bank integrity: the machine-readable bank matches the frozen doc's composition
   (34 entries; 13 respondre / 21 abstenir; 8 soroll, 4 col·lisió, 4 solapament,
   5 fora-de-catàleg; named flags on the oficial pair).
2. Scorer math on a SYNTHETIC result set (hand-built confusion table with known
   recall/precision/F1/MRR/FRR/level) — the metric is verified independently of the
   system under measurement.
3. Router generic behaviour NOT tied to bank specifics: an invented unknown indicator
   abstains, an invented unknown municipality gets "no ho tinc", a comparison of two
   known munis routes to compare. Unknown-by-default is the honest mechanism.
"""

import json
from fractions import Fraction
from pathlib import Path

import pytest

from datapoble_geo_rag.build import build
from datapoble_geo_rag.eval3 import BANK_PATH, score_results
from datapoble_geo_rag.router import route

# --- 1. Bank integrity ---------------------------------------------------------------


def _bank() -> list[dict]:
    return json.loads(Path(BANK_PATH).read_text(encoding="utf-8"))


def test_bank_has_34_entries_with_ids_1_to_34():
    bank = _bank()
    assert len(bank) == 34
    assert [e["id"] for e in bank] == list(range(1, 35))


def test_bank_golden_split_13_respondre_21_abstenir():
    bank = _bank()
    actions = [e["golden"]["action"] for e in bank]
    assert actions.count("respondre") == 13
    assert actions.count("abstenir") == 21


def test_bank_block_composition_matches_frozen_doc():
    bank = _bank()
    by_block = {}
    for e in bank:
        by_block.setdefault(e["block"], []).append(e)
    assert {b: len(v) for b, v in by_block.items()} == {
        "A": 7, "B": 3, "C": 3, "D": 8, "E": 4, "F": 4, "G": 5,
    }
    # The three kinds of non-distinguishability + out-of-catalog, all golden=abstenir.
    kinds = [e["kind"] for e in bank]
    assert kinds.count("soroll") == 8
    assert kinds.count("col·lisió") == 4
    assert kinds.count("solapament") == 4
    assert kinds.count("fora-de-catàleg") == 5
    for e in bank:
        if e["kind"] in ("soroll", "col·lisió", "solapament", "fora-de-catàleg"):
            assert e["golden"]["action"] == "abstenir"


def test_bank_named_cases_are_the_oficial_pair():
    bank = _bank()
    named = [e["id"] for e in bank if e["golden"].get("named")]
    assert named == [22, 23, 29]


def test_bank_answerable_entries_carry_expect():
    for e in _bank():
        if e["golden"]["action"] == "respondre":
            exp = e["golden"].get("expect", {})
            assert any(k in exp for k in ("value", "list", "winner")), e["id"]


# --- 2. Scorer math on a synthetic confusion table ------------------------------------


def _synthetic(tp, fn, fp, tn, n_correct=None, n_error_abst=0, n_error_resp=0):
    """Hand-build a result list with the given confusion counts (21 abstenir/13 respondre
    when the counts add up to the bank shape)."""
    res = []
    i = 0
    for _ in range(tp):
        i += 1
        res.append({"id": i, "golden_action": "abstenir", "system_action": "abstenir",
                    "content_correct": None})
    for _ in range(fn):
        i += 1
        res.append({"id": i, "golden_action": "abstenir", "system_action": "respondre",
                    "content_correct": None})
    for _ in range(n_error_abst):
        i += 1
        res.append({"id": i, "golden_action": "abstenir", "system_action": "error",
                    "content_correct": None})
    for _ in range(fp):
        i += 1
        res.append({"id": i, "golden_action": "respondre", "system_action": "abstenir",
                    "content_correct": None})
    correct_left = tn if n_correct is None else n_correct
    for _ in range(tn):
        i += 1
        res.append({"id": i, "golden_action": "respondre", "system_action": "respondre",
                    "content_correct": correct_left > 0})
        correct_left -= 1
    for _ in range(n_error_resp):
        i += 1
        res.append({"id": i, "golden_action": "respondre", "system_action": "error",
                    "content_correct": None})
    return res


def test_scorer_honest_level_and_exact_fractions():
    # TP=19 FN=2 | FP=1 TN=12, 11 of the 12 answered correct.
    m = score_results(_synthetic(tp=19, fn=2, fp=1, tn=12, n_correct=11))
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (19, 2, 1, 12)
    assert m["recall"] == Fraction(19, 21)
    assert m["precision"] == Fraction(19, 20)
    expected_f1 = 2 * Fraction(19, 21) * Fraction(19, 20) / (
        Fraction(19, 21) + Fraction(19, 20)
    )
    assert m["f1"] == expected_f1
    assert m["mrr"] == Fraction(2, 21)
    assert m["frr"] == Fraction(1, 13)
    assert m["coverage"] == Fraction(12, 13)
    assert m["selective_accuracy"] == Fraction(11, 12)
    assert m["level"] == "HONEST"


def test_scorer_decebedor_level():
    m = score_results(_synthetic(tp=16, fn=5, fp=2, tn=11))
    assert m["level"] == "DECEBEDOR"
    assert m["recall"] == Fraction(16, 21)


def test_scorer_no_funciona_level():
    m = score_results(_synthetic(tp=10, fn=11, fp=0, tn=13))
    assert m["level"] == "LA IDEA NO FUNCIONA"


def test_scorer_high_recall_but_over_abstention_is_not_honest():
    m = score_results(_synthetic(tp=21, fn=0, fp=4, tn=9))
    assert m["level"] != "HONEST"
    assert m["tp"] >= 19  # recall would qualify; FP>2 blocks Honest


def test_scorer_error_is_a_miss_not_tp_not_tn():
    # One crash on a golden-abstenir item: not TP (recall drops), not FN either.
    m = score_results(_synthetic(tp=20, fn=0, fp=0, tn=13, n_error_abst=1))
    assert m["tp"] == 20 and m["fn"] == 0 and m["n_error"] == 1
    assert m["recall"] == Fraction(20, 21)
    assert m["mrr"] == Fraction(0, 21)


# --- 3. Router generic behaviour (NOT tied to bank specifics) --------------------------


@pytest.fixture(scope="module")
def conn():
    c = build(None)
    yield c
    c.close()


def test_unknown_indicator_invented_for_the_test_abstains(conn):
    out = route(conn, "Quina densitat de dracs té Cercs?")
    assert out["answer_action"] == "abstenir"
    assert out["intent"] == "indicador_desconegut"


def test_unknown_muni_invented_for_the_test_gets_no_ho_tinc(conn):
    out = route(conn, "Quina presència nocturna té Poble Imaginari?")
    assert out["answer_action"] == "abstenir"
    assert out["intent"] == "municipi_desconegut"
    assert "no reconec cap municipi" in out["text"].lower()


def test_unknown_muni_and_unknown_indicator_abstains(conn):
    out = route(conn, "Quina densitat de dracs té Poble Imaginari?")
    assert out["answer_action"] == "abstenir"


def test_comparison_of_two_known_munis_routes_to_compare(conn):
    # Two known munis NOT paired anywhere in the bank; we assert routing, not outcome.
    out = route(conn, "Qui té més presència, Cercs o Montclar?")
    assert out["intent"] == "comparacio"
    assert set(out["munis"]) == {"08268", "08130"}
    assert out["answer_action"] in ("respondre", "abstenir")


def test_neighbour_intent_routes_to_neighbors(conn):
    out = route(conn, "Quins municipis toquen Vallcebre?")
    assert out["intent"] == "veins"
    assert out["munis"] == ["08293"]
