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

- **`renda_neta_persona` is illustrative for every row** (added for the B3
  /pregunta-li chips, whose renda example must resolve offline): plausible,
  tie-free values in the real Berguedà range, **not** the INE Atlas figures.
  The real column lives in `data/marts/mart_municipi.parquet`. Do not cite.

- **Municipality names follow the registers, article as a suffix** (`Pobla de
  Lillet, la`, `Nou de Berguedà, la`) — exactly how the real `mart_municipi` /
  `mart_electoral` spell them. Kept register-style on purpose so the offline
  gate exercises the router's toponym variants («la Pobla de Lillet» must
  resolve): B3 found that natural-form fixtures were masking a production
  refusal for every article-bearing municipality, the demo one included.

- **`mart_pols_mensual` is all-real (`is_real = 1`)**: 24 rows transcribed
  verbatim from the verified `data/marts/mart_pols_mensual.parquet` (D1, atur
  SEPE, byte-matched against the source CSV), trimmed to **two months**
  (`2026-05` + `2026-06`; the contract's `date:` for `atur_registrat` is the
  latest). Two months on purpose: the router pins dated marts to `MAX(date)`
  (B3), and the fixture must be able to catch a regression to the naive
  lookup — the stale month comes *first* in the file so an unpinned query
  would surface it (la Pobla: 27 al maig vs 31 al juny; Berga: 776 vs 760).
  Several rows are genuine «<5» doctrine rows (`atur_registrat` NULL +
  interval [1,4] + `atur_emmascarat = true`), including both province edge
  cases (Gombrèn 17080/Girona, Gósol 25100/Lleida) — and Gombrèn flips from a
  real 7 (maig) to masked (juny), a true month-to-month doctrine transition.
  **Identity caveat**: these rows carry the *official* register codes and the
  pols' own naming (natural article: `la Pobla de Lillet`), which differ from
  the synthetic `ine5` placeholders above (Bagà is `08009` in `mart_municipi`)
  and from the register-style article of `mart_municipi` (`Pobla de Lillet,
  la`). That disagreement is **faithful to the real marts** and the router
  resolves toponyms per table, so the mismatch is exercised, not hidden.

The agent itself does not read `is_real`; it is documentation for humans and a
hook for a future "fixture vs production" provenance flag.

## Schema

Columns mirror `semantic/metrics.yml` `column:` names exactly, so the SQL
builder can select `metric.column` straight from `metric.table`:

- `mart_municipi` — demografia, vivenda, turisme, pressió, energia, renda, índex.
- `mart_electoral` — política (columns are suffixed `_A20241` = Parlament 2024,
  matching the contract).
- `mart_pols_mensual` — treball (mensual, format llarg: 1 row per `ine5` +
  `date` "YYYY-MM"); columns mirror the real mart exactly
  (`atur_registrat`/`_min`/`_max`/`atur_emmascarat`), plus `is_real`.

`planned` metrics (`index_envelliment`, `pct_extrema_dreta`) are intentionally
**absent** — the contract marks them not-yet-computed, and the agent refuses to
query them, so there is nothing to seed.
