/**
 * Càrrega de dades de la pàgina de glossari pública (`/glossari` · `/es/glossari`).
 *
 * Mateix patró que la metodologia: tira del dataset real (`MunicipisDataset`, font: Sondeig)
 * NOMÉS per a les metadades del contracte de cada indicador (label, unitat, font, data,
 * dimensió, procedència i —quan l'export l'emeti— la definició). Així el glossari és
 * literalment «el contracte llegible»: cap terme, definició, font ni xifra es codifica a
 * mà; tot surt del mateix contracte semàntic que consumeix la resta del web → sempre sincronitzat.
 *
 * Prerender-safe: usa el `fetch` de SvelteKit sobre l'actiu estàtic, com la resta de rutes.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const dataset = await loadMunicipisDataset(fetch);
	return { dataset };
};
