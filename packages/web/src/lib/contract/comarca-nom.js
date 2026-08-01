/**
 * EL NOM DE LA COMARCA AMB EL SEU ARTICLE — JS PUR.
 *
 * Per què existeix (vot de Bea, 2026-07-31): la mediana comarcal ha de dur el NOM de la comarca
 * escrit — «mediana del Berguedà», no «mediana comarcal». En català això obliga a la
 * contracció correcta, i la contracció depèn del GÈNERE i el NOMBRE del topònim, que són
 * **lèxics**: no es poden deduir de com s'escriu el nom. «Garrotxa» és femenina i «Garraf»
 * masculí; «Selva» femenina i «Segrià» masculí; «Osona» no porta article i «Anoia» sí.
 * Un `if` per cas seria 43 `if`s que ningú tornaria a mirar; per això aquí hi ha **una taula
 * declarada** (com `GOVERN_PES_DENOM`) i **una funció** que la rendeix per locale.
 *
 * La taula guarda gènere i nombre, NO la preposició ja muntada: així el català i el castellà
 * en surten cadascun amb la seva regla (el català elideix davant de vocal —«de l'Alt Empordà»—
 * i el castellà no —«del Alt Empordà»—) sense duplicar la llista.
 *
 * `verify-govern.mjs` l'exerceix sobre les 43 comarques REALS de `municipis-territori.json`
 * (l'autoritat de la partició): una comarca nova, un canvi de nom o una entrada de més fan
 * caure el CI. Si tot i així arribés un nom desconegut a la pantalla, `deComarca` retorna
 * `null` i qui la crida ha de caure al rètol sense nom («mediana comarcal»): abans quedar-nos
 * curts que inventar-li un article.
 *
 * JS pur (sense tipus, sense Svelte, sense paraglide) pel mateix motiu que `slug-core.js` i
 * `govern/kpis.js`: que la guarda offline pugui importar la MATEIXA funció, no una còpia.
 */

/**
 * Gènere i nombre de cada comarca, i si el topònim porta article.
 *
 * Valors: `'m'` masculí singular · `'f'` femení singular · `'mp'` masculí plural ·
 * `'fp'` femení plural · `null` **sense article** (Osona és l'única de les 43).
 *
 * La clau és el nom EXACTE tal com arriba a `municipis-territori.json` (i, per tant, a
 * `govern.catalunya.json`), sense article: «Berguedà», «Alt Empordà», «Garrigues».
 * @type {Record<string, 'm'|'f'|'mp'|'fp'|null>}
 */
export const COMARCA_GENERE = {
	'Alt Camp': 'm',
	'Alt Empordà': 'm',
	'Alt Penedès': 'm',
	'Alt Urgell': 'm',
	'Alta Ribagorça': 'f',
	Anoia: 'f',
	Bages: 'm',
	'Baix Camp': 'm',
	'Baix Ebre': 'm',
	'Baix Empordà': 'm',
	'Baix Llobregat': 'm',
	'Baix Penedès': 'm',
	Barcelonès: 'm',
	Berguedà: 'm',
	Cerdanya: 'f',
	'Conca de Barberà': 'f',
	Garraf: 'm',
	Garrigues: 'fp', // «les Garrigues» — l'única en plural
	Garrotxa: 'f',
	Gironès: 'm',
	Lluçanès: 'm',
	Maresme: 'm',
	Moianès: 'm',
	Montsià: 'm',
	Noguera: 'f',
	Osona: null, // l'única sense article: «d'Osona», mai «de l'Osona»
	'Pallars Jussà': 'm',
	'Pallars Sobirà': 'm',
	"Pla d'Urgell": 'm',
	"Pla de l'Estany": 'm',
	Priorat: 'm',
	"Ribera d'Ebre": 'f',
	Ripollès: 'm',
	Segarra: 'f',
	Segrià: 'm',
	Selva: 'f',
	Solsonès: 'm',
	Tarragonès: 'm',
	'Terra Alta': 'f',
	Urgell: 'm',
	"Val d'Aran": 'f',
	'Vallès Occidental': 'm',
	'Vallès Oriental': 'm'
};

/** Els valors admesos de la taula (la guarda no en deixa entrar cap altre). */
export const COMARCA_GENERES = ['m', 'f', 'mp', 'fp', null];

/**
 * Comença per vocal (o `h` muda) → el català hi elideix l'article: «l'Alt Empordà».
 * El castellà NO elideix, per això aquesta prova només s'aplica al català.
 * @param {string} nom
 */
function comencaPerVocal(nom) {
	return /^[aeiouàèéíòóúüh]/i.test(String(nom).trim());
}

/**
 * El nom de la comarca precedit de «de» amb la contracció que li toca, en el locale demanat.
 *
 *   ca: «del Berguedà» · «de la Garrotxa» · «de l'Alt Empordà» · «de les Garrigues» · «d'Osona»
 *   es: «del Berguedà» · «de la Garrotxa» · «del Alt Empordà»  · «de las Garrigues» · «de Osona»
 *
 * Retorna `null` —mai una cadena a mitges— si la comarca no és a la taula: qui la crida ha de
 * caure al rètol sense nom. Inventar-li l'article seria escriure el nostre error a la pantalla.
 *
 * @param {string} nom Nom oficial de la comarca, sense article.
 * @param {'ca'|'es'} locale
 * @returns {string|null}
 */
export function deComarca(nom, locale) {
	const clau = String(nom ?? '').trim();
	if (!(clau in COMARCA_GENERE)) return null;
	const gen = COMARCA_GENERE[clau];
	// Sense article: el català apostrofa la preposició davant de vocal («d'Osona»), el castellà no.
	if (gen === null) {
		if (locale === 'ca') return comencaPerVocal(clau) ? `d'${clau}` : `de ${clau}`;
		return `de ${clau}`;
	}
	if (locale === 'ca') {
		if (comencaPerVocal(clau)) return `de l'${clau}`; // el gènere no canvia l'elisió
		if (gen === 'm') return `del ${clau}`;
		if (gen === 'f') return `de la ${clau}`;
		if (gen === 'mp') return `dels ${clau}`;
		return `de les ${clau}`;
	}
	if (gen === 'm') return `del ${clau}`;
	if (gen === 'f') return `de la ${clau}`;
	if (gen === 'mp') return `de los ${clau}`;
	return `de las ${clau}`;
}

/**
 * El nom de la comarca amb el seu article i prou (sense preposició), per a un títol:
 * «el Berguedà», «l'Alt Empordà», «les Garrigues», «Osona».
 *
 * Mateixa taula, mateixa política de `null` que `deComarca`.
 * @param {string} nom
 * @param {'ca'|'es'} locale
 * @returns {string|null}
 */
export function laComarca(nom, locale) {
	const clau = String(nom ?? '').trim();
	if (!(clau in COMARCA_GENERE)) return null;
	const gen = COMARCA_GENERE[clau];
	if (gen === null) return clau;
	if (locale === 'ca') {
		if (comencaPerVocal(clau)) return `l'${clau}`;
		if (gen === 'm') return `el ${clau}`;
		if (gen === 'f') return `la ${clau}`;
		if (gen === 'mp') return `els ${clau}`;
		return `les ${clau}`;
	}
	if (gen === 'm') return `el ${clau}`;
	if (gen === 'f') return `la ${clau}`;
	if (gen === 'mp') return `los ${clau}`;
	return `las ${clau}`;
}
