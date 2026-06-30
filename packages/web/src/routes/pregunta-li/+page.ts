/**
 * Càrrega de la pàgina «Pregunta-li» (`/pregunta-li` · `/es/pregunta-li`).
 *
 * Tira del dataset real (contracte semàntic, font: Sondeig) NOMÉS per construir els
 * xips d'exemple amb etiquetes d'indicador reals (mateixa idea que el `/metrics` de
 * l'API, però servit com a actiu estàtic → prerender-safe i sense dependre de l'API
 * viva). La crida real a `/ask` és client-side i no passa per aquí.
 *
 * Si el dataset no hi és, la pàgina segueix funcionant amb una llista d'exemples
 * canònics de reserva (vegeu el component): mai una pantalla trencada.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { MetricKey, MetricDef } from '$lib/contract/types';
import type { PageLoad } from './$types';

/**
 * Indicadors (claus del contracte) que volem oferir com a exemples, en ordre de
 * preferència: població, gap de pernocta (l'indicador estrella), IETR i residus.
 * Coherent amb el brief. Si alguna no és al dataset, se salta.
 */
const EXAMPLE_KEYS: MetricKey[] = ['poblacio', 'gap_pernocta_pct', 'pct_noprincipal', 'kg_hab_any'];

export const load: PageLoad = async ({ fetch }) => {
	let metricLabels: Array<{ key: MetricKey; label: MetricDef['label'] }> = [];
	try {
		const dataset = await loadMunicipisDataset(fetch);
		metricLabels = EXAMPLE_KEYS.filter((k) => dataset.metrics[k]).map((k) => ({
			key: k,
			label: dataset.metrics[k].label
		}));
	} catch {
		// Sense dataset: el component cau als exemples de reserva. Cap error visible.
		metricLabels = [];
	}
	return { metricLabels };
};
