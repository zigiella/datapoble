# DATA CARD — Berguedà geospatial substrate (Phase 0a)

Scope: the **31 municipalities of the Berguedà comarca**. Isolated experiment; does not
touch `packages/ai`.

## Committed source files (exact repo-relative paths)

| Purpose | Path | Used for |
|---|---|---|
| Pernocta bands + official ETCA | `data/web/pernocta-catalunya.json` (key `munis` → per ine5) | `estimacio`, `rang_baix`, `rang_alt`, `padro`, `tipus`, `nom`, `etca_oficial` |
| Register for <1000 hab | `data/territorial/senyal_sub1000.csv` | `register` when `etca_oficial` is null |
| Mirror municipalities | `data/web/municipis-mirall.json` | `twin` table |
| Geometry + canonical 31 set | `packages/web/static/geo/bergueda-municipis.geojson` | `geom` / `geom_geojson`, and the definition of "the 31" |
| ICAEN domestic electricity | `data/marts/mart_consum_electric.parquet` | `icaen_serie` (sector `USOS DOMESTICS`, 2013–2024) |

Note: `data/territorial/comarca_vegueria.csv` maps *comarca → vegueria* (not ine5 → comarca),
so it is **not** used to assign munis to Berguedà. The Berguedà set is taken directly from the
tracked `bergueda-municipis.geojson`, which contains exactly 31 features. `comarca` is therefore
set to the constant `"Berguedà"` by construction.

## Computed Berguedà register split

The register is **computed at build time**, never hardcoded. Rule:

- `etca_oficial` not null → `oficial`
- else look up ine5 in `senyal_sub1000.csv` → use its `registre` (`senyal_mes` | `senyal_menys` | `soroll`)
- else → `indeterminat` (counted, never silently dropped)

Result for the 31 Berguedà munis (sums to 31, zero `indeterminat`):

| register | count |
|---|---|
| oficial | 9 |
| senyal_mes | 3 |
| senyal_menys | 1 |
| soroll | 18 |
| indeterminat | 0 |
| **total** | **31** |

The earlier Catalunya-wide "99" signal figure does **not** apply to Berguedà — this is the
recomputed comarca-local split.

## Model caveat

- The pernocta estimate is a **Nivell C** model output (r² ≈ 0.41 on held-out data).
- `sigma` here = `(rang_alt − rang_baix) / 2`, i.e. half the published held-out **p10–p90** band —
  a spread indicator, not a formal standard deviation.
- `etca_oficial` (net annual ETCA) is an *official* figure but is **not** the same quantity as our
  pernocta estimate; treat the `oficial` register as "we defer to the official number here", not as
  a validation of the model. The `soroll` register means the muni's band is dominated by noise
  (margin too wide to claim signal).

## Extension availability (this box)

- DuckDB `spatial`: **available** — geometry stored as native `GEOMETRY`; `neighbors()` uses
  `ST_Intersects`.
- DuckDB `fts`: **available** — FTS index built on `municipi(ine5, nom)`; `name_search()` uses BM25.
- The build is offline-safe: if either extension fails to install, geometry falls back to
  `geom_geojson` text and search falls back to `LIKE`, and the build does not fail.

## Honesty note

No invented numbers; every value traces to a committed source file listed above.
Munis present in the geometry but absent from a source are marked `indeterminat` and counted,
never fabricated.
