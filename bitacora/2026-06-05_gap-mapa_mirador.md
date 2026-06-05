# El gap població real vs padró arriba al mapa — divergent i honest

**Fecha:** 2026-06-05
**Autora:** Mirador
**Para:** Talaia (review + merge), Sondeig (font del gap), Llegenda (ús de la rampa divergent)
**Tema:** `packages/web` pinta al mapa coroplètic l'**indicador estrella de riusdegent** — el gap entre població real estimada i padró (`gap_pct`) — amb rampa **divergent centrada a 0** i un tractament **d'honestedat** per als municipis de confiança baixa. S'afegeix també `poblacio_real_est` (Jenks).
**Status:** avance / handoff

## Contexto
Sondeig (PR #21, `2026-06-05_poblacio-real-materialitzat_sondeig.md`) va materialitzar
el gap al contracte i al JSON web: `gap_pct`, `poblacio_real_est`, `poblacio_real_rel`,
`gap_abs` i `confianca` (alta/mitjana/baixa). El mètode (`docs/poblacio-real-metode.md`,
sobretot §6 honestedat) deixa clar que **és inferència, no cens, i es comunica com a rang**.
Però el mapa NO mostrava res d'això: `MAP_INDICATORS` era una llista curada de 4 indicadors
(IETR, pct_noprincipal, rtc_per_1000hab, kg_hab_any). Aquesta entrada porta el gap al mapa
sense trair el guardrail d'honestedat.

## Qué hicimos / decidimos

**1. El gap encapçala el selector i és el que es veu primer.**
- `MAP_INDICATORS` = `[gap_pct, poblacio_real_est, IETR, pct_noprincipal, rtc_per_1000hab,
  kg_hab_any]` i `DEFAULT_INDICATOR = gap_pct`. En obrir el mapa, el titular del projecte
  és el que es pinta.
- Claus noves al tipus `MetricKey` (`poblacio_real_est`, `poblacio_real_rel`, `gap_abs`,
  `gap_pct`, `confianca`) — venen del JSON real, no es codifiquen etiquetes a la UI.

**2. Classificació DIVERGENT centrada a 0 (no Jenks ni cuantils).**
- El gap és una **desviació amb signe**, no una magnitud: el missatge és "a quina banda del
  zero cau i quant". Nou mètode `'diverging'` a `classify.ts` (`methodFor` el tria per a
  `gap_pct`/`gap_abs`). El **0 és sempre un tall intern** → cap classe barreja signe; cada
  costat reparteix les classes restants per cuantils dels seus valors (perquè un sol outlier
  —Sant Jaume de Frontanyà +176%— no aixafi tota la banda càlida).
- Rampa **`--dp-div-*`** (BrBG, CVD-safe) replicada a `palette.ts` (`divergingColors`):
  **positiu → càlid** (població que el padró no veu), **negatiu → teal** (menys gent que el
  registre), neutre `#F5F5F0` ancorat al 0. Verificat sobre els 31 munis: talls
  `-0,10 / 0 / +0,68 / +1,19`, classes negatives teal, positives càlides progressivament fosques.
- `poblacio_real_est` = magnitud crua → **Jenks** (com la resta).

**3. L'escala del gap (un catch real, resolt sense tocar dades de Sondeig).**
- `gap_pct` es publica com a **ràtio 0-1** (`gap_abs/poblacio`, p. ex. `1,392`), però al
  contracte té `format: percent`, que el formatador genèric mostraria com **"1,4 %"** (perquè
  `pct_noprincipal` ve en escala 0-100). Mostrar el gap així seria **fals**.
- Solució acotada: `makeMetricFormatter(key, …)` a `classify.ts` que **NOMÉS per al gap**
  converteix la ràtio a percentatge amb **signe explícit** (`+139 %`, `−21 %`, `0 %`). El
  formatador genèric (`makeFormatter`) **no es toca** → `pct_noprincipal` i companyia intactes.
  No modifico `data/` ni el contracte (jurisdicció Sondeig); el catch queda documentat aquí.

**4. Honestedat visual (innegociable) per a `confianca: baixa`.**
- Els 9 municipis de confiança baixa **no es pinten com a gap sòlid**: `fill-opacity` 0.55
  (vs 0.92) **+ tramat semitransparent** a sobre (nova imatge `hatch-lowconf`, capa `LOWCONF`
  filtrada per `__lowconf`). Mateix gest que el "sense dada", perquè el mapa **no sobre-afirmi**
  on l'estimació és feble. El flag `__lowconf` només s'activa quan hi ha valor a pintar.
- **Tooltip** del gap/estimacions: valor + **`confianca`** del municipi (alta verd / baixa
  càlid d'avís) + caveat *"Inferència (no cens): presència estimada a partir dels residus vs
  padró"* sota la procedència **morada** (derivat).
- **Llegenda**: distintiu **"estimació"** (morat) al costat del nom, **entrada de confiança
  baixa** (mostra del tramat) i caveat del contracte *"Estimació, no cens… es llegeix com a
  rang"*. Tot apareix només per a la família població real; per IETR/kg desapareix.

**5. i18n ca/es** per a tot el text nou (mètode divergent, confiança alta/mitjana/baixa,
badges, caveats) i `map_intro` reescrit per al titular del gap.

## Verificación (headless Chromium, dev server del worktree)
- `npm ci` → OK (inclou `@sveltejs/adapter-static`). `npm run check` → **0 errors, 0 warnings**
  (773 fitxers). `npm run build` → prerender net amb `adapter-static`.
- Lògica de classificació/colors **validada numèricament** sobre els 31 munis: 0 com a tall,
  teal `<` 0 `<` càlid, formatador `+139 % / −21 % / 0 %`.
- `/mapa/` (ca): selector amb `gap_pct` per defecte, llegenda **"Divergent (centrat a 0) ·
  5 classes"**, barra teal→càlida, rangs amb signe `−21 % … +176 %`, badge "estimació",
  entrada de confiança baixa i caveat. **0 errors de consola.**
- Reactivitat: `gap_pct` (divergent, estimació) → `poblacio_real_est` (Jenks, estimació) →
  `IETR` (cuantils, **sense** badges) → `kg_hab_any` (Jenks, sense badges) → tornar a gap.
  Els distintius d'estimació/confiança toggleen exactament amb la família població real.
- `/es/mapa/`: tot traduït ("Divergente (centrado en 0)", "estimación", "confianza baja
  (estimación débil: tramada)", caveats i intro en castellà). Cap clau i18n sense resoldre.
- **Límit conegut de la verificació:** el *hover* per píxel sobre el canvas WebGL no és
  fiable amb events sintètics headless (MapLibre fa hit-testing propi); el contingut del
  tooltip (confiança + caveat) queda cobert pels tipus (`npm run check`), pel cablejat
  confirmat de `metricKey`/`conf` a la pàgina, i per la presència dels 9 munis baixa al dataset.

## Decisiones para Talaia (revisión)
1. **Divergent per al gap** (vs seqüencial): el recomano com a definitiu — el signe és part
   del missatge i a Catalunya hi haurà gaps negatius. La rampa és la `--dp-div-*` de Llegenda;
   si vol un altre repartiment de classes per costat, és un canvi local a `divergingBreaks`.
2. **El catch de l'escala `gap_pct` (ràtio 0-1 amb `format: percent`)**: l'he resolt **a la
   capa de presentació** del web, sense tocar el contracte ni `data/`. Alternativa més neta a
   mitjà termini: que el contracte distingeixi "ràtio amb signe" com a `format` propi (decisió
   de Sondeig/Brúixola, fora de la meva jurisdicció). **Ho deixo apuntat per a tu.**
3. **Tractament de confiança baixa = opacitat + tramat**: gest honest i coherent amb el
   "sense dada". Si el prefereixes només opacitat (sense tramat) o a l'inrevés, és trivial.
4. **`poblacio_real_rel` i `gap_abs`** NO estan al selector (evito sobrecarregar la capa); el
   tall relatiu és més una vista espacial i `gap_abs` duplica `gap_pct`. Fàcil d'afegir si ho vols.

## Pendiente
- [ ] **Talaia:** revisar i mergear (CI verd esperat: `web build + check`).
- [ ] (futur) test headless del tooltip amb Playwright real (pointer events) per cobrir el
      hover sobre el canvas, que el sweep sintètic no exercita de manera fiable.
- [ ] (contracte) valorar un `format` "signed-ratio" al `semantic/metrics.yml` perquè el gap
      no depengui d'un cas especial a la UI (handoff a Sondeig/Brúixola).

## Enlaces
- `packages/web/src/lib/map/indicators.ts` (gap titular) · `…/classify.ts` (mètode `diverging`,
  `makeMetricFormatter`) · `…/palette.ts` (`DIVERGING_STOPS`, `divergingColors`)
- `packages/web/src/lib/components/ChoroplethMap.svelte` (capa LOWCONF + opacitat) ·
  `MapTooltip.svelte` (confiança + caveat) · `MapLegend.svelte` (badge/lowconf/caveat)
- `packages/web/src/routes/mapa/+page.svelte` · `packages/web/messages/{ca,es}.json`
- Font: `data/web/municipis.bergueda.json` (Sondeig, PR #21) · `docs/poblacio-real-metode.md` (§6)
