# Mapa coroplètic (MapLibre) + adopció del design-system + adapter static

**Fecha:** 2026-06-04
**Autora:** Mirador
**Para:** Talaia (review + merge), Llegenda (tokens/cartografia), Sondeig (mart real)
**Tema:** F2 de `packages/web` — vista `mapa` (MapLibre GL, coroplètic del Berguedà amb classificació cuantils/Jenks), adopció dels tokens reals + `sistema.css`, reconciliació de noms de token, i pas a `adapter-static` (Cloudflare Pages).
**Status:** avance / handoff

## Contexto
L'spec F2 demanava tres coses: (1) adoptar el **design-system mergejat** (`packages/design-system`) com a única font visual, reconciliant els noms de token que l'scaffold feia servir **per error** (`--dp-color-*`); (2) construir la vista **`mapa`** substituint el stub, segons `cartography/palette.md` (rampa `exposure`, 5 classes, cuantils/Jenks, hatch per "sense dada", llegenda amb mètode·classes·font·data, tooltip amb procedència); (3) deixar el build **estàtic** per a Pages. La web era un scaffold amb «Resum» feta i 5 stubs.

## Qué hicimos / decidimos
**1. Adopció del design-system (font única).**
- `src/app.css` ja **no defineix tokens**: importa `../../design-system/tokens/tokens.css` + `sistema/sistema.css` (ruta relativa — el monorepo no té workspaces npm i el design-system no es publica com a paquet; Vite resol el CSS).
- **Reconciliació** de noms (44 usos a 9 fitxers): `--dp-color-bg→--dp-bg`, `-surface→--dp-surface`, `-text→--dp-text`, `-muted→--dp-text-muted`, `-accent→--dp-forest`, `-border→--dp-border`, `-warning→--dp-warning`, `-accent-weak→--dp-accent-weak`. Cap `--dp-color-*` residual.
- Àlies d'**aplicació** (no de marca) que es deriven dels tokens: `--dp-maxw` (de `--maxw` de sistema), `--dp-radius`(→`--dp-radius-lg`), `--dp-accent-weak` (tint forest via `color-mix`).
- **Identitat**: Archivo als titulars (`--dp-font-display`), verd **forest**. Fonts Archivo+Inter+IBM Plex Mono carregades a `app.html` (Google Fonts, diacrítiques catalanes).

**2. Vista `mapa` (MapLibre GL).**
- `ChoroplethMap.svelte`: estil **autocontingut** (fons + geometria local, **sense tile-server**) → desplegable a Pages i funcional offline; basemap apagat amb `--dp-map-*`; coroplètic data-driven (`step` expression) amb la rampa `--dp-exposure-*`; **hatch** (canvas pattern) per "sense dada"; hover (`--dp-map-label`) i selecció (`--dp-map-highlight`) via feature-state. Només client (import dinàmic de maplibre-gl a `onMount`; la pàgina el guarda amb `{#if browser}`).
- `src/lib/map/classify.ts`: **cuantils** (R-7) i **Jenks** (Fisher–Jenks per DP), **5 classes per defecte**; `methodFor()` enruta IETR/IETR_rank→cuantils, magnituds crues→Jenks (palette.md §5). Testat: Jenks **aïlla l'outlier** (Castellar) a la seva classe; cuantils omplen la rampa.
- `src/lib/map/palette.ts`: espill dels hex `--dp-exposure-*` + mostreig de N colors (al canvas els colors han de ser literals; la llegenda HTML i el mapa usen els **mateixos** hex).
- `MapLegend.svelte` (sobre `.legend` de sistema): mètode + nº classes + rangs amb cifres tabulars + entrada "sense dada" (hatch) + **font·data** + nota de recàlcul a escala Catalunya.
- `MapIndicatorPicker.svelte`: `<select>` accessible amb 4 indicadors (IETR + `pct_noprincipal`, `rtc_per_1000hab`, `kg_hab_any`); **labels del contracte**, no codificades.
- `MapTooltip.svelte`: valor + **procedència** (`.prov--measured/-derived/-negative`, tokens `--dp-prov-*`) segons el `source` de la mètrica. Amaga la "unitat" quan és una escala (IETR "0-100") per no llegir-se confús.
- `mapa/+page.ts`: carrega el dataset (mock) i fa `fetch('/geo/…')` (funciona en prerender i client). La classificació es calcula a la pàgina i es comparteix mapa↔llegenda (talls idèntics).

**3. Geometria.**
- `static/geo/bergueda-municipis.geojson`: **31 municipis** del Berguedà, geometria **oficial** (Opendatasoft `georef-spain-municipio`, INE/IGN, CC-BY), `properties.ine5` = join_key. Generada per `tools/build-bergueda-geojson.mjs` (reproduïble). Aprimat sense dependències (5 decimals) → ~206 KB.
- **Trampa de codis documentada**: 30 municipis són província 08 (Barcelona) i **Gósol (25100) és a Lleida (25)** tot i ser del Berguedà.

**4. Estàtic per a Pages.**
- `adapter-auto`→**`adapter-static`** (`fallback: 404.html`); `+layout.ts` amb `prerender = true` + `trailingSlash = 'always'`. `npm run build` escriu un site estàtic a `build/` (rutes ca + `/es`, 404, asset geojson). Compte de Pages = IT.

**Verificació (headless Chromium + SwiftShader):** canvas render OK, **0 errors de consola**, selector reactiu (Cuantils↔Jenks), tooltip amb procedència, locale `es` traduït. `npm run check` i `npm run build` en **verd**.

## Por qué
- **Estil MapLibre sense tiles externes:** el coroplètic comarcal no necessita basemap ric; un estil autocontingut evita dependència de tile-server/clau, encaixa amb el principi "el dada resalta, el mapa s'apaga", i és trivialment desplegable a Pages estàtic.
- **Classificació a la pàgina (no al component):** mapa i llegenda han de compartir **exactament** els mateixos talls; calcular-los un cop i passar-los avall ho garanteix.
- **Geometria oficial ja, no provisional:** era viable sourcejar-la (Opendatasoft, INE5 directe), així el join amb el mart real serà immediat per `ine5`. Millor que geometria sintètica etiquetada.
- **`--dp-color-accent`→`--dp-forest` (no `--dp-link`):** els usos eren d'**èmfasi de marca** (verds), no enllaços navegacionals; els `<a>` ja els pinta `sistema.css` amb `--dp-link` (terracota).

## Honest boundaries
- **Dades = MOCK** amb forma de contracte. Només **2 municipis** tenen valors (Castellar 08052, Berga 08022); els altres **29 surten amb hatch ("sense dada")**. Per això la llegenda mostra ara **2 classes**, no 5: la lògica de 5 classes és correcta i s'**adapta** al nombre de valors únics; les **5 classes plenes apareixeran quan Sondeig empleni els 31 municipis** al mart. És el comportament honest, no un bug.
- **Geometria**: oficial, però aprimada només per arrodoniment (no Douglas–Peucker/topològic). Per a l'escala Catalunya (~947) caldrà simplificació topològica de debò (mapshaper) — anotat al build script.
- **IETR/derivats** del mock marcats "≈ il·lustratiu" (ve del scaffold); la **procedència** al tooltip és real (IETR→derivat).
- **Indicador població real vs padró** (Tasca B / #17): no toca aquí; el mapa ja llegeix `poblacio` del contracte quan existeixi.

## Pendiente
- [ ] **Sondeig:** publicar el mart amb els **31 municipis** (forma `MunicipisDataset`) → el mapa passa de 2 a 31 pintats i la llegenda a 5 classes plenes. Punt d'enganxament únic: `mapa/+page.ts` (i `mock/municipis.ts`).
- [ ] **Llegenda/Talaia:** validar la rampa `exposure` amb un valor real distribuït (avui només 2 punts); confirmar el tractament `diverging` per a `hab_per_hab` (desviació vs mitjana) com a segon mode del mapa.
- [ ] **Mirador (next):** capa d'etiquetes de topònim (glyphs) si es vol; mode diverging; vista `índex IETR` (taula `.tbl` + mapa enllaçats); tests (vitest per a `classify`, Playwright a11y).
- [ ] **Geometria:** simplificació topològica (mapshaper) en arribar a Catalunya.

## Enlaces
- Spec cartografia: `packages/design-system/cartography/palette.md`
- Tokens: `packages/design-system/tokens/tokens.css` · Components: `packages/design-system/sistema/sistema.css`
- Contrato: `semantic/metrics.yml` · Tipos: `packages/web/src/lib/contract/types.ts`
- Geometria: `packages/web/static/geo/bergueda-municipis.geojson` (build: `tools/build-bergueda-geojson.mjs`)
- Rama: `feat/mirador-mapa-f2`
