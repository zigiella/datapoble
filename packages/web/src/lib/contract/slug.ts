/**
 * Slug de municipi i formes del nom — façana TIPADA.
 *
 * La REGLA (article, accents, apòstrofs, ela geminada) viu a `./slug-core.js`, en JS pur, perquè
 * el verificador offline (`scripts/verify-govern.mjs`) la pugui importar i EXERCIR sobre els 947
 * noms reals sense duplicar-la — mateix patró que `$lib/govern/kpis.js`. Aquí només s'hi posen
 * els tipus i els dos ajudants que necessiten el `MunicipisDataset`.
 *
 *   "Quar, la"            → "la-quar"
 *   "Pobla de Lillet, la" → "la-pobla-de-lillet"
 *   "Castellar de n'Hug"  → "castellar-de-nhug"
 *
 * L'`ine5` segueix sent la CLAU INTERNA (dades, contracte, API); el slug és només la
 * cara pública de la URL. La conversió és determinista (funció pura del nom oficial),
 * així que no cal cap fitxer a mantenir a mà: la font és el mateix nom oficial.
 */
import type { MunicipisDataset } from './types';

export { toSlug, nomCanonic, nomIndex } from './slug-core.js';
import { toSlug } from './slug-core.js';

/** Slug d'un municipi pel seu `ine5` (via el nom oficial del dataset). */
export function slugForIne5(ine5: string, dataset: MunicipisDataset): string {
	return toSlug(dataset.municipis[ine5]?.nom ?? ine5);
}

/**
 * Índex bidireccional slug↔ine5 a partir d'una col·lecció de municipis. Llança si dos
 * municipis cauen al mateix slug (guarda de COL·LISIÓ).
 *
 * On corre, avui: (a) al `load` de la fitxa sobre el dataset del pilot (31) — camí ràpid de
 * resolució; (b) la MATEIXA guarda, a escala Catalunya, viu a `entries()` de
 * `municipi/[slug]/+page.ts`, que la passa sobre els **947** del catàleg en BUILD, així que un
 * xoc real trenca el build (= test de col·lisió a CI). Comprovat el 2026-07-31 sobre la
 * geometria oficial: 947 noms → 947 slugs, cap col·lisió; `verify-govern.mjs` ho torna a
 * comprovar offline a cada CI. Si algun dia n'apareix una, es resol amb sufix de comarca
 * (spec §8.1) — mai desactivant la guarda.
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
