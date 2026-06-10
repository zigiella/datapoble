# Gate de CI per al front de dades (dbt parse + verificadors offline)

**Fecha:** 2026-06-10
**Autora:** Sondeig (dades/pipeline)
**Para:** Talaia (review/merge, gatekeeper de main)
**Tema:** activar a CI el job de dades que fins ara era un TODO comentat — perquè els verificadors de la mart deixin de ser decoratius i **bloquegin** els merges.
**Status:** fet, verificat / handoff

## Contexto
El triatge del `vuelta-tuerca` (workflow de Talaia, 2026-06-10) va trobar el forat de més palanca del repo: el job `python` de `.github/workflows/ci.yml` estava **comentat** → `verify_marts.py`, `derive_fase1.py --check` i `dbt parse` existien però **no corrien com a gate**. Es podia mergear amb la mart trencada. *Tenir tests que no s'executen és pitjor que no tenir-ne.*

## Què he fet
Substituït el bloc `# TODO(Sondeig)` per un job `data` real que corre el que **sí** és reproduïble en checkout net (sense `data/raw/`, gitignored; sense xarxa):
- `ruff check packages/transform` (lint del front de dades).
- `dbt parse` (plantilla + schema vàlids; `--project-dir`/`--profiles-dir` a `packages/transform`).
- `python verify_marts.py` (ancoratges Castellar/Berga + Spearman IETR↔residus > 0,8).
- `python derive_fase1.py --check` (els 9 derivats Fase 1 + 2 senyals de centralitat, byte-fidels al parquet versionat).
- `PYTHONUTF8=1` al job: dbt llegeix els fitxers del projecte amb l'encoding del sistema; a CI (ubuntu) ja és UTF-8, però es força explícitament (a Windows local fallava amb `cp1252` sobre un accent — artefacte de plataforma, no del projecte).

## Per què `dbt build`/`dbt test` NO hi són (encara)
`dbt build` materialitza des de `data/raw/` (gitignored) → no reproduïble en checkout net. `dbt test` (accepted_values, between, not_null, unique de `_marts.yml`) necessita els models construïts → tampoc. La cobertura equivalent la donen avui els verificadors offline sobre el parquet versionat. Construir els marts des del parquet per córrer `dbt test` a CI = millora futura.

## Verificación (local, abans de cablejar — no s'activa un gate vermell)
venv net (Python 3.12), `pip install dbt-duckdb duckdb pandas pyarrow ruff`:
- `ruff check packages/transform` → **All checks passed**.
- `dbt parse` (PYTHONUTF8=1) → **exit 0**.
- `verify_marts.py` → **OK** (Spearman 0,869; 31 munis; Castellar/Berga quadren).
- `derive_fase1.py --check` → **OK** (parquet al dia; 9 derivats + 2 senyals centralitat).

## Pendiente / handoffs
- [ ] **Talaia:** review/merge.
- [ ] **Sondeig (jo) / Cabal:** `ruff` troba 4 issues preexistents **fora** de `transform` (3 a `ingestion`, auto-fixables; 1 `lambda` a `signals/tests`); per això el lint del gate s'acota a `packages/transform` (verd). Estendre `ruff` a ingestion+signals quan estiguin nets — follow-up separat.
- [ ] Futur: pinning de versions (avui `pip install` sense pin) i `dbt test` sobre marts construïts des del parquet.

## Enlaces
- `.github/workflows/ci.yml` (job `data` nou)
- `packages/transform/verify_marts.py` · `derive_fase1.py` · `models/marts/mart_municipi.sql`
- `bitacora/2026-06-10_restauracio-talaia_talaia.md` (el triatge que ho va destapar)

— Sondeig
