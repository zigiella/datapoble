# datapoble-geo-rag

Phase 0a of an **isolated** geospatial-RAG experiment: build a DuckDB substrate for the
**31 Berguedà municipalities** from committed data sources.

This package is self-contained. It does **not** import or depend on `packages/ai`.

## What it is

A single-command build that produces `data/bergueda.duckdb` with:

- `municipi` — one row per Berguedà muni (ine5, nom, comarca, tipus, padró, pernocta
  estimate + band, `sigma`, `rang_rel`, `etca_oficial`, `register`, geometry).
- `twin` — mirror municipalities (from `municipis-mirall.json`).
- `icaen_serie` — ICAEN domestic-electricity series 2013–2024 (from the mart parquet).
- native `GEOMETRY` (DuckDB `spatial`) + an FTS index on proper names.

Every value traces to a committed source file — see [`DATA_CARD.md`](./DATA_CARD.md).
No invented numbers.

## Build

From this directory, using the repo's `.venv`:

```sh
../../.venv/Scripts/python -m datapoble_geo_rag.build   # Windows
# or:  python -m datapoble_geo_rag.build   (with src on PYTHONPATH)
```

It writes `packages/geo-rag/data/bergueda.duckdb` and prints a summary:
total munis, the register split, geometry/sigma counts, twin/icaen rows, and
whether the `spatial` / `fts` extensions loaded.

You can also build an in-memory DB programmatically:

```python
from datapoble_geo_rag import build, name_search, neighbors
conn = build(None)                 # in-memory
name_search(conn, "Berga")         # -> [('08022', 'Berga'), ...]
neighbors(conn, "08022")           # touching munis within the 31 (None if no spatial)
```

## Test

```sh
../../.venv/Scripts/python -m pytest -q
```

The smoke test asserts the 31-count, the register split sums to 31 with no
`indeterminat`, band/sigma sanity, name search, spatial adjacency within the set,
and that a few munis' bands byte-match `pernocta-catalunya.json`.

## Embeddings (optional extra) — Phase 0b

Semantic search over the municipality descriptions uses a **local** model (no hosted
API). Two hard reasons, not cost: the "σ" sub-experiment needs **MC-Dropout**
(stochastic passes with dropout active — no embedding API exposes that), and CI must
stay **offline, reproducible and secret-free** on a public repo.

- **Model:** `intfloat/multilingual-e5-small` (MIT, 384-dim, CPU-friendly; `query:` /
  `passage:` prefixes). Pin the **revision** (HF commit SHA), not just the name.
- **Runs on CPU on a normal laptop** (~117M params; 31 docs + MC-Dropout passes take
  seconds; ~1–1.5 GB one-time install). No GPU, no pod.

### Install (choose one)

Reproducible / any OS / CI (forces the CPU `torch` wheel):

```sh
pip install -r requirements-embeddings.txt
```

Or, on **Windows** (where PyPI's `torch` is already CPU-only):

```sh
pip install -e ".[embeddings]"
```

> ⚠️ On **Linux** do NOT use the extra directly — PyPI's `torch` there is the ~2.5 GB
> **CUDA** build. Use `requirements-embeddings.txt` (it pins the CPU index).

### Infra policy

- **`[embeddings]` never ships to production** — the Render image builds only
  `packages/ai`, so `torch` stays out of the deployed API.
- **Commit the base embeddings artifact** (31×384 floats ≈ 47 KB) as the deterministic
  source of truth. Regenerating is a deliberate local step, not the default CI.
- **Per-PR CI stays offline**: the `geo-rag` job installs only base deps
  (`duckdb` + `pytest`) and runs on committed artifacts — it does **not** install
  `torch` or download weights.
- **Reproducibility:** pin `torch` + `sentence-transformers` + the model revision and
  fix seeds. CPU float ops are **not** bit-identical across machines, so if you ever
  re-generate and compare, use a tolerance (`np.allclose`, atol ≈ 1e-4), not equality.
- **MC-Dropout viability:** confirm the model config has **dropout p>0**
  (`hidden_dropout_prob`, `attention_probs_dropout_prob`) or σ comes out null. e5-small
  (MiniLM-based) ships p=0.1 — verify it on the pinned revision before committing.
