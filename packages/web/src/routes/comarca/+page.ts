/**
 * ÍNDEX DE COMARQUES (`/comarca` · `/es/comarca`) — el nivell «tota Catalunya» de l'espina.
 *
 * Neix amb W5 (esmena de Bea, 2026-07-31): la secció «Llegeix la comarca» de la home tenia una
 * sola porta oberta (el Berguedà) i una segona porta MORTA («Resta de Catalunya», `aria-disabled`)
 * que ja no deia la veritat — des de P-947 les 43 comarques tenen pàgina i els 947 municipis tenen
 * fitxa. Aquesta pàgina és el destí que li faltava: si la secció convida a llegir UNA comarca, la
 * porta ha de portar a TOTES, no a un mapa.
 *
 * Tot surt de `comarques.json` (l'agrupació que el prebuild deriva de `municipis-territori.json`);
 * cap xifra escrita a mà: el nombre de comarques, de vegueries i de municipis es COMPTA de
 * l'artefacte. L'agrupació es fa per la `vegueria` de CADA comarca (no per la llista `vegueries`)
 * perquè cap comarca es pugui perdre en silenci si un dia l'artefacte no les cobreix totes: el que
 * no tingui vegueria surt igualment, en un grup declarat.
 */
import { toSlug } from '$lib/contract/slug';
import type { ComarquesData } from '$lib/contract/comarques';
import type { PageLoad } from './$types';

export const prerender = true;
export const trailingSlash = 'always';

export const load: PageLoad = async ({ fetch }) => {
	const res = await fetch('/data/comarques.json');
	const data = (await res.json()) as ComarquesData;

	// Agrupació per vegueria a partir de la comarca (mai d'una llista paral·lela: una llista fixa
	// que descarta en silenci és el bug que ja ens ha mossegat al glossari i al mart).
	const byVeg = new Map<string, { nom: string; slug: string; nMunis: number }[]>();
	for (const c of data.comarques) {
		const veg = c.vegueria || '';
		if (!byVeg.has(veg)) byVeg.set(veg, []);
		byVeg.get(veg)?.push({ nom: c.nom, slug: toSlug(c.nom), nMunis: c.ine5s.length });
	}
	const coll = new Intl.Collator('ca');
	const vegueries = [...byVeg.entries()]
		.map(([nom, comarques]) => ({
			nom,
			slug: nom ? toSlug(nom) : '',
			comarques: comarques.sort((a, b) => coll.compare(a.nom, b.nom))
		}))
		.sort((a, b) => coll.compare(a.nom, b.nom));

	const totalComarques = data.comarques.length;
	const totalMunis = data.comarques.reduce((s, c) => s + c.ine5s.length, 0);
	const totalVegueries = vegueries.filter((v) => v.nom).length;

	return { vegueries, totalComarques, totalMunis, totalVegueries };
};
