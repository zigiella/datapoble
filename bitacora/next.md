# Cua — camí al llançament

*Derivada de `docs/pla-llancament-2026-06.md` (v2, decisions de Bea 2026-06-18). Es treballa de dalt
a baix; cada tasca = un PR. `P0` bloqueja el llançament. El carril de dades i la web NO depenen del
límit de despesa; les tasques marcades **(IA)** sí (esperen que es reposi).*

## P0 — bloquegen el llançament

1. ~~**[dades] Estendre Nivell C a tot Catalunya**~~ ✅ FET (#152, 2026-06-18) — **91→927 munis en
   rang** (486 ETCA validats + 441 sub-1000 sense validació). R²=0,41, cobertura 70%, held-out
   robust. Densitat=pop/àrea (r=0,9999 vs EMEX, sense ~900 crides). Costaners PROVISIONALS.
   **Pendent:** (a) llista costanera oficial (Bea) · (b) **vista de cobertura comarca/vegueria del
   mapa OBSOLETA** → actualitzar (deia «només Berguedà») · (c) pic litoral · (d) residus L2.
2. ~~**[web] Cercador a tota Catalunya**~~ ✅ FET (#146, 2026-06-18) — catàleg de 947 munis;
   `MuniSearch` hi cerca; `toSlug` arregla l'article inline `l'`.
3. ~~**[web] Prerenderitzar tots els munis**~~ ✅ FET (#146) — `entries()` a 947 (×2 locales),
   `load()` resol qualsevol slug → ine5+nom; «sense dades encara» amb nom real. Build 1m46s.
4. ~~**[web] Licitacions → «en construcció» al peu**~~ ✅ FET (#147, 2026-06-18) — pàgina digna
   `lic_wip_*`; fora de la nav, manté al peu; home i fitxa netes; maquinària conservada.
5. ~~**[web/disseny] Missatge d'abast «tota Catalunya»**~~ ✅ FET (#148, 2026-06-18) — línia d'abast
   a la home (`home_map_scope`) + `map_outside_scope` revisat (3 nivells). Còpia afinable per Bea.
6. **[ops] Ritual de llançament** (Talaia+Mirador) — treure noindex ×3 (`app.html`, `robots.txt`,
   `_headers`); `og:image`; ~~sitemap complet~~ ✅ (#150: 947×2 munis, bastida pre-llançament);
   deploy verd al domini; comprovació final. *(La resta és l'acte de publicar: el dia D.)*

## P1 — al llançament, no bloquegen el dia exacte

7. **[web/viz] Spec ric** (Mirador+Llegenda+Brúixola) — dades obertes §9 (/dades, descàrrega, xifra
   citable, embeds, kit premsa) · viz noves §4 (Dorling, slider, «el riu», beeswarm, emblema doble
   corrent) · ~~espina territorial + breadcrumb §7~~ ✅ FET (#151: muni→comarca→vegueria exacte +
   breadcrumb + veïns a tots els munis; bug eyebrow comarca corregit) · 3 profunditats + test CI §1.
8. **[llengües] Aranès + anglès** (Brúixola+Talaia) **(IA)** — repàs còpia ca/es font → Apertium/AINA
   (oc) + anglès. Espera la reposició del límit.
9. **[web/IA] Pregunta-li «super beta»** (Brúixola) **(IA)** — genUI / resposta-com-UI.
10. **[a11y] Accessibilitat AA** (Llegenda+Mirador) — teclat al mapa, contrast, `axe-core` a CI.

## Diferit a Fase 2
Licitacions de veritat (menors → majors/diputació) · fondària completa de fitxa (tipologia +
lectures-IA) per a tot CAT · fonts noves §12.
