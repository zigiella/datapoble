/**
 * Pont entre els tokens de dada del design-system i el canvas de MapLibre.
 *
 * Per què existeix: dins del canvas WebGL de MapLibre els colors han de ser literals
 * (les CSS custom properties --dp-* no s'hi resolen). Aquí repliquem els hex de les rampes
 * de dada (seqüencial "exposició" --dp-exposure-0..5 i divergent del gap --dp-div2-0..6, teal↔porpra)
 * i en mostregem N colors. La llegenda (HTML) sí que pot usar les variables, però usem els mateixos hex perquè
 * mapa i llegenda coincideixin pixel a pixel.
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

/**
 * Stops de la rampa DIVERGENT del GAP (espill de --dp-div2-0..6, família teal↔PORPRA, CVD-safe).
 * DA final ronda 2 (Bea): la rampa del gap és teal↔porpra, NO teal↔marró. La porpra lliga amb
 * --dp-prov-derived (#7A5BA6 = inferència): el costat «població que el padró no veu» és inferència.
 * Teal (negatiu: menys gent que el padró) → neutre (gap≈0) → porpra (positiu: població invisible).
 * L'índex 3 (#EFEEE8) és el neutre i s'alinea amb el `center` (0) de la classificació.
 * (La família teal↔marró —--dp-div-*— queda com a llegat; ja no es fa servir al render del gap.)
 */
export const DIVERGING_STOPS = [
	'#0F6E66', // -3  teal fort  (gap molt negatiu: menys gent que el registre)
	'#4FA8A0', // -2
	'#B9DED9', // -1  teal clar
	'#EFEEE8', //  0  neutre (≈ mitjana / gap 0)
	'#CDB3DD', // +1  porpra clar
	'#9466B6', // +2
	'#5E3A86' // +3  porpra fort (gap molt positiu: màxima població invisible)
] as const;

/** Índex del stop neutre dins DIVERGING_STOPS (gap=0). */
const DIV_NEUTRAL = 3;

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

/** Interpola una llista de stops en `t` ∈ [0,1] (sRGB lineal a trams). */
function sampleStops(stops: readonly string[], t: number): string {
	const x = Math.max(0, Math.min(1, t)) * (stops.length - 1);
	const i = Math.floor(x);
	const f = x - i;
	if (i >= stops.length - 1) return stops[stops.length - 1];
	const a = hexToRgb(stops[i]);
	const b = hexToRgb(stops[i + 1]);
	return rgbToHex(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f);
}

/**
 * N colors equiespaiats de la rampa seqüencial "exposició" (clar→fosc = baix→alt).
 * Per a n=1 retorna el color mitjà. Per defecte, n=5 (estàndard del sistema).
 */
export function rampColors(n: number): string[] {
	if (n <= 1) return [sampleStops(EXPOSURE_STOPS, 0.5)];
	return Array.from({ length: n }, (_, i) => sampleStops(EXPOSURE_STOPS, i / (n - 1)));
}

/**
 * Colors per a un coroplètic DIVERGENT, un per classe, ancorats al neutre (gap=0).
 *
 * A diferència de `rampColors` (que reparteix la rampa uniformement), aquí el color de cada
 * classe depèn del SIGNE i la MAGNITUD del seu valor representatiu respecte al `center`:
 *  - classes a l'esquerra del center → teal (com més negatiu, més fosc/saturat);
 *  - la classe que conté o limita amb el center → neutre (#F5F5F0);
 *  - classes a la dreta → càlid (com més positiu, més marró fosc).
 * L'escala de cada costat es normalitza pel seu propi extrem perquè la intensitat sigui
 * comparable a banda i banda encara que la distribució sigui asimètrica (gap +176% vs −21%).
 *
 * @param edges  talls exposats de la classificació: [min, ...breaks, max] (length = classes+1).
 * @param center punt neutre (0 per al gap).
 */
export function divergingColors(edges: number[], center: number): string[] {
	const classes = Math.max(1, edges.length - 1);
	if (classes === 1) return [sampleStops(DIVERGING_STOPS, 0.5)];

	// Posició normalitzada [0,1] del stop neutre dins la rampa (3/6 = 0.5 amb 7 stops).
	const neutralT = DIV_NEUTRAL / (DIVERGING_STOPS.length - 1);
	// Valor representatiu (punt mitjà) de cada classe i extrems per normalitzar cada costat.
	const mids = Array.from({ length: classes }, (_, i) => (edges[i] + edges[i + 1]) / 2);
	const negSpan = Math.max(center - edges[0], 1e-9); // amplitud del costat negatiu
	const posSpan = Math.max(edges[edges.length - 1] - center, 1e-9);

	return mids.map((mid) => {
		if (mid < center) {
			// k: 0 (a tocar del neutre) → 1 (extrem negatiu). t baixa de neutralT cap a 0 (teal fosc).
			const k = Math.min(1, (center - mid) / negSpan);
			return sampleStops(DIVERGING_STOPS, neutralT * (1 - k));
		}
		if (mid > center) {
			// k: 0 → 1 (extrem positiu). t puja de neutralT cap a 1 (marró fosc).
			const k = Math.min(1, (mid - center) / posSpan);
			return sampleStops(DIVERGING_STOPS, neutralT + (1 - neutralT) * k);
		}
		return DIVERGING_STOPS[DIV_NEUTRAL];
	});
}
