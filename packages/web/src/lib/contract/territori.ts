/**
 * Espina territorial — forma de `data/municipis-territori.json`.
 *
 * La genera `tools/deriva_territori.py` (punt representatiu del municipi dins la comarca; exacte
 * perquè les comarques són unions de municipis sencers). Dona, per a cada municipi de Catalunya, la
 * seva comarca i vegueria — la base del breadcrumb (Catalunya › vegueria › comarca › municipi) i de
 * la navegació «altres municipis de la comarca». NO és cap dada de població; és estructura
 * administrativa (geometria oficial).
 */

export interface MuniTerritori {
	comarca: string;
	vegueria: string;
}

export type TerritoriData = Record<string, MuniTerritori>;
