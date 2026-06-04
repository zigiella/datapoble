/**
 * Classificació coroplètica (datapoble · F2, Mirador).
 *
 * Materialitza l'spec de Llegenda i Talaia (packages/design-system/cartography/palette.md §5):
 *  - **5 classes per defecte**, sigui quin sigui el mètode.
 *  - **Cuantils** per a índexs normalitzats (IETR i derivats): ja són relatius a la distribució;
 *    objectiu = comparar rànquing.
 *  - **Jenks (natural breaks)** per a magnituds crues (kg_hab_any, pct_noprincipal,
 *    rtc_per_1000hab…): respecta els salts reals (l'outlier Castellar) i evita que un extrem
 *    aixafi la resta en una sola classe.
 *  - El "sense dada" NO és una classe de color: es pinta amb tramat (hatch) sobre --dp-nodata.
 *
 * El color comunica el mètode: la llegenda mostra sempre **mètode + nº de classes + font·data**.
 * Aquí calculem els TALLS i les ETIQUETES de rang; el pintat (rampa --dp-exposure-*) viu al
 * component de mapa, que pren 5 mostres de la rampa de 6 stops.
 */

import type { MetricFormat, MetricKey } from '$lib/contract/types';

export type ClassMethod = 'quantiles' | 'jenks';

/** Nombre de classes per defecte del sistema (decisió de Talaia, 2026-06-04). */
export const DEFAULT_CLASSES = 5;

/**
 * Mètode de classificació per clau de mètrica (palette.md §5).
 * Índexs normalitzats → cuantils; la resta (magnituds crues) → Jenks.
 * `guanya` és categòrica (text) i no entra al coroplètic seqüencial.
 */
const QUANTILE_KEYS = new Set<MetricKey>(['IETR', 'IETR_rank']);

export function methodFor(key: MetricKey): ClassMethod {
	return QUANTILE_KEYS.has(key) ? 'quantiles' : 'jenks';
}

/** Resultat de classificar una mètrica sobre el conjunt de municipis. */
export interface Classification {
	method: ClassMethod;
	/** Nombre de classes efectiu (pot ser < DEFAULT_CLASSES si hi ha pocs valors únics). */
	classes: number;
	/**
	 * Vores internes (length = classes - 1). El rang d'una classe i és
	 * [breaks[i-1], breaks[i]] amb el primer obert per baix pel min i l'últim pel max.
	 */
	breaks: number[];
	/** Mínim i màxim observats (per als extrems de l'escala de la llegenda). */
	min: number;
	max: number;
	/** Talls "exposats" per a la llegenda: [min, ...breaks, max]. */
	domain: number[];
	/** Nombre de valors numèrics no nuls usats (la resta són "sense dada"). */
	n: number;
}

/** Quantil lineal (interpolació tipus R-7) sobre una llista ja ordenada. */
function quantileSorted(sorted: number[], p: number): number {
	if (sorted.length === 0) return NaN;
	if (sorted.length === 1) return sorted[0];
	const h = (sorted.length - 1) * p;
	const lo = Math.floor(h);
	const hi = Math.ceil(h);
	return sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo]);
}

/** Talls per cuantils: classes-1 vores als percentils equiespaiats. */
function quantileBreaks(sorted: number[], classes: number): number[] {
	const breaks: number[] = [];
	for (let i = 1; i < classes; i++) {
		breaks.push(quantileSorted(sorted, i / classes));
	}
	return breaks;
}

/**
 * Jenks natural breaks (Fisher–Jenks per programació dinàmica), implementació clàssica.
 * Retorna les classes-1 vores internes. Per a N petit (≈31 municipis) és barat.
 */
function jenksBreaks(data: number[], nClasses: number): number[] {
	const sorted = [...data].sort((a, b) => a - b);
	const n = sorted.length;
	if (nClasses >= n) {
		// Cada valor (gairebé) a la seva classe: vores entre valors únics consecutius.
		const uniq = [...new Set(sorted)];
		return uniq.slice(1).map((v, i) => (v + uniq[i]) / 2).slice(0, nClasses - 1);
	}

	// Matrius de programació dinàmica (1-indexades com a l'algorisme canònic).
	const mat1: number[][] = Array.from({ length: n + 1 }, () => new Array(nClasses + 1).fill(0));
	const mat2: number[][] = Array.from({ length: n + 1 }, () =>
		new Array(nClasses + 1).fill(Infinity)
	);

	for (let j = 1; j <= nClasses; j++) {
		mat1[1][j] = 1;
		mat2[1][j] = 0;
	}

	for (let l = 2; l <= n; l++) {
		let s1 = 0; // suma de valors
		let s2 = 0; // suma de quadrats
		let w = 0; // recompte
		for (let m = 1; m <= l; m++) {
			const i3 = l - m + 1;
			const val = sorted[i3 - 1];
			w += 1;
			s1 += val;
			s2 += val * val;
			const variance = s2 - (s1 * s1) / w;
			const i4 = i3 - 1;
			if (i4 !== 0) {
				for (let j = 2; j <= nClasses; j++) {
					if (mat2[l][j] >= variance + mat2[i4][j - 1]) {
						mat1[l][j] = i3;
						mat2[l][j] = variance + mat2[i4][j - 1];
					}
				}
			}
		}
		mat1[l][1] = 1;
		mat2[l][1] = s2 - (s1 * s1) / w;
	}

	// Reconstrucció de les vores.
	const breaks: number[] = [];
	let k = n;
	for (let j = nClasses; j >= 2; j--) {
		const id = mat1[k][j] - 1; // índex (1-based) del primer element de la classe j
		// vora entre l'element id (últim de la classe inferior) i id+1
		breaks.push((sorted[id - 1] + sorted[id]) / 2);
		k = mat1[k][j] - 1;
	}
	return breaks.reverse();
}

/**
 * Classifica una sèrie de valors d'una mètrica.
 * @param values  valors crus (poden incloure null/undefined/NaN → "sense dada", s'ignoren).
 * @param method  cuantils o Jenks (per defecte segons la mètrica).
 * @param classes nombre de classes (per defecte 5).
 */
export function classify(
	values: Array<number | string | null | undefined>,
	method: ClassMethod,
	classes: number = DEFAULT_CLASSES
): Classification {
	const nums = values
		.map((v) => (typeof v === 'number' ? v : NaN))
		.filter((v) => Number.isFinite(v)) as number[];

	const sorted = [...nums].sort((a, b) => a - b);
	const min = sorted.length ? sorted[0] : 0;
	const max = sorted.length ? sorted[sorted.length - 1] : 0;
	const uniqueCount = new Set(sorted).size;
	const effClasses = Math.max(1, Math.min(classes, uniqueCount));

	let breaks: number[] = [];
	if (effClasses > 1) {
		breaks = method === 'quantiles' ? quantileBreaks(sorted, effClasses) : jenksBreaks(nums, effClasses);
		// vores estrictament creixents i dins [min,max]; desduplica per robustesa.
		breaks = breaks
			.filter((b) => b > min && b < max)
			.sort((a, b) => a - b)
			.filter((b, i, arr) => i === 0 || b !== arr[i - 1]);
	}

	return {
		method,
		classes: breaks.length + 1,
		breaks,
		min,
		max,
		domain: [min, ...breaks, max],
		n: nums.length
	};
}

/**
 * Índex de classe (0-based) per a un valor, donada una classificació.
 * Retorna -1 per a "sense dada" (no numèric). El valor == max cau a l'última classe.
 */
export function classOf(value: number | string | null | undefined, c: Classification): number {
	if (typeof value !== 'number' || !Number.isFinite(value)) return -1;
	for (let i = 0; i < c.breaks.length; i++) {
		if (value < c.breaks[i]) return i;
	}
	return c.breaks.length; // última classe
}

/**
 * Etiquetes de rang per classe, formatades segons el format de la mètrica i el locale.
 * length = classification.classes. Ex.: ["0–20", "20–41", …] amb cifres del locale.
 */
export function classRangeLabels(
	c: Classification,
	format: MetricFormat,
	locale: string
): string[] {
	const fmt = makeFormatter(format, locale);
	const edges = c.domain;
	const labels: string[] = [];
	for (let i = 0; i < c.classes; i++) {
		labels.push(`${fmt(edges[i])} – ${fmt(edges[i + 1])}`);
	}
	return labels;
}

/** Formatador d'un sol valor segons el format del contracte (Intl, locale-aware). */
export function makeFormatter(format: MetricFormat, locale: string): (n: number) => string {
	const loc = locale === 'es' ? 'es-ES' : 'ca-ES';
	switch (format) {
		case 'integer':
		case 'rank':
			return (n) => new Intl.NumberFormat(loc, { maximumFractionDigits: 0 }).format(n);
		case 'percent':
			return (n) =>
				new Intl.NumberFormat(loc, { maximumFractionDigits: 1 }).format(n) + '%';
		case 'decimal':
		case 'ratio':
			return (n) =>
				new Intl.NumberFormat(loc, {
					minimumFractionDigits: 1,
					maximumFractionDigits: 2
				}).format(n);
		default:
			return (n) => String(n);
	}
}
