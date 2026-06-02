# Spec · Frontend del observatorio — Talaia a Mirador

**Fecha:** 2026-06-02
**Autora:** Talaia
**Para:** Mirador (frontend)
**Tema:** portar las 6 pantallas del prototipo a una app SvelteKit + MapLibre con i18n, contra los tokens de Llegenda y los datos del contrato.
**Status:** spec

## Contexto
El prototipo es un HTML estático (Plotly + datos embebidos). Lo profesionalizamos: SvelteKit, mapas vectoriales, sistema de diseño, idiomas. Las pantallas del prototipo son la referencia funcional.

## Scope (tu jurisdicción)
`packages/web`. No defines diseño (es de Llegenda; tú implementas contra sus **tokens**). No defines métricas ni IA.

## Entregables
1. **App SvelteKit** + **MapLibre GL** (mapa coroplético) + **Observable Plot** (charts). TypeScript.
2. **i18n con Paraglide (inlang):** locales **ca + es** (en/fr ampliables), **rutas `/ca` `/es`**, default `ca`, selector de idioma, formato de cifras/fecha con `Intl`.
3. **Las 6 pantallas:** resumen (KPIs + Castellar↔Berga), mapa (coroplético con selector de indicador), índice IETR (ranking + scatter de validación r=0,87), day-tripper, **política** (con los caveats ecológicos visibles), y **"Pregúntale"** (llama a la API de Brúixola).
4. **A11y AA** (con Llegenda): **tabla-alternativa para cada gráfico**, navegación por teclado, `prefers-reduced-motion`.

## Integración / contrato
- Consume **`design-system` tokens** (Llegenda) y los **datos** (artefactos parquet/JSON del pipeline o la API). Mientras no estén listos, arranca contra **datos mock** con la **forma de `semantic/metrics.yml`** (mismas claves/columnas).
- Etiquetas de indicadores: vienen del **contrato** (`label.ca`/`label.es`), no las hardcodees.

## Test plan
- [ ] `pnpm build` verde; **vitest** (lógica) + **Playwright** (a11y: foco, contraste, tabla-alternativa).
- [ ] La home no se rompe al alternar ca↔es (expansión de texto).
- [ ] El mapa pinta los 31 (y escala a CAT) desde el geojson + mart.
- [ ] El panel "Pregúntale" muestra respuesta **+ procedencia**.

## Out of scope (para v1.1+)
- El sistema de diseño (Llegenda). · La lógica de IA (Brúixola; tú consumes su API). · El pipeline (Sondeig). · Scrollytelling avanzado (F3).

## Coordinación
- **Rama:** `feat/mirador-web`. **Identity-inline:** `git -c user.name="Mirador" -c user.email="mirador@datapoble.local"`.
- Empareja con Llegenda (tokens) y Brúixola (API). Puedes empezar **ya** contra mock + tokens iniciales.
- PR a `main`, CI verde, yo reviso.

— Talaia
