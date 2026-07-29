/**
 * La COMPOSICIÓ de la pàgina de metodologia (`/metodologia`): quins blocs editorials hi ha,
 * quines claus de mètrica documenta cadascun i quins són ANNEX DE RECERCA (model aparcat).
 *
 * ⚠️ Font ÚNICA de la composició: la comparteixen la pàgina (`routes/metodologia/+page.svelte`,
 * que hi posa títol i intro i18n per `ref`) i el verificador offline (`scripts/verify-docs.mjs`)
 * perquè no derivin. JS pur (sense tipus, sense Svelte, sense paraglide) perquè Node el pugui
 * importar tal qual — mateix patró que `src/lib/govern/kpis.js`.
 *
 * P-DOC (2026-07-27): dues coses que aquesta llista arregla i que el verificador guarda:
 *  1) El 500 LATENT: la pàgina renderitzava `dataset.metrics[key]` SENSE guarda — una clau
 *     fantasma als blocs petava el render amb el build verd (ja va passar amb index_turisme).
 *     Ara la pàgina FILTRA les claus absents i `verify-docs.mjs` CAU si un bloc en llista una
 *     que el dataset no serveix: la verificació local es posa vermella, la pàgina no.
 *  2) L'EMMARCAMENT: kg_hab_any / kwh_hab / vidre_hab / restauracio_* són targetes VIVES del
 *     tauler (E2 de Bea) i vivien NOMÉS dins l'annex «model aparcat» — un lector n'hauria
 *     conclòs que són recerca aparcada. Ara tenen fitxa als blocs vius; a l'annex hi queden
 *     només les peces del model (ràtios de base, gap de pernocta, càrregues i la bandera).
 *
 * `annex: true` = el bloc documenta el MODEL D'ESTIMACIÓ DE PERNOCTA, aparcat del web (vot de
 * Bea 2026-07-16). NO s'esborra — la metodologia és el rastre honest — però s'etiqueta com a
 * annex de recerca perquè ningú el llegeixi com a part del producte viu.
 *
 * @typedef {Object} MetodologiaBloc
 * @property {string} ref      Lletra de secció (visible; també la clau del títol/intro a la pàgina).
 * @property {string[]} keys   Claus de mètrica del contracte documentades al bloc, en ordre.
 * @property {boolean} [annex] El bloc és annex de recerca (model aparcat).
 */

/** @type {MetodologiaBloc[]} */
export const METODOLOGIA_BLOCS = [
	// A · Demografia i habitatge — amb les franges d'edat (E12), l'índex d'envelliment i la renda:
	// totes targetes del tauler viu. La 15-64 és DERIVADA per resta (fórmula al contracte,
	// verificada als 947: la suma de franges quadra amb la població, residu 0).
	{
		ref: 'A',
		keys: [
			'poblacio', 'pob_0_14', 'pob_15_64', 'pob_65_84', 'pob_85_mes', 'index_envelliment',
			'renda_neta_persona', 'hab_noprincipal', 'pct_noprincipal', 'hab_per_hab'
		]
	},
	// B · Treball — l'atur registrat (SEPE), amb la doctrina del «<5» al seu advertiment.
	{ ref: 'B', keys: ['atur_registrat'] },
	// C · Turisme reglat — el registre oficial sencer: total, HUT i les dues penetracions
	// (per càpita i sobre el parc; la segona amb el caveat de barreja de vintages 2021/2025).
	{ ref: 'C', keys: ['rtc_total', 'rtc_hut', 'rtc_per_1000hab', 'rtc_per_100hab_viv'] },
	// D · Comerç, serveis i restauració — els dos comptes OSM del tauler i les seves densitats
	// (MÍNIM observat, no cens: el caveat d'infra-mapejat rural ve del contracte).
	{
		ref: 'D',
		keys: ['serveis_estab', 'serveis_per_1000hab', 'restauracio_estab', 'restauracio_per_1000hab']
	},
	// E · El pols de la vida diària — els tres rastres físics del bloc D del tauler (E2 de Bea):
	// residus, elèctric domèstic i vidre. VIUS, no annex: aquí com a mesures oficials per capita.
	{ ref: 'E', keys: ['kg_hab_any', 'kwh_hab', 'vidre_hab'] },
	// F · Energia i rehabilitació.
	{ ref: 'F', keys: ['pct_icaen_EFG'] },
	// G · Transformació demogràfica (dimensió `origen`).
	{
		ref: 'G',
		keys: [
			'poblacio_nascuda_catalunya',
			'poblacio_nascuda_resta_espanya',
			'poblacio_nascuda_estranger',
			'pct_nascuda_estranger',
			'pct_nacionalitat_estrangera',
			'bretxa_naturalitzacio',
			'delta_pct_estrangera_finestra',
			'confianca_origen'
		]
	},
	// H · ANNEX — el model d'estimació de pernocta: les peces que NOMÉS existeixen dins el model
	// (ràtios contra la base residencial, gap de pernocta, càrregues i la bandera de confiança).
	{
		ref: 'H',
		annex: true,
		keys: [
			'kwh_base_ratio', 'gap_pernocta_pct', 'residu_base_ratio',
			'carrega_total_est', 'carrega_funcional_est', 'vidre_base_ratio', 'confianca'
		]
	}
];
