# Licitacions → pàgina «en construcció» (aparcades per al llançament)

**Data:** 2026-06-18
**Autora:** Talaia (encarna Mirador/web)
**Latido (Bea):** «a tope» · decisió §0.4 del pla: licitacions al PEU, en construcció.
**Status:** a la porta del PR (branca `chore/licitacions-en-construccio`). Tanca P0 #4 de `next.md`.

## Què he fet
Aparcat el cabal de licitacions per al llançament sense deixar cap fil penjat. La maquinària es
CONSERVA per a la Fase 2 (eina, artefacte, contractes, helpers de format — només desconnectats del
consum a la UI).

1. **`/licitacions`** → pàgina honesta **«en construcció»** (no el segell «stub»): explica què vindrà
   i per què encara no hi és (cobrir totes les fases, creuar fonts; cap xifra sense procedència).
   `+page.ts` simplificat (sense càrrega de dades). Claus i18n `lic_wip_*` (ca/es).
2. **Home** — `+page.ts` deixa de carregar l'artefacte; `buildTroballes(dataset)` sense lic → la
   troballa `'lic'` desapareix sola (ja condicionada). Import de `LicitacionsPayload` retirat.
3. **Fitxa** — `municipi/[slug]/+page.ts` deixa de carregar licitacions; `+page.svelte` treu la
   secció + el `lic` derivat + els imports de format (només s'usaven allà).
4. **Nav** — `/licitacions` FORA de la capçalera (escriptori + drawer mòbil); es **manté al peu**
   (secció Explora) cap a la pàgina en construcció. El sitemap segueix llistant `/licitacions/`.

## Verificat
- `svelte-check`: 0 errors / 0 warnings.
- `build`: OK. `/licitacions` mostra «en construcció» i CAP rastre del contingut vell (taxonomia
  1.295, veredicte «29/31», «confessió administrativa» → 0 matches). Fitxa de Berga sense secció de
  licitacions (0 matches). Home: una sola ocurrència de `/licitacions` (el peu), cap a la nav.

## Detall de mètode
Edició del layout: la indentació real era 2 tabs (no 3); el prefix del Read em va fer comptar de
més i van fallar uns quants intents fins que vaig inspeccionar els bytes (`cat -A`). Lliçó: per a
edicions multilínia, verificar la indentació exacta amb `cat -A`, no fiar-se del render del Read.

— Talaia 🌊
