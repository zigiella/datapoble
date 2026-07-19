/**
 * Els KPIs de la vista de govern (D5), en ORDRE FIX (gorra §3 / C6 §1.3, §7).
 *
 * ⚠️ Font ÚNICA de l'ordre i la composició del tauler: la comparteixen el component
 * (`municipi/[slug]/+page.svelte`) i el verificador offline (`scripts/verify-govern.mjs`)
 * perquè no derivin. JS pur (sense tipus, sense Svelte, sense paraglide) perquè Node el
 * pugui importar tal qual al test.
 *
 * Política editorial (C6 §7): l'ordre NO es reordena per enterrar cap indicador. Els
 * 12 «caps» de la gorra, amb dues absències DECLARADES:
 *  · slot 11 RADAR — porta del §4 de l'spec no superada → NO es renderitza res (C6 §5;
 *    cap string del radar abans de la porta). No és a la llista.
 *  · slot 12 LICITACIONS — secció aparcada per al llançament (decisió de Bea); el KPI
 *    mesurable del bloc D és residus (`kg_hab_any`), que sí que hi és.
 *
 * `kind`:
 *  · 'metric'  → targeta estàndard: valor de `row.values[key]`, procedència de
 *                `metrics[key]` (font O fórmula, C6 §8.1), rang de `govern[key]` si n'hi ha.
 *  · 'etca'    → presència oficial (ETCA d'Idescat) o «sense dada oficial»; sense rang.
 *  · 'atur'    → atur registrat (SEPE): sèrie mensual encara NO servida al web → targeta
 *                honesta «pendent», amb la seva font; sense rang. (Serrell: cal l'export web
 *                de `mart_pols_mensual`.)
 *  · 'serveis' → comerç/serveis + restauració (dos comptes OSM); sense rang (no oficial).
 */

/**
 * @typedef {Object} GovKpi
 * @property {'metric'|'etca'|'atur'|'serveis'} kind
 * @property {'A'|'B'|'C'|'D'} group  Bloc de la gorra §3.
 * @property {string} [key]           Clau de mètrica (kind 'metric').
 * @property {string} [deltaKey]      Mètrica secundària (p. ex. la variació de la finestra).
 * @property {boolean} [noRank]       El KPI no porta rang per doctrina (C6 §3).
 * @property {boolean} [bea]          Copy amb VOT NARRATIU DE BEA PENDENT (gorra §3.3).
 */

/** @type {GovKpi[]} */
export const GOVERN_KPIS = [
	// A · Qui hi ha (i qui hi haurà)
	{ kind: 'metric', key: 'index_envelliment', group: 'A' },
	{ kind: 'metric', key: 'poblacio', group: 'A' },
	{ kind: 'metric', key: 'pct_nacionalitat_estrangera', group: 'A', deltaKey: 'delta_pct_estrangera_finestra', noRank: true, bea: true },
	{ kind: 'etca', group: 'A', noRank: true },
	// B · Les cases (el nus)
	{ kind: 'metric', key: 'pct_noprincipal', group: 'B' },
	{ kind: 'metric', key: 'rtc_per_1000hab', group: 'B' },
	{ kind: 'metric', key: 'kwh_hab', group: 'B' },
	// C · El pols i l'economia
	{ kind: 'atur', group: 'C', noRank: true },
	{ kind: 'metric', key: 'renda_neta_persona', group: 'C' },
	{ kind: 'serveis', group: 'C', noRank: true },
	// D · Els diners i el que gastem (radar aparcat rere porta; licitacions aparcada)
	{ kind: 'metric', key: 'kg_hab_any', group: 'D' }
];

/**
 * Les 7 mètriques que el mart_govern (D4) rankeja. El front NO rankeja: si una clau NO és
 * aquí, el seu KPI no mostra rang (per doctrina, no per manca tècnica).
 * @type {string[]}
 */
export const GOVERN_RANK_KEYS = [
	'index_envelliment', 'poblacio', 'pct_noprincipal',
	'rtc_per_1000hab', 'kwh_hab', 'renda_neta_persona', 'kg_hab_any'
];

/**
 * Línia de procedència d'una mètrica (REGLA DE FERRO de Bea, C6 §8.1). Res es codifica a la
 * UI: font, data i fórmula surten del contracte (`metrics[key]`).
 *  · fórmula ≠ 'directe'  → INFERIDA: es mostra la FÓRMULA + la font de les entrades (muted).
 *  · 'directe' / absent   → MESURADA: es mostra la FONT · data.
 * @param {{source?:string, date?:string, formula?:string}|undefined} def
 * @returns {{ formula: string|undefined, src: string }}
 */
export function provenanceLine(def) {
	const f = def && def.formula;
	const isFormula = !!f && f !== 'directe';
	const src = def ? (def.date ? `${def.source} · ${def.date}` : (def.source ?? '')) : '';
	return { formula: isFormula ? f : undefined, src };
}
