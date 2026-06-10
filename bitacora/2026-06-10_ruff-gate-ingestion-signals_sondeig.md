# Netejar les 4 incidències de ruff i ampliar el gate a ingestion + signals

**Fecha:** 2026-06-10
**Autora:** Sondeig (dades/pipeline) · amb fixos de Cabal (events)
**Para:** Talaia (review/merge, gatekeeper de main)
**Tema:** tancar el follow-up del PR #77 — el lint del gate `data` s'acotava a `packages/transform` perquè `ruff` trobava 4 incidències preexistents en altres fronts. Netejades les 4 i ampliat el gate perquè el lint cobreixi també `ingestion` i `signals`.
**Status:** fet, verificat / handoff

## Contexto
El PR #77 va activar el job `data` de CI, però el seu pas de lint deia `ruff check packages/transform` i prou. El motiu era honest i quedava escrit al handoff de la seva bitàcola: `ruff` trobava **4 incidències preexistents fora de transform**, i no s'activa un gate en vermell. Aquesta entrada és aquell follow-up.

## Les 4 incidències (jurisdicció respectada)
Front **Sondeig** (ingestion):
1. `restauracio_osm.py:38` — **F401**: `from pathlib import Path` importat i no usat.

Front **Cabal** (signals):
2. `events.py:44` — **F541**: f-string sense cap `{placeholder}` (el `CREATE TABLE` és SQL literal) → treta la `f`.
3. `tests/test_convergencia.py:20` — **F401**: import no usat `LLINDAR_TURISME_ALT`.
4. `tests/test_events.py:221` — **E731**: `q = lambda s: …` reescrit com a `def q(s): return …`.

Dos commits identity-inline, un per front (Sondeig / Cabal); cap altre fitxer tocat.

## Sobre la config de ruff (verificat)
El brief preguntava si `signals` té config de ruff pròpia. **No en té** — ni `signals`, ni `ingestion`, ni `transform`. L'únic `[tool.ruff]` del repo viu a `packages/ai/pyproject.toml` (amb el seu propi job `ai-evals`). Per tant els tres fronts del job `data` corren amb les **regles per defecte** de ruff (E + F), i ampliar l'abast **no pot entrar en conflicte**: no hi ha cap config alternativa que sobreescriure. Justament per això salten F401/F541/E731 (regles del default).

## Canvi al gate
`.github/workflows/ci.yml`, job `data`:
- `Lint (ruff) · transform` → **`Lint (ruff) · transform + ingestion + signals`**
- `ruff check packages/transform` → `ruff check packages/transform packages/ingestion packages/signals`

Un sol pas, mateix intèrpret de regles per als tres fronts.

## Verificación (local, abans de cablejar)
- `ruff check packages/transform packages/ingestion packages/signals` → **All checks passed** (exit 0), amb ruff 0.15.16.
- `pytest packages/signals` en venv net (`pip install -e packages/signals[test]`, Python 3.12) → **85 passed**. Cap regressió pels fixos de Cabal.

## Pendiente / handoffs
- [ ] **Talaia:** review/merge. El job `data` ja cobreix els tres fronts Python en verd.
- [ ] Futur (ja anotat al #77): pinning de versions a CI i `dbt test` sobre marts construïts des del parquet.

## Enlaces
- `.github/workflows/ci.yml` (job `data`, pas de lint ampliat)
- `packages/ingestion/datapoble_ingestion/restauracio_osm.py` · `packages/signals/datapoble_signals/events.py` · `packages/signals/tests/test_convergencia.py` · `packages/signals/tests/test_events.py`
- `bitacora/2026-06-10_ci-data-gate_sondeig.md` (el #77 que va deixar aquest follow-up)

— Sondeig
