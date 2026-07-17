/**
 * Arrel `/` — la HOME «La Llera» (cercador primer): buscador de municipis + mapa + portes.
 *
 * Carrega el dataset (buscador), la geometria de Catalunya (mapa coroplètic), el catàleg de
 * municipis i els indicadors oficials a escala Catalunya. Tot són actius estàtics → `fetch`
 * prerender-safe.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { CatalegData } from '$lib/contract/cataleg';
import type { IndicadorsCatData } from '$lib/contract/indicadors';
import type { FeatureCollection } from 'geojson';
import type { PageLoad } from './$types';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const [dataset, munRes, comRes, catRes] = await Promise.all([
		loadMunicipisDataset(fetch),
		fetch('/geo/catalunya-municipis.geojson'),
		fetch('/geo/catalunya-comarques.geojson'),
		fetch('/data/municipis-cataleg.json')
	]);
	const geojson = (await munRes.json()) as FeatureCollection;
	const comarques = (await comRes.json()) as FeatureCollection;
	// Catàleg de tots els munis (cerca a tota Catalunya). No-fatal: sense ell, el cercador cau als 31.
	const cataleg = catRes.ok ? ((await catRes.json()) as CatalegData) : [];

	// Indicadors OFICIALS a escala Catalunya (pinten TOTS els municipis del mapa de la home, no
	// només el Berguedà). No-fatal. (El model de pernocta està aparcat: la home no en carrega res.)
	let catValues: IndicadorsCatData = {};
	try {
		const res = await fetch('/data/indicadors-catalunya.json');
		if (res.ok) catValues = (await res.json()) as IndicadorsCatData;
	} catch {
		catValues = {};
	}

	return { dataset, geojson, comarques, cataleg, catValues };
};
