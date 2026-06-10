# Bateria del gate: invariants del contracte + cobertura

**Fecha:** 2026-06-10
**Autora:** Sondeig (dades/pipeline)
**Para:** Talaia (review/merge)
**Tema:** quick win del repàs del pla — formalitzar al gate de dades els invariants del contracte i la cobertura, perquè una regressió **falli** en lloc de colar-se.
**Status:** fet, verificat / handoff

## Contexto
El repàs del pla (workflow `repas-pla`) va trobar que dos invariants només es comprovaven de forma **inline i tautològica** dins `derive_fase1.py --check` (i el de `carrega_funcional` ni s'afirmava), i que **no hi havia check de cobertura**. Amb el gate `data` ja viu (#77), tenia sentit afegir-los a `verify_marts.py` (que corre al gate).

## Què he fet (`packages/transform/verify_marts.py`)
Afegit, com a assercions que **surten amb codi ≠ 0** si fallen:
1. **Cobertura**: 0 nuls a `poblacio`, `kg_hab_any`, `kwh_hab`, `vidre_hab`, `IETR` (la bateria falla si falta una font clau).
2. **Invariant IETR**: `IETR = 0,5·IETR_stock + 0,5·IETR_impact` (tolerància d'arrodoniment 0,02).
3. **Invariant denominador**: `carrega_funcional_est = max(padró, pernocta L1, càrrega residus L2)`.

Dades comprovades abans d'escriure (no s'afegeix un test que peti): 31/31 sense nuls, 0 violacions dels dos invariants.

## Verificación
- `python verify_marts.py` → **verd**: Spearman 0,869 · IETR diff màx **0,010** · `carrega_funcional = max(padró,L1,L2)` OK · cobertura 31/31 · ancoratges Castellar/Berga OK.
- `ruff check packages/transform` → net.
- Corre al job `data` de CI (sobre el parquet versionat, sense raw).

## Pendiente (resta de la bateria del triatge)
- [ ] **Talaia:** review/merge.
- [ ] join INE anti-fanout · font-any · `osm_completeness_score`+flag · sensibilitat de bases ±10/20% · leave-one-out · estabilitat del ranking IETR a pesos.
- [ ] `dbt test` sobre marts construïts des del parquet (desbloqueja els data_tests de `_marts.yml`).

## Enlaces
- `packages/transform/verify_marts.py`
- `bitacora/2026-06-10_ci-data-gate_sondeig.md` (el gate on corre)

— Sondeig
