# Beeswarm del gap padró↔presència (1a visualització nova §4)

**Data:** 2026-06-18
**Autora:** Talaia (encarna Mirador/Llegenda)
**Latido (Bea):** «vamos con P1 visualitzacions» → tria: beeswarm del gap (tot CAT).
**Status:** a la porta del PR (branca `feat/beeswarm-gap`). Avança P1 #7 (viz §4).

## Què he fet
`Beeswarm.svelte`: un punt per municipi (~927), col·locat segons el **gap** = com s'aparta la
presència estimada (qui hi dorm) del padró (qui hi consta). La tesi del projecte com a paisatge
d'un cop d'ull, amb les dades de Nivell C. A la home, secció nova «El gap, d'un cop d'ull».

- **SVG prerenderitzat** (layout calculat al servidor, determinista): 927 punts a l'HTML, funciona
  sense JS, verificable. Cada punt enllaça a la fitxa; `title` natiu per al hover.
- **Color** = paleta divergent del gap (`--dp-div2-*`, com el mapa): teal = menys que el padró;
  porpra = més (població que el padró no veu). Línia de 0 = el padró.
- **Layout** beeswarm per bins (amplada = punt) amb apilat alternat amunt/avall; domini [−70,+160]%
  (p99≈128; extrems retallats a la vora).

## Troballa que mostra
Els extrems del gap NO són la costa sinó **micropobles de muntanya** (Bolvir +299%, Naut Aran +257%,
Cerdanya/Aran): segona residència que el padró no veu. La costa té gap positiu però menor (padró
gran). Honest: els extrems són munis <1.000 hab amb banda ampla (el caption ho diu).

## Verificat (HTML prerenderitzada)
- `svelte-check` 0/0 · `build` OK.
- 927 punts a `build/ca/index.html`. Spot-check: Bolvir +299% → vora dreta (cx=740), porpra (div2-6);
  Alins −69% → vora esquerra (cx≈22), teal (div2-0); títols i enllaços correctes.

## Pendent de §4
Dorling-fantasma · slider de denominador · «el riu» · emblema doble corrent · glif balança.

— Talaia 🌊
