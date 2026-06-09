# Fitxa per municipi `/municipi/[ine5]` (els 31 del Berguedà) + navegació — Mirador

**Fecha:** 2026-06-08
**Autora:** Mirador
**Para:** Talaia (review + merge), Bea (vot narratiu/marca)
**Tema:** `packages/web` — **generalitza la fitxa rica** que avui només tenen els dos extrems del Resum (Berga `08022`, Castellar `08052`) a **QUALSEVOL dels 31 municipis del Berguedà**, amb ruta pròpia, prerender, i navegació des del mapa i el Resum.
**Status:** PR #59 obert · **CI VERD** (web build+check, repo structure, ai evals — tots SUCCESS) · per revisar i mergear (Talaia)

## Contexto
Fins ara la presentació rica (files `.ex__rows`, subgrups «Senyals físics»/«Les 3 capes», pastilla de tipologia, confiança + score, procedència) només existia per als **dos extrems** del Resum. Bea vol poder accedir a la fitxa de **qualsevol** muni del Berguedà amb les mateixes dades. Aquesta presentació és el que calia **generalitzar a una ruta per municipi**. Tot dins `packages/web`.

## Què hem fet

### 1. Ruta nova `/municipi/[ine5]` (+ `/es/...`) — NOVA
`src/routes/municipi/[ine5]/{+page.ts,+page.svelte}`.
- **`+page.ts`**: `prerender=true`, `trailingSlash='always'`. `load()` carrega el dataset real (`loadMunicipisDataset`) i resol el muni per `params.ine5`; si no hi és → `row=null`. **`entries()`** declara els 31 codis per prerenderitzar, **derivats del dataset** (no llista codificada; el dia que entrin més comarques s'amplia sola).
- **Subtilesa clau (gotcha resolt):** `entries()` **NO rep el `fetch` de SvelteKit** (el que resol URLs relatives) — corre amb el `fetch` global de Node, que peta amb `/data/...` (`Failed to parse URL`). Solució: `entries()` **llegeix l'actiu del DISC** (`static/data/municipis.bergueda.json`, la còpia que deixa el prebuild `copy-data`), via `import('node:fs')` dinàmic (mòdul universal → `node:fs` només s'avalua en build). Amb **fallback NO-FATAL** (retorna `[]` → SPA) si l'actiu manca, per no trencar CI. El `load()` de cada entrada SÍ usa el `fetch` de SvelteKit (com Resum/Mapa) → prerender-safe.

### 2. La fitxa (`+page.svelte`) — TOTES les mètriques, com el Resum
- **Capçalera de dades** idèntica a la lectura dels extrems del Resum: rang IETR + valor gran, **pastilla de tipologia** (color de l'arquetip via `--tipo-c`, reusa `lib/map/tipologia`), línia de **confiança = bandera (alta/mitjana/baixa) + `confianca_score`/100** (es veuen TOTS DOS perquè poden divergir).
- **6 blocs editorials que cobreixen TOT el catàleg del municipi** (cap mètrica fora):
  - **A** Demografia i habitatge · **B** Turisme reglat · **C** Senyals físics per càpita · **D** Les 3 capes (inferència: pernocta/càrrega/pressió) · **E** Índex IETR (+ stock/impacte + energia EFG) · **F** Política (guanya + %indep/esq/xd).
- Cada fila reusa la pell `.ex__row` del Resum: **punt de procedència** (mesura slate / inferència porpra via `provenanceOf`) + valor formatat pel contracte (`formatMetric`/`pick`) + unitat curta editorial. **Mateixes regles d'honestedat** que el Resum: 0 d'OSM de la restauració = «sense dada» (`ZERO_IS_ABSENT`), gaps amb signe `+/−` (`SIGNED_PCT_KEYS`). **Cap xifra codificada.**
- **Selector de municipi** (sempre present): ordenat per nom localitzat (`Intl.Collator`), `onchange` → `goto(localizeHref('/municipi/${v}'))`.
- **Estat «sense dades encara»** per a `ine5` fora del Berguedà (resta de Catalunya): mateix gest amable que el tooltip del mapa (badge + h2 + cos + abast + sortides), **mai fitxa buida ni error lleig**. El selector hi segueix per saltar a un muni real.
- Chrome del design-system (`.ap-hero` + `.ds-main`/`.ds-sec`); CSS scoped propi només per als elements nous (selector, capçalera de muni, subtítols, estat buit) — el gros ve del design-system.

### 3. Navegació
- **Mapa → fitxa** (`mapa/+page.svelte`): el `ChoroplethMap` ja exposava `onselect` (abans només feature-state) → l'he cablejat a **`onMuniSelect`** que fa `goto(localizeHref('/municipi/${ine5}'))`, **només per als del Berguedà** (els de fora no naveguen; el hover ja els diu «sense dades»). El **`MapTooltip`** porta ara una **pista d'acció opcional** (`hint`): «Clica per obrir la fitxa →» (prop nou, default buit → cap usuari existent afectat).
- **Resum → fitxa** (`resum/+page.svelte`): el **nom** de cada fitxa d'extrem és ara un enllaç a `/municipi/[ine5]`, i la meta hi afegeix un enllaç curt «Fitxa completa →». CSS scoped propi (`.ex__name-link`, `.ex__fitxa`).

### 4. i18n ca/es
`messages/{ca,es}.json`: **22 claus noves** cadascun (chrome de la fitxa: títol/meta/eyebrow/lede; selector; 6 blocs + 3 subtítols; honestedat; srcline; estat buit; pistes `map_open_fitxa`/`resum_open_fitxa`). **Paritat 319/319.** Cap clau orfe (vaig retirar un `nav_municipi` que havia afegit i no enllaçava enlloc — la ruta es descobreix per mapa/Resum/selector, no per capçalera).

## Verificació
- **`npm run check`** → VERD (**0 errors, 0 warnings, 1047 fitxers**; Paraglide compila les 22 claus noves).
- **`npm run build`** → static OK · **31 `/municipi/[ine5]/` + 31 `/es/municipi/[ine5]/` prerenderitzats** (comptat al `build/`).
- **Prerender (build, HTML estàtic):** Berga `08022` → títol «Berga · Fitxa de municipi», pastilla «Capital de serveis», IETR escala, confiança, **30 mètriques** amb procedència, 6 blocs, valors reals (17.539 hab., CAT-JUNTS+), selector amb 31 opcions, 1 sol «n. d.» (l'EFG nul de Berga, esperat). Castellar/Gósol també 30 files + pastilla + IETR. `/es/...` amb chrome castellà natural («Ficha de municipio», «Demografía y vivienda», «Resumen comarcal»).
- **Preview EN VIU (DOM/`preview_eval`, port 5175):**
  - `/municipi/08022` (Berga): h1 «Berga», tipologia «Capital de serveis», IETR 0,3, confiança «mitjana» + 81/100, 6 blocs, **30 files (16 mesura + 14 inferència)**, selector 31 opcions value=08022.
  - **Selector navega:** seleccionar `08052` → `/municipi/08052/`, h1 «Castellar de n'Hug», IETR 89,4, «Poble d'excursió». ✅
  - **Estat buit:** `/municipi/08019` (Barcelona, fora) → badge «Sense dades encara», h2 «08019 encara no té dades», 2 sortides, **0 files de dada** (no fingeix), selector encara present. ✅
  - `/mapa`: mapa + canvas MapLibre munten, selector d'indicador 8 opcions, **0 errors de consola**.
- **Clic al mapa → fitxa:** wiring verificat per build/check (`onselect={onMuniSelect}` + `goto`+`localizeHref`, guardat al Berguedà). El **hit-test headless sobre el canvas MapLibre NO és fiable** (els `MouseEvent` sintètics no passen pel hit-test intern de MapLibre) — confirmat aquesta sessió. Però el **mecanisme** (`goto`+`localizeHref`) és **el mateix que el selector**, que SÍ navega en viu → garanteix que el clic també.

## Notes / disciplina
- Diff: **7 fitxers, tots dins `packages/web`** (2 nous: la ruta `municipi/[ine5]/{+page.ts,+page.svelte}`). NO s'ha tocat `data/`, `semantic/metrics.yml`, `packages/{ai,signals,ingestion,transform}`, `ci.yml` ni `.gitignore`. `static/data/` és gitignored (artefacte de Sondeig, el regenera el prebuild) → no es commiteja.
- Git **identity-inline** `Mirador <mirador@datapoble.local>`, sense trailer IA. Commit `943f943`, branca `feat/mirador-fitxa-municipi`, **PR #59**. Cos del commit/PR via heredoc (sense backticks que el bash es mengi).
- Worktree propi `_wt/mirador-f` off `origin/main`. **Vaig aturar el preview ABANS de tornar a git** (disciplina del vite al working tree). Committejat i pushat ABANS d'aquesta bitàcola.
- **`/es/municipi/[ine5]` també prerenderitza** (31): SvelteKit els descobreix pel crawling dels enllaços localitzats que vaig afegir al Resum/mapa, combinat amb `entries()`. (No depèn del fallback SPA, tot i que aquest també els cobriria.)
- Opcional del brief no fet (per no ampliar abast): cap entrada de «Municipis» a la capçalera (la ruta necessita un `[ine5]`; un landing sense muni seria estrany). Es reça per mapa/Resum/selector, com demanava el brief.
