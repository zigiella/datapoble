# F4.1 · Fitxa uniforme a tota Catalunya (espina per a tots)

**Data:** 2026-06-23
**Autora:** Talaia (encarna Mirador).
**Latido (Bea):** «estem fresques, acabem de resetejar. és el millor moment!».
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F4.

## El problema que resol
La fitxa tenia **3 nivells** (Berguedà ric / coberts targeta de rang / resta «sense dades») — l'arrel
del «les fitxes són diferents» que va veure Bea. Ara **cada muni té la seva espina**.

## Què he fet (canvi mínim, el svelte ja era null-safe)
- **`copy-data.mjs`**: parteix `municipis.catalunya.json` (947) en **un fitxer per muni**
  (`static/data/muni/<ine5>.json`, només la fila). Per què: la fitxa es prerenderitza per muni
  (947×2); amb el dataset sencer (1,8 MB) cada pàgina l'incrustaria → així només incrusta el SEU
  (~2 kB). Build-only (`static/` és gitignored).
- **Fitxa `+page.ts`**: `row` ara és per a **TOTS** els munis — el Berguedà del dataset ja carregat
  (camí ràpid, amb extres); la resta del fitxer per muni (espina + extres en NULL/`pendent`). La
  lectura-IA (artefacte Berguedà) es gateja a `isBergueda` (evita 916 fetches inútils).
- El svelte de la fitxa **no ha calgut tocar-lo**: ja renderitza `row?.values` null-safe («sense dada»
  on és null), deriva la banda de presència, i `tipologia='pendent'` → `tipologiaMeta` undefined → el
  xip de tipologia s'amaga sol. Honestedat ja integrada.

## Verificat (HTML prerenderitzat — la fitxa és SSR; el canvas no)
- **Girona** (no-Berguedà): IETR, Residus, Confiança presents; extres `pendent`; **cap «sense dades»**.
- **Berga** (Berguedà): fitxa completa intacta (Tipologia=capital_serveis, Confiança…).
- **la Vajol** (dels 20 sense covariables): renderitza l'espina que té (Residus, IETR), presència n.d.,
  sense trencar-se.
- `npm run check` 0 · `npm run build` ✔ · 947 fitxes partides.
- ⚠️ El **llustre visual** (que les fitxes no-Berguedà no quedin amb massa seccions buides) → **cop
  d'ull de Bea**: potser cal col·lapsar/anotar les seccions d'extres (política/origen) fora del Berguedà.

## Següent (F4.2 · mapa)
Estendre l'artefacte compacte del mapa amb l'espina del tooltip + **trames a tot CAT** (segons
confiança) + un sol tooltip. El mapa és canvas (WebGL) → no verificable headless → cop d'ull de Bea.

— Talaia 🌊
