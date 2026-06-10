# Coherència de copy: terminologia pública a «rastres» + «Transformació demogràfica»

**Fecha:** 2026-06-10
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea (vot del terme)
**Tema:** unificar la terminologia pública a **«rastres»** (vot de la Bea) i renombrar la secció **«Origen i arrelament» → «Transformació demogràfica»**.
**Status:** fet, verificat / handoff

## Contexto
El repàs del pla va trobar incoherència: la **fitxa** ja deia «Tres rastres de presència», però el **resum** i la **metodologia** encara deien «les 3 capes». La Bea va decidir el terme canònic: **«rastres»** (més evocador, marca la inferència, lliga amb la narrativa padró↔rastres). I va aprovar el rename de la secció d'origen.

## Què he fet (només textos i18n d'usuari, `ca.json` + `es.json`)
- **Títols de secció** → «Tres rastres de presència»: `resum_grp_capes` («Tres rastres · inferència»), `met_block_capes`.
- **Prosa** «3 capes» → «els tres rastres» (amb concordança de gènere): `map_gap_tooltip_caveat`, `muni_lede`, `muni_honesty`, `glo_intro_note`, `met_capes_intro` (+ «cada capa»→«cada rastre»), `met_confianca_what`, `met_honesty_1` (+ «rastres físics»→«senyals físics» per no repetir).
- **Rename de secció**: `muni_blk_origen` i `met_block_origen` → «Transformació demogràfica» (coherent amb `met_origen_intro`, que ja deia «TRANSFORMACIÓ DEMOGRÀFICA, no extranjería»).
- **Claus i18n intactes** (només canvien els valors). **Comentaris interns de codi** («model de 3 capes», L1/L2/L3) **es deixen** — és el nom tècnic del model, no el text públic.

## Verificación
- `npm run check` → **1100 fitxers, 0 errors, 0 warnings**. `npm run build` → OK (paraglide recompila).

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (opcional, baix) alinear els comentaris de codi a «rastres» si es vol coherència fins al detall intern.

## Enlaces
- `packages/web/messages/ca.json` · `es.json`
- bitàcoles germanes: `2026-06-10_constel-tooltip-textos_mirador.md`

— Mirador
