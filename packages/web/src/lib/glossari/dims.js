/**
 * La COMPOSICIÓ del glossari (`/glossari`): quines DIMENSIONS del contracte es publiquen al
 * diccionari i quines mètriques se n'amaguen (modelo aparcat / índexs interns).
 *
 * ⚠️ Font ÚNICA de la composició: la comparteixen la pàgina (`routes/glossari/+page.svelte`)
 * i el verificador offline (`scripts/verify-docs.mjs`) perquè no derivin. JS pur (sense tipus,
 * sense Svelte, sense paraglide) perquè Node el pugui importar tal qual — mateix patró que
 * `src/lib/govern/kpis.js`.
 *
 * P-DOC (2026-07-27): aquesta llista era una LLISTA FIXA DINS LA PÀGINA i descartava EN SILENCI
 * les dimensions que no coneixia — `treball` (atur registrat) i `origen` (les 8 de lloc de
 * naixement/nacionalitat) van arribar al dataset i el glossari les va callar: la capçalera deia
 * «26 indicadors» quan el contracte en publica 35. És la mateixa forma de bug que D10 va tancar
 * al mart (una llista a mà que la propera dimensió nova torna a trencar). Per això la llista viu
 * aquí i `verify-docs.mjs` CAU si el dataset porta una dimensió amb mètriques publicables que no
 * sigui a `GLOSSARI_DIMS` — la propera dimensió nova farà soroll, no silenci.
 */

/**
 * Ordre de presentació de les dimensions del contracte (les que quedin sense cap mètrica
 * publicable se salten soles a la pàgina). Les CLAUS són del contracte (`MetricDef.dimension`);
 * l'etiqueta humana de cadascuna és el missatge i18n `glo_dim_<dim>` (ca+es).
 * @type {string[]}
 */
export const GLOSSARI_DIMS = [
	'demografia',
	'origen',
	'vivenda',
	'treball',
	'turisme',
	'serveis',
	'pressio',
	'index',
	'energia'
];

/**
 * Indicadors retirats del públic (no surten al diccionari): l'IETR i la seva família, el model
 * d'una sola capa antic, els scores interns i — FASE NOVA (model aparcat, vot de Bea
 * 2026-07-16) — TOTA la família del model d'estimació de pernocta (gap_pernocta*,
 * poblacio_pernocta_est, carrega_*, index_turisme, ràtios de base, bandera de confiança i
 * tipologia derivada). La dada segueix al contracte; només no es publica aquí.
 * @type {string[]}
 */
export const GLOSSARI_HIDDEN = [
	'IETR', 'IETR_rank', 'IETR_stock', 'IETR_impact',
	'poblacio_real_est', 'gap_abs', 'gap_pct', 'poblacio_real_rel',
	'confianca_score', 'divergencia_senyals',
	// Família del model aparcat (A8 · fase-nova-aparcaments.md):
	'gap_pernocta', 'gap_pernocta_pct', 'poblacio_pernocta_est',
	'carrega_total_est', 'carrega_funcional_est', 'index_turisme',
	'kwh_base_ratio', 'residu_base_ratio', 'vidre_base_ratio',
	'confianca', 'tipologia'
];
