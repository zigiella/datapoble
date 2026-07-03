# datapoble-geo-rag

An **isolated** geospatial-RAG experiment over the **31 Berguedà municipalities**: a
DuckDB substrate built from committed data sources (Phase 0a), local descriptions +
embeddings (Phase 0b), and a spatial retriever whose only honest addition is that it
**reports ties it cannot break** instead of inventing a winner (Phase 1).

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

## Generative layer (optional extra) — contracte 08

The **generative layer** (contract `docs/experiment-rag-geo/08-contracte-capa-generativa.md`:
the delta against the deterministic 21/21 — not the σ-vs-σ star sub-experiment, which is
MC-Dropout on local embeddings and needs no API) needs an **LLM generation +
blind-validation** step, via the Anthropic API — local runs only, never in per-PR CI.

- **Models** (exact IDs, pinned snapshots — don't append date suffixes):
  - **Generator:** `claude-sonnet-5` — the realistic production-tier model; default
    sampling (stochastic; N=5 passes capture it). Intro pricing $2/$10 per MTok until
    2026-08-31, then $3/$15 (Sonnet 4.6 is now legacy).
  - **Blind validator:** `claude-haiku-4-5` at `temperature=0` — a **different** model
    (less-correlated blind spots), cheap, consistent. Haiku 4.5 / Sonnet 4.6 still accept
    `temperature`; Opus 4.7+/Fable 5 reject it. Don't set `effort` on Haiku — it errors.
- **Isolation:** the `[generativa]` extra (`anthropic`) **never** reaches Render (which
  builds only `packages/ai`), same discipline as `[embeddings]`.

### Install & key
```sh
pip install -e ".[generativa]"
cp .env.example .env      # then put the real key in .env (gitignored)
```
The `anthropic` SDK reads **`ANTHROPIC_API_KEY`** from the environment automatically
(`anthropic.Anthropic()`). Keep it in a gitignored `.env` (or `~/.secrets/`) — **never**
in this public repo, never in logs; write raw responses to a gitignored dir.

### Infra policy
- **Per-PR CI stays offline:** the `geo-rag` job installs neither extra, downloads no
  weights, and **calls no API**. API-needing tests use an env guard —
  `@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), ...)` (the analogue of
  `importorskip("torch")`). **No GitHub Actions secret** for the key → nothing to leak.
- **Reproducibility → provenance, not a seed.** There is no `seed` param and
  `temperature=0` is **not** bit-deterministic. Log per trial: `response.model`,
  `response._request_id`, `usage`, and the pinned SDK version. The record of truth is the
  committed per-trial JSON + raw responses — compare with tolerance / human review, not
  byte-equality (same spirit as the embeddings artifact).
- **Retries/limits:** the SDK's default `max_retries=2` (429/5xx/network, exponential
  backoff) is enough for ~340 calls/pass — no extra infra.
- **Cost trim (optional):** the generator reuses a frozen prompt across passes → cache
  the stable prefix (`cache_control: {"type": "ephemeral"}`); Sonnet's min cacheable
  prefix is ~2048 tokens or it silently won't cache. Or use the Batch API (−50%, async).

## Phase 1 — the spatial retriever (tie = abstention)

**Contract:** `docs/experiment-rag-geo/03-fase1-recuperador.md`.

Inability to distinguish appears at three heights and the honest system makes the **same
gesture** at each — it does **not** break a tie the data can't break, it **reports** it:

| height | name | gesture |
|---|---|---|
| data | **soroll** | "I can't tell this number from my own margin" |
| muni | **col·lisió** | "I can't tell this town from that one" |
| retrieval | **empat** | "I can't tell which document comes first" |

An unbreakable tie is the **abstention of ordering** — the same abstention-calibration
KPI as Phase 3, one level up. A retriever that always returns a clean winner over tied
data lies with confidence.

### `retrieval.py` (torch-free — the ranking path never imports torch)

`retrieve(conn, query_text, query_vec, anchor_ine5=None, k=5) -> dict`, in order:

1. **Hard spatial filter first.** `detect_anchor(conn, query_text)` matches a muni
   proper-name (via `municipi.nom`, longest surface form first, incl. de-articled
   "la Pobla de Lillet"). With an anchor, the candidate set = anchor + its spatial
   neighbours (`ST_Intersects`); otherwise = all 31 (comarca). This narrows **before**
   any scoring.
2. **Up to three ranked lists** over the candidates: (a) **spatial** (anchor only) by
   centroid distance `ST_Distance(ST_Centroid(geom), anchor)`, nearest first; (b)
   **semantic** cosine over `municipi_emb` (`array_cosine_similarity`); (c) **name** via
   FTS `match_bm25(nom)`.
3. **RRF fusion of ranks:** `score(d) = Σ_lists 1/(60 + rank_l(d))` (Cormack 2009) —
   fuse **ranks**, not raw scores.
4. **Tie detection** (the only addition):
   - **collision tie (data):** if the top candidate is in a `descriptions._collision_groups()`
     group, report the **whole** group (marking which members are in the 31); the note says
     the number is **not** muni-specific. For an `oficial` group it also cites that Idescat
     **does** separate them (ETCA 1005 vs 1121 for Guardiola ↔ la Pobla de Lillet).
   - **score tie (RRF):** if the #1/#2 fused scores are within `EPS` (relative gap < 0.02),
     the pair is reported tied — **not** ordered by phrasing noise.

Returns `{candidates:[{ine5,nom,score,register,estimacio,in_collision}], anchor,
n_candidates, tie:{is_tie,kind,group,note}}`. It never presents a shared/collision figure
as muni-specific and never imposes an order the data doesn't support.

### Query bank + committed query vectors

`data/fase1-bank.json` — ~8 hand-written entries `{id, query (Catalan), kind, anchor_ine5,
expected:{targets, expect_tie, tie_group}, query_vec:[384 floats]}`. It covers a normal
**spatial** query (`veïns de Berga`, anchor = Berga, targets = its real neighbours), a
normal **semantic** query, the **collision_oficial** case (Guardiola / la Pobla de Lillet,
no separating anchor → must report the tie + ETCA), and a **collision_soroll** case
(Gósol, Saldes → group of 3). The `query_vec`s are **committed** so eval/CI run torch-free.
The `.gitignore` tracks this file (only `*.duckdb` is ignored).

Regenerate the vectors (local, deliberate — needs torch; never in CI):

```sh
pip install -r requirements-embeddings.txt
# then run the small generator (embeds each query via embeddings.embed_query and rewrites
# data/fase1-bank.json). See docs/experiment-rag-geo/03-fase1-recuperador.md for the entries.
```

Each entry's `query_vec = embeddings.embed_query(query)` (the e5 `query:` prefix, 384-dim,
normalized). CPU float ops are not bit-identical across machines — regenerate and compare
with a tolerance, not equality.

### `eval.py` (torch-free)

`python -m datapoble_geo_rag.eval` runs `retrieve()` over the committed bank and scores each
entry against the contract: **normal** passes if an expected target is in top-k;
**collision_\*** passes only if `tie.is_tie` is True, `tie.group` reports the sharing munis,
and no single member is presented as a clean winner (fails if it hides the tie). It prints a
per-entry report, a `n pass / n fail` summary, and an **abstention-of-ordering** line
(collision cases correctly reported as ties). Current run: **8/8 pass, 4/4 collision cases
reported as ties**.

### Phase-1 tests

`tests/test_retrieval.py` (offline, torch-free — uses the committed bank vectors): the
anchor spatial filter narrows candidates (< 31, all within the 31); `collision_oficial` →
tie with group `{Guardiola, la Pobla de Lillet}` and an ETCA-separation note;
`collision_soroll` → tie; a normal entry → target in top-k with no false collision tie; an
RRF unit check (`rrf_score(r1,r2) == 1/(60+r1)+1/(60+r2)`). One torch-guarded test embeds a
live query and **skips** in CI.

## Phase 2 — the distinguishability rule (one rule, two uses)

**Contract:** `docs/experiment-rag-geo/04-fase2-distingibilitat.md`.

Phase 2 does not add a new function — it **generalises** Phase 1. Phase 1's collision tie
handles the **exact** collision (two munis, identical number). **Band overlap** is the
same phenomenon in continuous form, more common and previously invisible. The two show up
as **one rule**:

> Two munis can be **ordered** only if the distance between their estimates **exceeds their
> combined band uncertainty**. If the p10–p90 bands overlap, they are **not
> distinguishable** and the system **abstains from ordering** — the same gesture as the
> Phase-1 collision tie, but by **overlap** instead of by **identity**. The exact collision
> is this rule at **distance zero** (identical bands fully overlap).

### `distinguish.py` (torch-free, pure — numbers in, bool out)

The single shared rule, called by BOTH uses and by the tests so they can never contradict:

- `overlaps(a_low, a_high, b_low, b_high)` — `max(a_low,b_low) <= min(a_high,b_high)`.
- `distinguishable(a_low, a_high, b_low, b_high, min_gap=0.0)` — True iff the intervals are
  disjoint beyond `min_gap`. The default `0.0` means **any p10–p90 overlap → not
  distinguishable**: the clean, auditable criterion from the contract, on the
  **already-calibrated** band (78.4% coverage), with **no new parameter**. A finer
  `min_gap` is a **declared methodology parameter, never truth** (like `|ETCA|≥5%`).

### Use 1 — comparison between munis (`compare.py`, torch-free)

`compare(conn, ine5_a, ine5_b) -> {distinguishable, higher, lower, note}` reuses
`distinguish.distinguishable` (no reimplemented overlap). If distinguishable → order by
`estimacio`; if not → `higher/lower = None` and an abstention note (*"els seus intervals
p10-p90 s'encavalquen (…); no els puc ordenar amb confiança"*).
`answer_comparison(conn, query_text)` detects the **two** muni names in the query
(`retrieval.detect_anchors`, up to two) and routes to `compare()`; if a comparative query
names one/zero munis it says so honestly rather than inventing an opponent.

### Use 2 — σ modulation on one muni (`compare.answer`, torch-free)

`answer(conn, ine5) -> {ine5, nom, register, estimacio, band, sigma, rang_rel, tone,
s_score, text}`. The **same σ** (the band) sets the tone: **`ferm`** when the relative band
is narrow, **`prudent`** (wide range) when large; `soroll` is always prudent (its band
includes the padró). `s_score = estimacio − LAMBDA·sigma` with `LAMBDA=1.0`. **Honest
note:** `S = μ − λσ` is the standard **mean-variance (Markowitz)** risk penalty, **not** a
bespoke formula — our contribution is that σ is a **real reliability band** (half the
calibrated p10–p90), not the model's introspective variance. The `text` is a short Catalan
answer whose tone (firm vs hedged) and width reflect σ.

### Unification with Phase 1 (no duplicated overlap logic)

The Phase-1 exact-collision tie and the Phase-2 comparison both express "not orderable"
through `distinguish.distinguishable`: `retrieval._detect_tie` asserts the collision group's
identical bands are NOT distinguishable (the distance-zero limit) via the shared function,
so the two phases can't drift apart. Only the orderability **predicate** is shared; the
richer collision **note** (peers by exact-estimate group + ETCA) stays. The list-join
polish is a shared helper `descriptions.join_noms` (`"A, B i C"`, not `"A i B i C"`) used by
the collision/tie notes and the comparison notes.

### Bank + eval2

`data/fase2-bank.json` (torch-free — **no query vectors**; comparison is by band, detection
by name): entries `{id, kind, munis|query, expected}`. Required cases (contract, day 1):
`compare_separated` (Berga vs Gironella → order), `compare_overlap` (Olvan vs la Pobla de
Lillet → not distinguishable), `sigma_small` (Berga → `ferm`), `sigma_large` (Gósol soroll →
`prudent`), `exact_collision_limit` (Guardiola de Berguedà vs la Pobla de Lillet →
`distinguishable=False` via the **same** rule at distance zero). Pairs were picked by
inspecting the substrate bands so "separated" and "overlap" are genuinely so.

`python -m datapoble_geo_rag.eval2` runs the bank, scores per contract (orders only when
distinguishable; abstains on overlap; tone reflects σ), and prints an
**abstention-of-ordering** line. Current run: **5/5 pass, 2/2 non-distinguishable cases
(overlap + exact collision) reported as not-orderable**.

### Phase-2 tests

`tests/test_distinguish.py` (offline, torch-free): `distinguishable()` unit (disjoint True;
overlap False; **identical bands False** = the Phase-1 limit; touching False; declared
`min_gap`); `compare()` orders separated + abstains on overlap; `answer()` tone `ferm` for a
narrow-band muni and `prudent` for a soroll muni; `answer_comparison` detects two names and
is honest with one; exact collision (Guardiola/la Pobla de Lillet) → `distinguishable`
False **through the shared function** (asserts the substrate bands are identical and that
the pure `distinguishable` call agrees); `s_score == μ − λσ`.
