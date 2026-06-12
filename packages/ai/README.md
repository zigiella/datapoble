# ai · Brúixola — traceable text-to-SQL

Text-to-SQL **traceable** over the datapoble semantic contract
(`semantic/metrics.yml`), via OpenRouter (model-agnostic), with **provenance
always** and **offline-first** so it runs and is tested without any API key.
Answers in the active locale (ca/es).

> Scope: this package exposes a **function and an HTTP endpoint**. It does **not**
> build the "Pregúntale" UI — that's Mirador. It does **not** define metrics —
> that's Talaia's contract; here we only *consume* it.

---

## What it does

A natural-language question is turned into a **read-only, parametrized SQL**
query over the `mart_*` tables, and the answer always carries its provenance —
**source, date, formula and the exact query** — in the active locale. Anything
outside the catalog is **refused with a machine-readable reason**, never
hallucinated (refusal-as-a-feature).

```python
from datapoble_ai import Agent

with Agent() as agent:                       # offline by default (no key needed)
    ans = agent.ask("Quin municipi té més exposició turística-residencial?", locale="ca")
    print(ans.text)
    # El municipi amb més Exposició (IETR) és
    # Castellar de n'Hug (100 0-100). Font: … indicador derivat … Fórmula: 0.5*A_resid + 0.5*B_turis …
    print(ans.provenance.to_dict())          # source · date · formula · query · note
```

Three question shapes are understood by the deterministic router:

| Shape         | Example (ca)                                            | SQL                          |
|---------------|---------------------------------------------------------|------------------------------|
| `lookup`      | *Quants habitatges no principals té Castellar de n'Hug?* | `SELECT … WHERE municipi=$m` |
| `ranking`     | *Quin municipi té més IETR?* / *…menys establiments?*    | `… ORDER BY col DESC LIMIT 1`|
| `correlation` | *Quina relació hi ha entre l'índex i els residus?*       | join + Spearman over rows    |

---

## Architecture

```
question (NL, ca/es)
        │
        ▼
   LLMBackend  ──────────────┐
   ├─ OfflineBackend  (default, deterministic — ports the prototype ask.py)
   └─ OpenRouterBackend (OpenAI-compatible; needs OPENROUTER_API_KEY)
        │  picks ONE catalog metric + intent (enum-constrained tool-use)
        ▼
   Router.execute_intent      ← single guarded executor (both backends)
        │  parametrized, read-only SQL
        ▼
   Warehouse (DuckDB, read-only)   ← only mart_* tables, never raw
        │
        ▼
   Answer + Provenance  (source · date · formula · query · note), localized
```

Key idea: **the LLM never writes SQL**. It only *chooses* a metric and an intent
from enums derived from the contract; the same `Router` then builds the
parametrized query and the provenance. So the guardrails hold regardless of
backend.

### Modules (`src/datapoble_ai/`)

| File           | Responsibility |
|----------------|----------------|
| `catalog.py`   | Read-only loader of `semantic/metrics.yml`; locale-aware label/unit/synonym access; `planned` handling. |
| `warehouse.py` | Read-only DuckDB over the marts; SQL guardrails (SELECT/WITH only, no DDL/DML, no multi-statement, no `raw`). |
| `router.py`    | Deterministic NL→intent→parametrized SQL + provenance (the offline baseline). |
| `llm.py`       | `LLMBackend` interface + `OfflineBackend` (default) + `OpenRouterBackend` (behind the interface). |
| `agent.py`     | `Agent` facade; backend selection (`auto`/`offline`/`openrouter`). |
| `api.py`       | FastAPI app (`/ask`, `/metrics`, `/health`) — the endpoint Mirador calls. |
| `cli.py`       | `datapoble-ai "…" --locale ca` smoke CLI. |
| `i18n.py`      | ca/es phrase templates + ca/es number formatting. |
| `types.py`     | `Answer` / `Provenance` / refusal enums (the response contract). |

---

## Honest boundaries — what runs for real today vs scaffold

**Runs for real, offline, no key (covered by the test/eval suite):**
- Catalog loading from the actual `semantic/metrics.yml`.
- The deterministic router: lookup / ranking / correlation, ca + es.
- All SQL guardrails (read-only, contract tables only, no `raw`, parametrized).
- Provenance assembly from the contract (source/date/formula/query/note),
  including derived metrics surfacing their upstream `origin_source`.
- Refusals with machine-readable reasons (out-of-catalog, planned, unknown
  municipality, guardrail violation).
- FastAPI endpoint and the CLI.
- The eval gate.

**Scaffold / inert until the secret arrives:**
- `OpenRouterBackend` is fully wired (system prompt, enum-constrained tool
  schema, dispatch back into the guarded `Router`) but **does not run without
  `OPENROUTER_API_KEY`** — calling free text it can't resolve deterministically
  without the key raises a clear `RuntimeError` instead of faking an answer. The
  `openai` client is an *optional* dependency, imported lazily only on that path.

The **cost controls** (deterministic-first, question cache, rate-limit, hard
spend cap) and the **multi-model eval script** described below are implemented
and tested **offline** (no key); only the *live* LLM calls they gate need the
secret.

**Data boundary:** Sondeig has now industrialised the marts, so `data/marts/`
holds **real** `mart_municipi.parquet` / `mart_electoral.parquet`, and the
runtime agent/API query those (provenance `is_fixture: false`). The seed
**fixtures** in `fixtures/` are retained as the pinned input for the
deterministic offline **gate** (the test suite + `evals/run_evals.py` build
their warehouse with `use_fixtures=True`), so the gate exercises the router
logic against a fixed distribution and is decoupled from how the real marts
evolve. In the fixtures, two rows are *real* (Castellar de n'Hug, Berga —
transcribed from `docs/data-sources.md` §8, verified 2026-06-01); the rest are
synthetic placeholders so ranking/correlation have a distribution. See
`fixtures/README.md` and "Pointing at the real marts" below.

---

## Run the evals

The eval set lives in `evals/cases.yml` — seeded from the contract's own
`sample_questions` (ca + es) plus explicit guardrail cases. It runs **entirely
offline**.

```bash
# from packages/ai/
PYTHONPATH=src python evals/run_evals.py          # human report; exit 0 = all pass
PYTHONPATH=src python evals/run_evals.py --json   # machine-readable summary
```

Or via pytest (this is what CI runs — each case is its own test):

```bash
# from packages/ai/
python -m pytest                                  # whole suite (unit + evals)
python -m pytest tests/test_evals.py              # just the eval gate
```

Each case asserts the *shape* of a correct answer: answer-vs-refusal, the cited
metric, the municipality in the rows, required substrings, and that **every
answer has provenance** / every refusal has a reason. A guard test also asserts
that **every `sample_question` in the contract is covered** by an eval case.

---

## Run the API / CLI locally

```bash
# from packages/ai/
pip install -e ".[dev]"                # installs the package + dev tools
uvicorn datapoble_ai.api:app --reload  # http://127.0.0.1:8000/docs

# CLI
datapoble-ai "Quina població té Berga?" --locale ca
datapoble-ai "¿Dónde crece más la extrema derecha?" --locale es --json
```

Without an install, prefix with `PYTHONPATH=src` and use `python -m
datapoble_ai.cli …`.

---

## Enabling the OpenRouter (LLM) path

The key is a **secret provided at runtime — never committed** (`.gitignore`
already blocks `.env*`). When Bea provides it:

```bash
export OPENROUTER_API_KEY=sk-...           # the secret (never in the repo)
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet   # optional override
pip install -e ".[openrouter]"             # adds the openai client
```

Then `Agent(mode="auto")` (and the API) automatically use the LLM; with no key
they transparently fall back to the offline backend. Force a backend with
`mode="offline"` / `mode="openrouter"`.

---

## Desplegament a Render + control de cost

The API ships as a container (`Dockerfile`) for **Render** (EU region), and the
LLM bill is kept bounded by four layers — **all key-independent and tested
offline** (`src/datapoble_ai/costcontrol.py`):

### Cost control (why the LLM is cheap)

1. **Deterministic-first.** Even in `openrouter` mode the agent runs the
   keyword router *first*. A question it can answer (lookup / ranking /
   correlation) or precisely refuse (planned metric, unknown municipality) is
   served at **zero cost** — the LLM is called **only** for genuinely free text
   the router can't map to a metric. This is the biggest lever: most real
   questions never reach OpenRouter.
2. **Question cache.** Normalized `(question, locale)` → answer, in an in-memory
   LRU. An identical repeat question is free. *Persistence note:* Render's
   filesystem is ephemeral and the service may scale to several instances, so a
   cache that survives restarts would need an external store (Redis / KV). The
   in-process LRU is the cheap 80% and never lies — cached answers keep their
   full provenance.
3. **Rate-limit** per IP/user (token bucket). Over budget → HTTP **429** with a
   friendly message in the active locale (`Retry-After` header set).
4. **Hard spend cap.** A `SpendGuard` tracks *estimated* OpenRouter spend per
   UTC day and month against a ceiling. Once crossed, the agent **stops calling
   the LLM** and returns a graceful "daily AI limit reached" message — the
   deterministic answers keep working, because they never touch the guard.

All knobs are env vars (safe defaults; an unconfigured prod deploy fails
*cheap*, not surprising):

| Env var | Default | Meaning |
|---|---|---|
| `AI_CACHE_MAXSIZE` | `512` | LRU size; `0` disables the cache |
| `AI_RATE_CAPACITY` | `30` | token-bucket burst; `0` disables limiting |
| `AI_RATE_REFILL_PER_SEC` | `0.5` | sustained rate (≈30/min) |
| `AI_DAILY_USD` | `1.0` | daily spend ceiling; `0` = unbounded |
| `AI_MONTHLY_USD` | `20.0` | monthly spend ceiling; `0` = unbounded |
| `AI_USD_PER_CALL` | `0.01` | conservative per-call estimate (fallback) |
| `OPENROUTER_MODEL` | `anthropic/claude-3.5-sonnet` | model id |
| `AI_CORS_ORIGINS` | *(web + local dev)* | comma-separated allowed browser origins (see CORS below) |
| `AI_CORS_ORIGIN_REGEX` | `https://.*\.pages\.dev` | regex for dynamic origins (CF Pages previews); `""` disables |
| `AI_POLITICS_UNLOCK` | *(unset → vote questions always refused)* | **secret** word that lets the team ask vote-orientation questions (see *Political gate* below) |

`GET /health` reports the live cost-control state (cache hits/size, spend
to-date vs caps, rate-limit config).

### CORS (the browser calls us cross-origin)

The public **Mirador** front ("Pregunta-li") is an `adapter-static` build served
from a *different* origin (`riusdegent.cat` / Cloudflare Pages), and it calls
`/ask`, `/metrics`, `/health` straight from the browser. So the API ships a CORS
policy (`src/datapoble_ai/api.py`) with **explicit, safe defaults — never `*`**:

- Default allowed origins: `https://riusdegent.cat`, `https://riusdegent.pages.dev`,
  and local Vite `http://localhost:5173` / `:4173` / `http://127.0.0.1:5173`.
- Cloudflare Pages preview deploys (`https://<hash>.riusdegent.pages.dev`) are
  allowed by a default regex (`https://.*\.pages\.dev`).
- Methods `GET/POST/OPTIONS`; headers `Content-Type`, `X-Datapoble-User`;
  **credentials off** (no cookies).

**On Render:** set `AI_CORS_ORIGINS` to the comma-separated list of the web's
domains (it *replaces* the defaults), e.g.
`AI_CORS_ORIGINS=https://riusdegent.cat,https://riusdegent.pages.dev`. Tune or
disable the preview regex via `AI_CORS_ORIGIN_REGEX` (`""` turns it off).

### Political gate — vote questions are refused (discreetly)

By project decision, the public "Pregunta-li" **does not answer questions about
voting orientation**. Those are the metrics tagged `dimension: politica` in the
contract (`pct_indep`, `pct_esquerra`, `pct_extrema_dreta`, `guanya`). When a
question resolves to one of them, the agent returns a **neutral refusal**
(`refusal_reason: political_gated`):

> «Aquest observatori no respon preguntes sobre orientació de vot.»
> «Este observatorio no responde preguntas sobre orientación de voto.»

The gate lives in the **shared resolution layer** (`Router.execute_intent` in
`src/datapoble_ai/router.py`, via `src/datapoble_ai/politics.py`), so it holds
for **both** backends — offline and OpenRouter — and keys off the *resolved*
metric's dimension, not on brittle keyword matching. The same `politica` metrics
are also **omitted from `GET /metrics`**, so the public catalog never advertises
what the agent will decline.

**The refusal is deliberately discreet:** the message gives *no* hint that any
bypass exists.

**Team unlock (`AI_POLITICS_UNLOCK`).** For internal use, a single **secret word**
read at runtime from the `AI_POLITICS_UNLOCK` env var opens the gate. If a question
contains the word (matched whole-word, case- and accent-insensitively), the agent
answers normally — and the word is **stripped from the question before routing**, so
it never pollutes metric matching nor echoes back in the answer, the query, or the
provenance. The value is **never hardcoded and never committed** (same discipline as
`OPENROUTER_API_KEY` / `CostControl.from_env`).

**Fail-safe.** If `AI_POLITICS_UNLOCK` is **unset or empty**, there is no word to
match, so vote metrics are **always refused** — with no secret configured, the
observatory answers no political question. Locking is the default; unlocking is the
deliberate exception.

**On Render:** to enable the team unlock, add `AI_POLITICS_UNLOCK` as a **secret**
service env var (Render *Environment → Secret*), never as a committed value. Leave
it unset to keep every vote question refused.

### The container

Build **from the repo root** (the agent reads `semantic/metrics.yml` and
`data/marts/`, both outside this package):

```bash
docker build -f packages/ai/Dockerfile -t datapoble-ai .
docker run --rm -p 8000:8000 \
    -e OPENROUTER_API_KEY=sk-... \        # the SECRET — runtime only, never baked in
    -e AI_DAILY_USD=1.0 -e AI_MONTHLY_USD=20.0 \
    datapoble-ai
# http://127.0.0.1:8000/health
```

- `python:3.11-slim`, non-root user, `HEALTHCHECK` on `/health`.
- Listens on `$PORT` (Render injects it; defaults to 8000 locally).
- Start command: `python -m datapoble_ai.api` (uvicorn on `0.0.0.0:$PORT`).

**On Render:** create a *Web Service* from this repo, Docker runtime, Dockerfile
path `packages/ai/Dockerfile`, region EU. Set `OPENROUTER_API_KEY` as a secret
and any caps above as plain env vars. **Set `AI_CORS_ORIGINS` to the web's
domains** so the browser-side Mirador front can call the API (see *CORS* above).
Health check path `/health`. Without the key the service still runs in
**offline** mode (deterministic), which is a fine first deploy.

---

## Multi-model evals (quality vs cost) — `evals/compare_models.py`

A **separate, key-dependent** script (NOT part of CI) that runs the same
`cases.yml` set against several OpenRouter models and reports **pass-rate vs
estimated USD per model**, so a model is chosen on evidence:

```bash
export OPENROUTER_API_KEY=sk-...                    # required; makes real paid calls
PYTHONPATH=src python evals/compare_models.py
PYTHONPATH=src python evals/compare_models.py \
    --models anthropic/claude-3-haiku openai/gpt-4o-mini google/gemini-flash-1.5 --json
PYTHONPATH=src python evals/compare_models.py --pricing prices.json   # override the price table
```

It forces every case through the model (deterministic-first off) so it grades
the *LLM*, not the offline router. Per-model prices live in
`src/datapoble_ai/pricing.py` (reference values, overridable). **The offline CI
gate (`run_evals.py` / `tests/test_evals.py`) is untouched: deterministic, no
network, no key.**

---

## Pointing at the real marts

Sondeig now ships `data/marts/mart_municipi.parquet` (and `mart_electoral`), and
the warehouse **prefers them automatically** (real `*.parquet`/`*.csv` over the
fixtures): `Agent()` / the API run against the real data and `is_fixture` is
`false` in the provenance. Override the location explicitly with
`Agent(marts_dir=Path(...))` if needed.

**The fixtures are kept on purpose.** The deterministic offline gate (the test
suite and `evals/run_evals.py`) pins them via `use_fixtures=True`, so the gate
grades the **router logic against a known distribution** and stays green and
stable no matter how the real marts change. That keeps a clean separation:

| Caller | Data | Why |
|---|---|---|
| `Agent()` / API (offline or LLM) | real marts (fixtures only if absent) | honest answers; `is_fixture` tells you which |
| Test suite + eval gate | **fixtures, always** (`use_fixtures=True`) | deterministic, decoupled from disk |

So a question like "Quina població té Berga?" returns the real **17.539** at
runtime, while the gate asserts against the fixture's **17.160** — by design.

---

## Pending

- **`OPENROUTER_API_KEY`** (from Bea) to activate the live LLM path; then a live
  eval pass (`evals/compare_models.py`) to pick a model on quality-vs-cost.
- ~~**Real marts** from Sondeig to replace the seed fixtures.~~ **Done:**
  Sondeig now ships `data/marts/mart_municipi.parquet` and
  `mart_electoral.parquet` with real data, so the agent/API run against them
  automatically (`is_fixture: false`). The fixtures are retained on purpose as
  the **pinned input for the deterministic offline gate** (see "Pointing at the
  real marts"), so the gate proves the router logic and stays stable as the
  marts evolve.
- Optional, when traffic warrants: a **persistent / shared cache** (Redis/KV)
  to survive restarts and span Render instances (the in-memory LRU is per-process).
- Future (v1.1+, out of scope here): the Mirador UI, new metrics (Talaia),
  RAG over long docs.
