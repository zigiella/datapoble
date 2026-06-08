# Mapa de Catalunya amb el Berguedà ACTIU (Fase 0 de l'escala Catalunya) — Mirador

**Fecha:** 2026-06-08
**Autora:** Mirador
**Para:** Talaia (review + merge), Bea (qui ho va demanar: «convertir el mapa del Berguedà en un mapa de Catalunya amb el Berguedà actiu, anticipant la navegació a escala país»), Sondeig (FYI: faig servir la teva geometria del PR #54)
**Tema:** `packages/web` — `/mapa` passa de mostrar NOMÉS els 31 municipis del Berguedà a mostrar **TOT Catalunya** (els 947 municipis), amb la resta **atenuada** («sense dades encara») i el **Berguedà actiu** (el coroplètic, el selector i la llegenda d'abans, intactes). Capa de **límits de comarca** suaus per orientar. **Zoom inicial enquadrat al Berguedà**, amb el país de context al voltant.
**Status:** PR obert · CI pendent · per revisar i mergear (Talaia)

## Contexto
Sondeig (PR #54, a main: `1def890`) va deixar la **geometria de tot Catalunya** a `packages/web/static/geo/`:
- `catalunya-municipis.geojson` — **947 munis**, props `{ine5, nom}` (~1 MB simplificat).
- `catalunya-comarques.geojson` — **43 comarques**, props `{id, nom, cap}`.

El mapa anterior (`/mapa`) pintava el coroplètic del **Berguedà** (31 munis) des de `bergueda-municipis.geojson`. Bea vol l'escala país: el Berguedà actiu dins de Catalunya, la resta atenuada (honestedat: no fingim dada on no n'hi ha), límits de comarca per orientar, i el zoom inicial encara enquadrat al Berguedà. Sondeig va deixar la dada/geometria; jo NOMÉS he tocat la UI (`packages/web`).

## Decisions de Bea respectades
- **Tot Catalunya visible** (947 munis); els que NO són del Berguedà → **ATENUATS** (fill neutre clar `--dp-map-land`, opacitat 0,55), **MAI acolorits per l'indicador**.
- **Berguedà ACTIU:** els seus 31 munis acolorits pel coroplètic seleccionat (selector + llegenda + tooltip de procedència d'abans, sense canvis).
- **Límits de comarca SUAUS** a sobre (línia `--dp-map-label`, width 0,7, opacitat 0,35).
- **Zoom inicial al Berguedà** (no a tot Catalunya); el zoom-out revela el país atenuat.
- **Navegació anticipada:** hover sobre un muni de fora → estat amable «sense dades encara», NO un tooltip de dada buida.

## Què hem fet

### 1. Font ÚNICA de munis: `catalunya-municipis.geojson` (947), join per `ine5`
`routes/mapa/+page.ts`: el `load` ara carrega **en paral·lel** el dataset + `catalunya-municipis.geojson` + `catalunya-comarques.geojson` (abans: `bergueda-municipis.geojson`). NO es barreja amb el geojson del Berguedà (té una simplificació diferent i no encaixaria): **el Berguedà ja és DINS del de Catalunya** i el join és per `ine5`. Verificat que els 31 codis del Berguedà del dataset (incloent `25100` Gósol, a Lleida) **existeixen 1:1** dins del fitxer de Catalunya (0 missing).

### 2. `ChoroplethMap` reescrit a escala Catalunya (una source, capes per filtre)
`lib/components/ChoroplethMap.svelte`. Una sola source de municipis (`SRC='municipis'`, els 947) + una de comarques (`SRC_COM`). El **valor de l'indicador i la confiança només s'injecten als munis del Berguedà**; la frontera «té dades / no en té» es deriva de **`bergSet = new Set(Object.keys(dataset.municipis))`** (les claus del dataset = exactament els 31; el dia que entrin més comarques, s'amplia sol, sense llista codificada). `joinValues` posa `__inberg` a cada feature.

Capes (de baix a dalt), totes sobre la mateixa source amb `filter`:
- **`mun-base`** (`!__inberg`): atenuat, fill `--dp-map-land` opacitat 0,55 → «sense dades encara».
- **`mun-baseline`**: contorn tènue de TOTS els munis (estructura de fons, opacitat 0,5, width 0,4).
- **`mun-hatch`** (`__inberg && !__hasval`): tramat «sense dada» del Berguedà (igual que abans).
- **`mun-fill`** (`__inberg && __hasval`): el coroplètic real (mateixa expressió `step` data-driven sobre `__val`, mateixes rampes exposició/divergent, mateixa opacitat 0,55 per confiança baixa).
- **`mun-lowconf`** (`__inberg && __lowconf`): tramat semitransparent d'honestedat sobre el color.
- **`mun-line`** (`__inberg`): contorn una mica més marcat dels 31 (els distingeix del context atenuat).
- **`com-line`** (source comarques): límits de comarca suaus.
- **`mun-hover` / `mun-select`**: contorns per feature-state (a tot el país).

**Honestedat preservada:** la distinció és clara entre «sense dades encara» (munis de fora → base atenuada, fill pla apagat) i «sense dada de l'indicador» dins del Berguedà (→ tramat hatch). Són dos gestos visuals diferents per a dos significats diferents. La regla del 0 d'OSM de la restauració (`mapValue` → null → hatch) segueix intacta dins del Berguedà.

### 3. `fitBounds` inicial a la bbox del BERGUEDÀ (no a tot Catalunya)
`fitToBergueda()` recorre NOMÉS les features amb `ine5 ∈ bergSet` i hi enquadra (`padding: 36`). Verificat numèricament: bbox Berguedà `lng:[1,61, 2,07] lat:[41,90, 42,32]` és un **subconjunt estricte** de Catalunya `lng:[0,16, 3,32] lat:[40,52, 42,86]` → el zoom inicial mostra el Berguedà; el país queda de context. `minZoom` baixat de 7 a **6** perquè es pugui allunyar i veure tot Catalunya atenuat.

### 4. Hover/tooltip: Berguedà = dada+procedència; fora = «sense dades encara»
El payload de hover ara porta **`inBergueda`**. A `mapa/+page.svelte`:
- `inBergueda === true` → el `MapTooltip` d'abans (nom + dada + procedència + confiança + caveat d'inferència), sense canvis.
- `inBergueda === false` → una targeta amable nova (`.tip--outside`): nom del muni + **«Sense dades encara»** + una línia que explica que és fora del Berguedà + una nota d'abast («avui mesurem el Berguedà; la resta de Catalunya és context»). **Cap xifra, cap procedència** — només l'estat. Reusa l'embolcall `.tip` del design-system (mateixa restauració de superfície/tema que `MapTooltip`).

La capa `mun-base` és interactiva (s'afegeix a `interactive` del `wireInteractions`) perquè el hover «sense dades encara» funcioni sobre els 916 munis de fora.

### 5. Llegenda + eyebrow + i18n ca/es
- **Llegenda:** afegida una entrada nova **«sense dades encara (fora del Berguedà)»** (mostra de `--dp-map-land` atenuat), al costat de «sense dada / secret estadístic» i «confiança baixa». Així la llegenda explica els tres estats no-classe.
- **Eyebrow:** `map_eyebrow_b` passa de «31 municipis · geometria INE/IGN» a **«Berguedà actiu · Catalunya de context · geometria INE/IGN»** (anticipa l'escala).
- **i18n ca/es** (Paraglide els compila a `m.*()`): 5 claus noves —
  `map_outside_title` («Sense dades encara» / «Sin datos todavía»),
  `map_outside_sub`, `map_outside_scope`, `map_legend_dimmed`, i l'`map_eyebrow_b` actualitzat. El `map_title` («Mapa coroplètic del Berguedà») i el lede es mantenen: descriuen el que es MESURA (el Berguedà); Catalunya és context.

## Rendiment (947 polígons)
- **Una source per capa** (munis + comarques), no es duplica geometria. El color es resol per **expressió data-driven** (`step` sobre `__val`) i pels filtres `__inberg`/`__hasval`; en canviar d'indicador NOMÉS es fa `src.setData(...)` + `setPaintProperty('fill-color', ...)` (cap re-creació de capes, com abans).
- El `joinValues` recorre els 947 features un cop per canvi d'indicador (barat: és un `.map` sobre props, sense tocar geometria).
- Es manté el **`ResizeObserver` + `map.resize()`** (el fix del «mapa encallat» a 0px): verificat que quan el contenidor passa de col·lapsat a mida real, el canvas re-mesura i omple (784×538 amb finestra 1280×900).
- `static/geo/catalunya-municipis.geojson` ~1 MB (simplificat per Sondeig); es serveix com a actiu estàtic, `fetch` prerender-safe.

## Verificació
- **`npm run check`** → VERD (0 errors, 0 warnings, 1002 fitxers; Paraglide compila les claus noves).
- **`npm run build`** → static OK; `/mapa` i `/es/mapa` prerenderitzats.
- **Prerender (DOM, en viu i build):** eyebrow nou, selector amb els 7 indicadors, llegenda amb la fila «sense dades encara». Confirmat a `build/mapa/index.html` (CA: «Berguedà actiu · Catalunya de context», «sense dades encara (fora del Berguedà)») i `build/es/mapa/index.html` (ES: «Berguedà activo · Cataluña de contexto», «sin datos todavía (fuera del Berguedà)»). **Cap dels dos referencia ja `bergueda-municipis`** → la font és Catalunya.
- **Lògica de dades (test en Node sobre la dada real):** `bergSet`=31; **31 features inberg** (coroplètic) + **916 atenuades**; per `gap_pernocta_pct`: 31 amb valor, 0 hatch, **9 confiança baixa**; bbox Berguedà ⊂ bbox Catalunya (✓ fitBounds enquadra el Berguedà, no el país); comarques=43.
- **Preview WebGL:** com en sessions anteriors, el render headless es penja — la finestra de preview arrenca a 0px d'amplada i, en aquest entorn, **MapLibre no completa la càrrega de l'`style`** (`getStyle()` undefined, `isStyleLoaded()=false`) tot i tenir context WebGL i 0 errors de consola. Per això la verificació visual del canvas no és fiable aquí (ja documentat a la memòria). El que SÍ s'ha pogut verificar: 0 errors de consola, el canvas dimensiona correctament amb finestra real, i tota la lògica de capes/join/bbox per Node sobre la dada real.

## Notes / disciplina
- Diff: 5 fitxers, **tots dins `packages/web`** (`+page.ts`, `+page.svelte`, `ChoroplethMap.svelte`, `messages/ca.json`, `messages/es.json`). NO s'ha tocat `data/`, `semantic/`, `packages/{ai,signals,ingestion,transform}`, ni cap CI/.gitignore.
- `bergueda-municipis.geojson` queda al repo com a actiu estàtic però **ja no l'usa ningú** (es podria retirar en una neteja futura; no ho faig aquí per no ampliar l'abast).
- Per inspeccionar el mapa en viu vaig afegir TEMPORALMENT un hook `window.__map` (guardat per `import.meta.env.DEV`); **revertit** abans del commit (no és al diff).
