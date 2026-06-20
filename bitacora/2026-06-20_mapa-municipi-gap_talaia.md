# Mapa · vista municipi pintada pel gap (dades a tot Catalunya)

**Data:** 2026-06-20
**Autora:** Talaia (encarna Mirador)
**Latido (Bea):** «visualització de les dades als dos mapes — a la vista municipi, veure les dades i
pintar amb el color que toqui» (1r dels 3 punts).
**Status:** a la porta del PR (branca `feat/mapa-municipi-gap`). Stage A de 3 (municipi).

## Què he fet
A granularitat **municipi**, els municipis coberts pel Nivell C (927) ara es pinten pel seu **gap
padró↔presència** (paleta divergent: teal = menys gent que el padró · porpra = més, població que el
padró no veu), no amb el teal pla d'abans. És la dada que tenim a tot Catalunya feta visible al mapa.

- `joinValues` calcula `__gap` (de pernocta: estimació/padró) per als coberts, als DOS camins.
- Capa COVERED: `fill-color` = `step` divergent sobre `__gap` (case → teal pla si no hi ha padró).
- Llegenda /mapa: barra divergent «Municipis estimats (Nivell C): ← menys / més presència que el padró →».

## Bug latent arreglat (de #143)
El camí **numèric** de `joinValues` (el que fa servir /mapa amb indicadors) **no tenia `__covered`**
(només el categòric/home el tenia) → a /mapa la vista municipi NO pintava els coberts. Ara sí. Per
això la vista municipi de /mapa es veia buida fora del Berguedà; resolt.

## Verificat / declarat
- `svelte-check` 0 · `build` OK · la llegenda del gap surt a la /mapa prerenderitzada.
- **No verificat visualment** (canvas WebGL, headless no pot): els colors al mapa. **Cal el teu cop
  d'ull**: /mapa i home a granularitat municipi → els munis de fora del Berguedà pintats del teal al
  porpra segons el gap.

## Pendent (els altres 2 punts de Bea)
- **Vista comarca:** info per mouse-over (tooltip amb agregats de la comarca).
- **Vista vegueria:** info per mouse-over.

— Talaia 🌊
