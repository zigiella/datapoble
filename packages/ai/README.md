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
    # El municipi amb més Índex d'Exposició Turística-Residencial és
    # Castellar de n'Hug (100 0-100). Font: datapoble … Fórmula: 0.5*A_resid + 0.5*B_turis …
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
  `OPENROUTER_API_KEY`** — calling it without the key raises a clear
  `RuntimeError` instead of faking an answer. The `openai` client is an
  *optional* dependency, imported lazily only on that path.
- **Caching** of LLM responses is noted in the spec but not implemented yet
  (the offline path is deterministic, so it needs none).

**Data boundary:** at scaffold time `data/marts/` was empty (Sondeig had not
industrialised the marts), so the offline path runs against seed **fixtures**
in `fixtures/`. Two rows are *real* (Castellar de n'Hug, Berga — transcribed
from `docs/data-sources.md` §8, verified 2026-06-01); the rest are synthetic
placeholders so ranking/correlation have a distribution. Every answer's
provenance carries `is_fixture: true` while fixtures are in use. See
`fixtures/README.md`.

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

## Pointing at the real marts

When Sondeig ships `data/marts/mart_municipi.parquet` (and `mart_electoral`),
the warehouse prefers them automatically (real `*.parquet`/`*.csv` over the
fixtures), and `is_fixture` flips to `false` in the provenance. Override the
location explicitly with `Agent(marts_dir=Path(...))` if needed. Once the real
marts land, delete the fixtures.

---

## Pending

- **`OPENROUTER_API_KEY`** (from Bea) to activate the LLM path; then a live
  eval pass against the model + response caching.
- **Real marts** from Sondeig to replace the seed fixtures.
- CI job for the evals (added to `.github/workflows/ci.yml` in this PR).
- Future (v1.1+, out of scope here): the Mirador UI, new metrics (Talaia),
  RAG over long docs.
