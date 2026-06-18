/**
 * Càrrega de la FITXA DE MUNICIPI (`/municipi/[slug]` · `/es/municipi/[slug]`).
 *
 * Cobreix TOTA CATALUNYA: cada municipi (~947) té la seva fitxa. El nivell de contingut depèn de
 * les dades disponibles, en aquest ordre:
 *  - **Berguedà (31)** → fitxa completa amb TOTES les mètriques i procedència (dataset real de
 *    Sondeig, `data/web/municipis.bergueda.json`).
 *  - **Coberts pel Nivell C (rang)** → targeta de presència EN RANG (`pernocta-catalunya.json`).
 *  - **Resta** → estat AMABLE «sense dades encara» amb el NOM real del municipi (mai una fitxa
 *    buida ni un error lleig; honestedat: no fingim dada on no n'hi ha).
 *
 * La join key és l'`ine5`; el slug públic es resol del nom oficial (`toSlug`). La columna vertebral
 * de «tota Catalunya» és el CATÀLEG (`data/municipis-cataleg.json`, cens de noms+codis dels 947,
 * generat pel prebuild des de la geometria oficial), que resol QUALSEVOL slug → ine5 + nom.
 *
 * PRERENDER (adapter-static · Cloudflare Pages): `entries()` declara TOTS els municipis de Catalunya
 * (slugs derivats del catàleg) perquè cadascun tingui el seu `index.html` estàtic — URL real per a
 * cada poble (SEO + enllaços directes), sense servidor en runtime.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import { buildSlugIndex, toSlug } from '$lib/contract/slug';
import type { LecturesData, LecturaEntry } from '$lib/contract/lectures';
import type { PernoctaData, PernoctaMuni } from '$lib/contract/pernocta';
import type { CatalegData } from '$lib/contract/cataleg';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;
export const trailingSlash = 'always';

/**
 * Entrades a prerenderitzar: TOTS els municipis de Catalunya, derivats del catàleg real (no una
 * llista a mà), perquè la llista segueixi la FONT (la geometria oficial). Guarda de COL·LISIÓ:
 * si dos municipis cauen al mateix slug, llança → el build falla = test de col·lisió a CI (spec
 * §8.1; a escala Catalunya un xoc real es resoldria amb sufix de comarca).
 *
 * `entries()` corre en build amb el `fetch` global de Node (no resol `/data/...`), per això llegim
 * el JSON del DISC (la còpia del prebuild a `static/data/`). L'import de `node:fs` és dinàmic
 * perquè aquest mòdul és universal: `node:fs` només s'avalua en build (servidor), mai al client.
 */
export const entries: EntryGenerator = async () => {
	const { readFileSync } = await import('node:fs');
	const { join } = await import('node:path');
	const path = join(process.cwd(), 'static', 'data', 'municipis-cataleg.json');
	try {
		const cataleg = JSON.parse(readFileSync(path, 'utf8')) as CatalegData;
		const seen = new Map<string, string>(); // slug → ine5 (guarda de col·lisió)
		for (const m of cataleg) {
			const slug = toSlug(m.nom);
			if (seen.has(slug) && seen.get(slug) !== m.ine5) {
				throw new Error(`Col·lisió de slug "${slug}": ${seen.get(slug)} vs ${m.ine5} (${m.nom})`);
			}
			seen.set(slug, m.ine5);
		}
		return [...seen.keys()].map((slug) => ({ slug }));
	} catch (err) {
		// Degradació NO-FATAL si el catàleg no hi és (entorn sense el prebuild): cap fitxa
		// prerenderitzada explícitament; el fallback SPA del 404 les serveix (hidraten al client).
		// PERÒ una col·lisió SÍ que ha de trencar el build (re-llancem aquest cas).
		if ((err as Error).message?.startsWith('Col·lisió')) throw err;
		console.warn(
			`[municipi/entries] no s'ha pogut llegir ${path}: ${(err as Error).message}. ` +
				`Cap fitxa prerenderitzada explícitament (fallback SPA).`
		);
		return [];
	}
};

export const load: PageLoad = async ({ fetch, params }) => {
	const dataset = await loadMunicipisDataset(fetch);
	// Slugs del Berguedà (clau interna ↔ slug públic) + guarda de col·lisió del pilot.
	const { slugToIne5 } = buildSlugIndex(dataset.municipis);

	// Resol l'ine5 i el NOM del municipi. Camí ràpid: el Berguedà (dataset). Si no, el catàleg de
	// tota Catalunya (qualsevol poble) — així fins i tot els munis sense dades tenen nom a la pàgina.
	let ine5 = slugToIne5[params.slug] ?? null;
	let nom = ine5 ? (dataset.municipis[ine5]?.nom ?? null) : null;
	if (!ine5) {
		try {
			const res = await fetch('/data/municipis-cataleg.json');
			if (res.ok) {
				const cataleg = (await res.json()) as CatalegData;
				const hit = cataleg.find((mn) => toSlug(mn.nom) === params.slug);
				if (hit) {
					ine5 = hit.ine5;
					nom = hit.nom;
				}
			}
		} catch {
			/* sense catàleg: només es resolen els slugs del Berguedà */
		}
	}

	// `row` (dades completes del Berguedà): null per a la resta de Catalunya.
	const row = ine5 ? (dataset.municipis[ine5] ?? null) : null;

	// Presència estimada EN RANG (Nivell C) per als munis coberts FORA del Berguedà. Prerender-safe.
	let pernocta: PernoctaMuni | null = null;
	if (ine5 && !row) {
		try {
			const res = await fetch('/data/pernocta-catalunya.json');
			if (res.ok) {
				const all = (await res.json()) as PernoctaData;
				pernocta = all.munis[ine5] ?? null;
				if (pernocta && !nom) nom = pernocta.nom;
			}
		} catch {
			pernocta = null;
		}
	}

	// Lectura-IA és un artefacte del BERGUEDÀ: només es carrega si el muni hi és (`row`). Així la
	// resta de Catalunya no fa fetches inútils en prerender. Prerender-safe.
	// (Licitacions aparcades per al llançament —decisió Bea—: la fitxa no en mostra secció.)
	let lectura: LecturaEntry | null = null;
	if (row) {
		try {
			const res = await fetch('/data/lectures.bergueda.json');
			if (res.ok) {
				const data = (await res.json()) as LecturesData;
				lectura = data[ine5 as string] ?? null;
			}
		} catch {
			lectura = null;
		}
	}

	return { dataset, ine5, nom, row, lectura, pernocta };
};
