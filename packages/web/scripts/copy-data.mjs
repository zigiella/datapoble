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

import {
	copyFileSync,
	existsSync,
	mkdirSync,
	readdirSync,
	readFileSync,
	statSync,
	writeFileSync
} from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// W2 · la regla de slug i la clau d'ordenació de noms són font ÚNICA (`slug-core.js`), i les
// claus rankejables i el slug de mètrica també (`govern/kpis.js`): el prebuild les IMPORTA, no
// en fa una còpia, perquè les URL que genera aquí i les que pinta el front no puguin divergir.
import { toSlug, nomIndex } from '../src/lib/contract/slug-core.js';
import { GOVERN_RANK_KEYS, metricaSlug } from '../src/lib/govern/kpis.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

// `packages/web/scripts` → arrel del repo són tres nivells amunt.
const REPO_ROOT = resolve(__dirname, '../../..');
const DEST_DIR = resolve(__dirname, '../static/data');

// Actius de dades a copiar (font → nom a static/data). El dataset és l'únic imprescindible;
// la validació ETCA és opcional (la genera `tools/validacio_etca.py`).
//
// FASE NOVA · MODEL APARCAT (vot de Bea 2026-07-16): el web ja no consumeix el model
// d'estimació de pernocta. La frontera de consum actual de cada actiu:
//  · pernocta-catalunya.json — NOMÉS el camp oficial `etca_oficial` (fitxa de municipi);
//    l'estimació/banda del model ja no es llegeix enlloc del web.
//  · etca-validacio.json + metodologia-model.json — només /metodologia, seccions etiquetades
//    «model aparcat (annex de recerca)».
//  · lectures.bergueda.json (B1) i municipis-mirall.json (B2) — pendents de REGENERAR sobre
//    dades oficials (fora d'aquest lot; vegeu fase-nova-aparcaments.md §B).
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
	// Vista de govern (D5 → P-947) i tauler v2 (D7 → P-947): NO es copien sencers aquí. El govern es
	// parteix per municipi a `buildGovernSplit()` (si no, SvelteKit incrustaria els 0,67 MB sencers a
	// CADA una de les 947×2 pàgines prerenderitzades en fer-ne `fetch` al loader) i el tauler es copia
	// per shard a `copyTaulerShards()`. El monòlit `govern.bergueda.json` es manté a `data/web/` com a
	// retrocompat del pipeline de dades, però el web ja no el copia ni el consumeix.
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
		return [];
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
	return cataleg;
}

// El catàleg és la font dels NOMS (i, per tant, dels slugs) de qualsevol llista de municipis:
// el reaprofita `buildGovernLlistes()` per no tornar a llegir la geometria.
const CATALEG = buildCataleg();

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
 * Parteix `govern.catalunya.json` (947 munis, `{ine5: GovernEntry}`) en un fitxer PER MUNICIPI a
 * `static/data/govern/<ine5>.json` (el rang «k de n» de la seva comarca, ~0,3 kB). Per què (EL
 * MATEIX motiu que `buildMuniSplit`): la fitxa es prerenderitza per muni (947×2) i, si el loader fes
 * `fetch` del fitxer sencer (0,67 MB), SvelteKit n'INCRUSTARIA la resposta a CADA pàgina per a la
 * hidratació — 0,67 MB × 1.894 pàgines. Amb un fitxer per muni, cada fitxa només incrusta el SEU
 * rang. Frontera honesta: la font (`govern.catalunya.json`, de Sondeig) NO es modifica; aquí només
 * la partim per servir-la, igual que amb `municipis.catalunya.json`. Build-only (static/ gitignored).
 */
function buildGovernSplit() {
	const src = resolve(REPO_ROOT, 'data/web/govern.catalunya.json');
	if (!existsSync(src)) {
		console.warn(`[copy-data] AVÍS: no s'ha trobat ${src}; no es parteix el govern per municipi.`);
		return;
	}
	const data = JSON.parse(readFileSync(src, 'utf8'));
	const dir = resolve(DEST_DIR, 'govern');
	mkdirSync(dir, { recursive: true });
	let n = 0;
	for (const [ine5, entry] of Object.entries(data)) {
		writeFileSync(resolve(dir, `${ine5}.json`), JSON.stringify(entry));
		n++;
	}
	console.log(`[copy-data] OK: ${n} fitxes de govern → static/data/govern/ (de govern.catalunya.json)`);
}

buildGovernSplit();

/**
 * W2 · ELS LLISTATS PER COMARCA × MÈTRICA (`static/data/govern-llista/<comarca>/<metrica>.json`).
 *
 * Petició de Bea: cada rang que es pinti ha de portar al llistat d'aquella mètrica a aquella
 * comarca. Aquesta funció prepara la dada d'aquell llistat, i **no en calcula cap tros**: llegeix
 * `govern.catalunya.json` (el mart) i el reagrupa per la partició de `municipis-territori.json`,
 * que és l'autoritat declarada de la partició (la mateixa que fa servir el mart). Mateixa
 * frontera honesta que `buildGovernSplit()`: la font no es modifica; només es parteix.
 *
 * Tres decisions que són DOCTRINA, no format:
 *  1. **L'ordre és el `rang` LLEGIT**, mai un `sort` pel valor. Ordenar pel valor tornaria a
 *     calcular l'ordre al nostre costat (C6 §4) i, pitjor, desfaria els empats: el mart en
 *     declara 220 a Catalunya i un empat no pot pintar un guanyador fals. Dins d'un mateix rang
 *     els empatats s'ordenen per la clau d'ordenació de noms (`nomIndex`), que és estable i no
 *     insinua cap ordre de valor.
 *  2. **Els municipis SENSE dada hi surten igualment**, en un bloc a part al final (esmena de
 *     Bea, 2026-07-31). «No vol dir zero»: si el buit de la Quar es tractés com un 0, sortiria
 *     l'ÚLTIMA de la comarca quan pel seu recompte seria de les primeres (7 estrangers de 44 hab
 *     ≈ 15,9 %, la 2a — xifra verificada per Talaia AL MART; el recompte encara no se serveix al
 *     web, i per això la pàgina no el pot pintar). El motiu de
 *     l'absència el resol el front amb el mapa de `kpis.js` (n'hi ha TRES de diferents), que ja
 *     és la font única d'aquella frase.
 *  3. **El denominador honest viatja amb la llista**: `n_amb_dada` (LLEGIT del mart) i
 *     `n_comarca` (recompte de files de la partició territorial). Si divergeixen, la pàgina
 *     ho ha de dir; per això van tots dos i no un de sol.
 *
 * Guardes que trenquen el PREBUILD (no un avís silenciós): si dins d'una mateixa comarca les
 * cel·les d'una mètrica no coincideixen en vintage, denominador o referències, o si el
 * `n_amb_dada` del mart no és el nombre de cel·les amb rang que hi hem trobat, l'artefacte
 * seria una mitja veritat i val més no publicar-lo. (Comprovat el 2026-08-01 sobre els 947:
 * 0 divergències, 387 parells comarca × mètrica.)
 */
function buildGovernLlistes() {
	const govSrc = resolve(REPO_ROOT, 'data/web/govern.catalunya.json');
	const terrSrc = resolve(REPO_ROOT, 'data/web/municipis-territori.json');
	// El catàleg de mètriques (= el contracte semàntic servit) és OBLIGATORI: sense ell la pàgina
	// pintaria xifres sense font ni fórmula, que és exactament el que C6 §8.1 prohibeix. Si no hi
	// és, no es genera cap llistat — el «no» honest abans que una pàgina sense procedència.
	const contracteSrc = resolve(REPO_ROOT, 'data/web/municipis.bergueda.json');
	for (const p of [govSrc, terrSrc, contracteSrc]) {
		if (!existsSync(p)) {
			console.warn(`[copy-data] AVÍS: falta ${p}; no es generen els llistats per comarca × mètrica.`);
			return;
		}
	}
	if (!CATALEG.length) {
		console.warn(`[copy-data] AVÍS: catàleg buit; no es generen els llistats per comarca × mètrica.`);
		return;
	}
	const gov = JSON.parse(readFileSync(govSrc, 'utf8'));
	const terr = JSON.parse(readFileSync(terrSrc, 'utf8'));
	const metrics = JSON.parse(readFileSync(contracteSrc, 'utf8')).metrics ?? {};
	const nomByIne5 = new Map(CATALEG.map((mn) => [mn.ine5, mn.nom]));

	/**
	 * La definició de la mètrica que la pàgina necessita per pintar amb procedència, copiada
	 * VERBATIM del contracte servit (mai reescrita aquí). Són els MATEIXOS camps que fa servir la
	 * targeta de la fitxa (`provenanceLine` + rètol + unitat + format), perquè les dues pantalles
	 * no puguin dir coses diferents de la mateixa xifra. La `definicio` i la `note` llargues no
	 * hi viatgen: la fitxa i el glossari són el seu lloc, i aquí multiplicarien la pàgina per 10.
	 */
	const defDe = (key) => {
		const d = metrics[key];
		if (!d) return null;
		return {
			key: d.key ?? key,
			label: d.label,
			unit: d.unit,
			format: d.format,
			source: d.source,
			date: d.date,
			formula: d.formula
		};
	};

	// Partició territorial: comarca → ine5s + vegueria. L'autoritat, no el govern.json.
	// La vegueria hi viatja perquè la pàgina pugui pintar l'espina sencera sense carregar
	// `comarques.json` (12 kB que SvelteKit incrustaria a cadascuna de les 1.161 pàgines).
	const byComarca = new Map();
	for (const [ine5, t] of Object.entries(terr)) {
		if (!t?.comarca) continue;
		if (!byComarca.has(t.comarca)) byComarca.set(t.comarca, { vegueria: t.vegueria || '', ine5s: [] });
		byComarca.get(t.comarca).ine5s.push(ine5);
	}

	const dir = resolve(DEST_DIR, 'govern-llista');
	mkdirSync(dir, { recursive: true });
	const coll = new Intl.Collator('ca');
	const slugSeen = new Map();
	let nFitxers = 0;
	let nFiles = 0;
	let nSense = 0;

	for (const [comarca, { vegueria, ine5s }] of byComarca) {
		const cslug = toSlug(comarca);
		if (slugSeen.has(cslug) && slugSeen.get(cslug) !== comarca) {
			throw new Error(`[copy-data] col·lisió de slug de comarca "${cslug}": ${slugSeen.get(cslug)} vs ${comarca}`);
		}
		slugSeen.set(cslug, comarca);
		const cdir = resolve(dir, cslug);
		mkdirSync(cdir, { recursive: true });

		for (const metrica of GOVERN_RANK_KEYS) {
			const def = defDe(metrica);
			if (!def) {
				throw new Error(
					`[copy-data] ${comarca}/${metrica}: el contracte servit no declara aquesta mètrica. ` +
						`Un llistat sense font ni fórmula no es publica (C6 §8.1).`
				);
			}
			const munis = [];
			const sense = [];
			/** Camps que han de ser IDÈNTICS a totes les cel·les de la comarca per a la mètrica. */
			let comu = null;
			for (const ine5 of ine5s) {
				const cell = gov[ine5]?.metrics?.[metrica];
				if (!cell) {
					throw new Error(
						`[copy-data] ${comarca}/${metrica}: el mart no serveix la cel·la de ${ine5}. ` +
							`El llistat no pot dir «de ${ine5s.length}» si no ha vist tots els municipis.`
					);
				}
				const firma = {
					data: cell.data,
					n_amb_dada: cell.n_amb_dada,
					mediana_comarca: cell.mediana_comarca ?? null,
					ponderada_catalunya: cell.ponderada_catalunya ?? null,
					hab_ponderada_catalunya: cell.hab_ponderada_catalunya ?? null,
					pes_ponderada: cell.pes_ponderada ?? null
				};
				if (comu === null) comu = firma;
				else if (JSON.stringify(comu) !== JSON.stringify(firma)) {
					throw new Error(
						`[copy-data] ${comarca}/${metrica}: les cel·les del mart no coincideixen en ` +
							`vintage/denominador/referències (${ine5}). Un llistat amb dues veritats no es publica.`
					);
				}
				const nom = nomByIne5.get(ine5) ?? ine5;
				const base = { ine5, nom, slug: toSlug(nom) };
				if (cell.rang == null) sense.push(base);
				else munis.push({ ...base, valor: cell.valor, rang: cell.rang, empat: !!cell.empat });
			}
			if (comu === null) continue; // comarca sense municipis: impossible, però no s'inventa un fitxer

			// ORDRE = el rang LLEGIT. Els empatats (mateix rang) s'ordenen per la clau d'ordenació
			// de noms: estable, i no insinua cap ordre de valor que el mart no hagi declarat.
			munis.sort((a, b) => a.rang - b.rang || coll.compare(nomIndex(a.nom), nomIndex(b.nom)));
			sense.sort((a, b) => coll.compare(nomIndex(a.nom), nomIndex(b.nom)));

			if (comu.n_amb_dada !== munis.length) {
				throw new Error(
					`[copy-data] ${comarca}/${metrica}: el mart diu n_amb_dada=${comu.n_amb_dada} i hi ha ` +
						`${munis.length} municipis amb rang. El denominador publicat ha de ser el que es veu.`
				);
			}
			// Navegació lateral: les altres mètriques amb rang de la MATEIXA comarca, amb el seu
			// rètol del contracte. Viatja amb l'artefacte perquè la pàgina no hagi de carregar el
			// catàleg sencer de 56 mètriques (73 kB) per pintar 8 enllaços.
			const altres = GOVERN_RANK_KEYS.filter((k) => k !== metrica).map((k) => {
				const d = defDe(k);
				if (!d) throw new Error(`[copy-data] ${metrica}: '${k}' no és al contracte servit`);
				return { metrica: k, label: d.label };
			});
			const out = {
				comarca,
				vegueria,
				metrica,
				def,
				altres,
				...comu,
				n_comarca: ine5s.length,
				munis,
				sense
			};
			writeFileSync(resolve(cdir, `${metricaSlug(metrica)}.json`), JSON.stringify(out));
			nFitxers++;
			nFiles += munis.length;
			nSense += sense.length;
		}
	}
	console.log(
		`[copy-data] OK: ${nFitxers} llistats comarca × mètrica → static/data/govern-llista/ ` +
			`(${byComarca.size} comarques × ${GOVERN_RANK_KEYS.length} mètriques; ${nFiles} files amb ` +
			`rang, ${nSense} municipis sense dada que hi surten igualment amb el seu motiu)`
	);
}

buildGovernLlistes();

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

// (`validats.json` — el conjunt d'ine5 amb ETCA — ja NO es genera: només servia per capar la
// confiança del model, i el model està aparcat. Si mai cal, git en recorda el builder.)

/**
 * Copia els SHARDS del tauler v2 (D7 · P-947): un fitxer per municipi (`tauler/<ine5>.json`,
 * ~19 kB, el `TaulerEntry` directe) + el sidecar compartit `tauler/_meta.json` (frescor +
 * doctrina del «<5», una sola vegada). Sondeig parteix el tauler per municipi A POSTA: a 947 el
 * monòlit faria 17-24 MB que la fitxa carregaria sencer per pintar un sol poble. La fitxa carrega
 * NOMÉS el shard del seu `ine5` (loader `+page.ts`). Frontera honesta: aquí només copiem; la font
 * (de Sondeig) no es modifica. Idempotent, cross-platform, no-fatal si la font no hi és (CI).
 */
function copyTaulerShards() {
	const srcDir = resolve(REPO_ROOT, 'data/web/tauler');
	if (!existsSync(srcDir)) {
		console.warn(
			`[copy-data] AVÍS: no s'ha trobat ${srcDir}. No es copien els shards del tauler ` +
				`(regenera'ls amb el pipeline: Sondeig). Es manté la còpia existent, si n'hi ha.`
		);
		return;
	}
	const destDir = resolve(DEST_DIR, 'tauler');
	mkdirSync(destDir, { recursive: true });
	let n = 0;
	for (const f of readdirSync(srcDir)) {
		if (!f.endsWith('.json')) continue;
		copyFileSync(resolve(srcDir, f), resolve(destDir, f));
		n++;
	}
	console.log(`[copy-data] OK: ${n} fitxers del tauler → static/data/tauler/ (shards + _meta.json)`);
}

copyTaulerShards();

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
