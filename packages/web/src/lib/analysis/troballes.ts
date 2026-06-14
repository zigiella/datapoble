/**
 * Troballes deterministes per a la Home (datapoble · Mirador).
 *
 * Una «troballa» és un FET rellevant extret de les dades amb regles deterministes (cap LLM):
 * els extrems honestos del territori. v1 = 4 detectors sobre el dataset real (i licitacions):
 *  - `gap`  el municipi amb més gap de pernocta (gent que el padró no compta) — INFERÈNCIA.
 *  - `ietr` el #1 d'exposició territorial (IETR_rank) — INFERÈNCIA (índex derivat).
 *  - `div`  el de més divergència de senyals (el «no honest»: els senyals es contradiuen).
 *  - `lic`  el de més contractació pròpia (de licitacions-bergueda.json) — MESURA.
 *
 * Cada troballa torna NOMÉS dades estructurades (kind + municipi + valor + to + slug); el text P1
 * el posa la pàgina via i18n (`home_troballa_*`), perquè el relat sigui bilingüe i «cap xifra sense
 * procedència». L'ordre és estable (gap, ietr, div, lic) → sortida determinista.
 */
import type { MunicipisDataset, MetricKey } from '$lib/contract/types';
import { slugForIne5 } from '$lib/contract/slug';

export type TroballaKind = 'gap' | 'ietr' | 'div' | 'lic';

export interface Troballa {
	kind: TroballaKind;
	ine5: string;
	nom: string;
	slug: string;
	/** El número que sosté la troballa (sempre amb procedència via `to`). */
	valor: number;
	/** Naturalesa de la dada: punt slate (mesura) o porpra (inferència/interpretació). */
	to: 'mesura' | 'inferencia' | 'interpretacio';
}

/** Forma mínima de l'artefacte de licitacions que ens cal (data/web/licitacions-bergueda.json). */
export interface LicitacionsPayload {
	municipis: { ine5: string; nom: string; n_contractes_municipal: number }[];
}

/** Municipi (ine5) amb el valor numèric màxim d'una mètrica; null si cap en té. */
function argMaxMetric(
	dataset: MunicipisDataset,
	key: MetricKey,
	opts: { min?: number; exclude?: ReadonlySet<string> } = {}
): { ine5: string; nom: string; value: number } | null {
	let best: { ine5: string; nom: string; value: number } | null = null;
	for (const [ine5, row] of Object.entries(dataset.municipis)) {
		if (opts.exclude?.has(ine5)) continue;
		const raw = row.values?.[key];
		if (typeof raw !== 'number' || Number.isNaN(raw)) continue;
		if (opts.min !== undefined && raw < opts.min) continue;
		if (!best || raw > best.value) best = { ine5, nom: row.nom, value: raw };
	}
	return best;
}

/** «Quar, la» → «la Quar» · «Espunyola, l'» → «l'Espunyola» (per llegir-ho dins d'una frase). */
function displayNom(nom: string): string {
	const mt = nom.match(/^(.+),\s*(l['’]|les|els|la|el)$/i);
	if (!mt) return nom;
	const [, base, art] = mt;
	return /['’]$/.test(art) ? `${art}${base}` : `${art} ${base}`;
}

/**
 * Construeix la llista de troballes (ordre estable: gap, ietr, div, lic). DEDUPLICA per municipi:
 * cada troballa és d'un municipi DIFERENT (un mateix poble no domina dues targetes).
 */
export function buildTroballes(dataset: MunicipisDataset, lic?: LicitacionsPayload | null): Troballa[] {
	const out: Troballa[] = [];
	const used = new Set<string>();
	const push = (kind: TroballaKind, hit: { ine5: string; nom: string }, to: Troballa['to'], valor: number) => {
		used.add(hit.ine5);
		out.push({ kind, ine5: hit.ine5, nom: displayNom(hit.nom), slug: slugForIne5(hit.ine5, dataset), valor, to });
	};

	// gap de pernocta màxim (positiu): on els senyals veuen més gent que el padró.
	const gap = argMaxMetric(dataset, 'gap_pernocta_pct', { min: 0, exclude: used });
	if (gap) push('gap', gap, 'inferencia', Math.round(gap.value));

	// #1 d'exposició territorial (IETR màxim).
	const ietr = argMaxMetric(dataset, 'IETR', { exclude: used });
	if (ietr) push('ietr', ietr, 'inferencia', Math.round(ietr.value));

	// Divergència de senyals més alta (el «no honest»: els senyals es contradiuen).
	const div = argMaxMetric(dataset, 'divergencia_senyals', { min: 1, exclude: used });
	if (div) push('div', div, 'interpretacio', Math.round(div.value));

	// Contractació pròpia màxima (de licitacions): MESURA.
	if (lic?.municipis?.length) {
		let licTop: { ine5: string; nom: string; n: number } | null = null;
		for (const mun of lic.municipis) {
			if (used.has(mun.ine5)) continue;
			const n = mun.n_contractes_municipal ?? 0;
			if (!licTop || n > licTop.n) licTop = { ine5: mun.ine5, nom: mun.nom, n };
		}
		if (licTop && licTop.n > 0 && dataset.municipis[licTop.ine5]) push('lic', licTop, 'mesura', licTop.n);
	}

	return out;
}
