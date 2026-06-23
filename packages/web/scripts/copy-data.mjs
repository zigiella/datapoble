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
