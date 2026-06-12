# Renoms al contracte semàntic: Exposició / Capacitat / Impacte + provenance honesta

**Fecha:** 2026-06-11
**Autora:** Sondeig (dades/contracte) — executat per Talaia
**Para:** Talaia (review/merge) · Bea
**Tema:** PR-A2 — completa el Pas 2 de la spec de consultora 2 (§1.4) a la **font de veritat** (`semantic/metrics.yml`), després del PR-A (capa messages, #94).
**Status:** fet, verificat (export + check + build + preview glossari/resum) / handoff

## Contexto
El PR-A (#94) va netejar la capa `messages`, però el `/resum` i el `/glossari` encara mostraven «índex IETR», «stock/impact» i la procedència «datapoble (calculat) — Indicadors derivats i índex IETR». Aquests textos NO vénen de messages: vénen del **contracte** (`metrics.yml`), que l'exportador `tools/export_web_municipis.py` embeda al dataset `data/web/municipis.bergueda.json` (label/definicio/nota + `source` = «organisme — producte»).

## Què he fet (`semantic/metrics.yml`)
- **Provenance dels derivats** (bloc `sources.datapoble`): `organisme` «datapoble (calculat)» → **«indicador derivat»**; `producte` «Indicadors derivats i índex IETR» → **«vegeu la metodologia»**. Resultat a tota mètrica derivada: **«indicador derivat — vegeu la metodologia»** (treu el nom intern «datapoble» de la UI; §1.4).
- **IETR**: label → **«Exposició (IETR)»**; definicio i nota reescrites amb **capacitat/impacte** (la nota deixa de liderar amb «stock»: «0,5·capacitat (estructura preparada) + 0,5·impacte (empremta realitzada)»).
- **IETR_rank**: label → **«Rànquing d'exposició»** (coherent amb #94).
- **IETR_stock**: label (+ label_ca/label_es) → **«Capacitat · component estructural»**.
- **IETR_impact**: label (+ label_ca/label_es) → **«Impacte · component de pressió»**.
- Els termes tècnics (`stock`/`impact`) es **conserven a P3**: definicions-component, notes i `synonyms` de IETR_stock/IETR_impact (la jerga és a casa seva al glossari; spec §1.4).
- **Claus internes intactes**: `IETR`, `IETR_stock`, `IETR_impact`, `IETR_rank` segueixen sent les columnes del mart; només canvia el text públic.

## Re-export
- `python tools/export_web_municipis.py` → `data/web/municipis.bergueda.json` regenerat (31 municipis · 52 mètriques). Els marts parquet ja hi eren; cap valor inventat (l'export no toca dades, només propaga labels del contracte).
- Verificat: al dataset, 0 ocurrències de «datapoble (calculat)» / «Índex d'Exposició Turística» / «IETR · component» / «Rànquing IETR»; presents les noves.

## Verificación
- `npm run check` → **1104 fitxers, 0/0**. `npm run build` → OK (el precheck copia el dataset nou a `static/`).
- Preview **/resum**: 0 «stock», 0 «índex IETR», 0 «datapoble (calculat)»; «indicador derivat» i «exposició» presents.
- Preview **/glossari**: «Exposició (IETR)», «Capacitat · component estructural», «Impacte · component de pressió», «indicador derivat — vegeu la metodologia» tots ✓; residus vells a 0.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] Amb això el **Pas 2 (renoms) queda complet** (messages #94 + contracte). Següent: Pas 0 («el rang és la dada» + «no concloent» → cas Berga −2%) i slug (Pas 1; la Bea confirma que cap URL numèrica ha circulat → cost zero).
- [ ] (Pas 0) test CI de llista negra de jerga «above the fold» blindarà aquests renoms.

## Enlaces
- `semantic/metrics.yml` · `data/web/municipis.bergueda.json` · `tools/export_web_municipis.py`
- precede: `bitacora/2026-06-11_renoms-publics_mirador.md` (#94) · spec: memòria `reference-consultora2-especificacio`

— Sondeig
