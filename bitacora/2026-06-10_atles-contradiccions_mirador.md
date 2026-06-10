# Atles de contradiccions: mapa de divergencia_senyals al /resum

**Fecha:** 2026-06-10
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea (decisió de placement)
**Tema:** ② del repàs — la peça grossa: un mapa que ressalta on els senyals físics d'un municipi es contradiuen. Converteix la incertesa en producte.
**Status:** fet, verificat (build + preview DOM) / handoff

## Contexto
El repàs del pla i el `vuelta-tuerca`: «atles de contradiccions» = mapa de `divergencia_senyals` (atenuant concordants, destacant contradictoris). La **Bea va decidir** que vivís com a **secció pròpia al `/resum`**.

## Què he fet
- **`/resum/+page.ts`**: el `load` ara porta `geojson` + `comarques` (mateixos assets estàtics que `/mapa`, INE/IGN; el navegador els cacheja entre pàgines).
- **`/resum/+page.svelte`**: nova secció **D «Atles de contradiccions»** que **reusa `ChoroplethMap`** amb `indicator='divergencia_senyals'` i classificació **Jenks** (`classify`/`methodFor`/`mapValue`). Fosc = més contradicció. Tooltip **mínim** propi (nom + `divergència/100`); fora del Berguedà, «sense dades encara». No replico tota la maquinària del `/mapa` (selector, llegenda multi-mode): versió lean.
- **i18n** (ca/es): `resum_atles_title`, `resum_atles_lede`, `resum_atles_legend`, `resum_atles_tip`.

## Per què `divergencia_senyals`
És el component de concordança del `confianca_score` exposat sol (0-100): 0 = els 3 z de presència (residus/elèctric/no-principal) concorden; 100 = es contradiuen. Pintar-ho en mapa fa l'incertesa **honesta i visible** — el moviment més riusgent-native.

## Verificación
- `npm run check` → **1105 fitxers, 0 errors, 0 warnings**. `npm run build` → OK (el **prerender de /resum amb el fetch del geojson passa**).
- **Preview en viu** (`/resum`): la secció «Atles de contradiccions» hi és i dins `.atles-map` munta un `.maplibregl-map` **amb `<canvas>`** (MapLibre renderitza). El **screenshot fa timeout** (pàgina de mapa massa pesada per a la captura headless) → verificat per DOM, no per imatge.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (② resta) bloc «Interpretació» (5 preguntes) — l'última peça de la ②.
- [ ] (millora) si es vol, tooltip que digui QUIN parell de senyals divergeix (avui `divergencia_senyals` és un sol 0-100; caldria exposar els z components).

## Enlaces
- `routes/resum/+page.{ts,svelte}` · `lib/components/ChoroplethMap.svelte` (reusat) · `lib/map/classify.ts`

— Mirador
