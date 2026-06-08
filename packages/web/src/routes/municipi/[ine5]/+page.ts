/**
 * Càrrega de la FITXA DE MUNICIPI (`/municipi/[ine5]` · `/es/municipi/[ine5]`).
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
		return Object.keys(dataset.municipis).map((ine5) => ({ ine5 }));
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
	const ine5 = params.ine5;
	// `row` null = el codi no és al dataset (fora del Berguedà) → estat «sense dades encara».
	const row = dataset.municipis[ine5] ?? null;
	return { dataset, ine5, row };
};
