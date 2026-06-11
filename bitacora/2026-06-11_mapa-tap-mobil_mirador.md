# Tàctil al mapa: tap mostra la targeta i no navega (sprint mòbil #2)

**Fecha:** 2026-06-11
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea
**Tema:** segona peça de l'**sprint de mòbil** (backlog 2026-06-10, #2): a mòbil el *hover* no existeix → el tap navegava de cop sense ensenyar la dada.
**Status:** fet, verificat (check + build + preview); el tàctil fi el confirma la Bea al telèfon / handoff

## Contexto
El patró del mapa era d'escriptori pur: `mousemove` → targeta (hover), `click` → navega a la fitxa. A tàctil no hi ha `mousemove`, així que el primer toc ja navegava: l'usuari no veia mai la dada+procedència. El backlog #2 demanava **desacoblar**: *tap = mostra* (no navega); un **CTA dins la targeta** és qui obre la fitxa; *tap al fons = tanca*. Aplica a `mapa`, l'**atles** (reusa el mateix component de mapa) i la **constel·lació** (el tooltip era hover).

## Què he fet
Detecció de punter gruixut **`matchMedia('(pointer: coarse)')`** a cada component (a mòbil cert; a escriptori i a portàtils tàctils amb ratolí primari, fals → comportament de sempre).

- **`ChoroplethMap.svelte`** (mapa + atles):
  - Refactor: la càrrega del tooltip s'extreu a `buildHover(feat, point)` (compartida per hover d'escriptori i tap mòbil; mateixos camps que abans).
  - A **coarse**, el `click` sobre un municipi **selecciona i MOSTRA la targeta** (`onhover`) i **no** crida `onselect` → no navega. A escriptori, igual que abans (hover mostra, clic navega).
  - Nou: **tap al fons** (sense municipi) → `queryRenderedFeatures` buit → tanca la targeta i treu la selecció.
- **`MapTooltip.svelte`**: props noves `href` i `touchMode`. Si hi ha `href`, la pista d'acció és un **enllaç** (`<a>`) en lloc de text; a `touchMode` la targeta capta el toc (`pointer-events:auto`) amb àrea de toc còmoda, perquè el CTA «obrir fitxa» sigui tocable.
- **`mapa/+page.svelte`**: calcula `coarse`, passa `touchMode` + `href` (fitxa del municipi) i el text del CTA tàctil (`map_open_fitxa_touch` = «Obrir fitxa →» en lloc de «Clica per obrir…»).
- **`StockImpactScatter.svelte`** (constel·lació): a coarse el hover (`pointerenter/leave`) es desactiva; el **tap** (`pointerup`) sobre un punt **fixa/commuta** el seu tooltip i un **tap al fons** el tanca. A escriptori, hover igual.
- i18n nou: `map_open_fitxa_touch` (ca/es).

## Decisions
- **Heurística `(pointer: coarse)`** (no `maxTouchPoints`): mira el punter PRIMARI → els portàtils tàctils amb ratolí mantenen hover+clic; només els mòbils de debò entren al mode tap. Cost: el preview headless no l'emula (vegeu sota).
- **`href` sempre present a la targeta** (també a escriptori): a escriptori la targeta té `pointer-events:none`, així que l'enllaç és cosmètic i no genera doble navegació; simplifica i és honest (la targeta «és» d'aquell municipi).
- A tàctil faig servir `pointerup` (no `click`) per al toc: evita la regla a11y `a11y_click_events_have_key_events` (que el `svelte-ignore` no atrapava) i dispara `a11y_no_*_interactions`, que sí se suprimeix.

## Verificación
- `npm run check` → **1104 fitxers, 0 errors, 0 warnings**. `npm run build` → OK.
- Preview `mapa`: carrega net (canvas + toolbar, **0 errors** de consola).
- Preview `resum` (escriptori): constel·lació amb 31 punts; hover mostra el tooltip i `leave` l'amaga → **cap regressió** del camí d'escriptori després del guard `coarse`.
- **Límit conegut:** el preset mòbil de Playwright **no emula `(pointer: coarse)`** (reporta `fine:true` tot i `maxTouchPoints:10`) i el hover de MapLibre no respon a esdeveniments sintètics en headless. Per tant el camí TÀCTIL queda verificat per **codi + lògica**; el toc fi el confirma la **Bea al telèfon** (com a la peça #1).

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] **Bea:** provar al telèfon (tap mostra targeta → CTA obre fitxa → tap fora tanca) al mapa, l'atles i la constel·lació.
- [ ] (sprint mòbil) revisar amplada de la targeta a pantalles molt estretes (pot tocar vora); si molesta, clamar `x` als límits del contenidor.

## Enlaces
- `packages/web/src/lib/components/ChoroplethMap.svelte` · `MapTooltip.svelte` · `StockImpactScatter.svelte`
- `packages/web/src/routes/mapa/+page.svelte` · `messages/{ca,es}.json` (`map_open_fitxa_touch`)
- backlog: `bitacora/2026-06-10_backlog-preguntes-bea_talaia.md` (#2) · peça #1: `bitacora/2026-06-10_nav-mobil_mirador.md`

— Mirador
