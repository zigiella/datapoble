/**
 * Càrrega de dades del "resum".
 *
 * Avui llegeix el MOCK (src/lib/mock/municipis.ts), que té la forma del contracte.
 * Punt d'enganxament: quan el pipeline publiqui el mart o l'API estigui llesta,
 * es canvia aquesta funció per un `fetch` a l'endpoint/artefacte; la forma
 * (`MunicipisDataset`) i la resta de la pantalla no canvien.
 */
import { getMunicipisDataset, FEATURED_INE5 } from '$lib/mock/municipis';
import type { PageLoad } from './$types';

export const load: PageLoad = () => {
	const dataset = getMunicipisDataset();
	return {
		dataset,
		featured: {
			castellar: dataset.municipis[FEATURED_INE5.castellar],
			berga: dataset.municipis[FEATURED_INE5.berga]
		}
	};
};
