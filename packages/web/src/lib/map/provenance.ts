/**
 * Procedència del dada (contracte editorial: "cap número sense origen").
 *
 * Mapeja una MetricDef a la signatura visual `.prov--measured | --derived | --negative`
 * del design-system (sistema.css, tokens --dp-prov-*). Regla pràctica:
 *  - source que conté "datapoble (calculat)" / "calculat" → DERIVED (índex/inferència).
 *  - la resta (Idescat, RTC, ARC, ICAEN, Generalitat) → MEASURED (dada oficial directa).
 *  - sense valor numèric → NEGATIVE (sense dada / secret estadístic).
 */

import type { MetricDef } from '$lib/contract/types';

export type Provenance = 'measured' | 'derived' | 'negative';

export function provenanceOf(def: MetricDef | undefined, hasValue: boolean): Provenance {
	if (!hasValue) return 'negative';
	const src = (def?.source ?? '').toLowerCase();
	if (src.includes('calculat') || src.includes('datapoble')) return 'derived';
	return 'measured';
}
