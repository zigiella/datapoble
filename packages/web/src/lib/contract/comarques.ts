/**
 * Agrupació territorial — forma de `data/comarques.json` (la genera el prebuild des de
 * `municipis-territori.json`). Base de les pàgines de comarca/vegueria i del breadcrumb navegable.
 * NO és dada de població; només estructura administrativa. Els slugs es deriven dels noms (`toSlug`).
 */

export interface ComarcaEntry {
	nom: string;
	vegueria: string;
	/** ine5 dels municipis de la comarca. */
	ine5s: string[];
}

export interface VegueriaEntry {
	nom: string;
	/** noms de les comarques de la vegueria. */
	comarques: string[];
}

export interface ComarquesData {
	comarques: ComarcaEntry[];
	vegueries: VegueriaEntry[];
}
