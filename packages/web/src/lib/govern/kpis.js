/**
 * Els KPIs del TAULER DE DADES, en ORDRE FIX (gorra §3 / C6 §1.3, §7).
 *
 * V3 (redisseny aprovat per Bea 2026-07-29, «tot ok. HUT sí» —
 * `docs/ajuntaments/redisseny-tauler-v3.md` és el document vinculant): el tauler es llegeix
 * com la seqüència «Quants som? → Com canviem? → On vivim? → De què vivim? → Quin rastre
 * deixem?». Tres canvis estructurals respecte del tauler v2:
 *
 *  1. CAPÇALERA DE PRESÈNCIA (fora d'aquesta llista, vegeu PRESENCIA_KEY): padró + ETCA
 *     JUNTS a dalt de tot — són la mateixa pregunta («quanta gent hi ha?») amb dues
 *     respostes oficials. La targeta gran del padró i la targeta ETCA del grup A
 *     desapareixen, absorbides per la capçalera; «Els números clau» s'elimina sencera
 *     (duplicava 4 xifres del tauler).
 *  2. BARRES APILADES: les 4 targetes de franges d'edat i les 4 de lloc de naixement es
 *     fonen en DUES targetes (`kind: 'edats'` i `kind: 'naixement'`) amb barra apilada
 *     horitzontal. LES 8 XIFRES SEGUEIXEN AL DOM (recompte per franja + % per franja a les
 *     edats; recompte per origen + % nascuts a l'estranger al naixement): la barra diu la
 *     forma, els números segueixen sent citables. `verify-govern.mjs` ho vigila.
 *  3. REAGRUPACIÓ I RÈTOLS NOUS: «La gent» (A) · «Les cases» (B) · «Feina i renda» (C) ·
 *     «El dia a dia» (D, que ara inclou comerç/serveis — és vida diària, no macroeconomia).
 *     L'índex d'envelliment DEIXA de ser la primera targeta del tauler: va DARRERE de les
 *     edats de què deriva, amb la seva frase plana («X de 65+ per cada 100 menors de 15»).
 *
 * D8 · E1 (esmena de Bea): una sola vista, sense commutador — aquest tauler ÉS la fitxa.
 *
 * ⚠️ Font ÚNICA de l'ordre i la composició del tauler: la comparteixen el component
 * (`municipi/[slug]/+page.svelte`) i el verificador offline (`scripts/verify-govern.mjs`)
 * perquè no derivin. JS pur (sense tipus, sense Svelte, sense paraglide) perquè Node el
 * pugui importar tal qual al test.
 *
 * Política editorial (C6 §7): l'ordre NO es reordena per enterrar cap indicador. Absències
 * DECLARADES: slot RADAR (porta del §4 de l'spec no superada) i slot LICITACIONS (aparcada).
 *
 * `kind`:
 *  · 'metric'    → targeta estàndard: valor de `row.values[key]`, procedència de
 *                  `metrics[key]` (font O fórmula, C6 §8.1), rang de `govern[key]` si n'hi ha.
 *  · 'edats'     → UNA targeta amb barra apilada de les 4 franges (EDATS_BANDS): recompte i %
 *                  per franja. Les 3 franges mesurades amb la seva font; la 15-64 amb la seva
 *                  fórmula de resta (C6 §8.1 no s'estova) i el seu caveat del contracte
 *                  accessible a la targeta.
 *  · 'naixement' → UNA targeta amb barra apilada del lloc de naixement (NAIX_BAR_KEYS:
 *                  Catalunya · resta d'Espanya · estranger) + el % nascuts a l'estranger
 *                  (`pct_nascuda_estranger`, amb pendingRank com fins ara). La nota «foto,
 *                  no sèrie» hi va UNA vegada. V3-CONTRACTE: les tres xifres de naixement
 *                  són `formula: directe` → es pinten com a MESURADES amb font, sense ƒ
 *                  (f69/f72/f73 eren localitzadors de camp, no fórmules).
 *  · 'atur'      → atur registrat (SEPE): darrer mes + sèrie de 25 mesos + les DUES
 *                  comparacions, servits pel shard `tauler/<ine5>.json` (D7 · P-947).
 *  · 'serveis'   → comerç/serveis + restauració (dos comptes OSM); sense rang (no oficial).
 *
 * (El `kind: 'etca'` ja no existeix: l'ETCA viu a la capçalera de presència amb el padró.)
 */

/**
 * @typedef {Object} GovKpi
 * @property {'metric'|'edats'|'naixement'|'atur'|'serveis'} kind
 * @property {'A'|'B'|'C'|'D'} group  Bloc del tauler v3 (§3 del redisseny).
 * @property {string} [key]           Clau de mètrica (kind 'metric').
 * @property {string} [trendKey]      Clau de `tauler.tendencia` d'aquest KPI, si en té. Per
 *                                    defecte és `key`; s'explicita quan divergeixen.
 * @property {boolean} [noRank]       El KPI no porta rang per doctrina (C6 §3).
 * @property {boolean} [pendingRank]  El KPI HAURIA de portar rang però el mart encara no el
 *                                    serveix → targeta amb el motiu REAL escrit (mai un rang
 *                                    calculat al front: C6 §4 és frontera dura).
 * @property {boolean} [hut]          V3 (vot de Bea: HUT sí): la targeta de turisme diu també
 *                                    el recompte cru — «N establiments, M són HUT» — de
 *                                    `row.values.rtc_total` / `row.values.rtc_hut` (ja
 *                                    servits), amb la font única del registre (C6 §8.1).
 * @property {string} [note]          Clau i18n (ca+es) d'un LÍMIT de lectura que la targeta ha de
 *                                    declarar pel seu compte, perquè no es dedueix de la dada:
 *                                    p. ex. que d'aquesta xifra en tenim la foto i no la sèrie, o
 *                                    que la sèrie que l'acompanya mesura una altra cosa. El text
 *                                    viu a `messages/{ca,es}.json` i el resol el component.
 */

/**
 * CAPÇALERA DE PRESÈNCIA (v3 §3): la clau del padró, que es pinta A DALT del tauler al costat
 * de l'ETCA — amb la seva font, el seu rang comarcal, la seva tendència (el motiu honest de no
 * tenir-ne) i la seva frescor, com qualsevol altra xifra (C6 §8.1 val també a la capçalera).
 */
export const PRESENCIA_KEY = 'poblacio';

/**
 * Les 4 franges de la barra d'edats, en ordre. `band` és el rètol curt de la llegenda
 * (numèric, idèntic ca/es); el rètol llarg i la procedència surten del contracte.
 * La partició és exacta: pob_0_14 + pob_15_64 + pob_65_84 + pob_85_mes = poblacio
 * (verificat als 947 per D7; `verify-govern.mjs` ho re-verifica sobre el dataset servit).
 */
export const EDATS_BANDS = [
	{ key: 'pob_0_14', band: '0-14' },
	{ key: 'pob_15_64', band: '15-64' },
	{ key: 'pob_65_84', band: '65-84' },
	{ key: 'pob_85_mes', band: '85+' }
];

/**
 * Els 3 segments de la barra «D'on venim», en ordre. El rètol de cada segment és i18n
 * (`gov_naix_cat` / `gov_naix_resta` / `gov_naix_estranger`). També partició exacta del padró.
 */
export const NAIX_BAR_KEYS = [
	'poblacio_nascuda_catalunya',
	'poblacio_nascuda_resta_espanya',
	'poblacio_nascuda_estranger'
];

/**
 * E13 · CAVEAT DE MICROMUNICIPI (doctrina al capçal de `semantic/metrics.yml`; decisió de Bea
 * 2026-07-20: caveat, NO emmascarar). Quan `row.values.poblacio < E13_LLINDAR`, aquestes
 * targetes porten una nota visible: el denominador és minúscul i una sola persona o casa mou
 * el número. La llista i el llindar són DOCTRINA (contracte), no estil: si canvien allà,
 * canvien aquí i `verify-govern.mjs` cau si divergeixen del que el tauler pinta.
 * (El text de la nota — `gov_e13_micro` — està PENDENT DEL VOT de Bea: el concepte està
 * votat; la frase exacta, encara no.)
 */
export const E13_KEYS = ['kg_hab_any', 'kwh_hab', 'vidre_hab', 'rtc_per_1000hab', 'index_envelliment'];
export const E13_LLINDAR = 250;

/** @type {GovKpi[]} */
export const GOVERN_KPIS = [
	// A · La gent — les edats primer (la forma de la piràmide), l'índex DARRERE (en deriva),
	// després les dues lectures d'origen: d'on venim (naixement, foto) i nacionalitat (l'única
	// amb sèrie). La nota de grup («les particions sumen exactament el padró») la pinta el
	// component UNA vegada al peu del grup, no quatre cops per targeta.
	{ kind: 'edats', group: 'A' },
	// V3 §11: frase plana a la targeta («X persones de 65 o més per cada 100 menors de 15»);
	// la fórmula del contracte segueix sent la línia de procedència (C6 §8.1).
	{ kind: 'metric', key: 'index_envelliment', group: 'A' },
	// D11 · E11 · el lloc de naixement és l'altra PARTICIÓ del padró. «Nascuts fora de
	// Catalunya» (suma) segueix sense pintar-se: no és una mètrica servida i sumar-la aquí
	// seria fabricar una xifra sense procedència (C6 §8.1).
	// El % de la targeta de naixement (`pct_nascuda_estranger`) SEGUEIX sense rang al mart: el seu
	// pendingRank es queda. El que E9 demanava (`pct_nacionalitat_estrangera`) ja el té des de #294.
	{ kind: 'naixement', group: 'A', pendingRank: true, note: 'gov_naix_foto' },
	// D11: aquesta targeta és l'ÚNICA del bloc amb evolució, i la seva `note` diu de què és la
	// sèrie (nacionalitat = passaport, no biografia). Sense això, el +5,61 es llegiria com si
	// fos el creixement dels nascuts a l'estranger, que és una altra gent.
	{
		kind: 'metric',
		key: 'pct_nacionalitat_estrangera',
		group: 'A',
		note: 'gov_nac_serie_es_nacionalitat'
	},
	// B · Les cases
	{ kind: 'metric', key: 'pct_noprincipal', group: 'B' },
	// V3 §6 (vot de Bea: HUT sí): el rati + el cru («N establiments, M són HUT»). El rati sol
	// amaga que a molts pobles «turisme reglat» vol dir pisos turístics.
	{ kind: 'metric', key: 'rtc_per_1000hab', group: 'B', hut: true },
	// C · Feina i renda
	// E4 · l'atur el serveix D7 (darrer mes + 25 mesos + les dues comparacions). Sense rang
	// perquè `mart_govern` no el rankeja — no per manca de dada.
	{ kind: 'atur', group: 'C', noRank: true, trendKey: 'atur_registrat' },
	{ kind: 'metric', key: 'renda_neta_persona', group: 'C' },
	// D · El dia a dia — comerç/serveis (ve del grup C: és vida diària, no macroeconomia) +
	// els tres rastres físics junts (E2 de Bea), cadascun amb la seva font (C6 §8.1). El vidre
	// no el rankeja el mart (no és a les 7): surt sense rang, que és la lectura honesta.
	{ kind: 'serveis', group: 'D', noRank: true },
	{ kind: 'metric', key: 'kg_hab_any', group: 'D' },
	{ kind: 'metric', key: 'kwh_hab', group: 'D' },
	{ kind: 'metric', key: 'vidre_hab', group: 'D' }
];

/**
 * Les 7 mètriques que el mart_govern (D4) rankeja. El front NO rankeja: si una clau NO és
 * aquí, el seu KPI no mostra rang (per doctrina, no per manca tècnica).
 * (`poblacio` es pinta a la capçalera de presència, amb el seu rang igualment.)
 * @type {string[]}
 */
export const GOVERN_RANK_KEYS = [
	'index_envelliment', 'poblacio', 'pct_noprincipal',
	'rtc_per_1000hab', 'kwh_hab', 'renda_neta_persona', 'kg_hab_any',
	// W3 (esmena de Bea 2026-07-31, #294): el mart ja les rankeja. `pct_nascuda_estranger`
	// NO hi és a propòsit — aquella segueix sense rang i la seva targeta ho continua dient.
	'vidre_hab', 'pct_nacionalitat_estrangera'
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
