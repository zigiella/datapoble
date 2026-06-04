# transform · Sondeig

Projecte **dbt-duckdb**: `raw → staging → intermediate → marts`, amb tests i
lineage. Produeix **`mart_municipi`** (1 fila per municipi, clau `ine5`) amb les
columnes que `semantic/metrics.yml` marca `table: mart_municipi`, i
**`mart_electoral`** (1 fila per municipi, columnes amb sufix de convocatòria).

**Scope d'aquest PR:** Berguedà (31 municipis). Escala a Catalunya = canviar el
filtre `comarca` (vars de dbt) i regenerar la raw amb tota Catalunya.

## Capes

```
data/raw/ (parquet, el genera packages/ingestion)
   │
   ▼ seeds/          crosswalk_electoral_ine5                    (territori_codi→ine5)
   ▼ staging/        stg_rtc · stg_residus · stg_idescat_emex · stg_electoral  (views, neteja + ine5)
   ▼ intermediate/   int_rtc_municipi · int_residus_latest · int_electoral_classificacio
   ▼ marts/          mart_municipi · mart_electoral              (table + export parquet)
```

Les marts exporten automàticament a `data/marts/mart_municipi.parquet` i
`data/marts/mart_electoral.parquet` (via post-hook `COPY`). El nom és **canònic**
(sense sufix de pilot): la mart es clava per `ine5` i escala a Catalunya canviant
el filtre `comarca`, no el nom. És el nom que espera el warehouse de `packages/ai`.

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
| **IETR, IETR_rank** | datapoble | min-max winsoritzat p5/p95 (metodologia Talaia) |

## mart_electoral

1 fila per municipi (`ine5`), Parlament 2024 (`A20241`) i 2021 (`A20211`), Berguedà.
Columnes amb sufix de convocatòria: `vots_valids_*`, `pct_extrema_dreta_*`,
`pct_indep_*`, `pct_esq_*`, `guanya_*`. Percentatges sobre **vot vàlid** (suma de
candidatures). Classificació de blocs (extrema dreta / indep / esquerra) a
`int_electoral_classificacio` (regles de Talaia). **Lectura ECOLÒGICA**: agregat
municipal, mai individual; volàtil en micromunicipis.

## Honest boundaries

- **Corre de veritat:** dbt build/test verd (56 PASS), 31 files a cada mart,
  parquets generats i verificats (`verify_marts.py`, inclou Spearman IETR↔residus).
- **IETR:** calculat (min-max winsoritzat p5/p95). Ancoratges verificats: Castellar
  (08052) ≈89,4 #1; Berga (08022) ≈0,3 #31; Spearman(IETR, kg_hab_any)=0,87.
- **NULL deliberat:** `pct_icaen_EFG` (connector ICAEN, fora d'aquest PR).
- **Crosswalk Gósol (verificat):** al dataset electoral `ntc4-rnwr`,
  `territori_codi=25100` = Gósol (el **mateix** codi Idescat-derivat que mart_municipi);
  l'INE canònic `25101` és "la Granadella" en aquest dataset. El crosswalk
  (`seeds/crosswalk_electoral_ine5.csv`) és per tant **identitat** al Berguedà.
  Existeix com a infraestructura per a fonts futures que usin l'INE canònic.
