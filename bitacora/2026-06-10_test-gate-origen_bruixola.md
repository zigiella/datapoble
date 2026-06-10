# Test de regressió del gate d'origen (IA)

**Fecha:** 2026-06-10
**Autora:** Brúixola (IA / semàntica)
**Para:** Talaia (review/merge)
**Tema:** quick win del repàs del pla — blindar amb un test el gate que reté les mètriques d'origen de l'agent (avui sense cap cobertura).
**Status:** fet, verificat / handoff

## Contexto
El repàs del pla va trobar que el gate d'origen (`catalog.is_available()` → False si `dimension=='origen'`, a `catalog.py`) està implementat però **sense cap test**: una regressió (treure la condició o renombrar la dimensió) exposaria dades sensibles d'origen a la IA sense que res ho avisés. És privacitat per disseny → mereix guarda.

## Què he fet (`packages/ai/tests/test_catalog.py`)
`test_origen_metrics_are_held_back_from_agent`: itera **totes** les mètriques `dimension: origen` del contracte i comprova que (a) n'hi ha (test no buit), (b) cap té `is_available()` True, (c) cap és a `available_metrics()`, i (d) la sentinella `pct_nascuda_estranger` queda retinguda.

## Verificación
- `pytest` (packages/ai) → **116 passed** (115 + aquest). `ruff check src evals tests` → net.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (triatge) quan hi hagi la capa interpretativa/LLM viva: evals de **comportament** (re-emmarcament de preguntes trampa, refús de marc causal/ètnic), no només el gate d'accés.

## Enlaces
- `packages/ai/tests/test_catalog.py` · `packages/ai/src/datapoble_ai/catalog.py` (`is_available`)

— Brúixola
