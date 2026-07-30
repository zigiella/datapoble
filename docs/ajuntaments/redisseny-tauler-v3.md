# Redisseny del Tauler de dades · v3 — PROPOSTA (pendent del vot de Bea)

*Talaia, 2026-07-29. Encàrrec de Bea: «Repassa i redissenya tot el dashboard. Com és l'ordre i la
disposició de les xifres. Si hi ha una altra forma de posar les edats. Si població/padró ha d'estar
més a prop d'ETCA. Si els apartats són els adequats. Com rotulem els apartats. Si hem d'agrupar
mètriques. Si fossis tu qui entres al dashboard, com t'agradaria llegir-lo? Revisa també el text de
cada mètrica: què sobra, què falta.»*

Res d'aquest document canvia la doctrina: «<5» com a interval · cap fletxa sense període ·
`sense_serie` amb motiu · font O fórmula a cada xifra · rang LLEGIT del mart · frescor per targeta.
El redisseny és de LECTURA, no de dades.

---

## 1 · Diagnòstic del tauler actual (com es llegeix avui)

Ordre actual de la pàgina: **Tauler (A·B·C·D)** → targeta gran «N hab. padró» → **Els números
clau** → La maquinària (P3) → Pregunta-li → comarca → miralls.

Problemes, per ordre de gravetat:

1. **La primera xifra que veu el lector és «Índex d'envelliment: 350»** — un índex derivat abans
   de saber quanta gent hi viu. L'obertura d'un tauler municipal ha de ser «quants som», no una
   ràtio.
2. **El grup A té 12 targetes de 20** — població, 4 franges, 3 lloc-de-naixement, 2 percentatges,
   envelliment i ETCA, tot barrejat en una sola graella. És on el lector es perd.
3. **Padró i ETCA viuen separats** (ETCA és l'última targeta del grup A; el padró gran és una
   secció a part, per sota del tauler). Són la mateixa pregunta — «quanta gent hi ha?» — amb dues
   respostes oficials: els empadronats i la presència equivalent. La intuïció de Bea és correcta:
   han d'anar juntes, i a dalt de tot.
4. **Duplicació estructural**: la targeta gran del padró i «Els números clau» repeteixen 4 xifres
   que ja són al tauler (padró, ETCA, % no principal, renda). Dues seccions redundants.
5. **Dos grups es diuen gairebé igual** («El pols i l'economia» / «El pols de la vida diària») i la
   frontera entre ells és fina.
6. **Les edats com a 4 targetes de xifra grossa** pesen molt i diuen poc: el que un alcalde vol
   veure és la FORMA de la distribució (quanta canalla, quanta gent gran), no quatre números solts.

## 2 · Com m'agradaria llegir-lo (la narrativa)

Un lector — alcalde o veí — entra amb cinc preguntes, en aquest ordre:

> **Quants som?** → **Com canviem?** → **On vivim?** → **De què vivim?** → **Quin rastre deixem?**

El tauler v3 és exactament aquesta seqüència.

## 3 · Estructura proposada

### Capçalera de presència (nova, substitueix la targeta gran + absorbeix ETCA)
Al capdamunt, UNA franja amb les dues xifres de presència juntes:
- **Padró (2025): N empadronats** — font Idescat.
- **Presència oficial (ETCA): M** o «sense dada oficial» — amb una línia plana: *«equivalent a
  temps complet: quanta gent hi és de mitjana al llarg de l'any, comptant-hi segones residències i
  visitants»*. On no n'hi ha: «Idescat només la publica per a municipis ≥1.000 hab.»
- Si ETCA > padró o padró > ETCA, el lector ho veu SOL — no ho interpretem nosaltres (P1/P2
  tornaran a fer-ho quan E7b aterri).

### Grup 1 · «La gent» (abans A, de 12 targetes a 5)
| Targeta | Contingut | Canvi |
|---|---|---|
| **Estructura d'edats** | UNA targeta amb barra apilada horitzontal (0-14 · 15-64 · 65-84 · 85+), recompte i % per franja | Substitueix 4 targetes. La barra diu la forma; els números hi són igualment |
| **Índex d'envelliment** | la xifra + frase plana: *«X persones de 65 o més per cada 100 menors de 15»* | Deixa de ser la primera targeta del tauler; va DARRERE de les edats de què deriva |
| **D'on venim** | UNA targeta amb barra apilada (nascuts a Catalunya · resta d'Espanya · estranger) + % nascuts a l'estranger amb el seu rang quan arribi (E9) | Substitueix 4 targetes. La nota «foto, no sèrie» hi va UNA vegada, no quatre |
| **Nacionalitat estrangera** | % + l'única evolució del bloc (2021→2025), amb la nota que la sèrie és de nacionalitat | Es queda tal qual (és l'única amb sèrie) |
| *(ETCA puja a la capçalera)* | | |

### Grup 2 · «Les cases» (abans B, igual + 1 candidata)
- **% habitatge no principal** (amb rang comarcal) — es queda.
- **Establiments turístics / 1.000 hab** (amb rang) — es queda, i **proposta**: que la targeta
  digui també el recompte cru i els HUT (*«31 establiments, 24 són HUT»*) — les dues xifres JA
  arriben al web (`rtc_total`, `rtc_hut`), només és pintar-les. El rati sol amaga que a molts
  pobles «turisme reglat» vol dir pisos turístics.

### Grup 3 · «Feina i renda» (abans C, sense els serveis)
- **Atur registrat** (targeta ampla amb sèrie i les DUES comparacions) — es queda tal qual: és la
  targeta més ben resolta del tauler.
- **Renda neta per persona** (amb rang) — es queda.

### Grup 4 · «El dia a dia» (abans C+D reagrupats)
- **Comerç i serveis** (els dos comptes OSM) — ve del grup C: és vida diària, no macroeconomia.
- **Residus kg/hab/any** (amb rang) · **Elèctric domèstic kWh/hab** (amb rang) · **Vidre kg/hab/any**
  — es queden junts (E2 de Bea).

### Fora
- **«Els números clau»**: s'elimina (les 4 xifres ja són al tauler; una era duplicada dues vegades).
- **La targeta gran del padró**: absorbida per la capçalera de presència.
- La maquinària (P3), Pregunta-li, comarca i miralls: **es queden com estan**.

Recompte: de 20 targetes + 2 seccions duplicades → **13-14 targetes + 1 capçalera**, mateixa
informació, cap xifra perduda.

## 4 · Rètols proposats

| Ara | Proposta | Per què |
|---|---|---|
| Qui hi ha (i qui hi haurà) | **La gent** | Curt; la pregunta del futur la responen les franges i l'evolució, no el títol |
| Les cases | **Les cases** | Es queda: és el millor rètol dels quatre |
| El pols i l'economia | **Feina i renda** | Diu el que hi ha; «pols» xocava amb el grup següent |
| El pols de la vida diària | **El dia a dia** | Curt, i deixa de xocar |

## 5 · Text de cada mètrica: què sobra, què falta

**Sobra:**
- **«EMEX f69 (darrer any)» com a fórmula** a les tres targetes de lloc de naixement: és un
  localitzador de camp intern, no una fórmula, i surt amb el símbol ƒ com si fos una derivada.
  → Handoff Sondeig/Talaia: al contracte, `formula: directe` + la referència f69/f72/f73 a
  `origin_source`/nota interna. La targeta ha de dir «Idescat (EMEX) · 2025» i prou.
- **«sense procés automàtic» a cada targeta**: cuina interna. El lector vol saber si la dada és
  fresca (cadència + darrera càrrega, es queden); com la refresquem nosaltres és de /metodologia.
  → PENDENT DE VOT: és una esmena E5 de Bea; proposo moure-la, no esborrar-la.
- **La línia sencera d'ETCA** («Presència oficial: ETCA (població equivalent…), Idescat. Als
  municipis on…»): massa llarga per a peu de targeta; amb la capçalera nova es parteix en la
  frase plana + un enllaç a metodologia.
- **El motiu tècnic de `sense_serie`** tal com raja («Es deriva de franges d'EMEX, que no tenen
  sèrie per API», «encara no ingerida»): per al lector és argot. → Reescriptura al mart (Sondeig),
  to ciutadà: *«La font oficial només publica l'any vigent: no en podem ensenyar l'evolució»* /
  *«La font en té la sèrie; encara no la carreguem»*. El motiu HONEST es manté; canvia el registre.

**Falta:**
- **Frase plana a l'índex d'envelliment**: «X de 65+ per cada 100 menors de 15». La fórmula hi és;
  la traducció humana no.
- **El caveat de micromunicipi (E13, ja decidit per Bea: caveat, no emmascarar)** als per càpita
  físics quan padró < 250 — inclou el cas Sant Jaume (residus 1.132) ja investigat.
- **HUT a la targeta de turisme** (vegeu Grup 2).
- **«El % és sobre la població del padró»** una sola vegada com a nota del grup La gent (les dues
  particions sumen exactament el padró — verificat als 947; dir-ho dona confiança i estalvia
  quatre repeticions).

## 6 · Ordre d'execució proposat (si Bea vota que sí)

1. **Mirador** — reordenar grups i capçalera de presència + matar duplicats (cap dada nova).
2. **Mirador** — targetes de barra apilada (edats, origen); `verify-govern.mjs` s'adapta (les 8
   xifres segueixen al DOM, canvia la disposició).
3. **Sondeig** — reescriptura ciutadana dels `motiu` de `sense_serie` + fórmules f69→directe (amb
   Talaia al contracte).
4. **Talaia** — E13 (caveat micromunicipi) al contracte, que ja estava encuat.
5. Les guardes existents (20/20 amb fitxa, font-o-fórmula, períodes) han de seguir verdes; la de
   verify-docs vigila que cap mètrica quedi fora de la metodologia amb el reagrupament.

## 7 · Preguntes obertes per a Bea (vot narratiu)

1. Els rètols del §4 — vist-i-plau o alternatives?
2. «sense procés automàtic»: es mou a metodologia o es queda a cada targeta?
3. La barra apilada d'edats substitueix les 4 targetes o les COMPLEMENTA (barra + 4 mini-xifres)?
4. La capçalera de presència amb padró+ETCA junts: el text pla proposat per a ETCA serveix?
5. HUT a la targeta de turisme: sí/no?
