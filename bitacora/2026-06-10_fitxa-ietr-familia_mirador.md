# Fitxa: lectura IETR-família (estructura × empremta → quadrant)

**Fecha:** 2026-06-10
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge)
**Tema:** ② del repàs — treure l'IETR de número únic a la fitxa del municipi («no només 26,0»): afegir una lectura síntesi estructura (stock) × empremta (impact) + quadrant.
**Status:** fet, verificat (build + preview) / handoff

## Contexto
La fitxa ja llistava `IETR_stock`/`IETR_impact` com a KPIs, però sense la **lectura de quadrant** (que només existia a la constel·lació del Resum). El repàs del pla ho marcava com a pendent de la ②.

## Què he fet (`municipi/[ine5]/+page.svelte`, 1 fitxer)
Sota el número gran d'IETR, una línia de lectura: `stock {X} · impact {Y} — {quadrant} · {gloss}`. El quadrant es deriva amb la **mateixa semàntica** que la constel·lació (stock ≥ 50 × impact ≥ 50), **reusant les claus i18n `constel_q_*` / `constel_q_*_help`** (cap text nou; un sol lloc de veritat per a la gloss). Manté `stock`/`impact`.

## Verificación
- `npm run check` → **1100 fitxers, 0 errors, 0 warnings**. `npm run build` → OK.
- **Preview en viu** (`/es/municipi/08045`, Capolat): la línia mostra «stock 28 · impact 93 — Huella sin stock clásico · se nota sin estructura típica» (quadrant correcte: stock baix, impact alt). IETR gran = 60,5.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (② resta) narrativa mare (vot Bea) · atles de contradiccions · bloc «Interpretació».

## Enlaces
- `packages/web/src/routes/municipi/[ine5]/+page.svelte` · constel·lació (`StockImpactScatter.svelte`, mateixa semàntica)

— Mirador
