/**
 * Pobles mirall a escala Catalunya — forma de `data/municipis-mirall.json`.
 *
 * El genera `tools/deriva_miralls.py` (vector de comportament cat-escala: densitat, renda, gas, gap
 * padró↔presència, turisme/resident; z-normalitzat, euclidià, top-K bessons). Format COMPACTE per no
 * pesar a la fitxa: per a cada `ine5`, una llista de `[twinIne5, dist, codiSenyal]`. El nom i el slug
 * del bessó es resolen al web des del catàleg; el codi de senyal, a etiqueta i18n.
 *
 * És un «mapa mental», no una mesura: tota similitud és una projecció lossy (caveat a la UI).
 */

/** Una entrada crua de l'artefacte: [ine5 del bessó, distància, codi del senyal que els agermana]. */
export type MirallRaw = [string, number, string];

/** Artefacte sencer: ine5 → els seus K bessons (crus). */
export type MirallData = Record<string, MirallRaw[]>;

/** Codi de senyal → clau i18n de l'etiqueta («què els agermana»). */
export const MIRALL_SIGNAL: Record<string, string> = {
	d: 'mirall_sig_densitat',
	r: 'mirall_sig_renda',
	g: 'mirall_sig_gas',
	p: 'mirall_sig_presencia',
	t: 'mirall_sig_turisme'
};

/** Bessó ja resolt per a la UI (nom + slug del catàleg, distància, codi de senyal). */
export interface MirallVei {
	nom: string;
	slug: string;
	dist: number;
	signal: string;
}
