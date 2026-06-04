/**
 * Indicadors seleccionables al mapa coroplètic (F2).
 *
 * Subconjunt del catàleg del contracte orientat a la lectura territorial:
 *  - IETR (índex normalitzat) → cuantils (palette.md §5).
 *  - magnituds crues → Jenks: % habitatge no principal, establiments/1000 hab, residus kg/hab/any.
 *
 * Les ETIQUETES no es codifiquen aquí: vénen del catàleg de mètriques del contracte
 * (MetricDef.label) via el dataset. Aquí només triem QUINES claus i en quin ordre editorial.
 */

import type { MetricKey } from '$lib/contract/types';

/** Claus de mètrica pintables al mapa, en ordre editorial (IETR primer). */
export const MAP_INDICATORS: MetricKey[] = [
	'IETR',
	'pct_noprincipal',
	'rtc_per_1000hab',
	'kg_hab_any'
];

/** Indicador per defecte en obrir el mapa. */
export const DEFAULT_INDICATOR: MetricKey = 'IETR';
