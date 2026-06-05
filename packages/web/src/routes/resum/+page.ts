/**
 * Càrrega de dades del "resum".
 *
 * Llegeix les dades REALS dels 31 municipis (forma `MunicipisDataset`), font de Sondeig
 * (`data/web/municipis.bergueda.json`, copiat a static/ pel prebuild) via `$lib/data/dataset`
 * amb el `fetch` de SvelteKit (prerender-safe). La forma i la resta de la pantalla no canvien
 * respecte del mock: només canvia l'origen de les dades.
 */
import { loadMunicipisDataset, FEATURED_INE5 } from '$lib/data/dataset';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const dataset = await loadMunicipisDataset(fetch);
	return {
		dataset,
		featured: {
			castellar: dataset.municipis[FEATURED_INE5.castellar],
			berga: dataset.municipis[FEATURED_INE5.berga]
		}
	};
};
