/**
 * Pàgina de VEGUERIA (`/vegueria/[slug]`) — nivell més alt de l'espina (Catalunya › VEGUERIA ›
 * comarca › municipi). Vista de la vegueria: les seves comarques (enllaç a cada pàgina de comarca).
 * Tot des de `comarques.json` (prerender-safe). Slug = `toSlug(nom de la vegueria)`.
 */
import { toSlug } from '$lib/contract/slug';
import { error } from '@sveltejs/kit';
import type { ComarquesData } from '$lib/contract/comarques';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;
export const trailingSlash = 'always';

export const entries: EntryGenerator = async () => {
	const { readFileSync } = await import('node:fs');
	const { join } = await import('node:path');
	const path = join(process.cwd(), 'static', 'data', 'comarques.json');
	try {
		const data = JSON.parse(readFileSync(path, 'utf8')) as ComarquesData;
		const seen = new Map<string, string>();
		for (const v of data.vegueries) {
			const slug = toSlug(v.nom);
			if (seen.has(slug) && seen.get(slug) !== v.nom) {
				throw new Error(`Col·lisió de slug de vegueria "${slug}": ${seen.get(slug)} vs ${v.nom}`);
			}
			seen.set(slug, v.nom);
		}
		return [...seen.keys()].map((slug) => ({ slug }));
	} catch (err) {
		if ((err as Error).message?.startsWith('Col·lisió')) throw err;
		return [];
	}
};

export const load: PageLoad = async ({ fetch, params }) => {
	const res = await fetch('/data/comarques.json');
	const data = (await res.json()) as ComarquesData;
	const vegueria = data.vegueries.find((v) => toSlug(v.nom) === params.slug);
	if (!vegueria) throw error(404, 'Vegueria desconeguda');

	// Nombre de munis per comarca (de l'agrupació).
	const nMunis = new Map(data.comarques.map((c) => [c.nom, c.ine5s.length]));
	const comarques = vegueria.comarques
		.map((nom) => ({ nom, slug: toSlug(nom), nMunis: nMunis.get(nom) ?? 0 }))
		.sort((a, b) => a.nom.localeCompare(b.nom, 'ca'));

	const totalMunis = comarques.reduce((s, c) => s + c.nMunis, 0);
	return { vegueria: { nom: vegueria.nom }, comarques, totalMunis };
};
