/**
 * Els KPIs del TAULER DE DADES, en ORDRE FIX (gorra §3 / C6 §1.3, §7).
 *
 * D8 · E1 (esmena de Bea, `docs/ajuntaments/tauler-v2-esmenes-bea.md`): ja NO hi ha dues
 * vistes. El commutador Veïnal|Govern desapareix i aquest tauler —els KPIs amb rang comarcal,
 * ordre fix i política editorial— passa a ser LA fitxa, sense `?vista=govern`. El nom visible
 * és «Tauler de dades». La paritat de xifres deixa de ser un risc: no hi ha una segona vista
 * amb què discrepar.
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
 *  · 'atur'    → atur registrat (SEPE): darrer mes + sèrie de 25 mesos + les DUES comparacions,
 *                servits per `tauler.bergueda.json` (D7). Sense rang (el mart no el rankeja).
 *  · 'serveis' → comerç/serveis + restauració (dos comptes OSM); sense rang (no oficial).
 *
 * D9 · E12 (Bea): les FRANGES D'EDAT entren al bloc A com a targetes de ple dret. No hi entra
 * `pob_65_mes` a propòsit: és exactament `pob_65_84 + pob_85_mes`, que ja són al mateix bloc, i
 * pintar-la seria comptar la mateixa gent dues vegades a la mateixa pantalla. Viu al catàleg i és
 * el numerador de l'índex d'envelliment, que sí que hi és amb la seva fórmula.
 *
 * D11 · E11 (Bea): el LLOC DE NAIXEMENT entra al bloc A. D9 el va deixar fora per una premissa
 * falsa —«el mart només té nacionalitat»—: les quatre mètriques de la dimensió `origen` són
 * vives, `status: public` i arriben al web des de D7. Bea demana «nascuts fora de Catalunya i
 * nascuts a l'estranger», que és BIOGRAFIA (lloc de naixement), no PASSAPORT (nacionalitat):
 * a la Pobla, 134 nascuts a l'estranger contra un 9,58% de nacionalitat estrangera (~106
 * persones). Qui es naturalitza surt d'un conjunt i es queda a l'altre; el contracte mateix
 * prohibeix confondre'ls.
 *
 * El límit honest va escrit a la targeta (`note`): del lloc de naixement en tenim la FOTO, no la
 * sèrie — `mart_tendencia` no en porta cap entrada—, i l'única evolució que existeix (2021→2025)
 * és la de NACIONALITAT, que per això la declara la seva pròpia targeta.
 */

/**
 * @typedef {Object} GovKpi
 * @property {'metric'|'etca'|'atur'|'serveis'} kind
 * @property {'A'|'B'|'C'|'D'} group  Bloc de la gorra §3.
 * @property {string} [key]           Clau de mètrica (kind 'metric').
 * @property {string} [trendKey]      Clau de `tauler.tendencia` d'aquest KPI, si en té. Per
 *                                    defecte és `key`; s'explicita quan divergeixen.
 * @property {boolean} [noRank]       El KPI no porta rang per doctrina (C6 §3).
 * @property {boolean} [pendingRank]  El KPI HAURIA de portar rang però el mart encara no el
 *                                    serveix → targeta amb el motiu REAL escrit (mai un rang
 *                                    calculat al front: C6 §4 és frontera dura).
 * @property {string} [note]          Clau i18n (ca+es) d'un LÍMIT de lectura que la targeta ha de
 *                                    declarar pel seu compte, perquè no es dedueix de la dada:
 *                                    p. ex. que d'aquesta xifra en tenim la foto i no la sèrie, o
 *                                    que la sèrie que l'acompanya mesura una altra cosa. El text
 *                                    viu a `messages/{ca,es}.json` i el resol el component.
 */

/** @type {GovKpi[]} */
export const GOVERN_KPIS = [
	// A · Qui hi ha (i qui hi haurà)
	{ kind: 'metric', key: 'index_envelliment', group: 'A' },
	{ kind: 'metric', key: 'poblacio', group: 'A' },
	// E12 · les franges d'edat, just darrere de la població de la qual són la partició (la suma
	// de les quatre = `poblacio`, verificat als 947 per D7). La 15-64 és DERIVADA per resta: la
	// seva línia de procedència és la fórmula, no una font (C6 §8.1), i ho és sense excepció.
	{ kind: 'metric', key: 'pob_0_14', group: 'A' },
	{ kind: 'metric', key: 'pob_15_64', group: 'A' },
	{ kind: 'metric', key: 'pob_65_84', group: 'A' },
	{ kind: 'metric', key: 'pob_85_mes', group: 'A' },
	// D11 · E11 · el LLOC DE NAIXEMENT, just darrere de les franges d'edat perquè és l'altra
	// PARTICIÓ de la mateixa població: nascuts a Catalunya + resta d'Espanya + estranger =
	// `poblacio`, exacte als 947 municipis (verificat, no suposat). Van les tres xifres perquè
	// «nascuts fora de Catalunya» —el que Bea demana literalment— NO és una mètrica servida, i
	// sumar-les aquí seria fabricar una xifra sense procedència (C6 §8.1). Handoff a Sondeig si
	// es vol la xifra agregada com a mètrica pròpia, amb la seva fórmula al contracte.
	// Sense marca de rang, igual que les franges: rankejar un component d'una partició és
	// rankejar la mida del poble una altra vegada. El que sí que demana rang és el %.
	{ kind: 'metric', key: 'poblacio_nascuda_catalunya', group: 'A', note: 'gov_naix_foto' },
	{ kind: 'metric', key: 'poblacio_nascuda_resta_espanya', group: 'A', note: 'gov_naix_foto' },
	{ kind: 'metric', key: 'poblacio_nascuda_estranger', group: 'A', note: 'gov_naix_foto' },
	{ kind: 'metric', key: 'pct_nascuda_estranger', group: 'A', pendingRank: true, note: 'gov_naix_foto' },
	// E9 (Bea): el vot narratiu ja HI ÉS —el rang s'ha de mostrar—, però `mart_govern` NO
	// rankeja aquesta mètrica (viu a `mart_demografia`) i `export_govern_web.RANK_METRICS` en
	// té 7, sense aquesta. El front NO se'l pot inventar (C6 §4), així que la targeta declara
	// el motiu real. Handoff a Sondeig: afegir-la al mart i a RANK_METRICS → llavors treure
	// `pendingRank` i afegir-la a GOVERN_RANK_KEYS (segona passada de Mirador).
	// D9: la variació de la finestra ja NO es pinta des de `delta_pct_estrangera_finestra` amb el
	// període escrit al copy («2021→»): ara ve de `tauler.tendencia`, que porta els seus DOS
	// períodes a la dada. Mateixa xifra (+5,61 a la Pobla), però amb el període dit per la font.
	// D11: aquesta targeta és l'ÚNICA del bloc amb evolució, i la seva `note` diu de què és la
	// sèrie. Sense això, un lector que ve de les quatre targetes de dalt llegiria el +5,61 com si
	// fos el creixement dels nascuts a l'estranger, que és una altra gent.
	{
		kind: 'metric',
		key: 'pct_nacionalitat_estrangera',
		group: 'A',
		pendingRank: true,
		note: 'gov_nac_serie_es_nacionalitat'
	},
	{ kind: 'etca', group: 'A', noRank: true },
	// B · Les cases (el nus)
	{ kind: 'metric', key: 'pct_noprincipal', group: 'B' },
	{ kind: 'metric', key: 'rtc_per_1000hab', group: 'B' },
	// C · El pols i l'economia
	// E4 · l'atur ja NO és una targeta «pendent»: D7 el serveix (darrer mes + 25 mesos + les dues
	// comparacions). Segueix sense rang perquè `mart_govern` no el rankeja — no per manca de dada.
	{ kind: 'atur', group: 'C', noRank: true, trendKey: 'atur_registrat' },
	{ kind: 'metric', key: 'renda_neta_persona', group: 'C' },
	{ kind: 'serveis', group: 'C', noRank: true },
	// D · El pols de la vida diària (E2 de Bea): els tres rastres físics del dia a dia JUNTS
	// —residus, elèctric domèstic i vidre—, cadascun amb la seva font (C6 §8.1). El vidre no
	// el rankeja el mart (no és a les 7): surt sense rang, que és la lectura honesta.
	// (Radar aparcat rere porta; licitacions aparcada.)
	{ kind: 'metric', key: 'kg_hab_any', group: 'D' },
	{ kind: 'metric', key: 'kwh_hab', group: 'D' },
	{ kind: 'metric', key: 'vidre_hab', group: 'D' }
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
