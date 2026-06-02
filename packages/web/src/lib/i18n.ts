/**
 * Pont i18n entre Paraglide (runtime compilat) i SvelteKit.
 *
 * Estratègia (vegeu vite.config.ts): URL-first amb prefix /ca | /es, cookie de
 * record i fallback a baseLocale (ca). Les rutes de fitxers de SvelteKit es mantenen
 * CANÒNIQUES (sense carpeta per idioma): Paraglide "des-localitza" la URL entrant
 * via `reroute` (hooks compartits) i "localitza" els enllaços sortints.
 *
 * Aquest mòdul només reexporta i tipa el runtime generat, perquè la resta de l'app
 * importi d'un únic lloc estable (`$lib/i18n`) i no de `$paraglide/runtime` directament.
 */

import {
	baseLocale,
	locales,
	getLocale,
	setLocale,
	localizeUrl,
	deLocalizeUrl,
	localizeHref
} from '$lib/paraglide/runtime';
import type { Locale } from '$lib/contract/types';

export { baseLocale, locales, getLocale, setLocale, localizeUrl, deLocalizeUrl, localizeHref };

/** Llista de locales suportats, tipada al contracte (ca | es). */
export const SUPPORTED_LOCALES = locales as readonly Locale[];

/** Locale per defecte (ca), tipat. */
export const DEFAULT_LOCALE = baseLocale as Locale;

/** True si `value` és un locale suportat. */
export function isLocale(value: string): value is Locale {
	return (SUPPORTED_LOCALES as readonly string[]).includes(value);
}

/**
 * Locale actiu en aquest context de petició/render, tipat com a `Locale`.
 * Embolcalla `getLocale()` de Paraglide (resol via AsyncLocalStorage al servidor).
 */
export function currentLocale(): Locale {
	return getLocale() as Locale;
}

/** Tria el valor traduït correcte d'un camp del contracte segons el locale actiu. */
export function pick(localized: Record<Locale, string>, locale: Locale = currentLocale()): string {
	return localized[locale] ?? localized[DEFAULT_LOCALE];
}

/**
 * Etiqueta humana de cada locale per al selector d'idioma.
 * (El nom traduït de cada idioma també està als catàlegs; això és el rètol curt natiu.)
 */
export const LOCALE_LABEL: Record<Locale, string> = {
	ca: 'CA',
	es: 'ES'
};
