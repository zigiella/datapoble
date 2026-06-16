/**
 * Càrrega de dades del mapa (escala Catalunya · Fase 0).
 *
 * - dataset: dades REALS dels 31 municipis del Berguedà, forma `MunicipisDataset`
 *   (font: Sondeig, `data/web/municipis.bergueda.json`, copiat a static/ pel prebuild).
 *   Es carrega via `$lib/data/dataset` amb el `fetch` de SvelteKit (prerender-safe).
 * - geojson: geometria OFICIAL de TOTS els municipis de Catalunya (947, static/geo/…,
 *   INE/IGN), props `{ine5, nom}`. Capa base atenuada; a sobre, el coroplètic del Berguedà.
 *   El Berguedà ja és DINS d'aquest fitxer (no es barreja amb bergueda-municipis.geojson,
 *   que té una simplificació diferent): el join és per `ine5`.
 * - comarques: geometria de les 43 comarques (static/geo/…), props `{id, nom, cap}`,
 *   per dibuixar els límits comarcals suaus que orienten dins de Catalunya.
 *
 * El join dataset↔geometria és per `ine5`. Els 31 codis del Berguedà del dataset quadren
 * 1:1 amb els seus municipis dins del fitxer de Catalunya; la resta queden ATENUATS
 * («sense dades encara»), no acolorits per l'indicador (honestedat: no fingim dada).
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { FeatureCollection } from 'geojson';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const [dataset, munRes, comRes, vegRes] = await Promise.all([
		loadMunicipisDataset(fetch),
		fetch('/geo/catalunya-municipis.geojson'),
		fetch('/geo/catalunya-comarques.geojson'),
		fetch('/geo/catalunya-vegueries.geojson')
	]);
	const geojson = (await munRes.json()) as FeatureCollection;
	const comarques = (await comRes.json()) as FeatureCollection;
	const vegueries = (await vegRes.json()) as FeatureCollection;
	return { dataset, geojson, comarques, vegueries };
};
