# Elèctric domèstic ingerit + export marts→JSON per al web — Sondeig

**Fecha:** 2026-06-05
**Autora:** Sondeig
**Para:** Talaia (review/merge) · Mirador (consumeix el JSON)
**Tema:** (1) cablar de debò la ingesta del consum elèctric DOMÈSTIC (ICAEN `8idm-becu`) i materialitzar la sèrie 2013–2024 per `ine5`; (2) afegir un pas de pipeline repetible que exporti els marts reals a `data/web/municipis.bergueda.json` amb la forma EXACTA que espera el frontend (els 31 munis reals, no el mock).
**Status:** avance / handoff

## Contexto
Cap al pilot demoable calien dues coses de dades: l'**elèctric real** (indicador
estrella *població real vs padró*) i que el **web** pugui mostrar els 31 municipis
reals en lloc dels 2 del mock. L'stub `icaen_consum.py` (PR #14) ja existia amb tota
la lògica però **no estava cablejat** ni materialitzat; i el frontend de Mirador
arrencava contra `src/lib/mock/municipis.ts` (forma `MunicipisDataset`).

## Qué hicimos / decidimos

### TASCA 1 · Elèctric domèstic ingerit i materialitzat
- **Cablat a `all`:** `icaen_consum` afegit a `RUNNERS` de `__main__.py` (i als
  docstrings: ja no és "stub"). La raw guarda **tots els sectors** del Berguedà
  (fidelitat a la font, com residus), `data/raw/icaen_consum/` (gitignored).
- **Capa transform nova:** `stg_icaen_consum` (deriva `ine5` de `cdmun`, tipa
  any/consum, tots els sectors) → `mart_consum_electric` (filtra sector 7 USOS
  DOMÈSTICS, descarta NULLs per secret estadístic, uneix `codi6`+nom des de
  `mart_municipi`). **Format LLARG** `(ine5, codi6, municipi, comarca, any_consum,
  sector, consum_kwh_domestic)`, post_hook `COPY` → `data/marts/mart_consum_electric.parquet`
  (versionat, com els altres marts).
- **Cobertura (honesta):** **31/31 municipis × 2013–2024 = 372 files, ZERO forats,
  zero NULLs** al sector domèstic. El domèstic sobreviu al secret estadístic fins i
  tot a Castellar de n'Hug (166 hab), tal com predeia `docs/poblacio-real-fonts.md §2`.
  Ancoratges verificats que coincideixen amb el doc: Castellar 2024 = **266.857 kWh**
  (2023=273.219, 2022=271.939), Berga 2024 = **21.019.904 kWh**.
- **Decisió de disseny — NO normalitzo.** El mart guarda el consum **brut anual**
  (fidel a la font). La normalització del numerador de presència (kWh/habitatge vs
  kWh/població) i la fórmula del *gap* població-real són **síntesi teva (Talaia)**:
  quan decideixis, s'afegeix una columna derivada a `mart_municipi`. Aquí només
  materialitzo la sèrie traçable.
- Test nou: `assert_mart_consum_electric_grid` (graella completa 31×12, sense forats
  ni `(ine5, any)` duplicats) + not_null/between als YML.

### TASCA 2 · Export marts → JSON per al web (repetible)
- **`tools/export_web_municipis.py`**: llegeix `mart_municipi` + `mart_electoral` +
  el contracte `semantic/metrics.yml` i emet **`data/web/municipis.bergueda.json`**
  (versionat) amb la forma EXACTA `MunicipisDataset` (`packages/web/src/lib/contract/types.ts`),
  replicant el mock però amb els **31 munis reals**. Idempotent: `--check` falla si el
  JSON està desactualitzat (apte per a un futur job CI).
- **El catàleg `metrics` surt del contracte**, no codificat a l'script: label/unit/
  nota/date/dimension/status vénen de `metrics.yml` (frontera honesta del contracte).
  Només `format` (presentació) i la cadena `source` llegible es resolen amb un mapa
  fix, mirall de com Mirador ja els pinta.
- **Millora sobre el mock:** ompleno amb dades reals camps que el mock tenia com a
  il·lustratius/`planned` — p. ex. `pct_extrema_dreta` (real, Parlament 2024, els 31),
  `index_envelliment`, i la població real de Berga (17.539, no el placeholder 17.160).
  KPIs comarcals **calculats de debò** (sumes per a recomptes, ponderada per població
  per a `kg_hab_any`, mediana per a IETR), no placeholders.
- **Buit honest marcat:** `pct_icaen_EFG` = `null` per als 31 (status del contracte).
  Requereix el connector de **certificats** ICAEN (`j6ii-t3w2`), que és un dataset
  DIFERENT del consum (`8idm-becu`) i queda fora d'aquest PR. **No l'invento.**
- **NO he tocat `packages/web`** (jurisdicció de Mirador): només produeixo el JSON +
  el pas que el genera. Mirador haurà de canviar el loader del mock pel JSON.

### Verificació end-to-end
- `python -m datapoble_ingestion all` → 5 fonts OK (icaen_consum: 1559 files raw).
- `dbt build` → **PASS=68, ERROR=0** (inclou els 7 tests nous del mart elèctric; els
  marts existents no deriven). `dbt parse` net. `ruff check` net.
- `verify_marts.py` → OK (31 munis, ancoratges Castellar/Berga, Spearman=0,869).
- Export → 31 municipis, 19 mètriques; `--check` confirma idempotència.

## Por qué
- El consum **domèstic** és l'únic proxy elèctric que dóna sèrie sencera als 31
  (resistència al secret estadístic), per això és el tall del mart; deixar-lo brut
  i sense normalitzar manté la decisió metodològica (la teva) separada de la dada.
- Un **únic JSON amb la forma del contracte** desacobla Mirador del pipeline: el web
  passa de 2 munis mock a 31 reals canviant només el loader, sense tocar la forma.
  Que el catàleg surti de `metrics.yml` garanteix que les etiquetes segueixen sent
  dada de contracte, no missatge d'interfície.

## Decisiones para Talaia (revisión)
1. **Normalització del *gap*:** el mart elèctric és brut a propòsit. Quan triïs
   kWh/habitatge vs kWh/població i la fórmula (proposo z-score comarcal, com al doc),
   afegeixo la columna a `mart_municipi` en un PR curt de seguiment.
2. **CI:** el job Python (ruff+dbt) segueix sent un TODO comentat a `ci.yml` (no el
   toco, és de la Bea). Per tant dbt **no corre a CI**; els parquets versionats són la
   font per a `packages/ai`/deploy. Quan s'activi el job, `export_web_municipis.py
   --check` és un bon gate per evitar que el JSON web quedi obsolet.
3. **`packages/ai` no es veu afectat:** el warehouse carrega marts **per nom de taula
   del catàleg** (`warehouse.py:105`), no fa glob de `*.parquet`; el nou
   `mart_consum_electric.parquet` és inert per a la IA (cap mètrica del contracte hi
   apunta). El job `ai-evals` segueix com estava (el seu vermell per fixtures és de
   Brúixola, no d'aquest PR).

## Pendiente
- [ ] **Talaia:** decidir normalització + fórmula del *gap* → columna derivada a `mart_municipi`.
- [ ] **Mirador:** substituir el loader del mock (`getMunicipisDataset`) per la càrrega de
      `data/web/municipis.bergueda.json` (mateixa forma; no cal tocar tipus ni UI).
- [ ] Explorar fracció RESTA estacional de l'ARC (senyal intra-anual; pendent del PR #14).

## Enlaces
- `packages/ingestion/datapoble_ingestion/icaen_consum.py` · `__main__.py` (cablat a `all`)
- `packages/transform/models/staging/stg_icaen_consum.sql`
- `packages/transform/models/marts/mart_consum_electric.sql` + `_marts.yml` + `tests/assert_mart_consum_electric_grid.sql`
- `data/marts/mart_consum_electric.parquet` (372 files, 2013–2024)
- `tools/export_web_municipis.py` → `data/web/municipis.bergueda.json`
- `docs/poblacio-real-fonts.md` (Pendent actualitzat) · `semantic/metrics.yml` (contracte)
