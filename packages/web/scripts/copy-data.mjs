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
const SRC = resolve(REPO_ROOT, 'data/web/municipis.bergueda.json');
const DEST_DIR = resolve(__dirname, '../static/data');
const DEST = resolve(DEST_DIR, 'municipis.bergueda.json');

if (!existsSync(SRC)) {
	// CI i clons sense els marts no tenen la font generada: no és un error fatal.
	console.warn(
		`[copy-data] AVÍS: no s'ha trobat la font ${SRC}.\n` +
			`           El web farà servir la còpia existent a static/data (si n'hi ha) o el ` +
			`fallback del loader. Regenera-la amb: python tools/export_web_municipis.py`
	);
	process.exit(0);
}

mkdirSync(DEST_DIR, { recursive: true });
copyFileSync(SRC, DEST);

const kb = (statSync(DEST).size / 1024).toFixed(1);
console.log(`[copy-data] OK: data/web/municipis.bergueda.json → static/data/ (${kb} kB)`);
