# IETR + mart_electoral (extrema dreta) — segona oleada Sondeig

**Fecha:** 2026-06-02
**Autora:** Sondeig
**Para:** Talaia (review)
**Tema:** rellenar IETR/IETR_rank en mart_municipi (metodología de Talaia) y crear mart_electoral con clasificación política (extrema dreta / indep / esquerra) para Parlament 2024 y 2021 del Berguedà.
**Status:** avance / handoff

## Contexto
Primera oleada dejó `mart_municipi` con `IETR`/`IETR_rank` en NULL (los definía Talaia) y sin capa electoral. Esta entrada documenta las dos adiciones, sus fórmulas, y un hallazgo de datos que **corrige un supuesto de la spec** (el crosswalk de Gósol).

## Qué hicimos / decidimos

### SPEC 1 · IETR (Índex d'Exposició Turística-Residencial)
Método (de Talaia): **min-max winsorizado (p5/p95)** sobre los 31 municipios, dos dimensiones a pesos iguales.

- **Eje A (residencial)** = media de `pct_noprincipal` y `hab_per_hab` normalizados.
- **Eje B (turístico)** = media de `rtc_per_1000hab` y `rtc_per_100hab_viv` normalizados.
- Cada indicador se winsoriza a [p5, p95] (`quantile_cont`) y se reescala 0-100 contra la distribución comarcal. `IETR = 0.5·A + 0.5·B`. `IETR_rank = rank(IETR desc)`.
- Implementado **dentro de `mart_municipi.sql`** (CTEs `ind → q → norm → ietr`), estilo dbt del modelo. `round(IETR, 2)`.

**Anclajes verificados** (coinciden con el prototipo):
| municipi | IETR | rank |
|---|---|---|
| Castellar de n'Hug (08052) | **89,45** | **#1** |
| Berga (08022) | **0,30** | **#31** |

**Validación externa:** `verify_marts.py` calcula **Spearman(IETR, kg_hab_any) = 0,869 (> 0,8)** — el índice predice la carga real de residuos (en el prototipo, 0,87). Spearman = Pearson sobre rangos (sin dependencia de scipy, que no está instalado). Tests dbt: `IETR` between 0-100 + not_null; `IETR_rank` unique + not_null.

### SPEC 2 · mart_electoral
Nuevo connector `electoral.py` (dataset `ntc4-rnwr`, Socrata) + cadena dbt
`seed crosswalk → stg_electoral → int_electoral_classificacio → mart_electoral`.

- **Ingesta:** filtra `nom_nivell_territorial='Municipi'` y los 31 territori_codi del Berguedà, convocatorias `A20241` (2024) y `A20211` (2021). Guarda procedencia (`_provenance.json`, `lectura: ecològica`). 963 filas crudas.
- **Normalización de siglas** (`sigla_norm`): `regexp_replace(upper(strip_accents(sigles)), '[^A-Z0-9]', '')`. DuckDB trae `strip_accents()` nativo. Ej.: `ALIANÇA.CAT → ALIANCACAT`, `CAT-JUNTS+ → CATJUNTS`, `CUP - DT → CUPDT`.
- **Clasificación** (bloques NO exclusivos):
  - **EXTREMA DRETA** = VOX, ALIANCACAT, PXC, ESPANYA2000, FE/FET. *(En el Berguedà solo aparecen VOX y Aliança Catalana.)*
  - **INDEPENDENTISTA** = ERC, JUNTS (CATJUNTS/JXCAT/CIU/CDC/PDECAT), CUP\*, ALIANCACAT, ALHORA, SI, FNC.
  - **ESQUERRA** = PSC, ERC, CUP\*, COMUNS\*/ECP/PODEM/CATCOMU, PCTC.
  - Aliança Catalana cuenta a la vez en extrema dreta **e** independentista (es las dos cosas), tal como pide la spec.
- **Columnas** (por `ine5`, sufijo de convocatoria): `vots_valids_*`, `pct_extrema_dreta_*`, `pct_indep_*`, `pct_esq_*`, `guanya_*` (sigla más votada, argmax). Pcts sobre voto válido. Lectura **ECOLÓGICA** (nota explícita en el modelo y en `_marts.yml`).

**Anclaje verificado (Castellar 08052, 2024):** guanya=**CAT-JUNTS+**, pct_indep=**84,31%**, pct_extrema_dreta=**27,45%** (Vox 2,0 + Aliança 25,5). Coincide con la spec (Junts ~39, Aliança ~26, ERC ~14, PSC ~8, CUP ~5 → indep ≈84, XD ≈27).

**Señal del proyecto (la irrupción):** extrema dreta 2021→2024: Castellar 2,08→27,45; Berga 2,66→13,90. Aliança Catalana es el motor.

## Por qué — hallazgo que corrige la spec (crosswalk Gósol)
La spec asumía: *en `ntc4-rnwr`, `territori_codi` es INE canónico → Gósol = 25101*, y pedía un crosswalk `25101→25100`.

**Verificado en vivo (2026-06-02), es FALSO para este dataset:**
- En `ntc4-rnwr`, **Gósol está en `territori_codi=25100`** (mismo código Idescat-derivado que RTC/residus/EMEX y que `mart_municipi`). Devuelve las candidaturas de Gósol (CAT-JUNTS+ 47, ERC 21, PSC 14).
- **`25101` en este dataset es "la Granadella"** (otro municipio de Lleida, fuera del Berguedà). Un crosswalk `25101→25100` habría inyectado los votos de la Granadella en Gósol — un bug silencioso.

**Decisión:** el crosswalk (`seeds/crosswalk_electoral_ine5.csv`) es por tanto **identidad** en el Berguedà. Se mantiene como **infraestructura documentada** (cumple la intención de la spec: el join pasa por un crosswalk explícito y Gósol queda manejado y verificado) y como hook para fuentes futuras que sí usen el INE canónico. Verificado además que en el Berguedà solo Gósol tiene prefijo de provincia ≠08.

## Pendiente
- [ ] **Escala a Catalunya** (~947 municipios) — siguiente PR. El filtro electoral se parametriza cambiando `ELECCIONS_PILOT`/`BERGUEDA_INE5`; a escala CAT habrá municipios donde `territori_codi` SÍ difiera del ine5 de Idescat → el crosswalk dejará de ser identidad (ahí cobra valor real).
- [ ] Connector **ICAEN** (`j6ii-t3w2`) para `pct_icaen_EFG` (sigue NULL).
- [ ] Job de CI Python (ruff + dbt build + dbt test + verify_marts) — el hueco `TODO(Sondeig)` en `.github/workflows/ci.yml` sigue abierto; lo abordo aparte para no mezclar con esta oleada.
- [ ] Revisar con Talaia si alguna sigla menor del Berguedà (MPIC, SCAT, EB, FO) debe entrar en algún bloque; me he ceñido a la lista explícita de la spec para no inventar.

## Enlaces
- `packages/transform/models/marts/mart_municipi.sql` (IETR), `mart_electoral.sql`
- `packages/transform/models/intermediate/int_electoral_classificacio.sql`
- `packages/transform/seeds/crosswalk_electoral_ine5.csv`
- `packages/ingestion/datapoble_ingestion/electoral.py`
- `packages/transform/verify_marts.py` (Spearman + anclajes IETR)
- `semantic/metrics.yml` (contrato; no tocado)
