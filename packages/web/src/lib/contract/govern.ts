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

	// ── R-REFERENCIA (Sondeig, 2026-07-31) · LES REFERÈNCIES, SERVIDES AMB EL SEU DENOMINADOR ──
	// El mart en serveix TRES famílies (mediana · ponderada · estratificada per franja) i el
	// capçal de `semantic/metrics.yml` («QUINES ES PINTEN», vot de Bea «farem B+D») decideix
	// que la fitxa en pinta DUES: la ponderada de Catalunya (l'ancoratge oficial) i la mediana
	// de la comarca (els iguals, mateix perímetre que el rang). La resta d'aquests camps se
	// serveixen igualment i queden disponibles per a una decisió futura: són dada, no forats.
	//
	// ⚠️ CAP D'AQUESTES XIFRES ES POT PINTAR SENSE EL SEU DENOMINADOR (C6 §8.1), i el
	// denominador és DE NATURALESA DIFERENT segons la família: una mediana és «sobre N
	// MUNICIPIS» (`n_amb_dada`); una ponderada, «sobre N unitats del seu PES» (`pes_ponderada`
	// diu quina unitat és — i NO sempre són habitants).

	/** B+D · mediana de la comarca, sobre EXACTAMENT el mateix conjunt que ordena `rang`. */
	mediana_comarca: number | null;
	/** B+D · ponderada de Catalunya = total / total del pes. NULL a `poblacio` (seria la seva
	 *  pròpia mida): no és un forat, és que la pregunta no existeix. */
	ponderada_catalunya: number | null;
	/** Denominador de `ponderada_catalunya`: quantes unitats del pes hi ha darrere. */
	hab_ponderada_catalunya: number | null;
	/** Quina magnitud pondera aquesta mètrica (`poblacio`, `hab_total`, `pob_0_14`…). És el que
	 *  fa que el denominador es pugui NOMENAR: sense ell, «sobre 3.915.127 habitants» seria fals
	 *  a `pct_noprincipal`, que es pondera per HABITATGES. NULL a `poblacio`. */
	pes_ponderada: string | null;

	// Servides i NO pintades (disponibles; la doctrina explica per què):
	/** Mediana de Catalunya (municipi típic del país, cada muni hi pesa igual). */
	mediana_catalunya?: number | null;
	/** Municipis de Catalunya amb dada — denominador de `mediana_catalunya`. */
	n_mediana_catalunya?: number;
	/** Ponderada de la comarca i el seu denominador. */
	ponderada_comarca?: number | null;
	hab_ponderada_comarca?: number | null;
	/** ⛔ ESTRATIFICADA PER FRANJA DE POBLACIÓ — NO ES PINTA (doctrina «QUINES ES PINTEN»): amb
	 *  la variància AJUSTADA, la comarca explica millor que la mida a 8 de les 9 mètriques amb
	 *  rang. Se serveix per si un dia la resposta canvia; `verify-govern.mjs` cau si arriba a la
	 *  pantalla. */
	mediana_franja?: number | null;
	n_franja?: number;
}

/** Entrada d'un municipi: la seva comarca + les cel·les de rang per mètrica. */
export interface GovernEntry {
	comarca: string;
	/** Franja de mida del municipi (R-REFERENCIA). Servida, no pintada — vegeu `mediana_franja`. */
	franja_poblacio?: string | null;
	metrics: Record<string, GovernCell>;
}

/** Artefacte sencer, indexat per INE5. */
export type GovernData = Record<string, GovernEntry>;
