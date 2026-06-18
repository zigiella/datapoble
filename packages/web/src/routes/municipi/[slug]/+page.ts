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
import { buildSlugIndex, toSlug } from '$lib/contract/slug';
import type { LicitacionsData, LicitacionsMuni } from '$lib/contract/licitacions';
import type { LecturesData, LecturaEntry } from '$lib/contract/lectures';
import type { PernoctaData, PernoctaMuni } from '$lib/contract/pernocta';
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
		const slugs = new Set(Object.values(ine5ToSlug));
		// + munis coberts pel rang (Nivell C, fora del Berguedà) perquè la seva fitxa també es
		// prerenderitzi. Degradació no-fatal si l'artefacte encara no hi és.
		try {
			const pPath = join(process.cwd(), 'static', 'data', 'pernocta-catalunya.json');
			const pernocta = JSON.parse(readFileSync(pPath, 'utf8')) as { munis: Record<string, { nom: string }> };
			for (const m of Object.values(pernocta.munis)) slugs.add(toSlug(m.nom));
		} catch {
			/* sense artefacte de rang: només es prerenderitzen els del Berguedà */
		}
		return [...slugs].map((slug) => ({ slug }));
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

	// Presència estimada EN RANG (Nivell C) — munis coberts MÉS ENLLÀ del Berguedà (artefacte
	// `pernocta-catalunya.json`). Es carrega aviat perquè també resol el slug d'aquests munis (el
	// `slugToIne5` només coneix els 31 del Berguedà). Prerender-safe.
	// El Berguedà ja té dades completes; només cal l'artefacte de rang si el slug NO hi és.
	let pernoctaAll: PernoctaData | null = null;
	if (!slugToIne5[params.slug]) {
		try {
			const res = await fetch('/data/pernocta-catalunya.json');
			if (res.ok) pernoctaAll = (await res.json()) as PernoctaData;
		} catch {
			pernoctaAll = null;
		}
	}

	// Resol l'ine5: primer pel slug del Berguedà; si no, per un muni cobert (slug del nom oficial).
	let ine5 = slugToIne5[params.slug] ?? null;
	if (!ine5 && pernoctaAll) {
		for (const [code, m] of Object.entries(pernoctaAll.munis)) {
			if (toSlug(m.nom) === params.slug) {
				ine5 = code;
				break;
			}
		}
	}
	// `row` (dades completes del Berguedà) null per a munis coberts/desconeguts → es mostra el rang
	// (si cobert) o l'estat «sense dades encara».
	const row = ine5 ? (dataset.municipis[ine5] ?? null) : null;
	const pernocta: PernoctaMuni | null = ine5 && pernoctaAll ? (pernoctaAll.munis[ine5] ?? null) : null;

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

	// Lectura-IA del municipi (§3): opcional, de l'artefacte versionat `lectures.bergueda.json`
	// (la genera `tools/gen_fitxa.py`). Es passa en els DOS idiomes; la pàgina en tria el del
	// locale. Si l'artefacte no hi és encara (build sense generar), `lectura` és null i la fitxa
	// degrada amablement (cap veredicte/lectura, només els números i la maquinària). Prerender-safe.
	let lectura: LecturaEntry | null = null;
	if (ine5) {
		try {
			const res = await fetch('/data/lectures.bergueda.json');
			if (res.ok) {
				const data = (await res.json()) as LecturesData;
				lectura = data[ine5] ?? null;
			}
		} catch {
			lectura = null;
		}
	}

	return { dataset, ine5, row, lic, lectura, pernocta };
};
