# Bloc Licitacions a la fitxa de municipi (+ DRY de les etiquetes)

**Fecha:** 2026-06-12
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea
**Tema:** tercera i última peça de «Licitacions al web» (decisió Bea: secció + fitxa). Aquí, el **bloc a la fitxa**. Amb això «ambdues» queda complet.
**Status:** fet, verificat (check + build + HTML prerenderitzat ca/es) / handoff

## Què he fet
- **Helper compartit `$lib/format/licitacions.ts`**: `temaLabel`, `lecturaLabel`, `eurCurt` (etiquetes i18n + format d'euros). La secció `/licitacions` s'ha **refactoritzat** per usar-lo (treu els mapes locals duplicats → DRY).
- **Fitxa `municipi/[slug]`**:
  - `+page.ts`: carrega l'artefacte i hi busca el municipi (`lic`), opcional i prerender-safe.
  - `+page.svelte`: bloc nou **«Licitacions»** (després de Miralls) amb la dependència del Consell (lectura), el que contracta de propi (nº + import), els serveis que rep del Consell (import + els temes principals), i —si `no_contracta_propi`— la **nota honesta** (centralització + biaix de font, no mala gestió).
- i18n ca/es: `muni_lic_sub/_dependencia/_propi/_temes/_nota` (reusa `lic_*` per a temes/lectures/serveis).

## Verificació
- `npm run check` → **0/0**; `npm run build` → OK.
- HTML prerenderitzat: **Berga** (autònom) mostra el bloc amb 577 contractes propis; **Gironella** (no_contracta_propi) mostra la nota + «sobretot en: aigua, mobilitat, residus». ES correcte.

## Estat de «Licitacions al web»
- ✅ Pont de dades (#104, Cabal) · ✅ Secció `/licitacions` (#105, Mirador) · ✅ Bloc de fitxa (aquest). **Complet.**

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (vot #7 Bea) ara que Licitacions és al nav, valorar treure els stubs inerts «Índex IETR»/«Excursionista de dia»/«Política» de la capçalera d'escriptori.
- [ ] Quan es reconstrueixi el pipeline complet, integrar licitacions al mart (avui artefacte standalone).

## Enlaces
- `$lib/format/licitacions.ts` · `routes/municipi/[slug]/{+page.ts,+page.svelte}` · `routes/licitacions/+page.svelte` (refactor) · `messages/{ca,es}.json`
- secció: `bitacora/2026-06-12_licitacions-seccio_mirador.md` (#105) · dada: `…licitacions-export_cabal.md` (#104)

— Mirador
