/**
 * Vista de govern (C6 · D5): el rang comarcal «k de n» servit des del mart_govern (D4).
 *
 * FRONTERA DURA (C6 §4): el rang es calcula AL TRANSFORM (mart_govern, Sondeig), MAI al
 * front. Aquest artefacte és la sortida del mart re-serialitzada per servir-la al web
 * estàtic (`tools/export_govern_web.py` → `data/web/govern.bergueda.json` → `/data/govern.json`).
 * El front NOMÉS el LLEGEIX i el formata; no conté cap funció de rang ni de percentil.
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
