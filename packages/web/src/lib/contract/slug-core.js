/**
 * Nucli del SLUG i de les formes del nom de municipi — JS PUR.
 *
 * Per què un `.js` al costat de `slug.ts`: aquestes tres funcions són l'única regla d'article
 * del sistema (URL pública, títol de pantalla i clau d'ordenació surten totes d'aquí) i el
 * verificador offline `scripts/verify-govern.mjs` les ha de poder EXERCIR sobre els 947 noms
 * reals sense duplicar-les. És el mateix motiu —i el mateix patró— que `src/lib/govern/kpis.js`:
 * font única, importable per Node tal qual (sense tipus, sense Svelte, sense paraglide), perquè
 * la guarda i el codi no derivin. `slug.ts` les re-exporta amb tipus; cap punt de crida canvia.
 *
 * Les tres formes del MATEIX nom, i quan es fa servir cadascuna:
 *  · forma d'ÍNDEX   «Pobla de Lillet, la»  → com arriba dels marts; és la clau d'ORDENACIÓ
 *    (si s'ordena per la forma corrent, els 131 municipis amb article s'apilen sota «L»).
 *  · forma CORRENT   «la Pobla de Lillet»   → com arriba de la geometria oficial (= el catàleg
 *    dels 947); és la que es PINTA.
 *  · SLUG            «la-pobla-de-lillet»   → la cara pública de la URL.
 * La clau interna del join SEGUEIX SENT l'`ine5`: cap xifra depèn d'aquestes formes.
 */

/** "Nom, la|el|els|les|l'" (forma d'índex). Apòstrof recte o tipogràfic. */
export const ARTICLE = /^(.*),\s*(l['’]|la|el|els|les)$/i;

/**
 * Article al DAVANT (forma corrent): «l'Ametlla del Vallès» o «la Pobla de Lillet».
 * L'article amb apòstrof s'enganxa al nom; els altres quatre exigeixen un espai darrere,
 * perquè un nom que simplement COMENCI per aquestes lletres no es parteixi.
 */
const ARTICLE_DAVANT = /^(l['’])\s*(.+)$|^(la|el|els|les)\s+(.+)$/i;

/**
 * Slug públic a partir del nom oficial (spec consultora 2 §8.1).
 *
 * Regla: minúscules, sense accents ni apòstrofs, espais→guions, i l'article final
 * reordenat al davant:
 *   "Quar, la"            → "la-quar"
 *   "Pobla de Lillet, la" → "la-pobla-de-lillet"
 *   "Castellar de n'Hug"  → "castellar-de-nhug"
 *
 * És una funció PURA del nom oficial, així que no cal cap fitxer a mantenir a mà: les dues
 * formes del nom (índex i corrent) hi donen el MATEIX slug, i per això la URL no depèn de
 * quin artefacte hagi servit el nom.
 * @param {string} nom
 * @returns {string}
 */
export function toSlug(nom) {
	let s = String(nom).trim();
	const m = s.match(ARTICLE);
	if (m) s = `${m[2]} ${m[1]}`; // "Nom, la" → "la Nom"
	// Article INICIAL amb apòstrof sense espai ("l'Hospitalet", forma inline del geojson oficial):
	// hi inserim un separador perquè doni el MATEIX slug que la forma "Nom, l'" ("l-hospitalet",
	// no "lhospitalet"). Només l'article inicial; un apòstrof intern ("Castellar de n'Hug") es
	// manté i cau a "nhug" com fins ara. La forma "l' Nom" (ja amb espai) hi passa idempotent.
	s = s.replace(/^(l)['’]\s*/i, '$1 ');
	return s
		.replace(/l·l/gi, 'll') // ela geminada (l·l) → ll, no l-l
		.normalize('NFD')
		.replace(/\p{M}/gu, '') // treu marques combinades (accents)
		.replace(/['’·]/g, '') // apòstrofs i punt volat fora (n'Hug → nhug)
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-') // no-alfanumèric → guió
		.replace(/^-+|-+$/g, ''); // trim guions
}

/**
 * Nom del municipi en la seva forma CORRENT (article al davant), sigui quina sigui la forma
 * amb què arribi la fila.
 *
 * Per què cal: el mateix municipi ens arriba en DUES formes segons l'artefacte —
 * `municipis.*.json` (marts) el serveix en forma d'índex, «Pobla de Lillet, la», i la geometria
 * oficial (d'on surt el catàleg dels 947) i el tauler el serveixen com «la Pobla de Lillet».
 * La clau del join és sempre l'`ine5`, així que la divergència NO afecta cap xifra; però pintada
 * a un `<h1>` la forma d'índex es llegeix com un error. Aquí es normalitza NOMÉS per mostrar.
 *
 * Reutilitza la mateixa regla d'article que `toSlug` (una sola font de veritat), i per això els
 * dos noms ja donaven —i segueixen donant— el MATEIX slug: la URL no es toca.
 * @param {string} nom
 * @returns {string}
 */
export function nomCanonic(nom) {
	const s = String(nom).trim();
	const m = s.match(ARTICLE);
	if (!m) return s;
	// "Nom, l'" → "l'Nom" (sense espai); "Nom, la" → "la Nom".
	const art = m[2].toLowerCase();
	return /['’]$/.test(art) ? `${art}${m[1]}` : `${art} ${m[1]}`;
}

/**
 * Nom en forma d'ÍNDEX (article al final) — la INVERSA de `nomCanonic`, i la clau d'ORDENACIÓ
 * de qualsevol llista de municipis.
 *
 * Per què existeix: el catàleg dels 947 ve de la geometria oficial, que serveix la forma corrent
 * («l'Ametlla del Vallès», «les Borges Blanques»). Ordenar-la tal qual apila els **131** municipis
 * amb article sota les lletres «L» i «E», que és exactament el que la forma d'índex evita. El
 * dataset dels marts ja arriba en forma d'índex: aquí hi passa IDEMPOTENT.
 *
 * NO canvia mai la URL: `toSlug(nomIndex(nom)) === toSlug(nom)` per construcció (les dues formes
 * comparteixen la regla d'article). `verify-govern.mjs` ho exerceix sobre els 947.
 * @param {string} nom
 * @returns {string}
 */
export function nomIndex(nom) {
	const s = String(nom).trim();
	if (ARTICLE.test(s)) return s; // ja és forma d'índex
	const m = s.match(ARTICLE_DAVANT);
	if (!m) return s;
	const art = (m[1] ?? m[3]).toLowerCase();
	const cos = m[2] ?? m[4];
	return `${cos}, ${art}`;
}
