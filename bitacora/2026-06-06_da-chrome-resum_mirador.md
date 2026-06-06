# DA final a la web — chrome compartit + Resum a alta fidelitat (Fase 1)

**Fecha:** 2026-06-06
**Autora:** Mirador
**Para:** Talaia (review + merge), Llegenda (consum del design-system), Directora d'Art (fidelitat al target)
**Tema:** `packages/web` adopta el **disseny d'aplicació final** de la DA (ronda 2, ocre): capçalera + peu compartits i la pàgina **Resum** recreades a alta fidelitat sobre el contracte de tokens `--dp-*`. El **Mapa es deixa per a la Fase 2**.
**Status:** avance / handoff

## Contexto
Llegenda va mergear la DA final al design-system (PR #26): `packages/design-system/aplicacio/`
(CSS+JS de pàgina), `sistema/` (chrome), tokens nous (**marca = `--dp-brand` ocre #B5612A**,
paleta gap `--dp-div2-*`) i la marca SVG nova. La carpeta `reference/da-final/` porta el
**target exacte**: 7 captures + l'HTML que enllaça els CSS reals. La web encara duia el chrome
provisional de F1 (shell verd, sub-tagline "Observatori territorial del Berguedà", sense
commutador de tema) i un Resum bàsic. Aquesta entrada porta el chrome i el Resum al nivell
del target, consumint el design-system (no el toco).

## Qué hicimos / decidimos

**1. Adopció de tokens i marca (ocre).**
- `src/app.css` ara importa també `../../design-system/aplicacio/aplicacio.css` (ja importava
  `tokens.css` + `sistema.css`). Tota la pell de pàgina ve d'allà; no es redefineix cap `--dp-*`.
- SVG de marca nous + favicon ocre copiats a `static/brand/` i `static/favicon.svg`. El wordmark
  `degent` i l'eyebrow surten de `--dp-brand` (clar) / `--dp-brand-dark` (fosc) via les regles del
  design-system. **Es retira el verd com a marca.**
- `app.html`: afegida **IBM Plex Serif** (missió del peu) i un **script anti-FOUC** que fixa
  `data-theme` a `<html>` abans del primer pintat (evita el flaix clar→fosc).

**2. Chrome compartit (`+layout.svelte`), captures 01 i 07.**
- **Capçalera `.ds-top`** (sticky): marca SVG + wordmark **rius**·**degent** + sub-tagline mono
  «**Dades per entendre com s'habita el territori**» / «Datos para entender cómo se habita el
  territorio» (**no menciona el Berguedà**, com demana la spec). Nav amb Resum/Mapa actius
  (enllaços localitzats) i Índex/Excursionista/Política/Pregunta-li **inerts**. A la dreta,
  commutador **idioma CA/ES** + **tema clar/fosc amb icones sol/lluna**.
- **Peu `.ap-foot`** de 4 columnes (marca+missió serif+segell «Cap xifra sense procedència» ·
  Explora · El projecte · controls idioma/tema) + barra inferior legal amb coordenades i data.
- Components nous: **`ThemeSwitcher.svelte`** (aplica `data-theme`, persisteix `rdg-theme`),
  **`LangSwitcher.svelte`** reescrit amb la pell `.langer`, i **`ContourField.svelte`** — un
  **port en TS/SSR-safe** del generador de corbes de nivell de la DA (`aplicacio.js · drawField`),
  que dibuixa els anells + etiquetes de dada real + divisòria puntejada del hero i del peu.

**3. Pàgina Resum a alta fidelitat (captures 01 i 02).**
- Hero amb **eyebrow mono** (Observatori · Berguedà · 31 municipis · 42°16′N), **H1 Archivo**
  «Resum **comarcal**» (comarcal en accent), lede, i **corbes etiquetades al marge dret** (la
  màscara `.ap-hero__field` les confina a la dreta perquè el text de lectura quedi net).
- **5 fitxes KPI** comarcals amb número Archivo, unitat petita, etiqueta, **punt de procedència**
  (mesurada slate `--dp-prov-measured` / derivada porpra `--dp-prov-derived`) i **font en mono**.
- **«Dos extrems»**: **eix IETR 0–100** amb Berga (0,3) a l'esquerra i Castellar (89,5) a la dreta
  (els `left:%` són el valor IETR real), + **2 fitxes de municipi** (rànquing pill, IETR gran, 10
  files amb punt de procedència i 2 files ressaltades), caveats del contracte (IETR estructural +
  lectura ecològica) i srcline.

**4. Dades del contracte, cap xifra inventada.** El markup és fidel al target però **tots** els
valors, etiquetes, unitats i fonts surten del dataset real (`data/web/municipis.bergueda.json`,
forma `MunicipisDataset`) via `formatMetric`/`pick`. La procedència de cada punt es dedueix del
`source` amb `provenanceOf` (reusat de `map/provenance.ts`). Comprovat que les xifres del target
coincideixen amb el dataset (41.523 · 593 · 14,3‰ · 33,8% · 452,4 kg; Castellar IETR 89,5 rank 1;
Berga IETR 0,3 rank 31; etc.).

**5. i18n ca/es** per a tot el text nou (sub-tagline, nav, eyebrow, H1, lede, KPI, eix, fitxes,
caveats, srcline, peu).

## Por qué
- El target separa **magnitud** (KPI, fitxes) de **mètode/procedència** (punts slate/porpra, font
  mono, caveats): respecta el contracte editorial "cap xifra sense procedència". Reproduir-ho amb
  les classes del design-system (i no estils propis) garanteix que quan Llegenda toqui tokens, la
  web hi vagi sola.
- El doble símbol de `%`: `formatMetric`/`percent` ja imprimeix "74,3 %"; el target vol "74,3" +
  «%» petit com a unitat. Es va afegir `fmtValue()` que **per a percent retorna el número pelat**
  (via `formatDecimal`) i deixa el «%» al markup — sense tocar el formatador genèric (que el
  Mapa fa servir amb una altra semàntica de gap).

## Verificación (headless Chromium, vite preview del build del worktree)
- `npm ci` OK. **`npm run check` → 0 errors, 0 warnings** (809 fitxers). **`npm run build` →
  prerender net** amb `adapter-static`.
- Captures comparades amb el target (01/02/05/07) en **CA clar** i **ES fosc**:
  - `--dp-brand` resol a `#b5612a`; wordmark `degent` = ocre en clar (rgb 181,97,42) i ocre clar
    en fosc (rgb 232,181,103). `data-theme` s'aplica abans del pintat (anti-FOUC OK).
  - Resum: H1 "Resum comarcal."/"Resumen comarcal.", 5 KPI, 20 files d'extrem (10×2), eix amb
    pins Castellar 89,45% / Berga 0,3%. Percentatges sense doblar el «%». Peu de 4 columnes amb
    corbes. **Cap clau i18n sense resoldre.**
- **Límit de la verificació:** el *hover* sobre el canvas del Mapa (Fase 2) no s'exercita aquí;
  el Mapa només es comprova que **segueix compilant** (entra al prerender).

## Incidencia (i com es va recuperar) — para que no se repita
Per error, la **primera tanda d'edicions de codi va anar al repo principal**
`C:\DATA\PETS\datapoble` (que està a **`main`**), no al worktree `_wt/mirador`: vaig llegir els
fitxers de referència del repo principal i, per inèrcia, hi vaig **escriure** els canvis de `src/`.
El primer commit del worktree (722fa7b) només va capturar els SVG (copiats amb `cp`). En verificar,
la web servia el chrome vell → es va detectar.
**Recuperació:** es van **copiar** els fitxers editats del repo principal al worktree, es va
**`git restore`** el repo principal a net (i esborrar els 2 components nous que hi havien quedat),
deixant `main` **intacte** (només els CSV untracked preexistents). Tot el codi viu ara al worktree,
build i check verds. **Aprenentatge:** treballar sempre amb paths absoluts del worktree; el repo
principal és **només lectura** per a referència.

## Decisiones para Talaia (revisión)
1. **Fidelitat com a objectiu:** el markup segueix el target gairebé literal, però sempre amb
   dades del contracte. Si vols menys densitat a les fitxes (10 files), es retalla `fichaKeys`.
2. **`ContourField` (corbes) reimplementat en Svelte/TS** en comptes de carregar `aplicacio.js`
   (que toca el DOM imperativament i no encaixa amb SSR/Svelte 5). És determinista i `aria-hidden`.
   Si prefereixes treure les corbes en `prefers-reduced-motion` o en mòbil, és trivial.
3. **`prerender.entries` explícites** a `svelte.config.js`: el nou nav només enllaça Resum/Mapa,
   així que les rutes stub ja no es descobreixen per crawling; les declaro perquè es prerenderitzin
   igual (segueixen accessibles per URL directa). Alternativa: eliminar-les del tot quan toqui.
4. **Unitats curtes de les fitxes** ("hab.", "‰") són **editorials** (el contracte dona la unitat
   llarga); les trio per coincidir amb la captura. Documentat al codi (`SHORT_UNIT`).

## Pendiente
- [ ] **Talaia:** revisar i mergear (CI verd esperat: `web build + check`).
- [ ] **Fase 2 (Mirador):** portar el **Mapa** a la DA final (marc `.map-grid`, lectura "com es
      llegeix el color", llegenda divergent/seqüencial, `.pal-spec` de paletes) amb el MapLibre
      real ja existent. El hero del Mapa i el seu i18n també segueixen el target (captures 03/04/06).
- [ ] (menor) el segell pledge del peu i el responsive < 760px no s'han recapturat a fons; revisar
      en mòbil quan es tanqui la Fase 2.

## Enlaces
- `packages/web/src/routes/+layout.svelte` (chrome) · `…/routes/resum/+page.svelte` (Resum)
- `packages/web/src/lib/components/{ThemeSwitcher,LangSwitcher,ContourField}.svelte`
- `packages/web/src/app.css` (import aplicacio.css) · `…/src/app.html` (anti-FOUC + Plex Serif)
- `packages/web/svelte.config.js` (prerender.entries) · `packages/web/messages/{ca,es}.json`
- Target: `packages/design-system/reference/da-final/` (captures 01/02/05/07 + HTML)
- Font de dades: `data/web/municipis.bergueda.json` (Sondeig)
