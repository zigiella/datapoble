# Gate offline determinista amb els marts reals presents (fix del job `ai evals`)

**Fecha:** 2026-06-04
**Autora:** Brúixola
**Para:** Talaia (verificar CI + mergear PR #14)
**Tema:** deixar el gate `ai evals (offline)` **verd i determinista** ara que Sondeig ha aterrat els marts reals; desacoblar el gate de les dades del disc.
**Status:** fix / handoff · empès a `feat/sondeig-poblacio-real` (coordinat amb PR #14)

## Contexto
El PR #14 de Sondeig va reconciliar el nom dels marts (Tasca A): ara existeixen `data/marts/mart_municipi.parquet` i `mart_electoral.parquet` amb **dades REALS**. El meu `Warehouse` prefereix el real sobre les fixtures, així que va passar a `using_fixture=False` — i això va **trencar 3 tests offline** que assumien les fixtures (cosa que el meu propi README ja preveia, "once the real marts land…"). Resultat: el job **`ai evals (offline)` vermell** al #14.

Els 3 punts trencats:
- `tests/test_router.py:14` — `provenance.is_fixture is True` (real: `False`).
- `tests/test_router.py:37` — mínim `rtc_total` = "La Nou de Berguedà" a les fixtures (real: **Fígols**).
- `evals/cases.yml:92` (`ca_poblacio_lookup`) — `contains: ["17.160"]`, placeholder de Berga a les fixtures (real: **17.539**).

## Qué hicimos / decidimos
Vaig triar l'**enfocament recomanat**: forçar el suite offline a **usar fixtures explícitament**, perquè el gate determinista quedi **desacoblat** de si hi ha marts reals al disc. Així el gate prova la **lògica** del router (text→intent→SQL parametritzat + procedència), no les dades, i és estable quan els marts evolucionin. La separació clau: **runtime ≠ gate**.

1. **`src/datapoble_ai/warehouse.py`** — nou flag `use_fixtures: bool = False`. Quan és `True`, `_source_for` **salta** la cerca a `marts_dir` i va directe a la fixture CSV. Per defecte `False` → comportament runtime intacte (prefereix el real). No vaig tocar res del contracte: `validate`, paraules prohibides, binding de paràmetres i la procedència queden igual.
2. **`src/datapoble_ai/agent.py`** — passo `use_fixtures` a través del facade fins al `Warehouse`. Per defecte `False`: `Agent()` i l'API segueixen preferint els marts reals (frontera d'honestedat intacta — `is_fixture` segueix dient la veritat al runtime).
3. **`tests/conftest.py`** — les fixtures `warehouse` i `agent` es construeixen amb `use_fixtures=True`. El gate s'ancora a la distribució coneguda.
4. **`evals/run_evals.py`** — `run()` construeix l'agent offline amb `use_fixtures=True` (és la mateixa via que CI executa via `tests/test_evals.py`).
5. **`evals/compare_models.py`** — el warehouse també amb `use_fixtures=True`, perquè grada cada model contra el **mateix** `cases.yml` (consistència; no és part de CI).
6. **Docs (dins jurisdicció):** actualitzat el `packages/ai/README.md` (secció "Pointing at the real marts" + frontera de dades + nota "Pending") i `packages/ai/fixtures/README.md` per reflectir que **els marts reals ja existeixen** i que les fixtures es **mantenen a propòsit** com a input fix del gate. **Eliminada** la nota obsoleta del README que deia que els `mart_*_bergueda` no es recollien (resolt per Tasca A) i el consell ara erroni de "delete the fixtures".

## Por qué (gate determinista, significatiu i verd)
- **Determinista + desacoblat:** verificat que amb els parquets reals al disc, el warehouse del gate carrega les fixtures (`using_fixture=True`, Berga **17.160**, mín rtc **La Nou**), mentre el runtime carrega el real (`False`, Berga **17.539**). El gate no depèn de l'estat del disc.
- **Significatiu:** segueix exercint lookup/ranking/correlation (ca+es), refusals amb raó, i que **tota resposta porta procedència** — sobre una distribució coneguda i estable.
- **Honest:** NO vaig conflar "offline" (sense LLM) amb "fixtures" (sense dades reals). Un deploy keyless segueix servint marts reals; només el **gate** s'ancora a fixtures. Així no introdueixo cap regressió de la frontera d'honestedat.

## Verificació local (verd)
- `ruff check src evals tests` → **All checks passed!**
- `python -m pytest` → **85 passed** (eren 3 failed / 82 passed abans del fix).
- `python evals/run_evals.py` → **13/13 passed** (offline), amb els marts reals presents al disc.

## Disciplina respetada
- Treball **només a `packages/ai`** (+ el seu README i `fixtures/README.md`). **No** vaig tocar `data/marts/`, `packages/transform`, `packages/ingestion` ni `docs/`.
- **No** vaig tocar `.github/workflows/ci.yml` ni `.gitignore` (de la Bea).
- Contracte **text→SQL traçable intacte** (cita font/data/fórmula o rebutja amb raó); guardrails read-only sense canvis.
- Git **identity-inline**, **sense** co-autor IA. Push a `feat/sondeig-poblacio-real` (canvi coordinat amb el PR #14, no branca nova).
