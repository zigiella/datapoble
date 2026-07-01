"""Semantic search over the committed embeddings artifact — TORCH-FREE.

The ranking path never imports torch. It loads the committed base-embeddings parquet
(produced locally by embeddings.py) into a DuckDB ARRAY column and ranks by cosine
similarity. Query embedding is done separately by embeddings.embed_query (torch);
semantic_search takes a *ready* 384-dim vector, keeping this path torch-free.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

_PKG_ROOT = Path(__file__).resolve().parents[2]  # packages/geo-rag
ARTIFACT_PARQUET = _PKG_ROOT / "data" / "embeddings-e5-small.parquet"
ARTIFACT_META = _PKG_ROOT / "data" / "embeddings-e5-small.meta.json"

EMB_DIM = 384


def load_embeddings(
    conn: duckdb.DuckDBPyConnection, parquet_path: Path | None = None
) -> bool:
    """Create table municipi_emb(ine5 VARCHAR, emb FLOAT[384]) from the committed parquet.

    Returns True if the artifact existed and was loaded, False if absent (silently, so
    the Phase-0a substrate still builds without embeddings). Torch-free.
    """
    path = parquet_path or ARTIFACT_PARQUET
    if not Path(path).exists():
        return False

    conn.execute(
        f"""
        CREATE OR REPLACE TABLE municipi_emb (
            ine5 VARCHAR,
            emb FLOAT[{EMB_DIM}]
        );
        """
    )
    # read_parquet gives emb as a variable-length list; cast to the fixed-size array.
    conn.execute(
        f"""
        INSERT INTO municipi_emb (ine5, emb)
        SELECT ine5, CAST(emb AS FLOAT[{EMB_DIM}])
        FROM read_parquet(?)
        """,
        [str(path)],
    )
    return True


def semantic_search(
    conn: duckdb.DuckDBPyConnection,
    query_vec: list[float],
    k: int = 5,
) -> list[tuple[str, str, float]]:
    """Rank munis by cosine similarity to a ready query vector.

    query_vec: a 384-dim embedding (produced by embeddings.embed_query — torch — out
    of this path). Returns [(ine5, nom, score), ...] descending by cosine, top-k.
    Requires municipi_emb (see load_embeddings) and the municipi table (for nom).
    """
    if len(query_vec) != EMB_DIM:
        raise ValueError(f"query_vec must be {EMB_DIM}-dim, got {len(query_vec)}")

    vec_literal = "[" + ", ".join(repr(float(x)) for x in query_vec) + "]"
    return conn.execute(
        f"""
        SELECT e.ine5, m.nom,
               array_cosine_similarity(e.emb, {vec_literal}::FLOAT[{EMB_DIM}]) AS score
        FROM municipi_emb e
        JOIN municipi m ON m.ine5 = e.ine5
        ORDER BY score DESC
        LIMIT ?
        """,
        [k],
    ).fetchall()
