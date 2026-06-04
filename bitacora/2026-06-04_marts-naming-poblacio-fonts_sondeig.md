# Reconciliació nom marts + inventari de fonts "població real vs padró" — Sondeig

**Fecha:** 2026-06-04
**Autora:** Sondeig
**Para:** Talaia (review/merge) · Brúixola (desbloqueig)
**Tema:** (A) treure el sufix `_bergueda` del nom canònic dels marts perquè el warehouse de `packages/ai` els trobi; (B) inventari honest i verificat de proxies de presència humana per a l'indicador "població real vs padró" (només groundwork, sense l'estimació final).
**Status:** avance / handoff

## Contexto
Dos frentes. (A) La capa IA carregava fixtures perquè el warehouse espera
`data/marts/mart_municipi.parquet` / `mart_electoral.parquet` però el pipeline els
escrivia amb sufix de pilot (`_bergueda`) → Brúixola corria amb dades de mentida.
(B) Talaia vol l'indicador estrella població-real; abans de calcular res cal saber
**quines fonts de presència existeixen de veritat** amb granularitat municipal.

## Qué hicimos / decidimos

### TASCA A · nom canònic dels marts (desbloqueja Brúixola)
El sufix `_bergueda` només vivia al **post_hook `COPY`** dels dos models i a
`verify_marts.py` (els models dbt ja es diuen `mart_municipi`/`mart_electoral`, i el
contracte `semantic/metrics.yml` ja els referencia així via `table:`). El warehouse
deriva els noms de taula del catàleg (`catalog.tables()`), o sigui del contracte →
**el nom canònic correcte és sense sufix**. El sufix de pilot no ha d'anar al nom: la
mart es clava per `ine5` i escala a Catalunya canviant el filtre `comarca`, no el nom.

Canvis (cantó net, sense tocar `packages/ai`):
- `mart_municipi.sql` / `mart_electoral.sql`: post_hook `COPY … TO '…/mart_municipi.parquet'` (sense `_bergueda`).
- `verify_marts.py`: llegeix `mart_municipi.parquet`.
- `git mv` dels dos parquets versionats (contingut idèntic, 31 files c/u) als noms canònics.
- README transform actualitzat.

**Verificat end-to-end:**
- `verify_marts.py` → OK (31 munis, ancoratges Castellar/Berga, Spearman(IETR,kg_hab_any)=0,869).
- Warehouse de `packages/ai` (carregat amb el catàleg real) → `using_fixture={'mart_municipi':False,'mart_electoral':False}`, respon `SELECT count(*) FROM mart_municipi` = 31, Castellar (08052) `IETR_rank`=1. **Ja NO cau a fixtures.**
- `dbt parse` net.

> Nota per a Talaia (no ho he tocat, és de Brúixola): a `packages/ai/README.md`
> (secció "Pending") hi ha una línia que diu que els marts `_bergueda` no els recull
> el warehouse. Amb aquest PR ja **sí** els recull (renombrats). Cal actualitzar
> aquella nota a `packages/ai/README.md`, però és el seu fitxer — ho deixo a la teva
> validació amb Brúixola, no l'he editat.

### TASCA B · inventari de fonts població real vs padró
Lliurable: **`docs/poblacio-real-fonts.md`** — taula per proxy (disponible? ·
granularitat ine5? · endpoint · cobertura/latència · llicència · com mapeja a
presència) + recomanació. **NO** conté l'estimació ni la reclamació (és síntesi teva).

Verificat **en viu** (API SODA, 2026-06-04). Troballes:

**Sí, municipal i viables:**
- **Residus `69zu-w48s`** (ja ingerit): `codi_municipi`=ine5, **2000–2024**, té
  `generaci_residus_municipal`, `kg_hab_any`, `kg_hab_dia`. Cornerstone — ja és
  `kg_hab_any` a la mart. És el proxy més directe de càrrega física real.
- **Consum elèctric `8idm-becu`** (ICAEN) — **la troballa nova**. `cdmun`=ine5,
  **2013–2024**, sectors inclou `USOS DOMÈSTICS`. Clau: el sector domèstic
  **sobreviu al secret estadístic fins i tot a Castellar (166 hab)** (sèrie sencera),
  mentre que industrial/construcció surten NULL amb `observacions='Dada subjecta a
  secret estadístic'`. Senyal independent de residus → triangula.
- **Padró Idescat EMEX** (ja el tenim): el **denominador** oficial, no un proxy.

**No (o limitat) — els "no" honestos:**
- **Pernoctacions/EOH** → només **marca turística "Pirineus" / comarca**; Berga i
  Castellar no surten a municipi. ❌ per al pilot.
- **Taxa turística/IEET** → el dataset municipal `q4sr-68c3` **exclou Berga i
  Castellar** (cauen a "Resta"); només comarca `2nmt-74sj`. ⚠️
- **Aigua (volum)** → consum només **per comarca** (`2gws-ubmt`, portal ACA). El
  dataset municipal de l'ACA al portal obert (`i5n8-43cw`) és **estat de sequera**
  (categòric), **no litres**. Volum municipal → no obert sense conveni. ⚠️/❌
- **IMD `xsvx-ym46`** → per **estació d'aforament**, no municipi; ~3 estacions toquen
  el corredor del Berguedà; sèrie ~2017-2022. Proxy de corredor, no municipal. ⚠️
- **Tren (rodalia)** → inexistent al pilot; l'únic "tren" és el Tren del Ciment
  (turístic, nota de premsa, Castellar). ❌ com a sèrie.
- **Mòbil INE** → Castellar es dilou en cel·la gran. ❌ municipal fiable.
- **Visitants equipaments** (Museu/Tren del Ciment) → no API, però **ancoratge dur**
  d'excursionisme a Castellar (~50.000 visites/any vs 166 hab). Calibració, no pipeline.

**Recomanació (els 3):** residus (`69zu-w48s`) + elèctric domèstic (`8idm-becu`) +
padró (EMEX) com a denominador; visitants d'equipaments com a ancoratge de Castellar.

**Stub opcional creat** (no cablejat a `all`): `packages/ingestion/.../icaen_consum.py`
(dataset `8idm-becu`), + entrada a `config.SOURCES`. Verificat que importa i que **NO**
està al runner `all` (segueix sent stub fins que validis l'indicador). No hi ha model
dbt encara — això vindrà al PR de l'indicador.

## Por qué
- (A) El nom de pilot a l'artefacte és deute tècnic que es propaga: a escala Catalunya
  el sufix seria fals. Posar el nom canònic ara = el warehouse i tota la cadena
  funcionen sense excepcions especials, i l'escalat només toca el filtre `comarca`.
- (B) Un inventari amb "no" honestos val tant com els "sí": evita que construïm
  l'indicador sobre fonts que **semblen** municipals i no ho són (EOH, taxa, aigua). La
  parella residus+elèctric són dos senyals físics independents → el *gap* és defensable.

## Pendiente
- [ ] **Brúixola/Talaia:** actualitzar la nota de `packages/ai/README.md` (Pending) — el warehouse ja recull els marts reals. (No ho toco: fitxer d'altri.)
- [ ] **Indicador (Talaia):** decidir normalització del numerador de presència (per llar / per habitatge / absolut) i la fórmula del *gap* (proposo z-score comarcal). Llavors: cablejar `icaen_consum` a `all` + `stg_icaen_consum` (sector 7) + columna a `mart_municipi`.
- [ ] Confirmar si l'ARC publica fracció RESTA estacional (senyal intra-anual; el total anual l'amaga).
- [ ] El job CI Python (`TODO(Sondeig)` a `.github/workflows/ci.yml`) segueix obert; **no el toco** en aquest PR (és de la Bea). Ho abordo a part.

## Enlaces
- `data/marts/mart_municipi.parquet`, `data/marts/mart_electoral.parquet` (renombrats)
- `packages/transform/models/marts/mart_municipi.sql`, `mart_electoral.sql` (post_hook)
- `packages/transform/verify_marts.py`
- `docs/poblacio-real-fonts.md` (lliurable B)
- `packages/ingestion/datapoble_ingestion/icaen_consum.py` (stub) + `config.py` (SOURCES)
- `docs/data-sources.md` (Experiment 0 — base que aquest doc reenfoca)
