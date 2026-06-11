# Backlog: preguntes i temes de la Bea (mentre analitza la IA/interpretació)

**Fecha:** 2026-06-10
**Autora:** Talaia (recull) · **De:** Bea
**Tema:** 8 temes oberts de producte/arquitectura per pensar i planificar. NO són encàrrecs immediats: són el backlog raonat.
**Status:** backlog / qüestions obertes

## 1. Bases (llum/vidre/residus…) a escala Catalunya
**Pregunta:** d'on les agafem i com tractar-les de debò a tota Catalunya.
**Lectura (Talaia):** avui són FIXES i endògenes (410/1224/26,5, de viles de vall del Berguedà) → circularitat a escala (crítica de la consultora). Cap a **3 nivells**: (a) **contrast oficial** (ARC residus/vidre; ICAEN/Idescat elèctric domèstic) per sanity-check; (b) **base ESPERADA per tipus territorial** (litoral turístic, Pirineu, interior rural, capital comarcal, corona metro, agroindustrial, micromuni dispers), pop-ponderada; (c) **base modelada** = f(llars, vivenda, renda, clima, altitud, model de recollida…). Indicador clau: **excés = observat − esperat** («genera més del esperable pel seu tipus?»). Ordre: tipològic ABANS que modelat («no canviar base simple per caixa negra»). Àncora externa: **ETCA** (municipal ≥1.000 hab + comarcal). **Dep:** escala Catalunya + tipologia territorial. **Front:** Sondeig.

## 2. Mouseover/clic del mapa en MÒBIL
**Lectura:** el hover no existeix al mòbil. Patró: **tap a municipi → targeta/bottom-sheet** (dada + procedència + «obrir fitxa»); tap fora → tanca. Decuplar: tap = mostra (no navega); el botó de la targeta navega. Aplica a `/mapa`, l'atles i la **constel·lació** (el tooltip que vaig fer és hover). Detectar pointer coarse. **Front:** Mirador. **Junt amb #8.**

## 3. «Ranking IETR»: comarca I Catalunya
**Lectura:** sí, doble escala (consultora). Afegir `IETR_pct_cat` + `IETR_rank_cat` al costat del comarcal; la fitxa/resum mostren tots dos («#1 de 31 al Berguedà · percentil X de Catalunya»). Barat un cop hi hagi dada de Catalunya. **Dep:** escala Catalunya. **Front:** Sondeig + Mirador.

## 4. Política a la fitxa: deltes 2021–2024
**Lectura:** mostrar l'EVOLUCIÓ, no la foto («el vèrtigo, no la foto»). Δ extrema dreta, Δ participació entre eleccions. Mantenir els 3 guardrails (lectura ecològica, avís N petit, cap inferència individual/causal). **Dep:** ingerir múltiples eleccions per municipi. **Front:** Cabal/Sondeig (dada) + Mirador (UI).

## 5. Municipis mirall: comarca I Catalunya
**Lectura:** sí, doble escala com el ranking. «Miralls dins la comarca» + «miralls de tota Catalunya» (els segons són MÉS interessants: el bessó funcional d'un poble turístic del Berguedà pot ser al Pirineu o a la Costa Brava). **Dep:** vectors de característiques a escala Catalunya. **Front:** Sondeig (dada) + Mirador.

## 6. Secció «mapa de miralls» — visualització abstracta (graf?)
**Idees (Talaia), de més a menys recomanada:**
- **(b) Embedding 2D** (MDS/UMAP del vector de 8 senyals): cada muni un punt en un pla on proximitat = similitud funcional real; els «tipus territorials» emergeixen com a clústers. Com la constel·lació però amb les 8 dimensions → 2. **El meu favorit** per a la secció.
- **(d) Constel·lació de veïns EGOCÈNTRICA** (a la fitxa): tries un muni → ell al centre, miralls en òrbita, radi = (dis)similitud, etiqueta a cada radi = quin senyal els agermana.
- **(a) Graf de força**: nodes=munis, arestes=similitud>llindar. Adictiu però satura amb 947 → mostrar només el node + k-veïns (egocèntric), no tot.
- **(c) Heatmap de similitud**: tècnic, honest, compacte; menys sexy.
**Recomanació:** (b) per a la secció del menú + (d) a la fitxa. Caveat honest: tota projecció és lossy → «mapa mental, no mesura». **Front:** Mirador (+ Sondeig per al càlcul).

## 7. Menú: «Índex IETR» i «Excursionistes de dia» — què fer
**Lectura:** són stubs (només /resum i /mapa implementats). «Índex IETR» com a secció pròpia és **redundant** (l'IETR ja és a resum/mapa/metodologia/fitxa) → o bé una pàgina `/ranking` (taula ordenable de tots els munis, comarca+cat) accessible des del Resum, o fora del menú. «Excursionistes de dia» és una **tipologia**, ja es veu al mapa/fitxa → fora del menú. **Recomanació:** menú = espina del producte, ~5-6 ítems: **Resum · Mapa · Metodologia · Pregunta-li** + futur **Licitacions · Transformació demogràfica**. **Vot narratiu de la Bea.** **Front:** Mirador + Bea.

## 8. Menú de capçalera en MÒBIL
**Lectura:** nav responsiu (hamburger/drawer sota un breakpoint) amb selectors d'idioma i tema. **Front:** Mirador. **Junt amb #2** (sprint de mòbil).

## Agrupació per sprints (proposta)
- **Escala Catalunya** (gros): #1 bases esperades + #3 doble escala IETR + #5 miralls cat + #6 embedding. Tot depèn de tenir dada/vectors a escala.
- **Mòbil** (UX, independent): #2 + #8 + nav (#7).
- **Política temporal:** #4 (dada electoral multi-any).

— Talaia 🌊
