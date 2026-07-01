"""Phase-1 retrieval tests — OFFLINE, TORCH-FREE (uses committed bank vectors).

These read only the committed substrate + the committed query bank (data/fase1-bank.json,
which ships query vectors), so they run in CI with no torch. One torch-guarded test embeds
a fresh query and SKIPS in CI.

The contract: the retriever does NOT break a tie the data can't break — it REPORTS it. A
collision top must surface the whole sharing group; a real order must not be imposed.
"""

import json

import pytest

from datapoble_geo_rag.build import build
from datapoble_geo_rag.eval import BANK_PATH
from datapoble_geo_rag.retrieval import RRF_K, detect_anchor, retrieve, rrf_score


@pytest.fixture(scope="module")
def conn():
    c = build(None)
    yield c
    c.close()


@pytest.fixture(scope="module")
def bank():
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def _entry(bank, entry_id):
    return next(e for e in bank if e["id"] == entry_id)


# ---------------------------------------------------------------------------
# Hard spatial filter narrows candidates to anchor + neighbours
# ---------------------------------------------------------------------------

def test_anchor_spatial_filter_narrows(conn, bank):
    e = _entry(bank, "spatial-veins-berga")
    res = retrieve(conn, e["query"], e["query_vec"], anchor_ine5=e["anchor_ine5"], k=5)
    # Narrowed below the full comarca of 31...
    assert res["n_candidates"] < 31
    # ...and every returned candidate is a real muni within the 31.
    all31 = {r[0] for r in conn.execute("SELECT ine5 FROM municipi").fetchall()}
    for c in res["candidates"]:
        assert c["ine5"] in all31
    # The anchor itself is present in the filtered set (distance 0).
    assert e["anchor_ine5"] in {c["ine5"] for c in res["candidates"]}


def test_detect_anchor_finds_muni_name(conn):
    assert detect_anchor(conn, "veïns de Berga") == "08022"
    assert detect_anchor(conn, "quins pobles tenen més presència") is None


# ---------------------------------------------------------------------------
# Collision OFICIAL: Guardiola / la Pobla de Lillet -> reported tie, ETCA note
# ---------------------------------------------------------------------------

def test_collision_oficial_reports_tie(conn, bank):
    e = _entry(bank, "collision-oficial-guardiola")
    res = retrieve(conn, e["query"], e["query_vec"], anchor_ine5=e["anchor_ine5"], k=5)
    tie = res["tie"]
    assert tie["is_tie"] is True
    assert tie["kind"] == "collision"
    assert set(tie["group"]) == {"08099", "08166"}  # Guardiola + la Pobla de Lillet
    # The note must state Idescat separates them (ETCA), contradicting the oficial label.
    assert "ETCA" in tie["note"]
    assert "1005" in tie["note"] and "1121" in tie["note"]


# ---------------------------------------------------------------------------
# Collision SOROLL: a soroll group -> reported tie
# ---------------------------------------------------------------------------

def test_collision_soroll_reports_tie(conn, bank):
    e = _entry(bank, "collision-soroll-gosol")
    res = retrieve(conn, e["query"], e["query_vec"], anchor_ine5=e["anchor_ine5"], k=5)
    tie = res["tie"]
    assert tie["is_tie"] is True
    assert tie["kind"] == "collision"
    # Gósol shares its estimate with 2 other Catalunya munis (group of 3).
    assert set(tie["group"]) == {"08026", "25055", "25100"}
    assert "no els distingeix" in tie["note"]


# ---------------------------------------------------------------------------
# Normal: expected target in top-k, no false tie
# ---------------------------------------------------------------------------

def test_normal_spatial_targets_in_topk(conn, bank):
    e = _entry(bank, "spatial-veins-berga")
    res = retrieve(conn, e["query"], e["query_vec"], anchor_ine5=e["anchor_ine5"], k=5)
    topk = {c["ine5"] for c in res["candidates"]}
    assert set(e["expected"]["targets"]) & topk
    # Berga is unique (non-collision); the spatial result is not a collision tie.
    assert not (res["tie"]["is_tie"] and res["tie"]["kind"] == "collision")


def test_normal_semantic_target_in_topk(conn, bank):
    e = _entry(bank, "semantic-figols-menys-padro")
    res = retrieve(conn, e["query"], e["query_vec"], anchor_ine5=e["anchor_ine5"], k=5)
    topk = {c["ine5"] for c in res["candidates"]}
    assert "08080" in topk  # Fígols — the unique senyal_menys muni


# ---------------------------------------------------------------------------
# RRF unit: fusing two known rank lists yields 1/(K+r1) + 1/(K+r2)
# ---------------------------------------------------------------------------

def test_rrf_score_formula():
    r1, r2 = 1, 3
    assert rrf_score(r1, r2) == pytest.approx(1.0 / (RRF_K + r1) + 1.0 / (RRF_K + r2))
    # A candidate ranked #1 in both lists scores strictly higher than one ranked #2 in both.
    assert rrf_score(1, 1) > rrf_score(2, 2)


# ---------------------------------------------------------------------------
# Torch-guarded live query (SKIPS in CI where torch is absent)
# ---------------------------------------------------------------------------

def test_live_query_retrieve(conn):
    pytest.importorskip("torch")
    from datapoble_geo_rag import embeddings

    qvec = embeddings.embed_query("veïns de Berga")
    res = retrieve(conn, "veïns de Berga", qvec, anchor_ine5="08022", k=5)
    assert res["n_candidates"] < 31
    topk = {c["ine5"] for c in res["candidates"]}
    # At least one true Berga neighbour surfaces.
    assert topk & {"08011", "08045", "08050", "08268", "08144"}
