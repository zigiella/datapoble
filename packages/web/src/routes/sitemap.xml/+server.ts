/**
 * sitemap.xml — generat en build (prerender). Una entrada per ruta × idioma (/ca, /es),
 * cada una amb els seus `xhtml:link` alternates (ca/es/x-default→ca), com demana Google per a
 * llocs multilingües. El prefix es construeix a mà (/<locale><ruta>) per coincidir EXACTAMENT
 * amb `urlPatterns` (vite.config), sense dependre de quirks de localizeHref. Pre-llançament el
 * lloc va `noindex`; això és la bastida perquè al llançament només calgui treure el noindex.
 */
import { toSlug } from '$lib/contract/slug';
import type { CatalegData } from '$lib/contract/cataleg';
import type { ComarquesData } from '$lib/contract/comarques';
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
	// TOTS els municipis de Catalunya (catàleg): cada poble té fitxa prerenderitzada → entra al
	// sitemap (mateixa font que `municipi/[slug]` entries()). No-fatal si falta el catàleg.
	let muniRoutes: string[] = [];
	try {
		const res = await fetch('/data/municipis-cataleg.json');
		if (res.ok) {
			const cataleg = (await res.json()) as CatalegData;
			const slugs = new Set(cataleg.map((m) => toSlug(m.nom)));
			muniRoutes = [...slugs].map((slug) => `/municipi/${slug}/`);
		}
	} catch {
		muniRoutes = [];
	}

	// Pàgines de comarca (43) i vegueria (8): prerenderitzades, entren al sitemap.
	let terrRoutes: string[] = [];
	try {
		const res = await fetch('/data/comarques.json');
		if (res.ok) {
			const data = (await res.json()) as ComarquesData;
			terrRoutes = [
				...data.comarques.map((c) => `/comarca/${toSlug(c.nom)}/`),
				...data.vegueries.map((v) => `/vegueria/${toSlug(v.nom)}/`)
			];
		}
	} catch {
		terrRoutes = [];
	}
	const routes = [...STATIC_ROUTES, ...terrRoutes, ...muniRoutes];

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
