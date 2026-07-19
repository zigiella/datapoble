# D4 — mart_govern (rang per comarca) + regla «font o fórmula» + deprecació d'index_turisme + esmena L1/L3

**Agent:** Sondeig (dades) · **Data:** 2026-07-19 · **Tasca:** #5 de la cua (D4, prioritat de Bea 2026-07-18) · **PR:** #268

Quatre parts, un PR. El número que ven la demo és el **rang honest per comarca**.

## (a) `mart_govern` — el rang «k de n» calculat al transform, mai al front

Nou mart dbt (`packages/transform/models/marts/mart_govern.sql`), format llarg: 1 fila per
`ine5 × metric`. Per als **7 KPIs oficials i mesurats** del tauler (gorra §3): `valor`,
`rang` «k de n» **contra la comarca del municipi**, `n_amb_dada` (el denominador honest) i `data`.

- **Comarca = `municipis-territori.json`** (autoritat ine5→comarca, 947 munis) via
  `read_text` + `json_keys` — **mai una llista fixa**. Verificat: idèntica a la comarca de
  `mart_municipi` (que ve dels residus), però la partició ha de venir del mapa territorial
  canònic. Gombrèn (17080) → **19 del Ripollès**, no els 31 del Berguedà.
- **Rang:** `rank()` descendent pel valor (1 = el més alt), **empats comparteixen posició**
  (com `IETR_rank`, #263 — mai ordre fabricat dins l'empat). NULL honest: `valor` NULL →
  `rang` NULL i `n_amb_dada` l'exclou (renda: 20 munis · envelliment: 1).
- **KPIs (7):** `index_envelliment`, `poblacio`, `pct_noprincipal`, `rtc_per_1000hab`,
  `kwh_hab`, `renda_neta_persona`, `kg_hab_any`.
- **Fora, amb motiu** (frontera honesta, documentada al capçal): origen/«nova població»
  (nota narrativa VINCULANT de Bea — cap rang públic abans del seu vot; a més viu a
  `mart_demografia`), ETCA (presència absoluta i escassa; el rang duplicaria població; no és
  al pipeline dbt), atur (mensual i emmascarat `<5` = interval [1,4] — no es rankeja un
  interval; viu a `mart_pols_mensual`), serveis/restauració OSM (no oficial, «mínim observat»,
  NULL fora del Berguedà), radar/licitacions (tracks R/cabal).

**Byte-match (àncores A MÀ, gorra §2, la Pobla 08166):** envelliment 6/31 · padró 8/31 ·
%no-principal 10/31 · renda 19/31 · residus 24/31 — **tots quadren**. Gombrèn confirmat
contra els 19 del Ripollès (envelliment 14/19, kwh 16/19, %no-principal 11/19).

**Construcció:** `dbt run --select mart_govern` (amb `mart_municipi` sembrat des del parquet
versionat, ja que la raw és gitignorada al worktree). La sortida de dbt és **contingut
idèntic** a la que genera el mateix SQL sobre el parquet (comparat cel·la a cel·la). El
parquet versionat és la sortida real de dbt.

**Test** (`verify_govern.py`, al CI, offline): estructura (947×7=6629 files); comarca creuada
amb el JSON; **rang recalculat independentment amb pandas** i comparat fila a fila;
`n_amb_dada` = recompte real de no-nuls; rang dins [1, n_amb_dada]; NULL honest; Gombrèn
contra el Ripollès (no els 31); byte-match d'àncores a mà de la Pobla.

## (b) Regla de ferro de Bea (C6 §8.1): cada xifra amb font O fórmula

`export_web_municipis.build_metrics` ara emet el camp **`formula`** del contracte (49/49) +
`MetricDef.formula?: string` a `types.ts` (additiu, opcional — coordinat amb Mirador). D5 ja
pot mostrar font (mesurada) o fórmula (inferida) a cada KPI.

## (c) `index_turisme` fora dels publicadors

Deprecat al contracte (#267). Tret de: `export_web_municipis` (METRIC_KEYS/FORMAT/COL),
`export_indicadors_cat` (NUM_KEYS), `eval_writer` (FACT_KEYS). El mart el pot seguir calculant
(rastre). Exports regenerats, `--check` verd.

## (d) Esmena L1/L3 (handoff Mirador #256)

`kwh_hab`, `vidre_hab`, `restauracio_estab`, `restauracio_per_1000hab` i les 3 notes de font
(residus/icaen_consum/osm) citaven «capa L1/L3» → reescrites en termes de **senyal físic
mesurat oficial**. Els derivats del model (`poblacio_pernocta_est`, `carrega_*`,
`kwh_base_ratio`…) conserven el seu marc d'inferència (fora d'abast per disseny).

## ⚠️ Acoblament destapat (per a Talaia + Mirador)

Treure `index_turisme` del catàleg JSON fa **petar `/metodologia`** (500 en render):
`metodologia/+page.svelte` cablega `'index_turisme'` a la llista de claus del bloc C i
`srcLine()` fa `dataset.metrics[key].date` sense guarda. **No he tocat `packages/web/src`**
(jurisdicció de Mirador, és la seva feina de D5). El build NO peta (`handleHttpError: 'warn'`
→ CI web verd), així que és un acoblament de **runtime** que el CI no atrapa. `/glossari` NO
es veu afectat (itera el catàleg real + filtra per `HIDDEN`). **Recomanació:** fusionar D4
junt amb (o darrere) la neteja de `metodologia` de Mirador.

## Handoffs

- **➡️ Mirador (D5):** (1) `metodologia` — treure `'index_turisme'` de la llista de claus +
  guardar `srcLine`/`provOf` contra claus absents (evita el 500). (2) `MetricKey` a `types.ts`
  — treure `'index_turisme'` (el camp additiu `formula?` ja hi és). (3) cada targeta de KPI ja
  pot mostrar `metrics[key].formula`.
- **➡️ Talaia (contracte):** `catalog.is_available()`/`is_live()` de `packages/ai` no exclou
  `status: deprecated` (només `planned`) → l'agent tractaria `index_turisme` com a viu si el
  consulten. No ho toco (jurisdicció Brúixola/ai + decisió de contracte). `export_bergueda_bundle.py`
  (LLEGAT, cap workflow el crida, sortida gitignorada) encara el referencia — inofensiu.

## Verificació (offline, sense xarxa ni claus)

`verify_marts` · `verify_pols_mensual` · **`verify_govern`** · `derive_fase1 --check` · tots
els `--check` de la data-job → verd. **ai suite 206/206**. **svelte-check 0 errors** +
`npm run build` OK. **ruff** net.
