# F5.4 · Cinc indicadors més pintats a tot Catalunya (9 de 11)

**Data:** 2026-06-25
**Autora:** Talaia (encarna Mirador).
**Latido (Bea):** «que queda per pintar tots els mapes de CAT?» → «ok als 5 fàcils».
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F5.

## Què he fet
Diagnòstic amb dades: dels 11 indicadors del mapa, **5 ja tenien valor calculat a tot CAT al mart**
(916/916) però no eren a l'artefacte compacte → el mapa els pintava només al Berguedà. Deriven de
senyals que ja cobreixen el país (residus, EMEX, RTC), així que **no calia dada nova**, només
exposar-los.

Afegits a `tools/export_indicadors_cat.py` (`NUM_KEYS`): **càrrega total, índex de turisme, IETR,
% habitatge no principal, divergència de senyals**. Regenerat `indicadors-catalunya.json` (209 kB).
El selector, les etiquetes i la classificació del mapa ja existien → cap altre canvi.

## Resultat
El mapa pinta ara **9 de 11** indicadors a tot Catalunya:
gent que el padró no veu · residus · densitat · renda · càrrega · turisme · IETR · %no-principal ·
divergència. Mostra (Girona): càrrega 112.929, turisme 34, IETR 11, %no-principal 23, divergència 65.

## Verificat
- Compacte: 947 munis · càrrega/turisme/IETR/%no-principal 947, divergència 927.
- `npm run build` ✔ · artefacte servit amb els 9 + `conf`.
- ⚠️ Canvas → cop d'ull de Bea (la classificació Jenks s'adapta a cada indicador; càrrega té rang
  ampli com la densitat).

## Què queda per pintar-los TOTS (2)
**tipologia** + **densitat de restauració** — depenen d'OSM (només-Berguedà). És l'única peça que
necessita dada nova: baixar OSM a tot CAT + bbox + geometria 947 + recalibrar la tipologia per tipus.
2a onada pesada.

— Talaia 🌊
