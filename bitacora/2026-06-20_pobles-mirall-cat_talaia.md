# Pobles mirall de tota Catalunya — constel·lació egocèntrica (backlog #6d)

**Data:** 2026-06-20
**Autora:** Talaia (encarna Sondeig + Mirador)
**Latido (Bea):** «Endavant amb la teva proposta!» (el mirall «wow» cat-escala, millora sobre el
concepte d'espejo de la consultora — distinció feta explícita abans).
**Status:** a la porta del PR (branca `feat/pobles-mirall-cat`). Avança P1 #7 (viz §4, forma (d)).

## Què he fet
El **bessó funcional de cada poble, a qualsevol punt de Catalunya** — desbloquejat pel Nivell C #152
(ja tenim vectors cat-escala). Substitueix el mirall-de-xips que abans només funcionava dins el
Berguedà (`mirall.ts`, 31 munis) per una **constel·lació egocèntrica** per a TOTS els ~927 munis.

- `tools/deriva_miralls.py` → `data/web/municipis-mirall.json` (compacte, 112 kB): vector de
  comportament cat-escala (log densitat, renda, gas, gap padró↔presència, turisme/resident),
  z-normalitzat, euclidià, top-6 bessons + el **senyal que els agermana** (co-extremitat). Format
  `{ine5: [[twinIne5, dist, codi]]}`; nom/slug/etiqueta es resolen al web (catàleg + i18n).
- `MirallConstel.svelte`: SVG **prerenderitzat** (layout determinista) — el muni al centre, els
  bessons en òrbita (radi ∝ dissimilitud), etiqueta = quin senyal els uneix; clic → fitxa. Caveat:
  «mapa mental, no mesura».
- Loader de la fitxa resol els bessons des del catàleg; secció nova «El bessó del teu poble» per a
  qualsevol muni (fora del bloc `{#if row}`). Tret el mirall-de-xips antic + CSS/imports orfes.

## Sanity (bessons sensats i on-thesis)
- Salou → Creixell, Torroella de Montgrí, Roda de Berà, l'Ametlla de Mar (**turisme**).
- Bolvir → Prats i Sansor, Fontanals de Cerdanya, Guils… (**presència vs padró** — segona residència de muntanya!).
- Barcelona → el Masnou, Vilassar de Mar, Castelldefels (**densitat**).
- Berga → Gironella, Lleida, Besalú, Breda (**calefacció de gas**).

## Verificat
`svelte-check` 0 · `build` OK · Salou amb 6 bessons + senyal «turisme» a l'HTML; Agullana (sub-1000)
també té constel·lació → funciona per a tots els munis, no només Berguedà.

## Pendent (forma (b) del backlog #6 + doble escala #5)
- **Embedding 2D de secció** (PCA/MDS dels 927) — el «mapa mental» de Catalunya · el meu favorit per a secció.
- Doble escala (#5): afegir els bessons DE LA COMARCA (reusant `mirall.ts`, ara sense ús) al costat
  dels de tota Catalunya.

— Talaia 🌊
