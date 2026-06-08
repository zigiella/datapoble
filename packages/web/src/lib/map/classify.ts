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
 *  - **Divergent** per a desviacions amb signe (el gap població real↔padró): centrat a 0.
 *  - El "sense dada" NO és una classe de color: es pinta amb tramat (hatch) sobre --dp-nodata.
 *
 * El color comunica el mètode: la llegenda mostra sempre **mètode + nº de classes + font·data**.
 * Aquí calculem els TALLS i les ETIQUETES de rang; el pintat (rampes --dp-exposure-* / --dp-div-*)
 * viu al component de mapa, que pren les mostres de color corresponents.
 */

import type { MetricFormat, MetricKey } from '$lib/contract/types';

export type ClassMethod = 'quantiles' | 'jenks' | 'diverging' | 'categorical';

/** Nombre de classes per defecte del sistema (decisió de Talaia, 2026-06-04). */
export const DEFAULT_CLASSES = 5;

/**
 * Mètode de classificació per clau de mètrica (palette.md §5).
 * Índexs normalitzats → cuantils; desviacions amb signe (gap vs 0) → divergent centrat a 0;
 * la resta (magnituds crues) → Jenks.
 * `guanya` és categòrica (text) i no entra al coroplètic seqüencial.
 */
const QUANTILE_KEYS = new Set<MetricKey>(['IETR', 'IETR_rank']);

/**
 * Mètriques CATEGÒRIQUES (text amb un conjunt tancat d'arquetips): la `tipologia` d'habitança.
 * No es classifiquen amb talls numèrics — cada valor té el seu color propi (un per tipus, no rampa)
 * i una llegenda categòrica. El color comunica IDENTITAT (quin tipus), no ordre/magnitud.
 */
const CATEGORICAL_KEYS = new Set<MetricKey>(['tipologia']);

/**
 * Mètriques que són una DESVIACIÓ respecte a un punt neutre (0): el gap de PERNOCTA (població
 * invisible) i —per compatibilitat— el gap de càrrega antic.
 * gap=0 → no hi ha població invisible; >0 → població que el padró no veu (porpra); <0 → menys
 * gent que el padró (teal). Es classifiquen amb rampa divergent centrada a 0 (no Jenks ni
 * cuantils, que amagarien el signe). L1 (`gap_pernocta_pct`) és el cas que es pinta per defecte.
 */
const DIVERGING_KEYS = new Set<MetricKey>([
	'gap_pernocta_pct',
	'gap_pernocta',
	'gap_pct',
	'gap_abs'
]);

export function methodFor(key: MetricKey): ClassMethod {
	if (CATEGORICAL_KEYS.has(key)) return 'categorical';
	if (DIVERGING_KEYS.has(key)) return 'diverging';
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
	/**
	 * Punt neutre de la rampa divergent (només per `method='diverging'`): el valor (0)
	 * que separa el costat teal del càlid i marca quina vora és el zero. `undefined` per
	 * a mètodes seqüencials. La rampa de color s'ancora aquí (no al centre de l'escala).
	 */
	center?: number;
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
 * Talls per a una rampa DIVERGENT ancorada al `center` (per defecte 0).
 *
 * Una desviació amb signe (el gap població↔padró) no es pot classificar com una magnitud
 * crua: el missatge és "a quina banda del zero cau i quant". Per això:
 *  - el `center` (0) és SEMPRE una vora interna → cap classe barreja signe positiu i negatiu;
 *  - a cada costat es col·loquen sub-vores per cuantils dels valors d'aquell costat, de manera
 *    que la rampa teal (negatiu) i la càlida (positiu) reparteixen els municipis de forma
 *    equilibrada (i no que un sol outlier —Sant Jaume +176%— aixafi tota la banda càlida).
 *
 * El nombre d'interior breaks que rep cada costat és proporcional a quants municipis hi cauen
 * (mínim 1 si el costat té valors). Retorna les vores internes ordenades, amb el 0 inclòs.
 */
function divergingBreaks(data: number[], nClasses: number, center: number): number[] {
	const neg = data.filter((v) => v < center).sort((a, b) => a - b);
	const pos = data.filter((v) => v > center).sort((a, b) => a - b);
	// vores interiors a repartir, a banda del tall del propi center.
	const interior = Math.max(0, nClasses - 2);

	// Repartiment proporcional al recompte de cada costat (cada costat amb dades ≥ 1 vora).
	let nNeg = 0;
	let nPos = 0;
	if (neg.length && pos.length && interior > 0) {
		nNeg = Math.max(1, Math.round((interior * neg.length) / (neg.length + pos.length)));
		nNeg = Math.min(nNeg, interior - 1, Math.max(0, neg.length - 1));
		nPos = Math.min(interior - nNeg, Math.max(0, pos.length - 1));
	} else if (neg.length && interior > 0) {
		nNeg = Math.min(interior, Math.max(0, neg.length - 1));
	} else if (pos.length && interior > 0) {
		nPos = Math.min(interior, Math.max(0, pos.length - 1));
	}

	// Sub-vores per cuantils dins de cada costat (exclou els extrems del propi grup).
	const sub = (group: number[], count: number): number[] => {
		const out: number[] = [];
		for (let i = 1; i <= count; i++) out.push(quantileSorted(group, i / (count + 1)));
		return out;
	};

	const breaks = [...sub(neg, nNeg), center, ...sub(pos, nPos)];
	return breaks.sort((a, b) => a - b);
}

/**
 * Classifica una sèrie de valors d'una mètrica.
 * @param values  valors crus (poden incloure null/undefined/NaN → "sense dada", s'ignoren).
 * @param method  cuantils, Jenks o divergent (per defecte segons la mètrica via methodFor).
 * @param classes nombre de classes (per defecte 5).
 */
export function classify(
	values: Array<number | string | null | undefined>,
	method: ClassMethod,
	classes: number = DEFAULT_CLASSES
): Classification {
	// CATEGÒRIC: no hi ha talls numèrics. Els valors són cadenes (arquetips de tipologia) i el
	// color el resol el diccionari de tipologia, no una rampa. Retornem una classificació
	// degenerada (sense breaks, n = nombre de municipis amb categoria) perquè la pàgina/llegenda
	// puguin diferenciar el mode i comptar quants en tenen, sense intentar números sobre text.
	if (method === 'categorical') {
		const n = values.filter((v) => typeof v === 'string' && v !== '').length;
		return { method, classes: 0, breaks: [], min: 0, max: 0, domain: [], n };
	}

	const nums = values
		.map((v) => (typeof v === 'number' ? v : NaN))
		.filter((v) => Number.isFinite(v)) as number[];

	const sorted = [...nums].sort((a, b) => a - b);
	const min = sorted.length ? sorted[0] : 0;
	const max = sorted.length ? sorted[sorted.length - 1] : 0;
	const uniqueCount = new Set(sorted).size;
	const effClasses = Math.max(1, Math.min(classes, uniqueCount));

	// Punt neutre de la rampa divergent (gap respecte 0). Per a la resta de mètodes no aplica.
	const center = method === 'diverging' ? 0 : undefined;

	let breaks: number[] = [];
	if (effClasses > 1) {
		if (method === 'quantiles') breaks = quantileBreaks(sorted, effClasses);
		else if (method === 'diverging') breaks = divergingBreaks(nums, effClasses, center ?? 0);
		else breaks = jenksBreaks(nums, effClasses);
		// vores estrictament creixents i dins [min,max]; desduplica per robustesa.
		// El tall del center (0) es conserva encara que toqui un extrem: ancora el signe de la rampa.
		breaks = breaks
			.filter((b) => (b === center ? b >= min && b <= max : b > min && b < max))
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
		n: nums.length,
		center
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
 * Etiquetes de rang per classe, formatades segons la mètrica i el locale.
 * length = classification.classes. Ex.: ["0–20", "20–41", …] amb cifres del locale.
 * Rep la `key` per poder aplicar el format específic del gap (ràtio amb signe).
 */
export function classRangeLabels(
	c: Classification,
	format: MetricFormat,
	locale: string,
	key?: MetricKey
): string[] {
	const fmt = makeMetricFormatter(key, format, locale);
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

/**
 * Conjunt de claus que són una DESVIACIÓ amb signe sobre el padró (els gaps de població) i
 * s'han de mostrar amb el +/− explícit. El valor ja ve en escala 0-100 del contracte
 * (`gap_pernocta_pct = gap_pernocta / poblacio * 100`, igual que `pct_noprincipal`); aquí
 * NOMÉS hi afegim el signe perquè es llegeixi com una desviació respecte al padró (+31 %,
 * −2 %), no com un percentatge net. El ×100 ja NO viu al frontend: cap component cuina
 * l'escala (la convenció única és del contracte; vegeu docs/poblacio-real-metode.md).
 */
export const SIGNED_PCT_KEYS = new Set<MetricKey>(['gap_pernocta_pct', 'gap_pct']);

/**
 * Formatador sensible a la CLAU de mètrica (no només al format). Igual que `makeFormatter`
 * tret de les mètriques de desviació amb signe (els gaps): hi afegeix el +/− explícit. El
 * valor ja és 0-100 (com la resta de `percent`), així que NO el reescala. La resta de claus
 * deleguen al formatador per format.
 */
export function makeMetricFormatter(
	key: MetricKey | undefined,
	format: MetricFormat,
	locale: string
): (n: number) => string {
	if (key && SIGNED_PCT_KEYS.has(key)) {
		const loc = locale === 'es' ? 'es-ES' : 'ca-ES';
		return (n) =>
			new Intl.NumberFormat(loc, {
				maximumFractionDigits: 0,
				signDisplay: 'exceptZero'
			}).format(n) + ' %';
	}
	return makeFormatter(format, locale);
}
