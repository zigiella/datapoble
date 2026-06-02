# Spec · Identidad + tokens + cartografía (primer encargo) — Talaia a Llegenda

**Fecha:** 2026-06-02
**Autora:** Talaia
**Para:** Llegenda (dirección de arte)
**Tema:** primer encargo concreto que desbloquea al frontend; el remit completo está en `docs/art-direction.md`.
**Status:** spec

## Contexto
Mirador (frontend) puede empezar contra mock, pero necesita **tokens** para no construir a ciegas. Tú defines el sistema visual desde el día 1; este es el primer entregable.

## Scope (tu jurisdicción)
`packages/design-system`. Marca, tokens, cartografía, dataviz, a11y. No implementas el frontend (eso es Mirador); entregas el sistema que él implementa. Voto narrativo final de Bea.

## Entregables de este primer encargo
1. **2-3 rutas de identidad** del observatorio (nombre público —puede diferir de "datapoble"—, wordmark, atributos, moodboard, tono). Registro: serio pero legible por un alcalde *y* un vecino; territorio de montaña, no corporativo. → **Bea elige una.**
2. **Tokens iniciales** (color + tipografía con buenas diacríticas catalanas y cifras tabulares) en `design-system/tokens/`, exportables a CSS (Style Dictionary). *Es el contrato que consume Mirador.*
3. **Paleta cartográfica** de "exposición/presión": secuencial **perceptualmente uniforme + segura para daltonismo**, con su leyenda. (El método de clasificación —cuantiles vs Jenks— lo acordamos tú y yo.)

Trabaja contra los **datos del prototipo** (`docs/data-sources.md`) para ver colores sobre dato real.

## Acceptance / DoD
- [ ] Bea aprueba una ruta de identidad.
- [ ] Tokens compilando a variables CSS, consumidos por un componente de prueba.
- [ ] El mapa del prototipo re-coloreado con la paleta nueva (mockup).

## Out of scope (este encargo)
- Sistema completo de dataviz, editorial/scrollytelling, a11y full → fases F2/F3 (ver brief).
- Implementar el frontend (Mirador).

## Coordinación
- **Rama:** `feat/llegenda-identity`. **Identity-inline:** `git -c user.name="Llegenda" -c user.email="llegenda@datapoble.local"`.
- Empareja con Mirador (tokens) y conmigo (paletas/clasificación de mapas).
- PR a `main` (o entrega de assets), CI verde, review mío + voto de Bea en la marca.

— Talaia
