#!/usr/bin/env node
/**
 * verify-govern.mjs — verificador OFFLINE del TAULER DE DADES (D5 → D8 → V3 · C6 §10.7).
 *
 * V3 (redisseny aprovat per Bea 2026-07-29): capçalera de presència (padró+ETCA junts),
 * edats i lloc de naixement com a BARRES APILADES, HUT al turisme, «Els números clau» i la
 * targeta gran del padró eliminades, «sense procés automàtic» fora de les targetes (cap a
 * /metodologia). El verificador s'adapta A LA NOVA DISPOSICIÓ sense afluixar: les 8 xifres
 * de les barres segueixen exigides (via dada + cablatge), cap targeta sense font O fórmula,
 * cap fletxa sense període, el «<5» com a interval.
 *
 * Guarda la REGLA DE FERRO de Bea (C6 §8.1): CAP targeta de KPI del tauler pot quedar
 * sense línia de procedència (font O fórmula). A més comprova que el rang «k de n» es
 * LLEGEIX del mart (govern.json) i mai es fabrica al front, i que les xifres del rang
 * coincideixen amb les del dataset (paritat, C6 §10.1).
 *
 * Font única de l'ordre/composició del tauler: `src/lib/govern/kpis.js`, IMPORTADA aquí
 * (no es duplica → no deriva). Igual amb la regla d'article i de slug (`contract/slug-core.js`),
 * que aquí s'exerceix sobre els 947 noms reals. Offline, sense xarxa. Apte per a CI (data-job).
 *
 * W1/W5 (esmenes de Bea, 2026-07-31): dues seccions noves al final guarden que la NAVEGACIÓ
 * arribi als 947 (selector construït del catàleg, cap col·lisió de slug, la clau d'ordenació no
 * mou cap URL) i que la porta de la home ni torni a morir ni torni a portar xifres escrites a mà.
 *
 *   node scripts/verify-govern.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
	GOVERN_KPIS,
	GOVERN_RANK_KEYS,
	PRESENCIA_KEY,
	EDATS_BANDS,
	NAIX_BAR_KEYS,
	E13_KEYS,
	E13_LLINDAR,
	GOVERN_DENOM_REASON,
	GOVERN_DENOM_REASON_DEFAULT,
	GOVERN_DENOM_MIN_N,
	GOVERN_PES_DENOM,
	GOVERN_REF_DENOM_MUNIS,
	governReferences,
	provenanceLine
} from '../src/lib/govern/kpis.js';
// W1 · la regla d'article (slug, forma corrent, clau d'ordenació) també és font ÚNICA i
// importada: la guarda de col·lisió dels 947 ha d'exercir el `toSlug` REAL, no una còpia.
import { toSlug, nomCanonic, nomIndex } from '../src/lib/contract/slug-core.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(__dirname, '../../..');
const WEB = resolve(__dirname, '..');

const read = (p) => JSON.parse(readFileSync(p, 'utf8'));
const POBLA = '08166';
const dataset = read(resolve(REPO, 'data/web/municipis.bergueda.json'));
// P-947: el front ja NO consumeix els monòlits del Berguedà. Es verifica el que la fitxa LLEGEIX
// ARA: el rang comarcal dels 947 (`govern.catalunya.json`, {ine5: GovernEntry}) i el tauler pel
// SHARD del municipi (`tauler/<ine5>.json` = el `TaulerEntry` directe) + el sidecar compartit
// (`tauler/_meta.json`, on el bloc consumit és `_meta`). Es reconstrueix aquí la forma
// `{_meta, municipis}` que la resta del verificador espera, a partir del que se serveix — sense
// tornar a llegir cap monòlit.
const govern = read(resolve(REPO, 'data/web/govern.catalunya.json'));
const taulerMetaFile = read(resolve(REPO, 'data/web/tauler/_meta.json'));
const tauler = {
	_meta: taulerMetaFile._meta,
	municipis: { [POBLA]: read(resolve(REPO, `data/web/tauler/${POBLA}.json`)) }
};
const ca = read(resolve(WEB, 'messages/ca.json'));
const es = read(resolve(WEB, 'messages/es.json'));
const pageSrc = readFileSync(resolve(WEB, 'src/routes/municipi/[slug]/+page.svelte'), 'utf8');

const metrics = dataset.metrics;
const fails = [];
const ok = (cond, msg) => {
	if (!cond) fails.push(msg);
};

// Missatges i18n de procedència fixos de cada `kind` no-mètric (han d'existir a ca+es).
const I18N_PROV = {
	atur: ['gov_kpi_atur', 'gov_kpi_atur_src', 'gov_atur_absent'],
	serveis: ['gov_kpi_serveis', 'gov_kpi_serveis_a', 'gov_kpi_serveis_b'],
	edats: ['gov_kpi_edats', 'gov_edats_caveat_sum'],
	naixement: ['gov_kpi_naixement', 'gov_naix_cat', 'gov_naix_resta', 'gov_naix_estranger']
};

const EDATS_KEYS = EDATS_BANDS.map((b) => b.key);

// 1 · CADA KPI del tauler té una línia de procedència (font O fórmula) — també els que viuen
//     dins una barra apilada: fondre 8 targetes en 2 no relaxa C6 §8.1 per a cap de les 8 xifres.
for (const kpi of GOVERN_KPIS) {
	if (kpi.kind === 'metric') {
		const def = metrics[kpi.key];
		ok(!!def, `KPI '${kpi.key}': absent del catàleg de mètriques`);
		if (def) {
			const { formula, src } = provenanceLine(def);
			ok(
				!!(formula || src),
				`KPI '${kpi.key}': sense línia de procedència (ni font ni fórmula) — viola C6 §8.1`
			);
		}
	} else if (kpi.kind === 'edats') {
		for (const k of EDATS_KEYS) {
			const def = metrics[k];
			ok(!!def, `barra d'edats: '${k}' absent del catàleg`);
			if (!def) continue;
			const { formula, src } = provenanceLine(def);
			ok(!!(formula || src), `barra d'edats: '${k}' sense font ni fórmula — viola C6 §8.1`);
		}
		// La 15-64 és DERIVADA per resta (C6 §8.1 no s'estova): la seva línia és la FÓRMULA…
		ok(
			!!metrics.pob_15_64?.formula && metrics.pob_15_64.formula !== 'directe',
			`pob_15_64 hauria de ser derivada (fórmula de resta) i el contracte no ho diu`
		);
		// …i el seu caveat del contracte ha de seguir viatjant (la targeta el fa accessible).
		ok(
			!!metrics.pob_15_64?.note?.ca,
			`pob_15_64 sense 'note' al catàleg — el caveat de la franja derivada no seria accessible`
		);
		// Les altres tres són MESURADES (formula: directe): cap ƒ inventada sobre una lectura.
		for (const k of ['pob_0_14', 'pob_65_84', 'pob_85_mes']) {
			ok(
				metrics[k]?.formula === 'directe',
				`'${k}' hauria de ser mesurada (formula: directe), el contracte diu '${metrics[k]?.formula}'`
			);
		}
		for (const k of I18N_PROV.edats) ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
	} else if (kpi.kind === 'naixement') {
		for (const k of [...NAIX_BAR_KEYS, 'pct_nascuda_estranger']) {
			const def = metrics[k];
			ok(!!def, `barra de naixement: '${k}' absent del catàleg`);
			if (!def) continue;
			const { formula, src } = provenanceLine(def);
			ok(!!(formula || src), `barra de naixement: '${k}' sense font ni fórmula — viola C6 §8.1`);
		}
		// V3-CONTRACTE: els tres recomptes de naixement són MESURATS (f69/f72/f73 eren
		// localitzadors, no fórmules) → es pinten amb FONT, sense el símbol ƒ.
		for (const k of NAIX_BAR_KEYS) {
			ok(
				metrics[k]?.formula === 'directe',
				`'${k}' hauria de ser mesurada (V3-CONTRACTE: formula 'directe'), el contracte diu ` +
					`'${metrics[k]?.formula}' — la targeta hi pintaria una ƒ sobre una lectura directa`
			);
		}
		// El % sí que és derivat i la seva ƒ s'ha de pintar.
		ok(
			!!metrics.pct_nascuda_estranger?.formula &&
				metrics.pct_nascuda_estranger.formula !== 'directe',
			`pct_nascuda_estranger hauria de dur la seva fórmula al contracte`
		);
		for (const k of I18N_PROV.naixement) ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
	} else if (kpi.kind === 'serveis') {
		ok(!!metrics['serveis_estab']?.source, `KPI serveis: 'serveis_estab' sense font`);
		for (const k of I18N_PROV.serveis) ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
	} else if (kpi.kind === 'atur') {
		for (const k of I18N_PROV.atur) ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
	}
}

// 1b · V3 · CAPÇALERA DE PRESÈNCIA: el padró juga amb les mateixes regles que una targeta
//      (font, frescor) i l'ETCA hi té el seu text pla (aprovat per Bea) + el motiu on no n'hi ha.
{
	const def = metrics[PRESENCIA_KEY];
	ok(!!def, `capçalera de presència: '${PRESENCIA_KEY}' absent del catàleg`);
	if (def) {
		const { formula, src } = provenanceLine(def);
		ok(!!(formula || src), `capçalera de presència: padró sense font ni fórmula (C6 §8.1)`);
		ok(!!def.frescor, `capçalera de presència: padró sense bloc 'frescor' — no es podria datar`);
	}
	for (const k of [
		'muni_num_padro', 'muni_num_etca', 'muni_sense_dada_oficial', 'gov_pres_padro_u',
		'gov_pres_etca_txt', 'gov_pres_etca_absent', 'gov_pres_etca_src', 'gov_pres_etca_met'
	])
		ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
	ok(pageSrc.includes('gov-pres'), `la capçalera de presència no està cablejada a la fitxa`);
	ok(
		pageSrc.includes('PRESENCIA_KEY'),
		`la fitxa no llegeix la clau de presència del descriptor (PRESENCIA_KEY)`
	);
}

// 2 · Les 7 claus rankejables existeixen al catàleg (i el mart les rankeja).
for (const k of GOVERN_RANK_KEYS) ok(!!metrics[k], `clau rankejable '${k}' absent del catàleg`);

// 3 · El rang es LLEGEIX del mart i quadra amb el dataset (paritat). Cap KPI de rang buit
//     hauria de ser NULL a la Pobla (té dada a tots 7).
const gp = govern[POBLA];
ok(!!gp, `govern.catalunya.json sense la Pobla (${POBLA})`);
if (gp) {
	ok(gp.comarca === 'Berguedà', `la Pobla no surt al Berguedà al govern.catalunya.json`);
	for (const k of GOVERN_RANK_KEYS) {
		const cell = gp.metrics?.[k];
		ok(!!cell, `govern[${POBLA}] sense la mètrica '${k}'`);
		if (cell) {
			ok(Number.isInteger(cell.rang), `rang de '${k}' no és enter (${cell.rang})`);
			ok(Number.isInteger(cell.n_amb_dada) && cell.n_amb_dada > 0, `n_amb_dada de '${k}' invàlid`);
			ok(!!cell.data, `data (vintage) de '${k}' buida`);
			// Paritat: el valor del mart == el valor del dataset (mateixa xifra a totes dues vistes).
			const dv = dataset.municipis[POBLA]?.values?.[k];
			ok(
				dv == null || cell.valor == null || Math.abs(dv - cell.valor) < 1e-6,
				`paritat trencada a '${k}': dataset ${dv} ≠ mart ${cell.valor}`
			);
		}
	}
}

// 4 · i18n del tauler presents a ca+es. V3 hi suma la capçalera de presència, les barres, la
//     frase plana de l'envelliment, el cru HUT, la nota única del grup A i el caveat E13.
const I18N_UI = [
	'gov_board_title', 'gov_board_sub',
	'gov_grp_a', 'gov_grp_b', 'gov_grp_c', 'gov_grp_d', 'gov_rang_label', 'gov_rang_val',
	'gov_rang_cap', 'gov_rang_empat', 'gov_nova_norank',
	// D9 · tendència (E6/E11)
	'gov_tend_sense_serie', 'gov_tend_no_declarada', 'gov_tend_cmp_mes', 'gov_tend_cmp_any',
	'gov_tend_cmp_finestra', 'gov_tend_indeterminat', 'gov_tend_interval',
	'gov_tend_u_persones', 'gov_tend_u_punts',
	// D9 · frescor per targeta (E5; V3 retira el procés de la línia — vegeu I18N_GONE)
	'gov_frescor_mensual', 'gov_frescor_anual', 'gov_frescor_puntual', 'gov_frescor_irregular',
	'gov_frescor_nd', 'gov_frescor_carrega',
	// D9 · atur servit (E4)
	'gov_atur_u', 'gov_atur_masked', 'gov_atur_absent', 'gov_atur_serie_cap', 'gov_atur_serie_alt',
	// V3 · redisseny del tauler
	'gov_grp_a_nota', 'gov_envell_frase', 'gov_e13_micro', 'gov_hut_cru'
];
for (const k of I18N_UI) ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);

// 4b · Claus RETIRADES: no poden quedar òrfenes als catàlegs (higiene d'i18n, D8).
//      V3 en retira sis més: la targeta gran del padró (`muni_hab_padro`), «Els números clau»
//      sencera (`muni_nums_title`/`muni_num_nop`/`muni_num_renda`), la línia llarga d'ETCA
//      (`muni_etca_srcline`, partida en frase plana + enllaç) i el procés de refresc a la
//      targeta (`gov_frescor_sense_proces`/`gov_frescor_amb_proces` — la informació viu ara a
//      /metodologia via `met_fresc_*`; verify-docs vigila que hi sigui de veritat).
const I18N_GONE = [
	'gov_switch_aria', 'gov_view_veinal', 'gov_view_govern', 'gov_kpi_nova_frame', 'gov_bea_pending',
	'gov_kpi_atur_pending', 'gov_nova_delta_label',
	'muni_hab_padro', 'muni_nums_title', 'muni_num_nop', 'muni_num_renda', 'muni_etca_srcline',
	'gov_frescor_sense_proces', 'gov_frescor_amb_proces',
	// W5 · la porta morta de la home i el seu copy («Resta de Catalunya · 947 municipis», que
	// etiquetava el TOTAL com si fos la resta). `home_porta_soon` ja era òrfena abans d'avui:
	// no la pintava ningú des de feia temps i ningú se n'havia adonat.
	'home_porta_proxim', 'home_porta_proxim_sub', 'home_porta_soon'
];
for (const k of I18N_GONE) {
	ok(!(k in ca), `i18n '${k}' retirada però encara a ca.json (clau òrfena)`);
	ok(!(k in es), `i18n '${k}' retirada però encara a es.json (clau òrfena)`);
}

// 5 · Higiene: index_turisme (deprecat) fora del catàleg servit.
ok(!('index_turisme' in metrics), `index_turisme encara al catàleg servit (hauria d'estar fora)`);

// ── D9 · les tres regles de pintura, guardades sobre la DADA que el tauler consumeix ────────
// (El mart ja té el seu propi verificador —`verify_tendencia.py`, que recalcula els 1.894 Δ—;
//  aquí es guarda que el que el FRONT llegeix compleix el que el front promet.)

// 6 · FRESCOR PER TARGETA (E5): cada KPI de mètrica —inclosos els que viuen dins una barra i el
//     padró de la capçalera— ha de poder dir de quan és la seva xifra.
const frescKeys = new Set([PRESENCIA_KEY, ...EDATS_KEYS, ...NAIX_BAR_KEYS, 'pct_nascuda_estranger']);
for (const kpi of GOVERN_KPIS) if (kpi.kind === 'metric') frescKeys.add(kpi.key);
for (const k of frescKeys) {
	ok(
		!!metrics[k]?.frescor,
		`KPI '${k}': sense bloc 'frescor' al catàleg — la targeta no podria datar-se (E5)`
	);
}

// 6b · V3 · «sense procés automàtic» FORA de les targetes (vot de Bea): la fitxa del municipi
//      ja no pot pintar el procés de refresc; /metodologia sí (ho guarda verify-docs).
ok(
	!pageSrc.includes('proces_refresc'),
	`la fitxa del municipi encara llegeix 'proces_refresc' — el procés és de /metodologia (V3)`
);

// 7 · TENDÈNCIA (E6): el tauler ha d'existir amb la Pobla, i CAP entrada pot trencar les regles.
const tp = tauler.municipis?.[POBLA];
ok(!!tp, `shard tauler/${POBLA}.json sense la Pobla (${POBLA})`);
if (tp) {
	// 7a · Cap fletxa sense període, i cap 'sense_serie' sense motiu (les dues regles dures).
	let nAmbSerie = 0;
	let nSenseSerie = 0;
	for (const [key, entries] of Object.entries(tp.tendencia ?? {})) {
		ok(Array.isArray(entries) && entries.length > 0, `tendencia['${key}'] buida`);
		for (const e of entries ?? []) {
			if (e.estat === 'sense_serie') {
				nSenseSerie++;
				ok(!!e.motiu, `tendencia['${key}'] 'sense_serie' SENSE motiu — es pintaria un buit mut`);
				ok(e.direccio == null, `tendencia['${key}'] 'sense_serie' amb direcció (fletxa sense sèrie)`);
			} else {
				nAmbSerie++;
				ok(
					!!e.periode_actual && !!e.periode_anterior,
					`tendencia['${key}'] amb direcció '${e.direccio}' i SENSE període — viola la regla 1`
				);
				// Doctrina del «<5»: un delta emmascarat és un INTERVAL, mai un número ni un zero.
				if (e.delta_emmascarat) {
					ok(e.delta === null, `tendencia['${key}'] emmascarada però amb delta exacte`);
					ok(
						e.delta_min !== null && e.delta_max !== null,
						`tendencia['${key}'] emmascarada sense interval [min,max] — el front no podria pintar-la`
					);
				}
			}
		}
	}
	ok(nAmbSerie > 0 && nSenseSerie > 0, `la Pobla hauria de tenir tendències amb i sense sèrie`);

	// 7b · L'ATUR PORTA DUES COMPARACIONS (E6 de Bea): a la Pobla apunten en sentits OPOSATS
	//      (juny 2026: +4 vs maig, −3 vs juny 2025). Ensenyar-ne una sola seria triar la
	//      narrativa; aquest test cau si algú un dia en pinta només una.
	const at = tp.tendencia?.atur_registrat ?? [];
	ok(at.length === 2, `l'atur de la Pobla hauria de portar 2 comparacions, en porta ${at.length}`);
	const cmps = at.map((e) => e.comparacio).sort();
	ok(
		cmps.join(',') === 'mateix_mes_any_anterior,mes_anterior',
		`comparacions d'atur inesperades: ${cmps.join(',')}`
	);
	const dirs = new Set(at.map((e) => e.direccio));
	ok(dirs.size === 2, `àncora de la Pobla: les dues comparacions d'atur haurien de discrepar`);

	// 7c · POBLACIÓ I FRANGES: 'sense_serie' amb motiu (E11 — límit de la FONT, no pendent
	//      nostre). La barra d'edats pinta el motiu UNA vegada, però la fila de CADA franja ha
	//      de seguir al mart: una absència muda seguiria sent invisible.
	for (const k of ['poblacio', 'pob_0_14', 'pob_15_64', 'pob_65_84', 'pob_85_mes']) {
		const e = (tp.tendencia?.[k] ?? [])[0];
		ok(!!e, `tendencia['${k}'] absent`);
		if (e) ok(e.estat === 'sense_serie' && !!e.motiu, `tendencia['${k}'] sense motiu declarat`);
	}
	// L'origen SÍ que té sèrie (finestra 2021→2025): +5,61 punts a la Pobla, i ha de casar amb
	// el `delta_pct_estrangera_finestra` del dataset (paritat: la targeta ja no el llegeix d'allà).
	const org = (tp.tendencia?.pct_nacionalitat_estrangera ?? [])[0];
	ok(!!org && org.estat === 'amb_serie', `l'origen de la Pobla hauria de tenir sèrie`);
	if (org) {
		const dv = dataset.municipis[POBLA]?.values?.delta_pct_estrangera_finestra;
		ok(
			dv == null || Math.abs(dv - org.delta) < 1e-6,
			`paritat trencada a l'origen: dataset ${dv} ≠ tendència ${org.delta}`
		);
	}

	// 7d · ATUR (E4): darrer mes + sèrie. `valor: null` només amb `emmascarat` i interval.
	ok(!!tp.atur?.darrer?.date, `atur de la Pobla sense darrer mes`);
	ok((tp.atur?.serie ?? []).length > 1, `atur de la Pobla sense sèrie`);
	for (const p of [tp.atur?.darrer, ...(tp.atur?.serie ?? [])]) {
		if (!p) continue;
		if (p.valor === null) {
			ok(p.emmascarat === true, `punt d'atur ${p.date} nul sense emmascarar (seria un forat mut)`);
			ok(
				Number.isInteger(p.min) && Number.isInteger(p.max),
				`punt d'atur ${p.date} emmascarat sense interval — es pintaria un zero`
			);
		}
	}
}

// 8 · La frescor de l'atur no viu al catàleg de mètriques (l'atur no és a `mart_municipi`):
//     ve de `_meta.atur.frescor`. Sense això la targeta no es podria datar.
ok(!!tauler._meta?.atur?.frescor?.actualitzacio, `_meta.atur.frescor sense cadència declarada`);

// ── V3 · LES BARRES APILADES: les 8 xifres segueixen al DOM i la partició no menteix ────────
// Fondre 8 targetes en 2 barres és lectura, no pèrdua: (a) el component ha de CABLAR les dues
// barres des del descriptor (si algú les despenja, això cau); (b) cada xifra hi és a la dada;
// (c) la nota única del grup A («les particions sumen exactament el padró») ha de ser VERITAT
// sobre el dataset servit — si un dia no suma, la nota es torna mentida i això cau.
{
	ok(
		GOVERN_KPIS.some((k) => k.kind === 'edats'),
		`el tauler ha perdut la targeta d'estructura d'edats (barra apilada)`
	);
	ok(
		GOVERN_KPIS.some((k) => k.kind === 'naixement'),
		`el tauler ha perdut la targeta «d'on venim» (barra apilada)`
	);
	for (const name of ['EDATS_BANDS', 'NAIX_BAR_KEYS', 'gov_grp_a_nota', 'gov_envell_frase']) {
		ok(pageSrc.includes(name), `'${name}' no està cablejat a la fitxa — es declararia i no es pintaria`);
	}
	// Les 8 xifres, presents a la dada de la Pobla (el que la barra ha de pintar).
	const VUIT = [...EDATS_KEYS, ...NAIX_BAR_KEYS, 'pct_nascuda_estranger'];
	for (const k of VUIT) {
		ok(
			typeof dataset.municipis[POBLA]?.values?.[k] === 'number',
			`'${k}' sense valor a la Pobla — una de les 8 xifres de les barres faltaria al DOM`
		);
	}
	// La partició suma EXACTAMENT el padró a tots els municipis servits amb components complets.
	for (const [ine5, mu] of Object.entries(dataset.municipis)) {
		const v = mu.values ?? {};
		if (typeof v.poblacio !== 'number') continue;
		const ed = EDATS_KEYS.map((k) => v[k]);
		if (ed.every((x) => typeof x === 'number')) {
			ok(
				ed.reduce((a, b) => a + b, 0) === v.poblacio,
				`edats de ${ine5} no sumen el padró (${ed.join('+')} ≠ ${v.poblacio}) — la nota del grup A mentiria`
			);
		}
		const na = NAIX_BAR_KEYS.map((k) => v[k]);
		if (na.every((x) => typeof x === 'number')) {
			ok(
				na.reduce((a, b) => a + b, 0) === v.poblacio,
				`naixement de ${ine5} no suma el padró (${na.join('+')} ≠ ${v.poblacio}) — la nota del grup A mentiria`
			);
		}
	}
}

// ── V3 · HUT a la targeta de turisme (vot de Bea: sí) ───────────────────────────────────────
{
	const hutKpi = GOVERN_KPIS.find((k) => k.kind === 'metric' && k.hut);
	ok(!!hutKpi, `cap targeta declara el cru HUT — el vot de Bea (HUT sí) s'ha despenjat`);
	ok(hutKpi?.key === 'rtc_per_1000hab', `el cru HUT hauria de viure a la targeta de turisme`);
	for (const k of ['rtc_total', 'rtc_hut']) {
		ok(!!metrics[k]?.source, `'${k}' sense font al catàleg — el cru HUT quedaria sense procedència`);
		ok(
			typeof dataset.municipis[POBLA]?.values?.[k] === 'number',
			`'${k}' sense valor a la Pobla — el cru HUT no es podria pintar`
		);
	}
	ok(pageSrc.includes('gov_hut_cru'), `el cru HUT no està cablejat a la fitxa`);
}

// ── V3 · E13 — caveat de micromunicipi (doctrina del contracte, padró < 250) ────────────────
// La llista i el llindar del descriptor han de SER els de la doctrina (capçal de metrics.yml);
// si divergeixen, el tauler pintaria una doctrina que el contracte no diu. El cas fundacional
// (Sant Jaume de Frontanyà, 08216, 25 hab) ha d'activar la nota a les targetes afectades.
{
	const DOCTRINA_E13 = ['kg_hab_any', 'kwh_hab', 'vidre_hab', 'rtc_per_1000hab', 'index_envelliment'];
	ok(
		[...E13_KEYS].sort().join(',') === [...DOCTRINA_E13].sort().join(','),
		`E13_KEYS (${E13_KEYS.join(',')}) divergeix de la doctrina del contracte (${DOCTRINA_E13.join(',')})`
	);
	ok(E13_LLINDAR === 250, `E13_LLINDAR (${E13_LLINDAR}) divergeix del llindar de la doctrina (250)`);
	ok(pageSrc.includes('gov_e13_micro') && pageSrc.includes('showE13'), `la nota E13 no està cablejada a la fitxa`);
	const SJ = '08216';
	const sj = dataset.municipis[SJ];
	ok(!!sj, `Sant Jaume de Frontanyà (${SJ}) absent del dataset — el cas fundacional d'E13 no es pot exercir`);
	if (sj) {
		ok(
			typeof sj.values.poblacio === 'number' && sj.values.poblacio < E13_LLINDAR,
			`Sant Jaume hauria de ser micromunicipi (padró ${sj.values.poblacio} ≥ ${E13_LLINDAR}?)`
		);
		for (const k of E13_KEYS) {
			ok(
				typeof sj.values[k] === 'number',
				`'${k}' sense valor a Sant Jaume — la targeta amb caveat E13 no tindria número a acompanyar`
			);
		}
	}
}

// ── V3 · FORA DUPLICATS: les seccions eliminades no poden renéixer a mitges ─────────────────
{
	for (const gone of ['muni_nums_title', 'muni-5num', 'muni_hab_padro', 'muni_etca_srcline']) {
		ok(
			!pageSrc.includes(gone),
			`'${gone}' encara apareix a la fitxa — «Els números clau»/targeta gran del padró havien de desaparèixer (V3 §7)`
		);
	}
}

// ── D11 · LLOC DE NAIXEMENT (E11, adaptada a la barra de V3) ────────────────────────────────
// Aquesta secció existeix perquè la troballa de D11 no pugui tornar. D9 va tancar l'E11 de Bea
// amb una premissa falsa («el mart només té nacionalitat») i el tauler va quedar sense CAP
// mètrica de lloc de naixement tot i que les quatre arribaven servides al web. La guarda es
// planta a l'altre costat — de la DADA cap al descriptor.
const NAIX_KEYS = [...NAIX_BAR_KEYS, 'pct_nascuda_estranger'];
const naixCard = GOVERN_KPIS.find((x) => x.kind === 'naixement');
const kpiFor = (k) => GOVERN_KPIS.find((x) => x.kind === 'metric' && x.key === k);

// 9a · Si la dada hi és, el tauler l'ha de pintar (ara via la targeta de barra).
for (const k of NAIX_KEYS) {
	const v = dataset.municipis[POBLA]?.values?.[k];
	if (v == null) continue; // sense dada no hi ha res a exigir (el «no» és una resposta vàlida)
	ok(
		!!naixCard,
		`'${k}' té dada a la Pobla (${v}) i el tauler NO la pinta — E11 de Bea demana lloc de ` +
			`naixement, i tenir-lo servit i no ensenyar-lo és la regressió que D11 va tancar`
	);
}

// 9b · La foto NO es pot vendre com a sèrie. La targeta de naixement declara el seu límit UNA
//      vegada (V3), i no pren prestada la tendència d'una sèrie de NACIONALITAT (que mesura
//      una altra gent: qui es naturalitza en surt sense marxar del poble).
if (naixCard) {
	ok(
		naixCard.note === 'gov_naix_foto',
		`la targeta de naixement no declara la nota «foto, no sèrie» — la foto es llegiria com a evolució`
	);
	ok(
		!/nacionalitat|estrangera/.test(naixCard.trendKey ?? ''),
		`la targeta de naixement agafa la tendència de '${naixCard.trendKey}', que és una sèrie de ` +
			`NACIONALITAT presentada sota una etiqueta de lloc de naixement`
	);
}
for (const k of NAIX_KEYS) {
	// Si un dia el mart SÍ que serveix sèrie de lloc de naixement, la nota «foto, no sèrie»
	// passa a ser mentida: el test cau per obligar a reescriure-la, no per castigar la millora.
	for (const e of tauler.municipis?.[POBLA]?.tendencia?.[k] ?? []) {
		ok(
			e.estat !== 'amb_serie',
			`el mart ja serveix SÈRIE de '${k}': la nota de límit d'aquesta targeta ha quedat ` +
				`obsoleta i s'ha d'actualitzar (ja no és «foto, no sèrie»)`
		);
	}
}

// 9c · A l'inrevés: la targeta que SÍ que porta la sèrie de nacionalitat ha de dir que ho és.
const nacKpi = kpiFor('pct_nacionalitat_estrangera');
const nacAmbSerie = (tauler.municipis?.[POBLA]?.tendencia?.pct_nacionalitat_estrangera ?? []).some(
	(e) => e.estat === 'amb_serie'
);
if (nacKpi && nacAmbSerie) {
	ok(
		!!nacKpi.note,
		`el tauler pinta l'evolució de nacionalitat al costat del lloc de naixement i NO declara ` +
			`que és de nacionalitat — són conjunts diferents (a la Pobla: 134 nascuts a l'estranger ` +
			`vs ~106 amb passaport estranger)`
	);
}

// 9d · Tota `note` declarada al descriptor ha d'existir a ca+es I estar cablejada al component.
//      Sense el cablatge, la clau seria un text que no es pinta enlloc: un límit declarat en un
//      fitxer i invisible a la pantalla és pitjor que no declarar-lo.
for (const kpi of GOVERN_KPIS) {
	if (!kpi.note) continue;
	ok(!!ca[kpi.note] && !!es[kpi.note], `i18n de la nota '${kpi.note}' absent (ca/es)`);
	ok(
		pageSrc.includes(kpi.note),
		`la nota '${kpi.note}' es declara a kpis.js però no està cablejada a la fitxa (GOV_NOTE)`
	);
}

// ── P-947 · EL RANG ÉS DE LA SEVA COMARCA, NO DELS 31 ───────────────────────────────────────
// La promesa de P-947 (Bea, 2026-07-27): el MATEIX tauler per a TOTS els 947, amb el rang «k de n»
// de la comarca del PROPI municipi. Aquesta guarda ho exerceix sobre un municipi de FORA del
// Berguedà — Barcelona (Barcelonès) — perquè la resta del verificador mira la Pobla, que és del
// pilot. Si el rang es filtrés per la llista fixa del Berguedà (31) o pels 947 sencers, el
// denominador `n_amb_dada` NO cabria dins la seva comarca. El shard del municipi també ha de
// servir (atur), com per a qualsevol dels 947.
const territori = read(resolve(REPO, 'data/web/municipis-territori.json'));
const comarcaSize = {};
for (const t of Object.values(territori)) {
	if (t?.comarca) comarcaSize[t.comarca] = (comarcaSize[t.comarca] ?? 0) + 1;
}
ok(
	Object.keys(govern).length > 900,
	`govern.catalunya.json cobreix ${Object.keys(govern).length} munis, no els ~947`
);
const BCN = '08019';
const gb = govern[BCN];
ok(!!gb, `govern.catalunya.json sense un municipi de fora del Berguedà (${BCN}, Barcelona)`);
if (gb) {
	ok(
		gb.comarca === 'Barcelonès',
		`Barcelona (${BCN}) hauria de sortir al Barcelonès, surt a '${gb.comarca}'`
	);
	const nCom = comarcaSize[gb.comarca] ?? 0;
	ok(nCom > 0 && nCom < 31, `mida del ${gb.comarca} inesperada (${nCom}) — hauria de ser < 31 (Berguedà)`);
	for (const k of GOVERN_RANK_KEYS) {
		const cell = gb.metrics?.[k];
		if (!cell || cell.rang == null) continue; // sense dada, res a exigir (el «no» és vàlid)
		ok(
			cell.n_amb_dada <= nCom,
			`rang de '${k}' a Barcelona compta ${cell.n_amb_dada} munis, més que la seva comarca ` +
				`(${gb.comarca}, ${nCom}): el rang NO seria de la seva comarca`
		);
		ok(
			cell.rang >= 1 && cell.rang <= cell.n_amb_dada,
			`rang de '${k}' a Barcelona fora de [1, ${cell.n_amb_dada}]`
		);
	}
	// El SHARD d'un municipi de fora del pilot també ha de servir (atur), com per a qualsevol dels 947.
	const bcnShard = read(resolve(REPO, `data/web/tauler/${BCN}.json`));
	ok(
		!!bcnShard?.atur?.darrer?.date,
		`shard tauler/${BCN}.json sense atur (el tauler no arribaria a Barcelona)`
	);
}

// ── W1 · LA NAVEGACIÓ INTERNA ARRIBA ALS 947, NO ES QUEDA AL PILOT ──────────────────────────
// Esmena de Bea (2026-07-31): «un cop seleccionat un municipi, des de dins només es poden
// seleccionar municipis del Berguedà». La causa era una llista derivada del dataset del PILOT
// (31) dins d'una fitxa que se serveix per als 947 — la mateixa forma de bug que el glossari
// (`DIM_ORDER`) i el conjunt escrit a mà del mart: una llista curta que descarta en silenci.
// Es guarda pels DOS costats: la dada (el catàleg cobreix els 947 i cap slug xoca) i el
// cablatge (el selector es construeix del catàleg, no del dataset).
let nMunisCataleg = 0;
let nAmbArticle = 0;
let nComarques = 0;
{
	// (a) LA DADA. El catàleg el genera el prebuild des de la geometria oficial, que SÍ que és al
	//     repo: es reconstrueix aquí igual que a `copy-data.mjs` per no dependre de `static/`
	//     (gitignored) i que la guarda corri en un checkout net.
	const geo = read(resolve(WEB, 'static/geo/catalunya-municipis.geojson'));
	const cataleg = (geo.features ?? [])
		.map((f) => ({ ine5: String(f.properties?.ine5 ?? ''), nom: String(f.properties?.nom ?? '') }))
		.filter((mn) => mn.ine5 && mn.nom);
	ok(
		cataleg.length > 900,
		`el catàleg de municipis només cobreix ${cataleg.length} munis: el selector no arribaria als ~947`
	);

	// (b) COL·LISIÓ DE SLUGS a escala Catalunya. La guarda dura viu a `entries()` (trenca el BUILD);
	//     aquí es repeteix OFFLINE i abans, amb el toSlug REAL —importat, no reescrit—. A 947 el risc
	//     és més gran que al pilot: dos municipis amb el mateix slug es menjarien la fitxa l'un a
	//     l'altre. Si algun dia n'apareix una, es resol amb sufix de comarca (spec §8.1).
	const perSlug = new Map();
	for (const mn of cataleg) {
		const s = toSlug(mn.nom);
		if (perSlug.has(s) && perSlug.get(s).ine5 !== mn.ine5) {
			const prev = perSlug.get(s);
			ok(false, `col·lisió de slug "${s}": ${prev.ine5} (${prev.nom}) vs ${mn.ine5} (${mn.nom})`);
		}
		perSlug.set(s, mn);
	}
	ok(
		perSlug.size === cataleg.length,
		`${cataleg.length} municipis però només ${perSlug.size} slugs distints`
	);

	// (c) LA CLAU D'ORDENACIÓ NO POT MOURE LA URL. La llista es mostra en forma corrent i s'ordena
	//     per la forma d'índex; si `nomIndex` canviés el slug d'algun municipi, el selector portaria
	//     a una pàgina que no existeix. S'exerceix sobre els 947, i sobre els que tenen article
	//     (els únics on la funció fa res) es comprova que la volta sencera torna al nom original.
	let ambArticle = 0;
	for (const mn of cataleg) {
		const idx = nomIndex(mn.nom);
		ok(toSlug(idx) === toSlug(mn.nom), `nomIndex('${mn.nom}') mou el slug: '${toSlug(idx)}'`);
		if (idx === mn.nom) continue;
		ambArticle++;
		ok(
			nomCanonic(idx) === mn.nom,
			`la volta nomIndex→nomCanonic no torna a '${mn.nom}' (torna '${nomCanonic(idx)}')`
		);
	}
	ok(ambArticle > 100, `només ${ambArticle} municipis amb article: nomIndex no estaria fent res`);
	nMunisCataleg = cataleg.length;
	nAmbArticle = ambArticle;

	// (d) EL CABLATGE. La fitxa ha de rebre el catàleg i construir-hi el selector. Sense això, la
	//     dada seria correcta i la pantalla seguiria oferint 31 opcions.
	const loaderSrc = readFileSync(resolve(WEB, 'src/routes/municipi/[slug]/+page.ts'), 'utf8');
	ok(
		/return\s*\{[\s\S]*?\bcataleg\b[\s\S]*?\};/.test(loaderSrc),
		`el loader de la fitxa NO retorna el catàleg: el selector no podria arribar als 947`
	);
	ok(
		loaderSrc.includes('Col·lisió de slug'),
		`la guarda de col·lisió d'\`entries()\` ha desaparegut del loader de la fitxa`
	);
	ok(
		/const muniOptions[\s\S]{0,600}cataleg/.test(pageSrc),
		`el selector de la fitxa no es construeix del CATÀLEG (tornaria a quedar-se al pilot, W1)`
	);
	ok(
		!/const muniOptions[\s\S]{0,200}Object\.values\(dataset\.municipis\)\.map\(\(mr\)\s*=>\s*\(\{\s*\n?\s*ine5: mr\.ine5,\s*\n?\s*nom: nomCanonic/.test(
			pageSrc
		),
		`el selector torna a derivar-se del dataset del pilot (31) — és exactament el bug W1`
	);
}

// ── W5 · LA PORTA DE LA HOME ESTÀ OBERTA I LES SEVES XIFRES ES COMPTEN ──────────────────────
// Esmena de Bea (2026-07-31): «l'apartat de la home llegeix la comarca està desactualitzat».
// Deia «properament» d'una cosa que ja existeix i etiquetava el 947 com a «resta de Catalunya»
// quan és el TOTAL del país (la resta serien 916). La guarda vigila que no torni: cap porta
// morta a la home, i cap xifra de portes escrita al copy (les xifres es compten de l'artefacte).
{
	const homeSrc = readFileSync(resolve(WEB, 'src/routes/+page.svelte'), 'utf8');
	// Es miren els elements que es PINTEN, no els comentaris: el bloc que explica per què la porta
	// morta va caure hi anomena les classes, i una guarda que caigués per la seva pròpia
	// documentació seria un fals positiu (i acabaria empenyent a esborrar l'explicació).
	const homeMarkup = homeSrc.replace(/<!--[\s\S]*?-->/g, '');
	ok(
		!homeMarkup.includes('porta--soon') && !homeMarkup.includes('aria-disabled'),
		`la home torna a tenir una porta morta ('porta--soon'/'aria-disabled') a «Llegeix la comarca»`
	);
	ok(
		homeSrc.includes("localizeHref('/comarca')"),
		`la porta de tota Catalunya no porta a l'índex de comarques (/comarca)`
	);
	for (const k of ['home_porta_cat', 'home_porta_cat_sub', 'home_porta_cat_cta']) {
		ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
	}
	// Les xifres van per paràmetre, mai escrites: un número al copy es queda estale en silenci.
	for (const k of ['home_porta_cat_sub', 'home_porta_bergueda_sub']) {
		for (const [loc, cat] of [['ca', ca], ['es', es]]) {
			ok(
				!/\d/.test(cat[k] ?? ''),
				`i18n '${k}' (${loc}) porta una xifra escrita al copy: «${cat[k]}» — s'ha de comptar de la dada`
			);
		}
	}
	// L'índex de comarques ha d'existir de debò (la porta no pot apuntar al no-res).
	const idxSrc = readFileSync(resolve(WEB, 'src/routes/comarca/+page.ts'), 'utf8');
	ok(
		idxSrc.includes("fetch('/data/comarques.json')"),
		`l'índex de comarques no llegeix l'agrupació territorial (/data/comarques.json)`
	);
	for (const k of ['comarques_title', 'comarques_sub', 'comarques_meta', 'comarques_eyebrow',
		'comarques_sense_vegueria']) {
		ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
	}
	// L'agrupació ha de cobrir el país sencer. Es llegeix de la seva FONT versionada
	// (`municipis-territori.json`, d'on el prebuild deriva `comarques.json`) per no dependre de
	// `static/`, que és gitignored. Si un dia no sumés, la porta prometria «totes les comarques»
	// i n'ensenyaria una part.
	const munisPerComarca = {};
	let senseComarca = 0;
	for (const t of Object.values(territori)) {
		if (t?.comarca) munisPerComarca[t.comarca] = (munisPerComarca[t.comarca] ?? 0) + 1;
		else senseComarca++;
	}
	ok(
		Object.keys(territori).length > 900,
		`l'agrupació territorial només cobreix ${Object.keys(territori).length} municipis`
	);
	ok(senseComarca === 0, `${senseComarca} municipis sense comarca: no sortirien a cap porta`);
	ok(
		Object.keys(munisPerComarca).length > 40,
		`només ${Object.keys(munisPerComarca).length} comarques a l'agrupació`
	);
	nComarques = Object.keys(munisPerComarca).length;
}

// ── B2 · EL HERO DE LA HOME NO POT TORNAR A PROMETRE EL PILOT ───────────────────────────────
// Esmena de Bea (2026-07-31): les cotes del hero deien «31 municipis» en una portada que promet
// 43 comarques i 947 municipis dues seccions més avall. La causa és la de sempre: una xifra
// ESCRITA a mà (i, de propina, en català dur dins d'una pàgina que es tradueix). Mateixa guarda
// que W5 va posar a les portes, ara també a les cotes.
let nHeroLabels = 0;
{
	const homeSrc = readFileSync(resolve(WEB, 'src/routes/+page.svelte'), 'utf8');
	const decl = homeSrc.match(/const heroLabels\s*=\s*\$derived\(([\s\S]*?)\n\t\);/);
	ok(!!decl, `el hero de la home ja no declara heroLabels com a \`$derived\` de la dada comptada`);
	if (decl) {
		const body = decl[1];
		// Cap xifra escrita entre cometes: els números han de venir per paràmetre i18n. Les
		// coordenades del motiu de marca (42°17′N · 2°01′E) són l'excepció declarada — són el
		// MATEIX parell que el peu de pàgina, i no afirmen res sobre la nostra cobertura.
		const COORD = /^\d{1,2}°\d{2}′[NSEW]$/;
		for (const lit of body.match(/'[^']*'/g) ?? []) {
			const txt = lit.slice(1, -1);
			if (COORD.test(txt)) continue;
			ok(
				!/\d/.test(txt),
				`el hero de la home torna a portar una xifra escrita a mà («${txt}») — s'ha de comptar`
			);
		}
		ok(
			body.includes('totalMunis') && body.includes('totalComarques'),
			`el hero de la home no es construeix dels comptadors del loader (tornaria a quedar estale)`
		);
		nHeroLabels = (body.match(/,/g) ?? []).length; // orientatiu, per al report
	}
	for (const k of ['home_hero_munis', 'home_hero_comarques']) {
		ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
		for (const [loc, cat] of [['ca', ca], ['es', es]]) {
			ok(
				!/\d/.test(cat[k] ?? ''),
				`i18n '${k}' (${loc}) porta una xifra escrita al copy: «${cat[k]}»`
			);
		}
	}
	// El pilot no pot tornar al text que es PINTA. Es miren el markup i el codi sense comentaris
	// (el bloc que explica per què «31 municipis» va caure l'anomena; una guarda que caigués per
	// la seva pròpia documentació acabaria empenyent a esborrar l'explicació — la lliçó de W5).
	const homeViu = homeSrc
		.replace(/<!--[\s\S]*?-->/g, '')
		.replace(/\/\*[\s\S]*?\*\//g, '')
		.replace(/^\s*\/\/.*$/gm, '');
	ok(!/31 municipis/.test(homeViu), `«31 municipis» (el pilot) ha tornat a la home`);

	// El PEU es pinta a totes les pàgines, la portada inclosa: les seves cotes portaven un '31'
	// pelat (el pilot) i un '593' sense procedència. Aquí no hi ha cap comptador —el layout no
	// carrega dades—, així que la regla és més dura que a la home: cap cota pot ser un número
	// SOL. Una cota que digui de què és (altitud, coordenada) sí.
	const layoutSrc = readFileSync(resolve(WEB, 'src/routes/+layout.svelte'), 'utf8');
	const foot = layoutSrc.match(/const footLabels\s*=\s*\[([^\]]*)\]/);
	ok(!!foot, `no s'ha trobat footLabels al layout`);
	for (const lit of foot?.[1].match(/'[^']*'/g) ?? []) {
		const txt = lit.slice(1, -1);
		ok(
			!/^[\d.,\s]+$/.test(txt),
			`cota del peu «${txt}»: un número sol, sense unitat ni procedència, a totes les pàgines`
		);
	}
}

// ── B3 · EL DENOMINADOR DEL RANG ÉS LLEGIBLE, I EL MOTIU QUE EN DIEM ÉS VERITAT ─────────────
// Esmena de Bea (2026-07-31): «6 de 27» al costat de «8 de 31» sembla arbitrari. La targeta ho
// explica ara — però explicar-ho obliga a AFIRMAR UNA CAUSA, i una causa mal atribuïda és una
// mentida amb bona intenció. Per això aquesta secció no es limita al cablatge: contrasta CADA
// motiu declarat a `kpis.js` amb els 947 municipis servits. Si un dia la dada deixa de sostenir
// el text, cau aquí i no a la pantalla.
//
// (La premissa que va arribar al brief —«qui no té dada és zero»— és FALSA i aquesta secció
// també ho fixa: els 4 municipis del Berguedà sense percentatge tenen recompte, i dos no són
// zero —Fígols 5 de 41, la Quar 7 de 44—; tractar-los com a zero pintaria la Quar l'última
// quan seria la 2a de la comarca.)
const catDataset = read(resolve(REPO, 'data/web/municipis.catalunya.json'));
const catMunis = catDataset.municipis ?? catDataset;
let nDenomExplicat = 0;
{
	// (a) CABLATGE: la línia existeix, el loader serveix el total i cada motiu declarat es pinta.
	const loaderSrc = readFileSync(resolve(WEB, 'src/routes/municipi/[slug]/+page.ts'), 'utf8');
	ok(
		/return\s*\{[\s\S]*?\bcomarcaMunis\b[\s\S]*?\};/.test(loaderSrc),
		`el loader de la fitxa no retorna 'comarcaMunis': el denominador no es podria explicar`
	);
	// Cablatge de VERITAT: la condició s'ha de CRIDAR (no només declarar) i el text s'ha de
	// pintar amb les dues xifres. Declarar-la i no cridar-la deixaria el codi verd i la pantalla
	// muda, que és la forma d'error que aquesta secció existeix per evitar.
	ok(
		/\{#if denomIncomplet\(/.test(pageSrc),
		`la condició del denominador es declara però no es crida enlloc: la línia no es pintaria mai`
	);
	ok(
		/m\.gov_denom_line\(\{[^}]*\bn:[^}]*\btotal:/s.test(pageSrc),
		`la línia del denominador no es pinta amb les dues xifres (amb dada / total de la comarca)`
	);
	// El rang es pinta des d'UN sol lloc (snippet compartit): abans era el mateix marcatge tres
	// vegades, i una explicació que només arribés a dues terceres parts seria pitjor que cap.
	ok(
		pageSrc.includes('{#snippet rangComarcal('),
		`el rang ja no es pinta des d'un snippet compartit — les tres còpies poden divergir`
	);
	ok(
		(pageSrc.match(/@render rangComarcal\(/g) ?? []).length === 3,
		`el snippet del rang no es fa servir als TRES llocs que en pinten (presència, mètrica, naixement)`
	);
	ok(
		(pageSrc.match(/class="gov-kpi__rankk"/g) ?? []).length === 1,
		`hi ha marcatge de rang duplicat fora del snippet (tornaria a divergir)`
	);
	const REASONS = [...new Set([...Object.values(GOVERN_DENOM_REASON), GOVERN_DENOM_REASON_DEFAULT])];
	for (const k of ['gov_denom_line', ...REASONS]) {
		ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
		ok(pageSrc.includes(k), `el motiu '${k}' es declara però no es pinta enlloc`);
	}

	// (b) EL LLINDAR QUE EXPLIQUEM ÉS EL NOSTRE DE VERITAT. `demografia_min_n` viu al transform
	//     (jurisdicció de Sondeig): aquí només es LLEGEIX, per no explicar a la pantalla un
	//     llindar que allà ja s'ha mogut.
	const dbtYml = readFileSync(resolve(REPO, 'packages/transform/dbt_project.yml'), 'utf8');
	const minN = Number((dbtYml.match(/^\s*demografia_min_n:\s*(\d+)/m) ?? [])[1]);
	ok(
		Number.isInteger(minN) && minN === GOVERN_DENOM_MIN_N,
		`GOVERN_DENOM_MIN_N (${GOVERN_DENOM_MIN_N}) divergeix de demografia_min_n del transform (${minN})`
	);

	// (c) EL MOTIU 'minn' ÉS VERITAT ALS 947: cap municipi sense percentatge d'origen arriba al
	//     llindar, i cap que l'arribi es queda sense. Si això es trenca, la frase «hi viuen menys
	//     de 50 persones» passa a ser falsa per a algun poble concret.
	for (const [i, g] of Object.entries(govern)) {
		const cell = g.metrics?.pct_nacionalitat_estrangera;
		if (!cell) continue;
		const pob = catMunis[i]?.values?.poblacio;
		if (typeof pob !== 'number') continue;
		if (cell.valor === null) {
			ok(
				pob < GOVERN_DENOM_MIN_N,
				`${i} sense % de nacionalitat i amb ${pob} hab (≥ ${GOVERN_DENOM_MIN_N}): el motiu ` +
					`'gov_denom_minn' seria FALS per a aquest municipi`
			);
		} else {
			ok(
				pob >= GOVERN_DENOM_MIN_N,
				`${i} amb % de nacionalitat i només ${pob} hab: el llindar declarat no s'estaria aplicant`
			);
		}
	}
	// …i el cas fundacional, la Quar (08177): 7 persones de nacionalitat estrangera sobre 44 hab
	// = 15,9 %, que la faria la 2a de la comarca. Tractar-la com a zero —la premissa que va
	// arribar al brief— la pintaria l'ÚLTIMA. Per això la línia diu «no vol dir zero».
	//
	// ⚠️ El que NO pot dir és «el recompte sí que es publica»: el 7 viu a `mart_demografia`
	// (`poblacio_nacionalitat_estrangera`) i NO arriba al web —no és al contracte servit ni a cap
	// dataset—, així que a la fitxa de la Quar no hi ha cap xifra de nacionalitat. Aquesta guarda
	// planta la frontera als DOS costats: mentre no se serveixi, el text no el pot prometre; i el
	// dia que Sondeig el serveixi, cau per obligar a REESCRIURE la frase (que llavors es queda
	// curta), no per castigar la millora — mateix patró que la nota «foto, no sèrie» (§9b).
	{
		const QUAR = '08177';
		const v = catMunis[QUAR]?.values ?? {};
		ok(
			govern[QUAR]?.metrics?.pct_nacionalitat_estrangera?.valor === null,
			`la Quar (${QUAR}) hauria de tenir el PERCENTATGE suprimit pel llindar mínim N`
		);
		ok(
			v.poblacio_nacionalitat_estrangera === undefined,
			`el web ja serveix 'poblacio_nacionalitat_estrangera': la línia del denominador s'ha ` +
				`d'actualitzar per DIR que el recompte es publica (ara només diu que no vol dir zero)`
		);
		ok(
			!/recompte|recuento/i.test(`${ca.gov_denom_minn} ${es.gov_denom_minn}`),
			`la línia del denominador promet un RECOMPTE que el web no serveix per a nacionalitat`
		);
		// El que la Quar SÍ que té: la partició de lloc de naixement, amb els seus recomptes. La
		// seva fitxa no és muda, i això és el que sosté que un percentatge suprimit no és un forat.
		ok(
			NAIX_BAR_KEYS.every((k) => typeof v[k] === 'number') &&
				NAIX_BAR_KEYS.reduce((a, k) => a + v[k], 0) === v.poblacio,
			`la Quar (${QUAR}) sense la partició de lloc de naixement servida (recomptes citables)`
		);
	}

	// (d) EL MOTIU 'ratio' ÉS VERITAT: on no hi ha índex d'envelliment, és que no hi ha ningú de
	//     0 a 14 (divisió impossible), no que la dada falti.
	for (const [i, g] of Object.entries(govern)) {
		const cell = g.metrics?.index_envelliment;
		if (!cell || cell.valor !== null) continue;
		ok(
			catMunis[i]?.values?.pob_0_14 === 0,
			`${i} sense índex d'envelliment i amb ${catMunis[i]?.values?.pob_0_14} hab de 0-14: el ` +
				`motiu 'gov_denom_ratio' (divisió impossible) seria FALS per a aquest municipi`
		);
	}

	// (e) EL MOTIU 'font' NO ÉS EL NOSTRE LLINDAR. La renda la calla l'INE, no nosaltres: hi ha
	//     municipis per sota del llindar amb renda i per sobre sense. Si un dia el patró es
	//     tornés el del llindar, aquest text hauria de canviar (ens atribuiria una prudència que
	//     no és nostra) — i aquesta guarda cau per obligar-hi.
	{
		const senseRenda = Object.entries(govern).filter(
			([, g]) => g.metrics?.renda_neta_persona && g.metrics.renda_neta_persona.valor === null
		);
		ok(senseRenda.length > 0, `cap municipi sense renda: el motiu 'gov_denom_font' no s'exerceix`);
		ok(
			senseRenda.some(([i]) => (catMunis[i]?.values?.poblacio ?? 0) >= GOVERN_DENOM_MIN_N),
			`tots els municipis sense renda són per sota del llindar mínim N: el motiu declarat ` +
				`('la font no la publica') ja no distingiria de 'gov_denom_minn'`
		);
	}

	// (f) EL DENOMINADOR MAI POT SER MÉS GRAN QUE LA COMARCA, als 947 i a totes les mètriques
	//     (fins avui això només s'exercia a Barcelona). És la condició que fa que la frase «N dels
	//     T municipis de la comarca» no pugui sortir absurda.
	for (const [i, g] of Object.entries(govern)) {
		const tot = comarcaSize[g.comarca] ?? 0;
		ok(tot > 0, `${i}: comarca '${g.comarca}' sense municipis a l'agrupació territorial`);
		for (const k of GOVERN_RANK_KEYS) {
			const cell = g.metrics?.[k];
			if (!cell) continue;
			ok(
				cell.n_amb_dada <= tot,
				`${i}/${k}: n_amb_dada ${cell.n_amb_dada} > municipis de ${g.comarca} (${tot})`
			);
			if (cell.n_amb_dada < tot) nDenomExplicat++;
		}
	}
	ok(nDenomExplicat > 0, `cap cel·la amb denominador incomplet: la línia nova no s'exerciria mai`);

	// (g) LA POBLA, l'àncora de Bea: nacionalitat «6 de 27» AMB explicació (27 < 31) i vidre
	//     «17 de 31» SENSE (no li'n cal). Si això s'inverteix, la pantalla explicaria de més o de
	//     menys exactament on Bea mirarà.
	const bergTot = comarcaSize['Berguedà'] ?? 0;
	ok(bergTot === 31, `el Berguedà hauria de tenir 31 municipis a l'agrupació, en té ${bergTot}`);
	ok(
		govern[POBLA]?.metrics?.pct_nacionalitat_estrangera?.n_amb_dada === 27,
		`la nacionalitat de la Pobla hauria de ser «de 27» (4 munis sota el llindar)`
	);
	ok(
		govern[POBLA]?.metrics?.vidre_hab?.n_amb_dada === bergTot,
		`el vidre de la Pobla hauria de ser «de ${bergTot}» (cobertura sencera, sense explicació)`
	);
}

// ── R-PINTA · LES DUES REFERÈNCIES, AMB EL SEU DENOMINADOR I SENSE INTERCANVIAR-LOS ─────────
// Vot de Bea (2026-07-31): «farem B+D» → cada targeta amb rang pinta la PONDERADA DE CATALUNYA
// (ancoratge oficial) i la MEDIANA DE LA COMARCA (els iguals, mateix perímetre que el rang).
// Doctrina vinculant al capçal de `semantic/metrics.yml`, bloc «QUINES ES PINTEN».
//
// Aquesta secció no vigila estil: vigila que no es publiqui una PROCEDÈNCIA FALSA. Una mediana
// i una ponderada tenen denominadors de naturalesa diferent («N municipis» vs «N unitats del
// seu pes»), i el brief donava per fet que tota ponderada es diu «sobre N habitants». És fals a
// dues de les nou mètriques amb rang: `pct_noprincipal` es pondera per HABITATGES (`hab_total`)
// i `index_envelliment` per MENORS DE 15 (`pob_0_14`). Escriure «habitants» allà seria mentir
// amb la mateixa cara amb què el 500 d'Idescat faria semblar tots els municipis un 4,4 % millors.
//
// La mecànica viu a `governReferences` (kpis.js), funció pura IMPORTADA aquí: la guarda
// l'exerceix sobre els 947 × 9 en comptes de deduir-ho del marcatge.
let nRefsPintades = 0;
let nRefsPonderadaNoHab = 0;
{
	// (a) CABLATGE: les referències es pinten des del snippet compartit del rang (un sol lloc
	//     per als tres punts que en pinten) i el component no en fabrica cap.
	ok(
		/import\s*\{[\s\S]*?\bgovernReferences\b[\s\S]*?\}\s*from\s*'\$lib\/govern\/kpis'/.test(pageSrc),
		`la fitxa no importa 'governReferences': pintaria referències fora de la font única`
	);
	ok(
		/\{@const refs = refsPintades\(cell, key\)\}/.test(pageSrc),
		`les referències no es resolen dins el snippet compartit del rang: tornarien a divergir`
	);
	ok(
		(pageSrc.match(/refsPintades\(/g) ?? []).length === 2,
		`'refsPintades' es crida des de més d'un lloc: el marcatge de les referències es duplicaria`
	);
	ok(
		(pageSrc.match(/class="gov-kpi__refv"/g) ?? []).length === 1,
		`hi ha marcatge de referència duplicat fora del snippet (tornaria a divergir)`
	);
	// El denominador es pinta en un element PROPI i VISIBLE. Amagar-lo amb CSS (o fondre'l amb
	// el rètol) tornaria a deixar una xifra sense procedència a la pantalla amb el codi verd:
	// un `opacity: 0` no és una decisió d'estil, és retirar la procedència.
	ok(
		pageSrc.includes('class="gov-kpi__refd"'),
		`el denominador de la referència no té element propi: no es podria vigilar que es vegi`
	);
	{
		const refdCss = (pageSrc.match(/\.gov-kpi__refd\s*\{[^}]*\}/g) ?? []).join(' ');
		ok(refdCss.length > 0, `.gov-kpi__refd sense estil: podria heretar-ne un que l'amagui`);
		ok(
			!/display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*(?:0|0?\.0+)\s*[;}]|font-size\s*:\s*0\s*[;}]/.test(
				refdCss
			),
			`el denominador de la referència s'amaga amb CSS: seria una xifra sense procedència`
		);
	}

	// (b) i18n: cada rètol i cada denominador declarats existeixen a ca+es I es pinten.
	const DENOM_KEYS = [...new Set([GOVERN_REF_DENOM_MUNIS, ...Object.values(GOVERN_PES_DENOM)])];
	for (const k of ['gov_ref_comarca', 'gov_ref_catalunya', ...DENOM_KEYS]) {
		ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
		ok(pageSrc.includes(k), `la clau '${k}' es declara a kpis.js però no es pinta enlloc`);
	}
	// …i cada denominador porta el seu PARÀMETRE: una xifra sense el seu {n} no és procedència.
	for (const k of DENOM_KEYS) {
		ok(
			/\{n\}/.test(String(ca[k])) && /\{n\}/.test(String(es[k])),
			`el denominador '${k}' no porta la seva xifra {n}: seria una referència sense procedència`
		);
	}

	// (c) ELS DOS NOMS NO S'INTERCANVIEN. La guarda és sobre el TEXT, perquè el risc real és una
	//     passada de copy que digui «habitants» sota una mediana (o «municipis» sota la
	//     ponderada) i deixi el codi verd.
	const diu = (k, re) => re.test(`${ca[k]} ${es[k]}`);
	ok(
		diu(GOVERN_REF_DENOM_MUNIS, /municipis|municipios/i),
		`el denominador de la MEDIANA no diu municipis`
	);
	ok(
		!diu(GOVERN_REF_DENOM_MUNIS, /habitants|habitantes/i),
		`el denominador de la MEDIANA parla d'habitants: una mediana es diu sobre MUNICIPIS`
	);
	for (const [pes, k] of Object.entries(GOVERN_PES_DENOM)) {
		ok(
			!diu(k, /municipis|municipios/i),
			`el denominador de la PONDERADA per '${pes}' parla de municipis: una ponderada mai es ` +
				`diu sobre municipis`
		);
	}
	ok(
		diu(GOVERN_PES_DENOM.poblacio, /habitants|habitantes/i),
		`la ponderada per població no diu habitants`
	);
	// Els dos pesos que NO són gent han de dir una altra cosa que «habitants»: és tota la raó
	// per la qual el denominador es deriva de `pes_ponderada` i no s'escriu una vegada per a totes.
	ok(
		!diu(GOVERN_PES_DENOM.hab_total, /habitants|habitantes/i) &&
			diu(GOVERN_PES_DENOM.hab_total, /habitatges|viviendas/i),
		`la ponderada per 'hab_total' (habitatges) es diu en habitants: seria FALSA a pct_noprincipal`
	);
	ok(
		!diu(GOVERN_PES_DENOM.pob_0_14, /habitants|habitantes/i) &&
			diu(GOVERN_PES_DENOM.pob_0_14, /menors|menores/i),
		`la ponderada per 'pob_0_14' (menors de 15) es diu en habitants: seria FALSA a l'envelliment`
	);

	// (d) L'ESTRATIFICADA PER FRANJA NO ARRIBA A LA PANTALLA (doctrina: se serveix, no es pinta).
	//     Es mira el CODI sense comentaris — el comentari que explica per què no es pinta ha de
	//     poder anomenar-la sense fer caure la guarda.
	const codeOnly = pageSrc
		.replace(/<!--[\s\S]*?-->/g, ' ')
		.replace(/\/\*[\s\S]*?\*\//g, ' ')
		.replace(/(^|[^:])\/\/[^\n]*/g, '$1 ');
	for (const camp of ['mediana_franja', 'n_franja', 'franja_poblacio']) {
		ok(
			!codeOnly.includes(camp),
			`'${camp}' es llegeix al codi de la fitxa: l'estratificada per mida NO es pinta ` +
				`(la comarca explica millor que la franja a 8 de les 9 mètriques amb rang)`
		);
	}
	ok(
		!ca.gov_ref_comarca.match(/franja/i) && !es.gov_ref_comarca.match(/franja/i),
		`el rètol de la referència comarcal parla de franja: no és el que es pinta`
	);

	// (e) TOT PES SERVIT TÉ NOM. Un pes nou de Sondeig sense entrada a GOVERN_PES_DENOM faria
	//     DESAPARÈIXER la ponderada d'aquella mètrica en silenci. Ha de fer caure el CI.
	const pesosServits = new Set();
	for (const g of Object.values(govern)) {
		for (const cell of Object.values(g.metrics ?? {})) {
			if (cell.ponderada_catalunya != null) pesosServits.add(cell.pes_ponderada);
		}
	}
	for (const p of pesosServits) {
		ok(
			!!GOVERN_PES_DENOM[p],
			`el mart pondera per '${p}' i GOVERN_PES_DENOM no el sap nomenar: aquesta referència ` +
				`desapareixeria de la targeta sense dir-ho`
		);
	}

	// (f) LES 947 × 9 CEL·LES, EXERCIDES. Cap referència sense denominador; la mediana sempre en
	//     municipis i sobre el MATEIX conjunt que ordena el rang; la ponderada mai en municipis i
	//     sempre sobre el denominador que serveix el mart. I cap xifra recalculada al front.
	for (const [i, g] of Object.entries(govern)) {
		for (const [k, cell] of Object.entries(g.metrics ?? {})) {
			if (cell.rang == null) continue;
			const refs = governReferences(cell);
			for (const r of refs) {
				nRefsPintades++;
				ok(
					Number.isFinite(r.value),
					`${i}/${k}: referència '${r.id}' sense xifra`
				);
				ok(
					!!r.denomKey && Number.isFinite(r.denom) && r.denom > 0,
					`${i}/${k}: referència '${r.id}' PINTADA SENSE DENOMINADOR — viola C6 §8.1`
				);
				if (r.tipus === 'mediana') {
					ok(
						r.denomKey === GOVERN_REF_DENOM_MUNIS && r.denom === cell.n_amb_dada,
						`${i}/${k}: la mediana no es diu sobre els ${cell.n_amb_dada} municipis del rang`
					);
					ok(
						r.value === cell.mediana_comarca,
						`${i}/${k}: la mediana pintada no és la del mart (s'estaria calculant al front)`
					);
				} else {
					ok(
						r.denomKey !== GOVERN_REF_DENOM_MUNIS &&
							r.denom === cell.hab_ponderada_catalunya,
						`${i}/${k}: la ponderada no es diu sobre el seu propi denominador`
					);
					ok(
						r.value === cell.ponderada_catalunya,
						`${i}/${k}: la ponderada pintada no és la del mart (s'estaria calculant al front)`
					);
					if (GOVERN_PES_DENOM[cell.pes_ponderada] !== GOVERN_PES_DENOM.poblacio)
						nRefsPonderadaNoHab++;
				}
			}
			// La targeta amb rang no es pot quedar MUDA de referències: la mediana comarcal hi és
			// sempre (mateix GROUP BY que el rang). Si un dia no hi fos, es veuria aquí.
			ok(refs.length >= 1, `${i}/${k}: targeta amb rang i CAP referència pintable`);
			ok(
				refs.length === (k === PRESENCIA_KEY ? 1 : 2),
				`${i}/${k}: ${refs.length} referències (s'esperen ${k === PRESENCIA_KEY ? 1 : 2})`
			);
			// El plural del copy («sobre N municipis») ha de ser cert: amb 1 sol municipi la
			// frase seria gramaticalment falsa i, pitjor, un rang «1 de 1» sense sentit.
			ok(
				cell.n_amb_dada >= 2,
				`${i}/${k}: n_amb_dada = ${cell.n_amb_dada} — «sobre 1 municipis» seria fals`
			);
		}
	}
	ok(nRefsPintades > 0, `cap referència pintable als 947: la secció no s'exerciria`);
	ok(
		nRefsPonderadaNoHab > 0,
		`cap ponderada amb un pes que no siguin habitants: la distinció que fa honesta la línia ` +
			`(habitatges, menors de 15) no s'estaria exercint`
	);

	// (g) `poblacio` NO TÉ PONDERADA i això NO és un forat: la seva targeta es queda amb la
	//     mediana comarcal i prou. Als 947, sempre exactament una referència i mai un buit.
	for (const [i, g] of Object.entries(govern)) {
		const cell = g.metrics?.[PRESENCIA_KEY];
		if (!cell || cell.rang == null) continue;
		ok(
			cell.ponderada_catalunya === null,
			`${i}: 'poblacio' amb ponderada (${cell.ponderada_catalunya}): la pregunta no existeix ` +
				`(seria la seva pròpia mida) i el contracte diu que és NULL`
		);
		const refs = governReferences(cell);
		ok(
			refs.length === 1 && refs[0].id === 'comarca',
			`${i}: la capçalera de presència hauria de pintar NOMÉS la mediana comarcal`
		);
	}

	// (h) L'ÀNCORA DE BEA — la Pobla de Lillet, vidre: 48,6 amb el Berguedà a 49,8 i Catalunya a
	//     22,9. És el cas que justifica pintar-ne DUES («normal aquí, el doble que a Catalunya»):
	//     si un dia les dues xifres convergissin, la targeta deixaria de dir això i s'hauria de
	//     mirar el disseny un altre cop.
	{
		const vidre = govern[POBLA]?.metrics?.vidre_hab;
		ok(!!vidre, `la Pobla sense cel·la de vidre: l'àncora de la decisió B+D no s'exerciria`);
		if (vidre) {
			const [comarcal, catalana] = governReferences(vidre);
			ok(
				comarcal?.id === 'comarca' && catalana?.id === 'catalunya',
				`l'ordre de les referències ha canviat: la comarcal va PRIMERA (comparteix perímetre ` +
					`amb el «k de n» que té just a sobre)`
			);
			ok(
				Math.abs(comarcal.value - 49.8) < 0.05 && Math.abs(catalana.value - 22.9) < 0.05,
				`el vidre de la Pobla ja no compara 49,8 (Berguedà) amb 22,9 (Catalunya): ` +
					`${comarcal?.value} / ${catalana?.value}`
			);
			ok(
				catalana.denomKey === GOVERN_PES_DENOM.poblacio_residus,
				`el vidre es pondera per la població del dataset de l'ARC i el denominador no ho diu`
			);
			ok(
				Math.abs(vidre.valor - 48.6) < 0.05 && vidre.valor > catalana.value * 1.9,
				`el cas fundacional («el doble que a Catalunya») ja no es dona amb la dada servida`
			);
		}
		// I el cas que desmenteix el brief: el % d'habitatges no principals es pondera per
		// HABITATGES. Si algun dia el mart canviés el pes, el text hauria de canviar amb ell.
		const nop = govern[POBLA]?.metrics?.pct_noprincipal;
		ok(
			nop?.pes_ponderada === 'hab_total',
			`pct_noprincipal ja no es pondera per habitatges: el denominador pintat s'ha de revisar`
		);
		ok(
			governReferences(nop).find((r) => r.tipus === 'ponderada')?.denomKey ===
				GOVERN_PES_DENOM.hab_total,
			`la ponderada de pct_noprincipal no es diu en habitatges`
		);
	}
}

if (fails.length) {
	console.error('VERIFICACIÓ tauler de dades: FALLA');
	for (const f of fails) console.error(`  [x] ${f}`);
	process.exit(1);
}
const nCards = GOVERN_KPIS.length;
const nRank = GOVERN_KPIS.filter((k) => GOVERN_RANK_KEYS.includes(k.key)).length;
const nTend = Object.keys(tauler.municipis?.[POBLA]?.tendencia ?? {}).length;
console.log(
	`VERIFICACIÓ tauler de dades: OK — V3: ${nCards} targetes + capçalera de presència ` +
		`(padró+ETCA junts, font i frescor), totes amb font O fórmula i amb frescor; ` +
		`${nRank} amb rang comarcal LLEGIT del mart (+ el padró a la capçalera), paritat ` +
		`dataset↔mart a la Pobla; barres apilades amb LES 8 XIFRES a la dada i cablejades ` +
		`(particions = padró exacte a tot el dataset); HUT al turisme amb font; E13 alineada ` +
		`amb la doctrina (llindar ${E13_LLINDAR}, Sant Jaume exercit); ${nTend} mètriques amb ` +
		`tendència (cap fletxa sense període, cap 'sense_serie' sense motiu, atur amb les DUES ` +
		`comparacions i el «<5» com a interval); naixement amb el límit «foto, no sèrie» declarat ` +
		`UNA vegada i l'evolució de nacionalitat etiquetada com a tal; «sense procés automàtic» ` +
		`fora de les targetes (viu a /metodologia); duplicats morts (números clau, padró gran); ` +
		`i18n ca/es complet i sense claus òrfenes, index_turisme fora. ` +
		`P-947: ${Object.keys(govern).length} munis amb rang, i a Barcelona (fora del pilot) el ` +
		`rang es de la SEVA comarca (Barcelones) i el shard hi serveix l'atur. ` +
		`W1: el selector de la fitxa es construeix del CATALEG (${nMunisCataleg} munis, ` +
		`${nMunisCataleg} slugs distints, cap col·lisió; ${nAmbArticle} noms amb article on la clau ` +
		`d'ordenació NO mou la URL) i la guarda de col·lisió del build segueix al loader. ` +
		`W5: la porta de «Llegeix la comarca» és clicable i porta a /comarca; cap xifra de porta ` +
		`escrita al copy (es compten de l'agrupació: ${nComarques} comarques, ` +
		`${Object.keys(territori).length} municipis, cap sense comarca). ` +
		`B2: el hero de la home no porta cap xifra escrita a ma (${nHeroLabels + 1} cotes, les dues ` +
		`numeriques comptades del loader) i «31 municipis» no hi es. ` +
		`B3: el rang es pinta des d'UN snippet als tres llocs; ${nDenomExplicat} cel·les amb ` +
		`denominador incomplet porten explicacio, i els tres motius declarats s'han contrastat amb ` +
		`els 947 (llindar minim N = ${GOVERN_DENOM_MIN_N}, el mateix del transform; cap muni sense ` +
		`% d'origen hi arriba i cap que hi arribi se'l queda; sense index d'envelliment nomes on ` +
		`pob_0_14 = 0; la renda la calla la FONT, no el nostre llindar). La Pobla: nacionalitat ` +
		`«de 27» amb explicacio, vidre «de 31» sense. ` +
		`R-PINTA (B+D): ${nRefsPintades} referencies pintables als 947, TOTES amb el seu ` +
		`denominador — la mediana sobre els MUNICIPIS del rang, la ponderada sobre el seu propi ` +
		`pes i mai sobre municipis; ${nRefsPonderadaNoHab} ponderades amb un pes que NO son ` +
		`habitants (habitatges a pct_noprincipal, menors de 15 a l'envelliment) amb el nom ` +
		`correcte; 'poblacio' sense ponderada pinta nomes la comarcal als 947, sense cap buit; ` +
		`l'estratificada per franja no arriba al codi de la fitxa; ancora de la Pobla intacta ` +
		`(vidre 48,6 · Berguedà 49,8 · Catalunya 22,9).`
);
