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
 * B3 · PER QUÈ EL DENOMINADOR DEL RANG NO ÉS TOTA LA COMARCA (esmena de Bea, 2026-07-31).
 *
 * El rang es publica sobre `n_amb_dada` —els municipis de la comarca que TENEN la xifra— i
 * això, sense explicar, sembla arbitrari: «6 de 27» al costat de «8 de 31» a la mateixa
 * pantalla. La targeta ho ha de dir sense que calgui saber res del nostre pipeline.
 *
 * Aquest mapa declara, per mètrica, el MOTIU de l'absència. No és estil: cada entrada és una
 * afirmació verificable sobre la dada, i `verify-govern.mjs` la contrasta amb els 947 abans de
 * deixar-la publicar. Per això n'hi ha TRES i no una de sola: els motius són diferents i
 * atribuir-los malament seria mentir amb bona intenció.
 *
 *  · 'gov_denom_minn'   → LLINDAR NOSTRE (`demografia_min_n` = 50, `mart_demografia.sql`):
 *    per sota de 50 habitants no publiquem el percentatge d'origen perquè cada persona el mou
 *    2-4 punts i frega la identificació d'individus. Els RECOMPTES sí que es publiquen. És una
 *    decisió nostra, no un forat: als 9 municipis afectats de Catalunya, cap té 50 hab o més,
 *    i cap municipi de 50 hab o més es queda sense la xifra.
 *  · 'gov_denom_font'   → LÍMIT DE LA FONT: l'INE no publica renda per a certs municipis
 *    (ADRH). No és el nostre llindar —hi ha municipis de 38 hab amb renda i de 110 sense— i
 *    dir-ho com si ho fos ens atribuiria una prudència que no és nostra.
 *  · 'gov_denom_ratio'  → LA DIVISIÓ NO ES POT FER: l'índex d'envelliment és 65+/0-14, i a la
 *    Febró (Baix Camp) no hi viu ningú de 0 a 14 anys. No és secret ni absència de dada: és
 *    que el quocient no existeix.
 *
 * Una mètrica que NO és en aquest mapa i tingui forats pinta el motiu NEUTRE («no en tenim la
 * xifra»): quedar-nos curts abans que inventar-ne la causa.
 * (Els textos exactes són PENDENTS DEL VOT de Bea; el mecanisme, no.)
 * @type {Record<string, string>}
 */
export const GOVERN_DENOM_REASON = {
	pct_nacionalitat_estrangera: 'gov_denom_minn',
	pct_nascuda_estranger: 'gov_denom_minn',
	renda_neta_persona: 'gov_denom_font',
	index_envelliment: 'gov_denom_ratio'
};

/** Motiu per defecte quan no en sabem la causa (mai una explicació inventada). */
export const GOVERN_DENOM_REASON_DEFAULT = 'gov_denom_nd';

/**
 * El llindar del motiu 'gov_denom_minn', DECLARAT aquí i no escrit al copy: és la var
 * `demografia_min_n` de `packages/transform/dbt_project.yml`, i si algú la mou allà,
 * `verify-govern.mjs` cau abans que la pantalla expliqui un llindar que ja no és el nostre.
 */
export const GOVERN_DENOM_MIN_N = 50;

/**
 * R-PINTA · LES DUES REFERÈNCIES DE CADA TARGETA AMB RANG (vot de Bea 2026-07-31: «farem B+D»).
 *
 * La doctrina vinculant és al capçal de `semantic/metrics.yml`, bloc «QUINES ES PINTEN». En
 * curt: el mart serveix TRES famílies de referència i la fitxa en pinta DUES —
 *   1. `ponderada_catalunya` — l'ancoratge oficial, igual a totes les targetes: és
 *      total/habitants, l'equivalent exacte de com publiquen la xifra l'ARC, l'ICAEN i
 *      l'Idescat, i el número que un lector entén per «la mitjana».
 *   2. `mediana_comarca` — els iguals, i el MATEIX PERÍMETRE que el rang (`n_amb_dada`), que
 *      és la condició que fa que «17 de 31» i la mediana no comptin conjunts diferents.
 * — i la tercera (`mediana_franja`, estratificada per mida) se serveix però NO es pinta: amb la
 * variància AJUSTADA, la comarca explica millor que la franja a 8 de les 9 mètriques amb rang.
 *
 * El contrast entre les dues és INFORMACIÓ, no soroll: a la Pobla de Lillet el vidre fa 48,6
 * amb Catalunya a 22,9 i la mediana del Berguedà a 49,8 → «normal aquí, el doble que a
 * Catalunya». Cap de les dues xifres tota sola dona aquesta lectura.
 *
 * ⚠️ EL DENOMINADOR NO ÉS EL MATEIX PER A LES DUES (C6 §8.1, i és on el brief es queda curt):
 * una MEDIANA es diu «sobre N MUNICIPIS»; una PONDERADA, «sobre N unitats del seu pes» — i el
 * pes NO sempre són habitants. `pes_ponderada` ho declara cel·la a cel·la, i les 9 mètriques
 * amb rang fan servir CINC pesos diferents: tres són gent (`poblacio`, `poblacio_residus`,
 * `poblacio_kwh`), però `pct_noprincipal` es pondera per HABITATGES (`hab_total`) i
 * `index_envelliment` per MENORS DE 15 (`pob_0_14`). Escriure «sobre 3.915.127 habitants» sota
 * el % d'habitatges no principals seria una procedència FALSA, que és exactament el que la
 * regla de ferro existeix per impedir.
 */

/**
 * Nom del denominador d'una PONDERADA, per pes. La clau és el `pes_ponderada` que serveix el
 * mart; el valor, la clau i18n (ca+es) que el nomena. Un pes que NO sigui en aquest mapa no
 * es pot nomenar → la seva referència NO es pinta (mai un denominador inventat) i
 * `verify-govern.mjs` cau, perquè un pes nou de Sondeig ha d'arribar amb el seu nom, no en
 * silenci.
 * @type {Record<string, string>}
 */
export const GOVERN_PES_DENOM = {
	poblacio: 'gov_ref_denom_hab',
	poblacio_residus: 'gov_ref_denom_hab',
	poblacio_kwh: 'gov_ref_denom_hab',
	hab_total: 'gov_ref_denom_habitatges',
	pob_0_14: 'gov_ref_denom_menors15'
};

/** Clau i18n del denominador d'una MEDIANA: sempre municipis, mai habitants. */
export const GOVERN_REF_DENOM_MUNIS = 'gov_ref_denom_munis';

/**
 * @typedef {Object} GovernRef
 * @property {'comarca'|'catalunya'} id  Quina de les dues (clau d'iteració estable).
 * @property {'mediana'|'ponderada'} tipus  Família — decideix quin denominador li toca.
 * @property {string} labelKey   Clau i18n del rètol («mediana comarcal» / «mitjana de Catalunya»).
 * @property {number} value      La xifra, TAL COM LA SERVEIX EL MART (aquí no es calcula res).
 * @property {string} denomKey   Clau i18n del denominador, amb la seva unitat NOMENADA.
 * @property {number} denom      El denominador.
 */

/**
 * Les referències PINTABLES d'una cel·la, en ordre de pintura. Funció pura i compartida entre
 * el component i `verify-govern.mjs` (mateix patró que la resta d'aquest fitxer) perquè la
 * guarda pugui exercir-la sobre els 947 en comptes d'endevinar-ho del marcatge.
 *
 * No fa CAP càlcul (C6 §4): tria, ordena i etiqueta el que el mart ja serveix. Una referència
 * sense el seu denominador —o amb un pes que no sabem nomenar— NO surt: «no la tenim» és una
 * resposta vàlida i preferible a una procedència inventada.
 *
 * Ordre i per què: la COMARCAL primer (comparteix perímetre amb el «k de n» que hi ha just a
 * sobre: el lector acaba de llegir «de 31» i la mediana d'aquests mateixos 31 és la lectura
 * següent), i la CATALANA a sota com a ancoratge estable, igual a totes les targetes.
 *
 * @param {any} cell Cel·la de `GovernCell` servida pel mart.
 * @returns {GovernRef[]}
 */
export function governReferences(cell) {
	if (!cell) return [];
	/** @type {GovernRef[]} */
	const refs = [];
	// 1 · MEDIANA DE LA COMARCA — el denominador és `n_amb_dada`, el MATEIX del rang.
	if (
		typeof cell.mediana_comarca === 'number' &&
		Number.isInteger(cell.n_amb_dada) &&
		cell.n_amb_dada > 0
	) {
		refs.push({
			id: 'comarca',
			tipus: 'mediana',
			labelKey: 'gov_ref_comarca',
			value: cell.mediana_comarca,
			denomKey: GOVERN_REF_DENOM_MUNIS,
			denom: cell.n_amb_dada
		});
	}
	// 2 · PONDERADA DE CATALUNYA — NULL a `poblacio` (seria la seva pròpia mida): allà la
	//     targeta es queda amb la comarcal i prou, sense cap buit ni cap «n. d.» decoratiu.
	if (typeof cell.ponderada_catalunya === 'number') {
		const denomKey = GOVERN_PES_DENOM[cell.pes_ponderada];
		if (denomKey && typeof cell.hab_ponderada_catalunya === 'number' && cell.hab_ponderada_catalunya > 0) {
			refs.push({
				id: 'catalunya',
				tipus: 'ponderada',
				labelKey: 'gov_ref_catalunya',
				value: cell.ponderada_catalunya,
				denomKey,
				denom: cell.hab_ponderada_catalunya
			});
		}
	}
	return refs;
}

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
