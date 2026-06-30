/**
 * Forma de `data/web` → `static/data/metodologia-model.json` (la genera `copy-data.mjs` des dels CSV
 * d'anàlisi committejats: calibracio_intervals, discrepancia_etca_pernocta, nivellc_analisi).
 *
 * Són els tres gràfics germans de la secció «límits del model» de /metodologia: la calibració dels
 * intervals (reliability), el contrast ETCA↔pernocta (scatter, amb la partició senyal/soroll) i el
 * règim dens (consum domèstic per càpita vs densitat). Frontera honesta: la UI només els llegeix.
 */

export interface MetodologiaModel {
	/** Reliability: per nivell nominal (n), la cobertura empírica held-out (e). */
	reliability: { n: number; e: number }[];
	/** Cobertura empírica de l'interval nominal del 80% (la xifra clau). */
	interval80: number | null;
	/** Cobertura de l'interval 80% per tipus territorial, amb la n. Ordenat per n desc. La UI marca
	 *  «n massa petita» quan no es pot validar el tipus per separat (falsa precisió). */
	perTipus?: { tipus: string; e: number; n: number }[];
	discrepancia: {
		n: number;
		oposat: number;
		senyal: number;
		soroll: number;
		etca_min: number;
		/** Un punt per muni amb ETCA: x = la nostra pernocta (gap %), y = ETCA (gap %), cls = c|s|n. */
		punts: { x: number; y: number; cls: 'c' | 's' | 'n' }[];
	};
	regim: {
		/** Mediana de consum domèstic per càpita (kWh/resident) a la calibració. */
		mediana: number | null;
		/** Un punt per muni: d = densitat (hab/km²), k = kWh domèstic/càpita. */
		punts: { d: number; k: number }[];
	};
}
