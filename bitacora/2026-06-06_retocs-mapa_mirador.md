# Retocs a /mapa segons feedback de Bea — marc, paleta del gap, tooltip, paletes, favicon

**Fecha:** 2026-06-06
**Autora:** Mirador
**Para:** Talaia (review + merge), Llegenda (consum del design-system), Bea (feedback de direcció)
**Tema:** `packages/web` — 5 retocs sobre la pàgina **`/mapa`** (Fase 2, en producció) demanats per la direcció humana. Bea passa per sobre del handoff `da-final` en aquests punts; aquesta entrada documenta cada decisió.
**Status:** avance / handoff

## Contexto
La pàgina `/mapa` ja és a `main` i en producció (alta fidelitat, captures 03/04/06). Bea, sobre l'estat en viu, demana 5 ajustos. Tres són correccions de bug visual (marc que retalla tooltips, paleta del gap equivocada, tooltip fosc en tema clar) i dos són neteja (treure un bloc intern i posar favicon). **Cap canvi al dataset, ni a `data/`, `packages/ai`, `packages/design-system` ni als workflows.** Tot viu dins de `packages/web`.

## Què hem fet / decidit

### 1. 🔴 Treure el marc decoratiu del mapa (retallava els tooltips)
El `.map-grid`/`.map-stage` del design-system embolcallava el MapLibre amb **fons de paper + corbes** (`.map-stage__contours`) i, crucialment, el `.map-grid` portava **`overflow:hidden`** → les targetes/tooltips de municipi que sobreeixien pel marc **quedaven retallades**.

Com que **no puc tocar `aplicacio.css`** (és de Llegenda), la solució és **estructural al `mapa/+page.svelte`**: substitueixo el `.map-grid`/`.map-stage`/`ContourField` del cos per una presentació pròpia (classes locals *scoped*):
- `.map-wrap` — graella local (mapa `1fr` | costat `326px`), **`overflow:visible`**.
- `.map-canvaswrap` — contenidor net del mapa, **`overflow:visible`**, sense paper ni corbes. El separador amb el panell lateral el dona ara `.map-wrap .map-side { border-left }`.
- El tooltip és **germà** del `<ChoroplethMap>` dins de `.map-canvaswrap` (no fill del `.map`), així pot sortir per dalt sense que el `.map` (que conserva el seu `overflow:hidden` necessari pel canvas WebGL) el talli.

> **Gotcha resolt:** amb `.map-canvaswrap { display:flex }`, el `.map` (flex-item) quedava al seu ample de contingut i el **canvas sortia estret (~134px)**. Solució: `.map-canvaswrap { display:block }` + `.map { display:block; width:100% }`. Verificat: canvas **785px** sobre contenidor 786px. El `ResizeObserver` ja existent al component re-mesura i no cal tocar res més del mapa.

**El hero conserva el seu `ContourField`** (corbes etiquetades amb els talls reals del gap): Bea només es queixa del marc *al voltant del mapa*, no del hero.

### 2. 🔴 Bug de paleta del GAP — ara teal↔porpra (no ocre/marró)
El gap **ja** anava pel camí divergent (`methodFor('gap_pct') → 'diverging' → divergingColors`), però `DIVERGING_STOPS` (a `lib/map/palette.ts`) era la família **BrBG llegat (teal↔MARRÓ)**: el costat positiu acabava en `#8C510A` passant per ocres `#DFC27D`/`#BF812D`. Això és exactament el «ocre/marró» que veia Bea.

**Correcció:** `DIVERGING_STOPS` passa a ser l'espill exacte de **`--dp-div2-0..6` (teal↔porpra)** dels tokens (DA final ronda 2): `#0F6E66 · #4FA8A0 · #B9DED9 · #EFEEE8 (neutre) · #CDB3DD · #9466B6 · #5E3A86`. La porpra lliga amb `--dp-prov-derived` (inferència) = «població que el padró no veu». Els hex coincideixen amb les variables CSS perquè **canvas i llegenda pintin idèntic** (el canvas WebGL no resol `--dp-*`). El neutre de la llegenda ja referenciava `var(--dp-div2-3)` → ara coherent.
La resta d'indicadors (IETR, % hab. no principal, establiments/1000, residus, població real est.) segueixen amb la **seqüencial terra `--dp-exposure-*`** — sense canvis.

### 3. Tooltip de municipi clar en tema clar
`.tip` de `sistema.css` és un *tooltip mock* amb **fons fix fosc** (`--dp-neutral-900`) i una fletxa `::after` — per això el tooltip sortia fosc fins i tot en `[data-theme=light]`. No puc tocar `sistema.css`; ho resolc al `<style>` *scoped* de `MapTooltip.svelte`, que té **més especificitat** (`.tip.svelte-xxxx` = 0,2,0 > `.tip` = 0,1,0):
- `background: var(--dp-surface)`, `color: var(--dp-text)`, `border: 1px solid var(--dp-border)` → **segueix el tema**.
- `.tip::after { display:none }` → neutralitza la fletxa fosca del mock (a més quedava fora de lloc amb el nostre posicionament propi).

### 4. Treure la secció «Paletes per visualització» (`.pal-spec`)
Bea: és documentació interna nostra, no cal al web públic. Eliminat el bloc `.pal-spec` sencer del `mapa/+page.svelte` (3 targetes div/seq/cat + taula indicador→paleta + lede + nota). A més, **netejades les 19 claus i18n òrfenes** `map_pal_*` de `messages/ca.json` i `messages/es.json` (verificat que ja no es referencien enlloc del codi viu). La referència a `design-system` (com a font de veritat de les paletes) es conserva al codi i als comentaris.

### 5. Favicon visible a la pestanya
- Copiat **`packages/design-system/brand/favicon.ico`** → **`static/favicon.ico`** (ICO de 16/32/48, vàlid).
- `app.html`: ara hi ha els links correctes — `rel="icon" type="image/svg+xml"` (svg modern, principal), `rel="alternate icon" type="image/x-icon"` (ico, fallback navegadors sense SVG) i `rel="shortcut icon"` (compatibilitat).

## Verificació (navegador, Chromium headless · worktree)
Inspecció determinista via `preview_eval`/`preview_inspect` (el screenshot sobre canvas MapLibre es penja — patró conegut; no és error de la pàgina). A `/mapa/`:
- **Marc:** `.map-stage` absent, `.map-wrap` present, canvas pintat **785px** (omple l'ample), i **cap dels 8 ancestres del `.map-canvaswrap` té `overflow:hidden`** → els tooltips no es poden retallar. `overflow` de `.map-wrap` i `.map-canvaswrap` = `visible`.
- **Paleta gap:** indicador per defecte `gap_pct`; colors de la llegenda = **teal→porpra** (`#429C94 … #784F9D`), **cap marró**.
- **Tooltip clar:** la regla *scoped* `.tip` (amb `--dp-surface`) guanya en especificitat; en `[data-theme=light]` resol a **fons blanc + text fosc + vora clara**; fletxa fosca amagada. En dark, `--dp-surface` = `#1B212A` → segueix el tema.
- **Paletes:** `.pal-spec` absent; 142 → **123** claus i18n a cada locale (−19, simètric); `$schema` conservat.
- **Favicon:** els 3 `<link>` al `<head>`; `favicon.svg` (200, `image/svg+xml`) i `favicon.ico` (200) es serveixen.
- **`npm run check`** i **`npm run build`** → **VERDS** (0 errors, 0 warnings; build static OK). Cap `*/` dins comentaris CSS.

## Decisions per a Talaia (review)
- Els retocs 1 i 3 s'han fet **sense tocar `design-system`** (jurisdicció de Llegenda): el marc i el fons fosc del tooltip vénen d'`aplicacio.css`/`sistema.css`, i els he *sobreescrit* des de la jurisdicció web (markup propi + CSS scoped de més especificitat). **Suggeriment:** quan Llegenda toqui el design-system, valdria la pena (a) marcar `.map-grid`/`.map-stage` com a *opcional* o oferir una variant sense marc, i (b) fer que `.tip` de `sistema.css` usi `--dp-surface` en comptes del fosc fix, perquè altres consumidors no repeteixin l'*override*.
- El retoc 2 és un **canvi d'1 constant** (`DIVERGING_STOPS`) que ja estava previst pel contracte (`--dp-div2-*` existia als tokens des de la ronda 2); el render del gap ara hi és fidel.
- Les 19 claus `map_pal_*` les he **tret** (eren òrfenes). Si en algun moment es vol una pàgina interna de paletes (no pública), es recuperarien del git.
