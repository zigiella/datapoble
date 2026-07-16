# Fixtures — seed marts for the offline path

These CSVs seed a small warehouse so the deterministic agent can run SQL and
return numbers. At scaffold time they stood in for the real `data/marts/*`
(empty then). **Now the real marts exist** (Sondeig's pipeline ships
`mart_municipi.parquet` / `mart_electoral.parquet`), and the runtime
agent/API prefer them automatically.

These fixtures are **kept on purpose, not deleted**: the deterministic offline
**gate** (the test suite and `evals/run_evals.py`) pins them via
`use_fixtures=True`, so it grades the router logic against a fixed, known
distribution and stays green and stable independently of how the real marts
evolve. See `packages/ai/README.md`, "Pointing at the real marts".

## Honesty boundary — what is real vs synthetic

Every row carries an `is_real` flag.

- **`is_real = 1`** — values transcribed from `docs/data-sources.md` §8
  ("Hechos verificados clave", verified live against official sources on
  2026-06-01): **Castellar de n'Hug (08052)** and **Berga (08022)**.
  Population, dwelling split, RTC counts and the derived ratios for these two
  are real. (`IETR`/`IETR_rank`/`kg_hab_any`/`pct_icaen_EFG` for them are
  illustrative — the doc gives the inputs but not the final index value.)
- **`is_real = 0`** — the other eight Berguedà municipalities and the whole
  `mart_electoral` table are **synthetic but plausible** placeholders, so that
  ranking / correlation / "which municipality" questions have a distribution to
  operate on offline. **Do not cite these as fact.** They exist only to make
  the evals and the deterministic router runnable without the pipeline.
- **The pressure columns are illustrative for every row, `is_real` included**
  (`kwh_hab`, `poblacio_pernocta_est`, `gap_pernocta`, `gap_pernocta_pct`,
  `confianca`). Added in the X1 harvest so the doctrine's registers have
  something to grade offline. `kwh_hab` and `confianca` are **chosen**; the three
  derived columns are then computed with the contract's own formulas
  (`round(poblacio * kwh_hab / 1224)` etc.), so the fixture is internally
  consistent and a test can re-derive it. **Do not cite any of them as fact** —
  not even for Castellar de n'Hug and Berga, whose *inputs* are real but whose
  estimates here are not the pipeline's.

  Castellar de n'Hug carries `confianca: baixa` on purpose: it is the contract's
  own worked example of diverging signals (high waste, low electricity because
  the mountain burns wood), so the fixture exercises the `soroll` register — "I
  have the estimate and I disown it, with a reason" — rather than only the happy
  path. La Nou de Berguedà is the second such case.

The agent itself does not read `is_real`; it is documentation for humans and a
hook for a future "fixture vs production" provenance flag.

## Schema

Columns mirror `semantic/metrics.yml` `column:` names exactly, so the SQL
builder can select `metric.column` straight from `metric.table`:

- `mart_municipi` — demografia, vivenda, turisme, pressió, energia, índex.
- `mart_electoral` — política (columns are suffixed `_A20241` = Parlament 2024,
  matching the contract).

`planned` metrics (`index_envelliment`, `pct_extrema_dreta`) are intentionally
**absent** — the contract marks them not-yet-computed, and the agent refuses to
query them, so there is nothing to seed.
