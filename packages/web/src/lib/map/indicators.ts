/**
 * Indicadors seleccionables al mapa coroplètic (model de 3 capes · v2).
 *
 * L'indicador estrella de riusdegent ha evolucionat a TRES CAPES (docs/poblacio-real-metode.md v2)
 * que separen fenòmens diferents i NO s'han de confondre:
 *  - **L1 gap_pernocta_pct** — la «població invisible»: qui PERNOCTA al territori sense constar
 *    al padró (via consum elèctric domèstic). És una desviació amb signe → DIVERGENT centrat a 0
 *    (rampa teal↔porpra --dp-div2; porpra = positiu = població que el padró no veu). DEFECTE.
 *  - **L2 carrega_total_est** — la càrrega humana TOTAL (via residus, inclou excursionistes de
 *    dia). NO és «població»: és càrrega. Magnitud crua → seqüencial terra --dp-exposure (Jenks).
 *  - **L3 index_turisme** — la PRESSIÓ turística (hostaleria, via vidre/hab, 0-100). NO és
 *    població ni càrrega de persones. Índex normalitzat → seqüencial terra --dp-exposure.
 *
 * A més, la lectura territorial clàssica: IETR (índex), % habitatge no principal i residus kg/hab.
 *
 * S'ha RETIRAT del selector el `gap_pct` antic (gap de CÀRREGA d'una sola capa): ara és redundant
 * amb `carrega_total_est` i, dit «gap», es confondria amb el gap de pernocta. Queda al contracte
 * com a àlies de compatibilitat, però no es pinta (evitem dos «gap» al mapa).
 *
 * Les ETIQUETES no es codifiquen aquí: l'etiqueta editorial curta ve dels missatges i18n
 * (mapa/+page.svelte → INDICATOR_LABEL); la del contracte (MetricDef.label) és el fallback.
 * Aquí només triem QUINES claus i en quin ordre editorial.
 */

import type { MetricKey } from '$lib/contract/types';

/**
 * Claus de mètrica pintables al mapa, en ordre editorial.
 * Encapçala el gap de pernocta (L1, «població invisible»): és la nova signatura del projecte
 * i el que es veu primer en obrir el mapa. Després les altres dues capes (càrrega, pressió
 * turística) i la lectura territorial estructural.
 */
export const MAP_INDICATORS: MetricKey[] = [
	'gap_pernocta_pct',
	'carrega_total_est',
	'index_turisme',
	'IETR',
	'pct_noprincipal',
	'kg_hab_any'
];

/** Indicador per defecte en obrir el mapa: la població invisible (gap de pernocta, L1). */
export const DEFAULT_INDICATOR: MetricKey = 'gap_pernocta_pct';
