# Constel·lació: arregla l'encavalcament de l'eix Y + copy més clar (follow-up #81)

**Fecha:** 2026-06-10
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea (feedback + vot de copy)
**Tema:** dos retocs sobre la constel·lació del Resum després de veure-la desplegada (captura de la Bea).
**Status:** fet, verificat (build) / handoff

## Contexto
La Bea, mirant `/es/resum`: (1) **els textos s'encavalquen** — el rètol de l'eix Y horitzontal a dalt a l'esquerra xocava amb l'etiqueta del quadrant «HUELLA SIN STOCK CLÁSICO» (el copy més llarg del PR #81 ho va empitjorar); (2) els copies **«lo que tiene preparado» / «lo que se nota»** no s'acaben d'entendre (massa vagues: preparat per a què? es nota com?).

## Què he fet
- **Layout:** l'eix Y passa a **vertical a l'esquerra** (`rotate(-90)`, dins el marge esquerre) i l'eix X es **centra** a baix. Ja no s'encavalquen amb les etiquetes dels quadrants. Cap canvi a les posicions dels quadrants ni dels punts.
- **Copy (mantenint stock/impact, com va votar la Bea):**
  - eix X: `lo que tiene preparado (stock)` → **`preparado para recibir gente (stock)`** (ca: `preparat per rebre gent (stock)`).
  - eix Y: `lo que ya se nota (impact)` → **`rastro que ya se nota (impact)`** (ca: `rastre que ja es nota (impact)`).
  - lede actualitzat en coherència. Les glosses dels 4 quadrants (preparat/es nota) segueixen sent coherents amb els nous eixos (no calen canvis).

## Verificación
- `npm run check` → **1100 fitxers, 0 errors, 0 warnings**. `npm run build` → OK.
- Layout confirmat amb `npm run preview` (captura).

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] Si la Bea prefereix un altre wording d'eixos, és canvi d'1 línia per locale.

## Enlaces
- `packages/web/src/lib/components/StockImpactScatter.svelte` · `packages/web/messages/{ca,es}.json`
- bitàcola germana: `2026-06-10_constel-tooltip-textos_mirador.md` (PR #81)

— Mirador
