# Pas 4 · Disseny de bases per tipus territorial + validació ETCA

**Fecha:** 2026-06-11
**Autora:** Talaia (coord) · disseny amb sprint de recerca (workflow wf_61bc8375) · decisions de la Bea
**Tema:** arquitectura de l'escala a Catalunya (spec consultora 2 §2 + §2.3 + §11 + §12). Contracte de disseny abans d'escriure el model.
**Status:** disseny APROVAT (decisions de la Bea preses) / pendent d'execució

## Arquitectura — 3 nivells (concretats contra el repo)

**Nivell A — bases oficials de Catalunya com a ALARMA (no per estimar).**
Valors-àncora CAT: residus **~482 kg/hab** (ARC 2024, canònic), vidre **~24 kg/hab** (ARC 2024), elèctric domèstic **~1.264 kWh/hab** (DERIVAT: GWh ICAEN 2023 / població; no publicat → marcar com a derivat amb fórmula). Les bases endògenes actuals (410/1224/26,5, de viles Berguedà IETR<5) es queden per al model de 3 capes; el Nivell A és un guarda-raïls. Materialització: taula `bases_oficials_cat` {metrica, valor, any, font, es_derivat, rang} + test de CI que salta si la mitjana ponderada se'n desvia.

**Nivell B — classificador `tipus_territorial` (8 tipus + flag `micromunicipi`<250).**
Capa NOVA i SEPARADA de la `tipologia` comportamental existent: `tipologia` = *com s'habita* (pressió, z-scores), `tipus_territorial` = *què és* (estructura geogràfica estable). Columna determinista nova, regles per ordre (residual «interior rural» l'últim). 6/8 tipus = dada directa (micromunicipi=padró; costaner=llista Territori; AMB=llista; densitat+altitud=Idescat; capital comarcal=llista curada; zona climàtica=CTE). 2 = proxy (corona metro=mobilitat obligada cens 2011→fallback sistema urbà; agroindustrial=CCAE >5.000 hab→proxy elèctric industrial ICAEN). **És el pont de l'escala**: nivell d'agregació per heretar esperats calibrats.

**Nivell C — esperats per regressió robusta + indicador d'excés.**
`esperat = f(covariables NO del costat de la presència)`. REGLA DURA: prohibits com a predictors % no principal, places RTC, IETR_stock/impact, vidre_hab, gap_pernocta (són el que volem mesurar). Covariables admeses: renda (INE ADRH 2023, ~tots fins secció censal), altitud (Idescat), zona climàtica CTE (proxy graus-dia), gas natural municipal (ICAEN), hab_per_hab, índex envelliment (EMEX), `tipus_territorial` (efecte fix). **Indicador: excés = observat − esperat** per senyal; **incertesa = banda p10–p90** (substitueix l'interim ±10% de la fitxa, Pas 0a). Necessita N a escala Catalunya per ser estable → obliga el carril dades.

**Calibratge (§2.3, transversal):** coeficient senyal→persones per tipus contra **ETCA**; validació held-out → taula pública (Spearman ρ + error medià per tipus) a /metodologia; **go/no-go**.

## Decisions de la Bea (2026-06-11)
1. **Carril dades EN SILENCI** (escollit): validació ETCA del pilot ARA + ingerir covariables/ETCA de Catalunya **offline, sense publicar**. El producte web segueix sent Berguedà. Ingerir dades de Catalunya ≠ obrir el web a Catalunya.
2. **Go/no-go = ρ≥0,7 i error≤15%** (confirmat): presència ABSOLUTA («gent que el padró no veu» en xifra) només si el tipus valida prou bé contra ETCA; si no, només índexs relatius + «encara no ho mesurem prou bé aquí».
3. Defaults tècnics acceptats (criteri Talaia): ARC canònic / Idescat rang; elèctric «derivat» visible; no unificar llindar 250 (estructura) amb 75 (soroll); any de referència explícit a cada baseline.

## Dos carrils (pilot ↔ escala)
- **Carril PRODUCTE** (Berguedà): tot el que es publica. Hi viu el primer pas (ETCA dels 8) i el Nivell A.
- **Carril DADES** (offline, no publicat): covariables + ETCA Catalunya, regressió i calibratge per tipus. No es publica fins passar el go/no-go.
- **Regla d'or:** cap municipi mostra presència absoluta calibrada fins que el seu **tipus** passi ρ≥0,7 i error≤15%.

## Primer pas (pilot, esforç S) — EXECUCIÓ següent
Ingerir **ETCA/EPE Idescat** (SSV `id=epe n=9522`, anual, by=mun) per als **8 munis Berguedà ≥1.000 hab** (Berga, Gironella, Puig-reig, Avià, Bagà, Casserres, Cercs, Olvan) + Berguedà comarcal + CAT. Materialitzar `int_etca_municipi`; taula de validació `carrega_funcional_est` vs ETCA i `poblacio_pernocta_est` vs (resident+estacional) → Spearman ρ + error medià; publicar a /metodologia. **Primera validació EXTERNA discriminant** (avui l'única és Spearman(IETR,residus), ~circular). Honestedat: els 23 <1.000 (Castellar, Gósol, Saldes — els turístics extrems) NO tenen ETCA municipal → hereten el model del tipus amb flag «sense validació externa directa» + àncora comarcal.

## Buits de dada coneguts
ETCA municipal només ≥1.000 hab (exclou els turístics extrems); ETCA trimestral només >5.000 hab+capitals (no estacionalitat municipal al Berguedà); estacionalitat municipal sense font oberta (ICAEN/ARC anuals); RFDB exclou <1.000 (usar INE ADRH); graus-dia no publicats (proxy altitud/CTE); model de recollida no a l'open data ARC; OSM infra-mapeja (mantenir fora del mart_core, ODbL); CCAE fi amb secret estadístic; OD mobilitat municipal només cens 2011.

## Riscos clau
Circularitat si una covariable de presència s'escola al Nivell C (auditar predictors); sobre-validació amb 8 munis (els fàcils, cap turístic extrem → ρ enganyós; separar mètriques per tipus); falsa precisió en recalibrar (banda p10–p90 + held-out); barreja `tipus_territorial`↔`tipologia` (columnes+UI separades); mescla d'anys de referència (marcar-los); dispersió d'esforç (carril dades = recerca de baixa prioritat fins que la Bea prioritzi).

## Enllaços
- Recerca completa: workflow `wf_61bc8375` (output a tasks/wmfz01fhj). Spec: memòria `reference-consultora2-especificacio` (§2). ETCA: `bitacora/2026-06-10_etca-epe-validacio-externa_talaia.md`.

— Talaia 🌊
