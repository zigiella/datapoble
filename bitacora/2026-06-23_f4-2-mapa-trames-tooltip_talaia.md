# F4.2 · Mapa harmonitzat a tot Catalunya (trames + un sol tooltip)

**Data:** 2026-06-23
**Autora:** Talaia (encarna Mirador).
**Latido (Bea):** «F4.2 avanti!».
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F4.

## El que resol
El segon que va veure Bea: «es pinta diferent al Berguedà… al Berguedà fem servir trames també», i les
fitxes/tooltips diferents. Ara el **tractament de confiança i el tooltip són uniformes a tot CAT**.

## Què he fet
- **Dades (artefacte compacte):** `export_indicadors_cat.py` ara DERIVA de `municipis.catalunya.json`
  (DRY, mateixa font que la fitxa) i hi afegeix **`conf`** (confiança baixa/mitjana/alta) per muni.
  `indicadors-catalunya.json`: 947 munis, 64 kB (gap 927, residus 947, conf 947 — 217 de confiança
  baixa). Contracte `IndicadorsCatData` ampliat amb `conf`.
- **Trames a tot CAT (ChoroplethMap):** la confiança dels coberts ve de `catValues.conf`; els coberts
  amb valor i confiança **baixa** reben `__lowconf` → la capa LOWCONF (hatch-lowconf) deixa de ser
  només-Berguedà (filtre sense `__inberg`) i la capa COVERED els baixa l'opacitat (0,78→0,55). Mateix
  gest d'honestedat que al Berguedà, ara a tot el país.
- **Un sol tooltip:** els coberts passen a usar **MapTooltip** (indicador actiu + confiança, igual que
  el Berguedà); MapTooltip guanya un bloc opcional de **presència en rang** (banda + ETCA) per als
  coberts. S'elimina la targeta de rang separada (i els seus estils morts). `buildHover` dona
  valor+confiança als coberts des de catValues.

## Verificat
- `svelte-check` 0/0 · `npm run build` ✔ · artefacte amb `conf` copiat a static.
- ⚠️ **Colors/trames/tooltip del mapa = canvas WebGL → NO verificable headless** (lliçó coneguda). Cal
  el **cop d'ull visual de Bea** a /mapa: triar «Gent que el padró no veu» o «Residus» i comprovar que
  els munis de confiança baixa surten tramats a tot CAT, i que el tooltip d'un cobert mostra indicador
  + confiança + rang (com el del Berguedà). La home (indicador tipologia) no canvia.

## Estat de l'arc «fer-ho bé»
F1 (dades) · F2 (model unificat, guardó ETCA) · F3 (export espina) · **F4 (fitxa uniforme + mapa
harmonitzat)** — TOT a `main`. La promesa «volem fer-ho bé» és real de la dada al mapa. Queda la 2a
onada (F5: OSM + subtipus de tipologia a tot CAT) com a millora futura, no bloquejant.

— Talaia 🌊
