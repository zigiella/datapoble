/**
 * Contracte de la PRESÈNCIA ESTIMADA EN RANG (Nivell C) — forma de `data/web/pernocta-catalunya.json`.
 *
 * La genera `tools/export_pernocta_catalunya.py` (model base ~ densitat+renda+gas, calibrat ETCA;
 * banda p10–p90 del residual held-out per tipus). És la primera dada que el projecte publica més
 * enllà del Berguedà, sempre EN RANG (inferència, no cens). Frontera honesta: la UI només la
 * llegeix; l'ETCA oficial s'hi mostra com a validació, no com a substitut.
 */

export interface PernoctaMuni {
	nom: string;
	tipus: string;
	/** Padró (població resident registrada). */
	padro: number | null;
	/** Estimació central del model (qui dorm). Es mostra el RANG, no aquest punt sol. */
	estimacio: number;
	rang_baix: number;
	rang_alt: number;
	/** Població estacional ETCA oficial (Idescat EPE), validació; munis ≥1.000 hab. */
	etca_oficial: number | null;
	/** True si l'estimació del model cau dins ±15% de l'ETCA. */
	dins_banda: boolean;
}

export interface PernoctaData {
	metode: string;
	model: { r2: number; covariables: string[]; n_calibracio: number; validacio: string };
	nota_abast: string;
	munis: Record<string, PernoctaMuni>;
}
