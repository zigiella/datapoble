/**
 * DISTINGIBILITAT I COL·LISIÓ — port 1:1 de la doctrina de l'experiment geo-rag
 * (`packages/geo-rag`: `distinguish.py` i `descriptions.py::_collision_groups`).
 *
 * UNA sola regla per a totes les alçades del «no ho distingeixo»:
 *  - Dos municipis només es poden ORDENAR si les seves bandes NO se solapen
 *    (`bandsOverlap` → false). Si s'encavalquen, l'ordre no s'afirma.
 *  - La COL·LISIÓ és el cas límit a distància zero: el model dona exactament la
 *    mateixa estimació i banda a municipis diferents → la xifra NO és específica
 *    de cap d'ells, i la fitxa ho ha d'advertir (mai el número nu).
 *
 * Tot és JS pur sobre `pernocta-catalunya.json` (que ja viatja al client): cap
 * servidor, cap dependència nova. CANDAU per al futur: qualsevol pantalla que
 * vulgui mostrar municipis ORDENATS per presència ha de passar per `bandsOverlap`
 * abans d'afirmar un ordre.
 */
import type { PernoctaMuni } from './pernocta';

/** True si les dues bandes s'encavalquen → l'ordre entre elles NO es pot afirmar. */
export function bandsOverlap(aLow: number, aHigh: number, bLow: number, bHigh: number): boolean {
	return Math.max(aLow, bLow) <= Math.min(aHigh, bHigh);
}

export interface CollisionPeer {
	ine5: string;
	nom: string;
	/** ETCA oficial del peer (si en té): la font oficial SÍ distingeix els municipis. */
	etca_oficial: number | null;
}

/**
 * Municipis amb EXACTAMENT la mateixa (estimació, banda) que `ine5` — el grup de
 * col·lisió del model, a escala de tot el fitxer (tota Catalunya). Ordenats per nom.
 */
export function collisionPeers(
	munis: Record<string, PernoctaMuni>,
	ine5: string
): CollisionPeer[] {
	const self = munis[ine5];
	if (!self) return [];
	const out: CollisionPeer[] = [];
	for (const [k, v] of Object.entries(munis)) {
		if (k === ine5) continue;
		if (
			v.estimacio === self.estimacio &&
			v.rang_baix === self.rang_baix &&
			v.rang_alt === self.rang_alt
		) {
			out.push({ ine5: k, nom: v.nom, etca_oficial: v.etca_oficial ?? null });
		}
	}
	out.sort((a, b) => a.nom.localeCompare(b.nom, 'ca'));
	return out;
}
