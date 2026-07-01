"""Local embedding generation — the ONLY torch-dependent module (Phase 0b).

torch / sentence-transformers are imported here ONLY. This module regenerates the
COMMITTED base-embeddings artifact and provides a local query embedder. It is never
imported by the build or the semantic-search ranking path, and never runs in CI.

Model: intfloat/multilingual-e5-small (MIT, 384-dim). We PIN the HF commit SHA in
MODEL_REVISION so re-generation is reproducible. e5 convention: documents are prefixed
"passage: " and queries "query: ".

MC-Dropout note: the σ sub-experiment (later) needs stochastic passes with dropout
ACTIVE — that only works if the model config ships dropout p>0. regenerate_artifact()
verifies and prints this on the pinned revision. The committed base vectors here are
DETERMINISTIC (dropout OFF / model in eval mode).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .descriptions import generate_descriptions
from .search import ARTIFACT_META, ARTIFACT_PARQUET, EMB_DIM

MODEL_NAME = "intfloat/multilingual-e5-small"
# Resolved from huggingface_hub.model_info(MODEL_NAME).sha at implementation time and
# pinned so re-generation loads the exact weights. Verify/refresh via _resolve_revision().
MODEL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"

PREFIX_DOC = "passage: "
PREFIX_QUERY = "query: "

# Lazy singleton so importing this module doesn't load torch until actually used.
_MODEL = None


def _resolve_revision() -> str:
    """Return the current commit SHA for the model on the Hub (needs network)."""
    from huggingface_hub import model_info

    return model_info(MODEL_NAME).sha


def _load_model():
    """Load the SentenceTransformer at the pinned revision (torch import happens here)."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION)
    return _MODEL


def _dropout_probs(model) -> tuple[float, float]:
    """Return (hidden_dropout_prob, attention_probs_dropout_prob) from the HF config."""
    cfg = model[0].auto_model.config
    return (
        float(getattr(cfg, "hidden_dropout_prob", 0.0)),
        float(getattr(cfg, "attention_probs_dropout_prob", 0.0)),
    )


def embed_query(text: str) -> list[float]:
    """Embed a query string (prepends the e5 'query: ' prefix). Torch — local only.

    Returns a normalized 384-dim vector (list of floats). NOT used in the torch-free
    search path — callers pass the result to search.semantic_search.
    """
    model = _load_model()
    vec = model.encode(
        PREFIX_QUERY + text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return [float(x) for x in vec.tolist()]


def regenerate_artifact(conn) -> Path:
    """Regenerate the COMMITTED base-embeddings parquet + meta sidecar. Torch — local only.

    For each muni: embed PREFIX_DOC + description, deterministic base vector (dropout
    OFF), 384-dim, normalized. Writes:
      - data/embeddings-e5-small.parquet  (ine5 VARCHAR, emb DOUBLE[])
      - data/embeddings-e5-small.meta.json (model/revision/dim/prefixes/n/note)
    Verifies dropout p>0 (needed for the later MC-Dropout σ experiment) and prints it.
    Returns the parquet path.
    """
    import duckdb  # noqa: F401  (used implicitly via the passed conn)

    model = _load_model()
    h_do, a_do = _dropout_probs(model)
    print(f"[embeddings] model={MODEL_NAME} revision={MODEL_REVISION}")
    print(f"[embeddings] hidden_dropout_prob={h_do} attention_probs_dropout_prob={a_do}")
    if not (h_do > 0 and a_do > 0):
        # Not fatal for the base artifact (deterministic), but MC-Dropout σ would be null.
        print("[embeddings] WARNING: dropout p is not >0 — MC-Dropout σ would be null.")

    descriptions = generate_descriptions(conn)
    ine5s = sorted(descriptions)
    docs = [PREFIX_DOC + descriptions[i] for i in ine5s]

    # Deterministic base vectors: model is in eval() by default (dropout OFF).
    vecs = model.encode(docs, normalize_embeddings=True, convert_to_numpy=True)
    assert vecs.shape[1] == EMB_DIM, f"expected {EMB_DIM}-dim, got {vecs.shape[1]}"

    rows = [(ine5, [float(x) for x in vec.tolist()]) for ine5, vec in zip(ine5s, vecs, strict=True)]

    ARTIFACT_PARQUET.parent.mkdir(parents=True, exist_ok=True)

    wconn = conn.cursor()  # separate cursor; do not disturb caller's transaction
    wconn.execute("CREATE OR REPLACE TABLE _emb_out (ine5 VARCHAR, emb DOUBLE[])")
    wconn.executemany("INSERT INTO _emb_out VALUES (?, ?)", rows)
    wconn.execute(
        "COPY (SELECT ine5, emb FROM _emb_out ORDER BY ine5) TO ? (FORMAT PARQUET)",
        [str(ARTIFACT_PARQUET)],
    )
    wconn.execute("DROP TABLE _emb_out")

    meta = {
        "model": MODEL_NAME,
        "revision": MODEL_REVISION,
        "dim": EMB_DIM,
        "prefix_doc": PREFIX_DOC,
        "prefix_query": PREFIX_QUERY,
        "n": len(rows),
        "generated_note": (
            f"Base (deterministic, dropout OFF) e5-small embeddings for the "
            f"{len(rows)} Berguedà munis. Regenerated locally via "
            f"embeddings.regenerate_artifact() on "
            f"{datetime.now(UTC).strftime('%Y-%m-%d')}. "
            f"CPU float ops are not bit-identical across machines; compare with a "
            f"tolerance, not equality. dropout: hidden={h_do}, attention={a_do}."
        ),
    }
    ARTIFACT_META.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"[embeddings] wrote {ARTIFACT_PARQUET} ({len(rows)} rows) + {ARTIFACT_META.name}")
    return ARTIFACT_PARQUET
