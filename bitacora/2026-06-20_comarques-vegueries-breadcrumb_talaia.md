# Pàgines de comarca + vegueria + breadcrumb territorial navegable (§5)

**Data:** 2026-06-20
**Autora:** Talaia (encarna Mirador)
**Latido (Bea):** «breadcrumb territorial sempre present» → tria: «pàgines de comarca + breadcrumb complet».
**Status:** a la porta del PR (branca `feat/comarques-vegueries`). Tanca P1 #11 + avança §5.

## Què he fet
El breadcrumb navegable que demanaves necessitava DESTINS per a comarca i vegueria (no existien) →
els he construït. Ara es puja/baixa de nivell sense perdre's: Catalunya ⇄ vegueria ⇄ comarca ⇄ municipi.

- **Artefacte `comarques.json`** (copy-data, des de `municipis-territori.json`): 43 comarques (amb
  vegueria + ine5s) i 8 vegueries (amb comarques). Sense crides; estructura administrativa.
- **`/comarca/[slug]`** (43, prerender + guarda de col·lisió): breadcrumb + beeswarm del gap de la
  comarca (reusa `Beeswarm`) + llista de municipis amb el seu gap (enllaç a fitxa).
- **`/vegueria/[slug]`** (8): breadcrumb + llista de comarques (enllaç a cada pàgina de comarca).
- **`Espina` refactoritzada** a un `trail` de molles (`{label, href?}`) reutilitzable: la darrera és
  l'actual (sense enllaç). La fitxa, la comarca i la vegueria la construeixen al seu nivell. Ara els
  nivells són **enllaços** (Catalunya→home, vegueria→/vegueria, comarca→/comarca), no text.
- Sitemap ampliat amb les 43+8 pàgines.

## Verificat (HTML prerenderitzada)
- `svelte-check` 0 · `build` OK · 43 comarques + 8 vegueries prerenderitzades.
- Salou → breadcrumb amunt a `/comarca/tarragones` i `/vegueria/camp-de-tarragona`. Comarca Berguedà
  → amunt a vegueria (comarques-centrals) + Catalunya; avall, munis. Vegueria → avall, comarques.

## Pendents/notes (iniciativa fractal)
- **Redundància menor:** el Berguedà té `/resum` (subhome rica) I `/comarca/bergueda` (genèrica). El
  breadcrumb apunta a la genèrica. Opcions futures: redirigir `/comarca/bergueda`→`/resum`, o fer
  `/resum` la plantilla de totes les comarques.
- **Descobribilitat:** les pàgines de comarca/vegueria només s'arriben pel breadcrumb i el drill-down;
  es podria afegir un índex (a la home «portes» o un /catalunya).
- L'`Espina` ara és «sempre present» a les pàgines territorials; estendre-la a més vistes si cal.

— Talaia 🌊
