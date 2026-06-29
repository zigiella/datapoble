# 03 · Recomanació de solidesa — deixar datapoble sòlid, útil i honest

*Data: 2026-06-29 · Talaia · mètode Cambium Charter v0.5.*
*Pregunta de la Bea: «si l'objectiu és deixar el projecte el més sòlid, útil i honest possible —inclòs el dataset, que hem de netejar i curar— quina és la millor opció?»*

## Com s'ha decidit (i una lliçó incòmoda)

Diagnòstic multiagent sobre el repo (quatre lectors: dades, web, mètode, procés) + síntesi
+ **crítica adversarial** (honestedat, utilitat real, risc de dades) + **verificació manual** dels
fets que sostenen el dictamen.

**La síntesi automàtica va sobrepormetre.** Va posar com a prioritat #1 un defecte —«la fitxa mostra
confiança *alta* sense etiqueta de no-validació per als 947»— que el codi **ja resol** (és la feina P0:
`+page.svelte:530`, gate `{#if !validat}` → «sense validació oficial», score només si `validat`). Els
tres crítics ho van enxampar i s'ha confirmat obrint els fitxers. És exactament el pecat que combatem,
comès per la pròpia eina. **Conclusió de mètode: cap síntesi —ni la multiagent— entra sense
verificació manual del fet que la sosté.** Aquesta disciplina *és* l'actiu.

## Estat verificat (no de memòria)

- **`muni_lede`** (`messages/ca.json:262`) afirma literalment: *«La mateixa riquesa i honestedat que el
  Resum comarcal, ara per a qualsevol municipi.»* Es pinta a `+page.svelte:465` per a (gairebé) tots els
  947 munis amb fitxa → **overpromise viu i real**.
- **La confiança ja està capada** per validació (P0). No és el forat.
- **El tag de tipologia ja està tret** de la fitxa (queda un comentari ranci a `+page.svelte:504`).
- **`validacio_etca` NO existeix** a `municipis.catalunya.json` (0 ocurrències). La síntesi es va
  inventar un «camp mort a NULL». La validació es resol creuant `validats.json` (486 ine5) al loader.
- **Gap 947→927 = 20 munis**, i són **exactament** els 20 amb `confianca` però sense
  `poblacio_pernocta_est`. Tots micromunis; confiança `baixa`(10)/`mitjana`(10), **cap «alta», cap amb
  score**. Com que no són `validat`, la fitxa ja els mostra «sense validació oficial» → el forat és **a
  la dada** (l'artefacte afirma confiança sobre una estimació inexistent), no a la pantalla.
- **`IETR` es re-deriva independent** de la pernocta (winsorització resid/turisme, `derive_fase1.py`):
  NO s'ha de tocar quan falta la pernocta.
- **Infracobertura per tipus** (corona_metropolitana 55,6% n=9, litoral_metropolita 57,1% n=7) la
  calcula `calibracio_intervals.py` però **no arriba a la UI**. A n=7–9 el % és gairebé soroll: s'ha de
  publicar **amb la n al costat** o dir «no validat per separat (n massa petita)».
- **El nucli validat són 9 municipis** (Berguedà ≥1.000, ρ=0,967, error 8,2% *dins de mostra*); tota la
  resta és generalització (banda 80→78,4% *held-out*). Hauria de ser un **fet publicat**, no enterrat.

## La millor opció (north star)

**Tancar la distància entre el que el web *ENSENYA* i el que ha *VALIDAT* —regenerant la dada des de la
font, mai editant el JSON a mà, conservant els 947 amb banderes honestes— i alhora no buidar la
proposta de valor: protegir la pernocta elèctrica <1.000 hab (l'única dada que Idescat no té) com a
*RESPOSTA*, no només com a número ben etiquetat.**

## Prioritat (corregida contra el codi real)

1. **La còpia, no la confiança.** `muni_lede` honest (la confiança ja està capada). Barat, alt impacte,
   overpromise viu. → *en marxa (PR).*
2. **Degradar la maquinària P3 fora del Berguedà** (5 números, càrrega), NO la confiança. **Matís: NO la
   mateixa tisora per als 486 validats contra ETCA** — allà es pot mostrar *més*. Replegar-vs-caveat =
   **vot de la Bea**.
3. **Sanejar la dada des de la font.** Regla `pernocta_est null ⇒ confiança null` a l'exportador (els 20
   = el forat 927/947, un sol fenomen). → *en marxa (PR).*
4. **Banderes data-level** (`regim_dens`, `soroll`/`senyal` propagant la `classe` que **ja existeix** al
   CSV, `outlier`) — **tri-estat amb `no_classificable`**, mai default booleà; i `confianca` →
   `confianca_model` (que no es llegeixi com `confianca_resultat`).
5. **Cobertura per tipus a /metodologia** — **sempre amb la n**; si n<~15, «no validat per separat».
6. **Tancar la costura del gap a la fitxa** (≥1.000 = ETCA oficial) — últim pas escrit de Fase 1.
7. **Tapar el buit d'utilitat** (front-0, **vot de la Bea**): protegir la pernocta <1.000 i
   `serveisLectura` com a *resposta*; substituir la tipologia retirada del mapa per **% habitatge no
   principal** (oficial, respon la pregunta del periodista local); decidir què fem amb `/pregunta-li`.
8. ~~Arreglar el «camp mort `validacio_etca`»~~ — **descartat: el camp no existeix.**

## Curar el dataset: tres baranes innegociables

1. **Regenerar des de la font, mai editar el JSON a mà.** Funció pura i determinista (marts + CSV) →
   idempotent via `--check`. En working dir compartit, una escriptura interrompuda deixaria una dada que
   afirma validació que té a mitges.
2. **Overlay no destructiu.** No anul·lar en silenci: el mart (font) conserva l'original; l'exportador
   declina publicar una confiança sense estimació i **registra els munis afectats** (log + comentari).
3. **Banderes tri-estat amb `no_classificable`.** La `classe` soroll/senyal només cobreix 486 munis; un
   `soroll=false` per defecte sobre els altres **afirma netedat que mai s'ha provat** (survivorship
   bias). L'absència de validació ha de ser un *valor visible* — és el north star.

**El que NO s'esborra:** cap dels 947, ni els 142 soroll, ni el règim dens, ni els extrems costaners.
Curar = **etiquetar i degradar la UI**, no amputar. Que el model falli en un lloc és informació.

## El que és de la Bea (no s'executa sense tret de sortida)

- **Vot W2**: replegar la fitxa fora-Berguedà a targeta de rang *vs* conservar-la amb caveats forts.
- **Front-0 (utilitat)**: protegim la pernocta <1.000 com a resposta, o l'acceptem com a límit?
- **Postura política del *gap*** (pendent a `next.md`).

## Seguiment (source: workflow `datapoble-solidesa`, 2026-06-29; 8 agents)

Diagnòstic complet i crítica adversarial arxivats a la sessió de Talaia. Aquest doc és el resum durador
per al repo (no a la memòria local — lliçó de recuperació).
