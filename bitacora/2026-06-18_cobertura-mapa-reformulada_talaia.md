# Vista de cobertura del mapa reformulada (post-extensió Nivell C)

**Data:** 2026-06-18
**Autora:** Talaia (encarna Mirador/web)
**Latido (Bea):** «mantenir comarca per defecte, reformular» la vista de cobertura.
**Status:** a la porta del PR (branca `feat/cobertura-mapa-reformulada`). Resol el flag de #152.

## Per què
En estendre el Nivell C a tot Catalunya (#152, 927 munis en rang), la vista de cobertura per
comarca/vegueria del mapa quedà obsoleta: deia «només el Berguedà / Comarques Centrals tenen dades»,
quan ara cobrim ~tot CAT en rang. Contradeia el missatge d'abast de la home.

## Què he fet (ChoroplethMap + /mapa)
- **Capa comarca** (`COV_COM_FILL`): Berguedà = teal **sòlid** (dades completes); la **resta** = mateix
  teal **més clar** (estimació en rang). Cap gris «sense dades» (verificat: cap comarca a 0; la mínima,
  Conca de Barberà, 77%).
- **Capa vegueria** (`COV_VEG_FILL`): totes en rang (teal clar). Tret el **tramat «parcial»**
  (`COV_VEG_HATCH`) — ja no hi ha cap vegueria «parcial».
- **Llegenda** (/mapa) i claus i18n (ca/es): «Dades completes (Berguedà)» + «Estimació en rang (resta
  de Catalunya)» + «Forats puntuals sense dades · detall a municipi». Caveat actualitzat.

## Verificat / declarat
- `svelte-check` 0/0 (les claus i18n noves resolen; `map_legend_coverage_partial` retirada) · `build` OK.
- **No verificat visualment**: la llegenda es renderitza només en client en commutar a comarca/vegueria
  (el default de /mapa és municipi) → no surt a l'HTML prerenderitzada; i el canvas MapLibre no es pot
  verificar headless (lliçó documentada). **Cal el cop d'ull de Bea** al desplegament: home (default
  comarca) i /mapa commutant comarca/vegueria.

— Talaia 🌊
