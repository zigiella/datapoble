# Renoms públics (capa de missatges): de l'idioma intern a l'idioma de carrer

**Fecha:** 2026-06-11
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea
**Tema:** Pas 2 de l'especificació de consultora 2 (§1.4 taula de copies), part **messages**. Primer dels PRs de la spec.
**Status:** fet, verificat (check + build + preview) / handoff

## Contexto
La consultora 2 demana baixar la jerga de planta: a P1/P2 res de sigles (IETR, stock, impact). La taula §1.4 fixa els renoms públics. Aquest PR aplica els que viuen a `messages/{ca,es}.json` (la capa que controla Mirador). El que viu al **contracte** (`metrics.yml`) va a part (vegeu Pendiente → PR-A2).

## Què he fet (`messages/{ca,es}.json`, 28 claus en total)
- **Frase mare** → literal de la spec §6: «El padró diu qui consta. Els rastres diuen qui hi és. riusdegent mesura la distància.» (ES anàleg). ⚠️ «mesura» és més fort que l'anterior «fa visible» — **a confirmar per la Bea** (vot narratiu).
- **IETR → «Exposició»** als llocs públics: `nav_index`, `screen_index`, `map_ind_ietr` («Exposició (IETR)»), `muni_blk_ietr`, `resum_rank` («Rànquing d'exposició»), `resum_ietr_scale`, `card_rank_label`, `resum_axis_lo` (treu «IETR 0»). IETR es conserva com a cognom o a P3/glossari.
- **stock → «capacitat» / impact → «impacte»** a la constel·lació: `resum_constel_title` («Quina capacitat té × quin impacte rep»), `resum_constel_lede`, `constel_aria`, `constel_x`, `constel_y`, `constel_q_sense_stock` («Impacte sense capacitat clàssica»), `muni_blk_ietr_sub` («Capacitat (estructura) i impacte (pressió realitzada)»).
- **Població invisible → «Gent que el padró no veu (estimació)»** com a **etiqueta de mètrica** (`map_ind_pernocta`); «població invisible» es conserva com a nom d'**història/secció** (map_intro, caveats, met_*) — exactament com diu la spec.

## Verificación (preview, prod build)
- `npm run check` → **1104 fitxers, 0/0**. `npm run build` → OK.
- Preview /resum: renderitzen ✓ el títol «Quina capacitat té × quin impacte rep», la frase mare «riusdegent mesura la distància», el nav «Exposició» i «Rànquing d'exposició».

## Decisiones
- **Split per jurisdicció:** aquest PR només toca `messages` (Mirador). Els renoms del **contracte** (`metrics.yml`: provenance «datapoble (calculat)» → «indicador derivat», labels IETR_stock/IETR_impact, nota de fórmula amb stock/impact) van a PR-A2 perquè canvien la font de veritat i **obliguen a re-exportar** `municipis.bergueda.json` + afecten el glossari (P3). Fins llavors, el /resum mostrarà una barreja temporal (KPI «índex IETR» del dataset vell).
- Renoms d'etiqueta, NO de claus internes: `IETR_stock`/`IETR_impact`/`pernocta` segueixen sent les claus del contracte; només canvia el text públic. La tipologia `buit_administratiu` ja era fora de la UI (#79).

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] **Bea:** confirmar «mesura la distància» (vs «fa visible»).
- [ ] **PR-A2 (contracte, Sondeig):** `metrics.yml` renoms + re-export del dataset + verificar glossari/metodologia. Neteja l'«índex IETR»/«stock» residual del /resum.
- [ ] (Pas 0) test CI de llista negra de jerga «above the fold» — quan existeixi, blindarà aquests renoms.

## Enlaces
- `packages/web/messages/{ca,es}.json`
- spec: `reference-consultora2-especificacio` (memòria) · triatge workflow 2026-06-11 (wf_55675964)

— Mirador
