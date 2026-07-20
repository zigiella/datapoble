/**
 * Slug de municipi a partir del nom oficial (spec consultora 2 §8.1).
 *
 * Regla: minúscules, sense accents ni apòstrofs, espais→guions, i l'article final
 * reordenat al davant:
 *   "Quar, la"            → "la-quar"
 *   "Pobla de Lillet, la" → "la-pobla-de-lillet"
 *   "Castellar de n'Hug"  → "castellar-de-nhug"
 *
 * L'`ine5` segueix sent la CLAU INTERNA (dades, contracte, API); el slug és només la
 * cara pública de la URL. La conversió és determinista (funció pura del nom oficial),
 * així que no cal cap fitxer a mantenir a mà: la font és el mateix dataset.
 */
import type { MunicipisDataset } from './types';

// "Nom, la|el|els|les|l'" al final → article al davant. Apòstrof recte o tipogràfic.
const ARTICLE = /^(.*),\s*(l['’]|la|el|els|les)$/i;

export function toSlug(nom: string): string {
	let s = nom.trim();
	const m = s.match(ARTICLE);
	if (m) s = `${m[2]} ${m[1]}`; // "Nom, la" → "la Nom"
	// Article INICIAL amb apòstrof sense espai ("l'Hospitalet", forma inline del geojson oficial):
	// hi inserim un separador perquè doni el MATEIX slug que la forma "Nom, l'" ("l-hospitalet",
	// no "lhospitalet"). Només l'article inicial; un apòstrof intern ("Castellar de n'Hug") es
	// manté i cau a "nhug" com fins ara. La forma "l' Nom" (ja amb espai) hi passa idempotent.
	s = s.replace(/^(l)['’]\s*/i, '$1 ');
	return s
		.replace(/l·l/gi, 'll') // ela geminada (l·l) → ll, no l-l
		.normalize('NFD')
		.replace(/\p{M}/gu, '') // treu marques combinades (accents)
		.replace(/['’·]/g, '') // apòstrofs i punt volat fora (n'Hug → nhug)
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-') // no-alfanumèric → guió
		.replace(/^-+|-+$/g, ''); // trim guions
}

/**
 * Nom del municipi en la seva forma CORRENT (article al davant), sigui quina sigui la forma
 * amb què arribi la fila.
 *
 * Per què cal: el mateix municipi ens arriba en DUES formes segons l'artefacte —
 * `municipis.*.json` (marts) el serveix en forma d'índex, «Pobla de Lillet, la», i la geometria
 * oficial (d'on surt el catàleg dels 947) i el tauler el serveixen com «la Pobla de Lillet».
 * La clau del join és sempre l'`ine5`, així que la divergència NO afecta cap xifra; però pintada
 * a un `<h1>` la forma d'índex es llegeix com un error. Aquí es normalitza NOMÉS per mostrar.
 *
 * Reutilitza la mateixa regla d'article que `toSlug` (una sola font de veritat), i per això els
 * dos noms ja donaven —i segueixen donant— el MATEIX slug: la URL no es toca.
 */
export function nomCanonic(nom: string): string {
	const s = nom.trim();
	const m = s.match(ARTICLE);
	if (!m) return s;
	// "Nom, l'" → "l'Nom" (sense espai); "Nom, la" → "la Nom".
	const art = m[2].toLowerCase();
	return /['’]$/.test(art) ? `${art}${m[1]}` : `${art} ${m[1]}`;
}

/** Slug d'un municipi pel seu `ine5` (via el nom oficial del dataset). */
export function slugForIne5(ine5: string, dataset: MunicipisDataset): string {
	return toSlug(dataset.municipis[ine5]?.nom ?? ine5);
}

/**
 * Índex bidireccional slug↔ine5 a partir dels municipis del dataset. Llança si dos
 * municipis cauen al mateix slug (guarda de COL·LISIÓ: corre a `entries()`, en build,
 * així que un xoc trenca el build = test de col·lisió a CI). A escala Catalunya, un
 * xoc real es resoldria amb sufix de comarca (spec §8.1); avui, al Berguedà, no n'hi ha.
 */
export function buildSlugIndex(municipis: Record<string, { ine5: string; nom: string }>): {
	slugToIne5: Record<string, string>;
	ine5ToSlug: Record<string, string>;
} {
	const slugToIne5: Record<string, string> = {};
	const ine5ToSlug: Record<string, string> = {};
	for (const { ine5, nom } of Object.values(municipis)) {
		const slug = toSlug(nom);
		if (slug in slugToIne5 && slugToIne5[slug] !== ine5) {
			throw new Error(`Col·lisió de slug "${slug}": ${slugToIne5[slug]} vs ${ine5} (${nom})`);
		}
		slugToIne5[slug] = ine5;
		ine5ToSlug[ine5] = slug;
	}
	return { slugToIne5, ine5ToSlug };
}
