/**
 * W2 · EL LLISTAT D'UNA MÈTRICA A UNA COMARCA (`/comarca/[slug]/[metrica]/`).
 *
 * Petició de Bea (2026-07-31): «hem de poder clicar cada vegada que posi rang i accedir a cada
 * llistat». Aquest és l'artefacte que hi ha darrere de cada un d'aquests llistats: els municipis
 * d'una comarca per a UNA mètrica, amb el seu valor i el seu rang, i les mateixes referències
 * que ja pinta la targeta de la fitxa.
 *
 * FRONTERA DURA (C6 §4), sense excepcions noves: **aquí no es calcula cap rang ni cap
 * referència**. `copy-data.mjs` LLEGEIX `data/web/govern.catalunya.json` (el mart, de Sondeig),
 * agrupa les seves cel·les per la partició de `municipis-territori.json` —l'autoritat declarada
 * al capçal de `mart_govern.sql`— i les re-serialitza per comarca × mètrica. És exactament el
 * mateix que fa `buildGovernSplit()` per municipi: partir el que ja se serveix perquè cada
 * pàgina només carregui el seu tros. L'ORDRE de `munis` és el `rang` LLEGIT, no un `sort` per
 * valor: així un empat del mart segueix sent un empat a la pantalla i no hi apareix cap
 * guanyador que el mart no hagi declarat.
 *
 * Per què un fitxer per (comarca × mètrica) i no un per comarca: la pàgina és d'una mètrica, i
 * SvelteKit incrusta la resposta del `fetch` del loader a CADA pàgina prerenderitzada. Amb un
 * fitxer per comarca, les 9 pàgines d'una comarca portarien les 9 mètriques cadascuna.
 */
import type { MetricDef } from './types';

/** Un municipi de la comarca que TÉ la xifra: valor + rang, tal com els serveix el mart. */
export interface GovernLlistaMuni {
	ine5: string;
	/** Nom en forma corrent (article al davant), com el catàleg dels 947. */
	nom: string;
	/** Slug públic del municipi (`toSlug` del nom oficial) → enllaç a la seva fitxa. */
	slug: string;
	/** Valor mesurat, el MATEIX que la fitxa (mai recalculat). */
	valor: number;
	/** Rang ordinal descendent dins la comarca, LLEGIT del mart (1 = valor més alt). */
	rang: number;
	/** Rang compartit amb un altre municipi de la comarca (C6 §3.2). */
	empat: boolean;
}

/**
 * Un municipi de la comarca que NO té la xifra. **Hi surt igualment** (esmena de Bea,
 * 2026-07-31): «no vol dir zero». Ordenar-los com si el seu valor fos 0 els pintaria últims
 * quan la Quar, pel seu recompte, seria la 2a de la comarca (xifra verificada al MART; el
 * recompte encara no se serveix al web). Van en un bloc a part al FINAL, amb el motiu visible.
 */
export interface GovernLlistaSense {
	ine5: string;
	nom: string;
	slug: string;
}

/**
 * La definició de la mètrica que la pàgina necessita, copiada VERBATIM del contracte servit
 * (`municipis.bergueda.json`.metrics). Són els mateixos camps que fa servir la targeta de la
 * fitxa, perquè les dues pantalles no puguin dir coses diferents de la mateixa xifra.
 */
export type GovernLlistaDef = Pick<
	MetricDef,
	'key' | 'label' | 'unit' | 'format' | 'source' | 'date' | 'formula'
>;

/** El llistat sencer d'una (comarca × mètrica). */
export interface GovernLlista {
	/** Nom oficial de la comarca, sense article (l'article el posa `deComarca`). */
	comarca: string;
	/** Vegueria de la comarca (espina territorial), de la mateixa partició. */
	vegueria: string;
	/** Clau de mètrica del contracte (no el slug de la URL). */
	metrica: string;
	/** Rètol, unitat i procedència de la mètrica — del contracte, mai escrits a la pàgina. */
	def: GovernLlistaDef;
	/** Les altres mètriques amb rang de la mateixa comarca (navegació lateral), amb el seu rètol. */
	altres: { metrica: string; label: Record<string, string> }[];
	/** Vintage de la dada, tal com el mart. Uniforme a la comarca (el prebuild ho exigeix). */
	data: string;
	/** Denominador honest LLEGIT del mart: municipis de la comarca amb dada. */
	n_amb_dada: number;
	/** Municipis de la comarca segons la partició territorial (amb dada o sense). */
	n_comarca: number;
	/** Les mateixes referències que la targeta (B+D), servides amb el seu denominador. */
	mediana_comarca: number | null;
	ponderada_catalunya: number | null;
	hab_ponderada_catalunya: number | null;
	pes_ponderada: string | null;
	/** Amb dada, EN L'ORDRE DEL RANG del mart. */
	munis: GovernLlistaMuni[];
	/** Sense dada, ordenats per la clau d'ordenació de noms (forma d'índex). */
	sense: GovernLlistaSense[];
}
