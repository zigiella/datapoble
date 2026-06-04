#!/usr/bin/env node
/**
 * build-bergueda-geojson.mjs — genera el GeoJSON dels municipis del Berguedà (pilot).
 *
 * REPRODUÏBLE: re-executar-ho torna a baixar la geometria oficial i reescriu el fitxer.
 *
 * Font geometria: Opendatasoft "georef-spain-municipio" (georeferència oficial INE/IGN,
 *   re-distribuïda; CC-BY). Camp `mun_code` = INE5 (la nostra join_key del contracte),
 *   `geo_shape` = geometria. Veure docs/data-sources.md (trampa de codis Catastro≠INE).
 *
 * Àmbit: els 31 municipis del Berguedà. ATENCIÓ: 30 són a la província de Barcelona (08)
 *   i **Gósol (25100) és a Lleida (25)** — pertany al Berguedà però canvia de província.
 *
 * Sortida: packages/web/static/geo/bergueda-municipis.geojson
 *   FeatureCollection amb properties { ine5, nom } per fer el join amb el dataset del
 *   contracte (mock avui; mart/API demà). Geometria en EPSG:4326 (lon/lat), com vol MapLibre.
 *
 * Ús:  node tools/build-bergueda-geojson.mjs
 */

import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, '../packages/web/static/geo/bergueda-municipis.geojson');

// Els 31 codis INE5 del Berguedà (resolts i validats contra Opendatasoft per nom oficial).
// 30 a província 08 (Barcelona) + Gósol 25100 (Lleida). Aquest és l'artefacte estable.
const INE5 = [
	'08011', '08016', '08022', '08024', '08045', '08049', '08050', '08052', '08057',
	'08078', '08080', '08092', '08093', '08099', '08130', '08132', '08142', '08144',
	'08166', '08175', '08177', '08188', '08190', '08216', '08255', '08268', '08293',
	'08299', '08308', '08903', '25100'
];

const BASE =
	'https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/georef-spain-municipio/records';

/**
 * Aprimat lleuger i sense dependències per a un coroplètic a escala comarcal:
 *  - arrodoneix coordenades a 5 decimals (~1,1 m) — la geometria original ve a ~9 (absurd);
 *  - elimina punts consecutius duplicats després d'arrodonir.
 * No fa Douglas–Peucker (preservem la forma fil per randa a aquest nivell). Per a l'escala
 * Catalunya (~947 municipis) caldria simplificació topològica de debò (mapshaper) → anotat.
 */
const PREC = 1e5;
const round = (n) => Math.round(n * PREC) / PREC;

function thinRing(ring) {
	const out = [];
	let prev = null;
	for (const pt of ring) {
		const r = [round(pt[0]), round(pt[1])];
		if (!prev || r[0] !== prev[0] || r[1] !== prev[1]) out.push(r);
		prev = r;
	}
	// un anell tancat necessita ≥4 punts (primer == últim); si col·lapsa, retorna l'original arrodonit.
	if (out.length < 4) return ring.map((p) => [round(p[0]), round(p[1])]);
	// garanteix tancament
	const a = out[0];
	const b = out[out.length - 1];
	if (a[0] !== b[0] || a[1] !== b[1]) out.push([a[0], a[1]]);
	return out;
}

function simplifyGeometry(geom) {
	if (geom.type === 'Polygon') {
		return { type: 'Polygon', coordinates: geom.coordinates.map(thinRing) };
	}
	if (geom.type === 'MultiPolygon') {
		return {
			type: 'MultiPolygon',
			coordinates: geom.coordinates.map((poly) => poly.map(thinRing))
		};
	}
	return geom;
}

async function fetchOne(code) {
	const params = new URLSearchParams({
		where: `mun_code="${code}"`,
		select: 'mun_code,mun_name,geo_shape',
		limit: '1'
	});
	const res = await fetch(`${BASE}?${params}`);
	if (!res.ok) throw new Error(`HTTP ${res.status} per ${code}`);
	const data = await res.json();
	const row = data.results?.[0];
	if (!row || !row.geo_shape) throw new Error(`Sense geometria per ${code}`);
	// geo_shape ve com a Feature { type:'Feature', geometry, properties } o GeoJSON geometry.
	const geometry = row.geo_shape.geometry ?? row.geo_shape;
	return {
		type: 'Feature',
		properties: { ine5: row.mun_code, nom: row.mun_name },
		geometry: simplifyGeometry(geometry)
	};
}

async function main() {
	console.log(`Baixant geometria de ${INE5.length} municipis del Berguedà…`);
	const features = [];
	for (const code of INE5) {
		const f = await fetchOne(code);
		features.push(f);
		process.stdout.write('.');
	}
	process.stdout.write('\n');

	if (features.length !== 31) {
		throw new Error(`S'esperaven 31 municipis, n'hi ha ${features.length}`);
	}

	const fc = {
		type: 'FeatureCollection',
		name: 'bergueda-municipis',
		meta: {
			scope: 'Berguedà (31 municipis)',
			join_key: 'ine5',
			source: 'Opendatasoft georef-spain-municipio (INE/IGN, CC-BY)',
			generated: new Date().toISOString().slice(0, 10),
			generator: 'tools/build-bergueda-geojson.mjs'
		},
		features
	};

	mkdirSync(dirname(OUT), { recursive: true });
	writeFileSync(OUT, JSON.stringify(fc));
	console.log(`Escrit ${OUT} (${features.length} features).`);
}

main().catch((e) => {
	console.error('ERROR:', e.message);
	process.exit(1);
});
