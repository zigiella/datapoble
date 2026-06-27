# F5.5c · Tipologia + restauració al mapa a tot CAT — els 11/11 pintats

**Data:** 2026-06-27
**Autora:** Talaia (encarna Mirador).
**Latido (Bea):** «arranquem» (OSM) → últim pas: pintar-ho al mapa.
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F5.

## Què he fet
Els 2 indicadors que faltaven al mapa a escala CAT — **restauració** (numèric) i **tipologia**
(categòric) — ja es pinten per als municipis coberts. Amb això, **els 11 indicadors del mapa es
pinten a tot Catalunya**.

- **Artefacte compacte** (`export_indicadors_cat`): + `restauracio_per_1000hab` (numèric) i + `tip`
  (l'arquetip de tipologia, string; com `conf`). 947 munis · 257 kB.
- **Mapa (ChoroplethMap):**
  - `tipologiaMatchExpression(valExpr)` ara accepta on llegir l'arquetip → `__cat` (Berguedà) o
    `__covcat` (coberts).
  - `coveredColorExpr`: cas **categòric** (tipologia) → match sobre `__covcat`.
  - `joinValues`: `__covcat` per als coberts (de `catValues.tip`); el `covval` numèric passa per
    `mapValue` → el 0 d'OSM de la restauració es mostra «sense dada» també als coberts.
  - Capa COVERED: opacitat visible si hi ha covval **o** covcat. `buildHover`: el cobert categòric
    mostra l'arquetip; el numèric, amb `mapValue`.

## Verificat
- Compacte servit amb els 11 indicadors + `conf` + `tip` (Girona: restauració 5,46, tip
  segona_residència). 927 amb tip, 947 amb restauració.
- `svelte-check` 0/0 · `npm build` ✔.
- ⚠️ **Mapa = canvas WebGL → cop d'ull de Bea**: triar «tipologia» → tot CAT acolorit per arquetip
  (Berguedà i resta igual); «densitat de restauració» → coberts pintats, els 140 sense locals OSM
  tramats «sense dada». La trama de confiança baixa segueix a tot CAT.

## Estat
**Resposta a «què queda per pintar tots els mapes»: RES.** Els 11 indicadors del mapa es pinten a tot
Catalunya. Tota la fase «fer-ho bé» (F1–F5) és completa: dada, model, export, fitxa i mapa, uniformes
i honestos a tot el país.

— Talaia 🌊
