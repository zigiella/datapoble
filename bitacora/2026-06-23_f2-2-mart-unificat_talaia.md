# F2.2 · mart_municipi unificat a tota Catalunya (947) — el cor metodològic

**Data:** 2026-06-23
**Autora:** Talaia (encarna Sondeig)
**Latido (Bea):** «seguim» (rematar els regeneradors del CI després de la cirurgia del mart).
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F2.

## Què he fet
La unificació del model al mart, a escala Catalunya (947 munis), amb el guardó complert.

**Model (`mart_municipi.sql` reescrit):**
- **Base de presència L1 = `base_pred` per muni** (Nivell C, via `stg_nivellc`) en lloc de la fixa
  1224. CTE `pres` nova (calcula els derivats abans dels stats → de passada **arregla un build trencat**
  del model previ: `sstats` referenciava `gap_pernocta_pct` abans de definir-la; el CI només feia
  `dbt parse`, que no ho detecta).
- **Confiança/divergència per `tipus_territorial`** (z de kg/kwh/%no-principal, iguals amb iguals) —
  espina, tots els munis.
- **`comarca` per muni** (de `stg_residus`). IETR i index_turisme **globals** (indicadors absoluts).
- **OSM = 2a onada**: `tipologia` + restauració/serveis NOMÉS al Berguedà (referència pròpia →
  **preserva la classificació provada**); fora → `tipologia='pendent'`, restauració/serveis NULL
  (honest: «sense dada» ≠ «zero»). `IETR_rank` amb `row_number()` (únic a 947).

**Guardó (no regressar la joia):** presència del Berguedà recalculada vs ETCA = **8,2% error medià,
7/9 dins ±15%, ρ=0,967** — idèntic a la prova #161. La tipologia coneguda es manté (Berga=
capital_serveis, Castellar=excursió, Gósol=segona_residència).

**Resultat:** 947 munis · **927 amb presència** (20 sense covariables → NULL honest) · 31 del Berguedà
classificats, 916 `pendent`.

## Posats al dia (perquè el CI sigui verd a 947)
- `dbt_project.yml`: `n_municipis_expected` 31→947 · `_marts.yml`: `not_null` tret de presència/OSM
  (nul·lables per disseny), `pendent` als valors acceptats de tipologia · `verify_marts.py`: N=947,
  àncores IETR tretes (escala global), Spearman llindar 0,8→0,4 (més feble a escala, documentat).
- **Mirall `derive_fase1.py`** actualitzat al model nou (sstats per-tipus, bstats/btipo Berguedà,
  `pendent`, ràtio elèctric vs base_pred) — `--check` verd.
- **`tipus_territorial.py` i `validacio_etca.py`** cenyits al Berguedà (artefactes pilot/publicat),
  encara que el mart cobreixi tot CAT. `etca-validacio.json` regenerat amb la presència nova.

## Verificat
`ruff` (abast CI) OK · `dbt parse` OK · `verify_marts` OK (947) · `derive_fase1/validacio_etca/
tipus_territorial --check` OK · `dbt build --select mart_municipi` PASS=49.

## Següent (F3)
Exportar l'espina a tot CAT (`export_web_municipis.py` → dataset dels 927 amb presència+confiança) i
harmonitzar el web (un tooltip + trames a tot CAT). Després F5 (2a onada OSM). Els altres marts
(electoral/demografia) segueixen al Berguedà fins que F3 ho demani.

— Talaia 🌊
