# Neteja de components de mapa orfes (seguiment Fase 2)

**Fecha:** 2026-06-06
**Autora:** Mirador
**Para:** Talaia (review + merge)
**Tema:** `packages/web` — eliminar `MapIndicatorPicker.svelte` i `MapLegend.svelte`, que van quedar sense cap referència en reescriure `/mapa` a alta fidelitat.
**Status:** avance

## Contexto
A la Fase 2 (PR #28 + retocs #30, ja a `main`) la pàgina `/mapa` es va reescriure a alta
fidelitat seguint el handoff final de la DA. La nova `mapa/+page.svelte` usa un **`<select>`
natiu** (`.map-toolbar .select`) i una **llegenda inline** amb les classes `.map-legend` /
`.map-cls` del design-system, en lloc dels dos components que feia servir abans. Això va deixar
`MapIndicatorPicker.svelte` i `MapLegend.svelte` **orfes**. La decisió de no esborrar-los en
aquell PR (per mantenir-lo focalitzat) i de fer-ho en un PR separat ja estava registrada a
`bitacora/2026-06-06_da-mapa-paletes_mirador.md` (§«Decisiones para Talaia» punt 1 i Pendiente).

## Qué hicimos / decidimos
- **Verificat** que cap dels dos components es referencia enlloc del repo (`src`, tests, stories,
  barrels): `grep` a tot `C:\DATA\PETS\datapoble`. Els únics resultats són **bitàcoles** (registre
  històric), cap fitxer de codi. No hi ha fitxers `*.test.*` / `*.spec.*` / `*.stories.*` al web,
  ni cap barrel `index.*` a `components/`, ni cap import dinàmic per ruta.
- **Eliminats** `packages/web/src/lib/components/MapIndicatorPicker.svelte` (1.764 B) i
  `MapLegend.svelte` (5.936 B) — 271 línies en total.
- Es **conserven** la resta de components de mapa, que sí que s'usen: `ChoroplethMap.svelte`,
  `MapTooltip.svelte`, `ContourField.svelte`.

## Por qué
Codi mort confon (sembla que forma part de la vista quan no), embruta el `grep` i pot divergir
del contracte real (p. ex. `MapLegend` tenia la seva pròpia còpia de la lògica de rangs). La
llegenda i el selector en viu ja viuen a la pàgina, derivats de la **mateixa** classificació que
pinta el canvas; mantenir versions orfes només és deute. Esborrar-los tanca el seguiment de la
Fase 2 sense afectar res que es renderitzi.

## Verificación
- `npm run check` (worktree net, `npm ci`) → **0 errors, 0 warnings** (833 fitxers).
- `npm run build` → **prerender net** amb `adapter-static`, build OK (exit 0).
- CI esperat verd: job `web build + check`.

## Pendiente
- [ ] **Talaia:** revisar i mergear.

## Enlaces
- Seguiment de: `bitacora/2026-06-06_da-mapa-paletes_mirador.md` (§Decisiones per Talaia, punt 1)
- Pàgina que els va deixar orfes: `packages/web/src/routes/mapa/+page.svelte` (`<select>` natiu +
  llegenda inline `.map-legend`/`.map-cls`)
