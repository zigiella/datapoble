# Pas 0 · accessibilitat: «veure com a taula» a les visualitzacions

**Fecha:** 2026-06-11
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea
**Tema:** Pas 0 de l'spec de consultora 2 (§1.5 «Accesibilidad como credibilidad»): tota visualització ha de tenir **alternativa en taula**. Tanca el gros del Pas 0.
**Status:** fet, verificat (check + build + preview constel·lació i mapa) / handoff

## Contexto
La spec §1.5: «toda visualización con alternativa en tabla (botón "veure com a taula"; gratis, los datos ya están en el cliente); navegación por teclado; contraste AA». Les dues viz vives (constel·lació i mapa coroplètic) eren només SVG/canvas → inaccessibles per a lector de pantalla i teclat. La taula és la via barata i honesta (les dades ja hi són).

## Què he fet (només UI, dades ja al client)
- **Constel·lació** (`StockImpactScatter.svelte`): botó **«Veure com a taula / Veure el gràfic»** que commuta el gràfic per una **taula accessible** (`<caption>`, `<th scope>`): Municipi · Capacitat · Impacte · Població · Confiança, els 31 municipis ordenats alfabèticament.
- **Mapa** (`mapa/+page.svelte`): botó **«Veure com a taula / Veure el mapa»** que commuta el mapa+llegenda per una taula de l'**indicador actiu**: Municipi · Valor (formatat al locale; etiqueta categòrica per a la tipologia) · Confiança, ordenats per valor desc (per nom si és categòric). Caption = nom de l'indicador. Cobreix també l'**atles** (és una opció del mateix selector).
- i18n nou: `viz_as_table`, `viz_as_chart`, `viz_as_map`, `tbl_municipi/capacitat/impacte/poblacio/confianca/valor` (ca/es).

## Verificación (preview)
- **/resum** constel·lació: toggle OK; taula amb **31 files**, capçaleres correctes, primera fila «Avià 0 8 2.263 alta».
- **/mapa**: toggle OK; taula amb **31 files**, caption «Gent que el padró no veu (%)», ordre per valor desc (Quar +189% · Sagàs +158% · Sta. Maria de Merlès +122%), columna confiança.
- `npm run check` → **1116 fitxers, 0/0** (taules i botons sense warnings a11y). `npm run build` → OK.

## Pendiente (cua del Pas 0)
- [ ] **Talaia:** review/merge.
- [ ] **Mapa per LÍMIT INFERIOR del rang** («com a mínim») + «no concloent» a la taula/colors del mapa per a `gap_pernocta_pct` — ho deixo amb el reframe del dropdown a pregunta (§1.3), perquè toca colors+llegenda+copy del mapa alhora. Avui la taula del mapa mostra el PUNT (igual que el color del mapa); coherent entre ells, però encara no amb el «no concloent» de la fitxa.
- [ ] **Teclat complet** al mapa MapLibre i **axe-core a CI** (auditoria AA completa) — hardening a part.
- [ ] Confiança-com-nitidesa: el mapa ja porta trama de baixa confiança i la constel·lació l'anell discontinu (convenció ja present); formalitzar-la com a firma única queda per a una passada de design-system.

## Enlaces
- `packages/web/src/lib/components/StockImpactScatter.svelte` · `packages/web/src/routes/mapa/+page.svelte` · `messages/{ca,es}.json`
- spec: memòria `reference-consultora2-especificacio` (§1.5)

— Mirador
