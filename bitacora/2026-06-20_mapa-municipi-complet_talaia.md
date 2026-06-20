# Mapa · vista municipi completa (pinta per l'indicador a tot Catalunya)

**Data:** 2026-06-20
**Autora:** Talaia (encarna Mirador/Sondeig)
**Latido (Bea):** «ens concentrem en la secció mapa per fer-la completa; comencem per la vista municipi».
**Status:** a la porta del PR (branca `feat/mapa-municipi-complet`).

## Què he fet
Ara, a la vista **municipi** de /mapa, els municipis de fora del Berguedà es pinten pel **MATEIX
indicador** que tries (mateixa classificació i colors que el Berguedà), no sempre pel gap (com feia
#159, que es veia incoherent en triar p. ex. «Densitat de restauració»).

- **Artefacte `indicadors-catalunya.json`** (`tools/export_indicadors_cat.py`): per muni, els
  indicadors que tenim a tot Catalunya amb la MATEIXA clau del selector — **`gap_pernocta_pct`**
  (pernocta) i **`kg_hab_any`** (residus, baixats de l'ARC directament). 948 munis.
- **ChoroplethMap:** prop `catValues`; `joinValues` posa `__covval` (valor de l'indicador actiu del
  muni cobert); la capa COVERED es pinta amb `coveredColorExpr` (mateixa `fillColorExpression` i
  classificació que el Berguedà, sobre `__covval`); si l'indicador és només-Berguedà → `__covval`
  null → opacitat 0 (atenuat honest). El FILL del Berguedà queda **intacte** (risc mínim).
- **/mapa:** la `series` de classificació ara abasta Berguedà ∪ catValues per als indicadors
  cat-escala → escala compartida. Nota de llegenda honesta dels munis estimats.

## Honest sobre l'abast
Dels 9 indicadors, només **2 tenen dada a tot Catalunya** (gap, residus). Els altres 7 (tipologia,
càrrega, pressió turística, restauració, IETR, % no principal, contradiccions) són **només-Berguedà**
→ la resta queda atenuada (no fingim dada). Es poden afegir indicadors NOUS cat-escala (densitat,
renda, gas, turisme RTC/resident) com a següent tram per enriquir el mapa.

## Verificat / declarat
- `svelte-check` 0 · `build` OK · artefacte copiat · nota de llegenda a la /mapa prerenderitzada.
- **No verificat visualment** (canvas WebGL, headless): els colors → **cal el teu cop d'ull** a /mapa
  (tria «Gent que el padró no veu» i «Residus»: tot Catalunya pintat; tria «Densitat de restauració»:
  només Berguedà + resta atenuada).

## Pendents (els altres 2 punts de Bea + notes)
- Vista **comarca** i **vegueria**: info per mouse-over (agregats). Següent tram.
- **Home:** el mapa segueix amb tipologia (Berguedà) → a municipi els coberts queden atenuats. Si vols
  que la home mostri dada cat-escala a municipi, cal canviar-ne l'indicador (p. ex. al gap) — vot teu.
- Afegir indicadors cat-escala nous (densitat/renda/gas/turisme).

— Talaia 🌊
