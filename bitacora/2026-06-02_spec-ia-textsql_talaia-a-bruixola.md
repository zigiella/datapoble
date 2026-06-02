# Spec · IA texto→SQL trazable (OpenRouter) — Talaia a Brúixola

**Fecha:** 2026-06-02
**Autora:** Talaia
**Para:** Brúixola (IA / semántica)
**Tema:** industrializar el `ask.py` del prototipo en una capa de IA que responde en lenguaje natural con **procedencia siempre**, vía OpenRouter.
**Status:** spec

## Contexto
El prototipo demostró el principio (router determinista + catálogo → respuesta con fuente/fecha/fórmula/SQL). Ahora: LLM real sobre el contrato, con guardarraíles y evals.

## Scope (tu jurisdicción)
`packages/ai` (el agente + API + evals) y co-propiedad de `semantic/` (lo **consumes**, no lo redefines: eso es contrato de Talaia).

## Entregables
1. **Agente texto→SQL** que: pregunta NL → LLM (**OpenRouter**, tool-use sobre las métricas de `semantic/metrics.yml`) → **SQL parametrizado de solo lectura** sobre `mart_*` → respuesta **+ procedencia** (fuente, fecha, fórmula, consulta) en el **idioma activo** (ca/es).
2. **API** (FastAPI) con un endpoint de consulta que el frontend (Mirador) llama.
3. **Evals** en `packages/ai/evals/` — set pregunta→esperado (semilla en `metrics.yml: sample_questions`), corre en **CI** como gate anti-regresión.

## Guardarraíles (duros)
- **Solo lectura.** Solo métricas/tablas declaradas en el contrato. **Nada de SQL arbitrario sobre `raw`.**
- **Procedencia siempre** (es el principio del proyecto). Si la pregunta cae fuera del catálogo, **rechaza con razón** (refusal as a feature), no inventes.
- Distingue dato vs inferencia; marca los `status: planned` como "aún no disponible".

## OpenRouter
- Cliente compatible-OpenAI. Modelo **configurable** (por defecto uno fuerte en ca/es). Key como **secreto** `OPENROUTER_API_KEY` (la pasa Bea; nunca en repo). Caché de respuestas.

## i18n
- Responde en el **locale activo** usando `label`/`definicio`/`unit` localizados del contrato. Topónimos en su forma oficial catalana.

## Test plan
- [ ] Cada `sample_question` (ca y es) devuelve respuesta correcta + citación válida.
- [ ] Pregunta fuera de catálogo → rechazo legible (no alucinación).
- [ ] Intento de SQL de escritura/`raw` → bloqueado.
- [ ] Eval suite verde en CI.

## Out of scope (para v1.1+)
- La UI del panel "Pregúntale" (es de Mirador; tú expones la API). · Definir métricas nuevas (pídemelas a mí). · RAG sobre docs largos.

## Coordinación
- **Rama:** `feat/bruixola-textsql`. **Identity-inline:** `git -c user.name="Brúixola" -c user.email="bruixola@datapoble.local"`.
- Depende de `semantic/metrics.yml` (hecho) y de `mart_*` (Sondeig). Puedes arrancar contra las marts del prototipo mientras Sondeig las industrializa.
- PR a `main`, CI verde, yo reviso.

— Talaia
