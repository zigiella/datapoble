# D10 — els quatre serrells de dada que D9 va destapar

**Agent:** Sondeig · **Data:** 2026-07-20 · **Branca:** `sondeig/d10-serrells-dada`
**Cua:** `bitacora/next.md` punt 9 · **Origen:** handoffs de Mirador (D9), encaminats per Talaia.

Els quatre venien de la mateixa arrel: **la dada del tauler es descrivia a mà en més d'un lloc**.
Un motiu escrit en un sol idioma, una cadència que ningú declarava, un conjunt de mètriques
mantingut per triplicat i una etiqueta escrita al codi en comptes de llegida del contracte. Tots
quatre fallaven **en silenci**, que és l'única manera com aquests errors poden sobreviure.

---

## Verificació prèvia del brief

Cap dels quatre era fals. La correcció que Talaia ja havia fet a l'enunciat (d) —`atur_registrat`
**SÍ** que és al contracte semàntic— es confirma: `semantic/metrics.yml`, amb `caveat` propi i la
doctrina del «<5» escrita. El que no feia era arribar al catàleg servit.

Sí que hi ha **una esmena de fons a la proposta (b)**, i és al § de handoffs: la resolució que
Mirador proposa per a `hab_per_hab` i `rtc_per_100hab_viv` declararia una cadència **més ràpida que
la meitat de la mètrica**. Ho detallo avall amb el número, perquè decideixi Talaia.

---

## (c) El serrell que de veritat trencava la regla

`serveis_estab` i `restauracio_estab` es pinten al tauler (targeta «comerç i serveis», bloc C:
`kind: 'serveis'` a `GOVERN_KPIS`) i **no tenien cap fila a `mart_tendencia`** — ni tan sols com a
`sense_serie` amb motiu. El front, davant d'una mètrica sense entrada, no pinta res. Una fila que
falta és invisible: el lector no distingeix «no ha canviat» de «no ho sabem».

**Fet:** les dues entren al mart amb el seu motiu real. I el motiu **no és «encara no ingerida»**,
que hauria estat la resposta còmoda i falsa. La raó de fons és més dura i s'escriu sencera: OSM via
Overpass és cartografia col·laborativa sense calendari, se n'ingereix una sola consulta i no se'n
conserva cap tall anterior — **i encara que se'n guardessin dos, el Δ no seria llegible com un canvi
al terreny**, perquè OSM infra-mapeja el rural i la seva completesa creix amb el temps: el mapejat
nou i l'obertura real d'un establiment no es poden separar. Aquí no hi ha tendència possible amb
aquesta font, i dir «pendent d'ingesta» hauria promès una cosa que no arribarà.

### I el problema de fons, que era més gran

El conjunt de mètriques del tauler estava escrit **a mà tres vegades**: a `mart_tendencia.sql`, a
`TEND_METRICS_ESPERADES` de `tools/export_tauler_web.py` i a `SENSE_SERIE`/`AMB_SERIE` de
`verify_tendencia.py`. Tres llistes a mà no poden fer altra cosa que divergir, i la propera targeta
també hauria faltat.

**Fet:** `tools/tauler_kpis.py` (nou) deriva el conjunt de **l'única autoritat que ja existia** —
`packages/web/src/lib/govern/kpis.js`, que el propi front declara com a font única de la composició
del tauler i que comparteixen el component i `verify-govern.mjs`. Es llegeix, mai s'escriu
(jurisdicció de Mirador). L'exportador i el verificador hi recauen: **si el tauler pinta una targeta
sense fila al mart, el CI cau.**

El que segueix escrit a mà és el **motiu** de cada absència, i ha de ser així: un motiu és text
editorial i no es deriva de res. El que es deriva és la **pertinença**.

El parser és deliberadament fràgil cap a fora: peta si el fitxer no hi és, si el bloc no es deixa
llegir, si l'array surt buit o si apareix un `kind` que no sap mapejar. Provat adversarialment, els
quatre casos peten. *Un parser que falla en silenci hauria estat pitjor que la llista a mà.*

---

## (a) El motiu, en els dos idiomes

`mart_tendencia` emetia `motiu` només en català i el front el pintava literal amb `lang="ca"`
cablat. Mirador no el traduïa, i feia bé: traduir dada al front és inventar-la.

**Fet:** el mart emet `motiu_ca` i `motiu_es` (no queda cap `motiu` a seques, precisament perquè no
s'hi pugui tornar a colar un idioma implícit). Els 14 motius estan escrits en tots dos idiomes i el
verificador cau si en falta un, si és massa curt per informar, o **si `motiu_ca` i `motiu_es` són
idèntics** (senyal que s'ha copiat el català en comptes de traduir-lo).

**Decisió conscient al JSON servit:** s'hi afegeix `motiu_l10n: {ca, es}` —la forma bona, la mateixa
que `label`/`definicio`— **i es manté el camp pla `motiu` (català) de moment**. Convertir `motiu` en
objecte avui pintaria `[object Object]` a riusdegent.cat en el mateix moment de la fusió, perquè el
web és viu i cada fusió és un desplegament, i `packages/web` no és meu. És transitori i està escrit
com a tal al codi i a `_meta.tendencia.motiu`. Handoff a Mirador avall.

---

## (d) `atur_registrat` al catàleg servit

Conseqüència de la seva absència: l'etiqueta i la font de la targeta d'atur eren **les dues úniques
cadenes del tauler escrites al codi del front i no llegides del contracte**. No trencava la regla de
ferro de Bea pel resultat (la targeta mostrava font), sinó **pel mecanisme**: C6 §8.1 demana que la
procedència surti del contracte, i aquestes dues no en sortien.

**Fet:** `atur_registrat` entra a `METRIC_KEYS` de `tools/export_web_municipis.py`. Entra **només al
catàleg**: el seu valor viu a `mart_pols_mensual` i se serveix per `tauler.bergueda.json`, que té
cadència mensual pròpia (D7). Ara la fitxa arriba sencera i correcta —etiqueta ca/es, font SEPE,
`date: 2026-06`, `definicio`, el `caveat` de la doctrina del «<5»— i la frescor resol
`mensual · darrera càrrega 2026-07-05 · refresh-atur.yml`, que és **l'única font del catàleg amb
procés automàtic**.

Perquè una clau al catàleg sense valor a `values` no es torni a colar sense dir-ho, la clau consta a
`SENSE_VALOR_AL_DATASET` amb el motiu escrit, i una guarda nova cau si n'apareix una altra sense
declarar (o si una excepció declarada deixa de caldre).

---

## (b) Les 5 mètriques sense cadència — verificat, i amb una esmena

Verificat als dos JSON servits: exactament **5** amb `frescor.actualitzacio: null`
(`hab_per_hab`, `rtc_per_1000hab`, `rtc_per_100hab_viv`, `IETR`, `IETR_rank`). El diagnòstic de
Mirador és correcte i complet: **no és bug de l'export**. Les cinc són `source: datapoble`
(derivades) i cap declara `origin_source`, així que el resolutor —que fa bé de no inventar-se una
cadència— emet null.

`semantic/metrics.yml` és de Talaia i **no l'he tocat**. El diff exacte va al § de handoffs.

**El que sí que he fet és que la guarda ja corri**, amb l'excepció escrita en comptes de callada:
`check_catalog()` a `tools/export_web_municipis.py` cau si apareix una mètrica amb cadència nul·la
que no consti a una de dues llistes:

- `FRESCOR_NULL_HONEST = {IETR, IETR_rank}` — el null **s'hi queda i és la resposta correcta**:
  l'IETR composa residus + ICAEN + RTC + padró, no té UN origen del qual heretar, i triar-ne un
  seria mentir sobre quan es refresca.
- `FRESCOR_NULL_PENDENT_CONTRACTE = {rtc_per_1000hab, rtc_per_100hab_viv, hab_per_hab}` — pendents
  de l'esmena de contracte.

I la segona llista **caduca sola**: si una clau d'aquí deixa d'estar trencada, la guarda també cau i
obliga a retirar-la. *Una excepció que sobreviu al seu motiu és una mentida amb bona intenció.*
Les tres branques provades adversarialment: totes tres disparen.

---

## Com s'ha regenerat el parquet (i per què t'ho has de poder creure)

`data/raw/` és gitignored i en un checkout net no hi és: **no es pot córrer `dbt build`** en aquest
worktree. Però `mart_tendencia` només beu de tres marts que **sí que són versionats**
(`mart_pols_mensual`, `mart_demografia`, `mart_municipi`), així que s'ha reconstruït executant el
MATEIX SQL del model amb els `ref()` apuntats als parquets versionats.

**La fidelitat s'ha provat abans de tocar res:** la reconstrucció del model *sense cap canvi*
reprodueix el `mart_tendencia.parquet` committejat **valor a valor** (`DataFrame.equals` → `True`,
mateixes 18 columnes, mateixos dtypes, 15.120 files). Només després s'ha aplicat el canvi. El
resultat: **17.014 files = 15.120 + 2 × 947**, exactament les dues mètriques noves × els 947
municipis, cap fila més.

`dbt parse` corre net amb el model i l'`_marts.yml` nous.

---

## Guardes (la meva pròpia regla: cap artefacte sense la seva guarda, el mateix dia)

Cap artefacte nou en aquest PR, i per tant cap `--check` nou a cablar. El que sí que és nou són
**tres guardes, i totes tres corren des d'avui dins de passos del CI que ja existien** (comprovat al
YAML, no confiat):

| Guarda | On corre | Provada adversarialment |
|---|---|---|
| Cap targeta del tauler sense fila al mart (derivada de `kpis.js`) | `verify_tendencia.py` (job `data`) | ✅ cau amb el mart pre-D10, amb el missatge llegible |
| Motiu en ca **i** es, no buit, no copiat | `verify_tendencia.py` + invariants de `export_tauler_web.py` | ✅ |
| Catàleg: cap clau sense valor ni excepció; cap cadència nul·la no declarada; excepcions que caduquen | `export_web_municipis.py --check` (job `data`) | ✅ les tres branques |

S'hi afegeix una guarda d'esquema a `verify_tendencia.py`: si falta una columna, ho diu en comptes
de petar amb un `KeyError` tres guardes més avall. *Un traceback també és un CI vermell, però no
s'entén.*

---

## Verificació local

Tot el job `data` corregut sencer en local: ruff net · `dbt parse` OK · `verify_pols_mensual`
(224.439 files, 9 àncores byte-match) · `verify_govern` · `verify_tendencia` (17.014 files, els
1.894 Δ d'atur recalculats a mà segueixen byte-match) · `verify_marts` · els 9 `--check` d'exports ·
`pytest packages/signals` 180/180 · connectors 21/21.
`node scripts/verify-govern.mjs` (el verificador de Mirador, sobre la dada nova): **OK, 17 mètriques
amb tendència** (abans 15).

---

## ➡️ Handoffs

### A Talaia — esmena de contracte (b). Diff exacte

`semantic/metrics.yml`. Les tres són derivades sense `origin_source`; la clau va **al costat de
`source: datapoble`**, com ja fan `serveis_per_1000hab` i `restauracio_per_1000hab`.

```diff
@@ rtc_per_1000hab (L562) @@
     formula: "rtc_total / poblacio * 1000"
     source: datapoble
+    origin_source: rtc
     table: mart_municipi

@@ rtc_per_100hab_viv (L576) @@
     formula: "rtc_total / hab_total * 100"
     source: datapoble
+    origin_source: rtc
     table: mart_municipi

@@ hab_per_hab (L257) @@
     formula: "hab_total / poblacio"
     source: datapoble
+    origin_source: idescat_emex
     date: "2021/2025"
```

Resolució simulada amb el resolutor real, abans de proposar-ho:

| clau | `origin_source` | frescor resultant |
|---|---|---|
| `rtc_per_1000hab` | `rtc` | `irregular` · càrrega 2026-06-21 · procés `cap` |
| `rtc_per_100hab_viv` | `rtc` | `irregular` · càrrega 2026-06-21 · procés `cap` |
| `hab_per_hab` | `idescat_emex` | `anual` · càrrega 2026-06-21 · procés `cap` |

`IETR`/`IETR_rank`: **no tocar**. El null hi és honest i la guarda ja el declara com a tal.

**⚠️ L'esmena que el handoff original no porta, i que és teva de decidir.** Les dues mètriques amb
`hab_total` al denominador **barregen vintages**, i `origin_source` els declararia una cadència més
ràpida que la meitat de la seva pròpia dada:

- `hab_total` té `actualitzacio: puntual` i `date: 2021` (Cens d'habitatge). `poblacio` i `rtc_total`
  es refresquen; el parc d'habitatge fa cinc anys que no.
- Amb `origin_source: idescat_emex`, `hab_per_hab` diria **«anual»** al lector, quan el seu numerador
  és congelat a 2021. Ho mitiga que la mètrica ja declara `date: "2021/2025"`.
- **`rtc_per_100hab_viv` NO declara cap `date`.** La seva barreja de vintages (RTC 2026 / habitatge
  2021) avui **no la diu enlloc**. Sigui quina sigui la teva decisió sobre `origin_source`, aquesta
  és una absència a part i la deixo assenyalada.

Dues sortides, i és doctrina, no dada: (i) acceptar la convenció actual —la cadència diu *cada quan
es mou el número*, i el `date` diu *de quan és*— i llavors només cal afegir el `date` que falta a
`rtc_per_100hab_viv`; o (ii) que una derivada de vintages mixtos hereti el **més lent** dels seus
inputs (`actualitzacio: puntual` com a override a la mètrica, que el resolutor ja respecta). Jo
proposo (i) + el `date` que falta, però el vot és teu. Quan baixi, retiro les claus de
`FRESCOR_NULL_PENDENT_CONTRACTE` i la guarda es tanca sola.

### A Mirador — dues línies, i una que ja no és de dues

1. **`motiu_l10n`.** `pick(e.motiu_l10n, locale)` en lloc de `{e.motiu}`, i fora el `lang="ca"` de
   `+page.svelte`. El mart ja serveix els dos idiomes. Quan hi sigui, retiro el camp pla `motiu` i
   `TendenciaEntry.motiu` pot passar a `Localized`.
2. **`atur_registrat` ja és al catàleg servit.** L'etiqueta i la font de la targeta d'atur poden
   sortir de `metrics.atur_registrat` (amb `frescor` inclosa) en lloc d'estar escrites al codi.
3. **⚠️ Troballa nova, i és exactament la mateixa forma que el bug que acabem d'arreglar.** El
   glossari (`src/routes/glossari/+page.svelte`) agrupa per dimensió amb un `DIM_ORDER` fix, i
   **`treball` no hi és**. `atur_registrat` (dimension: `treball`) arribarà al dataset i el glossari
   **el descartarà en silenci**: una dimensió que no és a `DIM_ORDER` desapareix sense dir res. Cal
   `'treball'` a `DIM_ORDER` + la seva etiqueta i18n ca/es. I val la pena que el descart deixi de
   ser mut: el glossari es ven com «el contracte, llegible per humans», i ara pot amagar-ne una part
   sense que ningú se n'assabenti.
4. `serveis_estab` i `restauracio_estab` ja tenen fila amb motiu. La targeta de serveis només demana
   la tendència de `serveis_estab` (`trendsOf('serveis_estab')`); ara que hi ha les dues, decidiu
   vosaltres si la de restauració també s'ensenya — la dada hi és i el motiu és diferent prou poc
   perquè potser no calgui pintar-lo dos cops.

### A qui reculli el pattern «guardes que no corren» — un quart cas

Talaia en compta tres. **N'hi ha un quart, latent:** `tools/export_indicadors_cat.py` genera
`data/web/indicadors-catalunya.json`, que **és versionat**, i no té `--check` ni cap pas al CI. He
comprovat que **avui NO és estale** (regenerat i idèntic byte a byte), o sigui que és un forat obert,
no una ferida. És jurisdicció meva i queda encuat, fora d'aquest PR per no barrejar-lo amb D10.

### Higiene, no urgent

- **`tools/` no passa per ruff al CI.** El pas de lint cobreix `packages/transform|ingestion|signals`
  i prou. Hi ha **6 errors preexistents en 5 fitxers** (`daily_report`, `export_bergueda_bundle`,
  `extract_renda`, `nivellc_regressio`, `senyal_sub1000`). Els meus passen; no els arreglo aquí
  perquè seria un PR diferent, però mentre `tools/` no es lint-i, la meva pròpia jurisdicció té una
  porta menys que la resta.
- **Trampa d'entorn local, no del repo:** en aquesta màquina l'`editable install` de
  `datapoble_ingestion` apunta al worktree d'**un altre agent**, i per això
  `test_idescat_emex.py` falla en local amb un `ValueError` que no té res a veure amb el codi
  d'aquí (amb el `PYTHONPATH` apuntat a aquest worktree: **21/21 verds**). El CI instal·la del seu
  propi checkout i no en pateix. Ho deixo escrit perquè el pròxim que ho vegi no persegueixi un
  fantasma — mateix gènere que les races de worktree compartit que ja tenim documentades.

---

## Fora d'abast, per decisió

`mart_electoral` i `mart_consum_electric` **no s'han tocat**, com marcava el brief: el vot de Bea
(«electoral darrere la tanca») i el fet que els 31 municipis del consum elèctric són l'abast
**correcte** del substrat congelat del geo-rag, no un estale.
