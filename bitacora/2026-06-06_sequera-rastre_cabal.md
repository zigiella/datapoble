# Connector de sequera (ACA) — 2n rastre del cabal

**Fecha:** 2026-06-06
**Autora:** Cabal
**Para:** Talaia (review)
**Tema:** afegir un **2n rastre independent** a la taula `events`: la **sequera** (declaracions/canvis d'estat de l'ACA per municipi), pilot Berguedà. NO el motor de convergència (segueix sent PR següent).
**Status:** avance / handoff

## Contexto

El cabal ja tenia la taula `events` + 1 rastre (contractació, `ybgg-dgi6`, 1.295 events). Aquesta entrada documenta el **segon rastre**: una declaració/canvi d'estat de sequera (normalitat → prealerta → alerta → excepcionalitat → emergència) per a un municipi en una data **és un rastre administratiu net** —l'ACA declara una restricció→ senyal de **pressió hídrica** que convergeix amb el turisme/segona residència (més població real → més consum → més tensió quan l'embassament baixa). Mateix esquema `events`, font nova, connector nou en paral·lel al de contractació.

## Qué hicimos / decidimos

### La font (verificada de debò amb l'API SODA, no de memòria)
Dataset **`i5n8-43cw`** — «Estat de sequera per unitats d'explotació i municipis a les Conques Internes de Catalunya» (ACA, Dades Obertes de Catalunya). Inspecció directa del schema i de les dades:
- Columnes: `data_canvi_estat_sequera`, `codi_unitat_explotaci`/`unitat_explotaci`, `codi_estat_sequera_hidrol`/`estat_sequera_hidrol_gic`, `codi_estat_sequera_pluviom`/`estat_sequera_pluviom_tric`, `codi_municipi` (INE6)/`municipi`.
- **8.677 files** totals (tota la CIC); **una fila = un canvi d'estat per a un municipi en una data**.
- **Període 2021-01-01 → 2025-05-16** (cobreix tota la crisi 2023-24).
- Escala hidrològica completa (codis oficials del Pla de sequera): NORMALITAT `00004` · PREALERTA `00005` · ALERTA `00006` · EXCEPCIONALITAT `00007` · EMERGÈNCIA `00008`/II `00009` · PREEMERGÈNCIA `00120` · EMERGÈNCIA I `00121`. Segon eix **pluviomètric** (NORMALITAT/SEQUERA SEVERA/SEQUERA EXTREMA).

### La granularitat: **municipal real** (el "sí" honest)
El Berguedà és conca del **Llobregat** (conca interna) → el dataset **el cobreix sencer**: **31/31 municipis** hi són (verificat un a un, inclòs el cas límit Gósol `25100`). El `codi_municipi` és INE6; **`ine5 = codi_municipi[:5]`** casa exactament amb el `BERGUEDA_INE5` del package (`080229`→`08022` Berga, `251001`→`25100` Gósol). **Cada municipi pertany a una sola unitat d'explotació** (0 municipis amb >1 UE): Capçalera del Llobregat (06), Embassament del Llobregat (10) o Mig Llobregat (16).

→ **Diferència clau amb la lliçó supramunicipal de la contractació:** aquí NO cal el maneig comarcal. La font ja baixa a municipi, així que `ambit='municipal'` i `ine5` sempre vàlid. La **unitat d'explotació** (el nivell on l'ACA pren la decisió i propaga la Resolució) es **preserva com a traçabilitat**: `raw_id` = codi UE, i dins `objecte`. És informació supra valuosa per a la convergència, però el senyal ja arriba assignat al municipi.

### El rastre: connector `sequera.py` (398 events)
398 files del pilot → **398 events**. Normalització:
- `ine5 = codi_municipi[:5]`; `nom_muni` net del registre `BERGUEDA_INE5` (no del text de la font); `comarca='Berguedà'`; `ambit='municipal'`.
- `tipus_senyal='aigua_sequera'` (nou al vocabulari de `schema.py`; **distint** d'`aigua`, que és contractació de serveis d'aigua — aquí el senyal és la restricció declarada).
- `data = data_canvi_estat_sequera`, **`data_tipus='inici_vigencia'`** (la restricció entra en vigor amb la declaració).
- **`fase='realitzacio'`** (vegeu "Por qué" #1 — refinament respecte a la previsió).
- `font="Agència Catalana de l'Aigua (ACA)"`; `font_url` = URL del dataset (**mai NULL**).
- `import=NULL` (una declaració no té import); `cpv=NULL` (no aplica).
- `objecte` = text llegible amb tot el context: estat hidrològic + UE + estat pluviomètric.
- **`categoria='fet'`** (la declaració EXISTEIX) — `confianca` gradua la **inferència** de pressió.

Materialització a `data/events/events_sequera_bergueda.parquet` **via DuckDB** (mateix `events.py`, parametritzat amb `parquet_name`), **parquet separat** del de contractació. Raw + `_provenance.json` a `data/raw/sequera/` (gitignored).

**Anclajes verificados** (sobre el parquet materialitzat):
| estat hidrològic | confiança | events |
|---|---|---|
| NORMALITAT | 0.1 | 62 |
| PREALERTA | 0.4 | 137 |
| ALERTA | 0.6 | 101 |
| PREEMERGÈNCIA | 0.7 | 5 |
| EXCEPCIONALITAT | 0.8 | 83 |
| EMERGÈNCIA I | 0.9 | 10 |

- **Berga (UE Mig Llobregat)** explica la crisi sencera (16 canvis): normalitat→prealerta (oct-21)→alerta (jul-22)→**excepcionalitat (mai-23, el pic) mantinguda fins mai-24**→alerta→normalitat (mar-25). ✓
- 398 events · 31 municipis · període 2021-01-01→2025-05-16 · invariants tots nets (0 dups, 0 sense URL, 0 sense ine5, 0 sense data, 0 confiança fora de rang).

### Tests (`tests/test_sequera.py`, 43 passen en total al package)
Invariants del contracte reaplicats al rastre (offline, deterministes, aptes per CI) + específics de sequera: `event_id` únic amb prefix `seq_` · canvi només-pluviomètric és event distint · `data_tipus='inici_vigencia'` · `font_url` mai NULL · `ine5` derivat d'INE6 (cas Gósol) · `aigua_sequera`/`fet`/`realitzacio` · **confiança ordinal creixent amb la severitat** · robustesa a accents/majúscules · `import` NULL. El test del parquet codifica les àncores (31 municipis, tot municipal) com a assercions.

## Por qué — decisions de disseny que cal recordar

1. **`fase='realitzacio'`, no `reaccio` (refinament respecte a la meva entrada del 2026-06-02).** A l'entrada de la taula d'events vaig anotar provisionalment `fase='reaccio'` per a la sequera. Després de veure les dades ho he canviat a **`realitzacio`**: un canvi d'estat de sequera no *segueix* un fet passat (reacció) ni el *precedeix* (anticipació, com un contracte) — **és l'estat vigent contemporani**, descriu la pressió hídrica *mentre passa*. La declaració d'excepcionalitat de maig-23 ÉS la sequera de maig-23, no una reacció a ella. Frontera semàntica important per al motor de convergència, que creuarà senyals d'**anticipació** (contractació) amb senyals de **realització** (sequera).

2. **`confianca` ordinal per severitat (la frontera dada/inferència, adaptada a aquest rastre).** A contractació, `confianca` mesurava la força de l'evidència del *tema* (CPV vs paraula). Aquí el tema és cert (`aigua_sequera` sempre) — el que es gradua és **la força del senyal de pressió** que l'estat implica: NORMALITAT 0.1 (cap pressió, és la base) → EMERGÈNCIA II 1.0 (restricció màxima). **No és incertesa de la dada** (la declaració és sempre un FET): és quant *senyal de tensió hídrica* aporta. Ordinal i alineat amb l'escala oficial del Pla. Un estat no catalogat cau a 0.5 (no inventem severitat).

3. **`event_id` inclou els dos eixos (hidrològic + pluviomètric).** Verificat a l'històric de Berga: una mateixa data pot registrar un canvi **només pluviomètric** mantenint l'hidrològic (p.ex. 2022-01-28 i 2022-02-24, totes dues PREALERTA hidrològic, pluviomètric distint). Són files distintes a la font → events distints aquí. Si la clau només dugués (municipi, data, hidrològic), aquests col·lapsarien i perdríem transicions reals. `seq_` com a namespace → no col·lisiona amb els `con_` de contractació en una taula unificada futura.

4. **Parquet separat (`events_sequera_bergueda.parquet`), no fusionat.** `write_events_table` sobreescriu el parquet sencer; fusionar hauria obligat a re-llegir el de contractació (acoblament). Una font = una sortida (el patró del package). El motor de convergència (PR següent) llegirà tots dos `read_parquet` i operarà sobre la taula unificada — el contracte `EVENT_COLUMNS` és idèntic, així que la unió és trivial (`UNION ALL`).

## Honest boundaries (disciplina de Talaia)

- **El "sí" honest: granularitat municipal completa.** A diferència d'altres senyals d'aigua (la memòria notava "aigua-volum només comarcal"), l'**estat** de sequera SÍ baixa a municipi i cobreix els 31 del Berguedà. És el millor cas possible per al pilot. Ho dic clar perquè és un resultat fort, no un "ens conformem".
- **El `data` és la data del canvi, no la de fi de vigència.** La font és un **històric de transicions**, no d'intervals tancats: un estat val fins al canvi següent. La reconstrucció d'intervals ("quants dies va estar Berga en excepcionalitat") és feina del motor de convergència (ordenar per `data` dins de cada municipi). Aquí **no** ho fem: 1 fila = 1 event, fidelitat a la font. No invento dates de fi.
- **Eix triat = hidrològic.** El senyal de restricció/gestió (el que genera la Resolució de l'ACA amb mesures) és l'**hidrològic**; el pluviomètric és context meteorològic. L'`objecte` i el `confianca` es basen en l'hidrològic; el pluviomètric es **preserva** dins `objecte` (no es perd), però no condueix el senyal. Decisió explícita, revisable.
- **El `scope` del sidecar de procedència diu "(pilot: Castellar, Berga, Consell Comarcal)".** És text compartit hardcoded a `provenance.py` (pensat per a contractació). Per a sequera el "Consell Comarcal" no aplica (baixa a municipi). NO he tocat `provenance.py` per no alterar el comportament de contractació; el camp `note` del sidecar de sequera ja precisa "1 fila = 1 canvi d'estat (municipi × data)". Matís cosmètic, no de dades.
- **Mojibake de la font:** `unitat_explotaci`/`municipi` arriben amb `�` en alguns valors (pèrdua a l'origen). Els valors que **derivem** (`nom_muni` del registre, `comarca`) són nets; `objecte` conserva el text de la font (fidelitat). Mateix criteri que contractació.

## Recomanació per al motor de convergència (el següent pas)

Ara el cabal té **dos rastres amb temporalitats complementàries** sobre el mateix territori i clau (`ine5`):
- **Contractació** = senyal d'**anticipació** (què es prepara), amb pic estacional (turisme/cultura a Berga al maig, pre-Patum).
- **Sequera** = senyal de **realització** (la pressió hídrica vigent), continu, amb l'escala de severitat 2021-25.

**La hipòtesi de convergència a provar:** la **pressió turística/segona residència** (que infla la població real per damunt del padró — el nord de riusdegent) hauria de **co-ocórrer amb tensió hídrica**: els municipis-destí concentren consum d'aigua als mesos de més afluència. Disseny proposat:
1. **Unificar** els dos parquets (`UNION ALL` sobre `EVENT_COLUMNS`) → taula `events` única.
2. **Reconstruir intervals** de sequera per municipi (ordenar per `data`, l'estat val fins al canvi següent) → per a cada (municipi, mes) un nivell de severitat hidrològica (la `confianca` ja és l'escala numèrica).
3. **Creuar amb el senyal de contractació turística** (events `turisme_cultura_events`) i amb el model de 3 capes de Sondeig (pernocta/càrrega/turisme a `mart_municipi`): buscar municipis on **alta intensitat turística + alta severitat de sequera** coincideixen → candidats a "pressió hídrica amplificada per població invisible".
4. **Frontera honesta:** la sequera és **supramunicipal en origen** (es declara per UE; tots els municipis d'una UE comparteixen estat). Per tant **no discrimina entre municipis de la mateixa UE** — Berga i Castellar (UEs diferents: Mig Llobregat vs Capçalera) sí es distingeixen, però dos pobles de la mateixa UE no. La sequera aporta el **denominador de tensió de la zona**; la *variació* fina entre municipis l'han d'aportar els senyals municipals (contractació, residus, elèctric). Convé dir-ho perquè ningú llegeixi la severitat municipal com a mesura local independent.

## Pendiente

- [ ] **Motor de convergència** (PR següent): unificar els dos rastres + reconstruir intervals de sequera + creuar amb turisme. Definir la mètrica de co-ocurrència amb Talaia.
- [ ] **Extracció LLM** per refinar el calaix `altres` de contractació (segueix pendent del PR anterior).
- [ ] **Escala Catalunya:** el filtre de sequera (`PILOT_WHERE` de `sequera.py`) es parametritza igual que contractació (canviant `BERGUEDA_INE5`). A escala CAT, atenció: el dataset és **només Conques Internes** — les conques de l'Ebre (Pirineu de ponent, p.ex. la Val d'Aran) **no hi són** (les gestiona la CHE, no l'ACA). Un "no" honest a tenir present quan s'escali.
- [ ] **Integració semàntica:** afegir la font ACA a `semantic/metrics.yml` (`sources`) quan la capa madurri. NO he tocat `metrics.yml` (contracte de Talaia).
- [ ] **CI:** afegir `packages/signals` al job Python (ruff + pytest) quan s'obri (depèn del `TODO` de `ci.yml`, que NO toco).

## Enlaces
- `packages/signals/datapoble_signals/sequera.py` (connector `i5n8-43cw` → events)
- `packages/signals/datapoble_signals/schema.py` (afegit `aigua_sequera` a `TIPUS_SENYAL`)
- `packages/signals/datapoble_signals/config.py` (font `sequera` a `SOURCES`)
- `packages/signals/datapoble_signals/__main__.py` (CLI: `python -m datapoble_signals sequera`)
- `packages/signals/tests/test_sequera.py` + `tests/fixtures_sequera.py` (invariants + àncores)
- `data/events/events_sequera_bergueda.parquet` (398 events; versionat)
- `semantic/metrics.yml` (contracte de Talaia; **no tocado**)
