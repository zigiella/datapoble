# Densitat de restauració al mapa (2n proxy de L3) + honestedat dels 6 zeros d'OSM — Mirador

**Fecha:** 2026-06-07
**Autora:** Mirador
**Para:** Talaia (review + merge), Bea (qui ho va demanar: «exposar la densitat de restauració com a indicador VISIBLE»), Sondeig (FYI: la teva dada del PR #40 ja és al mapa)
**Tema:** `packages/web` — cablejar `restauracio_per_1000hab` (la dada que Sondeig va deixar **a punt** al JSON al PR #40) com a **indicador seleccionable del mapa coroplètic** `/mapa`, agrupat amb la capa de turisme, amb un **tractament cartogràfic honest** dels 6 municipis amb recompte 0 d'OSM.
**Status:** avance / handoff

## Contexto
Sondeig (bitàcola `2026-06-06_restauracio-osm-validacio-L3_sondeig.md`, PR #40 a main) va ingerir el **recompte d'establiments de restauració d'OpenStreetMap** (via Overpass) com a **2n proxy d'hostaleria** i va materialitzar `restauracio_estab` + `restauracio_per_1000hab` al mart, al `semantic/metrics.yml`, al JSON web (33 mètriques) i a `MetricKey` (`types.ts`). Valida la **capa L3** (pressió turística) del model de 3 capes: Spearman ≈ 0,54 vs `vidre_hab` i `index_turisme`. Sondeig **no** va tocar la UI (patró «dada primer, exposició després»). Bea vol veure-ho al mapa. Aquesta entrada documenta com ho he MOSTRAT (jo no he tocat cap dada).

## Què hem fet / decidit

### 1. `restauracio_per_1000hab` a `MAP_INDICATORS` (al costat d'`index_turisme`)
`lib/map/indicators.ts`: afegit a la llista d'indicadors seleccionables **just després d'`index_turisme`** (els dos proxies de L3 adjacents al selector). És una **densitat 0+** → seqüencial terra `--dp-exposure-*` (com `kg_hab_any`) i **Jenks** per defecte — sense tocar res: `methodFor()` ja retorna `jenks` per a tota clau que no sigui ni cuantil ni divergent, i `rampColors()` ja mostreja la rampa terra. Verificat a la llegenda en viu: «SEQÜENCIAL · JENKS (TALLS NATURALS) · 5 CLASSES». Format: el del contracte (`decimal`, 1-2 decimals; unit «per mil»/«por mil»).

### 2. i18n ca/es
`messages/ca.json` + `es.json` (Paraglide els compila a `m.*()`):
- `map_ind_restauracio` — etiqueta del selector: **«Densitat de restauració» / «Densidad de restauración»**.
- `map_caveat_restauracio` — caveat: recompte d'**OSM = MÍNIM observat, no cens** (infra-mapeja el rural); **2n proxy que VALIDA** la pressió turística del vidre; i la nota explícita dels 6 zeros (vegeu §3). Cablejat a `LAYER_KEYS` + `layerCaveat` del `mapa/+page.svelte` perquè surti a l'`.alert` principal quan l'indicador és actiu.

### 3. 🔴 HONESTEDAT CARTOGRÀFICA — el 0 d'OSM ≠ «la classe més baixa»
**El problema:** 6 micromunicipis surten amb `restauracio_per_1000hab = 0` a OSM (Castell de l'Areny, Fígols, Montclar, la Quar, Sant Jaume de Frontanyà, Viver i Serrateix). **4-5 tenen `vidre_hab` ALT** (Castell de l'Areny 60,1; la Quar 70,5; Viver i Serrateix 74,5) → és **buit de mapejat d'OSM, NO absència real d'hostaleria**. Pintar-los com la classe seqüencial més baixa (terra clar) seria una **mentida cartogràfica**: afirmaria «aquí gairebé no hi ha hostaleria» quan el senyal del vidre diu el contrari.

**La solució (la més neta que respecta el principi):** tractar el **valor 0 d'aquest indicador concret com a sense-dada-fiable** i reaprofitar el **tramat de «sense dada» que el mapa JA té** (no inventar cap gest nou). Centralitzat en **una funció `mapValue(key, raw)`** a `indicators.ts` + el set `OSM_COUNT_ZERO_AS_NODATA` (només `restauracio_per_1000hab`): si la clau hi és i `raw === 0` → retorna `null`. Les **tres vies de render** la consulten, així coincideixen:
1. **Classificació** (`mapa/+page.svelte` → `series`): els 6 zeros passen a `null` → `classify()` (que ja ignora els no-finits) **no els pren com a mínim de Jenks** ni els assigna a cap classe. Els talls es calculen només sobre els 25 valors reals (>0).
2. **Pintat** (`ChoroplethMap.svelte` → `joinValues`): `__hasval` queda **fals** per als 6 → cauen a la capa `HATCH` (`filter: ['!', ['get','__hasval']]`), **no** a `FILL`.
3. **Tooltip** (hover → payload `value`): mostra «Sense dada disponible» + procedència «sense dada», no «0,0 per mil».

La **llegenda/caveat** ho diu explícitament. És una regla **específica d'aquesta clau**: per a qualsevol altre indicador, un 0 real segueix sent un 0.

> **Per què `null` i no una 6a classe «buit» o un color propi:** el sistema ja codifica «sense dada fiable» amb un sol gest (el hatch sobre `--dp-nodata`), i la llegenda ja el documenta. Afegir-hi una classe nova duplicaria semàntica i trencaria la paleta de 5 classes. Degradar a `null` és **una línia**, reusa tota la cadena existent (classificació → hatch → tooltip → llegenda) i deixa el missatge net: «d'aquests 6 no en tenim dada fiable», que és **exactament** el que passa.

## Verificació
- **`npm run check`** → VERD (0 errors, 0 warnings; Paraglide compila les 2 claus noves; copy-data OK).
- **`npm run build`** → VERD (static, build en ~3,9 s).
- **Preview en viu** (dev `mirador-wt`, port 5174, Chromium headless via `preview_eval`):
  - Selector mostra **«Densitat de restauració»** en 4a posició (després d'«Pressió turística»); `value="restauracio_per_1000hab"`.
  - En seleccionar-lo: llegenda «DENSITAT DE RESTAURACIÓ · SEQÜENCIAL · JENKS · 5 CLASSES» (5 files de classe); **caveat complet** a l'`.alert` («MÍNIM observat, NO un cens… els 6 municipis amb recompte 0 d'OSM… es pinten amb el tramat de "sense dada", no com la classe més baixa»).
  - **Estat real de la font MapLibre** (`querySourceFeatures('bergueda')`): **els 6 zeros tenen `__hasval=false`** (→ capa hatch) i **els altres 25 `__hasval=true`** amb `__val` real (Gósol 28,99; Gisclareny 35,71; Berga 1,6). 25+6=31. ✅ La decisió honesta es compleix al canvas, no només a la teoria.

## Decisions per a Talaia (review)
- **Cap canvi fora de `packages/web`**: ni `data/`, ni `semantic/metrics.yml`, ni `signals|ingestion|transform`, ni workflows. La dada ja hi era (PR #40); jo només la MOSTRO. Diff = 5 fitxers (+61/−6).
- La regla del 0→nodata viu en **`mapValue`** (un únic lloc, `indicators.ts`), no escampada pels components. Si demà entra un altre indicador de recompte OSM amb el mateix biaix, només cal afegir-lo a `OSM_COUNT_ZERO_AS_NODATA`.
- La restauració **NO** entra a `ESTIMATE_KEYS` del tooltip (no és una estimació de les 3 capes; és una mesura/densitat). La seva procedència és «derivat» (font conté «calculat»), correcta per al punt morat. Quan és 0→nodata, la procedència passa a «sense dada» (negatiu) — coherent.

## Pendiente
- [ ] **Talaia:** review + merge.
- [ ] (Opcional, idea de Sondeig) integrar la restauració com a corroborador de la `confianca` de L3, **sense** deixar que els 0 d'OSM baixin la confiança (són buit de mapejat). Fora d'abast d'aquest PR (toca lògica de senyals/contracte).

## Enlaces
- `packages/web/src/lib/map/indicators.ts` (`MAP_INDICATORS`, `OSM_COUNT_ZERO_AS_NODATA`, `mapValue`)
- `packages/web/src/routes/mapa/+page.svelte` (`series` via `mapValue`, `INDICATOR_LABEL`, `LAYER_KEYS`/`layerCaveat`)
- `packages/web/src/lib/components/ChoroplethMap.svelte` (`joinValues` + hover via `mapValue`)
- `packages/web/messages/{ca,es}.json` (`map_ind_restauracio`, `map_caveat_restauracio`)
- Precedents: `bitacora/2026-06-06_restauracio-osm-validacio-L3_sondeig.md` (la dada upstream) · `bitacora/2026-06-06_da-mapa-paletes_mirador.md` + `2026-06-06_retocs-mapa_mirador.md` (el mapa)
