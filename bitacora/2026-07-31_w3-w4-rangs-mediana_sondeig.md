# W3 + W4 · el rang que faltava i el valor de referència honest (Sondeig)

**Data:** 2026-07-31 · **Agent:** Sondeig · **Tasca:** W3 i W4 de `bitacora/next.md`
(esmenes de Bea del 2026-07-31).
**Lliurament:** un PR · **branca:** `sondeig/w3-w4-rangs-mediana` · **no fusiono jo.**

Artefactes tocats: `packages/transform/models/marts/mart_govern.sql` ·
`packages/transform/models/marts/_marts.yml` · `packages/transform/verify_govern.py` ·
`tools/export_govern_web.py` · `tools/tauler_kpis.py` · `data/marts/mart_govern.parquet` ·
`data/web/govern.bergueda.json` · `data/web/govern.catalunya.json`.

## W3 · les dues mètriques que no tenien rang

`mart_govern` passa de **7 a 9 KPIs**: 947 × 9 = **8.523 files** (abans 6.629).

### `vidre_hab` — entra sense cap reserva

Esmena literal de Bea. Mateixa font i mateix denominador que `kg_hab_any` (ARC 2024,
població de residus), i **cobertura 947/947 sense un sol forat**: cap comarca amb dada
parcial, denominador mínim 3 municipis (el mateix mínim que ja tenien les altres set).
La Pobla: **48,6 kg/hab/any, 17 de 31**.

### `pct_nacionalitat_estrangera` — entra, i la premissa que la retenia era FALSA

⚠️ **Premissa falsa del repo, no del brief.** El capçal de `mart_govern.sql` deia, com a
motiu de l'exclusió: *«nota narrativa VINCULANT de Bea (gorra §3): cap rang públic d'aquest
KPI abans del seu vot»*. **El vot ja havia arribat feia dotze dies**: l'esmena **E9** de
`docs/ajuntaments/tauler-v2-esmenes-bea.md` (2026-07-19), document que el seu propi encapçalament
declara vinculant i que *«mana sobre C6 i sobre la gorra §3 allà on discrepin»*, diu
«**Rang comarcal al % nacionalitat estrangera** … el rang existeix; estava retingut esperant
el vot — **ara s'hi posa**».

I hi ha una segona premissa falsa, dins la mateixa fila d'E9: la columna «Estat de la dada»
deia «✅ **el rang existeix**». **No existia.** El mart no el calculava ni l'ha calculat mai
fins avui. D'aquí ve que el `pendingRank` del front hagi durat dotze dies: la tasca es va
donar per resolta del costat de la dada quan del costat de la dada no s'havia fet res. La
capçalera d'E9 assignava l'esmena a «Mirador» sol; era de tots dos.

**El que NO decideix aquesta tasca:** la nota narrativa de la gorra §3 segueix viva i sencera
per a tot el que és **copy** — l'etiqueta, el text de la fitxa i com es llegeix en veu alta un
«6 de 27». El rang es calcula amb la convenció uniforme del mart (`rank()` DESCENDENT, 1 = el
valor més alt), la mateixa de les altres vuit; fer-hi una excepció d'ordre hauria estat una
decisió editorial amagada dins el SQL. Però això vol dir que a la targeta el número 1 de la
comarca és el municipi amb el percentatge **més alt**, i com s'anomena això és vot de Bea, no
meu. **➡️ Handoff a: Bea (copy) + Mirador (pintura).**

**Denominador honest, i aquí sí que es veu per què cal.** La mètrica viu a `mart_demografia`
amb el llindar mínim N (els percentatges d'origen no es publiquen sota `demografia_min_n`):
**938 dels 947** tenen dada. **No és un denominador ridícul i per tant no calia dir que no** —
però al Berguedà 4 dels 31 municipis cauen, i el rang ho ha de dir: **«6 de 27», mai «6 de 31»**.
Les nou files sense dada surten amb `valor` i `rang` a NULL i la comarca comptada de menys, com
mana la doctrina. Àncora nova a `verify_govern.py` precisament per fixar-ho.

Les 9 sense dada: 08080, 08093, 08177, 08216 (Berguedà) · 25071 · 43057, 43061, 43143, 43146.

**D'on la pren el model sense trencar la partició comarcal.** `mart_demografia` porta la seva
pròpia columna `comarca`, derivada de `stg_residus`. Se n'ha pres **només `ine5` i el valor**:
la partició del rang la fixa `municipis-territori.json` i **només** ella, com les altres vuit.
Si s'hagués colat l'altra, dos KPIs del mateix tauler podrien rankejar contra dues particions
diferents sense que res petés. `mart_demografia` té 1 fila per `ine5` (947), així que el
`left join` no pot multiplicar files — i `verify_govern` ho comprova amb el recompte exacte.

### Les dues velles, intactes

Comprovat abans de res: reconstruint el model **sense canvis** amb els `ref()` apuntats als
parquets versionats, el resultat reprodueix el parquet committejat **valor a valor**
(`DataFrame.equals` → True, 6.629 files, mateixos dtypes i mateix esquema parquet). Després
del canvi, les **7 mètriques antigues surten idèntiques** columna a columna (valor, rang,
n_amb_dada, data). El que hi ha de nou és nou; el que hi havia no s'ha mogut.

## W4 · el valor de referència: la mediana de les NOSTRES dades

### La trampa, no trepitjada

Les constants `base_residencial: 410` · `base_electric: 1224` · `base_vidre: 26.5` de
`dbt_project.yml` **no s'han fet servir enlloc**. Són les bases de les capes L1/L2/L3 del model
de pernocta aparcat i posar-les a una targeta viva hauria estat reintroduir-lo per la porta del
darrere. Perquè no hi torni per despistat, `verify_govern.py` porta una **guarda amb nom**: si
una mediana catalana de residus, elèctric o vidre coincideix EXACTAMENT amb la seva base
aparcada, el CI s'atura i que algú ho miri. Provada en negatiu (peta amb el missatge correcte).

### Les sis medianes de Talaia: confirmades

Recalculades des de zero sobre els 947 municipis, sense mirar les seves:

| Mètrica | Mediana CAT (next.md) | **mesurada** | Mediana Berguedà (next.md) | **mesurada** |
|---|---|---|---|---|
| `kg_hab_any` | 472,1 | **472,06** (947 munis) | 759,9 | **759,88** (31) |
| `kwh_hab` | 1.529,3 | **1.529,30** (947) | 1.648,8 | **1.648,80** (31) |
| `vidre_hab` | 29,0 | **29,00** (947) | 49,8 | **49,80** (31) |

**Les sis confirmades.** Les dues que no quadren al decimal (472,1 i 759,9) són el mateix
número arrodonit a 1 decimal a `next.md`; el valor exacte és 472,06 i 759,88. Totes sis són
àncores a mà del verificador des d'ara.

### Què s'emet, i per què totes dues

Cada cel·la del mart (i del JSON) porta **`mediana_comarca`** i **`mediana_catalunya`**. Surten
del **mateix `partition by` que el rang** (la comarcal) i d'un de global (la catalana):
`median()` ignora els NULL, així que el denominador de la comarcal **és exactament `n_amb_dada`**,
el mateix del rang, i el de la catalana és **`n_mediana_catalunya`**, columna nova. Amb això la
targeta pot dir què és i sobre quants municipis es calcula, que és el que demana C6 §8.1.

**S'emeten per a les NOU mètriques, no només per a les tres.** El brief demanava com a mínim
`kg_hab_any`, `kwh_hab` i `vidre_hab` i preguntava si a alguna altra hi encaixa. La resposta és
que hi encaixa a totes: la mediana no és una mètrica nova sinó una **mesura de la nostra pròpia
dada**, surt del mateix GROUP BY, no costa cap càlcul extra i no fabrica res. Triar-ne tres al
model hauria estat fer jo el tall editorial dins la capa de dades. **Quina es pinta i on segueix
sent decisió de Bea** (Talaia recomana la comarcal); servint-les totes dues no la bloquegem, i si
demà la vol a renda o a envelliment no cal tornar a tocar el mart.

### No s'arrodoneix al mart (i el perquè importa)

Primer es va escriure amb `round(…, 2)`. Es va **retirar** en mesurar que DuckDB i pandas
trenquen els empats del `.005` amb regles diferents: **18-19 dels 387 grups comarcals**
discrepaven en 0,01, i cap dels dos intents de replicar la regla de DuckDB des de Python
(`Decimal(repr(x))` i `Decimal(x)`, HALF_UP) no la reprodueix del tot. El verificador hauria
acabat comprovant una regla d'implementació del motor, o afluixant a una tolerància.

**Sense arrodonir, la mediana de DuckDB i la de pandas coincideixen BIT A BIT** als 387 grups
comarcals i als 9 catalans. Per tant el mart emet la mediana exacta i `verify_govern.py` la
recalcula amb pandas i la compara amb **igualtat exacta**, que és la verificació més forta
disponible. Arrodonir per pintar és feina de la targeta.

### On van, dins la cel·la (i el preu)

Les medianes van **dins de cada cel·la** i no en un bloc global del fitxer, perquè el prebuild
de Mirador parteix `govern.catalunya.json` per municipi (`static/data/govern/<ine5>.json`) i el
front només llegeix el seu tros: una referència fora de l'entrada del municipi no li arribaria mai.

**El preu, mesurat:** `govern.catalunya.json` passa de **689 kB a 1.595 kB**. D'aquest creixement,
~197 kB són les dues mètriques noves i ~709 kB les medianes (la catalana és constant per mètrica i
es repeteix 947 cops — redundància que ja pagàvem amb `comarca` i `data`). Context: el fitxer
germà `municipis.catalunya.json` ja en fa 1.870 kB, i **el que el navegador carrega no és aquest
fitxer sinó el shard del municipi**, que passa d'~0,3 kB a ~1,7 kB. Si algun dia el pes del fitxer
versionat molesta, l'alternativa honesta seria un germà `govern-referencies.json` (43 comarques ×
9 + Catalunya × 9 ≈ 5 kB) amb el seu `--check`; **no s'ha fet** perquè obligaria Mirador a una
segona petició i el brief demanava explícitament emetre-les al JSON de govern.

## Guarda nova: el pont front↔dades

El conjunt de mètriques amb rang viu escrit **dues vegades** — `RANK_METRICS` a l'exportador i
`GOVERN_RANK_KEYS` a `packages/web/src/lib/govern/kpis.js` — i divergir en silenci ja va mossegar
el 2026-07-30 (els `kind` nous del v3 sense registrar; la lliçó escrita a `next.md` era «una
verificació per jurisdiccions es deixa els ponts entre jurisdiccions»).

`tools/tauler_kpis.py` guanya `claus_rankejades_del_front()` — llegeix `GOVERN_RANK_KEYS` de
l'autoritat del front, mai hi escriu, i **peta si no troba el bloc** (un parser que falla en
silenci seria pitjor que la llista a mà). L'exportador comprova **la direcció perillosa**: cap
clau que el front declari rankejable pot faltar al mart, perquè la targeta prometria un rang que
ningú serveix. La inversa —el mart rankeja i el front encara no ho pinta— és **estat de trànsit
legítim** i per això la guarda comprova inclusió, no igualtat: avui mateix el mart en rankeja 9 i
el front n'espera 7.

## El `pendingRank` NO cau en aquest PR (i no pot)

`GOVERN_RANK_KEYS` i el `pendingRank` de `pct_nacionalitat_estrangera` viuen a
`packages/web/src/lib/govern/kpis.js`, que és **de Mirador**, i Mirador treballa en paral·lel a
W1/W5. Aquest PR **serveix la dada**; la marca cau quan Mirador afegeixi les dues claus.
**➡️ Handoff a: Mirador** — dues línies, quan li vagi bé:
1. `GOVERN_RANK_KEYS` += `'vidre_hab'`, `'pct_nacionalitat_estrangera'`.
2. treure `pendingRank: true` de l'entrada de `pct_nacionalitat_estrangera` i el comentari «el
   vidre no el rankeja el mart» de l'entrada de `vidre_hab` (ja no és cert).
   La targeta de `kind: 'naixement'` manté el seu `pendingRank`: **`pct_nascuda_estranger` NO
   entra en aquest PR** — el lloc de naixement no és a `mart_municipi` i E9 parla de nacionalitat,
   no de naixement; confondre-les és el marc que el propi contracte prohibeix.

Un cop fet, les tres medianes ja hi seran servides per pintar-les (W4 · pintura).

## Handoff a Talaia · el contracte i la mediana

Per precedent propi de la casa (D11: «126+134 al front seria fabricar una xifra sense
procedència, C6 §8.1 → ha de néixer al contracte»), la mediana és una **xifra nova a la targeta**
i hauria de constar al contracte. Però **no és una mètrica nova per municipi**: és una mesura
agregada de mètriques que ja hi són. Per això la proposta és **un bloc de doctrina al capçal de
`semantic/metrics.yml`**, com els d'E13 i FRESCOR, i **no** nou claus noves. `semantic/metrics.yml`
és de Talaia i **no l'he tocat**. Diff exacte proposat, per enganxar després del bloc MICROMUNICIPI:

```yaml
# VALOR DE REFERÈNCIA (W4, esmena de Bea 2026-07-31; dada emesa per Sondeig a mart_govern).
# Les targetes de rang poden mostrar, al costat del «k de n», un valor de REFERÈNCIA: la
# MEDIANA d'aquella mateixa mètrica. No és una mètrica nova ni una clau d'aquest fitxer:
# és una MESURA agregada de les nostres pròpies dades i hereta font, `date` i `caveat` de
# la mètrica que resumeix.
#   · mart_govern emet DUES medianes per cel·la: `mediana_comarca` (calculada sobre els
#     `n_amb_dada` municipis de la comarca amb dada — el MATEIX denominador del rang) i
#     `mediana_catalunya` (sobre `n_mediana_catalunya`). Quina es pinta és decisió
#     editorial de Bea; la dada serveix les dues per no bloquejar-la.
#   · PROCEDÈNCIA OBLIGATÒRIA (C6 §8.1): qui pinti una mediana ha de dir QUÈ és i SOBRE
#     QUANTS municipis es calcula. Una mediana sense el seu denominador és una xifra sense
#     procedència.
#   · PROHIBICIÓ EXPLÍCITA: la referència no pot ser mai una constant del MODEL DE PERNOCTA
#     APARCAT (base_residencial 410 · base_electric 1224 · base_vidre 26,5 de
#     dbt_project.yml). Es mesura de les nostres 947 dades o no es publica.
#     verify_govern.py té una guarda que peta si una mediana hi coincideix.
```

## Verificació LOCAL (el CI per-PR també corre; això és el que he passat aquí)

- `ruff check packages/transform packages/ingestion packages/signals` (l'abast exacte del CI) —
  **net**. *(Nota: en aquest arbre hi ha ruff 0.15.22, no el 0.15.18 fixat al CI; els 6 avisos que
  treu són tots a `tools/*.py` que no he tocat i que el CI **no linta**. No els he perseguit,
  seguint l'avís del brief.)*
- **`verify_govern.py` — OK**: 8.523 files (947 × 9), 43 comarques, 30 sense dada amb rang NULL
  honest, **7 àncores de rang** a mà byte-match, Gombrèn contra els 19 del Ripollès, medianes
  recalculades amb **igualtat exacta** als 387 grups comarcals + 9 catalans, **6 àncores de
  mediana** a mà, cap coincidint amb les bases aparcades.
- **`verify_tendencia.py` — OK** (la guarda creuada front↔dades que va destapar el vermell d'ahir):
  20.802 files, 947 municipis, 3 mètriques amb sèrie i 18 declarades sense, 1.894 Δ d'atur
  recalculats a mà, cap fletxa sense període. El conjunt de mètriques del tauler **no canvia**
  (les dues noves ja es pintaven), per això segueix verda.
- `verify_contracte` (61 mètriques) · `verify_pols_mensual` (224.439 files, 9 àncores) ·
  `verify_marts` — OK.
- `dbt parse` — OK.
- Tots els `--check`: `derive_fase1` · `validacio_etca` · `tipus_territorial` ·
  `calibracio_intervals` · `export_pernocta_catalunya` · `discrepancia_etca_pernocta` ·
  `senyal_sub1000` · `export_licitacions` · `export_web_municipis` (catalunya + bergueda) ·
  **`export_govern_web`** · `export_tauler_web` — tots OK.
- `pytest tools/tests` (antileak) 5/5 · `pytest packages/signals/tests` 182/182 ·
  `pytest packages/ingestion/tests/test_atur_sepe.py test_idescat_emex.py` **21/21** (amb
  `PYTHONPATH` forçat a aquest arbre; vegeu la nota de la regla dura, al final).
- **`node packages/web/scripts/verify-govern.mjs`** (la guarda de Mirador, sobre la dada nova) —
  **OK**: 947 munis amb rang, paritat dataset↔mart a la Pobla, Barcelona amb el rang del
  Barcelonès.

### Guardes noves, provades EN NEGATIU (6/6 peten amb el missatge correcte)

| Mutació injectada | Resultat |
|---|---|
| `mediana_comarca` mentida a una fila | peta · «mediana_comarca ≠ mediana recalculada a 1 files» |
| `mediana_catalunya` de residus = 410 (la base aparcada) | peta · guarda del model aparcat + àncora |
| `n_mediana_catalunya` fals | peta · recompte real + «el tot no pot ser menor que la part» |
| columna `mediana_comarca` absent | peta · esquema, abans de cap KeyError |
| `vidre_hab` fora del mart | peta · conjunt de mètriques + 947×9 + tres àncores |
| `kpis.js` declara rankejable una clau que el mart no té | peta · guarda del pont front↔dades |
| `GOVERN_RANK_KEYS` renombrat a `kpis.js` | peta · el parser no passa per alt |

`packages/web/` va quedar restaurat byte-idèntic després de les proves (`git status` net).

## Premisses del brief

- **Certa:** `RANK_METRICS` en tenia 7 i hi faltaven les dues.
- **Certa:** `pct_nacionalitat_estrangera` viu a `mart_demografia`, no a `mart_municipi`.
- **Certes:** les sis medianes de Talaia (dues d'elles arrodonides a 1 decimal a `next.md`).
- **Certa i important:** les constants 410/1.224/26,5 són les bases del model aparcat. No tocades.
- **No aplicada:** «si alguna de les dues NO es pot rankejar honestament, digues-ho i no la
  forcis». **Totes dues es poden**: vidre 947/947 i nacionalitat 938/947 amb el «k de n» honest
  al seu lloc. El «no» no calia — el que calia era el matís de dalt: la nota narrativa que la
  retenia ja no la reté (E9), però el **copy** segueix sent de Bea.
- **Falsa, i és del repo:** el capçal de `mart_govern.sql` deia que el KPI d'origen esperava el
  vot de Bea; el vot era d'E9, del 2026-07-19. Esmenat al model.
- **Falsa, i és del repo:** la fila E9 de `tauler-v2-esmenes-bea.md` afirma «el rang existeix».
  No existia. **➡️ Handoff a: Talaia** — si aquell document es manté com a registre viu, aquella
  cel·la hauria de dir «FET el 2026-07-31 (W3)»; si és històric, val la pena una nota, perquè
  aquesta afirmació és exactament la que va deixar el `pendingRank` dotze dies penjat.

## Com s'ha regenerat el parquet

`data/raw/` és gitignored: no hi ha `dbt build` possible en un checkout net. `mart_govern` només
beu de dos marts versionats (`mart_municipi`, `mart_demografia`) i d'un JSON versionat
(`municipis-territori.json`), així que s'ha reconstruït executant el SQL del model amb els `ref()`
apuntats als parquets versionats i **escrivint amb el mateix `COPY … (FORMAT PARQUET)` del
post_hook de dbt** (no `pandas.to_parquet`, que hi afegiria metadata de pandas i canviaria els
dtypes de lectura). **Abans de tocar res**, la reconstrucció del model sense canvis reprodueix el
parquet committejat valor a valor. Mètode de D10 / V3-DADES.

## Regla dura del worktree

Cap `pip install -e` en aquest arbre. Les sondes pròpies d'aquesta tasca (`verify_govern`,
`export_govern_web`, `tauler_kpis`) resolen les rutes des del propi fitxer i no depenen de cap
instal·lació, igual que `tools/tests` i `packages/signals/tests`.

**El risc ha tornat a ser real i s'ha comprovat, no suposat.** Els tests d'ingestió (`atur_sepe`,
`idescat_emex`) sí que importen el paquet editable. Sonda de ruta:

- sense `PYTHONPATH`, el `__file__` de `datapoble_ingestion` apuntava al worktree d'**UN ALTRE
  AGENT** (identificador diferent del meu), viu ara mateix.
- amb `PYTHONPATH` cap a aquest arbre, apunta al meu `packages/ingestion/` i surten **21/21 verds**.

O sigui: la tercera aparició del mateix risc. No he reapuntat l'editable (trencaria les sondes de
tothom); he forçat `PYTHONPATH` i he comprovat la ruta al `__file__` abans de creure'm cap verd.

**Lliurament:** PR `sondeig/w3-w4-rangs-mediana` → `main`. **No fusiono jo.**
