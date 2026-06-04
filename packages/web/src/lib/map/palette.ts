/**
 * Pont entre els tokens de dada del design-system i el canvas de MapLibre.
 *
 * Per què existeix: dins del canvas WebGL de MapLibre els colors han de ser literals
 * (les CSS custom properties --dp-* no s'hi resolen). Aquí repliquem els hex de la rampa
 * seqüencial "exposició" (packages/design-system/tokens/tokens.css → --dp-exposure-0..5)
 * i en mostregem N colors. La llegenda (HTML) sí que pot usar les variables, però usem
 * els mateixos hex perquè mapa i llegenda coincideixin pixel a pixel.
 *
 * Rampa seqüencial = 6 stops com a RECURS de color; el render coroplètic per defecte usa
 * 5 classes → es prenen 5 MOSTRES de la rampa (palette.md §5), no els 6 stops literals.
 */

/** Stops de la rampa seqüencial "exposició/pressió" (espill de --dp-exposure-0..5). */
export const EXPOSURE_STOPS = [
	'#FBF3D9',
	'#F3D9A0',
	'#E8B567',
	'#D98B3E',
	'#B5612A',
	'#7E3A1E'
] as const;

/** Color de "sense dada" (--dp-nodata); es renderitza amb tramat, no pla. */
export const NODATA = '#E3E3DE';

/** Tokens de basemap apagat (--dp-map-*) — el dada resalta, el mapa s'apaga. */
export const MAP = {
	land: '#F2F1EC',
	water: '#D8E2E4',
	boundary: '#B9BEB6',
	label: '#5A6066',
	highlight: '#1B212A'
} as const;

function hexToRgb(hex: string): [number, number, number] {
	const h = hex.replace('#', '');
	return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}
function rgbToHex(r: number, g: number, b: number): string {
	const c = (n: number) => Math.round(n).toString(16).padStart(2, '0');
	return `#${c(r)}${c(g)}${c(b)}`;
}

/** Interpola la rampa de 6 stops en `t` ∈ [0,1] (sRGB lineal a trams). */
function sampleRamp(t: number): string {
	const stops = EXPOSURE_STOPS;
	const x = Math.max(0, Math.min(1, t)) * (stops.length - 1);
	const i = Math.floor(x);
	const f = x - i;
	if (i >= stops.length - 1) return stops[stops.length - 1];
	const a = hexToRgb(stops[i]);
	const b = hexToRgb(stops[i + 1]);
	return rgbToHex(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f);
}

/**
 * N colors equiespaiats de la rampa (clar→fosc = baix→alt).
 * Per a n=1 retorna el color mitjà. Per defecte, n=5 (estàndard del sistema).
 */
export function rampColors(n: number): string[] {
	if (n <= 1) return [sampleRamp(0.5)];
	return Array.from({ length: n }, (_, i) => sampleRamp(i / (n - 1)));
}
