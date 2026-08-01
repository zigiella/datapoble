# 2026-08-01 · Retirat el llindar mínim N de la capa origen — Sondeig

**Branca:** `sondeig/retira-llindar-origen` · **Decisió:** vot de Bea (2026-08-01), doctrina ja
escrita al capçal de `semantic/metrics.yml`, bloc «LLINDAR MINIM N DE LA CAPA ORIGEN: RETIRAT».
**No fusiono jo.**

> ⚠️ **AQUEST PR NO POT ANAR VERD TOT SOL.** Dues guardes cauen, i les dues estan FORA de la
> meva jurisdicció. No és un descuit: totes dues són guardes que es van escriure precisament
> perquè caiguessin el dia que el llindar es mogués. Detall exacte i diffs al §6.

---

## 1 · La comprovació pròpia: la font no calla res (i la matisació que hi falta)

El brief demanava verificar el número que va tancar la decisió. **Confirmat, i mesurat aquí**
(`stg_demografia_origen`, 947 files):

| què | files sense dada |
|---|---|
| `nac_estrangera` (el recompte d'estrangers) | **0 de 947** |
| `pob_nac_total` (el denominador) | **0 de 947** |
| `nascuda_estranger` | 0 de 947 |
| `pob_lloc_naix_total` | 0 de 947 |

La Quar (08177): **7 persones amb nacionalitat estrangera sobre 44 habitants** → 7/44 = **15,91 %**
(recalculat a mà). Fígols: 5/41 = **12,20 %**. Les dues xifres d'entrada són públiques a Idescat;
la divisió també ho és ara.

**⚠️ MATISACIÓ HONESTA QUE EL BRIEF NO PORTA, i que importa.** «La FONT no suprimeix res» és cert
del **producte que fem servir per al nivell** (EMEX, la foto del Cens anual) i **fals d'un producte
germà del mateix organisme**: la **sèrie anual de població estrangera** (`stg_demografia_estrangera_serie`,
la que dona el delta) **sí que reserva municipis**, cada any:

| any | municipis sense recompte a la SÈRIE |
|---|---|
| 2021 | 54 de 947 |
| 2022 | 48 |
| 2023 | 41 |
| 2024 | 34 |
| 2025 | **36** |

I a **16 municipis** els la reserva **tots cinc anys** → no tenen finestra, ni curta. Per això hi ha
municipis amb **nivell publicat i sense delta**, i això és el que toca: on la font calla, callem.
La frase precisa és «la font publica la FOTO dels 947 i reserva la SÈRIE d'alguns», no «la font no
calla res». Ho deixo escrit al capçal de `mart_demografia.sql`.

## 2 · Retirat el llindar (`mart_demografia.sql`)

`pct_nacionalitat_estrangera`, `pct_nascuda_estranger` i `bretxa_naturalitzacio` deixen de passar
per `case when supera_min_n`. Es publiquen sempre que hi hagi numerador i denominador.

| | abans | després |
|---|---|---|
| `pct_nacionalitat_estrangera` NULL | 9 | **0** |
| `pct_nascuda_estranger` NULL | 9 | **0** |
| `bretxa_naturalitzacio` NULL | 9 | **0** |
| `confianca_origen` = baixa / mitjana / alta | 9 / 197 / 741 | **9 / 197 / 741** (idèntic) |

**`confianca_origen = 'baixa'` es manté exactament on tocava**, els mateixos 9 municipis. La var
`demografia_min_n = 50` **no desapareix**: sobreviu com a bandera de precisió, que és per al que
serveix. Marcar no és suprimir — i ara la bandera és l'únic senyal de precisió que queda a la capa,
així que passa de dir «a més, t'he suprimit el percentatge» a dir «te'l dono, llegeix-lo amb aquesta
precaució».

Els nou municipis que guanyen percentatge:

| municipi | comarca | hab | estr. | % nac. | % nascuts fora | rang a la comarca |
|---|---|---|---|---|---|---|
| **la Quar** | Berguedà | 44 | 7 | **15,91** | 13,64 | **2 de 31** |
| Fígols | Berguedà | 41 | 5 | 12,20 | 14,63 | 4 de 31 |
| Senan | Conca de Barberà | 47 | 4 | 8,51 | 10,64 | 13 de 22 |
| Cava | Alt Urgell | 38 | 3 | 7,89 | 5,26 | 14 de 19 |
| Forès | Conca de Barberà | 39 | 2 | 5,13 | 7,69 | 18 de 22 |
| la Febró | Baix Camp | 35 | 2 | 5,71 | 5,71 | 23 de 28 |
| Savallà del Comtat | Conca de Barberà | 49 | 0 | 0,00 | 6,12 | 21 de 22 |
| Gisclareny | Berguedà | 28 | 0 | 0,00 | 0,00 | 29 de 31 |
| Sant Jaume de Frontanyà | Berguedà | 25 | 0 | 0,00 | 8,00 | 29 de 31 |

La Quar és la **2a del Berguedà**, com Bea deia. El llindar la pintava com si no existís.

## 3 · Rang i medianes — QUANTS canvien

**52 municipis canvien de rang** a `pct_nacionalitat_estrangera` (cap altra de les 9 mètriques de
`mart_govern` es mou ni un dígit: 0 files):

* **9** hi entren de nou (no en tenien).
* **43** ja hi eren i **baixen 1 o 2 posicions** (15 baixen 1, 28 baixen 2). Desplaçament màxim: 2.
* **Cap comarca canvia de número 1.** (Contrast amb el vintage de `kwh_hab`, que en va moure 5 i
  438 rangs: aquest canvi és molt més contingut, i és honest dir-ho.)

**100 municipis canvien de denominador** (`n_amb_dada`) — les 4 comarques amb algun micromunicipi:

| comarca | n_amb_dada abans → després |
|---|---|
| Berguedà | 27 → **31** |
| Baix Camp | 27 → 28 |
| Conca de Barberà | 19 → 22 |
| Alt Urgell | 18 → 19 |

**La Pobla de Lillet passa de «6 de 27» a «8 de 31»** (hi entren per damunt seu la Quar i Fígols).
L'àncora de `verify_govern.py` s'ha reescrit **amb el motiu al costat**, com es va fer amb les dues
de `kwh_hab`: una àncora que es canvia sense dir per què deixa de ser una àncora.

**Medianes i ponderades — el canvi és el que s'esperava, i on NO es mou també s'ha comprovat:**

| referència | abans | després |
|---|---|---|
| mediana de Catalunya | 10,58 (n=938) | **10,51 (n=947)** |
| ponderada de Catalunya | 18,745896 | 18,745381 |
| mediana del Berguedà | 5,74 | **5,74 (no es mou)** |
| mediana de l'Alt Urgell | 12,485 | 12,390 |
| mediana del Baix Camp | 12,330 | 11,990 |
| mediana de la Conca de Barberà | 11,430 | **9,325** |
| mediana de la franja <250 hab | 6,70 (n=171) | 6,44 (n=180) |

**Per què el Berguedà NO es mou i no és una sorpresa** (recalculat a mà): amb 27 valors la mediana
és el 14è; els 4 que hi entren són 0,00 · 0,00 · 12,20 · 15,91 — **dos per sota i dos per damunt**,
així que amb 31 valors el 16è és el mateix element. La Conca de Barberà és la que més es mou
(11,43 → 9,33) perquè hi entren tres municipis i un d'ells és un 0,00.

## 4 · El delta torna sol — i la guarda es queda

**La incoherència D-DELTA ha desaparegut per si sola, i està mesurada:** files amb `valor_actual`
NULL i `delta` publicat: **4 abans (Fígols, la Quar, Forès, Senan — totes de
`pct_nacionalitat_estrangera`), 0 després.** La Quar ja no diu «n. d. ↑ +1,62 punts»: diu
**15,91 % · ↑ +1,62 punts · 2021→2025**, amb el valor anterior (14,29) al darrere.

**La guarda de la regla s'ha escrit igualment** (`verify_tendencia.py`, §2b), perquè la doctrina del
contracte segueix vigent per a la resta de casos i perquè aquesta incoherència **va viure dotze dies
sense que res petés**. Provada EN NEGATIU. Un detall que calia afinar: **l'atur emmascarat també
porta `valor_actual` NULL** (doctrina del «<5»), però allà el nivell SÍ que es publica —com a
interval [1,4]— i el que s'emet és `delta_min`/`delta_max`, mai un `delta` exacte. Un nivell
publicat en interval no és un nivell suprimit: la guarda mira el **delta exacte**, i amb la
condició ingènua hauria marcat **278 files legítimes** d'atur emmascarat (files amb `valor_actual`
NULL i interval; amb delta exacte n'hi ha **0**).

### 4b · ⛔ Un forat que el brief no preveia i que la retirada del llindar posa a la vista

`mart_tendencia` **no tenia cap fila** de `pct_nacionalitat_estrangera` ni de
`poblacio_nacionalitat_estrangera` per als **16 municipis** on la font reserva la sèrie sencera:
`origen_out` filtrava `where serie_any_inicial is not null` i els deixava **absents**, no
`sense_serie`. Al shard de Gisclareny (08093) la clau directament no hi era.

Això és exactament l'antipatró que la doctrina prohibeix («una fila que falta és invisible; un motiu
es pot llegir»), i **es veia poc mentre el llindar també els amagava el nivell**. Retirat el llindar,
el resultat hauria estat publicar el nivell i callar l'evolució **sense dir-ho**. Corregit:

* `mart_tendencia.sql` · CTE nova `sense_origen_serie`: els 16 surten amb `estat: 'sense_serie'`,
  el **nivell servit** i el motiu escrit **en ca i es**, sense atribuir a la font cap raó que no
  hagi declarat («la reserva pel secret estadístic»; no diem per què).
* `verify_tendencia.py` · **guarda nova 1c: cap targeta sense fila PER MUNICIPI.** La guarda de D10
  comprovava que cada mètrica pintada té *alguna* fila; això deixava passar 931 de 947. Ara el
  conjunt del front (`kpis.js`) es creua amb els 947. Provada en negatiu.
* `SERIE_PARCIAL` declarat: `pct_nacionalitat_estrangera` i `poblacio_nacionalitat_estrangera` són
  les úniques mètriques amb els **dos estats alhora**, i és honest que ho siguin — la cobertura de
  la font varia per municipi i no ho pot decidir una llista nostra. Cap altra mètrica pot dur els
  dos estats sense declarar-se: també hi ha guarda.

`mart_tendencia`: 20.802 → **20.834 files** (+32 = 16 municipis × 2 mètriques).

## 5 · ⛔ SERRELL GROS TROBAT: el tauler servia un `kwh_hab` que la fitxa desmenteix

Regenerant `mart_tendencia.parquet` ha sortit que **estava ESTALE des de R-REFERENCIA**. La seva
darrera regeneració és `b806b29` (V3-DADES, 30/07); el fix del vintage de `kwh_hab` és `72a513b`
(R-REFERENCIA, 31/07) i **ningú va tornar a construir aquest mart**. El CI no corre `dbt build` i
aquest parquet no té `--check`: **el mateix forat que ja va mossegar amb `mart_consum_electric`.**

**La prova, número a número:** el `kwh_hab` del `mart_tendencia.parquet` versionat coincidia amb el
de `mart_municipi.parquet` (que sí que porta el fix) en **30 dels 947**. Regenerat: **947 de 947**.
O sigui que **el web publicava dos números diferents per a la MATEIXA mètrica del MATEIX municipi**
— el de la fitxa i el del tauler — a 917 municipis. La deriva va de **−11,88 % a +12,24 %** i **301
municipis anaven en direcció contrària** (exactament les xifres que R-REFERENCIA va documentar).

Per això el diff és de 932 fitxers: **917 dels 920 shards del tauler canvien pel `kwh_hab` estale**
(900 canvien NOMÉS per això) i només **20 pel canvi d'origen**. No he separat els dos canvis en dos
PR perquè no es poden separar: surten del mateix `dbt build`, i deixar-ne un a mitges tornaria a
versionar un mart estale.

**➡️ Candidata (meva, no urgent):** `mart_tendencia.parquet` i `mart_govern.parquet` no tenen
`--check` propi al CI. Els seus **derivats** (JSON del web) sí, i per això la deriva es va poder
quedar consistent-amb-ella-mateixa i incoherent amb la resta del lloc. Una guarda barata:
recalcular al verificador el `kwh_hab` de `mart_tendencia` contra `mart_municipi` i caure si
divergeixen (és el pont entre dues jurisdiccions de dada, que és on ja hem sagnat dues vegades).

## 6 · 🔴 Les dues guardes que cauen (les dues fora de la meva jurisdicció)

### 6a · `semantic/verify_contracte.py` (job **data**) — 2 errors · **Talaia**

El caveat de `pct_nacionalitat_estrangera` i el de `bretxa_naturalitzacio` **afirmen un recompte amb
xifres**, i la guarda E7a els el compta a la dada. Amb el perímetre nou: la bretxa negativa passa de
**37 de 938** a **39 de 947** (les dues noves: la Quar −2,27 i Cava −2,63). El pitjor cas segueix
sent Tornabous (27,42 vs 24,76). **La guarda fa exactament la seva feina.**

**Diff EXACTE (4 cadenes, cap altre canvi):**

```diff
   pct_nacionalitat_estrangera:
     caveat:
-      ca: "... però NO sempre: a 37 dels 938 municipis amb dada la supera (pitjor cas Tornabous...
+      ca: "... però NO sempre: a 39 dels 947 municipis amb dada la supera (pitjor cas Tornabous...
-      es: "... pero NO siempre: en 37 de los 938 municipios con dato lo supera (peor caso Tornabous...
+      es: "... pero NO siempre: en 39 de los 947 municipios con dato lo supera (peor caso Tornabous...

   bretxa_naturalitzacio:
     caveat:
-      ca: "... passa a 37 dels 938 municipis amb dada, quan hi ha més passaports estrangers...
+      ca: "... passa a 39 dels 947 municipis amb dada, quan hi ha més passaports estrangers...
-      es: "... ocurre en 37 de los 938 municipios con dato, cuando hay más pasaportes extranjeros...
+      es: "... ocurre en 39 de los 947 municipios con dato, cuando hay más pasaportes extranjeros...
```

(Només canvien els dos números a cada cadena: `37`→`39` i `938`→`947`.)

### 6b · `npm run verify:govern` (job **web**) — 12 errors · **Mirador**

Corregut en local contra la dada nova. **Cap error és un bug: totes són la guarda que Mirador va
escriure perquè caigués el dia que el llindar es mogués**, i el comentari del fitxer ho diu
literalment («cau per obligar a REESCRIURE la frase, no per castigar la millora»).

```
[x] 25071/43057/43061/43143/43146/08080/08093/08177/08216 amb % de nacionalitat i només N hab:
    el llindar declarat no s'estaria aplicant                                        (9 errors)
[x] la Quar (08177) hauria de tenir el PERCENTATGE suprimit pel llindar mínim N
[x] la nacionalitat de la Pobla hauria de ser «de 27» (4 munis sota el llindar)
[x] s'esperaven 30 municipis sense dada a tot Catalunya i n'hi ha 21
```

**El que li toca a Mirador** (no ho toco: `packages/web/` és seu):

1. `GOVERN_DENOM_REASON` (`kpis.js`): **`pct_nacionalitat_estrangera` i `pct_nascuda_estranger`
   ja no tenen forats** → surten del mapa. El motiu `gov_denom_minn` es queda **sense cap mètrica**;
   si no queda cap causa «llindar nostre» viva, la clau i18n i `GOVERN_DENOM_MIN_N` es poden retirar
   (i llavors la lectura de `demografia_min_n` del transform també, perquè la var segueix existint
   però **ja no suprimeix res**: llegir-la per explicar una supressió seria explicar el que no passa).
2. `verify-govern.mjs` §(b)/(c): la guarda del llindar i la de «cap muni <50 amb %» s'han de retirar
   o invertir; l'expectativa dels **30 municipis sense dada** passa a **21** (les tres causes vives
   són ara renda (20) i l'envelliment de la Febró (1); la causa «llindar nostre» desapareix).
3. **Copy:** la Quar deixa de necessitar el «No vol dir zero» — ara hi ha el número. I la guarda que
   deia «mentre no se serveixi el recompte, el text no el pot prometre» **segueix vigent**: el
   recompte encara NO és al catàleg servit (§7).

`npm run check` (0 errors, 1.298 fitxers) i `npm run verify:docs` **passen** amb la dada nova.

## 7 · El recompte al catàleg web: BLOQUEJAT pel contracte, amb el diff a punt

**⛔ PREMISSA DEL BRIEF, PARCIALMENT FALSA — i en el sentit bo.** El brief diu que
`poblacio_nacionalitat_estrangera` «no arriba a `data/web/municipis.*.json`»: **cert**. Però la
frase que arrossega de `next.md` («no és al contracte servit **ni a cap dataset del web**», «a la
fitxa de la Quar no hi ha CAP xifra de nacionalitat») **és falsa**: el recompte **ja se serveix**
als 947 shards del tauler (`data/web/tauler/08177.json` → `poblacio_nacionalitat_estrangera`,
`valor_actual: 7`, període 2021→2025) des de D7. El que passa és que **el front no el pinta**
(no és a `kpis.js`).

**Auditoria de TOTS els recomptes de la dimensió `origen`** (que era la pregunta del brief):

| columna de `mart_demografia` | al contracte | a `municipis.*.json` | als shards del tauler |
|---|---|---|---|
| `poblacio` | sí | sí | sí |
| `poblacio_nascuda_catalunya` | sí | sí | sí |
| `poblacio_nascuda_resta_espanya` | sí | sí | sí |
| `poblacio_nascuda_estranger` | sí | sí | sí |
| **`poblacio_nacionalitat_estrangera`** | **NO** | **NO** | **sí** |
| `delta_estrangers_finestra` | NO | NO | sí (com a delta de l'anterior) |

**És l'ÚNIC que falta**, i n'hi ha prou amb una entrada. **La segona meitat del forat és pitjor que
la primera:** avui se serveix al web una xifra **que no és al contracte** — sense etiqueta, sense
font i sense data pròpies. Això és el que la regla de ferro de Bea (C6 §8.1) existeix per impedir.

**No puc servir-lo aquest PR:** `tools/export_web_municipis.py` construeix el catàleg del contracte
(`raw[key]`) i sense entrada peta. I `semantic/metrics.yml` és de Talaia i el brief demana no
tocar-lo. Aquí va el diff exacte; **el dia que entri, el meu costat són 3 línies** i les deixo
escrites també.

**Diff EXACTE per a `semantic/metrics.yml`** — entrada nova, just ABANS de `pct_nacionalitat_estrangera`
(mirall de `poblacio_nascuda_estranger`):

```yaml
  poblacio_nacionalitat_estrangera:
    label: {ca: Població amb nacionalitat estrangera, es: Población con nacionalidad extranjera}
    definicio:
      ca: "Nombre de persones empadronades amb passaport no espanyol. És situació administrativa, NO lloc de naixement: qui es naturalitza surt d'aquest recompte sense moure's de casa."
      es: "Número de personas empadronadas con pasaporte no español. Es situación administrativa, NO lugar de nacimiento: quien se naturaliza sale de este recuento sin moverse de casa."
    dimension: origen
    unit: {ca: habitants, es: habitantes}
    formula: directe
    source: idescat_emex
    date: "2025"
    table: mart_demografia
    column: poblacio_nacionalitat_estrangera
    visibility: public
    caveat:
      ca: "És el NUMERADOR del % de nacionalitat estrangera, i es publica per als 947 municipis: la font el dona sencer. Als pobles petits val més llegir-lo que llegir el percentatge (7 persones de 44 diu més que «15,91 %»). Lectura ECOLÒGICA, mai individual."
      es: "Es el NUMERADOR del % de nacionalidad extranjera, y se publica para los 947 municipios: la fuente lo da entero. En los pueblos pequeños vale más leerlo que leer el porcentaje (7 personas de 44 dice más que «15,91 %»). Lectura ECOLÓGICA, nunca individual."
```

**El meu costat, a `tools/export_web_municipis.py`** (a punt, no aplicat):

```diff
   "poblacio_nascuda_estranger", "pct_nascuda_estranger",
-  "pct_nacionalitat_estrangera", "bretxa_naturalitzacio",
+  "poblacio_nacionalitat_estrangera", "pct_nacionalitat_estrangera", "bretxa_naturalitzacio",

   "poblacio_nascuda_estranger": "integer", "pct_nascuda_estranger": "percent",
+  "poblacio_nacionalitat_estrangera": "integer",

   "poblacio_nascuda_estranger": "poblacio_nascuda_estranger",
+  "poblacio_nacionalitat_estrangera": "poblacio_nacionalitat_estrangera",
```

## 8 · 💡 Trobat i NO tocat: 14 deltes sobre una finestra de zero anys

`int_demografia_deltes` calcula la finestra entre el primer i l'últim any **amb dada**. A **14
municipis** només hi ha **un** any amb dada, així que la finestra és `2025→2025` (o `2021→2021`…) i
el delta surt **0,00 amb `direccio: 'igual'`**. Senan (43146) n'és un, i ara que té nivell publicat
la seva targeta diria **«= 0,00 punts · 2025→2025»**.

No és fals —el període hi és declarat i el lector el pot veure— però un zero que vol dir «només en
tenim un punt» s'assembla massa a un zero que vol dir «no ha canviat», i aquesta distinció és la que
aquest projecte defensa. **No ho toco**: cap regla escrita ho prohibeix avui, la solució passa per
un motiu nou en dos idiomes, i decidir si una finestra d'un sol punt és una sèrie és doctrina.
**➡️ Handoff a: Talaia (doctrina)** — amb la meva recomanació: que `serie_n_anys = 0` no faci sèrie
i surti `sense_serie` amb motiu, com els 16 del §4b. Els 14: `25060 08130 43039 43146 08225 43072
25153 25154 08152 43158 25075 25124 08050 08095`.

## 9 · ⛔ Trobat i NO tocat: `mart_electoral.parquet` versionat és estale i el model n'emet 947

Reconstruint els marts, `mart_electoral.parquet` ha passat de **31 files a 947**: el parquet
versionat és de `01e16ef` (època del pilot) i el model ja cobreix tota Catalunya. **L'he restaurat
i NO el committejo.** Publicar la capa de vot dels 947 en un repo públic és una decisió editorial
—política editorial de la capa electoral = **Bea**, jurisdicció = **Talaia**—, no un efecte lateral
d'un `dbt build` meu. Les guardes anti-fuita dels exports segueixen verdes (5/5) perquè cap export
web el llegeix; l'únic consumidor és `tools/export_bergueda_bundle.py`, que no corre al CI.
**➡️ Handoff a: Talaia + Bea.**

## 10 · Verificació

**LOCAL, job `data` sencer:**

* `dbt build` **165/165** (8 taules, 137 tests, 19 vistes)
* `ruff` net · `dbt parse` OK
* `verify_tendencia.py` **OK** — 20.834 files, 947 municipis, 1.894 deltes d'atur recalculats a mà
  byte-match, cap fletxa sense període
* `verify_govern.py` **OK** — 8.523 files, 7 àncores de rang a mà, medianes i ponderades recalculades
* `verify_marts.py` · `verify_pols_mensual.py` OK
* Tots els `--check` verds: municipis (947 + 31), govern (947 + 31), tauler (31 + 947 shards),
  fase 1, ETCA, tipus territorial, calibració, pernocta, discrepància, senyal <1000, licitacions
* `pytest` ingestió 21/21 (**PYTHONPATH cap al MEU arbre, verificat al `__file__`**; mai `pip
  install -e` al worktree) · signals 182/182 · antifuita electoral 5/5
* ❌ `semantic/verify_contracte.py` — 2 errors, §6a (contracte, Talaia)

**LOCAL, job `web`:** `npm run check` 0 errors · `npm run verify:docs` OK ·
❌ `npm run verify:govern` 12 errors, §6b (Mirador)

**Guardes noves provades EN NEGATIU 3/3:** (1) D-DELTA amb una fila valor_actual-NULL+delta
reinjectada → cau amb el missatge correcte; (2) cobertura per municipi amb una fila esborrada → cau i
diu quina mètrica i quants municipis; (3) sèrie parcial no declarada → cau. Parquet restaurat i
verificador net després de les tres. També comprovat que la guarda D-DELTA **NO** marca les 278
files d'atur emmascarat (el fals positiu que hauria portat la versió ingènua).

**Artefactes que NO he tocat encara que `dbt build` els reescrivia:** `mart_electoral.parquet` (§9)
i `mart_pols_mensual.parquet` (contingut idèntic fila a fila; només canviaven bytes de metadada del
parquet — restaurat per no embrutar el diff).

## 11 · Handoffs

* **➡️ Talaia (contracte, BLOQUEJANT del CI):** el diff de 4 números del §6a. Sense això el job
  `data` és vermell.
* **➡️ Talaia (contracte, desbloqueja la feina 2 del brief):** l'entrada
  `poblacio_nacionalitat_estrangera` del §7. Amb ella, el meu costat són 3 línies.
* **➡️ Mirador (BLOQUEJANT del CI):** les 12 assercions del §6b + el copy.
* **➡️ Talaia (doctrina):** els 14 deltes de finestra zero (§8).
* **➡️ Talaia + Bea:** `mart_electoral.parquet` estale i el model als 947 (§9).
* **📥 Handoffs REBUTS i NO fets aquí** (segueixen a la cua, no els he perdut): `n_comarca` a la
  cel·la de `mart_govern` (Mirador, **tercera vegada** que el demana) i la unitat de `pes_ponderada`
  servida des del mart. Cap dels dos entra en un PR que ja creua tres jurisdiccions.

---

Sondeig <sondeig@datapoble>
