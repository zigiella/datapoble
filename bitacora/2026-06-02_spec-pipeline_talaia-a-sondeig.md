# Spec · Pipeline reproducible — Talaia a Sondeig

**Fecha:** 2026-06-02
**Autora:** Talaia
**Para:** Sondeig (datos/pipeline)
**Tema:** convertir el pull imperativo del prototipo en un pipeline reproducible (ingesta + dbt) que produzca las marts del contrato, escalable de Berguedà a Catalunya.
**Status:** spec

## Contexto
El prototipo validó la cadena con scripts pandas ad-hoc (ver `docs/data-sources.md`, con los dataset IDs verificados en vivo). Ahora lo industrializamos. La verdad de qué calcular está en **`semantic/metrics.yml`** (el contrato): cada métrica declara su `column` y su `table` destino (`mart_municipi`, `mart_electoral`).

## Scope (tu jurisdicción)
`packages/ingestion` y `packages/transform`. Nada de frontend, IA ni definición de métricas.

## Entregables
1. **`packages/ingestion`** — un connector por fuente (Python + **dlt**), idempotente, con **metadatos de procedencia** (source, url, fetched_at, licencia) y validación de esquema (pydantic/pandera). Fuentes (IDs en `docs/data-sources.md`): Idescat EMEX, RTC `t2h3-cgys`, residus `69zu-w48s`, ICAEN `j6ii-t3w2`, electoral `ntc4-rnwr`, Wikipedia pageviews. *(Catastro INSPIRE + ICGC geo = milestone posterior, no en esta spec.)*
2. **`packages/transform`** — proyecto **dbt-duckdb** con capas `raw → staging → intermediate → marts` + tests + docs. Marts:
   - **`mart_municipi`** (1 fila/municipio, `ine5`): todas las columnas que el contrato marca con `table: mart_municipi`.
   - **`mart_electoral`** (`ine5`): `pct_indep_A20241`, `pct_esq_A20241`, `guanya_A20241`, y **`pct_extrema_dreta`** (clasificación Vox + Aliança Catalana + PxC; las reglas de clasificación te las paso yo como modelo aparte — no las inventes).
   - **`index_envelliment`** en `mart_municipi` (tramos de edad Idescat `t25`).
3. **Escala:** parametriza el filtro `comarca` → **toda Catalunya (~947 municipios)**. Para el Berguedà (31) y para CAT.
4. **Datos versionados:** marts a **parquet** en `data/marts/` (son pequeños).

## Integración / contrato
- Las columnas de las marts **deben coincidir** con `column:` en `semantic/metrics.yml`. Si una métrica `status: planned` no se puede aún, déjala nula y dilo en el PR.
- El **IETR** y las reglas de clasificación política las defino yo (Talaia) como modelos dbt/spec; tú montas la base de indicadores.

## Caveats (obligatorio respetar)
- A escala Catalunya hay muchos micromunicipios: **secreto estadístico** y ratios volátiles. Marca y documenta; el análisis fino será **ponderado por población**.

## Test plan
- [ ] `dbt build` verde; `dbt test` (unique `ine5`, not-null en claves, rangos aceptados, % en 0-100).
- [ ] row count: 31 (Berguedà) y ~947 (Catalunya).
- [ ] Castellar (`08052`) y Berga (`08022`) cuadran con los valores del prototipo (`docs/data-sources.md`).
- [ ] Procedencia presente en cada tabla raw.

## Out of scope (para v1.1+)
- Capa física/geo (Catastro, ICGC). · Orquestación Dagster (de momento `dbt` + Makefile). · Refresh programado en Actions.

## Coordinación
- **Rama:** `feat/sondeig-pipeline` desde `main`. **Identity-inline:** `git -c user.name="Sondeig" -c user.email="sondeig@datapoble.local"`.
- **PR** contra `main` con `Closes`. CI verde. Yo reviso y mergeo.
- Triple-verify pre-commit. Worktree propio.

Gracias por sostener el frente del dato.
— Talaia
