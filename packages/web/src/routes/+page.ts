/**
 * Arrel `/`: redirigeix a la pantalla de resum, conservant el locale actiu.
 * El prefix d'idioma (/ca | /es) el resol Paraglide via `localizeHref`/reroute.
 */
import { redirect } from '@sveltejs/kit';
import { localizeHref } from '$lib/i18n';
import type { PageLoad } from './$types';

export const load: PageLoad = () => {
	redirect(307, localizeHref('/resum'));
};
