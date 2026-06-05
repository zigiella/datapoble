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
   ▼ staging/        stg_rtc · stg_residus · stg_idescat_emex · stg_electoral · stg_icaen_consum  (views, neteja + ine5)
   ▼ intermediate/   int_rtc_municipi · int_residus_latest · int_electoral_classificacio
   ▼ marts/          mart_municipi · mart_electoral · mart_consum_electric  (table + export parquet)
```

Les marts exporten automàticament a `data/marts/*.parquet` (via post-hook `COPY`):
`mart_municipi.parquet`, `mart_electoral.parquet` i `mart_consum_electric.parquet`.
El nom és **canònic** (sense sufix de pilot): la mart es clava per `ine5` i escala a
Catalunya canviant el filtre `comarca`, no el nom. `mart_municipi`/`mart_electoral`
són els noms que espera el warehouse de `packages/ai`.

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

## mart_consum_electric

Sèrie de **consum elèctric domèstic** per municipi × any (format **llarg**, clau
`ine5`+`any_consum`), Berguedà 2013–2024 → **31×12 = 372 files**. Font ICAEN
`8idm-becu`, sector **USOS DOMÈSTICS** (l'únic que sobreviu al secret estadístic a
micromunicipis → sèrie sencera sense forats per als 31). Columnes: `ine5, codi6,
municipi, comarca, any_consum, sector, consum_kwh_domestic`.

Proxy de **presència humana real** per a l'indicador "població real vs padró"
(`docs/poblacio-real-fonts.md`). **NO normalitzat**: consum brut anual, fidel a la
font. La normalització del numerador (kWh/habitatge vs kWh/població) i la fórmula
del *gap* són síntesi de Talaia (fora d'aquest PR); quan es decideixi, s'afegirà una
columna derivada a `mart_municipi`. Test: `assert_mart_consum_electric_grid` (graella
completa 372, sense forats ni duplicats).

## Export per al web (Mirador)

`tools/export_web_municipis.py` (a l'arrel del repo) llegeix `mart_municipi` +
`mart_electoral` + el contracte `semantic/metrics.yml` i emet
**`data/web/municipis.bergueda.json`** amb la forma EXACTA `MunicipisDataset`
(`packages/web/src/lib/contract/types.ts`). És el pas que substitueix el mock
(`packages/web/src/lib/mock/municipis.ts`) per dades reals dels 31 municipis. Idempotent
(`--check` falla si el JSON està desactualitzat → apte per a CI). Polítics = Parlament
2024; `pct_icaen_EFG` = null (buit honest, connector de certificats pendent).

```bash
python tools/export_web_municipis.py            # regenera el JSON
python tools/export_web_municipis.py --check    # verifica que està al dia
```

## Honest boundaries

- **Corre de veritat:** dbt build/test verd (68 PASS), 31 files a `mart_municipi`/
  `mart_electoral` i 372 a `mart_consum_electric`, parquets generats i verificats
  (`verify_marts.py`, inclou Spearman IETR↔residus).
- **IETR:** calculat (min-max winsoritzat p5/p95). Ancoratges verificats: Castellar
  (08052) ≈89,4 #1; Berga (08022) ≈0,3 #31; Spearman(IETR, kg_hab_any)=0,87.
- **NULL deliberat:** `pct_icaen_EFG` (connector de **certificats** ICAEN `j6ii-t3w2`,
  fora d'aquest PR — no confondre amb `mart_consum_electric`, que sí està ingerit).
- **Crosswalk Gósol (verificat):** al dataset electoral `ntc4-rnwr`,
  `territori_codi=25100` = Gósol (el **mateix** codi Idescat-derivat que mart_municipi);
  l'INE canònic `25101` és "la Granadella" en aquest dataset. El crosswalk
  (`seeds/crosswalk_electoral_ine5.csv`) és per tant **identitat** al Berguedà.
  Existeix com a infraestructura per a fonts futures que usin l'INE canònic.
