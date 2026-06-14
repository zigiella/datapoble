/**
 * Contracte de la LECTURA-IA de fitxa (§3) — la forma de `data/web/lectures.bergueda.json`.
 *
 * La genera el pipeline `tools/gen_fitxa.py` (escriptor opus-4.8 es → traductor sonnet-4.6 ca,
 * amb verificador determinista de xifres). Frontera honesta: la UI NOMÉS llegeix aquest
 * artefacte, mai l'edita. Cada `claim` porta el seu `to` (naturalesa epistèmica) i la seva
 * `evidencia` (claus de mètrica del contracte), perquè cada frase sigui traçable fins a la font.
 *
 * Si una banda no va superar la verificació, ve marcada `_gen:"fallback"` amb el `veredicte`
 * buit i les `lectures` buides: la UI ho detecta i degrada (mostra els cinc números i la
 * maquinària, sense la lectura narrativa). Mai una al·lucinació, mai una pantalla trencada.
 */

/** Naturalesa epistèmica d'una afirmació (mateix vocabulari que la procedència del mapa). */
export type LectTo = 'mesura' | 'inferencia' | 'interpretacio';

/** Una afirmació de lectura: text + naturalesa + claus de mètrica que la sostenen. */
export interface LectClaim {
	text: string;
	to: LectTo;
	evidencia: string[];
}

/** Bloc amb evidència però sense `to` (veredicte, contra-lectura). */
export interface LectEvidenced {
	text: string;
	evidencia: string[];
}

export interface LectPreguntes {
	propies: string[];
	comarca: string[];
	miralls: string[];
}

export interface LectConfianca {
	nivell: 'alta' | 'mitjana' | 'baixa';
	motius: string[];
}

/** Lectura completa d'un municipi en UN idioma. */
export interface Lectura {
	ine5: string;
	veredicte: LectEvidenced;
	perfil_public?: string;
	lectures: {
		ciutadania: LectClaim[];
		visitant: LectClaim[];
		govern: LectClaim[];
	};
	contra_lectura: LectEvidenced;
	dades_que_falten?: string[];
	preguntes: LectPreguntes;
	confianca: LectConfianca;
	/** Procedència de la redacció: del model o de la reserva determinista. */
	_gen?: 'model' | 'fallback';
}

/** Una entrada de l'artefacte: la lectura en els dos idiomes. */
export interface LecturaEntry {
	ca: Lectura;
	es: Lectura;
}

/** L'artefacte sencer: `{ine5: {ca, es}}`. */
export type LecturesData = Record<string, LecturaEntry>;
