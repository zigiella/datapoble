# F1.1 · Registre de municipis de tot Catalunya (fonament de l'extensió)

**Data:** 2026-06-21
**Autora:** Talaia (encarna Sondeig)
**Latido (Bea):** «ara podríem començar F1».
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F1 (des-acotar la ingesta).

## Què he fet (la part segura i verificable)
El primer fonament que tot connector necessita: el **registre dels 947 municipis** que substitueix la
llista hardcoded dels 31 del Berguedà. El que mancava per a tot CAT era el **`codi6`** (codi Idescat
de 6 dígits) que demanen els connectors per-muni (EMEX, origen: endpoint `?id={codi6}`).

- `tools/deriva_municipis_catalunya.py` → `data/territorial/municipis-catalunya.csv` (codi6;ine5;nom).
  - `ine5`+`nom` canònics de la **geometria ICGC** (947); `codi6` de l'**ARC residus** (cobreix els
    947, 0 forats), creuat per `ine5` i imposant el cens de la geometria (descarta junk/obsolets).
  - Verificació interna (no escriu si falla): 947 files, totes amb codi6, i els **31 codi6 del
    Berguedà quadren EXACTAMENT** (Gósol 251001 inclòs).
- `packages/ingestion/.../municipis.py`: afegit `CATALUNYA` (+`CATALUNYA_INE5`), carregat del registre;
  `BERGUEDA` es manté com a pilot. Càrrega tova (si el fitxer no hi és, queda buit → no trenca el
  pilot ni el CI). Assert: el Berguedà és subconjunt exacte del registre CAT.

## Verificat
- `deriva_municipis_catalunya.py`: 947 munis, Berguedà 31/31 ✓.
- Import del mòdul: CATALUNYA 947, BERGUEDA 31, assert del subconjunt passa.
- `data/raw/` és gitignored (regenerable); els **marts SÍ es versionen** (passaran de 31 a 947 quan
  es re-materialitzin a F2).

## Honest sobre l'abast
Això és el **fonament**, no la baixada. L'entorn d'aquest equip **no té dlt/dbt instal·lats** → córrer
el pipeline complet (ingesta + marts) és una **operació deliberada a part**. Els connectors encara
defaulten al Berguedà; des-acotar-los i córrer-los és F1.2.

## Següent (F1.2, quan diguis)
Des-acotar els connectors: **bulk** (RTC/residus/ICAEN/electoral → sense filtre de comarca, ràpid) i
**per-muni** (EMEX/origen → `CATALUNYA`, ~1.900 crides cortesos, cachejar) i **OSM** (bbox CAT +
geometria 947). Instal·lar l'entorn i córrer; **avisaré abans de les baixades pesades**. Després, F2:
unificar el model (base Nivell C + z-scores per tipus) i re-materialitzar els marts a 947.

— Talaia 🌊
