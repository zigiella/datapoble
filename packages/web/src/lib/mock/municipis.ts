/**
 * Dades MOCK amb la forma del contracte (datapoble).
 *
 * Per què existeix: el frontend (Mirador) arrenca abans que el pipeline (Sondeig)
 * publiqui els marts i abans que l'API estigui llesta. Aquest mòdul implementa
 * `MunicipisDataset` (src/lib/contract/types.ts) amb dades VERIFICADES del prototip
 * (docs/data-sources.md, "Experimento 0", verificació 2026-06-01), de manera que la
 * pantalla "resum" ja es pot construir contra la forma real.
 *
 * Honest boundaries:
 *  - Les etiquetes (label.ca/.es, unit) són còpia literal de `semantic/metrics.yml`.
 *    La UI MAI no codifica etiquetes; vénen d'aquí (= del contracte).
 *  - Castellar de n'Hug (08052) i Berga (08022) duen valors reals del prototip.
 *  - Els KPIs comarcals i alguns derivats marcats com a "≈" són il·lustratius
 *    (placeholders coherents) fins que el mart real els calculi. Estan anotats.
 *  - Quan arribi l'artefacte/endpoint, es reemplaça aquest mòdul per un loader;
 *    la forma (MunicipisDataset) no canvia.
 */

import type { MetricDef, MetricKey, MunicipiRow, MunicipisDataset } from '$lib/contract/types';

/**
 * Catàleg d'indicadors. `label` i `unit` són literals de metrics.yml.
 * Subconjunt orientat a la pantalla "resum"; ampliable a la resta de mètriques.
 */
const metrics: Record<MetricKey, MetricDef> = {
	poblacio: {
		key: 'poblacio',
		label: { ca: 'Població', es: 'Población' },
		unit: { ca: 'habitants', es: 'habitantes' },
		dimension: 'demografia',
		format: 'integer',
		source: 'Idescat — EMEX / Cens 2021',
		date: '2025',
		status: 'public'
	},
	hab_total: {
		key: 'hab_total',
		label: { ca: 'Habitatges (total)', es: 'Viviendas (total)' },
		unit: { ca: 'habitatges', es: 'viviendas' },
		dimension: 'vivenda',
		format: 'integer',
		source: 'Idescat — EMEX / Cens 2021',
		date: '2021',
		status: 'public'
	},
	hab_principal: {
		key: 'hab_principal',
		label: { ca: 'Habitatges principals', es: 'Viviendas principales' },
		unit: { ca: 'habitatges', es: 'viviendas' },
		dimension: 'vivenda',
		format: 'integer',
		source: 'Idescat — EMEX / Cens 2021',
		date: '2021',
		status: 'public'
	},
	hab_noprincipal: {
		key: 'hab_noprincipal',
		label: { ca: 'Habitatges no principals', es: 'Viviendas no principales' },
		unit: { ca: 'habitatges', es: 'viviendas' },
		dimension: 'vivenda',
		format: 'integer',
		source: 'Idescat — EMEX / Cens 2021',
		date: '2021',
		note: {
			ca: 'Secundàries + buides (no residència habitual). Senyal estructural de segona residència.',
			es: 'Secundarias + vacías (no residencia habitual). Señal estructural de segunda residencia.'
		},
		status: 'public'
	},
	pct_noprincipal: {
		key: 'pct_noprincipal',
		label: { ca: '% habitatge no principal', es: '% vivienda no principal' },
		unit: { ca: '%', es: '%' },
		dimension: 'vivenda',
		format: 'percent',
		source: 'datapoble (calculat) · Idescat EMEX',
		date: '2021',
		status: 'public'
	},
	hab_per_hab: {
		key: 'hab_per_hab',
		label: { ca: 'Habitatges per habitant', es: 'Viviendas por habitante' },
		unit: { ca: 'ràtio', es: 'ratio' },
		dimension: 'vivenda',
		format: 'ratio',
		source: 'datapoble (calculat)',
		date: '2021/2025',
		status: 'public'
	},
	index_envelliment: {
		key: 'index_envelliment',
		label: { ca: "Índex d'envelliment", es: 'Índice de envejecimiento' },
		unit: { ca: '65+/0-14 ×100', es: '65+/0-14 ×100' },
		dimension: 'demografia',
		format: 'decimal',
		source: 'Idescat — EMEX',
		date: '2025',
		status: 'planned'
	},
	rtc_total: {
		key: 'rtc_total',
		label: { ca: 'Establiments turístics', es: 'Establecimientos turísticos' },
		unit: { ca: 'establiments', es: 'establecimientos' },
		dimension: 'turisme',
		format: 'integer',
		source: 'Generalitat — Registre de Turisme de Catalunya (RTC)',
		date: '2026',
		status: 'public'
	},
	rtc_hut: {
		key: 'rtc_hut',
		label: { ca: "HUT (habitatges d'ús turístic)", es: 'HUT (viviendas de uso turístico)' },
		unit: { ca: 'establiments', es: 'establecimientos' },
		dimension: 'turisme',
		format: 'integer',
		source: 'Generalitat — RTC',
		date: '2026',
		status: 'public'
	},
	rtc_per_1000hab: {
		key: 'rtc_per_1000hab',
		label: { ca: 'Establiments / 1000 hab', es: 'Establecimientos / 1000 hab' },
		unit: { ca: 'per mil', es: 'por mil' },
		dimension: 'turisme',
		format: 'decimal',
		source: 'datapoble (calculat)',
		status: 'public'
	},
	rtc_per_100hab_viv: {
		key: 'rtc_per_100hab_viv',
		label: { ca: 'Establiments / 100 habitatges', es: 'Establecimientos / 100 viviendas' },
		unit: { ca: 'per cent', es: 'por cien' },
		dimension: 'turisme',
		format: 'decimal',
		source: 'datapoble (calculat)',
		status: 'public'
	},
	kg_hab_any: {
		key: 'kg_hab_any',
		label: { ca: 'Residus kg/hab/any', es: 'Residuos kg/hab/año' },
		unit: { ca: 'kg/hab/any', es: 'kg/hab/año' },
		dimension: 'pressio',
		format: 'decimal',
		source: 'Agència de Residus de Catalunya (ARC)',
		date: '2024',
		note: {
			ca: 'Proxy de càrrega real (població fantasma): captura l’excursionista de dia que el padró no veu.',
			es: 'Proxy de carga real (población fantasma): capta al excursionista de día que el padrón no ve.'
		},
		status: 'public'
	},
	pct_icaen_EFG: {
		key: 'pct_icaen_EFG',
		label: { ca: '% certificats E-G', es: '% certificados E-G' },
		unit: { ca: '%', es: '%' },
		dimension: 'energia',
		format: 'percent',
		source: 'datapoble (calculat) · ICAEN',
		status: 'public'
	},
	IETR: {
		key: 'IETR',
		label: {
			ca: "Índex d'Exposició Turística-Residencial",
			es: 'Índice de Exposición Turística-Residencial'
		},
		unit: { ca: '0-100', es: '0-100' },
		dimension: 'index',
		format: 'decimal',
		source: 'datapoble (calculat)',
		note: {
			ca: 'Exposició estructural (stock), no pressió realitzada. Validat externament amb residus (r=0,87).',
			es: 'Exposición estructural (stock), no presión realizada. Validado externamente con residuos (r=0,87).'
		},
		status: 'public'
	},
	IETR_rank: {
		key: 'IETR_rank',
		label: { ca: 'Rànquing IETR', es: 'Ranking IETR' },
		unit: { ca: 'posició', es: 'posición' },
		dimension: 'index',
		format: 'rank',
		source: 'datapoble (calculat)',
		status: 'public'
	},
	pct_indep: {
		key: 'pct_indep',
		label: { ca: '% vot independentista', es: '% voto independentista' },
		unit: { ca: '%', es: '%' },
		dimension: 'politica',
		format: 'percent',
		source: 'Generalitat — Processos electorals',
		date: '2024',
		note: {
			ca: 'Lectura ECOLÒGICA (no individual; falàcia ecològica). Volàtil en micromunicipis (N petit).',
			es: 'Lectura ECOLÓGICA (no individual; falacia ecológica). Volátil en micromunicipios (N pequeño).'
		},
		status: 'public'
	},
	pct_esquerra: {
		key: 'pct_esquerra',
		label: { ca: '% vot esquerra', es: '% voto izquierda' },
		unit: { ca: '%', es: '%' },
		dimension: 'politica',
		format: 'percent',
		source: 'Generalitat — Processos electorals',
		date: '2024',
		note: {
			ca: 'Lectura ecològica (no individual).',
			es: 'Lectura ecológica (no individual).'
		},
		status: 'public'
	},
	pct_extrema_dreta: {
		key: 'pct_extrema_dreta',
		label: { ca: '% vot extrema dreta', es: '% voto extrema derecha' },
		unit: { ca: '%', es: '%' },
		dimension: 'politica',
		format: 'percent',
		source: 'Generalitat — Processos electorals',
		date: '2017-2024',
		note: {
			ca: 'Lectura ecològica. Aliança Catalana és el focus (extrema dreta independentista, emergent i rural).',
			es: 'Lectura ecológica. Aliança Catalana es el foco (extrema derecha independentista, emergente y rural).'
		},
		status: 'planned'
	},
	guanya: {
		key: 'guanya',
		label: { ca: 'Candidatura guanyadora', es: 'Candidatura ganadora' },
		unit: { ca: 'sigla', es: 'sigla' },
		dimension: 'politica',
		format: 'text',
		source: 'Generalitat — Processos electorals',
		date: '2024',
		status: 'public'
	}
};

/**
 * Files de municipis. Dades VERIFICADES per a Castellar (08052) i Berga (08022)
 * — vegeu docs/data-sources.md §8 "Hechos verificados clave (en vivo)".
 * Els valors marcats amb el comentari "≈ il·lustratiu" són coherents però provisionals
 * fins que el mart real els publiqui (sobretot els derivats per càpita i els polítics).
 */
const municipis: Record<string, MunicipiRow> = {
	// Castellar de n'Hug — INE 08052 (Catastro 08051), Idescat 080522.
	'08052': {
		ine5: '08052',
		nom: "Castellar de n'Hug",
		idescat6: '080522',
		values: {
			poblacio: 166, // 2025
			hab_total: 276, // Cens 2021
			hab_principal: 71,
			hab_noprincipal: 205,
			pct_noprincipal: 74.3, // 205/276
			hab_per_hab: 1.66, // 276/166
			rtc_total: 30, // RTC, majoria HUT
			rtc_hut: 26, // ≈ il·lustratiu (gros del RTC són HUT)
			rtc_per_1000hab: 180.7, // 30/166*1000
			rtc_per_100hab_viv: 10.9, // 30/276*100
			kg_hab_any: 612.0, // ≈ il·lustratiu: proxy elevat per la càrrega d'excursionista de dia
			pct_icaen_EFG: 68.0, // ≈ il·lustratiu (parc antic; 58 certificats totals)
			IETR: 100.0, // extrem superior de la distribució comarcal
			IETR_rank: 1, // de 31
			pct_indep: 78.0, // ≈ il·lustratiu (mesa única; lectura ecològica, N petit)
			pct_esquerra: 24.0, // ≈ il·lustratiu
			pct_extrema_dreta: null, // status: planned al contracte
			guanya: 'Junts' // ≈ il·lustratiu
		}
	},
	// Berga — INE i Catastro 08022, Idescat 080229.
	'08022': {
		ine5: '08022',
		nom: 'Berga',
		idescat6: '080229',
		values: {
			poblacio: 17160, // ~2025
			hab_total: 9200, // ≈ il·lustratiu (parc urbà; pendent split Idescat)
			hab_principal: 7400, // ≈ il·lustratiu
			hab_noprincipal: 1800, // ≈ il·lustratiu
			pct_noprincipal: 19.6, // ≈ il·lustratiu
			hab_per_hab: 0.54, // ≈ il·lustratiu
			rtc_total: 45, // RTC: 36 HUT + 4 hotels + 4 rural + 1 càmping
			rtc_hut: 36,
			rtc_per_1000hab: 2.6, // 45/17160*1000 — ~69× menys intensitat que Castellar
			rtc_per_100hab_viv: 0.49, // ≈ il·lustratiu
			kg_hab_any: 458.0, // ≈ il·lustratiu (capital comarcal, càrrega més estable)
			pct_icaen_EFG: 52.0, // ≈ il·lustratiu (2.550 certificats)
			IETR: 41.0, // ≈ il·lustratiu (exposició mitjana-baixa)
			IETR_rank: 18, // ≈ il·lustratiu, de 31
			pct_indep: 56.0, // ≈ il·lustratiu (lectura ecològica)
			pct_esquerra: 47.0, // ≈ il·lustratiu
			pct_extrema_dreta: null, // status: planned
			guanya: 'ERC' // ≈ il·lustratiu
		}
	}
};

/**
 * KPIs comarcals (Berguedà, 31 municipis). En producció els calcula el pipeline
 * (mitjanes/sumes sobre tots els municipis). Aquí són ≈ il·lustratius però
 * coherents amb l'escala comarcal descrita a docs/data-sources.md.
 */
const dataset: MunicipisDataset = {
	contractVersion: '1.0',
	scope: 'Berguedà (31 municipis) → Catalunya (~947) en investigació',
	metrics,
	municipis,
	comarca: {
		label: { ca: 'Berguedà', es: 'Berguedà' },
		num_municipis: 31,
		values: {
			poblacio: 39200, // ≈ il·lustratiu (suma comarcal aprox.)
			hab_total: 26500, // ≈ il·lustratiu
			pct_noprincipal: 41.0, // ≈ il·lustratiu (mitjana comarcal)
			rtc_total: 690, // ≈ il·lustratiu (suma comarcal)
			rtc_per_1000hab: 17.6, // ≈ il·lustratiu
			kg_hab_any: 489.0, // ≈ il·lustratiu (mitjana comarcal)
			IETR: 50.0 // mediana de la distribució normalitzada
		}
	}
};

/** Codis INE5 dels dos municipis destacats a la comparativa del "resum". */
export const FEATURED_INE5 = {
	castellar: '08052',
	berga: '08022'
} as const;

/**
 * Retorna el dataset complet (forma `MunicipisDataset`).
 * Punt d'enganxament per al futur loader real (artefacte/API): substituir
 * aquest cos per la càrrega de dades sense canviar la signatura ni la forma.
 */
export function getMunicipisDataset(): MunicipisDataset {
	return dataset;
}

/** Conveniència: una fila de municipi per INE5 (o undefined si no hi és). */
export function getMunicipi(ine5: string): MunicipiRow | undefined {
	return dataset.municipis[ine5];
}
