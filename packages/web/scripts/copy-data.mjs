#!/usr/bin/env node
/**
 * copy-data.mjs — prebuild: copia el dataset real dins de `static/` perquè el web el serveixi.
 *
 * Per què cal: la FONT de dades viu FORA de `packages/web`, a `data/web/municipis.bergueda.json`
 * (la genera Sondeig des dels marts; veure `tools/export_web_municipis.py`). SvelteKit/Vite
 * només serveixen actius des de `static/`, i el site és 100% prerenderitzat (adapter-static):
 * el `fetch('/data/…')` del loader s'executa en BUILD. Per tant el JSON ha de ser dins de
 * `static/` ABANS de `vite build`/`dev`. Aquest pas el hi copia, cross-platform (Node, sense
 * `cp`/`copy`), idempotent.
 *
 * Frontera honesta: el JSON és la font (de Sondeig); aquí NOMÉS el llegim i el copiem,
 * MAI el modifiquem. Mateix patró que la geometria (`static/geo/bergueda-municipis.geojson`).
 *
 * Si la font no existeix: avisem i fem fallback NO-FATAL (no trenquem el build de CI, que
 * corre sense els marts). Si ja hi ha una còpia prèvia, es manté; si no, el loader del mapa
 * en té el seu propi fallback documentat.
 *
 * Ús:  node scripts/copy-data.mjs       (l'invoca `prebuild`/`predev` via npm)
 */

import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// `packages/web/scripts` → arrel del repo són tres nivells amunt.
const REPO_ROOT = resolve(__dirname, '../../..');
const DEST_DIR = resolve(__dirname, '../static/data');

// Actius de dades a copiar (font → nom a static/data). El dataset és l'únic imprescindible;
// la validació ETCA és opcional (la genera `tools/validacio_etca.py`).
const FILES = [
	{ src: resolve(REPO_ROOT, 'data/web/municipis.bergueda.json'), name: 'municipis.bergueda.json' },
	{ src: resolve(REPO_ROOT, 'data/web/municipis.catalunya.json'), name: 'municipis.catalunya.json' },
	{ src: resolve(REPO_ROOT, 'data/web/etca-validacio.json'), name: 'etca-validacio.json' },
	{ src: resolve(REPO_ROOT, 'data/web/licitacions-bergueda.json'), name: 'licitacions-bergueda.json' },
	{ src: resolve(REPO_ROOT, 'data/web/lectures.bergueda.json'), name: 'lectures.bergueda.json' },
	{ src: resolve(REPO_ROOT, 'data/web/pernocta-catalunya.json'), name: 'pernocta-catalunya.json' },
	{ src: resolve(REPO_ROOT, 'data/web/municipis-territori.json'), name: 'municipis-territori.json' },
	{ src: resolve(REPO_ROOT, 'data/web/municipis-mirall.json'), name: 'municipis-mirall.json' },
	{ src: resolve(REPO_ROOT, 'data/web/indicadors-catalunya.json'), name: 'indicadors-catalunya.json' }
];

mkdirSync(DEST_DIR, { recursive: true });

/**
 * Catàleg de TOTS els municipis de Catalunya (947) derivat de la geometria oficial
 * `static/geo/catalunya-municipis.geojson` (props `{ine5, nom}`). És la base de «tota
 * Catalunya»: el cercador hi cerca i la fitxa hi resol QUALSEVOL slug → ine5 + nom (perquè
 * cada poble tingui pàgina, amb dada/rang on n'hi ha o un «sense dades encara» digne).
 *
 * Frontera honesta: NO és una dada de població ni cap xifra — només el cens de noms+codis,
 * la columna vertebral de navegació. La geometria SEMPRE és al repo (no depèn dels marts), així
 * que això és determinista i segur a CI. El slug es deriva del nom en RUNTIME (toSlug), no aquí,
 * perquè la lògica d'slug visqui en un sol lloc (`$lib/contract/slug`).
 */
function buildCataleg() {
	const geoPath = resolve(__dirname, '../static/geo/catalunya-municipis.geojson');
	if (!existsSync(geoPath)) {
		console.warn(`[copy-data] AVÍS: no s'ha trobat ${geoPath}; no es genera el catàleg de municipis.`);
		return;
	}
	const geo = JSON.parse(readFileSync(geoPath, 'utf8'));
	const cataleg = geo.features
		.map((f) => ({ ine5: String(f.properties.ine5), nom: String(f.properties.nom) }))
		.filter((m) => m.ine5 && m.nom)
		.sort((a, b) => a.nom.localeCompare(b.nom, 'ca'));
	const dest = resolve(DEST_DIR, 'municipis-cataleg.json');
	writeFileSync(dest, JSON.stringify(cataleg));
	const kb = (statSync(dest).size / 1024).toFixed(1);
	console.log(`[copy-data] OK: municipis-cataleg.json → static/data/ (${cataleg.length} munis, ${kb} kB)`);
}

buildCataleg();

/**
 * Agrupació territorial `comarques.json` derivada de `data/web/municipis-territori.json`
 * (muni→comarca→vegueria, exacte). És la base de les pàgines de comarca/vegueria i del breadcrumb
 * navegable: per a cada comarca, la seva vegueria i els seus municipis (ine5); per a cada vegueria,
 * les seves comarques. NO és cap dada de població; només estructura administrativa. El slug es deriva
 * dels noms en runtime (`toSlug`), no aquí.
 */
function buildComarques() {
	const terrPath = resolve(REPO_ROOT, 'data/web/municipis-territori.json');
	if (!existsSync(terrPath)) {
		console.warn(`[copy-data] AVÍS: no s'ha trobat ${terrPath}; no es genera comarques.json.`);
		return;
	}
	const terr = JSON.parse(readFileSync(terrPath, 'utf8'));
	const com = new Map(); // comarca → { nom, vegueria, ine5s:Set }
	const veg = new Map(); // vegueria → Set<comarca>
	for (const [ine5, t] of Object.entries(terr)) {
		if (!t.comarca) continue;
		if (!com.has(t.comarca)) com.set(t.comarca, { nom: t.comarca, vegueria: t.vegueria || '', ine5s: [] });
		com.get(t.comarca).ine5s.push(ine5);
		if (t.vegueria) {
			if (!veg.has(t.vegueria)) veg.set(t.vegueria, new Set());
			veg.get(t.vegueria).add(t.comarca);
		}
	}
	const coll = new Intl.Collator('ca');
	const out = {
		comarques: [...com.values()]
			.map((c) => ({ ...c, ine5s: c.ine5s.sort() }))
			.sort((a, b) => coll.compare(a.nom, b.nom)),
		vegueries: [...veg.entries()]
			.map(([nom, set]) => ({ nom, comarques: [...set].sort((a, b) => coll.compare(a, b)) }))
			.sort((a, b) => coll.compare(a.nom, b.nom))
	};
	const dest = resolve(DEST_DIR, 'comarques.json');
	writeFileSync(dest, JSON.stringify(out));
	console.log(
		`[copy-data] OK: comarques.json → static/data/ (${out.comarques.length} comarques, ${out.vegueries.length} vegueries)`
	);
}

buildComarques();

/**
 * Parteix `municipis.catalunya.json` (947 munis) en un fitxer PER MUNICIPI a `static/data/muni/<ine5>.json`
 * (només la fila `MunicipiRow`: ine5+nom+idescat6+values). Per què: la fitxa es prerenderitza per muni
 * (947×2) i, si carregués el dataset sencer (1,8 MB), cada pàgina l'incrustaria. Amb un fitxer per muni,
 * cada fitxa només incrusta el SEU (~2 kB) → client lleuger i build ràpid. Build-only (static/ és
 * gitignored). El catàleg de `metrics` segueix venint del dataset del Berguedà (mateix per a tots).
 */
function buildMuniSplit() {
	const src = resolve(REPO_ROOT, 'data/web/municipis.catalunya.json');
	if (!existsSync(src)) {
		console.warn(`[copy-data] AVÍS: no s'ha trobat ${src}; no es parteixen les fitxes per municipi.`);
		return;
	}
	const data = JSON.parse(readFileSync(src, 'utf8'));
	const muniDir = resolve(DEST_DIR, 'muni');
	mkdirSync(muniDir, { recursive: true });
	let n = 0;
	for (const [ine5, row] of Object.entries(data.municipis)) {
		writeFileSync(resolve(muniDir, `${ine5}.json`), JSON.stringify(row));
		n++;
	}
	console.log(`[copy-data] OK: ${n} fitxes per municipi → static/data/muni/ (de municipis.catalunya.json)`);
}

buildMuniSplit();

/**
 * Parser CSV mínim però correcte (camps entre cometes amb comes, p. ex. «Prat de Llobregat, el»).
 */
function splitCsvLine(ln) {
	const out = [];
	let cur = '';
	let q = false;
	for (let i = 0; i < ln.length; i++) {
		const c = ln[i];
		if (q) {
			if (c === '"') {
				if (ln[i + 1] === '"') {
					cur += '"';
					i++;
				} else q = false;
			} else cur += c;
		} else if (c === '"') q = true;
		else if (c === ',') {
			out.push(cur);
			cur = '';
		} else cur += c;
	}
	out.push(cur);
	return out;
}
function parseCsv(text) {
	const lines = text.trim().split(/\r?\n/);
	const head = splitCsvLine(lines[0]);
	return lines.slice(1).map((ln) => {
		const cells = splitCsvLine(ln);
		const o = {};
		head.forEach((h, i) => (o[h] = cells[i]));
		return o;
	});
}

/**
 * `metodologia-model.json` — els TRES gràfics germans de /metodologia (la secció de límits del
 * model), derivats dels CSV d'anàlisi committejats (font de veritat, ja verificats a CI):
 *  · reliability — calibració dels intervals (data/territorial/calibracio_intervals.csv, files GLOBAL).
 *  · discrepancia — scatter ETCA↔pernocta dels 486 munis (data/territorial/discrepancia_etca_pernocta.csv),
 *    amb el recompte 8 senyal / 142 soroll (la xifra honesta) i la banda de soroll com a protagonista.
 *  · regim — consum domèstic per càpita vs densitat (data/territorial/nivellc_analisi.csv): ensenya
 *    que els nuclis densos cauen sota la mediana de calibració → allà l'estimació NO és fiable.
 * Frontera honesta: aquí només transformem CSV→JSON; cap número nou. Build-only (static/ gitignored).
 */
function buildMetodologiaModel() {
	const T = (p) => resolve(REPO_ROOT, 'data/territorial', p);
	const calP = T('calibracio_intervals.csv');
	const disP = T('discrepancia_etca_pernocta.csv');
	const anaP = T('nivellc_analisi.csv');
	if (!existsSync(calP) || !existsSync(disP) || !existsSync(anaP)) {
		console.warn('[copy-data] AVÍS: falten CSV d\'anàlisi; no es genera metodologia-model.json.');
		return;
	}
	// Reliability (files GLOBAL): nominal → empíric (cobertura leave-one-out).
	const cal = parseCsv(readFileSync(calP, 'utf8'));
	const reliability = cal
		.filter((r) => r.scope === 'GLOBAL')
		.map((r) => ({ n: Number(r.nivell_nominal), e: Number(r.cobertura_loo) }));
	const interval80 = reliability.find((r) => r.n === 80)?.e ?? null;

	// Cobertura per TIPUS territorial al nominal 80 (la promesa headline), amb la n. La UI marca
	// «n massa petita» quan no es pot validar el tipus per separat (a n=7-9 el % és gairebé soroll).
	const TIPUS = ['interior_rural', 'litoral_vacacional', 'metropolita_dens', 'corona_metropolitana', 'litoral_metropolita'];
	const perTipus = TIPUS.map((t) => {
		const r = cal.find((x) => x.scope === t && Number(x.nivell_nominal) === 80);
		return r ? { tipus: t, e: Number(r.cobertura_loo), n: Number(r.n) } : null;
	})
		.filter(Boolean)
		.sort((a, b) => b.n - a.n);

	// Discrepància (scatter): un punt per muni amb ETCA. cls = coincident|senyal|soroll → c|s|n.
	const dis = parseCsv(readFileSync(disP, 'utf8'));
	const CLS = { coincident: 'c', senyal: 's', soroll: 'n' };
	const punts = dis.map((r) => ({
		x: Number(r.our_gap_pct),
		y: Number(r.etca_gap_pct),
		cls: CLS[r.classe] ?? 'c'
	}));
	const oposat = dis.filter((r) => r.signe_oposat === '1');
	const discrepancia = {
		n: dis.length,
		oposat: oposat.length,
		senyal: oposat.filter((r) => r.classe === 'senyal').length,
		soroll: oposat.filter((r) => r.classe === 'soroll').length,
		etca_min: 5,
		punts
	};

	// Règim dens: consum domèstic per càpita (kWh/resident) vs densitat. Mediana = calibració (amb ETCA).
	const ana = parseCsv(readFileSync(anaP, 'utf8'));
	const reg = [];
	const calRatios = [];
	for (const r of ana) {
		const kwh = Number(r.kwh_dom);
		const res = Number(r.resident) || Number(r.poblacio);
		const dens = Number(r.densitat_hab_km2);
		if (!(kwh > 0 && res > 0 && dens > 0)) continue;
		const k = kwh / res;
		reg.push({ d: Math.round(dens * 10) / 10, k: Math.round(k) });
		if (Number(r.etca) > 0) calRatios.push(k);
	}
	calRatios.sort((a, b) => a - b);
	const mediana = calRatios.length
		? Math.round(calRatios[Math.floor((calRatios.length - 1) / 2)])
		: null;

	const out = { reliability, interval80, perTipus, discrepancia, regim: { mediana, punts: reg } };
	const dest = resolve(DEST_DIR, 'metodologia-model.json');
	writeFileSync(dest, JSON.stringify(out));
	const kb = (statSync(dest).size / 1024).toFixed(1);
	console.log(
		`[copy-data] OK: metodologia-model.json → static/data/ (${reliability.length} nivells, ` +
			`${punts.length} munis scatter, ${reg.length} règim, ${kb} kB)`
	);
}

buildMetodologiaModel();

/**
 * `validats.json` — el conjunt d'ine5 que tenen ETCA oficial (Idescat), derivat de
 * `pernocta-catalunya.json` (`etca_oficial != null`). És el senyal de VALIDACIÓ per municipi:
 * la fitxa l'usa per no mostrar mai «confiança alta» sobre la pernocta a un municipi sense ETCA
 * (regla de la passada d'overpromise: la validació mana sobre l'heurística interna). Inclou els 9
 * municipis del Berguedà amb ETCA; els 22 petits no hi són → «estimació sense validació oficial».
 */
function buildValidats() {
	const src = resolve(REPO_ROOT, 'data/web/pernocta-catalunya.json');
	if (!existsSync(src)) {
		console.warn(`[copy-data] AVÍS: no s'ha trobat ${src}; no es genera validats.json.`);
		return;
	}
	const munis = JSON.parse(readFileSync(src, 'utf8')).munis;
	const validats = Object.entries(munis)
		.filter(([, v]) => v.etca_oficial != null)
		.map(([ine5]) => ine5)
		.sort();
	const dest = resolve(DEST_DIR, 'validats.json');
	writeFileSync(dest, JSON.stringify(validats));
	console.log(`[copy-data] OK: validats.json → static/data/ (${validats.length} munis amb ETCA)`);
}

buildValidats();

for (const f of FILES) {
	if (!existsSync(f.src)) {
		// CI i clons sense els marts no tenen la font generada: no és un error fatal.
		console.warn(
			`[copy-data] AVÍS: no s'ha trobat ${f.src}. Es manté la còpia existent (si n'hi ha) ` +
				`o el fallback del loader. Regenera-la amb el pipeline (Sondeig).`
		);
		continue;
	}
	const dest = resolve(DEST_DIR, f.name);
	copyFileSync(f.src, dest);
	const kb = (statSync(dest).size / 1024).toFixed(1);
	console.log(`[copy-data] OK: ${f.name} → static/data/ (${kb} kB)`);
}
