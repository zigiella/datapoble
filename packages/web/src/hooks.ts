/**
 * Hooks universals (client + servidor).
 *
 * `reroute` tradueix la URL que veu el navegador (localitzada: /es/mapa) a la ruta
 * canònica del sistema de fitxers de SvelteKit (/mapa). Així NO cal duplicar carpetes
 * per idioma: hi ha un sol arbre de rutes i Paraglide fa el mapatge a la frontera.
 *
 * Aparellat amb `localizeHref`/`localizeUrl` per als enllaços sortints (vegeu LangSwitcher
 * i la navegació), que afegeixen el prefix de locale correcte.
 */

import { deLocalizeUrl } from '$lib/paraglide/runtime';
import type { Reroute } from '@sveltejs/kit';

export const reroute: Reroute = (request) => {
	return deLocalizeUrl(request.url).pathname;
};
