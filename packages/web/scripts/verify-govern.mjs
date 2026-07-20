#!/usr/bin/env node
/**
 * verify-govern.mjs — verificador OFFLINE del TAULER DE DADES (D5, esmenat a D8 · C6 §10.7).
 *
 * D8 · E1: ja no hi ha vista de govern separada ni commutador — el tauler ÉS la fitxa. El
 * verificador segueix guardant les mateixes invariants, ara sobre la vista única.
 *
 * Guarda la REGLA DE FERRO de Bea (C6 §8.1): CAP targeta de KPI del tauler de govern pot
 * quedar sense línia de procedència (font O fórmula). A més comprova que el rang «k de n»
 * es LLEGEIX del mart (govern.json) i mai es fabrica al front, i que les xifres del rang
 * coincideixen amb les del dataset (paritat, C6 §10.1).
 *
 * Font única de l'ordre/composició del tauler: `src/lib/govern/kpis.js`, IMPORTADA aquí
 * (no es duplica → no deriva). Offline, sense xarxa. Apte per a CI (data-job).
 *
 *   node scripts/verify-govern.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { GOVERN_KPIS, GOVERN_RANK_KEYS, provenanceLine } from '../src/lib/govern/kpis.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(__dirname, '../../..');
const WEB = resolve(__dirname, '..');

const read = (p) => JSON.parse(readFileSync(p, 'utf8'));
const dataset = read(resolve(REPO, 'data/web/municipis.bergueda.json'));
const govern = read(resolve(REPO, 'data/web/govern.bergueda.json'));
const tauler = read(resolve(REPO, 'data/web/tauler.bergueda.json'));
const ca = read(resolve(WEB, 'messages/ca.json'));
const es = read(resolve(WEB, 'messages/es.json'));

const metrics = dataset.metrics;
const POBLA = '08166';
const fails = [];
const ok = (cond, msg) => {
	if (!cond) fails.push(msg);
};

// Missatges i18n de procedència fixos de cada `kind` no-mètric (han d'existir a ca+es).
const I18N_PROV = {
	etca: ['muni_num_etca', 'muni_etca_srcline', 'muni_sense_dada_oficial'],
	// D9: l'atur ja no és «pendent»; el que ha d'existir és l'etiqueta, la font i el text de
	// l'absència honesta (`gov_atur_absent`) per si un dia l'artefacte del tauler no hi és.
	atur: ['gov_kpi_atur', 'gov_kpi_atur_src', 'gov_atur_absent'],
	serveis: ['gov_kpi_serveis', 'gov_kpi_serveis_a', 'gov_kpi_serveis_b']
};

// 1 · CADA KPI del tauler té una línia de procedència (font O fórmula).
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
	} else if (kpi.kind === 'serveis') {
		ok(!!metrics['serveis_estab']?.source, `KPI serveis: 'serveis_estab' sense font`);
		for (const k of I18N_PROV.serveis) ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
	} else if (kpi.kind === 'etca' || kpi.kind === 'atur') {
		for (const k of I18N_PROV[kpi.kind]) ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
	}
}

// 2 · Les 7 claus rankejables existeixen al catàleg (i el mart les rankeja).
for (const k of GOVERN_RANK_KEYS) ok(!!metrics[k], `clau rankejable '${k}' absent del catàleg`);

// 3 · El rang es LLEGEIX del mart i quadra amb el dataset (paritat). Cap KPI de rang buit
//     hauria de ser NULL a la Pobla (té dada a tots 7).
const gp = govern[POBLA];
ok(!!gp, `govern.json sense la Pobla (${POBLA})`);
if (gp) {
	ok(gp.comarca === 'Berguedà', `la Pobla no surt al Berguedà al govern.json`);
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

// 4 · i18n del tauler presents a ca+es. D8 · E1: el commutador ja no existeix (una sola vista),
//     així que `gov_switch_aria`/`gov_view_*` han desaparegut; E10 retira `gov_kpi_nova_frame`
//     (i amb ella `gov_bea_pending`, que només l'acompanyava). D9 hi suma la tendència, la
//     frescor i l'atur servit.
const I18N_UI = [
	'gov_board_title', 'gov_board_sub',
	'gov_grp_a', 'gov_grp_b', 'gov_grp_c', 'gov_grp_d', 'gov_rang_label', 'gov_rang_val',
	'gov_rang_cap', 'gov_rang_empat', 'gov_nova_norank',
	// D9 · tendència (E6/E11)
	'gov_tend_sense_serie', 'gov_tend_no_declarada', 'gov_tend_cmp_mes', 'gov_tend_cmp_any',
	'gov_tend_cmp_finestra', 'gov_tend_indeterminat', 'gov_tend_interval',
	'gov_tend_u_persones', 'gov_tend_u_punts',
	// D9 · frescor per targeta (E5)
	'gov_frescor_mensual', 'gov_frescor_anual', 'gov_frescor_puntual', 'gov_frescor_irregular',
	'gov_frescor_nd', 'gov_frescor_carrega', 'gov_frescor_sense_proces', 'gov_frescor_amb_proces',
	// D9 · atur servit (E4)
	'gov_atur_u', 'gov_atur_masked', 'gov_atur_absent', 'gov_atur_serie_cap', 'gov_atur_serie_alt'
];
for (const k of I18N_UI) ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);

// 4b · Claus RETIRADES: no poden quedar òrfenes als catàlegs (higiene d'i18n, D8).
//      D9 en retira dues més: `gov_kpi_atur_pending` (l'atur ja NO és pendent: es serveix) i
//      `gov_nova_delta_label`, que portava el període ESCRIT AL COPY («variació 2021→») quan
//      ara el període surt de la dada (`periode_anterior`/`periode_actual`).
const I18N_GONE = [
	'gov_switch_aria', 'gov_view_veinal', 'gov_view_govern', 'gov_kpi_nova_frame', 'gov_bea_pending',
	'gov_kpi_atur_pending', 'gov_nova_delta_label'
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

// 6 · FRESCOR PER TARGETA (E5): cada KPI de mètrica ha de poder dir de quan és la seva xifra.
for (const kpi of GOVERN_KPIS) {
	if (kpi.kind !== 'metric') continue;
	const f = metrics[kpi.key]?.frescor;
	ok(!!f, `KPI '${kpi.key}': sense bloc 'frescor' al catàleg — la targeta no podria datar-se (E5)`);
}

// 7 · TENDÈNCIA (E6): el tauler ha d'existir amb la Pobla, i CAP entrada pot trencar les regles.
const tp = tauler.municipis?.[POBLA];
ok(!!tp, `tauler.bergueda.json sense la Pobla (${POBLA})`);
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

	// 7c · POBLACIÓ I FRANGES: 'sense_serie' amb motiu (E11 — límit de la FONT, no pendent nostre).
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

// ── D11 · LLOC DE NAIXEMENT (E11) ──────────────────────────────────────────────────────────
// Aquesta secció existeix perquè la troballa de D11 no pugui tornar. D9 va tancar l'E11 de Bea
// amb una premissa falsa («el mart només té nacionalitat») i el tauler va quedar sense CAP
// mètrica de lloc de naixement tot i que les quatre arribaven servides al web. Un test que
// només mirés el que el tauler pinta no ho hauria vist mai: el forat era el que NO pintava.
// Per això la guarda es planta a l'altre costat — de la DADA cap al descriptor.
const NAIX_KEYS = [
	'poblacio_nascuda_catalunya',
	'poblacio_nascuda_resta_espanya',
	'poblacio_nascuda_estranger',
	'pct_nascuda_estranger'
];
const kpiFor = (k) => GOVERN_KPIS.find((x) => x.kind === 'metric' && x.key === k);

// 9a · Si la dada hi és, el tauler l'ha de pintar. Aquesta és LA guarda de D11.
for (const k of NAIX_KEYS) {
	const v = dataset.municipis[POBLA]?.values?.[k];
	if (v == null) continue; // sense dada no hi ha res a exigir (el «no» és una resposta vàlida)
	ok(
		!!kpiFor(k),
		`'${k}' té dada a la Pobla (${v}) i el tauler NO la pinta — E11 de Bea demana lloc de ` +
			`naixement, i tenir-lo servit i no ensenyar-lo és la regressió que D11 va tancar`
	);
}

// 9b · La foto NO es pot vendre com a sèrie. Cada targeta de lloc de naixement declara el seu
//      límit, i cap d'elles pren prestada la tendència d'una sèrie de NACIONALITAT (que mesura
//      una altra gent: qui es naturalitza en surt sense marxar del poble).
for (const k of NAIX_KEYS) {
	const kpi = kpiFor(k);
	if (!kpi) continue;
	ok(
		!!kpi.note,
		`KPI '${k}': sense nota de límit — la foto es llegiria com si tingués evolució`
	);
	ok(
		!/nacionalitat|estrangera/.test(kpi.trendKey ?? kpi.key),
		`KPI '${k}': agafa la tendència de '${kpi.trendKey}', que és una sèrie de NACIONALITAT ` +
			`presentada sota una etiqueta de lloc de naixement`
	);
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
const pageSrc = readFileSync(
	resolve(WEB, 'src/routes/municipi/[slug]/+page.svelte'),
	'utf8'
);
for (const kpi of GOVERN_KPIS) {
	if (!kpi.note) continue;
	ok(!!ca[kpi.note] && !!es[kpi.note], `i18n de la nota '${kpi.note}' absent (ca/es)`);
	ok(
		pageSrc.includes(kpi.note),
		`la nota '${kpi.note}' es declara a kpis.js però no està cablejada a la fitxa (GOV_NOTE)`
	);
}

if (fails.length) {
	console.error('VERIFICACIÓ vista de govern: FALLA');
	for (const f of fails) console.error(`  [x] ${f}`);
	process.exit(1);
}
const nCards = GOVERN_KPIS.length;
const nRank = GOVERN_KPIS.filter((k) => GOVERN_RANK_KEYS.includes(k.key)).length;
const nTend = Object.keys(tauler.municipis?.[POBLA]?.tendencia ?? {}).length;
const nNaix = NAIX_KEYS.filter((k) => !!kpiFor(k)).length;
console.log(
	`VERIFICACIÓ tauler de dades: OK — ${nCards} KPIs (tots amb font O fórmula i amb frescor), ` +
		`${nRank} amb rang comarcal LLEGIT del mart, paritat dataset↔mart a la Pobla, ` +
		`${nTend} mètriques amb tendència (cap fletxa sense període, cap 'sense_serie' sense motiu, ` +
		`atur amb les DUES comparacions i el «<5» com a interval), ` +
		`${nNaix}/${NAIX_KEYS.length} mètriques de lloc de naixement pintades amb el seu límit ` +
		`declarat (foto, no sèrie) i l'evolució de nacionalitat etiquetada com a tal, ` +
		`i18n ca/es complet i sense claus òrfenes, index_turisme fora.`
);
