# Restauració de Talaia en màquina nova (post-pet) + comprovació de salut

**Fecha:** 2026-06-10
**Autora:** Talaia (coordinació)
**Tema:** restaurar Talaia en un entorn nou després d'un pet de hardware; verificar la salut del repo; i fer **durador** l'estat de recuperació.
**Status:** aprenentatge / restauració

## Contexto
La màquina on treballàvem va petar (trigaran a arreglar-la). La Bea em va reinvocar en un espai nou i em va demanar **clonar el repo, estudiar-lo i restaurar-me**. Detall clau: el meu fitxer de recuperació `talaia-estat-riusdegent.md` vivia **fora del repo**, en disc local (`C:\LAB`), **no sincronitzat**.

## Què he fet / decidit
- **Reconstrucció només des del repo.** Clonat `zigiella/datapoble` net i reconstruïda identitat + mètode + estat a partir de la bitàcola, `docs/`, `semantic/metrics.yml` i el git log. Confirmació pràctica que **«el repo > el xat»** funciona: la restauració completa és possible **sense** el fitxer extern.
- **Comprovació de salut** en la màquina nova (node v24.7.0, npm 10.8.2, Python 3.12.4), reproduint els **dos gates reals de CI** (`.github/workflows/ci.yml`):
  - **web** (`packages/web`): `npm ci` → `npm run check` → `npm run build` → svelte-check **1096 fitxers, 0 errors / 0 warnings**; build `adapter-static` OK. ✓
  - **ai-evals** (`packages/ai`, venv net): `pip install -e ".[dev]"` → `ruff check` → `pytest` → ruff net, **115 passed**. ✓
  - El job python/dbt de Sondeig segueix sent un **TODO comentat** → `dbt` **no és gate de CI**; amb `data/raw/` a `.gitignore`, un `dbt build` net no és reproduïble (igual que 2026-06-07/08). Sense canvis.
- **Memòria `.claude` recreada** (MEMORY.md + 5 fitxers) com a còpia de treball **autocarregada** cada sessió.

## Què he perdut (honest)
El fitxer `talaia-estat-riusdegent.md` (local-only) → **perdut amb el pet**. Tot el que vivia a **GitHub** (el repo) o a **OneDrive** (`Desktop/CAJON`, els docs de la consultora) ha **sobreviscut**.

## Per què (la lliçó)
Local-only **no sobreviu** un pet de màquina. L'estat durador de recuperació ha de viure **a prova de pets**. Decisió amb la Bea (2026-06-10): l'estat durador de Talaia passa a viure **al repo** —aquesta bitàcola n'és l'àncora—, no en un fitxer local. La memòria `.claude` queda com a **mirall** local autocarregat, no com a font única.

## Snapshot d'estat (àncora per a la pròxima restauració)
- `main` **net**, **0 PRs oberts**; últim moviment funcional **2026-06-09 (PR #75, «onada B»)**.
- **FASE 1 «endurir el model»** feta en gran part: `tipologia`, `confianca_score` 0-100, **IETR dual** (stock/impact), bloc de confiança + divergència de senyals, base-ratios.
- **Següent al full de ruta:** Sprint **Licitacions** + capa **Demografia** → després **bases esperades** + **escala Catalunya**. Base de treball: `docs/feedback-consultora-i-roadmap.md`.

## Pendiente
- [ ] **Bea:** confirmar el següent encàrrec (Licitacions/Demografia o un altre rumb).
- [ ] **Talaia:** en cada fita rellevant, deixar el snapshot **al repo** (no fiar-se de la memòria de sessió).
- [ ] (Opcional) afegir el job python a CI (`ruff` + `dbt parse`) quan Sondeig ho prioritzi — avui és TODO.

## Enlaces
- `.github/workflows/ci.yml` (els gates verificats) · `docs/00-vision-v3.md` · `docs/feedback-consultora-i-roadmap.md` · `docs/equip-com-treballem.md`
- Entrades germanes: `2026-06-02_kickoff_talaia.md` · `2026-06-08_fase1-endurir-model_sondeig.md`

— Talaia 🌊
