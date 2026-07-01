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

### Collision notes (honest rendering of a source error)

The Nivell C model gives **identical** `(estimacio, rang_baix, rang_alt)` to different munis
(54 groups Catalunya-wide). Rendering the number naked would propagate a source error in
silence, so `generate_descriptions` reads `pernocta-catalunya.json` and **appends a warning**
to any Berguedà muni whose estimate is shared (**12 of 31**). Register-aware:

- **oficial** (the serious case — the label promises "contrastable", yet the model collapses
  two towns Idescat separates): names the peer(s) + cites the distinguishing ETCA, e.g.
  Guardiola de Berguedà ↔ la Pobla de Lillet (852=852; ETCA 1005 vs 1121).
- **senyal / soroll**: states the estimate is shared by N Catalunya munis and is not
  muni-specific until fixed at source.

Not a 0b defect (the substrate is rendered faithfully); the structural cause + the extent
across the oficial register Catalunya-wide are the **handoff to Sondeig**
(`docs/experiment-rag-geo/02-handoff-sondeig-collisio.md`). Guarded by `tests/test_collision.py`.

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

## Phase 1 — the retriever + committed query bank

### Query bank (a committed artifact, torch-free to consume)

| Path | Content |
|---|---|
| `data/fase1-bank.json` | ~8 hand-written entries: `{id, query (Catalan), kind, anchor_ine5, expected:{targets, expect_tie, tie_group}, query_vec:[384 floats]}` |

- `query_vec` is **committed** (each = `embeddings.embed_query(query)`, e5 `query:` prefix,
  384-dim, normalized) so the eval and CI run **torch-free** on the bank.
- `kind ∈ {normal_spatial, normal_semantic, collision_oficial, collision_soroll}`. Minimum
  coverage (from the contract): a spatial query (`veïns de Berga`, anchor = Berga, targets =
  its real `ST_Intersects` neighbours), a semantic query, the `collision_oficial` case
  (Guardiola de Berguedà / la Pobla de Lillet, **no separating anchor** → must report the
  tie and that Idescat separates them, ETCA 1005 vs 1121), and a `collision_soroll` case
  (Gósol / Saldes — groups of 3 Catalunya-wide).
- Introduces **no new numbers**: it holds only queries, expected ine5 targets, and the
  committed 384-float vectors (a function of the queries + the pinned model). Regenerating is
  a deliberate local step (needs torch); CPU float ops are not bit-identical across machines.
- `.gitignore` tracks this file (only `*.duckdb` is ignored).

### The tie = the abstention of ordering

The retriever reuses the substrate (native `GEOMETRY`, FTS, `municipi_emb`) and adds one
honest gesture: it does **not** break a tie the data can't break. A **collision tie** is
reported straight from `descriptions._collision_groups()` (the same identical-estimate groups
already flagged in the descriptions) — the shared figure is **never** rendered as
muni-specific, and for an `oficial` group the note cites the distinguishing ETCA. A **score
tie** (RRF #1/#2 within `EPS`) is reported, not ordered by phrasing noise. This is the same
abstention-calibration KPI as Phase 3, one level up — a well-reported tie is an abstention
hit; a false tie-break hiding the tie is a failure. See `docs/experiment-rag-geo/03-fase1-recuperador.md`.

## Phase 2 — the distinguishability rule (one rule, two uses)

Phase 2 **generalises** the Phase-1 tie: the exact collision (identical estimate+range) and
**band overlap** are the same phenomenon at two resolutions. One rule serves both uses so
the system never contradicts itself.

**The rule (torch-free, pure — `distinguish.py`).** Two munis can be **ordered** only if the
distance between their estimates **exceeds the combined band uncertainty**. Concretely,
`distinguishable(a_low, a_high, b_low, b_high, min_gap=0.0)` is True iff the p10–p90 bands
are disjoint beyond `min_gap`. The default `min_gap=0.0` means **any overlap → not
distinguishable** — the clean, auditable criterion on the **already-calibrated** band (78.4%
coverage), introducing **no new number/parameter**. A finer `min_gap` is a **declared
methodology parameter, never truth** (same status as the `|ETCA|≥5%` threshold).

**Use 1 — comparison (`compare.py`).** `compare(conn, a, b)` calls the shared
`distinguishable` (no reimplemented overlap): disjoint bands → order by `estimacio`;
overlapping bands → abstain from ordering. The exact collision (Guardiola de Berguedà ↔ la
Pobla de Lillet, identical `[726,1037]`) resolves through the **same** function at distance
zero — not a special path.

**Use 2 — σ modulation (`compare.answer`).** The same σ (half the calibrated p10–p90 band)
sets the tone: `ferm` for a narrow relative band, `prudent` for a wide one; `soroll` is
always prudent. `s_score = estimacio − λ·sigma` (`λ=1.0`). This is the **mean-variance
(Markowitz)** risk penalty — **not** a bespoke formula; the contribution is that σ is a
**real reliability band**, not the model's introspective variance (see the `sigma` caveat
above).

**No new sources or numbers.** Phase 2 adds only logic + a query-vector-free bank
(`data/fase2-bank.json`) holding ine5 pairs/queries and expected outcomes; every band it
reads already lives in the `municipi` table (from `pernocta-catalunya.json`). See
`docs/experiment-rag-geo/04-fase2-distingibilitat.md`. Guarded by `tests/test_distinguish.py`
and `eval2` (5/5 pass; 2/2 non-distinguishable cases reported as not-orderable).

## Honesty note

No invented numbers; every value traces to a committed source file listed above.
Munis present in the geometry but absent from a source are marked `indeterminat` and counted,
never fabricated. The 0b descriptions add no numbers — they only reword substrate fields;
semantic retrieval over these 31 short docs is phrasing-sensitive and is reported as-is
(no cherry-picked query), consistent with "the observatory that knows what it doesn't know".
