# 3 capes al mapa + pàgina de metodologia pública

**Fecha:** 2026-06-06
**Autora:** Mirador
**Para:** Talaia (review + merge), Llegenda (consum del design-system)
**Tema:** `packages/web` — el model de **3 capes** (mètode v2) arriba al **selector del mapa** i neix la **pàgina de metodologia pública** (`/metodologia` · `/es/metodologia`).
**Status:** avance / handoff
**Branca:** `feat/mirador-3capes-metodologia`

## Contexto
L'indicador estrella ha evolucionat de **una sola capa** (residus) a **tres** (docs/poblacio-real-metode.md v2 + semantic/metrics.yml), ja materialitzades al JSON web per Sondeig (`gap_pernocta_pct`, `carrega_total_est`, `index_turisme`, `vidre_hab`, `kwh_hab`, `confianca`). La meva feina: **surtir-les al web** honestament i **explicar-les en públic**. **Cap canvi a `data/`, `semantic/`, `packages/ai`, `packages/design-system` ni als workflows.** Tot dins `packages/web`.

## Què he fet

### 1. Les 3 capes al selector del mapa (`MAP_INDICATORS`)
`lib/map/indicators.ts` — el selector passa a ser, en ordre editorial:
1. **`gap_pernocta_pct`** «**Població invisible (%)**» — DEFECTE. Qui PERNOCTA sense constar al padró (via elèctric domèstic). Paleta **divergent `--dp-div2`** (teal↔porpra, centrat a 0; porpra = població que el padró no veu).
2. **`carrega_total_est`** «Càrrega humana total» — càrrega TOTAL (residus, inclou excursionistes de dia). Paleta **seqüencial terra `--dp-exposure`** (Jenks).
3. **`index_turisme`** «Pressió turística» — hostaleria (vidre, 0–100). Seqüencial `--dp-exposure`.
4. **IETR** · 5. **% habitatge no principal** · 6. **Residus kg/hab/any** (sense canvis).

**Tret del selector el `gap_pct` antic** (gap de càrrega d'una capa): era redundant amb `carrega_total_est` i, dit «gap», es confondria amb el gap de pernocta. Queda al contracte com a àlies de compatibilitat però **no es pinta** (evitem dos «gap»).

Canvis mínims encadenats:
- **`contract/types.ts`** — `MetricKey` amb les claus noves (`gap_pernocta_pct/gap_pernocta/poblacio_pernocta_est`, `carrega_total_est`, `index_turisme`, `kwh_hab`, `vidre_hab`).
- **`lib/map/classify.ts`** — `gap_pernocta_pct`/`gap_pernocta` a `DIVERGING_KEYS` (rampa divergent centrada a 0). `gap_pernocta_pct` a `SIGNED_RATIO_PCT_KEYS`: ve com a **ràtio 0–1** amb `format: percent`, i es mostra com a **percentatge amb signe** (+87 %, −2 %), no "0,9 %". Els antics es conserven per compatibilitat.
- **`mapa/+page.svelte`** — `INDICATOR_LABEL` a les 3 capes; el **hero** pinta ara les cotes reals del **gap de pernocta** (no del de càrrega); **caveats per indicador**: cada capa derivada (pernocta/càrrega/turisme) ensenya el seu caveat d'honestedat propi, i els indicadors **oficials** (% no principal, residus) o l'**índex** (IETR) no en porten. La **srcline** surt ara del contracte (`def.source · def.date`) per indicador.
- **Tooltip i llegenda** (`MapTooltip.svelte`, `MapLegend.svelte`) — `ESTIMATE_KEYS` inclou les 3 capes: totes mostren confiança + recordatori d'inferència. El tractament de **confiança baixa** (opacitat + tramat) i el «sense dada» (hatch) ja existien i s'apliquen igual; el caveat de pernocta és el que es veu per defecte.

### 2. Pàgina de metodologia pública (`/metodologia`, ca/es)
Nova ruta `routes/metodologia/{+page.ts,+page.svelte}`. Explica **cada indicador un per un**: *què mesura · com es calcula (fórmula) · font i data · oficial 🟦 o inferència 🟪*. Estructura per blocs amb el chrome del lloc (hero + `.ds-main`/`.ds-sec`, Archivo, tokens):
- **A** Demografia i habitatge · **B** Turisme reglat · **C** Les 3 capes de presència (amb intro pròpia: els 3 senyals físics, les bases de vall, el *catch* del vidre) · **D** IETR · **E** Energia · **F** Política · **★** Honestedat.
- El bloc C empella cada **senyal físic** amb la seva **capa**: elèctric→L1 pernocta, residus→L2 càrrega, vidre→L3 pressió turística, + confiança.
- **Font, data i procedència surten del contracte** (dataset real), no codificades a mà: la vora esquerra i el badge de cada fitxa es deriven del `source` amb `provenanceOf` (mateixa regla que mapa i resum). El text «què mesura / com es calcula» és copy i18n nou, fidel a metrics.yml i al doc v2.
- **Enllaçada des del peu** (`foot_link_method` → «Metodologia», abans inert) i afegida a la **nav de capçalera**.

`prerender = true` global → la ruta es genera per crawling des dels nous enllaços; **no cal tocar `prerender.entries`**. Confirmat: `build/metodologia/index.html` i `build/es/metodologia/index.html` existeixen.

### 3. i18n ca/es
Tot el text nou en ca i es (copy NOU de funcionalitat). Etiquetes d'indicador, lectura del color, caveats per capa i tot el contingut de metodologia. Reescrits `map_intro`/`map_lede_*`/`map_read_gap`/`map_gap_tooltip_caveat` perquè parlin de la **població invisible via elèctric** (abans deien "residus", del model v1).

## Verificació
- **`npm run check`** → 0 errors, 0 warnings (902 fitxers). **`npm run build`** → static OK, prerender complet. Cap `*/` espuri dins comentaris CSS.
- **Headless** (Chromium, `dev` al worktree, DOM determinista — el hover sobre el canvas MapLibre no és fiable headless, patró conegut; verifico per DOM/consola):
  - `/mapa/`: selector amb les **6 claus** correctes, **`gap_pct` absent**, per defecte `gap_pernocta_pct`; llegenda **divergent** «5 classes» amb talls reals amb signe (1a classe `−17 % – −5 %`); caveat de pernocta.
  - Commutació a `index_turisme` → llegenda **seqüencial Jenks** (1a classe `7,8–14,7`), caveat de turisme; a `carrega_total_est` → enters (`69–792`), caveat de càrrega; a `pct_noprincipal` (oficial) → **cap caveat de capa**.
  - `/metodologia/` (ca) i `/es/metodologia/` (es): 7 blocs, 17 fitxes, **9 inferència / 8 oficial**, bloc C amb senyals+capes aparellats, enllaç del peu i nav actius. **0 logs de consola.**

## Decisions per a Talaia (review)
- **`gap_pct` fora del selector** (no del contracte): segueix viu com a àlies de compatibilitat per a altres consumidors; només l'he retirat de la lectura del mapa per no duplicar «gap». Si el vols recuperar com a vista, és una línia a `MAP_INDICATORS`.
- **Procedència de derivats aritmètics**: `% habitatge no principal`, `hab/hab` i `establiments/1000` surten com a **inferència 🟪** a la metodologia perquè el seu `source` al contracte és «datapoble (calculat)». És **coherent amb la regla `provenanceOf`** i amb el que ja fa el `resum`. Si vols que els càlculs purament aritmètics sobre dades oficials es marquin diferent (p. ex. un 3r estat «derivat-directe»), és **decisió de contracte/Llegenda**, fora de la meva jurisdicció — ho deixo apuntat.
- **Caveat per indicador al mapa**: he fet que el primer caveat només aparegui per a les 3 capes derivades (amb el seu text específic). Els oficials i l'IETR mantenen només el caveat 2 (classes/geometria). Si prefereixes un caveat sempre visible, és trivial.
- He deixat la clau i18n `foot_link_method` («Metodologia IETR») òrfena (substituïda per `foot_link_method_to` = «Metodologia») per no arriscar; es pot esborrar en una neteja.
- **Headless del hover real**: segueix pendent per a un PR amb Playwright (el canvas MapLibre no respon bé a `mousemove` sintètics). La lògica de valor/format/llegenda està verificada numèricament.
