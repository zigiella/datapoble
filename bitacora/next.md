# Cua — camí al llançament

*Derivada de `docs/pla-llancament-2026-06.md` (v2, decisions de Bea 2026-06-18). Es treballa de dalt
a baix; cada tasca = un PR. `P0` bloqueja el llançament. El carril de dades i la web NO depenen del
límit de despesa; les tasques marcades **(IA)** sí (esperen que es reposi).*
*Mètode: **Cambium Charter v0.5** (adoptat 2026-06-20).*

## P0 — bloquegen el llançament

1. ~~**[dades] Estendre Nivell C a tot Catalunya**~~ ✅ FET (#152, 2026-06-18) — **91→927 munis en
   rang** (486 ETCA validats + 441 sub-1000 sense validació). R²=0,41, cobertura 70%, held-out
   robust. Densitat=pop/àrea (r=0,9999 vs EMEX, sense ~900 crides). Costaners PROVISIONALS.
   **Pendent:** ~~(a) llista costanera oficial~~ ✅ (#154: 70 oficials Territori/PPOL per ine5;
   geomètrica = 0 FN / 13 FP) · ~~(b) vista de cobertura~~ ✅ (#153) · (c) pic litoral · (d) residus L2.
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
   citable, embeds, kit premsa) · viz noves §4: ~~beeswarm del gap~~ ✅ (#155) · pendents (Dorling,
   slider, «el riu», emblema doble corrent) · ~~espina territorial + breadcrumb §7~~ ✅ (#151) ·
   3 profunditats + test CI §1.
   - **Pobles mirall de tota Catalunya**: ~~(d) constel·lació egocèntrica a la fitxa~~ ✅ FET (#157,
     «El bessó del teu poble», 6 bessons cat-escala SVG per a tots els munis). Pendent: **(b) embedding
     2D de secció** (PCA/MDS dels 927, el «mapa mental») + doble escala #5 (afegir bessons de la
     COMARCA reusant `mirall.ts`).
11. ~~**[web] Breadcrumb territorial navegable + pàgines de comarca/vegueria (§5)**~~ ✅ FET (#158):
    43 `/comarca/[slug]` (beeswarm del gap + munis) + 8 `/vegueria/[slug]` (comarques) + `Espina`
    refactoritzada a `trail` amb enllaços (Catalunya⇄vegueria⇄comarca⇄municipi). Sitemap ampliat.
    Notes: redundància `/resum` vs `/comarca/bergueda`; descobribilitat (índex de comarques) pendent.
8. **[llengües] Aranès + anglès** (Brúixola+Talaia) **(IA)** — repàs còpia ca/es font → Apertium/AINA
   (oc) + anglès. Espera la reposició del límit.
9. **[web/IA] Pregunta-li «super beta»** (Brúixola) **(IA)** — genUI / resposta-com-UI.
10. **[a11y] Accessibilitat AA** (Llegenda+Mirador) — teclat al mapa, contrast, `axe-core` a CI.

12. **[web/viz] Secció mapa completa (home + /mapa)** (Mirador) — Bea, fer el mapa complet:
    - ~~vista municipi: pintar els coberts amb la seva dada~~ ✅ FET: #159 (gap) → **#160** (per
      l'INDICADOR triat: gap+residus a tot CAT, escala compartida; resta només-Berguedà atenuat;
      `indicadors-catalunya.json`). Cal cop d'ull visual de Bea.
    - ⏳ **indicadors cat-escala NOUS** (densitat, renda, gas, turisme RTC/resident) per enriquir.
    - ⏳ vista **comarca**: info per mouse-over (tooltip amb agregats).
    - ⏳ vista **vegueria**: info per mouse-over.
    - ⏳ **home:** indicador del mapa (tipologia→gap?) perquè mostri dada cat-escala a municipi (vot Bea).

13. **[dades] Dataset PROFUND a tot Catalunya** (Sondeig) — Bea «volem fer-ho bé». Pla:
    `docs/pla-catalunya-profund.md`. Estendre el dataset ric del Berguedà als 947, model unificat, honest.
    - ~~Prova del model unificat al Berguedà (guardó ETCA)~~ ✅ #161 (PASSA: base Nivell C millora 11,9%→8,2%).
    - ~~F1.1 registre de municipis CAT (codi6)~~ ✅ #162 · ~~F1.2a connectors bulk~~ ✅ #163 ·
      ~~F1.2b per-muni a trossos (EMEX/origen)~~ ✅ #164 → **raw dels 947 baixat** (residus/rtc/icaen/
      electoral/EMEX/origen; OSM diferit a 2a onada).
    - ~~**F2.1** dbt + pont stg_nivellc~~ ✅ #166 · ~~**F2.2** unificar mart_municipi a 947~~ ✅ #167:
      base L1 = base_pred per muni · confiança per tipus_territorial · comarca per muni · OSM 2a onada
      (tipologia/restauració Berguedà, resta `pendent`). **Guardó ETCA Berguedà 8,2%/ρ=0,967** (= #161).
      947 munis, 927 amb presència. Verificadors del CI (verify_marts/derive_fase1/etca/tipus) al dia.
    - ~~**F3** exportar l'espina a tot CAT~~ ✅ #169 (`municipis.catalunya.json`, 947; bergueda regenerat).
    - ~~**F4.1** fitxa uniforme~~ ✅ #170 (row per a tots, fitxa partida per muni; resol «fitxes diferents»).
    - ~~**F4.2** mapa harmonitzat~~ ✅ #172 (trames a tot CAT segons confiança + un sol tooltip; `conf` a
      l'artefacte compacte). **Cal cop d'ull visual de Bea** (canvas WebGL).
    - ⏳ **F5** 2a onada (no bloquejant): OSM a tot CAT (restauració/serveis) + subtipus de tipologia +
      indicadors cat-escala nous (densitat/renda/gas) + altres marts (electoral/demografia) a tot CAT.
    - **L'arc «fer-ho bé» (F1–F4) és complet i a `main`.**

## Diferit a Fase 2
Licitacions de veritat (menors → majors/diputació) · fondària completa de fitxa (tipologia +
lectures-IA) per a tot CAT · fonts noves §12.
