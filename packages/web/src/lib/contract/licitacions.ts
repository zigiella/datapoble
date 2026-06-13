/**
 * Tipus de l'artefacte de Licitacions (el cabal · pilar 2).
 * Forma exacta de `data/web/licitacions-bergueda.json`, generat per
 * `tools/export_licitacions.py` des de les sortides de `packages/signals`.
 */

export interface LicitacionsTema {
	tema: string;
	n: number;
	import: number | null;
}

export interface LicitacionsMuni {
	ine5: string;
	nom: string;
	poblacio: number | null;
	import_municipal_directe: number | null;
	n_contractes_municipal: number;
	import_serveis_comarcals: number | null;
	/** Ràtio serveis comarcals / contractació pròpia. `null` = no contracta res propi. */
	dependencia_ratio: number | null;
	/** autonom · dependencia_mitjana · molt_dependent · no_contracta_propi */
	dependencia_lectura: string;
	confianca: number | null;
	temes_rebuts: { tema: string; import: number | null }[];
}

export interface LicitacionsData {
	scope: string;
	font: string;
	comarca: {
		n_contractes: number;
		n_comarcal: number;
		n_municipal: number;
		import_total: number | null;
		temes: LicitacionsTema[];
		dependencia: Record<string, number>;
	};
	municipis: LicitacionsMuni[];
}
