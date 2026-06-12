# Pas 1 · URLs slug llegibles (ine5 = clau interna)

**Fecha:** 2026-06-11
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea
**Tema:** Pas 1 de l'spec de consultora 2 (§8.1): URLs de municipi amb **slug llegible** en lloc del codi INE. Fet ARA (pre-llançament): la Bea confirma que **cap URL numèrica ha circulat** → cost zero, sense redireccions 301.
**Status:** fet, verificat (check + build + HTML prerenderitzat) / handoff

## Contexto
Les fitxes eren `/municipi/08052/`. La spec vol `/ca/municipi/castellar-de-nhug/` (i `/es/...`): el slug és la cara pública; **l'`ine5` segueix sent la clau interna** (dades, contracte, API). Moment ideal ara que no hi ha públic ni SEO acumulat (el primer enllaç que vegi Google/premsa ja serà el bo).

## Què he fet
- **`$lib/contract/slug.ts`** (nou): `toSlug(nom)` determinista — minúscules, sense accents (`\p{M}`), sense apòstrofs, espais→guions, **article final reordenat** ("Quar, la"→`la-quar`; "Pobla de Lillet, la"→`la-pobla-de-lillet`; "Castellar de n'Hug"→`castellar-de-nhug`). + `slugForIne5()` i `buildSlugIndex()` (índex bidireccional slug↔ine5).
- **Route renombrat** `municipi/[ine5]` → `municipi/[slug]` (`git mv`, historial conservat).
  - `+page.ts`: `entries()` genera els 31 **slugs** (via `buildSlugIndex`) per prerenderitzar; `load` resol `params.slug` → `ine5` i en treu la fila.
  - `+page.svelte`: picker i miralls enllacen per slug; `ine5` (intern) segueix usant-se per a la lògica.
- **Enllaços actualitzats** a slug: `/resum` (extrems), `/mapa` (clic→fitxa via `slugForIne5`, i el CTA del tooltip via `toSlug(nom)`).
- **Guarda de COL·LISIÓ**: `buildSlugIndex` llança si dos municipis cauen al mateix slug; corre a `entries()` (build) → un xoc trenca el build = **test de col·lisió a CI** (spec §8.1; a escala Catalunya, sufix de comarca — futur).

## Verificación
- `npm run check` → **0/0**. `npm run build` → OK; **`entries()` ha generat 31 slugs sense col·lisió** i ha prerenderitzat `build/municipi/<slug>/index.html` + `build/es/municipi/<slug>/` (31+31).
- HTML prerenderitzat: `/resum` enllaça a `/municipi/berga` i `/municipi/castellar-de-nhug` (slugs); la fitxa `castellar-de-nhug` carrega («Castellar de n'Hug» + rang/no-concloent); **cap enllaç `/municipi/NUMERO` residual**.
- Sanity de `toSlug` sobre noms reals: Avià→avia, Sagàs→sagas, Gósol→gosol, Sant Jaume de Frontanyà→sant-jaume-de-frontanya, Castell de l'Areny→castell-de-lareny ✓.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (§8.1, a part) **sitemap.xml per idioma** + **hreflang `x-default`** per fitxa + **og:image per municipi** — additius, següent passa de SEO.
- [ ] Comparador `/compara/<a>-vs-<b>/` (§8.2) — quan toqui.
- [ ] Renames oficials de municipi (rars): generarien slug nou + redirect del vell; sense públic encara, no aplica.

## Enlaces
- `packages/web/src/lib/contract/slug.ts` · `packages/web/src/routes/municipi/[slug]/{+page.ts,+page.svelte}` · `mapa/+page.svelte` · `resum/+page.svelte`
- spec: memòria `reference-consultora2-especificacio` (§8.1)

— Mirador
