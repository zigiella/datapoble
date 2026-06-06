# Mapa a alta fidelitat + «Paletes per visualització» + fix del render (Fase 2)

**Fecha:** 2026-06-06
**Autora:** Mirador
**Para:** Talaia (review + merge), Llegenda (consum del design-system), Directora d'Art (fidelitat al target)
**Tema:** `packages/web` — Fase 2: la pàgina **Mapa** a alta fidelitat (captures 03/04/06), el lliurable que faltava **«Paletes per visualització»** (`.pal-spec`, §B.3), i la **correcció del bug crític** pel qual el mapa es quedava a «Carregant el mapa…».
**Status:** avance / handoff

## Contexto
La Fase 1 (chrome + Resum) ja és a `main` i en producció. El **paquet de revisió**
(`_detallets/paquet-revisio-mapa/`) prioritzava 4 punts sobre l'estat en viu: (1) 🔴 el mapa no
es renderitza, (2) 🔴 falta la secció de paletes, (3) 🟠 capçaleres incoherents entre /resum i
/mapa, (4) 🟡 hero del Resum sense eyebrow ni èmfasi. El target exacte és
`design-system/reference/da-final/` (HTML + captures). El CSS de l'aplicació (incloent
`.map-grid`, `.map-stage`, `.pal-spec`…) i els tokens nous (`--dp-div2-*` teal↔porpra,
`--dp-cat-*`, `--ap-purple`) **ja vivien al design-system**: aquesta feina els CONSUMEIX.

## El bug del mapa: causa real i correcció

**Símptoma.** A `/mapa` apareixia el teló «Carregant el mapa…» i no es resolia mai.

**Diagnòstic (al navegador, Chromium headless).** El canvas de MapLibre **sí** que es creava
(`hasCanvas: true`), però l'estat es quedava amb el teló perquè **`map.on('load')` no s'emetia
mai** → la bandera `ready` no passava a cert. Cap error a la consola. La clau: MapLibre
s'inicialitza a `onMount` i **mesura el contenidor una sola vegada**; si en aquell instant el
contenidor té amplada/alçada **0 o degenerada** (hidratació de SvelteKit abans que el grid
resolgui la columna, o el contenidor momentàniament colapsat), el canvas WebGL **no completa la
primera renderització i `load` no arriba**. És exactament la pista de la revisió: «si `.map-stage`
neix amb alçada 0, MapLibre no pinta i es queda penjat; dóna-li alçada i crida `map.resize()`».

**Correcció** (`ChoroplethMap.svelte`):
- **`ResizeObserver`** sobre el contenidor: quan adquireix mida no-degenerada (>0) crida
  `map.resize()`, que força MapLibre a re-mesurar i **desbloqueja `load`**. També fa el mapa
  responsiu als canvis de columna/finestra.
- `map.resize()` de **seguretat** dins de `load` abans d'enquadrar; desconnexió de l'observer a
  `onDestroy`; i un `catch` a `init()` perquè un error no deixi la UI muda al teló.
- A més, el Mapa hi-fi munta el MapLibre **dins de `.map-stage`** (que ja porta `min-height:430px`):
  el contenidor té alçada garantida des del primer frame, cosa que **reforça** el fix.

**Verificat** (servidor del worktree, viewport real): `load` s'emet, **0 errors de consola**, i
`queryRenderedFeatures('mun-fill')` = **31 municipis** pintats. Canviar d'indicador recolora i
commuta llegenda + paleta sense incidència.

## Qué hicimos / decidimos

**1. Pàgina `/mapa` a alta fidelitat (`mapa/+page.svelte`, reescrita).**
- **Hero** amb `ContourField` (corbes etiquetades), eyebrow mono «Cartografia · 31 municipis ·
  geometria INE/IGN», **H1 Archivo** «Mapa **coroplètic**» i lede amb els ressaltats **càlid/porpra**
  (població invisible) i **teal** (menys gent que el registre). Les **etiquetes de les corbes són
  els talls REALS del gap** (de la classificació, formatats amb signe) — no decoració inventada.
- **Barra d'eines** `.map-toolbar` amb el `<select id="indicator">` (els 6 indicadors de
  `MAP_INDICATORS`, ordre editorial).
- **`.map-grid`**: a l'esquerra el `.map-stage` amb el **mapa coroplètic REAL** (el MapLibre dels
  31 munis); a la dreta `.map-side` amb:
  - **`.map-read`** «com es llegeix el color» — el text **canvia segons indicador** (gap: porpra =
    no vist / teal = menys gent / neutre = mitjana; seqüencial: clar = baix / fosc = alt).
  - **`.map-legend`** que **commuta divergent↔seqüencial** amb els **talls reals** de la
    classificació (5 classes), el mètode correcte al subtítol (divergent centrat a 0 · Jenks ·
    cuantils), i les mostres de color idèntiques a les que pinta el canvas (mateixa funció
    `divergingColors`/`rampColors`). Conserva «sense dada» (tramat) i «confiança baixa» (velat).

**2. «Paletes per visualització» (`.pal-spec`, §B.3) — el lliurable clau.** Després de `.map-grid`,
abans dels caveats. **3 targetes** (Divergent «gap» `--dp-div2-*` · Seqüencial «terra»
`--dp-exposure-*` · Qualitativa Okabe-Ito `--dp-cat-*`) + **taula indicador→paleta** (6 files).
**Wiring:** en cada canvi del selector, la targeta de la paleta de l'indicador actiu rep `.on`
(anell accent + badge «actiu»): **divergent** per al gap, **seqüencial** per a IETR/%/ràtio/residus.
La qualitativa documenta el contracte (mai s'activa amb els indicadors actuals).

**3. Color del coroplètic real.** El **gap** usa la rampa divergent **teal↔porpra `--dp-div2-*`**
(porpra = població que el padró no veu, lliga amb `--dp-prov-derived`); la resta, la seqüencial
**«terra» `--dp-exposure-*`**. (La lògica de classificació i el pont de color del canvas ja
existien de la F2 i materialitzen `palette.md §5`; aquí la pàgina hi-fi en consumeix els colors
per a la llegenda perquè **mapa i llegenda coincideixin**.)

**4. Dades reals, cap xifra inventada.** Valors, talls, etiquetes de rang i textos de la llegenda
surten del **dataset real** i de la **classificació** (`classify`/`classRangeLabels`/
`makeMetricFormatter`). El gap es formata com a desviació amb signe (+139 % / −21 %).

**5. i18n ca/es** complet per a tot el text nou del Mapa (eyebrow, H1, lede, indicadors, subtítols
de llegenda, «com es llegeix», les 3 paletes + taula, caveats, srcline). ~46 claus noves `map_*`.

**6. Punts 3 i 4 de la revisió: ja resolts per la Fase 1 — verificat, no calia tocar res.**
- **Capçalera** (punt 3): el `+layout.svelte` és **compartit** per /resum i /mapa; la sub-tagline
  és `brand_sub` = «Dades per entendre com s'habita el territori» (**no menciona el Berguedà**).
  Comprovat al navegador a les dues rutes.
- **Hero del Resum** (punt 4): manté l'eyebrow amb coordenades «42°16′N · 1°53′E» i el lede amb
  `<b class="warm">dos extrems</b>` + «de la pressió turística-residencial». Comprovat.

## Por qué
- **El fix per resize, no per timeout.** El problema de fons és de mida del contenidor a l'init, no
  de càrrega de dades; un `ResizeObserver` ataca la causa (i cobreix tant el cas real de 0px com la
  responsivitat). Evita hacks tipus «reintenta `ready` amb setTimeout».
- **Llegenda derivada de la mateixa classificació que el canvas.** Així els talls i els colors de la
  llegenda **no poden divergir** del que es pinta: una sola font de veritat (`classification` +
  `divergingColors`/`rampColors`). El mètode (divergent/Jenks/cuantils) també es mostra al subtítol,
  fidel al contracte editorial.
- **Consumir el design-system, no duplicar-lo.** Tot el CSS (`.map-*`, `.pal-*`) i els tokens
  (`--dp-div2-*`, `--dp-cat-*`, `--ap-purple`) ja eren a `aplicacio.css`/`tokens.css`. La pàgina
  només aporta **estructura + dades + wiring**; l'únic CSS local és encaixar el component de mapa
  dins de `.map-stage` (`.map-stage__live`).

## Verificación (Chromium headless, servidor del worktree)
- **`npm run check` → 0 errors, 0 warnings** (854 fitxers). **`npm run build` → prerender net**
  amb `adapter-static`, **cap problema de postcss** (comentaris CSS sense `*/` interns).
- **`/mapa` CA clar:** mapa carregat (sense teló), **31 munis pintats**, hero/eyebrow/H1 correctes,
  llegenda 5 classes amb talls reals («1 · −21 % – −10 %»…), `.pal-spec` 3 targetes amb la
  **divergent destacada**, taula 6 files, readnote en mode gap. La rampa divergent resol als tokens
  exactes (#0F6E66 teal → #EFEEE8 neutre → #5E3A86 porpra).
- **Canvi d'indicador → IETR (seqüencial):** la paleta `.on` passa a **seqüencial**, el readnote a
  «escala de terra», la llegenda a «seqüencial · Cuantils · 5 classes» amb talls reals d'IETR, i el
  canvas recolora. Sense errors.
- **`/es/mapa` (ES) i tema fosc:** tot traduït (eyebrow «Cartografía», H1 «Mapa coroplético»,
  «Paletas por visualización»…) i el mapa es pinta igualment; `.map-stage` fosc (#0C1014).
- **Límit de la verificació:** el **hover/tooltip** no s'exercita de forma fiable en headless (els
  esdeveniments sintètics de `mousemove` no disparen el sistema de gest de MapLibre — mateix límit
  documentat al PR #22). El wiring de hover/tooltip és **idèntic** al de la F2 ja verificada i
  mergejada; el tooltip es posiciona dins de `.map-stage__live` (relatiu).

## Nota d'entorn (per a qui verifiqui) — importante
El servidor de preview `riusdegent-web` del harness apunta a **`C:/DATA/PETS/datapoble/packages/web`
(el checkout principal, a `main`)**, no al worktree. Verificar-hi els canvis del worktree dóna
**falsos negatius** (vaig veure el mapa encallat perquè servia el codi vell sense el fix). Vaig
afegir una entrada `mirador-wt` (port 5174) a `P2-POBLE/.claude/launch.json` que apunta al worktree
i hi vaig fer tota la verificació. (Aquest `launch.json` és infra local del harness, **fora** del
repo; no toca `datapoble`.) Lliga amb la incidència de la Fase 1: el checkout principal és **només
lectura**.

## Decisiones para Talaia (revisión)
1. **Components orfes.** En passar a `<select>` natiu + llegenda inline (fidelitat al handoff),
   `MapIndicatorPicker.svelte` i `MapLegend.svelte` queden **sense cap referència** a tot `src/`.
   No els he esborrat en aquest PR per mantenir-lo focalitzat; he deixat un **chip de tasca de
   seguiment** per eliminar-los en un PR separat. Si ho prefereixes dins d'aquest, ho faig.
2. **Etiquetes de les corbes del hero = talls reals del gap.** Per no inventar xifres, les cotes del
   «full topogràfic» del hero són els extrems + talls de la classificació del gap (formatats). Si
   prefereixes els valors fixos del handoff (+176 %, +119 %…), són constants editorials i es canvia
   en una línia.
3. **`.pal-spec` viu a la pàgina Mapa** (no com a component reutilitzable). És específic d'aquesta
   vista; si en algun moment cal a un altre lloc, s'extreu a un component.
4. **Promoció de tokens (§8 del handoff):** `--dp-div2-*` (teal↔porpra) i `--ap-purple` ja són als
   tokens del design-system (Llegenda), així que **no calia capa de pàgina**. Res pendent per part
   de Mirador en aquest punt.

## Pendiente
- [ ] **Talaia:** revisar i mergear (CI verd esperat: `web build + check`).
- [ ] (seguiment) eliminar `MapIndicatorPicker.svelte` + `MapLegend.svelte` (orfes) — chip creat.
- [ ] (menor) recapturar el responsive < 880px del `.map-grid` (la columna passa a 1) i el hover/
      tooltip en un navegador real quan es validi en staging.

## Enlaces
- `packages/web/src/routes/mapa/+page.svelte` (pàgina hi-fi + `.pal-spec` + wiring)
- `packages/web/src/lib/components/ChoroplethMap.svelte` (fix del render: ResizeObserver + resize)
- `packages/web/messages/{ca,es}.json` (claus `map_*` noves)
- Target: `packages/design-system/reference/da-final/` (HTML + captures 03/04/06)
- CSS/tokens consumits: `packages/design-system/aplicacio/aplicacio.css` · `…/tokens/tokens.css`
- Paquet de revisió: `_detallets/paquet-revisio-mapa/` (README + Revisió + integració/)
