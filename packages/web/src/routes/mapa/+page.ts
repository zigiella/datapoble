/**
 * Càrrega de dades del mapa.
 *
 * - dataset: MOCK amb forma de contracte (src/lib/mock/municipis.ts). Punt d'enganxament:
 *   quan el mart/API publiqui els valors per municipi, es canvia per un fetch; la forma
 *   (MunicipisDataset) no canvia.
 * - geojson: geometria OFICIAL dels municipis del Berguedà (static/geo/…, INE/IGN), servida
 *   com a actiu estàtic. `fetch` de SvelteKit funciona en prerender i al client.
 */
import { getMunicipisDataset } from '$lib/mock/municipis';
import type { FeatureCollection } from 'geojson';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const dataset = getMunicipisDataset();
	const res = await fetch('/geo/bergueda-municipis.geojson');
	const geojson = (await res.json()) as FeatureCollection;
	return { dataset, geojson };
};
