/**
 * Municipis mirall — veïns FUNCIONALS (semblants en COMPORTAMENT, no en geografia).
 *
 * Idea del consultor («municipios espejo»): més útil que el veí geogràfic és el municipi
 * que es comporta IGUAL. Construïm un vector de senyals **per càpita / relatius** (no
 * absoluts, perquè no volem agrupar per MIDA sinó per patró), el **z-normalitzem** sobre
 * els 31 municipis (cada senyal pesa igual) i mesurem la distància euclidiana. Els `k`
 * més propers són els miralls. Tot surt del dataset (contracte); cap xifra inventada.
 */
import type { MunicipisDataset, MetricKey, MetricValue, MunicipiRow } from '$lib/contract/types';

// Vector de COMPORTAMENT: senyals per càpita / relatius (deixem fora els absoluts com la
// població o la càrrega, que agruparien per mida en lloc de per patró).
const FEATURES: MetricKey[] = [
	'gap_pernocta_pct', // pernocta relativa al padró
	'kg_hab_any', // càrrega per residus (per càpita)
	'vidre_hab', // empremta hostalera (per càpita)
	'pct_noprincipal', // habitatge no principal (%)
	'rtc_per_1000hab', // turisme reglat (densitat)
	'restauracio_per_1000hab', // restauració (densitat)
	'serveis_per_1000hab', // serveis (densitat)
	'index_envelliment' // envelliment
];

function num(v: MetricValue | undefined): number | null {
	return typeof v === 'number' && Number.isFinite(v) ? v : null;
}

export interface Mirall {
	ine5: string;
	nom: string;
	tipologia: string | null;
	dist: number;
}

/** Els `k` municipis més semblants en comportament a `ine5` (z-normalitzat, euclidià). */
export function municipisMirall(dataset: MunicipisDataset, ine5: string, k = 5): Mirall[] {
	const munis = Object.values(dataset.municipis);
	const target = dataset.municipis[ine5];
	if (!target || munis.length < 2) return [];

	// Estadístics per característica (mitjana + desviació) per z-normalitzar: cada senyal pesa igual.
	const stats = FEATURES.map((f) => {
		const vals = munis.map((m) => num(m.values[f])).filter((v): v is number => v !== null);
		const mean = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
		const variance = vals.length
			? vals.reduce((a, b) => a + (b - mean) ** 2, 0) / vals.length
			: 0;
		return { mean, sd: Math.sqrt(variance) || 1 };
	});

	const vec = (m: MunicipiRow): number[] =>
		FEATURES.map((f, i) => {
			const v = num(m.values[f]);
			return v === null ? 0 : (v - stats[i].mean) / stats[i].sd; // absent → mitjana (neutre)
		});

	const tv = vec(target);
	return munis
		.filter((m) => m.ine5 !== ine5)
		.map((m) => {
			const mv = vec(m);
			const dist = Math.sqrt(tv.reduce((acc, t, i) => acc + (t - mv[i]) ** 2, 0));
			return {
				ine5: m.ine5,
				nom: m.nom,
				tipologia: typeof m.values.tipologia === 'string' ? m.values.tipologia : null,
				dist
			};
		})
		.sort((a, b) => a.dist - b.dist)
		.slice(0, k);
}
