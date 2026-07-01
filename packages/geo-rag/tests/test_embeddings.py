"""Phase-0b tests: descriptions, the committed embeddings artifact, and semantic search.

The OFFLINE tests here (no torch) are what CI runs — they read only the committed
parquet + meta sidecar and the torch-free search path. One torch-guarded test embeds a
live query and SKIPS in CI (where torch is absent).
"""

import json

import pytest

from datapoble_geo_rag.build import build
from datapoble_geo_rag.descriptions import generate_descriptions
from datapoble_geo_rag.search import ARTIFACT_META, ARTIFACT_PARQUET, semantic_search


@pytest.fixture(scope="module")
def conn():
    c = build(None)  # in-memory; build() auto-loads municipi_emb if the artifact exists
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Descriptions (torch-free)
# ---------------------------------------------------------------------------

def test_descriptions_count(conn):
    descs = generate_descriptions(conn)
    assert len(descs) == 31


def test_descriptions_per_register(conn):
    descs = generate_descriptions(conn)
    regs = dict(conn.execute("SELECT ine5, register FROM municipi").fetchall())

    saw = {"oficial": False, "senyal_mes": False, "senyal_menys": False, "soroll": False}
    for ine5, text in descs.items():
        reg = regs[ine5]
        saw[reg] = True
        if reg == "oficial":
            assert "ETCA" in text, text
        elif reg in ("senyal_mes", "senyal_menys"):
            assert "exclou el padró" in text, text
        elif reg == "soroll":
            assert "no es distingeix" in text, text
            assert "inclou el padró" in text, text
    # Every register present in the 31 was exercised (senyal_menys count is 1 -> present).
    assert all(saw[r] for r in ("oficial", "senyal_mes", "senyal_menys", "soroll")), saw


def test_descriptions_directionality(conn):
    descs = generate_descriptions(conn)
    regs = dict(conn.execute("SELECT ine5, register FROM municipi").fetchall())
    for ine5, text in descs.items():
        if regs[ine5] == "senyal_mes":
            assert "per sobre del padró" in text, text
        if regs[ine5] == "senyal_menys":
            assert "per sota del padró" in text, text


# ---------------------------------------------------------------------------
# Committed artifact (torch-free)
# ---------------------------------------------------------------------------

def test_artifact_files_exist():
    assert ARTIFACT_PARQUET.exists(), f"missing {ARTIFACT_PARQUET}"
    assert ARTIFACT_META.exists(), f"missing {ARTIFACT_META}"


def test_meta_has_revision():
    meta = json.loads(ARTIFACT_META.read_text(encoding="utf-8"))
    assert meta["dim"] == 384
    assert meta["n"] == 31
    assert meta.get("revision"), "meta.revision must be non-empty"
    assert meta["model"] == "intfloat/multilingual-e5-small"


def test_parquet_loads_31x384(conn):
    rows = conn.execute(
        "SELECT ine5, emb FROM read_parquet(?)", [str(ARTIFACT_PARQUET)]
    ).fetchall()
    assert len(rows) == 31
    for ine5, emb in rows:
        assert len(emb) == 384, f"{ine5}: emb len {len(emb)} != 384"


def test_artifact_ine5_matches_municipi(conn):
    art = {r[0] for r in conn.execute("SELECT ine5 FROM read_parquet(?)", [str(ARTIFACT_PARQUET)]).fetchall()}
    muni = {r[0] for r in conn.execute("SELECT ine5 FROM municipi").fetchall()}
    assert art == muni, f"symmetric diff: {art ^ muni}"


def test_municipi_emb_loaded(conn):
    emb_flag = conn.execute("SELECT value FROM _substrate_meta WHERE key='embeddings'").fetchone()[0]
    assert emb_flag == "1", "municipi_emb should be loaded (artifact is committed)"
    n = conn.execute("SELECT COUNT(*) FROM municipi_emb").fetchone()[0]
    assert n == 31
    dim = conn.execute("SELECT len(emb) FROM municipi_emb LIMIT 1").fetchone()[0]
    assert dim == 384


# ---------------------------------------------------------------------------
# Cosine self-retrieval (torch-free): a muni's own vector ranks itself #1
# ---------------------------------------------------------------------------

def test_self_retrieval_rank1(conn):
    for ine5 in ("08022", "08177", "08080"):  # Berga (oficial), la Quar (senyal_mes), Fígols (senyal_menys)
        vec = conn.execute(
            "SELECT emb FROM municipi_emb WHERE ine5 = ?", [ine5]
        ).fetchone()[0]
        res = semantic_search(conn, list(vec), k=5)
        assert res, f"{ine5}: no results"
        assert res[0][0] == ine5, f"{ine5}: rank-1 was {res[0]}, expected self"


# ---------------------------------------------------------------------------
# Torch-guarded live query (SKIPS in CI where torch is absent)
# ---------------------------------------------------------------------------

def test_query_embedding_finds_senyal_mes(conn):
    pytest.importorskip("torch")
    from datapoble_geo_rag import embeddings

    # Honest note: e5-small retrieval is phrasing-sensitive on these 31 short docs.
    # A query echoing the senyal wording ("senyal per sobre del padró") reliably
    # surfaces senyal_mes munis; a looser paraphrase ("més presència que el padró")
    # does not. We assert on the faithful rephrasing, not a cherry-picked one.
    qvec = embeddings.embed_query("poble amb senyal per sobre del padró")
    res = semantic_search(conn, qvec, k=5)
    top5 = {ine5 for ine5, _nom, _score in res}
    senyal_mes = {
        r[0] for r in conn.execute(
            "SELECT ine5 FROM municipi WHERE register = 'senyal_mes'"
        ).fetchall()
    }
    assert top5 & senyal_mes, f"no senyal_mes muni in top-5: {res}"
