# El mapa mostra els munis coberts EN RANG (Nivell C)

**Data:** 2026-06-18
**Autora:** Talaia (encarna Mirador/web)
**Latido (Bea):** «tira per la UI» → «ataca» (el mapa, després de la fitxa #142 i /metodologia).
**Status:** a la porta del PR (branca `feat/mapa-rang-coberts`).

## Què he fet
Tercer i últim tram de la UI de la **presència estimada EN RANG**: després de la fitxa (#142) i
/metodologia, ara el **mapa** deixa de tractar els munis coberts (fora del Berguedà) com a «sense
dades» i els mostra amb la seva banda. Toca els DOS mapes (home i /mapa), a granularitat municipi.

1. **`ChoroplethMap.svelte`** — nova capa `COVERED`: municipis de FORA del Berguedà amb presència
   estimada (artefacte `pernocta-catalunya.json`), pintats en el color de cobertura a MITJA opacitat
   (0,5) — visibles i clicables, però honestament per sota del Berguedà (estimació en rang, no cens).
   - `coveredSet` = claus de `pernocta` que NO són del Berguedà (els del Berguedà ja tenen dades
     completes i van al coroplètic; el model també els estima però la UI prioritza la dada real).
   - `joinValues` marca `__covered`; la capa només es mostra a granularitat municipi (`MUN_LAYERS`).
   - `buildHover` adjunta la fila de rang (`pernocta`) als munis coberts.
2. **`/mapa`** — tooltip de rang propi (`tip--range`): banda `rang_baix–rang_alt`, ETCA oficial com a
   validació si n'hi ha, caveat d'inferència i CTA «obre la fitxa». El clic hi navega.
3. **Home** — passa la prop `pernocta` (la capa pinta a municipi) i el clic navega als coberts. La
   home no té tooltips (cop d'ull); la banda es llegeix a la fitxa.
4. **Càrrega** — `/mapa/+page.ts` i `/+page.ts` llegeixen `pernocta-catalunya.json` (no-fatal:
   sense l'artefacte el mapa funciona igual). Claus i18n noves (`map_range_*`) a ca/es.

## Frontera honesta
- Els munis coberts es pinten en **un sol to** (cobertura), MAI per l'indicador del Berguedà: no
  barregem una estimació en rang amb les mètriques fines del Berguedà.
- La banda és INFERÈNCIA: el tooltip i la fitxa ho diuen; l'ETCA oficial hi surt com a validació,
  no com a substitut. Cap xifra tancada fora del Berguedà.

## Verificat
- `svelte-check`: 0 errors / 0 warnings (1272 fitxers).
- `build` (adapter-static): OK. Prerender de **113 fitxes** de municipi = 31 Berguedà (dades
  completes) + 82 coberts nous (rang). Comprovat per HTML prerenderitzada: Altafulla i el Catllar
  porten la banda i l'ETCA dins l'`index.html`.
- 9 munis surten a `pernocta-catalunya.json` I al Berguedà (l'anàlisi Nivell C inclou el Berguedà):
  no és col·lisió — el `coveredSet` i la fitxa els resolen cap a la dada real del Berguedà (per això
  91 coberts → 82 fitxes noves).

## No verificat (declarat)
- L'aspecte VISUAL de la capa `COVERED` i del tooltip de rang sobre el canvas: el preview headless
  s'ennuega amb MapLibre/WebGL (lliçó documentada). Cal el cop d'ull de la Bea al desplegament:
  commutar a granularitat «municipi» i passar/clicar un muni cobert (p. ex. Altafulla, Tarragonès).

— Talaia 🌊
