/**
 * Indicadors seleccionables al mapa coroplètic (F2).
 *
 * Subconjunt del catàleg del contracte orientat a la lectura territorial:
 *  - gap_pct (gap població real vs padró) → DIVERGENT centrat a 0 (titular de riusdegent).
 *  - poblacio_real_est (presència humana estimada) → Jenks (magnitud crua).
 *  - IETR (índex normalitzat) → cuantils (palette.md §5).
 *  - magnituds crues → Jenks: % habitatge no principal, establiments/1000 hab, residus kg/hab/any.
 *
 * Les ETIQUETES no es codifiquen aquí: vénen del catàleg de mètriques del contracte
 * (MetricDef.label) via el dataset. Aquí només triem QUINES claus i en quin ordre editorial.
 */

import type { MetricKey } from '$lib/contract/types';

/**
 * Claus de mètrica pintables al mapa, en ordre editorial.
 * El gap població real↔padró és l'indicador estrella de riusdegent → encapçala la llista
 * i és el que es veu primer en obrir el mapa.
 */
export const MAP_INDICATORS: MetricKey[] = [
	'gap_pct',
	'poblacio_real_est',
	'IETR',
	'pct_noprincipal',
	'rtc_per_1000hab',
	'kg_hab_any'
];

/** Indicador per defecte en obrir el mapa: el gap (titular del projecte). */
export const DEFAULT_INDICATOR: MetricKey = 'gap_pct';
