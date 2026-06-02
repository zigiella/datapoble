# Fixtures — seed marts for the offline path

These CSVs are a **stand-in** for the real `data/marts/*` that Sondeig
industrialises (the pipeline). At the time this package was scaffolded,
`data/marts/` was empty, so the offline/deterministic agent needs a small
warehouse to actually run SQL against and return numbers. When the real marts
land, point the warehouse at them and delete these (see
`packages/ai/README.md`, "Pointing at the real marts").

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
