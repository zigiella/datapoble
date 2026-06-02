# transform · Sondeig

Projecte **dbt-duckdb**: `raw → staging → intermediate → marts`, amb tests i
lineage. Produeix **`mart_municipi`** (1 fila per municipi, clau `ine5`) amb les
columnes que `semantic/metrics.yml` marca `table: mart_municipi`.

**Scope d'aquest PR:** Berguedà (31 municipis). Escala a Catalunya = canviar el
filtre `comarca` (vars de dbt) i regenerar la raw amb tota Catalunya.

## Capes

```
data/raw/ (parquet, el genera packages/ingestion)
   │
   ▼ staging/        stg_rtc · stg_residus · stg_idescat_emex   (views, neteja + ine5)
   ▼ intermediate/   int_rtc_municipi (agrega RTC) · int_residus_latest (any vigent)
   ▼ marts/          mart_municipi                               (table + export parquet)
```

`mart_municipi` exporta automàticament a `data/marts/mart_municipi_bergueda.parquet`
(via post-hook `COPY`).

## Com executar

Requisits: `dbt-duckdb` (`pip install dbt-duckdb`). La raw ha d'existir abans
(`python -m datapoble_ingestion all` des de `packages/ingestion`).

```bash
cd packages/transform
DBT_PROFILES_DIR=. dbt build          # construeix models + corre tests + exporta parquet
DBT_PROFILES_DIR=. dbt test           # només tests
DBT_PROFILES_DIR=. dbt docs generate  # catàleg + lineage

# Verificació d'ancoratges (Castellar 08052 i Berga 08022 vs docs/data-sources.md)
python verify_marts.py
```

`profiles.yml` és local (DuckDB a `datapoble.duckdb`, gitignored). En Windows
git-bash, `dbt` és a `…/venv/Scripts/dbt`.

## Tests (contracte)

- `unique` + `not_null` sobre `ine5` (clau de join).
- `not_null` sobre claus i mètriques directes (poblacio, hab_total, rtc_total…).
- `between` 0–100 per a percentatges (`pct_noprincipal`), 0–N per a ràtios.
- `assert_mart_municipi_rowcount`: exactament **31** files (Berguedà).

## Columnes de mart_municipi

Mapa contracte → font:

| columna | font | nota |
|---|---|---|
| poblacio, hab_total, hab_principal, hab_noprincipal | Idescat EMEX | directe |
| pct_noprincipal, hab_per_hab, index_envelliment | derivat EMEX | fórmula del contracte |
| rtc_total, rtc_hut, rtc_per_1000hab, rtc_per_100hab_viv | RTC | agregat per municipi |
| kg_hab_any | Residus (ARC) | darrer any = 2024 |
| **pct_icaen_EFG** | ICAEN | **NULL** — connector pendent (fora d'aquest PR) |
| **IETR, IETR_rank** | datapoble | **NULL** — els defineix Talaia (model a part) |

## Honest boundaries

- **Corre de veritat:** dbt build/test verd, 31 files, parquet generat i verificat.
- **NULL deliberat:** `IETR`, `IETR_rank`, `pct_icaen_EFG` (vegeu taula).
- **`mart_electoral`:** fora d'aquest PR (l'electoral i la classificació política
  els defineix Talaia).
- **Caveat `ine5` Gósol:** `25100` (derivat del codi Idescat 251001, no l'INE
  canònic 25101). Consistent per al join intern; l'electoral necessitarà
  crosswalk. Vegeu `packages/ingestion/datapoble_ingestion/municipis.py`.
