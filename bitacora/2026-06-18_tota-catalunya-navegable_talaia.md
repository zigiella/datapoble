# Tota Catalunya navegable — catàleg + cercador + fitxes de tot el país

**Data:** 2026-06-18
**Autora:** Talaia (encarna Mirador/web)
**Latido (Bea):** «a tope» (treballar la cua del pla de llançament).
**Status:** a la porta del PR (branca `feat/tota-catalunya-navegable`). Tanca P0 #2 i #3 de `next.md`.

## Què he fet
La base de «tota Catalunya»: qualsevol veí pot **cercar** el seu poble i **arribar** a una fitxa real
(dada/rang on n'hi ha, «sense dades encara» digne a la resta).

1. **Catàleg de tots els munis** (`scripts/copy-data.mjs` · `buildCataleg`) → `static/data/
   municipis-cataleg.json` (cens de noms+codis dels **947**, derivat de la geometria oficial; sempre
   al repo, independent dels marts). Contracte `$lib/contract/cataleg.ts`.
2. **Cercador a tot el país** (`MuniSearch`): cerca sobre el catàleg (947), no sobre els 31 del
   dataset; els del Berguedà mantenen el xip de tipologia. Abast i18n actualitzat.
3. **Fitxes de tot Catalunya** (`municipi/[slug]/+page.ts`): `entries()` prerenderitza els **947**
   (slugs del catàleg, amb guarda de col·lisió que trenca el build si dos xoquen); `load()` resol
   QUALSEVOL slug → ine5 + nom via catàleg (Berguedà ràpid → catàleg → rang). La fitxa mostra el nom
   real fins i tot sense dades (`data.nom`).

## Troballa d'slug (i fix de contracte)
El geojson porta l'article ENGANXAT (`l'Hospitalet`) mentre el dataset/pernocta el porten al final
(`Hospitalet de Llobregat, l'`). Sense tocar res, donarien slugs diferents (`lhospitalet` vs
`l-hospitalet`). **Fix a `toSlug`:** un article inicial `l'` amb apòstrof rep separador → totes dues
convencions **convergeixen**. Verificat (rèplica fidel): 947 slugs únics, **0 col·lisions**, i els 31
del Berguedà i els 82 coberts **casen** amb el geojson (cap URL existent trencada). Un apòstrof intern
(`n'Hug`) es manté com fins ara.

## Verificat
- `svelte-check`: 0 errors / 0 warnings.
- `build`: OK en **1m46s** (de ~10s; el prerender de ~1.894 pàgines de municipi —947×2 locales— hi
  afegeix ~90s, acceptable per a estàtic). 947 fitxes/locale.
- Per HTML prerenderitzada: Abella de la Conca (Lleida, sense dades) → nom + «Sense dades encara»;
  l'Hospitalet (cobert) → rang + ETCA; Berga (Berguedà) → fitxa completa; home → abast «tots els
  municipis de Catalunya».

## No verificat (declarat)
La interacció EN VIU del cercador (client-side): el preview headless s'ennuega amb la home (mapa
WebGL). L'índex es deriva del catàleg carregat i svelte-check passa; cal el cop d'ull de Bea al
desplegament (escriure un poble de fora del Berguedà i comprovar que hi navega).

— Talaia 🌊
