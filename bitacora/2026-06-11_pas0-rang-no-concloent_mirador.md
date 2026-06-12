# Pas 0 · «el rang és la dada» + «no concloent» a la fitxa (família pernocta)

**Fecha:** 2026-06-11
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea
**Tema:** Pas 0 de l'spec de consultora 2 (§10 «Població invisible: invertir la jerarquia»), primera llesca: la família pernocta es publica en RANG, no com a punt amb signe. Resol la pregunta del **Berga −2%**.
**Status:** fet, verificat (check + build + preview Berga/Castellar) / handoff

## Contexto
La spec §10: per a tot indicador inferit, **el rang és la dada; el punt és una cortesia**. I si el rang creua el 0, el valor és **«no concloent»** i no es mostra mai com a número amb signe (els caveats no viatgen amb la captura; el rang sí). La fitxa mostrava `gap_pernocta_pct` com a punt amb signe → Berga «−2%» i Puig-reig «−5%» semblaven pèrdues reals quan són soroll.

## Què he fet (`municipi/[ine5]/+page.svelte`, només UI)
- **Banda de sensibilitat** calculada a la UI a partir dels valors existents (cap dada nova): com que `poblacio_pernocta_est ∝ 1/base`, amb sensibilitat de base **±10%** la banda és `[est/1,1 , est/0,9]`. La constant `GAP_SENSITIVITY = 0.1` està documentada i és **interina**: el §2 la substituirà pel **p10–p90 del model d'esperats**.
- **Regla «no concloent»**: el rang del gap creua 0 ⟺ `|gap_pernocta_pct| < 10` (derivat de la banda). En aquest cas, `gap_pernocta` i `gap_pernocta_pct` mostren **«≈ 0 · no concloent»** (neutre), mai un signe.
- **Rang com a titular** a les tres files de la capa pernocta (`poblacio_pernocta_est`, `gap_pernocta`, `gap_pernocta_pct`): «baix … alt» + «(punt mig X)» petit i secundari.
- Nota de bloc que ho explica (`ficha_range_note`) + i18n nou (`ficha_inconcludent`, `ficha_midpoint`, `ficha_range_note`, ca/es).
- **Frase mare:** revertida a **«fa visible»** (decisió de la Bea: «fa visible» > «mesura»).

## Verificación (preview)
- **Berga (08022):** pernocta «15.613 … 19.082 hab. (punt mig 17.174)»; gap absolut i % → **«≈ 0 · no concloent»** ✓ (padró 17.539; punt mig per sota → soroll, no pèrdua).
- **Castellar de n'Hug (08052):** rang **concloent** positiu — pernocta «198 … 242 (punt mig 218)», gap «+19 … +46% (punt mig +31)» ✓.
- `npm run check` → **1107 fitxers, 0/0**. `npm run build` → OK.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (Pas 0, resta) **mapa per límit inferior** del rang («com a mínim») + **accessibilitat AA** (taula alternativa per viz, teclat, contrast) + **confiança-com-nitidesa** com a firma visual.
- [ ] (§2) substituir la sensibilitat ±10% interina pel p10–p90 del model d'esperats (bases per tipus + ETCA).
- [ ] La família pernocta absoluta (`poblacio_pernocta_est`) NO és «no concloent» quan el gap ho és: és un recompte positiu, sempre rang (correcte).

## Enlaces
- `packages/web/src/routes/municipi/[ine5]/+page.svelte` · `messages/{ca,es}.json`
- spec: memòria `reference-consultora2-especificacio` (§10) · backlog Berga: pregunta resolta

— Mirador
