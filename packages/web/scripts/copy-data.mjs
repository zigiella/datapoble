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

import { copyFileSync, existsSync, mkdirSync, statSync } from 'node:fs';
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
	{ src: resolve(REPO_ROOT, 'data/web/etca-validacio.json'), name: 'etca-validacio.json' },
	{ src: resolve(REPO_ROOT, 'data/web/licitacions-bergueda.json'), name: 'licitacions-bergueda.json' },
	{ src: resolve(REPO_ROOT, 'data/web/lectures.bergueda.json'), name: 'lectures.bergueda.json' }
];

mkdirSync(DEST_DIR, { recursive: true });

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
