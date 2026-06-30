/**
 * Arrel `/` — la HOME «La Llera» (cercador primer): buscador de municipis + mapa + troballes.
 * Abans redirigia a /resum; ara /resum és la subhome de comarca i l'arrel és la portada.
 *
 * Carrega el dataset (buscador + troballes), la geometria de Catalunya (mapa coroplètic) i
 * l'artefacte de licitacions (per a la troballa de contractació pròpia). Tot són actius
 * estàtics → `fetch` prerender-safe.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { PernoctaData } from '$lib/contract/pernocta';
import type { CatalegData } from '$lib/contract/cataleg';
import type { IndicadorsCatData } from '$lib/contract/indicadors';
import type { FeatureCollection } from 'geojson';
import type { PageLoad } from './$types';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const [dataset, munRes, comRes, vegRes, catRes] = await Promise.all([
		loadMunicipisDataset(fetch),
		fetch('/geo/catalunya-municipis.geojson'),
		fetch('/geo/catalunya-comarques.geojson'),
		fetch('/geo/catalunya-vegueries.geojson'),
		fetch('/data/municipis-cataleg.json')
	]);
	const geojson = (await munRes.json()) as FeatureCollection;
	const comarques = (await comRes.json()) as FeatureCollection;
	const vegueries = (await vegRes.json()) as FeatureCollection;
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

	// Indicadors a escala Catalunya (pinten TOTS els municipis del mapa de la home, no només el
	// Berguedà) + estatut de validació (capa la confiança del tooltip). No-fatals.
	let catValues: IndicadorsCatData = {};
	try {
		const res = await fetch('/data/indicadors-catalunya.json');
		if (res.ok) catValues = (await res.json()) as IndicadorsCatData;
	} catch {
		catValues = {};
	}
	let validats: string[] = [];
	try {
		const res = await fetch('/data/validats.json');
		if (res.ok) validats = (await res.json()) as string[];
	} catch {
		validats = [];
	}

	return { dataset, geojson, comarques, vegueries, pernocta, cataleg, catValues, validats };
};
