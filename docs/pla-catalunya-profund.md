# Pla — el dataset profund a tota Catalunya («fer-ho bé»)

> Bea: *«volem fer-ho bé»*. Estendre el que tenim al Berguedà (dataset profund: presència, tipologia,
> confiança, IETR…) a **tot Catalunya (947 municipis)** amb **un sol mètode coherent**, honest a
> escala, **sense trencar el pilot validat del Berguedà**. Document de coordinació (Talaia); les
> decisions de mètode hi queden traçades. Enllaça amb [metodologia-presencia-catalunya](metodologia-presencia-catalunya.md),
> [analisi-escala-nivellc](analisi-escala-nivellc.md) i [tipologia-municipal](tipologia-municipal.md).

## 0. El problema (què va veure Bea)
Al mapa, el Berguedà i la resta es pinten i s'expliquen **diferent**: el Berguedà té el dataset
profund (Nivell B: 3 senyals → confiança + **trames**, tooltip ric); la resta només té presència en
rang (Nivell C). Dues fitxes, dos models, experiència incoherent. *No és un problema de disseny: és
que la dada profunda existeix només al Berguedà.* Fer-ho bé = que la dada profunda existeixi, honesta,
a tot el país.

## 1. La bona notícia
Dues peces clau **ja estan resoltes** i ens donen el marc:
- **La base de presència a tot CAT** (el cor) ja és Nivell C: `base = f(densitat, renda, gas)`,
  ajustada contra l'ETCA sobre 486 munis, *held-out* robusta, **en rang**. No cal reinventar-la.
- **El marc de referència honest** ja existeix: el **`tipus_territorial`** (corona, metropolità dens,
  litoral metropolità, interior rural, litoral vacacional…). És la clau per fer honestos a escala els
  indicadors **relatius** (vegeu §3).

## 2. Dues feines, de natura molt diferent
**(A) Des-acotar el pipeline (enginyeria, mecànica, risc baix).** El pipeline ja està gairebé
parametritzat; només cau al Berguedà en punts concrets:
- Connectors **bulk** (RTC, residus, ICAEN, electoral): avui filtren `comarca='Berguedà'` a la query
  → treure el filtre / recórrer tot CAT. Fàcil.
- Connectors **per-muni** (Idescat EMEX, demografia/origen): ~947×N crides lentes → escalar +
  **cachejar/versionar** (cortesia amb l'API). El gruix de temps de baixada.
- Connectors **OSM** (restauració, serveis): bbox + geometria del Berguedà hardcoded → bbox CAT +
  **geometria dels 947** (ja la tenim: `catalunya-municipis.geojson`).
- Llista `BERGUEDA` (31 codis) → generar la de tot CAT des de la geometria/font oficial.
- `dbt_project.yml`: `comarca: "Berguedà"`, `n_municipis_expected: 31` → tot CAT.
- L'**export** (`export_web_municipis.py`) és **agnòstic**: escala sol quan els marts tinguin 947.

**(B) Unificar el mètode (la feina REAL de «fer-ho bé», risc metodològic).** Avui el mart calcula els
indicadors **relatius al Berguedà**: les **bases** (`base_electric=1224`, `base_residencial=410`,
`base_vidre=26.5`) i els **z-scores** (tipologia, confiança, divergència) són sobre els **31 munis**.
Si simplement correm el mateix SQL amb 947, comparem Barcelona amb Gósol → soroll. Cal repensar els
**àncoratges relatius** (§3).

## 3. Decisions de mètode (el nucli)
1. **Base de presència → unificada en Nivell C.** Substituir la base fixa (`1224`) per `base_pred` de
   covariables **a tot arreu, inclòs el Berguedà**. Un sol model, traçable. → **Guardó:** el Berguedà
   recalculat ha de **reproduir la seva validació ETCA** dins tolerància; si no, el Berguedà manté
   calibratge propi com a cas especial documentat. *No trenquem la joia.*
2. **Grup de referència dels z-scores → `tipus_territorial`, no la comarca.** Tipologia i confiança
   comparen cada muni amb **els del seu tipus** (rural amb rural, litoral amb litoral). Coherent amb la
   banda d'incertesa, que ja és per tipus. Evita el problema de comarques minúscules (Aran) i de
   barrejar escales. *Iguals amb iguals.*
3. **Bases de residus/vidre → per tipus territorial** (o petit model de covariables), no el valor
   Berguedà. Residus ja és tot-CAT (ARC); el vidre també (fraccions ARC).
4. **Abast publicat: l'ESPINA primer, honesta i uniforme; la resta, segona onada validada.**
   - **Espina (s'estén ara, valida a escala):** presència/gap, `tipus_territorial`, **confiança**,
     residus (kg/hab, vidre/hab), densitat, covariables. Aquests pinten el mapa + tooltip + **trames**
     **uniformement a tot CAT**. Resol el que va veure Bea.
   - **Segona onada (Berguedà-pilot fins validar per tipus):** indicadors dependents d'OSM
     (restauració/serveis — OSM **infra-mapa el rural**: és un mínim observat, no cens) i els subtipus
     fins de tipologia. S'estenen amb bandera de fiabilitat **quan validin**, no abans.
   - *Honest: estendre tot de cop amb números febles diluiria la confiança. Estenem el que aguanta.*

## 4. Fases (cada una és PR verificat; no es fa tot d'un cop)
- **F1 · Des-acotar la ingesta (risc baix).** Connectors + llista + geometria + `dbt_project.yml` a
  tot CAT → `data/raw` amb els 947. **No toca encara la sortida del Berguedà.** Verificació: recompte
  de files per font ≈ 947; mostres puntuals.
- **F2 · Unificar el model (mart).** *Diagnòstic fet (2026-06-22): dbt corre a 947; els únics
  blocatges eren el `seed` electoral (trivial) i l'acoblament dur a l'OSM (2a onada).* Disseny concret:
  - **Pont Nivell C → dbt:** `data/territorial/nivellc_regressio.csv` (JA existeix, 927 munis amb
    `base_pred` + `tipus_territorial`) entra com a staging `stg_nivellc`. El mart el consumeix.
  - **Base de presència (L1):** el macro `estimacio_presencia(padró, kwh_hab, base)` ja pren la base
    com a paràmetre → passar-li `base_pred` per-muni en lloc de `var('base_electric')` (1224).
  - **Stats per `tipus_territorial`:** med/vstats/sstats/q passen de globals (31) a **per tipus**
    (z-scores i confiança comparant iguals amb iguals).
  - **`comarca` per muni:** substituir el literal `'{{ var("comarca") }}'` per un join (territori).
  - **OSM-opcional (espina):** `stg_restauracio_osm`/`stg_serveis_osm` toleren l'absència de raw;
    `tipologia` + restauració/serveis queden **pendents** (NULL) fora del Berguedà → 2a onada (F5).
  - **Quirk d'entorn:** dbt a Windows necessita `PYTHONUTF8=1` (accents als fitxers del projecte).
  - Materialitzar `mart_municipi` per als ~927. Verificació: **re-validació ETCA del Berguedà**
    (guardó §3.1) + sanity per tipus.
- **F3 · Exportar l'espina a tot CAT.** `municipis.catalunya.json` (o estendre el dataset) amb
  l'espina §3.4 per als 947, rang + confiança. Verificació: l'artefacte cobreix ~927 amb confiança.
- **F4 · Harmonitzar el web.** Un sol tooltip + fitxa + **trames a tot CAT** (segons confiança, no
  segons «és Berguedà»). Resol el «fitxes diferents». Verificació: SSR de la fitxa/tooltip; cop d'ull
  visual de Bea al mapa (canvas).
- **F5 · Segona onada** (OSM + subtipus) quan validin per tipus.

## 5. El que NO sacrifiquem (honestedat)
- **Cap número sense procedència**; estimació ≠ cens; **rang** on no validem; el **«no»** és resposta.
- El Berguedà va tenir **curació i validació a mà**; a escala, el pipeline és automàtic → **més
  incertesa** → confiança graduada + rang + bandera on és feble. *«La mateixa dada» a tot CAT ≠ «la
  mateixa fiabilitat».*
- **No regressar el Berguedà**: és el guardó de F2.

## 6. Magnitud (honest)
És una **fase multi-sessió**, no un PR. El gruix de rellotge són les baixades per-muni (EMEX/origen,
~1.900 crides cortesos) i l'OSM a escala; la resta és bulk. Cada fase aporta valor i és verificable
per separat. F1 es pot començar ja (risc baix, necessària sí o sí).

— Talaia 🌊
