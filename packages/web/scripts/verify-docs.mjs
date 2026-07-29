#!/usr/bin/env node
/**
 * verify-docs.mjs — verificador OFFLINE de les pàgines de DOCUMENTACIÓ del contracte:
 * el GLOSSARI (`/glossari`) i la METODOLOGIA (`/metodologia`). P-DOC (2026-07-27).
 *
 * Neix de dos bugs reals de la mateixa família (la llista fixa que descarta en silenci /
 * la clau fixa que peta en render):
 *
 *  1) GLOSSARI MUT: la pàgina agrupava per una DIM_ORDER escrita a mà sense `treball` ni
 *     `origen` → l'atur registrat i les 8 mètriques d'origen es publicaven al tauler i el
 *     diccionari les DESCARTAVA EN SILENCI (capçalera «26 indicadors» amb 35 publicables).
 *     Guarda: si el dataset porta una dimensió amb mètriques publicables que el glossari no
 *     llista, AQUÍ CAU — la propera dimensió nova fa soroll, no silenci.
 *
 *  2) EL 500 LATENT de metodologia: la pàgina renderitzava `dataset.metrics[key]` sense
 *     guarda → una clau fantasma als blocs petava el render AMB EL BUILD VERD (va passar
 *     amb index_turisme). Ara la pàgina filtra i AQUÍ CAU: vermell a la verificació local,
 *     mai a la pàgina.
 *
 * Font única de composició (mateix patró que verify-govern.mjs ↔ kpis.js):
 *  · glossari    → `src/lib/glossari/dims.js` (GLOSSARI_DIMS + GLOSSARI_HIDDEN)
 *  · metodologia → `src/lib/metodologia/blocs.js` (METODOLOGIA_BLOCS)
 *  · tauler      → `src/lib/govern/kpis.js` (per exigir que cap targeta viva quedi sense fitxa)
 *
 * Offline, sense xarxa. Apte per a CI (job web).
 *
 *   node scripts/verify-docs.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { GLOSSARI_DIMS, GLOSSARI_HIDDEN } from '../src/lib/glossari/dims.js';
import { GOVERN_KPIS } from '../src/lib/govern/kpis.js';
import { METODOLOGIA_BLOCS } from '../src/lib/metodologia/blocs.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(__dirname, '../../..');
const WEB = resolve(__dirname, '..');

const read = (p) => JSON.parse(readFileSync(p, 'utf8'));
const dataset = read(resolve(REPO, 'data/web/municipis.bergueda.json'));
const ca = read(resolve(WEB, 'messages/ca.json'));
const es = read(resolve(WEB, 'messages/es.json'));
const metrics = dataset.metrics;

const fails = [];
const ok = (cond, msg) => {
	if (!cond) fails.push(msg);
};

const hidden = new Set(GLOSSARI_HIDDEN);
const dims = new Set(GLOSSARI_DIMS);

// ── 1 · GLOSSARI: cap dimensió publicable descartada en silenci ─────────────────────────────
// Tota dimensió del dataset amb ≥1 mètrica NO amagada ha de ser a GLOSSARI_DIMS. Aquesta és LA
// guarda de P-DOC: sense ella, la propera dimensió nova del contracte desapareix del diccionari
// sense que res es posi vermell (com van desaparèixer `treball` i `origen`).
const perDim = new Map();
for (const def of Object.values(metrics)) {
	if (hidden.has(def.key)) continue;
	if (!perDim.has(def.dimension)) perDim.set(def.dimension, []);
	perDim.get(def.dimension).push(def.key);
}
for (const [dim, keys] of perDim) {
	ok(
		dims.has(dim),
		`glossari: la dimensió '${dim}' té ${keys.length} mètriques publicables (${keys.join(', ')}) ` +
			`i NO és a GLOSSARI_DIMS — el diccionari les descartaria EN SILENCI`
	);
}

// 1b · Cada dimensió llistada té la seva etiqueta i18n (ca+es) i està cablejada a la pàgina
//      (el mapa DIM_LABEL és codi: una dimensió sense entrada es pintaria amb la clau crua).
const gloSrc = readFileSync(resolve(WEB, 'src/routes/glossari/+page.svelte'), 'utf8');
for (const dim of GLOSSARI_DIMS) {
	const key = `glo_dim_${dim}`;
	ok(!!ca[key] && !!es[key], `glossari: i18n '${key}' absent (ca/es)`);
	ok(
		gloSrc.includes(key),
		`glossari: la dimensió '${dim}' no està cablejada a DIM_LABEL (+page.svelte no menciona '${key}')`
	);
}

// 1c · El recompte que la capçalera pot mostrar (deriva sol a la pàgina; aquí es deixa al log
//      per comparar amb el render — P-DOC: 26 → 35).
const nPublicables = [...perDim.values()].reduce((n, ks) => n + ks.length, 0);
const nDims = [...perDim.keys()].filter((d) => dims.has(d)).length;

// ── 2 · METODOLOGIA: cap clau fantasma, cap duplicat, emmarcament coherent ──────────────────
const seen = new Set();
for (const bloc of METODOLOGIA_BLOCS) {
	for (const key of bloc.keys) {
		// 2a · El 500 latent: una clau que el dataset no serveix NO pot quedar als blocs.
		ok(
			!!metrics[key],
			`metodologia: la clau '${key}' del bloc ${bloc.ref} NO és al dataset — la pàgina l'ometria ` +
				`(abans petava en render amb el build verd; ara ha de caure AQUÍ)`
		);
		ok(!seen.has(key), `metodologia: la clau '${key}' surt a més d'un bloc`);
		seen.add(key);
		// 2b · EMMARCAMENT (P-DOC): un bloc VIU no pot documentar una peça del model aparcat, i
		//      l'annex només pot documentar peces del model (les vives hi quedarien enterrades —
		//      el bug que P-DOC arregla: kg/kwh/vidre/restauració llegides com a «recerca aparcada»).
		if (bloc.annex) {
			ok(
				hidden.has(key),
				`metodologia: '${key}' és al bloc ANNEX ${bloc.ref} però NO és una peça del model ` +
					`(no és a GLOSSARI_HIDDEN) — una mètrica viva etiquetada «model aparcat»`
			);
		} else {
			ok(
				!hidden.has(key),
				`metodologia: '${key}' és una peça del model aparcat (GLOSSARI_HIDDEN) dins el bloc ` +
					`VIU ${bloc.ref} — l'annex és el seu lloc`
			);
		}
	}
}

// 2c · CAP TARGETA VIVA DEL TAULER SENSE FITXA metodològica en un bloc NO-annex. És la guarda
//      que fa que la PROPERA targeta nova del tauler no torni a quedar sense metodologia (la
//      forma del forat que P-DOC tanca: 10 targetes vives sense fitxa).
const fitxaViva = new Set(METODOLOGIA_BLOCS.filter((b) => !b.annex).flatMap((b) => b.keys));
const taulerKeys = new Set();
for (const kpi of GOVERN_KPIS) {
	if (kpi.kind === 'metric') taulerKeys.add(kpi.key);
	else if (kpi.kind === 'atur') taulerKeys.add('atur_registrat');
	else if (kpi.kind === 'serveis') {
		taulerKeys.add('serveis_estab');
		taulerKeys.add('restauracio_estab');
	}
	// kind 'etca': artefacte extern (no és mètrica del catàleg), documentat a la seva secció pròpia.
}
for (const key of taulerKeys) {
	ok(
		fitxaViva.has(key),
		`metodologia: la targeta VIVA del tauler '${key}' no té fitxa a cap bloc viu — ` +
			`el tauler la pinta i la metodologia no l'explica`
	);
}

// 2d · La doctrina del «<5» de l'atur i el caveat de vintages viatgen pel `note` del contracte:
//      si la fitxa els ha de dir, el contracte els ha de portar (i la pàgina ja pinta `note`).
ok(
	!!metrics.atur_registrat?.note?.ca && /<5|«<5»/.test(metrics.atur_registrat.note.ca),
	`metodologia: el 'note' d'atur_registrat no porta la doctrina del «<5» — la fitxa quedaria muda`
);
ok(
	!!metrics.rtc_per_100hab_viv?.note?.ca && /vintage/i.test(metrics.rtc_per_100hab_viv.note.ca),
	`metodologia: el 'note' de rtc_per_100hab_viv no declara la barreja de vintages`
);

// ── 3 · Higiene i18n: el copy L1/L2/L3 retirat amb P-DOC no pot quedar orfe als catàlegs ────
const I18N_GONE = [
	'met_kwh_what', 'met_kwh_how', 'met_vidre_what', 'met_vidre_how',
	'met_residus_what', 'met_residus_how', 'met_restauracio_what', 'met_restauracio_how',
	'met_turisme_what', 'met_turisme_how'
];
for (const k of I18N_GONE) {
	ok(!(k in ca), `i18n '${k}' retirada (P-DOC) però encara a ca.json (clau òrfena)`);
	ok(!(k in es), `i18n '${k}' retirada (P-DOC) però encara a es.json (clau òrfena)`);
}
// I les noves han d'existir (ca+es).
for (const k of ['met_how_directe', 'met_block_treball', 'met_block_serveis', 'met_block_vida']) {
	ok(!!ca[k] && !!es[k], `i18n '${k}' absent (ca/es)`);
}

if (fails.length) {
	console.error('VERIFICACIÓ glossari+metodologia: FALLA');
	for (const f of fails) console.error(`  [x] ${f}`);
	process.exit(1);
}
console.log(
	`VERIFICACIÓ glossari+metodologia: OK — glossari: ${nPublicables} indicadors publicables en ` +
		`${nDims} dimensions, cap dimensió del dataset descartada en silenci, etiquetes ca/es ` +
		`cablejades; metodologia: ${seen.size} fitxes en ${METODOLOGIA_BLOCS.length} blocs, cap ` +
		`clau fantasma ni duplicada, l'annex només amb peces del model i cap peça del model en ` +
		`bloc viu, ${taulerKeys.size}/${taulerKeys.size} targetes vives del tauler amb fitxa, ` +
		`«<5» i vintages al contracte, i18n net.`
);
