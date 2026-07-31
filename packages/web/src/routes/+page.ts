/**
 * Arrel `/` — la HOME «La Llera» (cercador primer): buscador de municipis + mapa + portes.
 *
 * Carrega el dataset (buscador), la geometria de Catalunya (mapa coroplètic), el catàleg de
 * municipis, els indicadors oficials a escala Catalunya i l'agrupació territorial (les xifres
 * de les portes, W5). Tot són actius estàtics → `fetch` prerender-safe.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import { toSlug } from '$lib/contract/slug';
import type { CatalegData } from '$lib/contract/cataleg';
import type { ComarquesData } from '$lib/contract/comarques';
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

	// W5 · les xifres de les PORTES es COMPTEN de l'agrupació territorial (`comarques.json`, la
	// mateixa font de /comarca i /vegueria), mai s'escriuen al copy: un número escrit al text es
	// queda estale en silenci —és el que li va passar al «947 municipis» de la porta morta— i a
	// més el 947 hi estava etiquetat com a «resta de Catalunya» quan és el TOTAL. No-fatal: sense
	// l'artefacte els comptadors queden a 0 i les portes s'ensenyen sense subtítol.
	let totalComarques = 0;
	let totalMunis = 0;
	let berguedaMunis = 0;
	try {
		const res = await fetch('/data/comarques.json');
		if (res.ok) {
			const agrup = (await res.json()) as ComarquesData;
			totalComarques = agrup.comarques.length;
			totalMunis = agrup.comarques.reduce((s, c) => s + c.ine5s.length, 0);
			berguedaMunis = agrup.comarques.find((c) => toSlug(c.nom) === 'bergueda')?.ine5s.length ?? 0;
		}
	} catch {
		totalComarques = 0;
	}

	return {
		dataset,
		geojson,
		comarques,
		cataleg,
		catValues,
		totalComarques,
		totalMunis,
		berguedaMunis
	};
};
