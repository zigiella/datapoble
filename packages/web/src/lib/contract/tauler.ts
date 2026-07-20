/**
 * TAULER v2 — atur mensual + tendència (D7, Sondeig · D9, Mirador).
 *
 * Mirall de `data/web/tauler.bergueda.json` (`tools/export_tauler_web.py` des de
 * `mart_pols_mensual` + `mart_tendencia`), servit a `/data/tauler.json`.
 *
 * FRONTERA DURA, igual que amb el rang comarcal (C6 §4): el front NOMÉS LLEGEIX. Cap delta,
 * cap direcció, cap interval i cap període es calcula aquí — tot ve del mart, que els recalcula
 * i els compara byte a byte al seu propi verificador (`verify_tendencia.py`).
 *
 * Les tres doctrines que aquests tipus transporten (i que la UI ha d'obeir):
 *  1. **Cap fletxa sense període.** Tota entrada amb `direccio` porta `periode_actual` i
 *     `periode_anterior`. Els períodes es pinten DES D'AQUÍ, mai escrits al copy.
 *  2. **«<5» = interval, mai zero.** `valor: null` + `emmascarat: true` + `min`/`max` és el
 *     rang [1,4] del SEPE. Un delta que toqui un mes emmascarat és `delta: null` +
 *     `delta_min`/`delta_max`: un INTERVAL, no un número.
 *  3. **L'absència es declara.** `estat: 'sense_serie'` ve amb `motiu` escrit; és una fila
 *     explícita, no una absència (una absència es llegeix com un zero, un `sense_serie` no).
 */

/** Un punt de la sèrie d'atur. `valor: null` + `emmascarat` = «<5» → interval [min,max]. */
export interface AturPunt {
	/** Mes en `YYYY-MM`. */
	date: string;
	/** Aturats registrats. `null` quan el SEPE emmascara (1-4). MAI s'ha de pintar com a 0. */
	valor: number | null;
	min: number;
	max: number;
	emmascarat: boolean;
}

/** Bloc d'atur d'un municipi: l'última foto + la sèrie curta (25 mesos). */
export interface AturBloc {
	darrer: AturPunt;
	serie: AturPunt[];
}

/** Estat d'una entrada de tendència: hi ha sèrie o s'ha de dir per què no. */
export type TendenciaEstat = 'amb_serie' | 'sense_serie';

/** Quina comparació fa l'entrada (l'atur en porta DUES, i sovint discrepen). */
export type TendenciaComparacio = 'mes_anterior' | 'mateix_mes_any_anterior' | 'finestra_anual';

/**
 * Direcció afirmada pel mart. `indeterminat` NO és un buit: és la resposta quan l'interval
 * del «<5» travessa el zero i, per tant, ni el signe es pot afirmar.
 */
export type TendenciaDireccio = 'puja' | 'baixa' | 'igual' | 'indeterminat';

/** Una entrada de tendència (municipi × mètrica × comparació). */
export interface TendenciaEntry {
	estat: TendenciaEstat;
	comparacio: TendenciaComparacio | null;
	/** Motiu literal quan `estat === 'sense_serie'`. Es pinta tal qual; mai una fletxa grisa. */
	motiu: string | null;
	/** Període de la xifra actual (`2026-06` o `2025`). */
	periode_actual: string | null;
	/** Període contra el qual es compara. Sense això, no hi ha fletxa. */
	periode_anterior: string | null;
	valor_actual: number | null;
	valor_anterior: number | null;
	/** Delta exacte. `null` quan `delta_emmascarat` (llavors mana l'interval). */
	delta: number | null;
	delta_min: number | null;
	delta_max: number | null;
	delta_emmascarat: boolean;
	/** `persones` | `punts_percentuals` | … (l'emet el mart). */
	unitat_delta: string | null;
	direccio: TendenciaDireccio | null;
}

/** Entrada d'un municipi al tauler. `tendencia` és per clau de mètrica → LLISTA d'entrades. */
export interface TaulerEntry {
	ine5: string;
	nom: string;
	idescat6?: string;
	comarca?: string;
	atur: AturBloc;
	tendencia: Record<string, TendenciaEntry[]>;
}

/** Frescor + doctrina de l'atur, a l'arrel de l'artefacte (no per municipi). */
export interface TaulerMetaAtur {
	darrer_mes: string;
	mesos_serie: number;
	frescor: {
		actualitzacio: string | null;
		darrera_carrega: string | null;
		proces_refresc: string | null;
		font_frescor: string | null;
		date?: string | null;
	};
	/** Text del contracte sobre l'emmascarament «<5» del SEPE. */
	doctrina_menys_de_5?: string;
}

export interface TaulerMeta {
	atur: TaulerMetaAtur;
	tendencia?: { regla?: string; fonts?: string[] };
}

/** Artefacte sencer. */
export interface TaulerData {
	_meta: TaulerMeta;
	municipis: Record<string, TaulerEntry>;
}
