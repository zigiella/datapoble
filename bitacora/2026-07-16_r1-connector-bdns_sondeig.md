# R1 · Connector BDNS → fitxa de subvenció (contracte C3)

**Fecha:** 2026-07-16
**Autora:** Sondeig (dades/pipeline)
**Para:** Talaia (review/merge, guardiana de main)
**Tema:** primer connector del radar de subvencions: ingesta BDNS normalitzada al contracte C3, amb fixtures reals arxivades i CI 100% offline.
**Status:** fet, verificat en viu / **3 decisions que necessiten la teva ratificació**

## Contexto
Tasca R1 de `docs/ajuntaments/tasques-especificades.md` (barrera ▶️ verificada al tip d'`origin/main`, commit `3df0af1`: `next.md` diu «TRET DE SORTIDA DONAT PER BEA» i l'spec «EN MARXA»). Contractes vinculants: **C3** (la fitxa, la clau d'identitat, la porta humana) i **C4 §2** (les fixtures són candidates al banc). Dial: **una tasca i parar** → D1 no s'ha tocat.

## Què he fet
- `packages/signals/datapoble_signals/subvencions_bdns.py` — connector: client amb **fallback dels 4 miralls** + backoff + User-Agent identificat, batch diari educat, normalització a C3, clau d'identitat i dedupe.
- `schema.py` — contracte germà `SUBVENCIO_COLUMNS` + vocabularis `ESTATS_SUBVENCIO` / `AMBITS_SUBVENCIO` (taula pròpia, **no** `EVENT_COLUMNS`: una convocatòria muta i acumula procedències; un event és immutable).
- `config.py` — alta de la font al registre `SOURCES` + `data/subvencions/`.
- `tests/fixtures/bdns_convocatories.json` — **26 convocatòries reals arxivades** (captura literal, amb l'avís legal de la font); `tests/fixtures_bdns.py` (loader) i `tests/test_subvencions_bdns.py` (**39 tests, 100% offline**).
- `.github/workflows/ci.yml` — els tests de R1 **corren a CI** (abans `signals` només es lintava; cap test seu s'executava).

## Verificación (àncores mesurades EN VIU, no llegides de documentació)
- ⚠️ **La trampa de les regions és REAL i pitjor del que deia l'spec:** finestra 01/01–30/06/2026, `regiones=49` (Catalunya sola) → **867**; `regiones=49,50,51,52,53` → **6.057**. La pare sola es menja el **86%** (l'spec estimava ~3/4). L'API declara l'arbre (`/api/regiones`: 49 té fills 50-53) i **no l'aplica al filtre**. Ids verificats un a un.
- **Dates:** `dd/MM/yyyy` a la petició confirmat; l'ISO → **HTTP 400**.
- **4 miralls** verificats: mateix `totalElements` (642.986) → fallback viable.
- **5 tipus de beneficiari genèrics**, cap «ajuntament» (confirmat a `/api/beneficiarios`): el filtre fi és de R2, tal com deia l'spec.
- **End-to-end contra l'API real** (dia 2026-07-14): 52 convocatòries, 52/52 amb `id_bdns`, cap `font_url` NULL, 52 claus úniques, els 3 àmbits presents.
- **L'`enllac` verificat AL NAVEGADOR**, no per HTTP: el portal és una SPA d'Angular que torna **200 amb el mateix esquelet per a qualsevol ruta, fins i tot inventada** (`/GE/es/tonteria/absurda` → 200). Un 200 no prova res; el que ho prova és que la pàgina renderitza la convocatòria correcta (comprovat amb la 919221: Esparreguera, 3.500 €, ES511).
- CI local: `ruff check packages/transform packages/ingestion packages/signals` → **All checks passed**; `pytest packages/signals/tests/test_subvencions_bdns.py` → **39 passed**.

## Esmenes a l'spec (el que he trobat que no quadrava)
1. **`vpd=GE` NO és obligatori** a `busqueda`: sense ell, HTTP 200 i el mateix `totalElements`. S'envia igualment (convenció del portal), però el connector no hi confia.
2. **El mapa de camps de l'spec és el del DETALL, no el de la cerca.** Són dos esquemes: `busqueda` torna la fila **plana** amb `numeroConvocatoria` i `nivel1/2/3`; la fitxa (`?numConv=`) torna `codigoBDNS` i `organo.*`. Cal cridar les dues (`numeroConvocatoria == codigoBDNS`, verificat).
3. **`urlBasesReguladoras` no és una URL:** és text lliure («Convenio», «www.labisbal.cat» sense esquema; 3/26 a les fixtures). L'`enllac` canònic és la fitxa del portal.
4. **Els paràmetres desconeguts s'ignoren en silenci** (`abierto=true` no filtra res i no dona error) → una errata en un filtre no peta: retorna dades sense filtrar. Per això la trampa de regions es guarda amb un test que **compta**, no que miri codis HTTP.

## ⚠️ Decisions que necessiten la teva ratificació (no les he preses en silenci)
1. **He inclòs l'àmbit ESTATAL a la ingesta** (`regiones=1`), que el llistó de R1 no enumera. Mesurat: l'estatal són **1.275 convocatòries més** i el conjunt és **disjunt** del català (6.057 + 1.275 = 7.332 **exactes**); al batch real d'un dia van ser **12 de 52 (23%)**. Excloure-les faria invisibles les convocatòries ministerials a què un ajuntament SÍ es pot presentar → **FN de sistema**, el pecat greu de C4 §1; i C3 §3 preveu `estatal` com a valor de `territori` al perfil, que no podria casar mai. L'asimetria mana: ingerir de més ho arregla R2; ingerir de menys, no ho arregla ningú. **Girar-ho és una línia** (`REGIONS_R1_SPEC`). Si ho vols com deia l'spec, digues-ho i ho canvio.
2. **`termini: NULL` és AMBIGU i C3 potser necessita esmena.** De les 26 fixtures: només **8** porten data de fi; **11** no porten data però sí `textFin` en **prosa** («Finaliza el 15 de septiembre de 2026», «15 Dies Hàbils», «Vint dies a partir de l'endemà de la publicació al BOPB»); **7** no porten res. C3 només té `termini: date|NULL` → NULL barreja «no hi ha termini» amb «el termini existeix, en lletres». **No he escrit cap parser de prosa**: seria inferència servida com a fet, justament al camp que diu si s'hi és a temps. Si R2/R4 llegeixen NULL com «sense termini», es prendrà una decisió sobre una ambigüitat. Decideix tu: camp nou a C3, o doctrina explícita.
3. **La trampa de codis de C3 §5 no és aplicable a R1, i ho he verificat en comptes de suposar-ho:** la BDNS **no publica cap codi municipal** (ni INE ni cadastral) — el gra més fi és la província (NUTS3). R1 no casa cap municipi, així que no pot triar-ne malament cap. El test que hi he posat és la **guarda** que ho manté cert (si algun dia la fitxa emetés un codi, cau) + les àncores 08052/08166/`081666[:5]` perquè R2 les hereti verificades.

## Fronteres honestes del connector (el «no» com a resposta)
- `cofinancament` → **sempre NULL**: la BDNS no publica cap %.
- `estat` → només `oberta`/`tancada`; **mai `anul·lada`** (la font no té camp d'anul·lació: corregeix i esborra sense marcar).
- `ambit_territorial` → només `estatal`/`CAT`/`provincia` (la font no baixa de NUTS3; `comarca`/`municipi` els portarà CIDO a R5).
- `estat` deriva d'**`abierto`** (el flag de la font), no del termini: 8 de 26 fixtures reals porten `abierto=false` **amb termini futur** (convenis de concessió directa). Deduir-lo del termini diria «oberta» a convocatòries a què ningú es pot presentar.
- La procedència **no menteix sobre l'abast**: `write_provenance` posava per defecte l'scope del pilot de contractació («Castellar, Berga, Consell Comarcal»), fals aquí; se sobreescriu amb l'abast real (Catalunya + estatal). Amb test.

## Pendiente / handoffs
- [ ] **Talaia:** review/merge + ratificar les 3 decisions de dalt.
- [ ] **⚠️ Reportat, NO tapat (anterior a R1, fora del dial):** `packages/signals/tests/test_licitacions.py::test_real_parquet_cobertura_i_conservacio` és **vermell al tip de `main`** sobre dades versionades: la **conservació de l'import no quadra** (`sum(import_assignat)` = 11.744.503,22 vs `sum(import_total)` = 19.419.168,11 → **7,67 M€ de diferència**, amb tolerància de 5 €). No és cosa meva i no l'he tocat; per això el pas de CI que he afegit s'acota al fitxer de R1. **La resta de la suite de `signals` no ha estat mai al CI** (només s'hi lintava): cablejar-la sencera + esbrinar aquest desquadre = tasca pròpia, teva de prioritzar.
- [ ] **R2 (jo, proper latido si el dial ho permet):** filtre dur + perfil `config/municipis/*.yaml`. **El perfil NO és de R1**: el llistó de R1 no el demana i C3 §3 el lliga al filtre (R2). No l'he creat per no inflar l'abast.
- [ ] **C4:** les 26 fixtures són candidates al banc; cap porta etiqueta `golden` (l'etiquetatge és de Bea, a mà, mai d'un model).

## Enlaces
- `packages/signals/datapoble_signals/subvencions_bdns.py` (les àncores viuen al docstring)
- `packages/signals/tests/test_subvencions_bdns.py` · `tests/fixtures/bdns_convocatories.json`
- `docs/ajuntaments/C3-subvencions-perfil.md` · `C4-avaluacio-radar.md` · `docs/ajuntaments/tasques-especificades.md`

— Sondeig
