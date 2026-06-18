# Pla de llançament — auditoria inline + pla per fases

**Data:** 2026-06-18
**Autora:** Talaia (coordinadora)
**Latido (Bea):** «Fes planificació. Objectiu sortida online amb un producte bo. Igual millor no fer
càlculs amb les licitacions i deixar-ho com una pàgina en construcció. La publicació ha de ser amb
tota Catalunya i una web sòlida.»
**Status:** pla lliurat (`docs/pla-llancament-2026-06.md`), a la porta del PR. Pendent: vot de Bea al §0.

## Què he fet
1. **Intent amb workflow (7 agents)** — auditoria de llançament + red-team + síntesi. **Va fallar
   tot**: límit de despesa mensual del compte (`monthly spend limit`). No és transitori; reintentar
   el mateix toparia igual.
2. **Auditoria INLINE** (el bucle principal sí respon) sobre el repo real. Troballes ancorades:
   - **Cercador** (`MuniSearch.svelte`) només indexa els 31 del Berguedà → forat P0 per a «tota
     Catalunya».
   - **Prerender** de fitxes: 113 de ~947; la resta cau al fallback SPA (404).
   - **Licitacions**: viu i ben enllaçat (nav `+layout.svelte:93,126,162`, troballa a la home
     `troballes.ts:92` —condicionada, desapareix sola—, secció a la fitxa). Mapada la cirurgia
     d'aparcament.
   - **noindex** a 3 llocs (`app.html:15`, `static/robots.txt`, `static/_headers`), tots amb
     comentari «treure al llançament». **Sense `og:image`**. Analytics sense cookies ✅, hreflang ✅.
   - **Stubs** `/index`,`/day-tripper`,`/politica`: inerts a la nav, rutes reals amb segell «stub».
3. **Pla per fases** amb el principi «solidesa i honestedat > features»; proposo RE-TALLAR la línia
   de llançament (dades obertes/viz noves/espina → post-llançament) per sortir sòlids i aviat.

## Decisions que necessito de Bea (§0 del pla)
Abast del re-tall · fitxes de tota Catalunya (prerender tots vs fallback) · licitacions enllaçada o
no · llengües al dia 1 (ca/es).

## Resolució (Bea, 2026-06-18) — decisions del §0
- **Abast:** tot l'spec al llançament (no es retalla res).
- **Cobertura:** tot Catalunya, TOTS els munis (estendre Nivell C a 43 comarques + baixar el llindar
  dels 1.000 hab). Carril dades, **NO bloquejat pel límit de despesa** (és Python + dades obertes).
- **Fitxes:** prerenderitzar tots els munis.
- **Licitacions:** al PEU com a «en construcció» (fora de la nav principal).
- **Llengües:** ca/es + aranès + anglès al dia 1.

Plegat al pla v2 (`docs/pla-llancament-2026-06.md`) i convertit en cua operativa (`bitacora/next.md`,
P0 primer). **Correcció a un risc abans escrit:** estendre Nivell C NO depèn de l'IA (numpy + Socrata/
INE); el límit de despesa només frena lectures, pregunta-li super beta i traducció oc/en.

— Talaia 🌊
