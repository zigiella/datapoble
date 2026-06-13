/**
 * Etiquetes i format compartits de Licitacions (secció `/licitacions` + bloc de fitxa).
 * Les etiquetes són copy i18n (categòric nou, no al contracte semàntic).
 */
import { m } from '$lib/paraglide/messages';

const TEMA: Record<string, () => string> = {
	residus: () => m.lic_tema_residus(),
	aigua: () => m.lic_tema_aigua(),
	turisme: () => m.lic_tema_turisme(),
	cultura: () => m.lic_tema_cultura(),
	mobilitat: () => m.lic_tema_mobilitat(),
	habitatge: () => m.lic_tema_habitatge(),
	urbanisme: () => m.lic_tema_urbanisme(),
	manteniment: () => m.lic_tema_manteniment(),
	energia: () => m.lic_tema_energia(),
	social: () => m.lic_tema_social(),
	educacio: () => m.lic_tema_educacio(),
	salut: () => m.lic_tema_salut(),
	seguretat: () => m.lic_tema_seguretat(),
	digitalitzacio: () => m.lic_tema_digitalitzacio(),
	administracio: () => m.lic_tema_administracio(),
	altres: () => m.lic_tema_altres()
};
export const temaLabel = (t: string): string => TEMA[t]?.() ?? t;

const LECTURA: Record<string, () => string> = {
	autonom: () => m.lic_lectura_autonom(),
	dependencia_mitjana: () => m.lic_lectura_mitjana(),
	molt_dependent: () => m.lic_lectura_molt(),
	no_contracta_propi: () => m.lic_lectura_nopropi()
};
export const lecturaLabel = (l: string): string => LECTURA[l]?.() ?? l;

/** Import en euros, forma curta i humana (42,4 M€ · 886 k€ · 1.200 €). `intl` = 'ca-ES'/'es-ES'. */
export function eurCurt(v: number | null, intl: string): string {
	if (v == null) return '—';
	if (v >= 1e6)
		return `${(v / 1e6).toLocaleString(intl, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} M€`;
	if (v >= 1e3) return `${Math.round(v / 1e3).toLocaleString(intl)} k€`;
	return `${v.toLocaleString(intl)} €`;
}
