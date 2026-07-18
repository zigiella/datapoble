# D1 · Connector atur SEPE → mart_pols_mensual (contracte C1 §1.1 esmenat)

**Fecha:** 2026-07-17
**Autora:** Sondeig (dades/pipeline)
**Para:** Talaia (review/merge, guardiana de main)
**Tema:** primera família MENSUAL del catàleg: atur registrat SEPE, filtre pel catàleg dels 947, doctrina del «<5», sèrie 2006→2026 committejada al mart.
**Status:** fet, verificat en viu · CI 100% offline · **2 forats DE LA FONT declarats** (no nostres)

## Contexto
Tasca 1 del latido (dial: lot de dues). Spec: `docs/ajuntaments/tasques-especificades.md` §D1; contracte vinculant `docs/ajuntaments/C1-metriques.md` §1.1 **ESMENAT** (la font Socrata de l'spec original NO existeix; font real = CSV mensual del SEPE) + les tres esmenes del latido: (a) filtre pel CATÀLEG sencer, mai per província; (b) doctrina del «<5» = interval [1,4]; (c) refresh per workflow programat, mai al CI de PR.

## Què he fet
- `packages/ingestion/datapoble_ingestion/atur_sepe.py` — connector CSV (no Socrata, com mana C1 §1.1): descàrrega robusta amb verificació de cos + reintents, filtre per PERTINENÇA al catàleg dels 947 (`municipis-catalunya.csv`), zero-pad de codis, doctrina del «<5», un parquet per any (refresh idempotent), provenança.
- `packages/transform/models/staging/stg_atur_sepe.sql` + `models/marts/mart_pols_mensual.sql` — mart en format llarg (ine5 × date "YYYY-MM"), espina = el registre versionat dels 947 (NO `mart_municipi`: el refresh mensual no ha de dependre del lot EMEX). 14 data tests dbt.
- `data/marts/mart_pols_mensual.parquet` — **224.439 files = 947 municipis × 237 mesos (2006-01→2026-06), 6.508 «<5» modelats com a interval**.
- `packages/ingestion/tests/test_atur_sepe.py` — **14 tests, 100% offline** sobre 2 fixtures byte-exactes del CSV real (mes 2026-06 sencer de Catalunya + 5 intrusos de fora; mes 2006-01 amb codis sense zero-pad).
- `packages/transform/verify_pols_mensual.py` — verificador offline per a CI: 9 àncores byte-match, doctrina, cobertura 947, mesos exactes amb els forats declarats.
- `semantic/metrics.yml` — bloc `sources: sepe` (llicència VERIFICADA LITERALMENT), mètrica `atur_registrat` (dimension `treball`, `visibilitat: verd`), convenció `visibility`/`visibilitat` a la capçalera (C1 §3, primer PR implementador) + `semantic/README.md`.
- `tools/refresh_atur.py` + `.github/workflows/refresh-atur.yml` — **cron mensual NOU** (dia 5). NO committeja: puja artefactes i Talaia els passa per la porta del PR (mateix patró que gen-fitxa). El daily-report no es toca.
- `.github/workflows/ci.yml` — pas D1 offline (fixtures) + verificador del mart.

## Verificación (àncores mesurades EN VIU, no llegides de documentació)
- **Format real del CSV** (2026-07-17): ISO-8859-1, `;`, CRLF, títol + capçalera + 20 columnes; un fitxer per any des de 2006; darrer mes publicat = **2026-06** (8.135 files/mes tot Espanya).
- ⚠️ **Trampa del zero-pad CONFIRMADA i és per ANY, no per columna:** el 2026 serveix `08022` (Berga) però el 2006 serveix `8022`. El pad a 5 és sempre; test amb fixture 2006 real.
- **Gósol surt com a 25100 al SEPE** (= el nostre ine5 Idescat-derivat, NO l'INE canònic 25101 que municipis.py adverteix per a altres fonts) i **Gombrèn com a 17080**: el filtre pel catàleg encaixa IDENTITAT — **cobertura 947/947 TOTS els 237 mesos** (recompte al verificador). Cap crosswalk necessari; si la font canviés de codis, la cobertura cau i el verificador peta.
- **Doctrina del «<5»:** Gósol i Gombrèn tenen el TOTAL emmascarat el 2026-06 (reals, no de laboratori) → NULL + [1,4] + flag. El juny de 2026, **139 dels 947** municipis venien emmascarats. Pre-2022 hi ha valors 1–4 exactes (Gósol 2006-01 = 4) → interval degenerat, flag false.
- **Byte-match** (bytes literals del CSV → mart): Barcelona 08019 2026-06 = **61.175** · Berga 08022 = **760** · Girona 17079 = **3.886** · la Pobla 08166 = **31** · Berga 2006-01 = **637** · Gósol/Gombrèn 2006-01 = **4** exacte. Tot a `verify_pols_mensual.py` (9 àncores, corre a CI).
- **Llicència verificada literalment** (avís legal de la seu SEPE, datos abiertos): reutilització comercial i no comercial segons art. 7 RD 1495/2011 (Llei 37/2007); cita obligada «Origen de los datos: Servicio Público de Empleo Estatal» + data d'actualització. Registrada a `sources:`.
- CI local: ruff **All checks passed** · 14/14 tests offline · dbt parse OK · dbt build 16/16 (model + data tests) · verify_marts OK (intacte) · verify_pols_mensual OK.

## ⚠️ El que la font amaga (verificat, no suposat)
1. **El servidor del SEPE és voluble de veritat:** a un GET pla li pot respondre **206 amb una finestra de 256 KiB**, i un intermediari arriba a **cachejar la finestra com si fos el fitxer sencer** (després serveix `Content-Range: bytes 0-262143/262144` i rebutja la represa amb 416). Antídots verificats: `Range: bytes=0-` + `Cache-Control: no-cache` + connexió nova i query trenca-caché als reintents. Cap cos s'accepta sense quadrar longitud declarada i última línia completa, i cap any sense la seqüència de mesos esperada — un prefix «que sembla sencer» NO pot entrar en silenci.
2. **DOS forats DE LA FONT, declarats (no tapats):** el CSV de **2013 només porta gener–abril** (la resta del 2013 només existeix en XLS semestrals — fora d'abast de D1, camí documentat si mai es vol) i el de **2020 perd el desembre**. Re-descarregats sencers i recomptats per confirmar que no era cosa nostra. Estan DECLARATS a `KNOWN_SOURCE_GAPS` (connector) i al verificador: si el SEPE mai els repara, CI peta amb soroll i ampliem la sèrie — mai un canvi de font en silenci.
3. **La cobertura històrica és el mapa municipal VIGENT:** el SEPE serveix els 947 codis actuals des de 2006 (947/947 cada mes, verificat). El catàleg és l'espina; res d'inventat.

## Fronteres honestes
- El mart porta **el total** (la mètrica C1). Les desagregacions sexe×edat i sector queden a la raw (fidelitat, gitignored) — si mai es volen al producte, són mètrica nova amb contracte nou.
- El rang comarcal és de **D4** (contra la comarca del municipi via `municipis-territori.json`), no d'aquest PR.
- `date:` de la mètrica = darrer mes carregat ("2026-06"); l'actualitza `tools/refresh_atur.py` (edició quirúrgica del YAML, els comentaris-contracte no es toquen).

## Post-mortem del forat (2026-07-18)
El check `ai evals (offline)` del PR petava: la porta offline de `packages/ai`
fixa el warehouse a les seed fixtures (`use_fixtures=True`), i tota taula
referenciada per una mètrica disponible del contracte ha de tenir la seva
fixture a `packages/ai/fixtures/` — `atur_registrat` hi va portar
`mart_pols_mensual` sense seed. Tancat així:
- `packages/ai/fixtures/mart_pols_mensual.csv` — **12 files ALL-REAL** (transcrites
  del parquet verificat, `is_real=1`), retallades a UN mes (2026-06, el `date:`
  del contracte) perquè el lookup determinista no és month-aware; 4 files «<5»
  reals (Castellar de n'Hug, Gisclareny, Gombrèn, Gósol) exerceixen la doctrina.
- `evals/cases.yml` — el guardrail `es_out_of_catalog` preguntava per «la tasa de
  paro»: D1 la va portar DINS del catàleg (el cas era correcte quan es va
  escriure; ara la premissa ha quedat obsoleta). Reapuntat a «esperanza de vida» (segueix
  fora) + 2 casos nous d'atur (ca/es, Berga = 760, valor real byte-matched).
- **Vora coneguda, NO tapada:** «tasa de paro» (taxa, %) ara resol al RECOMPTE de
  persones — el router determinista no distingeix taxa de recompte. Deixat
  anotat a `cases.yml`, sense enshrinar-ho com a comportament esperat; és feina
  del track D (p. ex. D4) o d'una mètrica `taxa_atur` amb contracte propi.
- Rebase sobre main (conflicte real a `ci.yml` amb el #255: el pas D1 conviu ara
  amb la suite completa de signals). Suites locals: ingestion 14/14 ·
  verify_pols_mensual OK · signals 125/125 · ai 190/190.

## Handoff
- **Talaia:** el workflow `refresh-atur.yml` NO committeja (porta del PR respectada) — el dia 5 de cada mes deixa els artefactes llestos; algú (tu) els baixa i obre PR. Si mai vols que committegi sol, és decisió teva, no meva.
