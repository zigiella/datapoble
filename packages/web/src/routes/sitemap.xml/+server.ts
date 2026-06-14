/**
 * sitemap.xml — generat en build (prerender). Una entrada per ruta × idioma (/ca, /es),
 * cada una amb els seus `xhtml:link` alternates (ca/es/x-default→ca), com demana Google per a
 * llocs multilingües. El prefix es construeix a mà (/<locale><ruta>) per coincidir EXACTAMENT
 * amb `urlPatterns` (vite.config), sense dependre de quirks de localizeHref. Pre-llançament el
 * lloc va `noindex`; això és la bastida perquè al llançament només calgui treure el noindex.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import { slugForIne5 } from '$lib/contract/slug';
import type { RequestHandler } from './$types';

export const prerender = true;

const SITE = 'https://riusdegent.cat';
const LOCALES = ['ca', 'es'] as const;
const STATIC_ROUTES = [
	'/',
	'/resum/',
	'/mapa/',
	'/licitacions/',
	'/metodologia/',
	'/glossari/',
	'/pregunta-li/'
];

const loc = (route: string, locale: string) => `${SITE}/${locale}${route === '/' ? '/' : route}`;

export const GET: RequestHandler = async ({ fetch }) => {
	const dataset = await loadMunicipisDataset(fetch);
	const muniRoutes = Object.keys(dataset.municipis).map(
		(ine5) => `/municipi/${slugForIne5(ine5, dataset)}/`
	);
	const routes = [...STATIC_ROUTES, ...muniRoutes];

	const urls = routes.flatMap((route) =>
		LOCALES.map((locale) => {
			const alts = [
				...LOCALES.map((l) => `    <xhtml:link rel="alternate" hreflang="${l}" href="${loc(route, l)}"/>`),
				`    <xhtml:link rel="alternate" hreflang="x-default" href="${loc(route, 'ca')}"/>`
			].join('\n');
			return `  <url>\n    <loc>${loc(route, locale)}</loc>\n${alts}\n  </url>`;
		})
	);

	const xml =
		`<?xml version="1.0" encoding="UTF-8"?>\n` +
		`<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n` +
		`${urls.join('\n')}\n</urlset>\n`;

	return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });
};
