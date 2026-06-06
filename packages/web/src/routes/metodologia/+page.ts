/**
 * Càrrega de dades de la pàgina de metodologia pública.
 *
 * Tira del dataset real (forma `MunicipisDataset`, font: Sondeig) NOMÉS per a les metadades
 * del contracte de cada indicador: label (ca/es), unitat, font i data, i la procedència
 * (oficial 🟦 / inferència 🟪). Així la pàgina NO codifica fonts ni dates a mà: cada fitxa surt
 * del mateix contracte semàntic (semantic/metrics.yml) que consumeix la resta del web. El text
 * explicatiu (què mesura, fórmula llegible) són missatges i18n de funcionalitat (copy nou).
 *
 * Prerender-safe: usa el `fetch` de SvelteKit sobre l'actiu estàtic, com la resta de rutes.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const dataset = await loadMunicipisDataset(fetch);
	return { dataset };
};
