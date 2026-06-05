/**
 * Loader del dataset REAL (datapoble · Mirador).
 *
 * Substitueix el mock (`$lib/mock/municipis`) per la càrrega de les dades reals dels
 * 31 municipis del Berguedà. La FONT és `data/web/municipis.bergueda.json` (la genera
 * Sondeig des dels marts: `tools/export_web_municipis.py`), copiada a `static/data/`
 * pel pas `prebuild` (`scripts/copy-data.mjs`). Es serveix com a actiu estàtic, igual
 * que la geometria — així el `fetch` de SvelteKit funciona EN PRERENDER i al client.
 *
 * La forma és exactament `MunicipisDataset` (mateix contracte que ja feia servir el web):
 * només canvia l'ORIGEN de les dades; ni els tipus ni la UI no canvien. Les etiquetes
 * (label.ca/.es, unit, note…) segueixen venint del dataset (= del contracte semàntic),
 * mai codificades a la UI.
 */

import type { MunicipiRow, MunicipisDataset } from '$lib/contract/types';

/** Ruta de l'actiu estàtic (la còpia que fa el prebuild des de data/web/). */
const DATA_URL = '/data/municipis.bergueda.json';

/** Tipus mínim de la funció `fetch` de SvelteKit (load) o del navegador. */
type FetchLike = (input: string) => Promise<Response>;

/**
 * Carrega el dataset real dels 31 municipis.
 * Punt d'unió: rep el `fetch` del `load` de SvelteKit (prerender-safe). Si l'actiu no
 * existeix (p. ex. un entorn sense el pas de còpia), llança amb un missatge accionable.
 */
export async function loadMunicipisDataset(fetchFn: FetchLike): Promise<MunicipisDataset> {
	const res = await fetchFn(DATA_URL);
	if (!res.ok) {
		throw new Error(
			`No s'ha pogut carregar ${DATA_URL} (HTTP ${res.status}). ` +
				`Executa el prebuild (npm run copy-data) per copiar data/web/municipis.bergueda.json a static/.`
		);
	}
	return (await res.json()) as MunicipisDataset;
}

/** Conveniència: una fila de municipi per INE5 (o undefined si no hi és). */
export function getMunicipi(dataset: MunicipisDataset, ine5: string): MunicipiRow | undefined {
	return dataset.municipis[ine5];
}

/**
 * Codis INE5 dels dos municipis destacats a la comparativa del "resum":
 * els dos extrems de la pressió turística-residencial del Berguedà.
 * Castellar de n'Hug (màxim) ↔ Berga (capital comarcal).
 */
export const FEATURED_INE5 = {
	castellar: '08052',
	berga: '08022'
} as const;
