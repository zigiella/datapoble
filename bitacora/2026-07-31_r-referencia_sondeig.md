# R-REFERENCIA · el vintage que barrejava anys, el sector que no miràvem i les referències (Sondeig)

**Data:** 2026-07-31 · **Agent:** Sondeig · **Tasca:** bloc **R-REFERENCIA** de `bitacora/next.md`
(recerca de Bea del 2026-07-31 + verificació de Talaia).
**Lliurament:** un PR · **branca:** `sondeig/r-referencia` · **no fusiono jo.**

Artefactes tocats: `packages/transform/models/intermediate/int_consum_electric_pc.sql` ·
`int_consum_serveis_pc.sql` (NOU) · `int_residus_latest.sql` ·
`packages/transform/models/marts/mart_municipi.sql` · `mart_govern.sql` ·
`mart_consum_electric.sql` · `_marts.yml` ·
`packages/transform/tests/assert_consum_electric_vintage.sql` (NOU) ·
`packages/transform/verify_govern.py` · `tools/export_govern_web.py` ·
`data/marts/mart_municipi.parquet` · `mart_govern.parquet` · `mart_consum_electric.parquet` ·
`data/web/govern.{bergueda,catalunya}.json` · `municipis.{bergueda,catalunya}.json` ·
`etca-validacio.json`.

**`semantic/metrics.yml` NO s'ha tocat** (és de Talaia). Les esmenes proposades, amb diff exacte,
al final d'aquest document.

---

## Tasca 1 · 🔴 el bug del vintage: CONFIRMAT, i és pitjor del que deia el brief

### La prova, feta des de zero

Sense mirar el número de ningú, sobre la raw:

| xifra | valor |
|---|---|
| consum domèstic ICAEN 2024, sector 7, suma dels 947 | **10.032.130.000 kWh** (947/947, zero forats) |
| padró 2024 (suma dels 947) | **8.012.231** |
| padró 2025 (suma dels 947) | **8.124.126** |
| kWh/hab amb el padró de 2025 — **el que publicàvem** | **1.234,86** |
| kWh/hab amb el padró de 2024 — **el que toca** | **1.252,10** |
| raó dels dos padrons | **1,013966** (+1,3966 %) |

**El 1.252 de Bea surt exacte.** El bug era real i el brief l'encerta.

### ⛔ Però el brief diu «un 1,40 % per sota» i això només és cert de l'AGREGAT

Municipi a municipi l'error **no és uniforme, i ni tan sols té el mateix signe**:

| percentil de l'error per municipi | valor |
|---|---|
| mínim | **−11,88 %** |
| p5 | −3,78 % |
| mediana | +0,80 % |
| p95 | +4,45 % |
| màxim | **+12,24 %** |

**301 dels 947 anaven en direcció CONTRÀRIA** (el seu padró havia baixat de 2024 a 2025, així que el
seu consum per càpita sortia massa ALT, no massa baix). 62 municipis amb error >5 % i 6 amb >10 %.

I la conseqüència que el brief no preveia: **si l'error no és uniforme, l'ORDRE tampoc no ho és.**
Comparant el `mart_govern` vell amb el nou:

- **438 dels 947 municipis canvien de rang comarcal** a `kwh_hab`; salt màxim **11 posicions**.
- **5 comarques canvien de número 1** (Baix Llobregat, Bages, Ripollès, Osona, Urgell).

O sigui que no publicàvem un número un 1,4 % baix: publicàvem **un ordre equivocat per a gairebé la
meitat de Catalunya**. Les altres vuit mètriques de `mart_govern` surten **idèntiques valor a valor**
(comprovat parquet contra parquet): el canvi és quirúrgic.

### SÍ que es podia aparellar honestament — i per doble via

El brief avisava: «si NO pots aparellar els anys honestament, NO ho maquillis». **Es pot**, i sense
canviar de família de font:

- **`stg_demografia_estrangera_serie.poblacio_total`** (Idescat, Cens anual de l'INE) porta una
  **sèrie municipal 2021→**. És la mateixa font que el padró que ja publiquem: la seva xifra de
  **2025 coincideix municipi a municipi (947/947) amb l'EMEX f321** que fèiem servir.
  Cobertura 2024: **947/947, cap NULL**. És el nou denominador.
- **Contrast independent:** la població que **l'ARC** publica dins el seu propi dataset de residus
  (`stg_residus.poblacio_residus`) és **idèntica municipi a municipi (947/947, diferència màxima 0)**
  a la d'Idescat per a **2023 i 2024**. (Per a 2021 i 2022 divergeixen: és la ruptura metodològica
  documentada — l'Idescat passa al Cens anual el 2021 i l'ARC encara duia padró.)
- Agregats: 8.012.231 (2024) i 8.124.126 (2025), les xifres oficials.

**No ha calgut la via `censph`** que el brief deixava com a pla B, ni cap crida de xarxa nova.

### ⚠️ Un efecte lateral que hauria estat un bug NOU si no s'hagués mirat

La capa L1 del model aparcat calculava `poblacio × kwh_hab / base_pred`. Mentre `kwh_hab` duia el
padró de 2025 al denominador, aquell `poblacio` **es cancel·lava** i el resultat era exactament
`consum_total / base_pred` — que és com el calcula el camí **validat contra l'ETCA**
(`tools/export_pernocta_catalunya.py`, que fa `kwh_dom / base_pred` sense cap padró). Mesurat: **828
dels 927 idèntics** i els 99 restants a 1 persona d'arrodoniment (màxim 0,26 %).

Arreglant `kwh_hab` i deixant-hi `poblacio`, els dos camins s'haurien separat un 1,40 % — hauria
semblat que la validació ETCA MILLORAVA (error medià 8,2 % → 7,8 %) quan el que passava era que
havia inflat l'estimació. **S'ha corregit multiplicant per `poblacio_kwh`** (el mateix padró que hi
ha al denominador del senyal): la capa L1 queda com abans del fix, els dos camins tornen a
coincidir i l'ETCA torna al seu **8,2 % honest**. El model aparcat no s'ha mogut.

El `gap_pernocta` sí que es mesura contra el padró VIGENT: la pregunta és «quanta gent hi ha de més
respecte del padró que publiquem», i el contracte ja declara aquesta barreja (`date: "2024/2025"`).

**La bretxa germana, MESURADA i NO tocada:** la capa L2 fa `poblacio(2025) × kg_hab_any(2024)`, la
mateixa barreja. No entra en aquest PR: tocar-la és moure el model aparcat, i el contracte ja la
declara. **➡️ Handoff a: Talaia** si es vol homogeneïtzar.

### Abast del canvi a `mart_municipi` (55 → 60 columnes)

| columna | files que canvien | per què |
|---|---|---|
| `kwh_hab` | 917 | el fix |
| `kwh_base_ratio` | 762 | és `kwh_hab / 1224` |
| `confianca_score` | 463 | z-score de `kwh_hab` per tipus territorial |
| `divergencia_senyals` | 364 | íd. |
| `poblacio_pernocta_est` / `gap_pernocta` | 129 / 129 | **només arrodoniment** (màx 0,26 %, ±22 persones) |
| `confianca` | 17 | canvi de banda real (5 baixa→alta, 6 baixa→mitjana, 4 mitjana→baixa, 2 alta→baixa) |
| `gap_pernocta_pct` | 13 | arrodoniment |
| `carrega_funcional_est` | 6 | arrodoniment (delta màxim 1 persona) |
| **`tipologia`** | **0** | la classificació no es mou |
| les altres **46** | **0** | intactes |

Columnes noves: `poblacio_residus`, `kwh_any`, `poblacio_kwh`, `kwh_serveis_hab`, `kwh_serveis_any`.

### Guarda nova, provada en negatiu

`packages/transform/tests/assert_consum_electric_vintage.sql` peta si l'any del consum i l'any del
padró divergeixen, si la cobertura del domèstic deixa de ser 947, o si l'any no és el declarat per
`any_corroborador_electric`. **Provada:** apuntant el denominador a 2023 → `FAIL 1`. Neix el mateix
dia que el fix (regla del rol): aquest bug era invisible precisament perquè cap test el mirava.

---

## Tasca 2 · el sector SERVEIS

### ⛔ Premissa del brief a matisar: JA s'ingeria

`icaen_consum.py` baixa el dataset **sencer** (tots els sectors) des del primer dia, per fidelitat a
la font — el capçal del connector ho diu. El que filtrava `codi_sector = '7'` era la capa transform.
**No hi ha connector nou ni cap crida de xarxa en aquest PR:** el que faltava era exposar-lo.

### El que s'emet

`int_consum_serveis_pc.sql` → `mart_municipi.kwh_serveis_hab`, **mateix any i mateix denominador**
que el domèstic (l'aparellament de la tasca 1), perquè les dues xifres siguin comparables i sumables.

- **Cobertura 2024: 939 de 947.** Els 8 restants surten **NULL, mai zero**: la font els suprimeix
  amb `observacions = 'Dada subjecta a secret estadístic'`. Són 08008 Argençola · 17005 el Far
  d'Empordà · 17070 Fontanilles · 17129 Pedret i Marzà · 25133 Maials · 25913 Riu de Cerdanya ·
  **43109 la Pobla de Mafumet** · 43154 Torroja del Priorat. (La Pobla de Mafumet, 4.187 hab, al
  costat del complex petroquímic de Tarragona: el secret estadístic mossega justament on hi ha la
  instal·lació gran. Frontera honesta declarada, no forat.)
- Per això `kwh_serveis_hab` **no porta `not_null`** al schema, a diferència del domèstic.

### ⛔ El «total» NO surt gratis, i per això no s'emet

El brief deia «deixa preparat el total si surt gratis». **No surt gratis i no s'ha fet.** El dataset
no publica cap fila de total: només 6 sectors (1 PRIMARI · 3 INDUSTRIAL · 4 CONSTRUCCIÓ ·
5 TRANSPORT · 6 SERVEIS · 7 DOMÈSTIC). Sumar-los seria un **mínim observat, no un total**:

> **El 2024 només 46 dels 947 municipis tenen els 6 sectors amb valor.** Als altres **901** en falta
> almenys un, per secret estadístic o perquè la font directament no n'emet la fila. I el que falta
> més sovint és l'**INDUSTRIAL**, que és precisament el sector que pot dominar el total d'un municipi.

Un «total» així seria una xifra que sembla completa i no ho és. El «no» és la resposta.

### Les xifres, i d'on venen les de Bea

| | ponderada (total ÷ hab) | mediana dels 947 |
|---|---|---|
| domèstic | **1.252,11** | **1.538,20** |
| serveis | **1.696,26** (939 munis) | **1.144,80** |
| suma | 2.948,4 | **2.683,0** |

**Les tres xifres de referència de Bea (1.500 / 1.100 / 2.700) són MEDIANES, no ponderades**, i
quadren: 1.538 / 1.145 / 2.683. Val la pena que ho sàpiga en triar quina referència es pinta,
perquè les dues respostes a la mateixa pregunta difereixen un 25 % al domèstic i un 48 % als serveis.

### La preocupació de Bea, mesurada: té raó i el senyal no és turisme

Els 8 municipis amb més serveis per càpita:

| municipi | comarca | padró | domèstic | **serveis** | vidre | index_turisme |
|---|---|---|---|---|---|---|
| Torrent | Baix Empordà | 181 | 6.500 | **21.589** | 114,3 | 100,0 |
| Argelaguer | Garrotxa | 467 | 1.250 | **15.938** | 38,8 | 54,6 |
| Naut Aran | Val d'Aran | 1.893 | 6.900 | **13.590** | 60,4 | 80,6 |
| Gurb | Osona | 2.738 | 1.983 | **13.315** | 33,4 | 48,2 |
| Granyanella | Segarra | 154 | 1.848 | **12.952** | 23,0 | 35,7 |
| Vila-sana | Pla d'Urgell | 754 | 1.576 | **12.024** | 29,0 | 42,9 |
| Abrera | Baix Llobregat | 13.207 | 1.282 | **10.327** | 11,8 | 22,2 |
| la Pobla de Massaluca | Terra Alta | 344 | 1.422 | **10.052** | 29,7 | 43,7 |

Torrent i Naut Aran sí que són turisme (vidre alt, índex 100 i 81). **Gurb, Abrera, Granyanella,
Vila-sana i Argelaguer no**: vidre baix i índex mig-baix, i el que tenen és una instal·lació gran.
La correlació de Spearman de `kwh_serveis_hab` amb els senyals de turisme és **feble**
(vidre +0,22 · RTC/1.000 hab +0,19) i **amb la població és zero (+0,02)**. **297 dels 939 municipis
consumeixen més en serveis que en domèstic.** La hipòtesi del «fals paradís turístic estadístic» es
confirma en dades: separar-los era necessari.

**`kwh_serveis_hab` NO entra a `mart_govern`** en aquest PR (no té rang comarcal). Tres motius, tots
explícits: (a) no és al contracte i el contracte és de Talaia; (b) el front encara no la pinta;
(c) **jo mateix he mesurat que cap referència territorial l'explica** (vegeu la tasca 3) — servir un
rang comarcal amb una referència que he demostrat que és quasi soroll seria vendre una comparació
que no aguanta. La dada viu a `mart_municipi`, llesta.

---

## Tasca 3 · les referències, calculades i servides

`mart_govern` passa de 12 a 20 columnes (les 8.523 files no canvien). Al costat de les
`mediana_comarca` / `mediana_catalunya` de W4 hi ha ara:

### 1 · La PONDERADA (total ÷ habitants) — amb un pes PER MÈTRICA

`ponderada_comarca` · `hab_ponderada_comarca` · `ponderada_catalunya` · `hab_ponderada_catalunya` ·
`pes_ponderada`.

**La decisió que fa que el número sigui el bo:** cada mètrica es pondera pel **seu propi
denominador**, no per `poblacio`. Així la ponderada és *aritmèticament idèntica* al quocient dels
totals — que és com publiquen la xifra l'ARC, l'ICAEN i l'Idescat:

| mètrica | pes | ponderada de Catalunya |
|---|---|---|
| `kg_hab_any` | `poblacio_residus` | **476,8463** |
| `kwh_hab` | `poblacio_kwh` | **1.252,1090** |
| `vidre_hab` | `poblacio_residus` | **22,8890** |
| `pct_noprincipal` | `hab_total` | 23,6459 |
| `index_envelliment` | `pob_0_14` | 148,3589 |
| `rtc_per_1000hab` | `poblacio` | 13,9053 |
| `renda_neta_persona` | `poblacio` | 16.485,38 |
| `pct_nacionalitat_estrangera` | `poblacio` | 18,7459 |
| `poblacio` | **cap** → **NULL** | — |

Les tres de Talaia (476,8 · 1.234,9→**1.252,1** · 22,9) confirmades. `poblacio` surt **NULL amb
`pes_ponderada` NULL**: una població ponderada per la població no és una referència, és una altra
pregunta (la mida del municipi on viu el català mitjà). Forat declarat, no oblidat.

**⚠️ El detall que hauria passat desapercebut:** ponderar-ho tot per `poblacio` dona un número que
s'assembla al bo i no ho és. Al Berguedà, residus: **452,90** amb el pes correcte (`poblacio_residus`)
i **452,41** amb `poblacio` (2025). El **452,4** que hi ha a `next.md` és el segon: **la mateixa
barreja de vintages de la tasca 1 era també dins el número de referència**, en petit. El bo és 452,90.

### 2 · El «500» d'Idescat: la diferència NO és un misteri, és una fila del nostre propi dataset

`next.md` deia «175.768 t que Idescat compta i que no s'atribueixen a cap municipi». **Ho he trobat,
i té nom:** el dataset de l'ARC (`69zu-w48s`) porta una fila amb `codi_municipi = 0`,
`municipi = 'No territorialitzable'`, `comarca = 'NA'`, població 0 i **175.115,55 t** el 2024.

| | tones 2024 | kg/hab (÷ 8.012.231) |
|---|---|---|
| els 947 municipis | 3.820.608,82 | **476,85** |
| «No territorialitzable» | 175.115,55 | +21,86 |
| **total ARC** | **3.995.724,37** | **498,70** |

El titular d'Idescat (~500 kg/hab, 3.996.000 t) **és el total de l'ARC amb la fila no
territorialitzable inclosa**, arrodonit. La discrepància de Talaia (175.768 t) venia d'usar els
3.996.000 arrodonits; la xifra exacta és **175.115,55 t (4,38 %)**.

**Conseqüència, i és la de Talaia:** la referència ha de sortir de la mateixa font i del mateix
perímetre que el numerador (**476,85**). Publicar el 500 al costat de xifres municipals que sumen
476,85 faria semblar **tots** els municipis un 4,4 % millors del que són. Ara ho podem dir amb el
nom de la fila, no com a diferència inexplicada — i això és molt més honest de posar a una targeta.

### 3 · L'ESTRATIFICADA per franja de població

`franja_poblacio` (al nivell del municipi, al JSON) · `mediana_franja` · `n_franja`, amb els talls
de Bea sobre el padró vigent.

**Les sis xifres de Talaia, confirmades exactes** (amb el `kwh_hab` BUGAT: 1.818 · 1.734 · 1.551 ·
1.491 · 1.347 · 1.156). **Amb el vintage arreglat es mouen** i el gradient segueix sent monòton:

| franja | n | **kWh/hab (arreglat)** | kWh/hab (bugat) | residus | vidre | serveis |
|---|---|---|---|---|---|---|
| <250 | 179 | **1.824,2** | 1.818,1 | 554,0 | 38,7 | 1.192,1 |
| 250-499 | 148 | **1.728,2** | 1.734,4 | 479,0 | 35,6 | 1.221,4 |
| 500-999 | 148 | **1.565,6** | 1.551,4 | 427,8 | 30,6 | 1.023,4 |
| 1.000-4.999 | 252 | **1.505,9** | 1.491,1 | 438,0 | 26,2 | 1.065,7 |
| 5.000-19.999 | 149 | **1.364,7** | 1.347,0 | 502,2 | 24,6 | 1.093,7 |
| ≥20.000 | 70 | **1.169,2** | 1.155,8 | 447,2 | 19,2 | 1.433,4 |

### 4 · La pregunta de Talaia: què explica el residu, si no la mida?

Mesurat sobre els 947, **variància explicada ajustada pels graus de llibertat** (perquè `comarca` té
41 grups i `franja` 6: comparar `eta²` cru hauria afavorit la comarca només per tenir més caselles) i
amb **baseline de permutació** (400 remostrejos, quant dona la mateixa partició amb les etiquetes
barrejades):

| | franja (k=6) | tipus_territorial (k=5) | **comarca (k=41)** | atzar |
|---|---|---|---|---|
| **`kg_hab_any`** | **0,040** | **0,133** | **0,331** | 0,005 / 0,043 |
| `kwh_hab` | 0,095 | 0,053 | 0,349 | 0,005 / 0,042 |
| `vidre_hab` | 0,165 | 0,061 | 0,322 | 0,006 / 0,042 |
| `kwh_serveis_hab` | **0,004** | **0,004** | **0,021** | 0,005 / 0,042 (p=0,10 · 0,11 · 0,05) |

**Resposta honesta, en tres trossos:**

1. **Talaia té raó que `tipus_territorial` explica el residu millor que la mida** — 13,3 % contra
   4,0 %, més del triple. La mediana per tipus ho ensenya: `litoral_vacacional` 703,3 kg/hab (n=63)
   contra `metropolita_dens` 418,6 (n=44) i `interior_rural` 464,3 (n=804).
2. **Però ni l'una ni l'altra l'expliquen bé, i la millor que tenim ja la fem servir:** la
   **COMARCA** explica el **33,1 %**, 2,5 vegades més que `tipus_territorial` i 8 vegades més que la
   mida. I la comarca és exactament la partició amb què `mart_govern` ja calcula el rang i la
   `mediana_comarca` de W4. **Recomanació: als residus, la referència que ja hi ha (la mediana
   comarcal) és la millor de què disposem; no cal afegir-hi una de per mida, i pintar-la seria
   convidar a llegir una relació que a les dades no hi és.**
3. **El que de debò explica el residu no és cap estrat, és una variable contínua: la intensitat
   turística.** Spearman de `kg_hab_any` amb `vidre_hab` **+0,53**, amb `index_turisme` **+0,53**,
   amb `rtc_per_1000hab` **+0,53**; amb la població, **−0,10**. La mida no hi és; el turisme sí.
   (Coherent amb el gradient no monòton: la franja 5.000-19.999 puja a 502 kg/hab perquè hi ha les
   viles turístiques mitjanes.)

**I una que ningú havia preguntat:** al **sector SERVEIS no hi ha CAP estratificació territorial que
funcioni**. Franja i tipus donen 0,004 — **estadísticament indistingible de l'atzar** (p = 0,10 i
0,11), i la comarca 0,021 amb p = 0,05. Té tot el sentit: el consum de serveis d'un municipi el fixa
si hi ha o no una instal·lació gran, i això no és territori, és un fet puntual. **Per això
`kwh_serveis_hab` es publica com a xifra crua i sense referència comparativa.**

### El que s'ha servit i el que ha costat

Les vuit columnes noves van **dins la cel·la** (mateixa raó que W4: el prebuild de Mirador parteix el
fitxer per municipi), llevat de `franja_poblacio`, que va **al nivell del municipi** perquè és un
atribut del municipi i repetir-la a les 9 cel·les eren 8 còpies de la mateixa cadena.

**Preu mesurat:** `govern.catalunya.json` **1.595 kB → 3.434 kB** (+115 %). El shard que el navegador
carrega passa d'~1,7 kB a **3,7 kB**. La meitat del creixement són els dos `ponderada_*` sense
arrodonir (18 xifres per número): el mart no arrodoneix a posta i l'exportador **re-serialitza, no
decideix precisió**. `govern.bergueda.json`: 119 → 112 kB (baixa perquè `franja_poblacio` ha sortit
de la cel·la).
**➡️ Handoff a: Talaia + Mirador (no bloqueja).** Si aquest pes molesta, l'alternativa honesta és la
que W4 ja va deixar escrita: un germà `govern-referencies.json` (43 comarques × 9 + Catalunya × 9 +
6 franges × 9 ≈ pocs kB) amb el seu `--check`. Obliga Mirador a una segona petició i per això no
s'ha fet sense parlar-ho.

### ⚠️ Dues referències del mateix número que no diuen ben bé el mateix

`mart_demografia` ja publicava `pct_nacionalitat_estrangera_comarca` / `_catalunya`, i el meu
`ponderada_*` de la mateixa mètrica **no hi coincideix del tot**:

| | mart_demografia | mart_govern (nou) |
|---|---|---|
| Catalunya | 18,74 | 18,7459 |
| Berguedà | 12,69 | 12,7054 |

Dues causes, totes dues petites però reals: (a) `mart_demografia` suma **tots** els municipis
(947 / 31), i la meva ponderada només els que **tenen dada publicable** (938 / 27) — el **mateix
denominador honest que el rang**, que és el que ha d'acompanyar un «6 de 27»; (b) jo pondero
percentatges ja arrodonits a 2 decimals (+0,0003). **Cap de les dues és falsa; responen preguntes
lleugerament diferents.** Ho declaro perquè si una targeta arribés a pintar-les totes dues hi hauria
un 0,013 pp de diferència sense explicació. **➡️ Handoff a: Talaia** (quina mana).

---

## Serrells trobats pel camí (tots dins la meva jurisdicció, tots dits)

### 🩹 `data/marts/mart_consum_electric.parquet` estava ESTALE des de l'escalat a Catalunya

El parquet versionat tenia **372 files (31 municipis del Berguedà)**; el model n'emet **11.364
(947 × 12)** des de F2. El test `assert_mart_consum_electric_grid` ja ho hauria caçat — però **el CI
no corre `dbt build`** (no té `data/raw/`) i aquest mart **no té exportador amb `--check`**. Només ho
veu qui construeix en local, i des de F2 ningú no havia reconstruït aquest model.
Regenerat. *(Lliçó germana de la del rol: una guarda que no s'executa decora.)*

### 🩹 Vermell preexistent al `dbt build`: el topall de `consum_kwh_domestic`

`between 0..1e9`, escrit quan el mart era del Berguedà. Barcelona el supera **cada any** (màxim
observat 2.067.646.878 kWh el 2013) → el test fallava a **12 files** en la primera construcció
neta. Pujat a **5e9** (≈2,4× el màxim observat: segueix sent una guarda de magnitud, no un topall
ajustat a la dada), amb el motiu escrit al costat.

### ✅ Auditades i correctes, no tocades

`kg_hab_any` i `vidre_hab` divideixen per `poblacio_residus`, la població del MATEIX dataset de
l'ARC. Verificat a més que aquesta població **és** el padró oficial de l'any (947/947 idèntica a
l'Idescat). Coherents, com deia el brief.

### ⛔ Premissa del brief falsa (la del sector serveis)

«Sector SERVEIS: no l'ingerim» → **sí que l'ingerim** des del primer dia; el filtre era a transform.

---

## Esmenes de contracte proposades (diff exacte · `semantic/metrics.yml` és de Talaia, NO tocat)

### E-R1 · `kwh_hab` — la fórmula i la data deien 2024 i n'hi havia dos

```diff
     unit: {ca: kWh/hab/any, es: kWh/hab/año}
-    formula: "consum_domestic_kwh / poblacio"
+    formula: "consum_domestic_kwh / poblacio_del_mateix_any"
     source: icaen_consum
     date: "2024"
     table: mart_municipi
     column: kwh_hab
     visibility: public
     synonyms: {ca: [electricitat, consum elèctric, llum], es: [electricidad, consumo eléctrico, luz]}
+    caveat:
+      ca: "Fins al 2026-07-31 aquesta mètrica dividia el consum de 2024 pel padró de 2025 i declarava `date: 2024` sense dir-ho: el consum per habitant de tots els municipis sortia esbiaixat (el ponderat de Catalunya, 1.234,9 en comptes de 1.252,1) i, com que el padró no havia variat igual a tot arreu, l'error per municipi anava de −11,9% a +12,2% i movia el rang comarcal a 438 dels 947. Ara el denominador és el padró del MATEIX any del consum (Idescat, Cens anual de l'INE), i per això NO és el mateix número que el padró que es mostra a la fitxa (2025)."
+      es: "Hasta el 2026-07-31 esta métrica dividía el consumo de 2024 por el padrón de 2025 y declaraba `date: 2024` sin decirlo: el consumo por habitante de todos los municipios salía sesgado (el ponderado de Cataluña, 1.234,9 en vez de 1.252,1) y, como el padrón no había variado igual en todas partes, el error por municipio iba de −11,9% a +12,2% y movía el rango comarcal en 438 de los 947. Ahora el denominador es el padrón del MISMO año del consumo (Idescat, Censo anual del INE), y por eso NO es el mismo número que el padrón que se muestra en la ficha (2025)."
```

### E-R2 · `rtc_per_1000hab` — no declarava `date` (el forat que el brief demanava tapar)

És l'única per càpita pública sense `date`. La seva germana `rtc_per_100hab_viv` ja declara la
barreja; aquesta la té igual (registre VIU llegit com a foto de 2026 ÷ padró 2025) i no la deia.

```diff
     dimension: turisme
     unit: {ca: per mil, es: por mil}
     formula: "rtc_total / poblacio * 1000"
     source: datapoble
+    origin_source: rtc
+    date: "2026/2025"
     table: mart_municipi
     column: rtc_per_1000hab
     visibility: public
     synonyms: {ca: [intensitat turística], es: [intensidad turística]}
+    caveat:
+      ca: "Barreja de vintages declarada: el numerador (RTC) és un registre VIU llegit com a foto del dia de la càrrega (2026) i el denominador és el padró de 2025. On el padró hagi crescut des del 2025, la intensitat surt lleugerament sobreestimada. Fins al 2026-07-31 aquesta mètrica no declarava cap data — era l'única per càpita pública que no ho feia."
+      es: "Mezcla de vintages declarada: el numerador (RTC) es un registro VIVO leído como foto del día de la carga (2026) y el denominador es el padrón de 2025. Donde el padrón haya crecido desde 2025, la intensidad sale ligeramente sobreestimada. Hasta el 2026-07-31 esta métrica no declaraba ninguna fecha — era la única per cápita pública que no lo hacía."
```

### E-R3 · `kwh_serveis_hab` — entrada NOVA (a col·locar just després de `kwh_hab`)

```yaml
  kwh_serveis_hab:
    label: {ca: Elèctric de serveis kWh/hab, es: Eléctrico de servicios kWh/hab}
    definicio:
      ca: "Consum elèctric del sector SERVEIS per habitant empadronat, mateix any i mateix denominador que l'elèctric domèstic (dada oficial ICAEN, sector 6). Es publica SEPARAT del domèstic perquè mesura una altra cosa: l'activitat econòmica de serveis del municipi, no la presència residencial."
      es: "Consumo eléctrico del sector SERVICIOS por habitante empadronado, mismo año y mismo denominador que el eléctrico doméstico (dato oficial ICAEN, sector 6). Se publica SEPARADO del doméstico porque mide otra cosa: la actividad económica de servicios del municipio, no la presencia residencial."
    dimension: pressio
    unit: {ca: kWh/hab/any, es: kWh/hab/año}
    formula: "consum_serveis_kwh / poblacio_del_mateix_any"
    source: icaen_consum
    date: "2024"
    table: mart_municipi
    column: kwh_serveis_hab
    visibility: public
    synonyms: {ca: [serveis, activitat econòmica, polígon], es: [servicios, actividad económica, polígono]}
    caveat:
      ca: "Cobertura 939 de 947: a 8 municipis la font suprimeix la xifra per secret estadístic i aquí surt buida, mai zero («no publicat» ≠ «no consumeix»); un d'ells és la Pobla de Mafumet, al costat del complex petroquímic. NO és un indicador de turisme: mesurat sobre els 947, la seva correlació amb els senyals turístics és feble (Spearman +0,22 amb el vidre) i amb la població és zero. Una sola instal·lació gran —un polígon, una cimentera, una depuradora— pot fer-la disparar en un municipi petit, i per això es publica com a xifra crua i SENSE referència comparativa: cap estratificació territorial que tinguem l'explica (franja de població i tipus territorial expliquen el 0,4% de la seva variància, indistingible de l'atzar)."
      es: "Cobertura 939 de 947: en 8 municipios la fuente suprime la cifra por secreto estadístico y aquí sale vacía, nunca cero («no publicado» ≠ «no consume»); uno de ellos es la Pobla de Mafumet, junto al complejo petroquímico. NO es un indicador de turismo: medido sobre los 947, su correlación con las señales turísticas es débil (Spearman +0,22 con el vidrio) y con la población es cero. Una sola instalación grande —un polígono, una cementera, una depuradora— puede dispararla en un municipio pequeño, y por eso se publica como cifra cruda y SIN referencia comparativa: ninguna estratificación territorial que tengamos la explica (franja de población y tipo territorial explican el 0,4% de su varianza, indistinguible del azar)."
```

### E-R4 · bloc de doctrina de les REFERÈNCIES (ampliació del bloc W4 del capçal)

Per enganxar **just després** del bloc «VALOR DE REFERÈNCIA (W4…)» que W4 va proposar:

```yaml
# REFERÈNCIES, LES TRES (R-REFERENCIA, 2026-07-31; recerca de Bea, dada emesa per Sondeig a
# mart_govern). Una targeta de rang pot mostrar TRES referències diferents i NO diuen el mateix:
#   · MEDIANA (comarcal o catalana, W4) — «com és un municipi típic». Cada municipi hi pesa igual:
#     Sant Jaume de Frontanyà (25 hab) tant com Barcelona (1,7 M).
#   · PONDERADA (`ponderada_comarca` / `ponderada_catalunya`) — «quant li toca a cada habitant».
#     És TOTAL ÷ HABITANTS, l'equivalent exacte de com publiquen la xifra l'ARC, l'ICAEN i
#     l'Idescat, i per tant el número que un lector entén per «la mitjana de Catalunya».
#     REGLA VINCULANT: cada mètrica es pondera pel SEU PROPI DENOMINADOR (`pes_ponderada`:
#     pct_noprincipal per hab_total, index_envelliment per pob_0_14, kg_hab_any i vidre_hab per
#     poblacio_residus, kwh_hab per poblacio_kwh). Ponderar-ho tot per `poblacio` dona un número
#     que s'assembla al bo i no ho és (Berguedà, residus: 452,90 correcte vs 452,41).
#     `poblacio` NO en té i surt NULL: no és un forat, és que la pregunta no existeix.
#   · ESTRATIFICADA (`mediana_franja`) — «com són els municipis de la meva mida».
#
# REGLA VINCULANT · LA REFERÈNCIA SURT DE LA MATEIXA FONT I DEL MATEIX PERÍMETRE QUE EL NUMERADOR.
#   Cas fundacional: el titular d'Idescat de residus per a Catalunya és ~500 kg/hab i la taula
#   municipal de l'ARC en suma 476,85. No es contradiuen: el dataset de l'ARC porta una fila
#   `No territorialitzable` amb 175.115,55 t el 2024 (4,4%), residus reals que no s'atribueixen a
#   cap municipi; amb ella el total fa 498,70. Posar el 500 al costat de xifres municipals que
#   sumen 476,85 faria semblar TOTS els municipis un 4,4% millors del que són.
#
# ⚠️ L'ESTRATIFICADA PER MIDA NO SERVEIX PER A TOT, i el contracte ho ha de dir perquè la dada
#   se serveix per a les nou mètriques. Variància explicada ajustada, mesurada sobre els 947
#   (bitàcola 2026-07-31): la franja de població explica el 16,5% del vidre i el 9,5% del consum
#   elèctric —gradients monòtons i defensables— però NOMÉS EL 4,0% dels residus, on el gradient
#   ni tan sols és monòton (554 → 479 → 428 → 438 → 502 → 447). Als residus el que explica més
#   és la COMARCA (33,1%), que és la partició que el rang i la mediana comarcal ja fan servir; i
#   el millor predictor no és cap estrat sinó una contínua, la intensitat turística
#   (Spearman +0,53 amb vidre_hab, amb index_turisme i amb rtc_per_1000hab; −0,10 amb la població).
#   Al sector serveis no funciona CAP estratificació (0,4%, indistingible de l'atzar).
#
# PROCEDÈNCIA OBLIGATÒRIA (C6 §8.1): una mediana es diu «sobre n MUNICIPIS» (`n_amb_dada` /
#   `n_mediana_catalunya` / `n_franja`); una ponderada, «sobre n HABITANTS» (`hab_ponderada_*`).
#   Cap de les tres es pot pintar sense el seu denominador.
#
# PROHIBICIÓ EXPLÍCITA (ampliada): cap referència pot ser una constant del MODEL DE PERNOCTA
#   APARCAT — base_residencial 410 · base_electric 1224 · base_vidre 26,5 · base_comarcal 452
#   (dbt_project.yml). La quarta hi entra el 2026-07-31 perquè la ponderada comarcal de residus
#   del Berguedà mesura 452,90, a mig punt d'ella: és una MESURA nova, no la constant, però la
#   guarda de verify_govern.py ho comprova a cada CI sobre TOTES les referències, no només sobre
#   la mediana catalana.
```

### E-R5 · secundàries, no urgents (les deixo dites, no proposo diff)

- `restauracio_per_1000hab` i `serveis_per_1000hab` declaren `date: "2026"` i el seu denominador és
  el padró de 2025 → serien `"2026/2025"`. Són Berguedà-only i el numerador és OSM («mínim
  observat»), així que la barreja hi pesa menys que el caveat que ja porten.
- La capa L2 del model aparcat (`carrega_total_est` i família) fa `poblacio(2025) × kg_hab_any(2024)`.
  El contracte ja ho declara amb `date: "2024/2025"`. No tocat.

---

## Verificació LOCAL (el CI per-PR també corre; això és el que he passat aquí)

- **`dbt build --select +mart_municipi +mart_govern +mart_consum_electric`** — **115 PASS, 0 ERROR**
  (n'eren 108 abans; 7 tests nous de les columnes noves + la guarda del vintage).
- **`verify_govern.py` — OK**: 8.523 files (947×9), 43 comarques, 30 sense dada amb rang NULL honest,
  7 àncores de rang a mà byte-match, Gombrèn contra els 19 del Ripollès, medianes W4 amb **igualtat
  exacta** (387 grups comarcals + 9 catalans, 6 àncores), **ponderades recalculades amb el pes propi
  de cada mètrica** (rtol 1e-12, 3 àncores) i **estratificada per 6 franges amb igualtat exacta**;
  cap referència coincidint amb les quatre bases aparcades.
- `verify_marts` · `verify_tendencia` (20.802 files, 1.894 Δ a mà) · `verify_pols_mensual`
  (224.439 files) · `verify_contracte` (61 mètriques) — **OK**.
- `dbt parse` — OK. `ruff check packages/transform packages/ingestion packages/signals` — **net**.
- Tots els `--check`: `derive_fase1` · `validacio_etca` · `tipus_territorial` · `calibracio_intervals`
  · `export_pernocta_catalunya` · `discrepancia_etca_pernocta` · `senyal_sub1000` ·
  `export_licitacions` · `export_web_municipis` (catalunya + bergueda) · **`export_govern_web`** ·
  `export_tauler_web` — **tots OK**.
- `pytest tools/tests` 5/5 · `pytest packages/signals/tests` 182/182 ·
  `pytest packages/ingestion/tests/{test_atur_sepe,test_idescat_emex}.py` **21/21**.
- **Guardes de Mirador sobre la dada nova** — `node packages/web/scripts/verify-govern.mjs` **OK**
  (947 munis amb rang, paritat dataset↔mart a la Pobla, Barcelona amb el rang del Barcelonès) i
  `verify-docs.mjs` **OK**. `packages/web/` **no s'ha tocat** (`git status` net).

### Guardes noves, provades EN NEGATIU (12/12 peten amb el missatge correcte)

| Mutació injectada | Missatge |
|---|---|
| `ponderada_catalunya` de `kwh_hab` = 1.234,86 (el valor bugat) | `ponderada_catalunya ≠ ponderada recalculada a 947 files` |
| `ponderada_comarca` × 1,000001 (1e-6 relatiu) | `≠ ponderada recalculada a 7576 files` |
| `hab_ponderada_catalunya` +1 habitant | `≠ suma recalculada dels habitants amb dada` |
| residus ponderats per `poblacio` i no pel seu pes | `pes_ponderada de kg_hab_any: esperava {'poblacio_residus'}, tinc {'poblacio'}` |
| franja de la Pobla falsejada | `franja_poblacio ≠ franja recalculada dels talls declarats` |
| `mediana_franja` del vidre = 26,5 (base aparcada) | guarda del model aparcat |
| `ponderada_comarca` de residus = 452 (`base_comarcal`) | guarda de la quarta constant aparcada |
| `n_franja` fals | `≠ recompte real de valors no nuls per (mètrica, franja)` |
| columna `ponderada_catalunya` absent | esquema, abans de cap KeyError |
| columna `mediana_franja` absent (exportador) | `el mart no porta les columnes de referència` |
| `poblacio` amb ponderada fabricada (havia de ser NULL) | `el patró de NULL no coincideix amb el recalculat` |
| padró del denominador apuntat a 2023 (dbt) | `assert_consum_electric_vintage` → `FAIL 1` |

---

## Com s'ha regenerat el parquet

`data/raw/` és gitignored (no hi ha `dbt build` possible en un checkout net), així que en aquest
arbre s'hi ha muntat una **unió de directori de només lectura** cap a la `data/raw/` de l'arbre
principal — cap fitxer versionat en sap res i `git status` no la veu. Amb això,
`dbt build --select +mart_municipi +mart_govern +mart_consum_electric` reconstrueix els tres marts
amb els seus propis `post_hook` (`COPY … FORMAT PARQUET`), no amb `pandas.to_parquet`.

**Abans de tocar res**, la reconstrucció **sense cap canvi** reprodueix `mart_municipi.parquet`
committejat **valor a valor** (`DataFrame.equals` → True, 947×55): és la condició prèvia per poder
atribuir al canvi tot el que després es mogui. `mart_demografia.parquet` es reconstrueix idèntic en
contingut però amb bytes diferents (metadata del motor) → **restaurat**, per no embrutar el diff amb
soroll sense canvi de dada.

## Regla dura del worktree

**Cap `pip install -e` en aquest arbre.** Els tests d'ingestió sí que importen el paquet editable:
sonda feta abans de creure'm cap verd —
el `__file__` de `datapoble_ingestion` apunta al `packages/ingestion/` **d'aquest worktree** (no al
d'un altre agent, com va passar dues vegades), i llavors 21/21. Les sondes pròpies (`verify_govern`, `export_govern_web`, `tauler_kpis`) resolen les
rutes des del propi fitxer i no depenen de cap instal·lació.

**Lliurament:** PR `sondeig/r-referencia` → `main`. **No fusiono jo.**
