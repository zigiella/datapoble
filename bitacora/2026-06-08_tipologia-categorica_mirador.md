# Tipologia categòrica al mapa + confianca_score (Fase 1) — Mirador

**Fecha:** 2026-06-08
**Autora:** Mirador
**Para:** Talaia (review + merge), Bea (vot narratiu/marca), Sondeig (FYI: consumeixo les 4 mètriques que vas afegir al PR #57)
**Tema:** `packages/web` — exposa al frontend la **Fase 1** (PR #57 de Sondeig): la **`tipologia`** d'habitança com a indicador **CATEGÒRIC** del mapa (la joia narrativa: «quin TIPUS de pressió», no «més/menys»), el **`confianca_score`** (0-100) al costat de la bandera de confiança, i el tipus destacat a les fitxes del Resum.
**Status:** PR #58 obert · **CI VERD** (web build+check, repo structure, ai evals — tots pass) · per revisar i mergear (Talaia)

## Contexto
Sondeig (PR #57, a main: `84ff236`) va deixar 4 derivats nous al mart + contracte + JSON web, sobre senyals que ja hi eren (docs/tipologia-municipal.md):
- **`tipologia`** — categòrica, 6 valors snake_case (`capital_serveis`, `segona_residencia`, `excursio`, `dormitori_invisible`, `buit_administratiu`, `indeterminat`).
- **`confianca_score`** — 0-100 auditable (complementa l'etiqueta `confianca`).
- **`IETR_stock` + `IETR_impact`** — els dos costats de l'IETR.

Jo NOMÉS he tocat la UI (`packages/web`). El mapa fins ara tractava tots els indicadors com a numèrics (seqüencial Jenks/cuantils o divergent del gap). La tipologia és el primer indicador **categòric**: el color ha de comunicar IDENTITAT (quin tipus), no ordre.

## Decisions de disseny
- **Paleta categòrica** (nova, `lib/map/tipologia.ts`) — 6 colors distingibles, CVD-raonable, coherent amb la marca i la procedència del projecte:
  - `capital_serveis` → **ocre de marca** `#B5612A` (la pressió estructural «de debò», l'àncora càlida).
  - `segona_residencia` → **porpra d'inferència** `#7A5BA6` (= `--dp-prov-derived`: llits que s'omplen = població que el padró no veu = inferència).
  - `excursio` → **ambre** `#E1A23A` (activitat de dia, transitòria; càlid però clar, separat de l'ocre per lluminositat).
  - `dormitori_invisible` → **verd-teal** `#3E9B8E` (fred, distingible de la porpra).
  - `buit_administratiu` → **blau apagat** `#5E7FA6` (micromunicipi tranquil, serè).
  - `indeterminat` → **gris càlid neutre** `#ADA89B`.
- **Honestedat (`indeterminat`):** és un estat HONEST (territori mixt, **15 dels 31** municipis), NO un buit lleig. Va en gris neutre — l'única tinta no saturada — i a la llegenda/Resum l'etiqueta surt en to apagat/itàlica perquè es llegeixi com a «el model no força una narració», no com a error. **Diferent del tramat «sense dada»** (que és secret estadístic / buit de mapejat): `indeterminat` SÍ es pinta, en neutre.
- **Paleta categòrica SEPARADA de les rampes de dada** (`--dp-exposure` / `--dp-div2`): la categòrica no comunica ordre. La mantinc en un mòdul propi.
- **El selector encapçala amb «Tipologia»** (la joia narrativa). El **defecte segueix sent `gap_pernocta_pct`** (la signatura «població invisible» del projecte; el hero està construït sobre els valors del gap — no el trastoco).

## Què hem fet

### 1. Diccionari de presentació ca/es (`lib/map/tipologia.ts`, NOU)
Els 6 valors snake_case → **etiqueta humana + frase curta** del que vol dir, via i18n (les cadenes vénen de `messages/{ca,es}.json`, no es codifiquen al mòdul). Exporta `TIPOLOGIA_ORDER` (ordre editorial + color + label() + blurb()), `tipologiaMeta/Color/Label/Blurb()`, `isCategorical()` i `tipologiaMatchExpression()` (l'expressió `match` de MapLibre). Castellà revisat perquè soni natural: «Capital de servicios», «Pueblo de segunda residencia», «Pueblo de excursión», «Dormitorio invisible», «Vacío administrativo», «Indeterminado».

### 2. `classify`: nou mètode `'categorical'`
`lib/map/classify.ts`: `ClassMethod` += `'categorical'`; `CATEGORICAL_KEYS = {tipologia}`; `methodFor('tipologia')='categorical'`. `classify()` fa **curtcircuit** per categòric (no calcula talls numèrics; retorna una classificació degenerada amb `n` = nombre de munis amb categoria) — així la pàgina pot distingir el mode sense intentar números sobre text.

### 3. `ChoroplethMap`: fill categòric per `match`, no `step`
`lib/components/ChoroplethMap.svelte`:
- `fillColorExpression(c, key)` ara rep la clau: si és categòric → **`['match', ['get','__cat'], val0,color0, …, fallback]`** (del diccionari de tipologia); si no → la rampa `step` d'abans.
- `joinValues` injecta **`__cat`** (la cadena d'arquetip) per al cas categòric i posa **`__hasval`** segons si l'arquetip és conegut (inclou `indeterminat`, que SÍ es pinta). Confiança baixa segueix velant (tramat `__lowconf`).
- El payload de hover porta ara **`confScore`** (0-100). `mapValue` ja deixa passar les cadenes, així que el valor de la tipologia arriba al tooltip sense canvis.

### 4. `mapa/+page.svelte`: selector + llegenda categòrica + read
- `tipologia` al `INDICATOR_LABEL` i a `MAP_INDICATORS` (encapçala). `catMode = method==='categorical'`.
- **Llegenda categòrica nova** (`{#if catMode}`): graella de 6 files (swatch + etiqueta humana + frase curta), sub «categòric · 6 tipus · un color per arquetip». L'`indeterminat` amb classe `r--neutral` (to apagat). CSS scoped propi (`.map-cls--cat`).
- `map-read` mostra el text categòric (`map_read_cat`). Caveat propi (`map_caveat_tipologia`) al bloc d'alertes. `confScore` passat al `MapTooltip`.

### 5. `MapTooltip`: tipologia + frase + confianca_score
`lib/components/MapTooltip.svelte`: en mode tipologia, el «valor» és l'**etiqueta humana** (no el snake_case, mida menor perquè un nom llarg respiri) + la **frase curta** sota + el **caveat de tipologia** («lectura narrativa, no cens»). La **confiança** mostra ara **bandera + score** (`hasScore`): es veuen TOTS DOS perquè poden divergir.

### 6. `resum/+page.svelte`: el tipus destacat + score a les fitxes
A la capçalera de cada fitxa (Castellar/Berga): **pastilla de tipologia** (color de l'arquetip via `--tipo-c` + etiqueta humana + frase curta) i una línia de **confiança = bandera + `confianca_score`/100**. CSS scoped nou (la pàgina no en tenia; la resta del chrome ve del design-system). `{@const}` moguts al nivell del `{#each}` (no poden ser fills directes d'un `<div>` — ho va enganxar el compilador).

### 7. types + i18n
`contract/types.ts`: `MetricKey` += `tipologia`, `confianca_score`, `IETR_stock`, `IETR_impact`. `messages/{ca,es}.json`: 18 claus noves cadascun (label indicador, read-cat, leg-cat-sub, 6×{label,blurb}, 2 caveats, score-label), **paritat 297/297**.

## El cas que demostra l'honestedat (Castellar)
**Castellar de n'Hug:** `tipologia='excursio'`, `confianca='alta'` però `confianca_score=32,8`. Els residus diuen «molta gent», l'elèctric diu «poca» (calefacció de llenya a muntanya trenca el senyal) → els senyals divergeixen → el score baixa. **Es veuen els dos** (bandera + score) al mapa i al Resum: el score és el costat fi i honest de la tensió, no s'amaga. Berga, en canvi: `capital_serveis`, score 80,9 (senyals coherents).

## Verificació
- **`npm run check`** → VERD (**0 errors, 0 warnings, 1021 fitxers**; Paraglide compila les 36 claus noves).
- **`npm run build`** → static OK; `/mapa`, `/es/mapa`, `/resum`, `/es/resum` prerenderitzats.
- **Prerender (build):** selector amb «Tipologia d'habitança» / «Tipología de habitación del territorio» encapçalant; Resum pinta Castellar=«Poble d'excursió» (score 33/100) i Berga=«Capital de serveis» (score 81/100); ES natural.
- **Preview EN VIU (DOM/`preview_eval`, port 5174):** aquesta sessió el render WebGL **SÍ** ha carregat i s'ha pogut verificar a fons:
  - Selector: 8 opcions, `tipologia` primera, defecte `gap_pernocta_pct`.
  - En seleccionar tipologia: llegenda categòrica amb **6 files**, colors correctes (ocre/porpra/ambre/teal/blau/gris), `indeterminat` amb `r--neutral`; header «Tipologia d'habitança», sub «categòric · 6 tipus…».
  - **Tooltip (hover headless que va caure sobre Gósol):** «Gósol» · «Tipologia d'habitança» · **«Poble de segona residència»** + frase + «Confiança: alta · 62/100» + caveat de tipologia. (Confirma tooltip categòric + score en viu.)
  - Resum ca i es: pastilles + confiança+score correctes (Castellar 33/100, Berga 81/100).
  - **0 errors/warnings de consola** (una expressió `match` mal formada s'hi veuria).
- **Dada (re-fetch de l'asset en viu + replicació del mapeig):** 31 munis, **tots amb tipus reconegut** (0 a hatch), **6 colors distints** en ús, recompte per tipus = doc (capital 6 / segona_residència 5 / indeterminat 15 / excursió 2 / buit 2 / dormitori 1).

## Notes / disciplina
- Diff: **10 fitxers, tots dins `packages/web`** (1 nou: `lib/map/tipologia.ts`). NO s'ha tocat `data/`, `semantic/metrics.yml`, `packages/{ai,signals,ingestion,transform}`, CI ni `.gitignore`.
- Git **identity-inline** `Mirador <mirador@datapoble.local>`, sense trailer IA. Commit `0f7c56f`, branca `feat/mirador-tipologies`, **PR #58**. (Vaig haver d'amendar el missatge: els backticks del cos en bash s'havien menjat dues paraules — ara intacte via heredoc. No s'havia pushat encara, amend segur.)
- **IETR dual (`IETR_stock`/`IETR_impact`)**: deixats al `MetricKey` (i ja al JSON), però **NO afegits com a indicadors del mapa** en aquesta PR (l'opcional del brief). El desglossament és més de fitxa/glossari que de coroplètic; ho deixo per a una PR pròpia si Talaia/Bea ho volen, per no ampliar l'abast d'aquesta (que ja és gran amb el categòric).
- Llançament: vaig aturar el preview ABANS de tornar a git (disciplina del vite al working tree).
