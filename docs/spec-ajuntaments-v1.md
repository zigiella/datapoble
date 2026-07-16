# SPEC · datapoble per a ajuntaments — v1
## Dashboard complet + radar de subvencions (experimental, activat a la Pobla de Lillet)

**De:** Bea (direcció humana) · **Per a:** Talaia (adopció, direcció i trossejat a `bitacora/next.md`)
**Data:** juliol 2026 · **Estat:** proposta per a adopció — Talaia la revisa adversarialment, la fixa al repo (suggerit: `docs/spec-ajuntaments-v1.md`) i n'esdevé la directora
**Prioritat declarada:** 1) **dashboard** (indicadors + dades internes + xat amb les dades) · 2) **radar de subvencions** · després, la resta
**Milestone extern:** demo a la Magda Lorente (Diba — Oficina de Serveis Digitals i Orientació a la Dada / SeTDIBA), setmana 6-8

> **Com llegir aquesta spec (mètode Cambium):** cada fase és publicable per si sola; cada tasca és un PR; els contractes es fusionen abans del codi que els implementa; cada tasca porta **llistó** (criteris d'acceptació) i és verificable adversarialment per Talaia. Aquesta spec defineix *què* i *amb quins límits*; el *com* fi el decideix cada front dins de la seva jurisdicció.

---

## 0. Decisió de producte

datapoble incorpora una **segona audiència**: els equips de govern dels municipis petits (començant pel Berguedà, cas real: la Pobla de Lillet, 1.107 hab.). No canvia la missió ni la veu: **els mateixos números honestos per a tothom** — la fitxa que veu un alcalde és la mateixa que veu un veí o un periodista. El que s'hi afegeix és utilitat directa de govern: pols mensual del municipi, dades internes que cap font pública té, un radar que vigila convocatòries, i un xat que respon amb font, fórmula i abstenció honesta.

**No-objectius d'aquesta v1 (fora d'abast, explícit):** butlletí mensual narratiu («el poble aquest mes»), cartell A4 imprimible, radar per a entitats, fases 4–5 del RAG-geo (graf/temporal), extensió a Catalunya, cap forma de personalització que amagui indicadors incòmodes.

---

## 1. Principis (els del repo + tres de nous)

Hereten i manen: **right-sizing** (ADR-01: la dada és petita; res de serveis nous si DuckDB + Parquet + workflows ho fan), **procedència sempre** (cap número sense font, data i fórmula — `semantic/metrics.yml` és l'únic contracte), **CI offline** (fixtures; cap test depèn de xarxa ni de claus), **secrets només a workflows** (mai al codi ni al CI de PR), **privacitat per disseny** (etiquetes de visibilitat; la capa electoral 🔴 no es toca ni es creua).

Nous, específics d'aquesta spec:

1. **Porta humana a tota sortida amb destinatari.** El radar *proposa*, mai presenta ni envia res a cap administració; el xat *cita i s'absté*, mai afirma sense procedència; les dades internes *entren* validades i *surten* només agregades.
2. **Política editorial de govern:** cap indicador es retira ni es suavitza perquè incomodi un ajuntament. Si un número fa mal, s'explica (banda, context comarcal), no s'amaga. Això és condició de credibilitat davant la Diba, no un risc.
3. **Pressupost d'IA amb sostre dur.** Tota crida LLM passa pel patró `SpendGuard` existent; cada workflow amb clau porta límit diari i tall. Ordre de magnitud objectiu: radar < 0,15 €/dia; xat segons ús amb sostre mensual fixat per Bea.

---

## 2. Mapa de la transformació (sobre el que ja existeix)

```
                         JA EXISTEIX                    S'HI AFEGEIX (aquesta spec)
ingesta      idescat/rtc/residus/icaen/electoral…   + atur_otreball (primària, mensual)
                                                     + hermes_diba (selectiu: RFDB/IRPF,
                                                       habitatge construcció, vehicles)
                                                     + municipal_csv (dades internes)
signals      licitacions, contractació, sequera…    + subvencions (BDNS + CIDO + match)
transform    dbt+DuckDB → marts                     + mart_pols_mensual, mart_govern,
                                                     + mart_subvencions
semantic     metrics.yml (70 mètriques)             + ~12-15 mètriques noves (contracte C1)
ai           Brúixola text→SQL traçable + refús     + collita geo-rag: gàbia generativa
                                                       (validació dura SQL + validador cec)
web          municipi/[slug], licitacions,          + mode govern a municipi/[slug]
             pregunta-li (UI feta), mapa…           + secció radar (quan surti de l'experimental)
workflows    ci, daily-report, gen-fitxa…           + radar-diari (cron matinal + dispatch)
```

**Trampa de codis (recordatori obligatori a tot connector nou):** join per `ine5`. Castellar de n'Hug = **08052** (INE/Idescat; 08051 al Cadastre); la Pobla de Lillet = **08166** (Idescat 6 dígits: 081666). Els connectors nous inclouen test de la trampa.

---

## 3. Contractes (es fusionen abans del codi)

**C1 · Extensió de `metrics.yml`.** Famílies noves amb font i llicència: `atur_registrat` (mensual, Observatori del Treball via Socrata — client existent), `rfdb`, `irpf_base`, `habitatges_iniciats/acabats`, `parc_vehicles` (HERMES Diba, dataset «Indicadors socioeconòmics», citat com a font secundària/agregador), i les internes municipals (C2). Regla intacta: cap mètrica sense fórmula, font i data. *(Owner: Talaia; implementen Sondeig/Brúixola en consum.)*

**C2 · Contracte de dades internes municipals.** Fitxers `data/municipal/<ine5>/<indicador>.csv` amb esquema mínim `data,valor` (+ columna `nota` opcional), un indicador per fitxer, freqüència mensual, **només agregats de municipi** (mai persones, mai adreces). Cada indicador declara al contracte: `publicable: true|false` (decisió de l'ajuntament titular; si `false`, només surt al correu/mode intern, mai al web) i `llindar_alerta` opcional (dispara avís per correu, mai publicació automàtica). Validació del connector: esquema, monotonia de dates, valors no negatius, salt > x3 → quarantena i avís. Procedència: `municipal · <ajuntament> · manual`.

**C3 · Fitxa de subvenció normalitzada + perfil municipal.** Fitxa: `id_bdns?, font(s), organisme, objecte, beneficiaris, ambit_territorial, import, cofinancament?, data_publicacio, termini, enllaç, estat`. Perfil (`config/municipis/<ine5>-<slug>.yaml`): `tipus_beneficiari, poblacio, territori[], materies[{nom,pes}], projectes_en_cartera[], cofinancament_max, destinataris[]`. **Estat d'activació al perfil** (`actiu: true|false`): la ingesta i el filtre corren per a tots; **les sortides només per als perfils actius**. v1: actiu només `08166-lillet`; `08052-castellar` i `_default` preparats i dorments.

**C4 · Avaluació del radar (doctrina de banc, heretada del geo-rag).** Banc de **20 convocatòries reals arxivades** (mix: elegibles clares, descartables clares, i 4-6 casos frontera), **etiquetat a mà per Bea, congelat abans de veure cap sortida del classificador**. Mètriques: recall d'elegibles (el número de seguretat), precisió del semàfor, i taxa de descartades-amb-motiu-erroni. El prompt del classificador és sistema i es versiona; retocar-lo després del banc = entrenar contra el test (conjunt de desenvolupament separat). A més del banc: **validació en paral·lel 1 mes** contra el mètode manual, amb recall reportat tal com surti.

**C5 · Collita del RAG-geo cap a producte.** Quan la passada oficial generativa (preregistrada, contracte 08) estigui feta i reportada: PR de collita que porta a `packages/ai` (i) els **estatuts i regles de to** (oficial/senyal/soroll, bandes, col·lisió, empat, fora-de-catàleg — dos silencis diferents), i (ii) la **gàbia** (validació dura: cap número sense traçar a cel·la, agregats recomputats; validador cec: segon model, context aïllat, sense veure el raonament). `packages/geo-rag` queda congelat com a annex de recerca amb el seu resultat literal. **Fases 4–5: tancades** (cap necessitat de producte; la porta ja existeix).

**C6 · Mode govern.** Definició de la vista: ~12 KPIs (dels existents + C1 + C2) amb **percentil comarcal** (contra els 31), sèries temporals, seccions licitacions i (quan s'activi públicament) radar, i bloc de preguntes suggerides cap a `/pregunta-li`. Política editorial del §1.2 escrita al brief. *(Owner: Talaia amb vot narratiu de Bea; implementa Mirador; tokens/impressió, Llegenda — la sortida impresa queda post-v1.)*

---

## 4. Track R — Radar de subvencions (experimental · només la Pobla)

*Objectiu: que un matí de la setmana 3 el correu digui «ahir la BDNS va publicar X i encaixa amb el perfil de la Pobla per Y» — amb el banc C4 aprovat i sense haver enviat res enlloc.*

| # | Tasca (=PR) | Front | Llistó (criteris d'acceptació) |
|---|---|---|---|
| R0 | Contractes C3+C4 fusionats | Talaia | banc congelat amb etiquetes de Bea; perfils amb `actiu:` |
| R1 | Connector BDNS (`signals/subvencions_bdns.py`) + fixtures | Sondeig | API REST pública consumida amb paginació i dedupe per id; CI verd offline amb fixtures reals arxivades; test de la trampa de codis |
| R2 | Filtre dur + puntuació de perfil (`subvencions_match.py`) | Sondeig | determinista, testejat amb el banc: cap elegible clar filtrat; log de descartades amb motiu d'una línia |
| R3 | Semàfor + resum 3 línies (`ai/radar_classify.py`) | Brúixola | Haiku via OpenRouter, temperatura 0, proveïdor fixat; **corre només post-filtre**; run del banc C4 reportat tal com surt; SpendGuard amb sostre diari |
| R4 | Workflow `radar-diari.yml` + correu | Sondeig/Trazo | cron matinal + `workflow_dispatch`; secret només al workflow; correu amb verdes+grogues+descartades; **destinataris = Bea** (secretaria de la Pobla quan l'Ajuntament digui sí); cap sortida per a perfils `actiu:false` |
| R5 | Connector CIDO (RSS) + dedupe interfonts | Sondeig | convocatòria vista a 2 fonts = 1 fitxa amb 2 procedències |
| R6 | Esborrany de memòria per a verdes (`ai/radar_memoria.py`) | Brúixola | Sonnet via OpenRouter, **només sota demanda** (mai al cron); sortida com a fitxer adjunt/artifact, mai enviament extern |

**Porta de sortida de l'experimental** (cap anunci, cap `radar-bergueda.json` públic, cap perfil nou actiu abans de): banc C4 aprovat + 1 mes de validació paral·lela amb recall reportat + vistiplau narratiu de Bea.

---

## 5. Track D — Dashboard (indicadors + dades internes)

| # | Tasca (=PR) | Front | Llistó |
|---|---|---|---|
| D0 | Contractes C1+C2+C6 fusionats | Talaia | mètriques amb font/fórmula/llicència; política editorial escrita |
| D1 | Connector atur mensual (Observatori del Treball, Socrata) → `mart_pols_mensual` | Sondeig | sèrie mensual 31 municipis; byte-match de 3 municipis contra la font; refresh al workflow existent |
| D2 | Connector HERMES selectiu (RFDB/IRPF, habitatge construcció, vehicles) | Sondeig | només famílies absents de fonts primàries del repo; citat com a agregador; res que dupliqui mètriques existents |
| D3 | Connector `municipal_csv` + validació + quarantena | Sondeig | contracte C2 complet; fixture amb dades sintètiques etiquetades «demo»; alerta de llindar → correu, mai web |
| D4 | `mart_govern` (KPIs + percentils comarcals) | Sondeig | percentil contra els 31 calculat a transform, no al front |
| D5 | Vista mode govern a `municipi/[slug]` | Mirador | reutilitza KpiCard/MetricRow; i18n ca/es; AA; percentil visible amb la banda quan n'hi ha; enllaç a metodologia per indicador |
| D6 | Dades internes reals de la Pobla | Bea | proposar el CSV a l'Ajuntament (pilot); mentre no arribi, la demo va amb sintètiques marcades |

---

## 6. Track X — Xat amb les dades (seqüenciat rere el tancament del geo-rag)

| # | Tasca (=PR) | Front | Llistó |
|---|---|---|---|
| X0 | Tancar l'experiment preregistrat (paràfrasis 09 → passada oficial generativa) | Talaia/Brúixola | *ja contractat al track RAG-geo; aquesta spec no el modifica — només el seqüencia com a prerequisit de X1* |
| X1 | PR de collita (contracte C5) | Brúixola | doctrina + gàbia a `packages/ai`; geo-rag congelat amb resultat literal; evals del xat passen offline |
| X2 | API viva (`render.yaml`) amb clau, SpendGuard i CORS | Trazo | `/pregunta-li` funciona en producció; sense clau, mode offline honest (mai pantalla trencada — ja dissenyat així) |
| X3 | Catàleg ampliat + preguntes suggerides mode govern | Brúixola/Mirador | les mètriques D1-D3 responen pel xat amb procedència; 6-8 preguntes suggerides a la vista govern; pregunta fora de catàleg → refús llegible |

**Nota de seqüència:** si X0 s'encalla, el xat surt a la demo en mode text→SQL amb plantilles (ja honest i traçable) i la gàbia generativa arriba després. Cap dependència de la demo en X1.

---

## 7. Seqüència, portes i demo

```
Set 1   R0 R1        D0 D1          (X0 en curs, el seu propi track)
Set 2   R2 R3        D2             X0 passada oficial
Set 3   R4 (correu!) D3 D4          X1 collita
Set 4   R5 R6        D5             X2 API viva
Set 5-6 validació paral·lela radar · D6 · X3 · polir
Set 6-8 ★ DEMO MAGDA
```

**Portes (gates) que no es negocien:** el radar no surt de l'experimental sense la porta del §4 · cap resposta generativa al xat públic abans de X1 · cap dada interna al web sense `publicable:true` de l'ajuntament titular.

**Guió de demo (15'):** mode govern de la Pobla (atur del mes, percentils comarcals, dades internes) → xat en directe amb una resposta traçada i una **abstenció amb motiu** (al one-pager: el KPI 21/21 de la Fase 3 i el recall del radar del mes de validació) → el correu del radar del matí amb convocatòries reals → canvi a Castellar amb un clic (multi-poble = 1 YAML) → tancament: els 180+ municipis <5.000 hab. de la demarcació són el mateix pipeline.

---

## 8. Riscos

| Risc | Mitigació |
|---|---|
| Col·lisió amb el track RAG-geo actiu | X0 és el final natural d'aquell track, no un competidor; cap PR d'aquesta spec toca `geo-rag/` abans de X1 |
| Fals negatiu del radar | filtre dur testejat amb banc + descartades-amb-motiu al correu + mes de validació paral·lela + log |
| Cost API | SpendGuard a cada punt de crida; sostres al §1.3; Haiku només post-filtre; Sonnet només on-demand |
| Dades internes mal enteses (privacitat) | contracte C2: només agregats, `publicable` explícit, quarantena de valors anòmals |
| Deriva d'abast pre-demo | els no-objectius del §0 són vinculants; qualsevol excepció passa per Bea |
| La demo «va bé» i arriba pressió d'escalar | la resposta és el disseny: perfils dorments + `_default`; escalar = activar, no construir |

## 9. Mesura d'èxit

**Producte:** radar — recall del mes de validació (objectiu ≥0,9 sobre elegibles clares), convocatòries útils detectades; dashboard — mode govern viu amb ≥12 KPIs i ≥1 indicador intern real; xat — respostes amb procedència al 100%, abstencions correctes a preguntes fora de catàleg. **Procés:** cada fase publicada per si sola; CI verd offline sempre; cost mensual d'API dins de sostre. **Extern:** demo feta, one-pager lliurat, següent pas acordat amb la Diba (encaix SeTDIBA/Catàleg).

---

*Per a Talaia: si adoptes aquesta spec, el primer PR és fixar-la al repo amb les teves esmenes (la teva revisió adversarial és part del mètode), obrir R0/D0 i encuar la resta a `next.md`. On aquesta spec xoqui amb un ADR o un contracte existent, mana el repo — i m'ho fas saber per la bitàcora.*
