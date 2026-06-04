# API a Render (Dockerfile) + control de cost de la IA + evals multi-model

**Fecha:** 2026-06-04
**Autora:** Brúixola
**Para:** Talaia (review/merge)
**Tema:** dejar la API FastAPI lista para Render y blindar el coste de OpenRouter (innegociable antes de publicitar), más un arnés de evals multi-model.
**Status:** avance / handoff

## Contexto
`packages/ai` ya tenía el text→SQL trazable (router determinista offline + backend OpenRouter cableado pero inerte sin key) y el gate de evals offline en CI. El [doc de deploy](../docs/deploy.md) decidió **plataformas gestionadas** (Cloudflare Pages + **Render** + Actions) y me asignó: **Dockerfile de la API + control de cost + evals multi-model**. Esta entrada documenta esas tres piezas. Todo es **key-independent y testeado OFFLINE**; solo las llamadas LLM en vivo necesitan el secreto.

## Qué hicimos / decidimos

### 1 · Dockerfile para Render (`packages/ai/Dockerfile`)
- `python:3.11-slim`, usuario **no-root**, `HEALTHCHECK` a `/health`, escucha en **`$PORT`** (Render lo inyecta; 8000 por defecto en local). Arranque: `python -m datapoble_ai.api` (nuevo `api._serve()` → uvicorn en `0.0.0.0:$PORT`).
- **Contexto de build = raíz del repo** (no `packages/ai`): el `Catalog` lee `semantic/metrics.yml` y el `Warehouse` lee `data/marts/`. Fijo `DATAPOBLE_ROOT=/app` dentro de la imagen para que el layout sea inequívoco. Añadí `.dockerignore` (raíz) para que el contexto no arrastre los otros packages ni node_modules.
- `OPENROUTER_API_KEY` se lee **del entorno, nunca hardcoded**. Sin key la imagen corre en modo **offline** (determinista) → primer deploy válido sin secreto.
- Nuevo extra `server = [uvicorn]` en `pyproject.toml`; la imagen instala `.[openrouter,server]`.
- **No pude construir la imagen aquí** (no hay Docker en el entorno). Sí verifiqué lo que depende de runtime: `DATAPOBLE_ROOT` resuelve el catálogo desde fuera del repo, y `python -m datapoble_ai.api` levanta uvicorn y responde `/health` 200. El build de imagen lo validará Render.

### 2 · Control de cost (`src/datapoble_ai/costcontrol.py`) — 4 capas
- **(a) Determinista-primero.** En modo `openrouter`, el agente corre el router **antes** de tocar la red. Si resuelve la pregunta (lookup/ranking/correlation) o la rechaza con precisión (planned / municipio desconocido), responde a **coste cero**. Solo el **texto libre real** que el router no mapea escala al LLM. (Antes el backend llamaba al LLM siempre.) Es la palanca grande.
- **(b) Caché de preguntas.** Normaliza `(pregunta, locale)` (minúsculas, trim, colapsa espacios) → LRU in-memory. Pregunta idéntica repetida = gratis. **Caveat documentado:** el fs de Render es efímero y puede haber varias instancias → una caché persistente necesitaría store externo (Redis/KV). La LRU in-process es el 80% barato y conserva la procedencia.
- **(c) Rate-limit** por IP/usuario (token-bucket, configurable). Excedido → **429** con mensaje amable **en el locale activo** (ca/es) + `Retry-After`.
- **(d) Tope de gasto duro** (`SpendGuard`): gasto **estimado** de OpenRouter por día/mes UTC contra un techo. Superado → **deja de llamar al LLM** y devuelve "límit de consultes IA assolit avui" (gracioso); las respuestas deterministas siguen.
- Dos nuevos `RefusalReason`: `BUDGET_EXCEEDED`, `RATE_LIMITED`, con frases ca/es. Todo configurable por env (`AI_DAILY_USD`, `AI_MONTHLY_USD`, `AI_RATE_CAPACITY`, `AI_RATE_REFILL_PER_SEC`, `AI_CACHE_MAXSIZE`, `AI_USD_PER_CALL`) con defaults que fallan **barato**. `GET /health` expone el estado (hits de caché, gasto vs topes, config de rate-limit).

### 3 · Evals multi-model (`evals/compare_models.py`) — **script aparte, NO en CI**
- Corre el **mismo** `cases.yml` contra varios modelos de OpenRouter (lista configurable) vía el backend LLM (con determinista-primero **desactivado** para puntuar al modelo, no al router) y reporta **pass-rate vs USD estimado por modelo** → decidir modelo por evidencia.
- Precios por modelo en `src/datapoble_ai/pricing.py` (referencia, override con `--pricing`). **Requiere la key**; sin ella sale con mensaje claro y código 2. Vive en `evals/` (testpaths=`tests` → pytest no lo recoge) y pasa ruff, así que **no corre en CI**.

## Por qué
El único coste que escala con el uso son las llamadas a OpenRouter (igual en VPS o gestionado). El orden importa: **determinista-primero + caché** hacen que la mayoría de consultas no cuesten nada; rate-limit y tope duro acotan el peor caso. Por eso el control de cost es *innegociable antes de publicitar la API* y por eso es todo offline-testable: la disciplina (gate de evals verde, sin red, sin key) no se toca.

## Disciplina respetada
- **Gate `ai-evals` intacto:** offline/determinista/sin red. Suite **85 passed** (eran 58), ruff limpio sobre `src evals tests`. La comparación multi-model es script aparte.
- Contrato text→SQL traçable intacto (cita fuente/fecha/fórmula o rechaza con razón).
- **No** toqué `.github/workflows/ci.yml` ni `.gitignore`. Añadí `.dockerignore` (fichero distinto, solo afecta al build context).
- **La key nunca en el repo.** Identity-inline, sin co-autor IA, rama + PR, nunca a main.

## Pendiente
- [ ] `OPENROUTER_API_KEY` en **Render + Actions** (lo aporta Bea) → primer paso del live eval con `compare_models.py` para fijar modelo (calidad vs coste).
- [ ] Crear el *Web Service* en Render (Docker, `packages/ai/Dockerfile`, región EU, healthcheck `/health`). Necesita: cuenta/servicio Render (Bea/IT).
- [ ] Marts reales: los `mart_*_bergueda.parquet` actuales **no** los recoge el warehouse (espera `mart_municipi.parquet` / `mart_electoral.parquet`). Es de Sondeig; lo dejo anotado, no lo toco.
- [ ] Si el tráfico lo pide: caché compartida/persistente (Redis/KV) para sobrevivir reinicios y abarcar varias instancias.

## Enlaces
- `packages/ai/Dockerfile`, `.dockerignore`
- `packages/ai/src/datapoble_ai/costcontrol.py`, `pricing.py`
- `packages/ai/src/datapoble_ai/llm.py` (determinista-primero + spend guard), `api.py` (rate-limit + caché + 429)
- `packages/ai/evals/compare_models.py`
- `packages/ai/tests/test_costcontrol.py`, `test_pricing.py`
- `docs/deploy.md` (sección "L'API a Render")
- `packages/ai/README.md` (sección "Desplegament a Render + control de cost")
