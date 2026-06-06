# Restauració (OSM) com a 2n proxy d'hostaleria — validació de la capa L3 — Sondeig

**Fecha:** 2026-06-06
**Autora:** Sondeig
**Para:** Talaia (review/merge + decisió d'exposició al web) · Bea (qui ho va demanar) · Mirador (FYI: la dada ja és al JSON, **a punt**, però com es mostra ho decidiu Bea i Talaia) · Brúixola (FYI: 2 columnes noves a `mart_municipi`)
**Tema:** ingerir el **nombre d'establiments de restauració** (CCAE-56) per municipi com a **2n proxy d'hostaleria** (complement del vidre) i **validar/matissar la capa L3** (pressió turística) del model de 3 capes (`docs/poblacio-real-metode.md` §7, pendent: «Restauració … encreuat amb el vidre»).
**Status:** avance / handoff
**Pilot:** Berguedà (31 municipis, `ine5`).

## Contexto
La capa L3 del model surt del **vidre/hab** (ampolles de bar/restaurant = activitat
d'hostaleria). Bea va demanar un **2n senyal independent** d'hostaleria per validar-la
o matissar-la. El doc `docs/poblacio-real-fonts.md` §T2 ja havia explorat les fonts:
Idescat `ee` (CCAE-56) oficial **però** amb secret estadístic municipal, i **OSM via
Overpass** com a proxy obert. Aquest PR materialitza el recompte i fa l'encreuament.

## Qué hicimos / decidimos

### 1 · Font: OSM/Overpass PRIMARI; Idescat oficial = «no» municipal honest
- **Idescat (CCAE-56) NO és viable a nivell municipal per API oberta** (verificat en
  viu 2026-06-06, confirma `poblacio-real-fonts.md` §T2): l'**EMEX** `dades.json`
  (Berga `080229`) **no** exposa establiments per CCAE — només afiliacions SS pel
  sector ample «serveis» (no aïlla hostaleria) i allotjament turístic (`t182`). La
  taula `taules/v2/ee` és **a escala Catalunya** (per branca i mida d'empresa, sense
  geografia municipal). El detall municipal d'establiments (la fitxa «El municipi en
  xifres») té **secret estadístic** als micromunicipis i només viu al portal CSV/web,
  no a cap API SoQL/JSON-stat consultable. → **Reportat com a sostre/contrast no
  disponible municipalment.** OSM és l'única via municipal per al pilot.
- **OSM/Overpass = PRIMARI.** Connector nou `restauracio_osm.py` (cablejat a `all`):
  - Query Overpass `nwr[amenity~restaurant|cafe|bar|fast_food|pub|biergarten|ice_cream]`
    sobre el **bbox del Berguedà** (derivat de la geometria real).
  - **Assignació de cada POI al seu municipi per PUNT-EN-POLÍGON** amb la **geometria
    administrativa real dels 31 munis** (`packages/web/static/geo/bergueda-municipis.geojson`,
    mateixa `ine5`), via l'extensió **`spatial` de DuckDB** (`ST_Contains` /
    `ST_Point`). El bbox rectangular sobre-captura veïns (Bages, Solsonès, Ripollès,
    Lluçanès…); el punt-en-polígon els **retalla** amb precisió. Snapshot 2026-06-06:
    **203 POIs al bbox → 144 assignats** als 31 munis (59 descartats = municipis veïns).
  - **Robust:** reintents amb backoff, rotació de 3 miralls Overpass, `User-Agent`
    explícit (el primari respon **406** sense capçalera — gotcha resolta).
  - Sortida: `data/raw/restauracio_osm/restauracio_osm.parquet` (1 fila/municipi,
    compte + desglossament per amenity) + `_provenance.json` (ODbL, query, comptes).

### 2 · Materialització + contracte
- **`mart_municipi`**: `restauracio_estab` (compte enter, absència→0) i
  `restauracio_per_1000hab` (densitat = estab/poblacio*1000). `stg_restauracio_osm`
  (view) + join al mart. Tests dbt `not_null`+`between` (mart i staging). **dbt build
  98 PASS** (era 91).
- **`semantic/metrics.yml`**: font `osm_overpass` + 2 mètriques amb labels **ca/es**,
  `source`/`date`/`format` i **`note`** amb el caveat de completesa (vegeu §3).
- **JSON web** regenerat (`data/web/municipis.bergueda.json`, ara **33 mètriques**) +
  clau afegida a `types.ts` (`MetricKey`). **`npm run check` i `npm run build` VERDS.**
- **NO he tocat la UI** (`indicators.ts`, `routes/resum|mapa|metodologia`): patró «dada
  primer, exposició després». La dada és al mart + contracte + JSON, **a punt**.

### 3 · FRONTERA HONESTA (al `note` del contracte i a la provenance)
- **OSM infra-mapeja el rural → el compte és un MÍNIM observat, NO un cens.** La
  completesa del mapejat varia entre municipis: **6 micromunicipis surten amb 0
  establiments** (Castell de l'Areny, Fígols, Montclar, la Quar, Sant Jaume de
  Frontanyà, Viver i Serrateix) tot i tenir senyal de vidre → és buit de mapejat, no
  absència real d'hostaleria.
- **Frontera dada/inferència:** el compte és una **MESURA**; la lectura de «pressió
  turística» que se'n fa és **inferència**. Procedència: `restauracio_estab` →
  `source: osm_overpass`; `restauracio_per_1000hab` → `source: datapoble`,
  `origin_source: osm_overpass`.
- **Llicència ODbL** (atribució + compartir-igual) anotada — a tenir en compte si es
  publica el derivat.

## PAYLOAD ANALÍTIC — ¿valida la capa L3? **SÍ** (amb un matís honest)

Correlació de Spearman (rang, N=31, sense scipy — `pandas.rank().corr`, com `verify_marts.py`):

| Parella | Spearman ρ | t (df=29) | Lectura |
|---|--:|--:|---|
| **restauracio_per_1000hab ↔ vidre_hab** | **0,544** | 3,49 | **moderada-positiva, p<0,01** |
| **restauracio_per_1000hab ↔ index_turisme** | **0,539** | 3,45 | **moderada-positiva, p<0,01** |
| restauracio_per_1000hab ↔ rtc_per_1000hab | 0,207 | — | dèbil (RTC = allotjament, no restauració) |
| restauracio_estab ↔ poblacio (absolut) | 0,893 | — | el compte absolut escala amb la mida (esperat) |

> Pearson de referència (sensible als extrems): per1000 ↔ vidre = **0,745**;
> per1000 ↔ index_turisme = **0,712**. La diferència Pearson>Spearman indica que els
> **extrems turístics** (Gósol, Castellar, Gisclareny) estiren fort la relació lineal.

**Veredicte: el recompte de restaurants CONFIRMA el senyal d'hostaleria del vidre com
a 2n proxy INDEPENDENT.** Dos senyals de naturalesa diferent (vidre = **activitat**,
ampolles consumides; restauració = **capacitat**, stock de locals) apunten al mateix
fenomen i coincideixen als extrems esperats. Els ancoratges es compleixen:
- **Gósol** i **Castellar de n'Hug** alts per càpita (top-4) — ✓ esperat.
- **Berga** (capital): **#1 absolut** (28 locals) però **per càpita baix** (1,60 /1000,
  **rang #24 de 31**), `index_turisme` 26,6 — ✓ esperat «moderat-baix per càpita».

**El matís (no el forço — és el límit de la dada):** les **discrepàncies de rang més
grosses són els 6 micromunicipis amb 0 locals OSM** però vidre alt (Viver i Serrateix
vidre 74,5; la Quar 70,5; Sagàs 132,5 amb només 1 local). **Això és infra-mapejat
d'OSM al rural, NO una contradicció del senyal del vidre.** És exactament el caveat
«mínim, no cens». Si l'enfortim contra el vidre, la baixa ρ als micromunicipis és
*completesa de la font*, no *desacord de fenomen* — als munis amb mapejat raonable els
dos proxies concorden. **Per tant: valida, amb la frontera ben marcada.** (No cau en el
*catch* del model: no derivo res per resta; són dues mesures independents encreuades.)

### Taula — restauració per municipi (snapshot OSM 2026-06-06), ordre per densitat

| Municipi | Pob. | Estab. | **/1000 hab** | vidre_hab | index_turisme |
|---|--:|--:|--:|--:|--:|
| Gisclareny | 28 | 1 | **35,71** | 144,0 | 100,0 |
| Gósol | 207 | 6 | **28,99** | 149,4 | 100,0 |
| la Nou de Berguedà | 163 | 3 | **18,40** | 90,8 | 71,5 |
| Castellar de n'Hug | 166 | 3 | **18,07** | 107,7 | 83,5 |
| Saldes | 301 | 5 | **16,61** | 90,1 | 71,0 |
| l'Espunyola | 260 | 3 | 11,54 | 39,2 | 34,8 |
| Santa Maria de Merlès | 179 | 2 | 11,17 | 79,9 | 63,8 |
| Capolat | 93 | 1 | 10,75 | 77,2 | 61,9 |
| Montmajor | 471 | 5 | 10,62 | 46,5 | 40,0 |
| Vilada | 430 | 4 | 9,30 | 35,6 | 32,3 |
| Borredà | 434 | 4 | 9,22 | 49,8 | 42,4 |
| Cercs | 1.236 | 11 | 8,90 | 36,4 | 32,8 |
| Sant Julià de Cerdanyola | 234 | 2 | 8,55 | 58,1 | 48,3 |
| Vallcebre | 260 | 2 | 7,69 | 55,7 | 46,6 |
| Castellar del Riu | 151 | 1 | 6,62 | 78,4 | 62,7 |
| Sagàs | 153 | 1 | 6,54 | **132,5** | 100,0 |
| la Pobla de Lillet | 1.106 | 7 | 6,33 | 48,6 | 41,5 |
| Gironella | 5.082 | 23 | 4,53 | 20,6 | 21,6 |
| Guardiola de Berguedà | 962 | 4 | 4,16 | 53,0 | 44,6 |
| Bagà | 2.167 | 9 | 4,15 | 34,5 | 31,5 |
| Olvan | 926 | 3 | 3,24 | 36,1 | 32,6 |
| Casserres | 1.665 | 5 | 3,00 | 38,7 | 34,5 |
| Avià | 2.263 | 6 | 2,65 | 27,8 | 26,7 |
| **Berga** | 17.539 | **28** | **1,60** | 27,6 | 26,6 |
| Puig-reig | 4.558 | 5 | 1,10 | 28,3 | 27,1 |
| Castell de l'Areny | 68 | **0** | 0,00 | 60,1 | 49,7 |
| Fígols | 41 | **0** | 0,00 | 1,2 | 7,8 |
| Montclar | 133 | **0** | 0,00 | 44,2 | 38,4 |
| la Quar | 44 | **0** | 0,00 | 70,5 | 57,1 |
| Sant Jaume de Frontanyà | 25 | **0** | 0,00 | 39,6 | 35,1 |
| Viver i Serrateix | 178 | **0** | 0,00 | 74,5 | 59,9 |

**Total: 144 establiments** mapejats als 31 munis (de 203 al bbox; 59 = veïns descartats).
Compte = mapejat a OSM, **mínim observat**. Els 6 munis amb 0 (excepte Fígols, que també
té vidre ínfim) = **infra-mapejat rural** amb senyal de vidre present → buit de font, no
absència real.

## Por qué
- **Dos proxies independents que concorden** (vidre = activitat, restauració =
  capacitat) fan la capa L3 més defensable que un de sol. La discordança als
  micromunicipis és **completesa de font** (OSM), no del fenomen → es comunica així.
- **OSM en comptes d'Idescat** perquè el detall municipal oficial **no existeix obert**
  (secret estadístic). Un buit honest marcat val més que una xifra oficial inexistent.
- **Punt-en-polígon amb la geometria del repo** (no `area` Overpass): la gotcha
  documentada (`area["name"="Berguedà"]` no resol per accent/relació) queda evitada, i
  l'assignació és **determinista i reproduïble** (la query i el retall espacial ho són;
  l'snapshot d'OSM pot variar amb el temps — per això és «mínim», no cens).

## Pendiente
- [ ] **Talaia/Bea:** decidir si i **com exposar** `restauracio_estab` /
      `restauracio_per_1000hab` al web (mapa? fitxa? cap?). La dada és al JSON **a
      punt**; jo **no** he tocat la UI (patró «dada primer»).
- [ ] **Talaia:** si vols, integrar la restauració com a **corroborador secundari** de
      la `confianca` de L3 (concorda amb el vidre? ↑ confiança), amb el caveat que els
      0 d'OSM no han de **baixar** la confiança (són buit de mapejat, no senyal).
- [ ] Idescat `ee` CCAE-56 municipal: **descartat** per al pilot (secret estadístic, no
      API). Com a sostre comarcal caldria descàrrega CSV manual — fora de pipeline obert.
- [ ] El job CI Python (`TODO(Sondeig)` a `.github/workflows/ci.yml`) segueix obert; els
      tests offline nous (`packages/ingestion/tests/test_restauracio_osm.py`) hi
      entrarien quan s'activi. **No el toco** (és de la Bea).

## Enlaces
- `packages/ingestion/datapoble_ingestion/restauracio_osm.py` (connector, cablejat a `all`)
- `packages/ingestion/datapoble_ingestion/config.py` (`SOURCES['restauracio_osm']`, `OVERPASS_ENDPOINTS`)
- `packages/ingestion/tests/test_restauracio_osm.py` (offline, mockeja Overpass)
- `packages/transform/models/staging/stg_restauracio_osm.sql` + `mart_municipi.sql` (join + 2 columnes)
- `semantic/metrics.yml` (font `osm_overpass` + `restauracio_estab` / `restauracio_per_1000hab`)
- `tools/export_web_municipis.py` + `data/web/municipis.bergueda.json` (33 mètriques)
- `packages/web/src/lib/contract/types.ts` (`MetricKey`)
- `docs/poblacio-real-fonts.md` §T2 (inventari previ de la font) · `docs/poblacio-real-metode.md` §7 (pendent que això tanca)
