/**
 * Càrrega de dades del mapa.
 *
 * - dataset: dades REALS dels 31 municipis del Berguedà, forma `MunicipisDataset`
 *   (font: Sondeig, `data/web/municipis.bergueda.json`, copiat a static/ pel prebuild).
 *   Es carrega via `$lib/data/dataset` amb el `fetch` de SvelteKit (prerender-safe).
 * - geojson: geometria OFICIAL dels municipis del Berguedà (static/geo/…, INE/IGN), servida
 *   com a actiu estàtic. `fetch` de SvelteKit funciona en prerender i al client.
 *
 * El join dataset↔geometria és per `ine5` (els 31 codis quadren 1:1).
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { FeatureCollection } from 'geojson';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const dataset = await loadMunicipisDataset(fetch);
	const res = await fetch('/geo/bergueda-municipis.geojson');
	const geojson = (await res.json()) as FeatureCollection;
	return { dataset, geojson };
};
