/**
 * Tipus de l'artefacte de validació externa contra ETCA (Pas 4 · spec §2.3).
 * Forma exacta de `data/web/etca-validacio.json`, generat per `tools/validacio_etca.py`
 * (comparació de la nostra inferència de presència amb la Població ETCA d'Idescat).
 */

/** Resum d'una mètrica nostra vs ETCA sobre els municipis coberts. */
export interface EtcaSummary {
	n: number;
	spearman: number;
	error_median_pct: number;
	passa: boolean;
}

/** Fila per municipi (tots els del pilot; `covered=false` si no té ETCA municipal). */
export interface EtcaMuni {
	ine5: string;
	municipi: string;
	padro: number | null;
	etca: number | null;
	pernocta_est: number | null;
	err_pernocta_pct: number | null;
	carrega_funcional_est: number | null;
	err_carrega_pct: number | null;
	covered: boolean;
}

export interface EtcaValidacio {
	font: string;
	base: string | null;
	any: string | null;
	go_no_go: { rho_min: number; error_max_pct: number };
	pernocta_vs_etca: EtcaSummary | null;
	carrega_vs_etca: EtcaSummary | null;
	municipis: EtcaMuni[];
}
