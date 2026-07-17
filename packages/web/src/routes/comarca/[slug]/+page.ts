/**
 * Pàgina de COMARCA (`/comarca/[slug]` · `/es/comarca/[slug]`) — nivell intermedi de l'espina
 * territorial (§5). Dona destí navegable al breadcrumb (Catalunya › vegueria › COMARCA › municipi)
 * i una vista de la comarca: mapa + els seus municipis (enllaç a fitxa).
 *
 * Tot des d'artefactes estàtics (prerender-safe): `comarques.json` (agrupació) i
 * `municipis-cataleg` (noms). Slug = `toSlug(nom de la comarca)`.
 * (El gap padró↔presència del model està APARCAT: la pàgina no carrega pernocta.)
 */
import { toSlug } from '$lib/contract/slug';
import { error } from '@sveltejs/kit';
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { ComarquesData } from '$lib/contract/comarques';
import type { CatalegData } from '$lib/contract/cataleg';
import type { IndicadorsCatData } from '$lib/contract/indicadors';
import type { FeatureCollection } from 'geojson';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;
export const trailingSlash = 'always';

/** Prerender de les 43 comarques (slugs del nom oficial). Guarda de col·lisió → trenca el build. */
export const entries: EntryGenerator = async () => {
	const { readFileSync } = await import('node:fs');
	const { join } = await import('node:path');
	const path = join(process.cwd(), 'static', 'data', 'comarques.json');
	try {
		const data = JSON.parse(readFileSync(path, 'utf8')) as ComarquesData;
		const seen = new Map<string, string>();
		for (const c of data.comarques) {
			const slug = toSlug(c.nom);
			if (seen.has(slug) && seen.get(slug) !== c.nom) {
				throw new Error(`Col·lisió de slug de comarca "${slug}": ${seen.get(slug)} vs ${c.nom}`);
			}
			seen.set(slug, c.nom);
		}
		return [...seen.keys()].map((slug) => ({ slug }));
	} catch (err) {
		if ((err as Error).message?.startsWith('Col·lisió')) throw err;
		return [];
	}
};

export const load: PageLoad = async ({ fetch, params }) => {
	const [comRes, catRes, munGeoRes, comGeoRes, dataset] = await Promise.all([
		fetch('/data/comarques.json'),
		fetch('/data/municipis-cataleg.json'),
		fetch('/geo/catalunya-municipis.geojson'),
		fetch('/geo/catalunya-comarques.geojson'),
		loadMunicipisDataset(fetch)
	]);
	const data = (await comRes.json()) as ComarquesData;
	const comarca = data.comarques.find((c) => toSlug(c.nom) === params.slug);
	if (!comarca) throw error(404, 'Comarca desconeguda');

	const cataleg = catRes.ok ? ((await catRes.json()) as CatalegData) : [];
	const nomByIne5 = new Map(cataleg.map((mn) => [mn.ine5, mn.nom]));

	// Municipis de la comarca: nom + slug (enllaç a la fitxa; tota la resta viu allà).
	const munis = comarca.ine5s
		.map((ine5) => {
			const nom = nomByIne5.get(ine5) ?? ine5;
			return { ine5, nom, slug: toSlug(nom) };
		})
		.sort((a, b) => a.nom.localeCompare(b.nom, 'ca'));

	// Geometria + indicadors per al MAPA de la comarca (mateixos artefactes que /mapa). El mapa
	// enquadra als municipis de la comarca (comarca.ine5s) i pinta el Berguedà (dataset) o la resta
	// (catValues) pel mateix indicador. No-fatals.
	const geojson = (await munGeoRes.json()) as FeatureCollection;
	const comarquesGeo = (await comGeoRes.json()) as FeatureCollection;
	let catValues: IndicadorsCatData = {};
	try {
		const r = await fetch('/data/indicadors-catalunya.json');
		if (r.ok) catValues = (await r.json()) as IndicadorsCatData;
	} catch {
		catValues = {};
	}

	return {
		comarca: { nom: comarca.nom, vegueria: comarca.vegueria, ine5s: comarca.ine5s },
		munis,
		dataset,
		geojson,
		comarques: comarquesGeo,
		catValues
	};
};
