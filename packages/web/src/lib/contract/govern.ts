/**
 * Vista de govern (C6 · D5): el rang comarcal «k de n» servit des del mart_govern (D4).
 *
 * FRONTERA DURA (C6 §4): el rang es calcula AL TRANSFORM (mart_govern, Sondeig), MAI al
 * front. El rang és «k de n» de LA COMARCA DEL PROPI municipi (mai una llista fixa). Aquest
 * artefacte és la sortida del mart re-serialitzada per servir-la al web estàtic: a escala
 * Catalunya (P-947), `tools/export_govern_web.py` → `data/web/govern.catalunya.json` (947,
 * `{ine5: GovernEntry}`, ~0,67 MB). El prebuild (`copy-data.mjs`) el PARTEIX per municipi a
 * `/data/govern/<ine5>.json` (perquè el loader no incrusti el fitxer sencer a cada pàgina); el front
 * en llegeix NOMÉS l'entrada del seu municipi (`GovernEntry`) i la formata — no conté cap funció de
 * rang ni de percentil. (El monòlit `govern.bergueda.json` es manté com a retrocompat del pipeline
 * de dades, però el web ja no el consumeix.)
 *
 * Forma: `{ [ine5]: { comarca, metrics: { [metricKey]: GovernCell } } }`.
 */

/** Una cel·la del mart per (municipi × mètrica): valor + rang «k de n» + procedència. */
export interface GovernCell {
	/** Valor mesurat (el mateix que el dataset; NULL = sense dada). */
	valor: number | null;
	/** Rang ordinal descendent dins la comarca (1 = valor més alt). NULL si no hi ha dada. */
	rang: number | null;
	/** Denominador honest: municipis de la comarca amb dada per aquesta mètrica. */
	n_amb_dada: number;
	/** Vintage (any/rang) de la dada, tal com el mart. */
	data: string;
	/** Rang compartit amb un altre municipi de la comarca (C6 §3.2). */
	empat: boolean;
}

/** Entrada d'un municipi: la seva comarca + les cel·les de rang per mètrica. */
export interface GovernEntry {
	comarca: string;
	metrics: Record<string, GovernCell>;
}

/** Artefacte sencer, indexat per INE5. */
export type GovernData = Record<string, GovernEntry>;
