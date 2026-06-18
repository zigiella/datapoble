/**
 * Arrel `/` — la HOME «La Llera» (cercador primer): buscador de municipis + mapa + troballes.
 * Abans redirigia a /resum; ara /resum és la subhome de comarca i l'arrel és la portada.
 *
 * Carrega el dataset (buscador + troballes), la geometria de Catalunya (mapa coroplètic) i
 * l'artefacte de licitacions (per a la troballa de contractació pròpia). Tot són actius
 * estàtics → `fetch` prerender-safe.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { LicitacionsPayload } from '$lib/analysis/troballes';
import type { PernoctaData } from '$lib/contract/pernocta';
import type { CatalegData } from '$lib/contract/cataleg';
import type { FeatureCollection } from 'geojson';
import type { PageLoad } from './$types';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const [dataset, munRes, comRes, vegRes, licRes, catRes] = await Promise.all([
		loadMunicipisDataset(fetch),
		fetch('/geo/catalunya-municipis.geojson'),
		fetch('/geo/catalunya-comarques.geojson'),
		fetch('/geo/catalunya-vegueries.geojson'),
		fetch('/data/licitacions-bergueda.json'),
		fetch('/data/municipis-cataleg.json')
	]);
	const geojson = (await munRes.json()) as FeatureCollection;
	const comarques = (await comRes.json()) as FeatureCollection;
	const vegueries = (await vegRes.json()) as FeatureCollection;
	const licitacions = licRes.ok ? ((await licRes.json()) as LicitacionsPayload) : null;
	// Catàleg de tots els munis (cerca a tota Catalunya). No-fatal: sense ell, el cercador cau als 31.
	const cataleg = catRes.ok ? ((await catRes.json()) as CatalegData) : [];

	// Presència estimada EN RANG (Nivell C): munis coberts fora del Berguedà. Opcional i no-fatal
	// (el mapa de la home funciona igual sense l'artefacte). Es mostren només a granularitat municipi.
	let pernocta: PernoctaData | null = null;
	try {
		const res = await fetch('/data/pernocta-catalunya.json');
		if (res.ok) pernocta = (await res.json()) as PernoctaData;
	} catch {
		pernocta = null;
	}

	return { dataset, geojson, comarques, vegueries, licitacions, pernocta, cataleg };
};
