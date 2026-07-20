# L'electoral rere la tanca — i les quatre portes per on la tanca s'anunciava

**Front:** Brúixola · **Data:** 2026-07-20 · **Tasques:** electoral rere la tanca (decisió de Bea,
via Talaia) + deprecated-refús (handoff de Sondeig, #268)

## Primer, el que el brief donava per fet i no és cert

El brief deia: «ja existeix el mecanisme per tancar-ho: la dimensió `origen` està retinguda de
l'agent amb test de regressió; **l'electoral no té aquesta porta**». Tres premisses, verificades una
a una:

1. **«L'electoral no té porta» — FALS.** `packages/ai/src/datapoble_ai/politics.py` existeix des de
   fa temps: `PoliticsGate`, que refusa tota mètrica `dimension: politica` a l'executor compartit
   pels dos backends, amb còpia neutra i deliberadament discreta, i **fail-safe** (si
   `AI_POLITICS_UNLOCK` no està configurada no hi ha paraula que casi, i la porta no s'obre per a
   ningú). Bea ja havia decidit sobre això i ja estava implementat.
2. **«El xat pot respondre preguntes electorals contra un parquet de 31 municipis» — FALS tal com
   està escrit.** Amb la configuració de producció (cap secret) el xat **refusa** cada pregunta de
   vot: `political_gated`. Comprovat contra les quatre mètriques. Només és cert **darrere la clau**
   de runtime.
3. **«31 municipis / 372 files» — FALS.** `mart_electoral` té **31 files i 31 municipis** (una fila
   per municipi; les dues eleccions són columnes, `_A20241` i `_A20211`). Les 372 files són de
   `mart_consum_electric` (12 mesos × 31 municipis). Els dos parquets es van creuar al traspàs.
   La conclusió de fons no canvia: 31 de 947.

El que sí que era exacte: 3 de les 4 mètriques no porten `status`, i per tant comptaven com a vives.

## El forat real: la porta tanca la RESPOSTA, i tot el que només ENUMERA hi passava pel costat

`PoliticsGate` s'activa sobre una **mètrica ja resolta**. Per construcció, doncs, no arriba a cap
superfície que es limiti a llistar el catàleg. N'hi havia quatre obertes, totes verificades
executant, no llegint:

1. **El prompt i l'enum del model** (`llm.py`): `pct_indep`, `pct_esquerra` i `guanya` s'oferien al
   LLM com a mètriques triables, amb etiqueta i definició. El model podia triar-les i només llavors
   ser refusat — i un prompt que enumera una taula electoral és un prompt que la filtra.
2. **La llista «Mètriques disponibles»** del refús `out_of_catalog` (`router.py`): es construïa amb
   `available_metrics()` sense filtrar, així que a qui preguntava una cosa fora de catàleg se li
   responia que sí que podíem contestar «% vot independentista, % vot esquerra, Candidatura
   guanyadora» — i si ho preguntava, refús. Això contradiu literalment la doctrina que el propi
   `api.py` té escrita per a `/metrics`: «the public catalog must not announce what the
   "Pregunta-li" will refuse to answer».
3. **`pct_extrema_dreta`, el pitjor.** És `status: planned`, i una mètrica planned es refusa a
   `parse()`, **abans** d'arribar a la porta. Resultat literal en producció:
   > «La mètrica «% vot extrema dreta» està definida al contracte però encara no està calculada
   > (status: planned), així que encara no la puc consultar.»

   Anomena la mètrica de vot **i promet que arriba**. I no és una ruta hipotètica: les dues
   frases que hi porten («On creix més l'extrema dreta?» / «¿Dónde crece más la extrema derecha?»)
   són **`sample_questions` del contracte**. A més estava fixat com a comportament esperat per 4
   tests i 2 casos d'eval.
4. **L'allow-list de SQL** (`catalog.tables()` → `Warehouse.allowed_tables`) contenia
   `mart_electoral` perquè derivava de les mètriques disponibles.

## La decisió: mateixa FORMA que `origen`, frontissa diferent

La porta d'`origen` encaixa en la forma —retenir la dimensió sencera a `is_available()`, que és
**l'únic predicat que llegeixen totes les superfícies**; una porta que s'ha de reimplementar a cada
superfície és una porta que en faltarà a alguna— però **no encaixa en la condició**:

- `origen` és **incondicional**: no té escapatòria fins que existeixi la frontera d'origen (#71).
- `politica` és **condicional**: Bea va dissenyar una clau de runtime.

Col·lapsar-les hauria **revocat en silenci una clau que no és meva de revocar**: el meu role diu
que «què pot respondre l'agent sobre capes sensibles» és decisió de **Bea**. I hauria tingut un
segon efecte gens obvi: en deixar de ser resoluble la mètrica, el refús hauria caigut al de
`planned`, que **anomena la mètrica** — hauríem canviat una porta discreta per una que crida.

Per això he separat dos conceptes al catàleg:

- `HELD_BACK_DIMENSIONS = {origen, politica}` — què **no s'anuncia ni es consulta**.
- `KEYED_DIMENSIONS = {politica}` — quines d'aquestes una clau de runtime encara pot obrir.

I dos predicats: `is_computed()` («hi ha número darrere?») i `is_available()` («l'agent el pot
mostrar?»). La clau segueix funcionant exactament igual (verificat: Berga, 49,10%); el que ha
desaparegut és l'**anunci**.

Conseqüència documentada al codi: `mart_electoral` **es queda** a l'allow-list de SQL, perquè la
ruta amb clau ha de poder executar-se; l'allow-list acota el radi d'explosió, no és la porta de
política. En canvi `mart_demografia` (origen, sense clau) **surt** de l'allow-list.

**No he reconstruït el mart**, com manava el brief.

## Tasca 2 — deprecated-refús (#268), i la meitat que el handoff no demanava

`is_available()` només excloïa `planned`. Ara `NOT_SERVED_STATUSES = {planned, deprecated}`.

El detall que importa: `index_turisme` **segueix tenint columna al `mart_municipi` real** (55
columnes). O sigui que no fallava res — el xat simplement continuava servint un número que el
projecte havia decidit no sostenir (vot de Bea, 2026-07-18). El mode de fallada silenciós, que és
el dolent.

I la meitat que no es demanava: en excloure'l, el refús queia a la còpia de `planned` — «encara no
està calculada» — que d'una mètrica **retirada** és una promesa falsa de retorn. Afegit
`METRIC_DEPRECATED` amb còpia pròpia (ca+es). **La còpia queda pendent del vot narratiu de Bea.**

## Estat verificat (executant, no llegint)

Catàleg servit: **47 mètriques**. `politica`, `origen` i `index_turisme`: fora de
`available_metrics()`, de l'enum del LLM, del prompt, de la llista del refús i de `/metrics`.
Segellat (per defecte): tota pregunta de vot → `political_gated` discret, **inclosa la planned**;
`pressió turística` → `metric_deprecated`; `població` segueix responent. Amb clau: respon igual que
abans. **220 tests verds, `ruff` net.**

Les portes noves **mosseguen**: revertint només les dues constants del catàleg, cauen 7 tests
(3 de catàleg, 2 de politics, 1 de guardrails, 1 de costcontrol). Un test que no pot fallar no és
una porta.

## Handoffs

**➡️ Handoff a: Bea — decisió, no codi.** La clau segueix oberta i **darrere hi ha 31 municipis de
947**, sense cap avís de cobertura a la resposta: Berga contesta 49,10% i els altres 916 tornarien
buit — el buit per artefacte de pilot i el buit per «no ho sabem» es llegeixen igual, que és el
problema que aquesta tasca volia treure. Jo he tancat l'anunci i **no he tocat la clau**. Tres
sortides, totes teves: (a) revocar la clau; (b) reconstruir el mart —decisió editorial: publicar
agregats electorals dels 947 en un repo públic—; (c) deixar la clau i posar-hi un avís de cobertura
a la resposta. Mentre no diguis, queda com està.

**➡️ Handoff a: Talaia — contracte.** `semantic/metrics.yml`, `sample_questions`: hi ha dues
preguntes llavor de vot. El contracte posa d'exemple justament allò que l'observatori ha decidit no
respondre. Proposta (no ho toco, és teu):

```diff
   ca:
-    - On creix més l'extrema dreta?
   es:
-    - ¿Dónde crece más la extrema derecha?
```

**➡️ Handoff a: Mirador — web.** `packages/web/src/lib/ask/api.ts`: `RefusalReason` és una unió
tancada a la qual li falten **dos** valors que l'API ja retorna: `political_gated` (això ja passava
abans d'avui) i `metric_deprecated` (nou). Tots dos cauen al `default` →
`pl_refusal_generic()`. Degrada bé (el `text` de l'API es continua pintant com a detall), però el
titular és genèric.

**Serrell propi (queda a la meva cua, no en aquest PR):** `Warehouse.query` no embolcalla els errors
de DuckDB — una `BinderException` puja crua fins al cridador (vist amb `vidre_hab`, absent de la
fixture CSV). Hauria de ser `WarehouseError` i acabar en refús, no en excepció.

## Nota de mètode

Els primers sondeigs els vaig fer amb `python` pelat des de l'arrel i **estava important
`datapoble_ai` del worktree d'un altre agent** (el `pip install -e` apunta a un sol lloc), amb el
seu `semantic/metrics.yml`, on `index_turisme` encara constava com a públic. Ho vaig veure perquè
un traceback duia una ruta que no era la meva. `pytest` no hi cau (`pythonpath = ["src"]` al
`pyproject`), però qualsevol sonda ad-hoc sí. **Els sondeigs manuals han de fixar el `PYTHONPATH`**;
si no, es verifica l'arbre d'un altre i es conclou el contrari del que passa al teu.
