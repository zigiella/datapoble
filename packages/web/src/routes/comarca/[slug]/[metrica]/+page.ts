/**
 * W2 · LLISTAT D'UNA MÈTRICA A UNA COMARCA (`/comarca/[slug]/[metrica]/`).
 *
 * Petició de Bea (2026-07-31): «hem de poder clicar cada vegada que posi rang i accedir a cada
 * llistat» — «poder clicar un rang i anar a una pàgina d'aquella mètrica amb el rang comarcal i
 * navegar entre municipis». Aquesta és aquella pàgina.
 *
 * PER QUÈ AQUESTA RUTA (decisió de Mirador, justificada a la bitàcola):
 *  · Penja de `/comarca/[slug]/`, que ja existeix i ja té el seu índex (`/comarca/`, #295): el
 *    llistat és una VISTA d'una comarca, no un nivell nou de l'espina. Així el breadcrumb surt
 *    sol (Catalunya › vegueria › comarca › mètrica) i la pàgina de comarca en pot ser la porta.
 *  · L'alternativa —`/metrica/[metrica]/[comarca]/`— hauria fet de la mètrica el nivell superior
 *    i hauria obligat a inventar un índex de mètriques que ningú ha demanat.
 *  · El slug de la mètrica es DERIVA de la clau del contracte (`metricaSlug`), no d'una segona
 *    taula de noms que caldria mantenir sincronitzada: una URL i la xifra que pinta no poden
 *    divergir sense que el CI ho vegi.
 *
 * COST DE BUILD (mesurat abans de decidir, com demanava el brief): 43 comarques × 9 mètriques
 * = 387 pàgines × 3 còpies prerenderitzades (canònica + /ca + /es) = **1.161 `index.html`**, més
 * els **387** JSON del prebuild. Mesurat: el build passa de **5.933 a 7.481 fitxers** (+1.548),
 * un **37 %** del límite de 20.000 de Cloudflare Pages. Es prerenderitza tot: hi ha marge de
 * sobres i el site no té servidor en runtime (adapter-static) on generar-ho sota demanda.
 *
 * La dada NO es calcula aquí (C6 §4): el prebuild (`copy-data.mjs` → `buildGovernLlistes`)
 * reagrupa les cel·les del mart per comarca × mètrica i la pàgina en llegeix el seu fitxer i
 * prou. Un sol `fetch`: el fitxer ja porta la vegueria i la definició de la mètrica, perquè
 * SvelteKit incrusta la resposta de cada `fetch` del loader a CADA pàgina prerenderitzada.
 */
import { error } from '@sveltejs/kit';
import { toSlug } from '$lib/contract/slug';
import { GOVERN_RANK_KEYS, metricaSlug, metricaFromSlug } from '$lib/govern/kpis';
import type { ComarquesData } from '$lib/contract/comarques';
import type { GovernLlista } from '$lib/contract/govern-llista';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;
export const trailingSlash = 'always';

/**
 * Prerender de les 43 comarques × les 9 mètriques amb rang. Les dues llistes surten de la FONT
 * (l'agrupació territorial i el descriptor del tauler), mai escrites a mà. Guarda de col·lisió
 * de slug de mètrica: dues mètriques al mateix slug compartirien pàgina —una xifra sota el
 * rètol d'una altra—, així que trenca el build.
 */
export const entries: EntryGenerator = async () => {
	const { readFileSync } = await import('node:fs');
	const { join } = await import('node:path');
	const seenMetrica = new Map<string, string>();
	for (const key of GOVERN_RANK_KEYS) {
		const ms = metricaSlug(key);
		if (seenMetrica.has(ms) && seenMetrica.get(ms) !== key) {
			throw new Error(`Col·lisió de slug de mètrica "${ms}": ${seenMetrica.get(ms)} vs ${key}`);
		}
		seenMetrica.set(ms, key);
	}
	const path = join(process.cwd(), 'static', 'data', 'comarques.json');
	try {
		const data = JSON.parse(readFileSync(path, 'utf8')) as ComarquesData;
		const slugs = [...new Set(data.comarques.map((c) => toSlug(c.nom)))];
		return slugs.flatMap((slug) => [...seenMetrica.keys()].map((metrica) => ({ slug, metrica })));
	} catch (err) {
		if ((err as Error).message?.startsWith('Col·lisió')) throw err;
		// Sense l'agrupació (entorn sense prebuild) no es prerenderitza cap llistat: el fallback
		// SPA els serveix. No-fatal, com la resta de rutes territorials.
		console.warn(`[comarca/metrica/entries] no s'ha pogut llegir ${path}: ${(err as Error).message}`);
		return [];
	}
};

export const load: PageLoad = async ({ fetch, params }) => {
	// Una mètrica que el mart no rankeja no té llistat: no hi hauria ORDRE a publicar, i
	// fabricar-lo aquí seria exactament el que C6 §4 prohibeix. 404 honest.
	const metrica = metricaFromSlug(params.metrica);
	if (!metrica) throw error(404, 'Mètrica sense rang comarcal');

	const res = await fetch(`/data/govern-llista/${params.slug}/${params.metrica}.json`);
	if (!res.ok) throw error(404, 'Comarca desconeguda');
	const llista = (await res.json()) as GovernLlista;

	// L'artefacte i la URL han de parlar de la MATEIXA mètrica i la MATEIXA comarca: si no,
	// la pàgina pintaria una llista sota un títol que no li correspon.
	if (llista.metrica !== metrica || toSlug(llista.comarca) !== params.slug) {
		throw error(404, 'Llistat incoherent amb la ruta');
	}

	return { llista };
};
