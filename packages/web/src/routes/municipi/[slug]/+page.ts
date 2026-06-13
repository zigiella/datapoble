/**
 * Càrrega de la FITXA DE MUNICIPI (`/municipi/[slug]` · `/es/municipi/[slug]`).
 *
 * Generalitza la riquesa que el Resum només donava als dos extrems (Berga i Castellar) a
 * QUALSEVOL dels 31 municipis del Berguedà. Tira del MATEIX dataset real (`MunicipisDataset`,
 * font: Sondeig via `data/web/municipis.bergueda.json`) que la resta del web, i resol el
 * municipi pel paràmetre de ruta `ine5` (codi INE de 5 dígits, la join key del contracte).
 *
 * - Si l'`ine5` és al dataset (un dels 31 del Berguedà) → es passa la seva fila i la pàgina
 *   pinta la fitxa completa amb TOTES les mètriques i la procedència, com el Resum.
 * - Si NO hi és (resta de Catalunya, ~916 munis sense dades encara) → `row` és null i la
 *   pàgina mostra un estat AMABLE «sense dades encara» (no una fitxa buida ni un error lleig).
 *   Mateixa honestedat que el tooltip «fora del Berguedà» del mapa: no fingim dada on no n'hi ha.
 *
 * PRERENDER (adapter-static · Cloudflare Pages): `entries()` declara els 31 codis del Berguedà
 * (les claus REALS del dataset, no una llista codificada a mà) perquè cadascun tingui el seu
 * `index.html` estàtic en build. Així `/municipi/08022/` i la variant `/es/municipi/08022/`
 * existeixen com a actiu, sense servidor en runtime. La resta de codis no es prerenderitzen
 * (el `fallback` SPA del 404 els serveix amb l'estat «sense dades»).
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import { buildSlugIndex } from '$lib/contract/slug';
import type { LicitacionsData, LicitacionsMuni } from '$lib/contract/licitacions';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;
export const trailingSlash = 'always';

/**
 * Entrades a prerenderitzar: els 31 municipis del Berguedà (els que tenen dades).
 * Es deriven de l'artefacte real del dataset perquè la llista segueixi la FONT de dades
 * (el dia que entrin més comarques, s'amplia sola), no una constant codificada a la UI.
 *
 * A diferència dels `load`, `entries()` NO rep el `fetch` de SvelteKit (que resol URLs
 * relatives): corre en build amb el `fetch` global de Node, que no sap resoldre `/data/...`.
 * Per això aquí llegim el JSON del DISC (la còpia que el prebuild deixa a `static/data/`,
 * mateix actiu que serveix el loader en runtime). L'import de `node:fs` és dinàmic perquè
 * aquest mòdul és universal: `node:fs` només s'avalua en build (servidor), mai al client.
 */
export const entries: EntryGenerator = async () => {
	const { readFileSync } = await import('node:fs');
	const { join } = await import('node:path');
	// El build corre amb cwd = `packages/web`; el prebuild (copy-data) ha deixat la còpia a
	// `static/data/`. Llegim d'allà (mateix actiu que serveix el loader en runtime).
	const path = join(process.cwd(), 'static', 'data', 'municipis.bergueda.json');
	try {
		const dataset = JSON.parse(readFileSync(path, 'utf8')) as Awaited<
			ReturnType<typeof loadMunicipisDataset>
		>;
		// Slug públic per municipi (derivat del nom oficial); buildSlugIndex llança si dos
		// municipis xoquen → el build falla = test de col·lisió a CI (spec §8.1).
		const { ine5ToSlug } = buildSlugIndex(dataset.municipis);
		return Object.values(ine5ToSlug).map((slug) => ({ slug }));
	} catch (err) {
		// Degradació NO-FATAL (mateix esperit que copy-data): si l'actiu no hi és en un entorn
		// sense els marts, no prerenderitzem cap fitxa explícita — el fallback SPA del 404 les
		// serveix igualment (hidraten al client). Mai trenquem el build per això.
		console.warn(
			`[municipi/entries] no s'ha pogut llegir ${path}: ${(err as Error).message}. ` +
				`Cap fitxa prerenderitzada explícitament (fallback SPA).`
		);
		return [];
	}
};

export const load: PageLoad = async ({ fetch, params }) => {
	const dataset = await loadMunicipisDataset(fetch);
	// El slug és la cara pública de la URL; l'ine5 (clau interna) es resol del nom oficial.
	const { slugToIne5 } = buildSlugIndex(dataset.municipis);
	const ine5 = slugToIne5[params.slug] ?? null;
	// `row` null = slug desconegut → estat «sense dades encara» (degradació amable, no 404 lleig).
	const row = ine5 ? (dataset.municipis[ine5] ?? null) : null;

	// Licitacions del municipi (el cabal): opcional, de l'artefacte standalone. Prerender-safe.
	let lic: LicitacionsMuni | null = null;
	if (ine5) {
		try {
			const res = await fetch('/data/licitacions-bergueda.json');
			if (res.ok) {
				const data = (await res.json()) as LicitacionsData;
				lic = data.municipis.find((mu) => mu.ine5 === ine5) ?? null;
			}
		} catch {
			lic = null;
		}
	}
	return { dataset, ine5, row, lic };
};
