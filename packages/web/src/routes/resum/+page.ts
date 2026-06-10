/**
 * Càrrega de dades del "resum".
 *
 * Llegeix les dades REALS dels 31 municipis (forma `MunicipisDataset`), font de Sondeig
 * (`data/web/municipis.bergueda.json`, copiat a static/ pel prebuild) via `$lib/data/dataset`
 * amb el `fetch` de SvelteKit (prerender-safe). La forma i la resta de la pantalla no canvien
 * respecte del mock: només canvia l'origen de les dades.
 */
import { loadMunicipisDataset, FEATURED_INE5 } from '$lib/data/dataset';
import type { FeatureCollection } from 'geojson';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	// geojson + comarques: per a l'atles de contradiccions (ChoroplethMap de divergencia_senyals).
	// Mateixos assets estàtics que /mapa (INE/IGN); el navegador els cacheja entre pàgines.
	const [dataset, munRes, comRes] = await Promise.all([
		loadMunicipisDataset(fetch),
		fetch('/geo/catalunya-municipis.geojson'),
		fetch('/geo/catalunya-comarques.geojson')
	]);
	const geojson = (await munRes.json()) as FeatureCollection;
	const comarques = (await comRes.json()) as FeatureCollection;
	return {
		dataset,
		geojson,
		comarques,
		featured: {
			castellar: dataset.municipis[FEATURED_INE5.castellar],
			berga: dataset.municipis[FEATURED_INE5.berga]
		}
	};
};
