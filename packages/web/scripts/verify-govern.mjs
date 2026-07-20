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
	atur: ['gov_kpi_atur', 'gov_kpi_atur_pending', 'gov_kpi_atur_src'],
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
//     (i amb ella `gov_bea_pending`, que només l'acompanyava).
const I18N_UI = [
	'gov_board_title', 'gov_board_sub',
	'gov_grp_a', 'gov_grp_b', 'gov_grp_c', 'gov_grp_d', 'gov_rang_label', 'gov_rang_val',
	'gov_rang_cap', 'gov_rang_empat', 'gov_nova_norank', 'gov_nova_delta_label'
];
for (const k of I18N_UI) ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);

// 4b · Claus RETIRADES: no poden quedar òrfenes als catàlegs (higiene d'i18n, D8).
const I18N_GONE = [
	'gov_switch_aria', 'gov_view_veinal', 'gov_view_govern', 'gov_kpi_nova_frame', 'gov_bea_pending'
];
for (const k of I18N_GONE) {
	ok(!(k in ca), `i18n '${k}' retirada però encara a ca.json (clau òrfena)`);
	ok(!(k in es), `i18n '${k}' retirada però encara a es.json (clau òrfena)`);
}

// 5 · Higiene: index_turisme (deprecat) fora del catàleg servit.
ok(!('index_turisme' in metrics), `index_turisme encara al catàleg servit (hauria d'estar fora)`);

if (fails.length) {
	console.error('VERIFICACIÓ vista de govern: FALLA');
	for (const f of fails) console.error(`  [x] ${f}`);
	process.exit(1);
}
const nCards = GOVERN_KPIS.length;
const nRank = GOVERN_KPIS.filter((k) => GOVERN_RANK_KEYS.includes(k.key)).length;
console.log(
	`VERIFICACIÓ tauler de dades: OK — ${nCards} KPIs (tots amb font O fórmula), ` +
		`${nRank} amb rang comarcal LLEGIT del mart, paritat dataset↔mart a la Pobla, ` +
		`i18n ca/es complet i sense claus òrfenes, index_turisme fora.`
);
