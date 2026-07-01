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

### 0b implementation (what shipped)

Three new modules under `src/datapoble_geo_rag/`:

- **`descriptions.py` (torch-free)** — `generate_descriptions(conn) -> {ine5: str}`
  builds one Catalan document per muni from the `municipi` table only (nothing invented
  beyond its fields). Numbers render as integers; `tipus` underscores become spaces. One
  fixed template per `register`:
  - `oficial` → "… Registre oficial: ≥1.000 hab amb dada ETCA d'Idescat (…) — el model
    es pot contrastar amb la font oficial."
  - `senyal_mes` → "… per sobre del padró (…). Registre senyal: <1.000 hab; l'interval
    exclou el padró, sense validació oficial."
  - `senyal_menys` → same, "per sota del padró (…)".
  - `soroll` → "… Registre soroll: el rang inclou el padró (…) — l'estimació no es
    distingeix del propi marge en aquest poble."

- **`embeddings.py` (the ONLY torch module)** — pins the model revision in
  `MODEL_REVISION` (currently
  `614241f622f53c4eeff9890bdc4f31cfecc418b3` for `intfloat/multilingual-e5-small`),
  verifies dropout p>0 (confirmed `hidden=0.1`, `attention=0.1`), and
  `regenerate_artifact(conn)` writes the committed base vectors (dropout OFF,
  deterministic, `passage:` prefix, normalized). Also `embed_query(text)` (prepends
  `query:`) for local use. Never imported by the build or the search ranking path.

- **`search.py` (torch-free)** — `load_embeddings(conn)` loads the committed parquet into
  `municipi_emb(ine5 VARCHAR, emb FLOAT[384])` if present (silently skipped if absent, so
  0a still builds). `semantic_search(conn, query_vec, k=5) -> [(ine5, nom, score)]` ranks
  by `array_cosine_similarity`. It takes a **ready** vector; query embedding
  (`embeddings.embed_query`, torch) stays out of this path.

`build()` auto-loads `municipi_emb` when the artifact exists and records
`embeddings=1|0` in `_substrate_meta`.

### Committed artifact

- `data/embeddings-e5-small.parquet` — `(ine5 VARCHAR, emb DOUBLE[])`, 31 rows × 384 dim
  (~73 KB). Committed as the deterministic source of truth.
- `data/embeddings-e5-small.meta.json` — `{model, revision, dim, prefix_doc,
  prefix_query, n, generated_note}`. The `.gitignore` ignores only `*.duckdb`; these two
  artifacts are explicitly kept tracked.

### Regenerate (local, deliberate — never in CI)

```sh
pip install -r requirements-embeddings.txt          # torch CPU + sentence-transformers
python -c "from datapoble_geo_rag.build import build; \
from datapoble_geo_rag import embeddings; embeddings.regenerate_artifact(build(None))"
```

This re-downloads the pinned-revision weights, re-embeds the 31 documents, and rewrites
the parquet + meta. CPU float ops are not bit-identical across machines — compare with a
tolerance (`np.allclose`, atol ≈ 1e-4), never equality.

### Tests / CI

`tests/test_embeddings.py` — the offline tests (descriptions, artifact shape, meta
revision, `municipi_emb` load, cosine **self-retrieval** rank-1) read only committed
artifacts and the torch-free path; these are what the `geo-rag` CI job runs. One
torch-guarded test (`pytest.importorskip("torch")`) embeds a live query and **skips** in
CI. Retrieval is phrasing-sensitive on these 31 short docs: a query echoing the document
wording surfaces the intended register; a loose paraphrase may not.
