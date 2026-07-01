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
