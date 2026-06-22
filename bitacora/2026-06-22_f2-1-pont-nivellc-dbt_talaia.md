# F2.1 · dbt diagnosticat + pont Nivell C→dbt (stg_nivellc)

**Data:** 2026-06-22
**Autora:** Talaia (encarna Sondeig)
**Latido (Bea):** «comencem F2».
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F2.

## Diagnòstic (entendre abans de la cirurgia)
Instal·lat dbt-duckdb (core 1.11.11) al venv i corregut el pipeline sobre el raw de tot CAT. Troballes:
- **dbt corre a 947** — el plumbing escala. Dos blocatges només: el `seed` electoral (trivial) i
  **l'acoblament dur a l'OSM** (`stg_restauracio_osm`/`stg_serveis_osm` + la `tipologia`), que és
  material de **2a onada** i no tinc a escala → el mart quedava SKIP.
- **Quirk d'entorn:** dbt a Windows necessita `PYTHONUTF8=1` (llegeix els fitxers del projecte amb
  cp1252 i topa amb els accents). Documentat al pla.
- **El pont ja existeix:** `data/territorial/nivellc_regressio.csv` (versionat) té `base_pred` +
  `tipus_territorial` per a **927 munis** — exactament el que el mart necessita per unificar.

## Fet en aquest tros (F2.1)
- **`stg_nivellc`** (staging nou): entra el pont al dbt — `ine5, tipus_territorial, base_pred` des de
  `nivellc_regressio.csv`. Construeix net: **927 munis, 5 tipus**. És l'input que el mart consumirà
  per a (a) la base de presència L1 unificada (`base_pred` en lloc de la fixa 1224) i (b) els z-scores
  per `tipus_territorial`.
- `dbt_project.yml`: var `territorial_root`.
- Pla §F2: disseny concret de la unificació (pont, base paramètrica, stats per tipus, comarca per
  muni, OSM-opcional, quirk UTF-8).

## Verificat
`dbt run --select stg_nivellc` OK · 927 munis / 5 tipus a la vista. Marts versionats intactes (el
diagnòstic va deixar `mart_demografia.parquet` tocat → restaurat). duckdb i target són gitignored.

## Següent (F2.2 — la cirurgia del mart)
Consumir `stg_nivellc` al mart: base L1 = `base_pred`; med/vstats/sstats/q **per tipus_territorial**;
`comarca` per muni (join territori); OSM-opcional (tipologia/restauració/serveis → pendents fora del
Berguedà, 2a onada). Re-materialitzar a ~927 i **re-validar el Berguedà vs ETCA** (guardó). És el tros
gros i delicat: es fa amb cap clar i iterant fins que el Berguedà passi.

— Talaia 🌊
