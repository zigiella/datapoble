# Llista costanera OFICIAL (substitueix la provisional al Nivell C)

**Data:** 2026-06-18
**Autora:** Talaia (encarna Sondeig/dades) · noms aportats per Bea
**Latido (Bea):** «Tinc els noms» (Territori 2023 → 70 costaners, validat amb el PPOL).
**Status:** a la porta del PR (branca `data/llista-costanera-oficial`). Tanca el pendent (a) de #152.

## Què he fet
Substituïda la classificació costanera PROVISIONAL (geomètrica) per la **llista OFICIAL** que ha
configurat la Bea: **70 municipis costaners** derivats de la llista de municipis litorals de Territori
(Generalitat, 27.06.2023) quadrada amb el perímetre del **PPOL** (91 = 70 costaners + 21 zona
d'influència DPMT, Llei 8/2020).

- La llista de Territori en té **76**; se'n treuen **5 sense costa** (afectats per la Llei de costes:
  Tortosa, Torroella de Fluvià, Vilamacolum, Riumors, l'Armentera) + **l'Aldea** (terme no limita amb
  mar) per quadrar amb els 70 del PPOL. Sant Pere de Ribes i Mont-ras es conserven (tenen franja).
- `data/territorial/municipi_litoral.csv` (70 costaner + 6 exclosos, traçable). **Match per `ine5`**
  → robust als canvis de topònim (Castell-Platja d'Aro→«Castell d'Aro…», Sant Carles de la Ràpita→
  «la Ràpita», que Bea va avisar).
- `nivellc_analisi.py`: `load_costaners()` ara llegeix la llista oficial; re-corregut el pipeline.

## Cross-check (la geomètrica #149 vs l'oficial)
**0 falsos negatius** (la derivació geomètrica va caçar els 70) i **13 falsos positius** (la segona
fila: Alella, Argentona, Sant Boi, els «de Dalt», Vinyols, la Canonja, Camarles…) → la geomètrica va
ser un bon control; l'oficial els treu net. Els 70 `ine5` casen tots amb el catàleg (els 439xx
recents inclosos).

## Resultat
litoral_metro 7 + litoral_vacacional 63 = **70**. Els 13 FPs passen a interior_rural. Model global
igual (R²=0,41, cobertura 70%); litoral_vacacional ara **49%**, banda [−20,+29] (costa pura, sense
dilució d'interior → més honest). 927 munis publicats. Metodologia i export actualitzats (ja no
«provisional»; citen Territori/PPOL/Llei 8/2020).

## Verificat
Pipeline net · `svelte-check` 0 · `build` OK · sanity: Alella/Argentona → interior_rural; Salou/
Cadaqués → litoral; nota de l'artefacte = «llista OFICIAL de 70…».

## Pendent
`zona_influencia` (21 munis del PPOL) com a metadada quan en tinguem els noms (NO entra al tipus
litoral) · dada de pic per al litoral (xifra absoluta) · residus L2.

— Talaia 🌊
