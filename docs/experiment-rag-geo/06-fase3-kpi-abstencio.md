# Fase 3 · el KPI d'abstenció — contracte de disseny (abans de construir el banc i la mètrica)

**De:** Talaia · **Origen:** nota de la Rapaz (30-06-2026, OneDrive/CAJON/14) · **Data:** 2026-07-01
**Ordre:** aquest contracte es fusiona **abans** de construir el banc i de codificar la mètrica. Aquí «definit abans» no és estil: és el que **impedeix fer-se trampes**, perquè aquesta és l'única fase que produeix un número que pot dir que l'experiment s'equivoca.

> Les fases 0, 1 i 2 construïen mecanisme i **no podien sortir malament**: es corregeixen fins que fan el que vols. La Fase 3 **mesura, i pot sortir malament** — aquest és el seu sentit. El perill no és que surti malament; és construir-la, després de tres èxits, de manera que **no pugui sortir malament sense adonar-se'n**. El contracte treu aquesta opció de les mans.

## Les tres coses que es fixen abans de veure cap resultat

### 1. Composició del banc
- Entre **30 i 50** preguntes, etiquetades.
- Com a **mínim un de cada tres** casos té com a resposta honesta **l'abstenció**, no una xifra.
- Dins dels casos d'abstenció, hi són **les tres menes de no distingibilitat** que el sistema diu saber tractar:
  - **soroll de la dada** (l'interval inclou el padró),
  - **col·lisió de municipi** (mateixa estimació que un altre poble),
  - **solapament de bandes en comparació** (dos munis que no s'ordenen).
- **Casos contestables de debò** també, amb resposta sòlida, perquè la mètrica capti tots dos costats. *Un banc tot d'abstencions mesura tan malament com un tot de contestables.*
- **Preguntes fora del catàleg** (municipi sense dada, indicador que no existeix): resposta daurada = «no ho tinc», una altra forma d'abstenció honesta.

### 2. Etiquetatge congelat
- Les **respostes daurades les fixa la Bea, a mà**, sobre la dada verificada, decidint per a cada pregunta si la resposta honesta és **respondre o abstenir-se**.
- Es congelen **ABANS** de córrer el sistema. *Un banc que es pot retocar després de veure els resultats no és un banc, és una justificació.*
- L'etiquetatge **no es delega a cap model** (ni a la Talaia). El dia que el decideixi un LLM per anar més ràpid, la vara de mesura passa a ser una extensió del que es mesura, i el número és un mirall.
- El banc es **versiona al repo amb la seva data de congelació**, com els `--check`.

### 3. Nivells d'èxit definits per endavant (els fixa la Bea, abans de saber el número)
- **Honest:** el recall d'abstenció que et semblaria un bon resultat. *Proposta de partida de la Rapaz:* s'absté correctament a la gran majoria dels casos on la daurada és abstenir-se, sense abstenir-se de més als contestables. → **[Bea fixa el número]**
- **Decebedor:** el nivell que diria que hi ha feina, però la idea s'aguanta. → **[Bea fixa el número]**
- **La idea no funciona:** el nivell per sota del qual conclouries que heretar la σ de la dada **no basta** per calibrar l'abstenció. → **[Bea fixa el número]**

## La mètrica

Sobre el banc etiquetat: **abstention recall, precision i F1** (com AbstentionBench i RefusalBench). Els dos errors es reporten **separats**, perquè no són el mateix:

- **Abstenir-se de menys** (respon on hauria de callar): el **pecat greu**, el que el projecte existeix per no cometre. *«Barcelona −18% llegit com a fet», en versió conversa.*
- **Abstenir-se de més** (calla on podria respondre): el **pecat prudent**, que fa el sistema menys útil sense fer-lo mentider.

El número que es mira **primer** és el **recall d'abstenció**: quantes vegades, quan la resposta era callar, el sistema va callar. La precisió el complementa.

## El que compta com a resultat, encara que sigui negatiu

Un resultat negatiu **ben mesurat** és una contribució, no un fracàs, sempre que el banc fos honest. Si el KPI surt pobre sobre un banc net, s'ha après una cosa real i publicable: que heretar la σ de la dada no basta per calibrar l'abstenció, i **per què** el problema és dur. L'únic fracàs de debò és **un número bonic sobre un banc trucat** — no ensenya res i a més menteix.

## La decisió que es pren ara, en fred (es congela amb el banc)

> **Es prefereix un resultat negatiu honest a un positiu fabricat.** Si el número decep, es publica el número i el que se n'aprèn; **no es retoca el banc** fins que doni bé.

## Ordre respecte a la resta

La Fase 3 **tanca el nucli de valor** (fases 0–3, el 70%). El sub-experiment **estrella** (σ real vs σ d'embeddings MC-Dropout) ve després i és independent. Les fases **4 (graf) i 5 (temporal) no s'obren** fins que el número de la 3 estigui sobre la taula (portes tancades).

## Repartiment de feina (jurisdicció)

- **Talaia:** redacta les *preguntes* del banc (cobrint la composició de dalt) amb els *fets de dada verificats* al costat perquè la Bea pugui etiquetar informada; codifica la mètrica (recall/precision/F1 + els dos errors) i l'arnès de córrer; NO decideix cap resposta daurada.
- **Bea:** fixa la **resposta daurada** de cada pregunta (respondre/abstenir-se + què), els **tres nivells d'èxit**, i **congela** el banc (data). Després, i només després, la Talaia corre el sistema i reporta el número tal com surti.
