# signals · Cabal — el cabal (pilar 2)

**Intel·ligència territorial des dels rastres administratius i digitals.** Quan un
fenomen no té dataset net, el seu *rastre* sí que existeix: algú ha hagut de
**contractar** el servei, publicar un edicte, declarar una restricció. Aquesta
capa normalitza aquests rastres a una taula única d'**events** (una fila per
senyal), amb traçabilitat sempre i la frontera **dada/inferència** explícita.

> És el principi dels *kg de residus* (proxy de població fantasma) generalitzat a
> qualsevol rastre.

## Scope

La **taula `events`** (el contracte de la capa) + **dos rastres independents**:
**contractació** (Socrata `ybgg-dgi6`) i **sequera** (Socrata `i5n8-43cw`, ACA).
**No** el motor de convergència (PR següent).

| peça | dataset | accés | loader | events |
|---|---|---|---|---|
| **Contractació** (contractes menors) | Socrata `ybgg-dgi6` | analisi.transparenciacatalunya.cat | `requests` | 1.295 |
| **Sequera** (estat de sequera ACA) | Socrata `i5n8-43cw` | analisi.transparenciacatalunya.cat | `requests` | 398 |

**Pilot:** el Berguedà — Berga (`08022`), Castellar de n'Hug (`08052`) i el
**Consell Comarcal del Berguedà** (l'òrgan supramunicipal) per a la contractació;
els **31 municipis** del Berguedà per a la sequera (la font baixa a municipi).

## El contracte: la taula `events`

Una fila = un senyal. Columnes mínimes (vegeu `schema.py` per a la llista completa
i els vocabularis controlats):

| columna | què és |
|---|---|
| `event_id` | id estable i únic (hash determinista; els **lots** són events distints) |
| `ine5` | codi INE5; **NULL si `ambit` ≠ municipal** |
| `nom_muni` | municipi (net, del registre) o òrgan |
| `ambit` | `municipal` · `comarcal` · `supramunicipal` |
| `comarca` | comarca del senyal |
| `data` / `data_tipus` | data principal + què representa (`adjudicacio`/`publicacio`/`anunci`) |
| `font` / `font_url` | qui contracta · URL traçable (**mai NULL**) |
| `tipus_senyal` | tema (taxonomia CPV+paraules) — **inferència** |
| `fase` | `anticipacio` (un contracte és anticipació) |
| `objecte` | descripció de l'objecte del contracte |
| `import` | € sense IVA (≥ 0) |
| `categoria` | `fet` (el contracte existeix) vs `inferencia` |
| `confianca` | 0..1 sobre el `tipus_senyal` inferit |

**Dada vs inferència, explícit:** el contracte **existeix** → `categoria='fet'`.
Però què *implica* (la pressió que el `tipus_senyal` codifica) és **inferència**,
graduada per `confianca`.

## La lliçó: micromunicipi → supramunicipal (crèdit a Talaia)

Els òrgans comarcals/supra **no són un municipi**. El Consell Comarcal del
Berguedà porta `codi_ine10 = 8101410007` → `[:5]` = `81014`, que és un **codi de
comarca, no de municipi**. Per això:

- detectem l'àmbit pel **nom de l'òrgan** (no pel codi),
- i marquem `ambit='comarcal'`, `ine5=NULL`, `comarca='Berguedà'`.

*Un contracte comarcal és senyal per als micromunicipis de la comarca.* Els
pobles petits **no contracten els seus serveis**: Castellar té **23 contractes i
cap de turisme** real — la seva intensitat turística (Tren del Ciment, Museu del
Ciment, ~50.000 visites/any a 166 habitants) **no apareix com a contractació
pròpia**; viu al Consell (**695 contractes**). Marquem `ambit` perquè la
**convergència** (PR futur) pugui repartir el senyal supra als micromunicipis.

## Com executar

```bash
cd packages/signals
python -m datapoble_signals contractacio   # descarrega + normalitza + escriu events
python -m datapoble_signals sequera         # estat de sequera ACA → events
python -m datapoble_signals all             # tots dos rastres
pytest -q                                   # tests (offline; el parquet és opcional)
```

Requereix xarxa (API pública, sense autenticació). Idempotent: re-córrer
sobreescriu el parquet i la raw; `event_id` és estable entre execucions.

## Sortida

```
data/raw/contractacio/  contractacio_raw.json + _provenance.json   (gitignored; 1 fila = 1 contracte)
data/raw/sequera/        sequera_raw.json + _provenance.json        (gitignored; 1 fila = 1 canvi d'estat)
data/events/             events_bergueda.parquet                    (versionat; contractació, 1 fila = 1 event)
data/events/             events_sequera_bergueda.parquet            (versionat; sequera, 1 fila = 1 event)
```

Cada rastre escriu el seu **propi parquet** (mateix contracte `EVENT_COLUMNS`).
El motor de convergència (PR futur) els unirà (`UNION ALL`) en una taula única.

El parquet es materialitza **via DuckDB** (`data` → DATE; `import`/`confianca` →
DOUBLE) — el cast és explícit i reproduïble, com a la capa transform de Sondeig.

## Taxonomia `tipus_senyal` (heurística verificada per Talaia)

Senyal fort = **CPV** (codi oficial de l'objecte). Sense CPV → fallback per
**paraules clau** sobre l'objecte. `confianca`: `0.9` (CPV) · `0.6` (paraula) ·
`0.3` (`altres`).

| `tipus_senyal` | CPV (família) |
|---|---|
| `neteja_residus` | `90…` |
| `aigua` | `6512/6513`, `41/45…` aigua |
| `mobilitat_via` | `4523…`, `6371…`, `6010…` |
| `turisme_cultura_events` | `7995…`, `92…` |
| `seguretat_socorrisme` | `7971…`, `7525…`, `7561…` |
| `altres` | cap match |

## El rastre de sequera (ACA, `i5n8-43cw`)

Una **declaració/canvi d'estat de sequera** de l'Agència Catalana de l'Aigua per a
un municipi en una data és un **rastre administratiu net**: l'ACA declara una
restricció → senyal de **pressió hídrica** (que convergeix amb el turisme/segona
residència). Font: «Estat de sequera per unitats d'explotació i municipis a les
Conques Internes de Catalunya». **398 events** al Berguedà, **2021-01-01 →
2025-05-16**, escala hidrològica completa (normalitat → prealerta → alerta →
preemergència → excepcionalitat → emergència).

Diferències de normalització respecte a la contractació:

| camp | contractació | sequera |
|---|---|---|
| `ambit` | municipal **o** comarcal (la lliçó supra) | **sempre municipal** (la font baixa a municipi: 31/31 del Berguedà) |
| `data_tipus` | `adjudicacio`/`publicacio`/`anunci` | `inici_vigencia` (la restricció entra en vigor) |
| `fase` | `anticipacio` (un contracte precedeix el fet) | `realitzacio` (l'estat declarat és contemporani) |
| `tipus_senyal` | heurística CPV+paraules | `aigua_sequera` (fix) |
| `confianca` | força de l'evidència del tema (CPV vs paraula) | **força del senyal de pressió** segons severitat (normalitat 0.1 → emergència II 1.0) |
| `import` | € sense IVA | NULL (una declaració no en té) |

`categoria='fet'` igualment (la declaració EXISTEIX); el que *implica* (la pressió)
és inferència, graduada per `confianca`. La **unitat d'explotació** (el nivell on
l'ACA pren la decisió i la propaga) es preserva a `raw_id` i dins `objecte`.

## Honest boundaries (disciplina de Talaia, innegociable)

- **Corre de veritat:** el connector descarrega `ybgg-dgi6`, normalitza 1.295
  contractes a events, escriu procedència i materialitza el parquet via DuckDB.
  **Àncores verificades** contra l'experiment de Talaia: Consell **695**, Berga
  **577**, Castellar **23**; pic de turisme/cultura a Berga al **maig (54)**;
  Castellar **sense turisme** propi (1 hit feble).
- **La classificació és heurística.** ~**48%** dels contractes **no porten CPV** a
  la font → el fallback és per paraules clau (sorollós) i el calaix **`altres` és
  gran a propòsit** (~38% dels events). Preferim no inventar tema. **El
  refinament fi és feina de l'LLM** (PR posterior) — no està fet aquí.
- **El mojibake és de la font.** `ybgg-dgi6` emet **algunes** files de text lliure
  (`objecte`/`denominacio`) amb el caràcter de reemplaçament `�` —pèrdua a
  l'origen, irrecuperable—; la majoria de camps (inclòs el nom de l'òrgan) arriben
  nets en UTF-8. Els valors que **derivem nosaltres** (`nom_muni` del registre,
  `comarca`) són sempre nets; `objecte`/`font` conserven el text tal com ve
  (fidelitat). No és un bug del nostre fetch.
- **Data:** preferim `data_adjudicacio_contracte`; si l'expedient no està adjudicat
  (fases obertes) caiem a publicació/anunci i ho marquem a `data_tipus`. **2 de
  1.295** events (consultes pre-mercat) queden sense cap data.

## Fora de scope (PRs següents)

El **motor de convergència** (unir els dos rastres, repartir el senyal comarcal
als micromunicipis, reconstruir intervals de sequera, creuar amb el turisme);
l'extracció **LLM** (OpenRouter) per a fonts messy i per refinar `altres`;
l'**escala Catalunya** (atenció: el dataset de sequera és **només Conques
Internes** — les conques de l'Ebre les gestiona la CHE, no l'ACA).

## Estructura

- `schema.py` — el contracte: columnes d'`events` + vocabularis controlats.
- `taxonomy.py` — heurística CPV + paraules clau → `tipus_senyal` + `confianca`.
- `municipis.py` — INE5 del Berguedà + detecció d'òrgans supra (la lliçó).
- `contractacio.py` — connector `ybgg-dgi6` → normalització a events.
- `sequera.py` — connector `i5n8-43cw` (ACA) → events de sequera.
- `events.py` — escriptura de la taula `events` a parquet via DuckDB.
- `socrata.py` / `config.py` / `provenance.py` — client SODA, registre de fonts,
  sidecar de procedència (mateix patró que `packages/ingestion`).
