/**
 * Pàgina de COMARCA (`/comarca/[slug]` · `/es/comarca/[slug]`) — nivell intermedi de l'espina
 * territorial (§5). Dona destí navegable al breadcrumb (Catalunya › vegueria › COMARCA › municipi)
 * i una vista de la comarca: els seus municipis (enllaç a fitxa) + el seu gap padró↔presència.
 *
 * Tot des d'artefactes estàtics (prerender-safe): `comarques.json` (agrupació), `municipis-cataleg`
 * (noms) i `pernocta-catalunya` (gap). Slug = `toSlug(nom de la comarca)`.
 */
import { toSlug } from '$lib/contract/slug';
import { error } from '@sveltejs/kit';
import type { ComarquesData } from '$lib/contract/comarques';
import type { CatalegData } from '$lib/contract/cataleg';
import type { PernoctaData, PernoctaMuni } from '$lib/contract/pernocta';
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
	const [comRes, catRes, pernRes] = await Promise.all([
		fetch('/data/comarques.json'),
		fetch('/data/municipis-cataleg.json'),
		fetch('/data/pernocta-catalunya.json')
	]);
	const data = (await comRes.json()) as ComarquesData;
	const comarca = data.comarques.find((c) => toSlug(c.nom) === params.slug);
	if (!comarca) throw error(404, 'Comarca desconeguda');

	const cataleg = catRes.ok ? ((await catRes.json()) as CatalegData) : [];
	const nomByIne5 = new Map(cataleg.map((mn) => [mn.ine5, mn.nom]));
	const pern: Record<string, PernoctaMuni> = pernRes.ok
		? ((await pernRes.json()) as PernoctaData).munis
		: {};

	// Municipis de la comarca: nom + slug + gap (si cobert pel Nivell C).
	const munis = comarca.ine5s
		.map((ine5) => {
			const nom = nomByIne5.get(ine5) ?? ine5;
			const p = pern[ine5];
			const gap = p && p.padro ? ((p.estimacio - p.padro) / p.padro) * 100 : null;
			return { ine5, nom, slug: toSlug(nom), gap, cobert: !!p };
		})
		.sort((a, b) => a.nom.localeCompare(b.nom, 'ca'));

	// Subconjunt de pernocta de la comarca (per al beeswarm del gap).
	const pernSub: Record<string, PernoctaMuni> = {};
	for (const ine5 of comarca.ine5s) if (pern[ine5]) pernSub[ine5] = pern[ine5];

	return {
		comarca: { nom: comarca.nom, vegueria: comarca.vegueria },
		munis,
		pernSub,
		coberts: Object.keys(pernSub).length
	};
};
