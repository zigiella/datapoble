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

## Phase 0b — descriptions + embeddings artifact

### Generated descriptions (derived, not a new source)

`descriptions.generate_descriptions(conn)` produces one Catalan document per muni from the
**`municipi` table only** — no new external source. Every number in a description already
lives in the substrate (`nom`, `tipus`, `estimacio`, `rang_baix`, `rang_alt`, `padro`,
`etca_oficial`) and is rounded to an integer for display; `tipus` underscores render as
spaces. Fixed template per `register`:

| register | shape (numbers as integers) |
|---|---|
| `oficial` | "{nom} (Berguedà) · {tipus}. Presència estimada {estimacio} (rang {rang_baix}–{rang_alt}). Registre oficial: ≥1.000 hab amb dada ETCA d'Idescat ({etca_oficial}) — el model es pot contrastar amb la font oficial." |
| `senyal_mes` | "… (rang …), per sobre del padró ({padro}). Registre senyal: <1.000 hab; l'interval exclou el padró, sense validació oficial." |
| `senyal_menys` | same as `senyal_mes` but "per sota del padró ({padro})". |
| `soroll` | "… Registre soroll: el rang inclou el padró ({padro}) — l'estimació no es distingeix del propi marge en aquest poble." |

### Committed embeddings artifact

| Path | Content |
|---|---|
| `data/embeddings-e5-small.parquet` | `(ine5 VARCHAR, emb DOUBLE[])`, 31 rows × 384-dim base vectors (deterministic, dropout OFF, `passage:`-prefixed, normalized) |
| `data/embeddings-e5-small.meta.json` | `{model, revision, dim:384, prefix_doc:"passage: ", prefix_query:"query: ", n:31, generated_note}` |

- **Model:** `intfloat/multilingual-e5-small` (MIT, 384-dim), **pinned revision**
  `614241f622f53c4eeff9890bdc4f31cfecc418b3`.
- **Dropout confirmed p>0** on the pinned revision (`hidden_dropout_prob=0.1`,
  `attention_probs_dropout_prob=0.1`) — precondition for the later MC-Dropout σ experiment.
- The artifact is the deterministic **source of truth**; `torch`/`sentence-transformers`
  are used ONLY to regenerate it locally (see README "Regenerate"), never in CI.
- Reproducibility caveat: CPU float ops are not bit-identical across machines — compare
  re-generated vectors with a tolerance (`np.allclose`, atol ≈ 1e-4), not equality.

## Honesty note

No invented numbers; every value traces to a committed source file listed above.
Munis present in the geometry but absent from a source are marked `indeterminat` and counted,
never fabricated. The 0b descriptions add no numbers — they only reword substrate fields;
semantic retrieval over these 31 short docs is phrasing-sensitive and is reported as-is
(no cherry-picked query), consistent with "the observatory that knows what it doesn't know".
