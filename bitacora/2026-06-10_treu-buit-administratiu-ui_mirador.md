# Treu «buit administratiu» de la UI pública (àlies → indeterminat)

**Fecha:** 2026-06-10
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Sondeig (FYI: la DADA i el classificador NO canvien; només la presentació)
**Tema:** pegat de presentació demanat pel triatge del `vuelta-tuerca` i votat per la Bea: no mostrar l'etiqueta «buit administratiu» a la cara pública.
**Status:** fet, verificat / handoff

## Contexto
El triatge (workflow de Talaia) i la consultora: etiquetar «buit administratiu» Fígols (41 hab, 760 kg residus/hab — la petjada més alta de la comarca) i Montclar (593) és autocontradictori i citable en contra. La consultora recomana treure-ho de la UI; la **Bea ho va votar** (treure'l ara, mostrar-lo com a neutre / `indeterminat`). El rework de tipologia a 3 camps + 9 etiquetes (que ho resol de fons) és **fer_després**.

## Què he fet (només presentació, 1 fitxer)
A `packages/web/src/lib/map/tipologia.ts` (punt únic de presentació que consumeixen fitxa, mapa, llegenda, resum i mirall):
- Tret `buit_administratiu` de `TIPOLOGIA_ORDER` → ja no és una categoria pròpia de la llegenda (de 6 a 5 arquetips) ni té color blau propi al mapa.
- Afegit `UI_ALIAS = { buit_administratiu: 'indeterminat' }` aplicat a `tipologiaMeta()` i a `tipologiaMatchExpression()`: els municipis amb aquesta tipologia es presenten EXACTAMENT com `indeterminat` (gris càlid neutre, etiqueta «Indeterminat», blurb honest), **no** com a «sense dada».
- Conservat el tipus `TipologiaValue` amb `buit_administratiu` (la dada l'emet) i les claus i18n `tipo_buit_administratiu_*` (orfes ara; es netejaran amb el rework).

## Per què així
La Bea va votar «mostrar-lo com a neutre, com indeterminat». Col·lapsar-lo a `indeterminat` és més honest que inventar un calaix nou: diu «no el presentem com un tipus segur», que és cert. Sense tocar el mart ni la dada → 0 risc de pipeline, reversible quan arribi el rework. Afecta Fígols (08080) i Montclar (08130).

## Verificación
- `npm run check` (svelte-check) → **1096 fitxers, 0 errors, 0 warnings**.
- `npm run build` (adapter-static, prerender) → **OK**.
- Lògica: `tipologiaMeta('buit_administratiu')` → meta d'`indeterminat`; el `match` de MapLibre acoloreix `buit_administratiu` amb el gris d'`indeterminat`; la llegenda té 5 entrades.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (fer_després) rework de tipologia 3 camps + 9 etiquetes: substitueix aquest àlies i reclassifica Fígols/Montclar amb un calaix honest (p.ex. «senyals contradictòries»). Llavors netejar les claus i18n `tipo_buit_administratiu_*` orfes.

## Enlaces
- `packages/web/src/lib/map/tipologia.ts`
- `bitacora/2026-06-10_restauracio-talaia_talaia.md` (triatge)

— Mirador
