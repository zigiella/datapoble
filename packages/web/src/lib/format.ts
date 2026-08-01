/**
 * Formatatge de xifres i dates amb `Intl`, sensible al locale actiu.
 *
 * Per què: ca i es fan servir el punt com a separador de milers i la coma com a
 * decimal, però altres convencions (percentatge, signe) i futurs locales (en/fr)
 * difereixen. Centralitzem-ho aquí perquè cap component "cuini" números a mà.
 *
 * El mapatge de `MetricFormat` -> opcions d'Intl viu aquí; els components només
 * criden `formatMetric(value, def, locale)` i obtenen la cadena ja localitzada.
 */

import type { Locale, MetricDef, MetricValue } from '$lib/contract/types';

/** Mapatge mínim al BCP-47 que entén Intl. */
const BCP47: Record<Locale, string> = {
	ca: 'ca-ES',
	es: 'es-ES'
};

function intlLocale(locale: Locale): string {
	return BCP47[locale] ?? 'ca-ES';
}

/** Enter localitzat (separador de milers segons locale). */
export function formatInteger(value: number, locale: Locale): string {
	return new Intl.NumberFormat(intlLocale(locale), { maximumFractionDigits: 0 }).format(value);
}

/** Decimal localitzat amb un nombre fix de decimals. */
export function formatDecimal(value: number, locale: Locale, fractionDigits = 1): string {
	return new Intl.NumberFormat(intlLocale(locale), {
		minimumFractionDigits: fractionDigits,
		maximumFractionDigits: fractionDigits
	}).format(value);
}

/**
 * Percentatge localitzat. Els valors del contracte ja vénen en escala 0-100
 * (p. ex. pct_noprincipal = 74.3), de manera que dividim per 100 abans de
 * formatar amb `style: 'percent'` perquè Intl posi el signe correcte.
 */
export function formatPercent(value: number, locale: Locale, fractionDigits = 1): string {
	return new Intl.NumberFormat(intlLocale(locale), {
		style: 'percent',
		minimumFractionDigits: fractionDigits,
		maximumFractionDigits: fractionDigits
	}).format(value / 100);
}

/** Data/any. Accepta any (número/cadena) o ISO; aquí formatem només l'any de moment. */
export function formatYear(value: number | string, locale: Locale): string {
	// Els valors del contracte solen ser anys o rangs ("2021", "2017-2024").
	// Si és un any net, el deixem tal qual (no hi ha localització d'un enter d'any);
	// la funció existeix per a quan el pipeline passi dates completes.
	return String(value);
}

/**
 * Xifra del TAULER DE DADES: com `formatMetric`, però SENSE el símbol de percentatge — el
 * markup del tauler el pinta com a unitat petita al costat, i posar-l'hi aquí el duplicaria.
 *
 * Viu aquí, i no dins d'una pàgina, perquè la fitxa del municipi i el LLISTAT per comarca
 * (W2) han de formatar la mateixa xifra exactament igual: si divergissin, la mateixa dada es
 * llegiria amb dos nombres de decimals segons per on hi arribes.
 *
 * Retorna `null` quan no hi ha valor, perquè qui la crida triï el text de «sense dada» (i18n).
 */
export function formatBoardValue(
	value: MetricValue | undefined,
	def: Pick<MetricDef, 'format'>,
	locale: Locale
): string | null {
	if (value === null || value === undefined) return null;
	if (def.format === 'percent' && typeof value === 'number') return formatDecimal(value, locale, 1);
	return formatMetric(value, def, locale);
}

/**
 * Formata el valor d'una mètrica segons el seu `format` declarat al contracte.
 * Retorna `null` perquè el cridador decideixi com mostrar "no disponible" (i18n).
 */
export function formatMetric(
	value: MetricValue | undefined,
	def: Pick<MetricDef, 'format'>,
	locale: Locale
): string | null {
	if (value === null || value === undefined) return null;

	switch (def.format) {
		case 'text':
			return String(value);
		case 'rank':
			return typeof value === 'number' ? formatInteger(value, locale) : String(value);
		case 'integer':
			return typeof value === 'number' ? formatInteger(value, locale) : String(value);
		case 'percent':
			return typeof value === 'number' ? formatPercent(value, locale) : String(value);
		case 'ratio':
			return typeof value === 'number' ? formatDecimal(value, locale, 2) : String(value);
		case 'decimal':
		default:
			return typeof value === 'number' ? formatDecimal(value, locale, 1) : String(value);
	}
}
