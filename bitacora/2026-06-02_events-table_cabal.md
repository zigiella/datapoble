# Taula d'events + connector de contractació — primera oleada Cabal (el cabal, pilar 2)

**Fecha:** 2026-06-02
**Autora:** Cabal
**Para:** Talaia (review)
**Tema:** estrenar el pilar 2 (intel·ligència territorial des de rastres administratius): el **contracte de la capa d'events** + **UN rastre** (connector de contractació `ybgg-dgi6`), pilot Berguedà. NO el motor sencer.
**Status:** avance / handoff

## Contexto

El pilar 2 (*el cabal*) generalitza el principi dels **kg de residus** (proxy de població fantasma): quan un fenomen no té dataset net, el seu *rastre* administratiu sí que existeix. Algú ha hagut de **contractar** el servei. Aquesta entrada documenta el **model d'event** (el contracte de la capa) i el primer rastre que el produeix: la contractació pública. Paquet nou `packages/signals`, en paral·lel a `packages/ingestion` (Sondeig) i amb el mateix estil (socrata/config/provenance).

## Qué hicimos / decidimos

### El contracte: la taula `events` (`schema.py`)
Una fila = un senyal. Columnes mínimes del brief + traçabilitat addicional, en ordre canònic fix (`EVENT_COLUMNS`). Vocabularis controlats: `ambit` (municipal/comarcal/supramunicipal), `fase` (anticipacio/realitzacio/reaccio), `categoria` (fet/inferencia), `tipus_senyal` (6 temes), `data_tipus`. La idea: tota font futura del cabal (sequera, edictes…) normalitza a **aquesta** taula → la convergència opera sobre una taula única sense saber d'on ve el senyal.

**Dada vs inferència, explícit (el cor de la disciplina):** el contracte EXISTEIX → `categoria='fet'`. El que *implica* (la pressió que codifica el `tipus_senyal`) és **inferència**, graduada per `confianca`.

### El rastre: connector de contractació (`contractacio.py`, dataset `ybgg-dgi6`)
1.295 contractes del pilot → 1.295 events. Normalització:
- `ine5 = codi_ine10[:5]` **si** l'òrgan és municipal; `nom_muni` net del registre INE5; `font = nom_organ`.
- `fase = anticipacio` sempre (un contracte és anticipació). `data = data_adjudicacio_contracte`; `font_url = enllac_publicacio.url`; `import = import_adjudicacio_sense` (≥0).
- `tipus_senyal` per **heurística CPV + paraules clau** (`taxonomy.py`, verificada per Talaia): neteja/residus `90…`, aigua, mobilitat/via `4523…`/`6371…`, turisme/cultura/events `7995…`/`92…`, seguretat/socorrisme `7971…`/`7525…`, altres.
- `confianca`: **0.9** (match per CPV) · **0.6** (només paraula clau) · **0.3** (`altres`). Marca el grau d'inferència.

Materialització a `data/events/events_bergueda.parquet` **via DuckDB** (cast explícit `data→DATE`, `import/confianca→DOUBLE`). Raw + `_provenance.json` a `data/raw/contractacio/` (gitignored).

**Anclajes verificados** (coinciden amb l'experiment de Talaia):
| òrgan | events | àncora Talaia |
|---|---|---|
| Consell Comarcal del Berguedà (`comarcal`, ine5=NULL) | **695** | ~695 ✓ |
| Berga (`08022`) | **577** | ~577 ✓ |
| Castellar de n'Hug (`08052`) | **23** | ~23 ✓ |

- **Berga, turisme/cultura per mes:** pic clar a la **primavera, maig = 54** (anchor de Talaia ~58; la forma —pic de Corpus/Patum— és la correcta). ✓
- **Castellar: cap turisme propi** (1 hit feble per paraula clau). Dominen `mobilitat_via` (13, accés) i `aigua` (3). ✓

### La lliçó (micromunicipi → supramunicipal) — crèdit a Talaia
**Hallazgo que cal deixar escrit:** el Consell Comarcal porta `codi_ine10 = 8101410007` → `[:5]` = **`81014`**, que **no és un INE5 de municipi** (és un codi de comarca). Si haguéssim derivat `ine5` cegament del prefix, hauríem inventat un municipi fantasma `81014` i el join amb `mart_municipi` (Sondeig) hauria fallat en silenci.

**Decisió:** la detecció d'`ambit` es fa pel **nom de l'òrgan** (no pel codi). Òrgan comarcal → `ambit='comarcal'`, `ine5=NULL`, `comarca='Berguedà'`. Invariant garantit i testejat: *`ine5` vàlid **o** `ambit≠municipal`*.

**Per què importa (el senyal de veritat):** *un contracte comarcal és senyal per als micromunicipis de la comarca*. Els pobles petits **no contracten els seus serveis**. Castellar (166 hab, ~50.000 visites/any entre Tren del Ciment i Museu) té **23 contractes i cap de turisme** — la seva pressió turística és invisible a la seva pròpia contractació; **viu del Consell** (695 contractes). Per això marquem `ambit`: la **convergència** (PR futur) ha de poder **repartir** el senyal supramunicipal als micromunicipis de la comarca. Sense aquesta marca, Castellar semblaria un poble sense vida turística — fals.

### Tests (`tests/test_events.py`, 23 passen)
Els 5 invariants del brief, offline sobre fixtures (deterministes, aptes per CI) + reaplicats al parquet si existeix:
`event_id` únic (lots inclosos) · dates parsejables · cap event sense `font_url` · `ine5` vàlid **o** `ambit≠municipal` · imports no negatius. A més: vocabularis, taxonomia (CPV vs keyword vs altres), lògica supra, fallback de data i de `font_url`. El test del parquet **codifica les àncores** (695/577/23) com a assercions.

## Por qué — decisions de disseny que cal recordar

1. **`event_id` inclou `numero_lot`.** Sense el lot, 79 events col·lapsaven: són **lots** d'una mateixa licitació (mateix expedient/objecte/data, diferent `descripcio_lot`/pressupost) — transport escolar i obres de camins del Consell. Cada lot és un sub-contracte distint → un senyal distint → ha de tenir el seu id. Verificat fila a fila.
2. **Fallback de data.** El brief diu `data = data_adjudicacio_contracte`, però 210 expedients no estan adjudicats (fases obertes). Caiem —en ordre semàntic— a `data_publicacio_contracte` → `data_publicacio_anunci` (la intenció de contractar feta pública: també anticipació) i ho marquem a `data_tipus`. Resultat: **1.293/1.295 events datats** (els 2 sense data són consultes pre-mercat). Cap data inventada.
3. **Pur-`requests`, no dlt.** El connector fa normalització pesada per fila (CPV multivalor, detecció supra, fallback de data) que no encaixa net al model de `dlt.resource` de Sondeig; produïm una **única taula tipada via DuckDB**, que és el patró de `transform`. La raw es desa igualment amb procedència.

## Honest boundaries (disciplina de Talaia)

- **La classificació és heurística.** ~**48%** dels contractes **no porten CPV** a la font; el fallback per paraules clau és sorollós. El calaix **`altres` és gran a propòsit** (489 events, ~38%): preferim no inventar tema. **El refinament fi és feina de l'LLM** (PR posterior, fonts messy) — no està fet aquí. Ho dic clar perquè ningú llegeixi `altres` com a "res rellevant".
- **El mojibake és de la font.** `ybgg-dgi6` emet **algunes** files de text lliure (`objecte`/`denominacio`) amb `�` (pèrdua a l'origen, irrecuperable: el JSON ja arriba així en UTF-8 vàlid); la majoria de camps —inclòs el nom de l'òrgan— arriben nets. Els valors que **derivem** (`nom_muni`, `comarca`) són sempre nets; `objecte`/`font` conserven el text de la font (fidelitat). No és un bug nostre de fetch (ho vaig confirmar inspeccionant els bytes: `Berguedà` = `…c3a0`, no `efbfbd`).
- **Traçabilitat sempre:** cada event amb `font_url`; si falta l'enllaç, cau a la URL del dataset (mai NULL). Testejat.

## Pendiente

- [ ] **Motor de convergència** (PR següent): repartir el senyal `comarcal`/`supramunicipal` als micromunicipis de la comarca (el `ambit` ja està marcat per a això). Definir la regla de repartiment amb Talaia (uniforme? ponderat per població/residus?).
- [ ] **Connector de sequera** (DOGC/ACA): rastre de restriccions → events amb `data_tipus='inici_vigencia'`, `fase='reaccio'`. L'esquema ja ho preveu.
- [ ] **Extracció LLM** (OpenRouter) per a fonts messy i per **refinar `altres`** (la classificació fina dels 489 sense CPV).
- [ ] **Escala Catalunya:** el filtre del pilot es parametritza canviant `PILOT_WHERE`/`BERGUEDA_INE5`. A escala CAT caldrà el registre INE5 complet (es pot reutilitzar el de Sondeig) i, per als òrgans supra, un catàleg de comarques per a `comarca_from_organ`.
- [ ] **Integració semàntica:** quan la capa madurri, afegir les fonts del cabal a `semantic/metrics.yml` (`sources`) i decidir si `events` esdevé una entitat del catàleg. No he tocat `metrics.yml` (és el contracte de Talaia).
- [ ] **CI:** afegir `packages/signals` al job Python (ruff + pytest) quan Sondeig obri el seu (depèn del `TODO` de `ci.yml`).

## Enlaces
- `packages/signals/datapoble_signals/schema.py` (el contracte d'event)
- `packages/signals/datapoble_signals/contractacio.py` (connector `ybgg-dgi6`)
- `packages/signals/datapoble_signals/taxonomy.py` (CPV + paraules → tipus_senyal)
- `packages/signals/datapoble_signals/municipis.py` (INE5 Berguedà + detecció supra — la lliçó)
- `packages/signals/datapoble_signals/events.py` (escriptura via DuckDB)
- `packages/signals/tests/test_events.py` (els 5 invariants + àncores)
- `data/events/events_bergueda.parquet` (1.295 events; versionat)
- `semantic/metrics.yml` (contracte de Talaia; **no tocado**)
