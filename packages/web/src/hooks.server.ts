/**
 * Hooks de servidor.
 *
 * `paraglideMiddleware` (generat a $lib/paraglide/server) detecta el locale de cada
 * petició segons l'estratègia configurada (url > cookie > baseLocale) i el fa
 * disponible via AsyncLocalStorage durant tot el render SSR, de manera que
 * `getLocale()` i els missatges `m.*` resolen el locale correcte fins i tot amb
 * peticions concurrents.
 *
 * A més, injectem `lang="<locale>"` a l'etiqueta <html> via `transformPageChunk`,
 * cosa necessària per a accessibilitat (lectors de pantalla) i SEO.
 */

import type { Handle } from '@sveltejs/kit';
import { paraglideMiddleware } from '$lib/paraglide/server';

export const handle: Handle = ({ event, resolve }) =>
	paraglideMiddleware(event.request, ({ request, locale }) => {
		event.request = request;
		return resolve(event, {
			transformPageChunk: ({ html }) => html.replace('%paraglide.lang%', locale)
		});
	});
