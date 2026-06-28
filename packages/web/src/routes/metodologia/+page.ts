/**
 * Càrrega de dades de la pàgina de metodologia pública.
 *
 * Tira del dataset real (forma `MunicipisDataset`, font: Sondeig) NOMÉS per a les metadades
 * del contracte de cada indicador: label (ca/es), unitat, font i data, i la procedència
 * (oficial 🟦 / inferència 🟪). Així la pàgina NO codifica fonts ni dates a mà: cada fitxa surt
 * del mateix contracte semàntic (semantic/metrics.yml) que consumeix la resta del web. El text
 * explicatiu (què mesura, fórmula llegible) són missatges i18n de funcionalitat (copy nou).
 *
 * Prerender-safe: usa el `fetch` de SvelteKit sobre l'actiu estàtic, com la resta de rutes.
 */
import { loadMunicipisDataset } from '$lib/data/dataset';
import type { EtcaValidacio } from '$lib/contract/etca';
import type { MetodologiaModel } from '$lib/contract/metodologia';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const dataset = await loadMunicipisDataset(fetch);
	// Validació externa contra ETCA (Pas 4). És opcional: si l'actiu no hi és (entorn sense
	// el pipeline), la secció no es renderitza. Prerender-safe (actiu estàtic, copiat al prebuild).
	let etca: EtcaValidacio | null = null;
	try {
		const res = await fetch('/data/etca-validacio.json');
		if (res.ok) etca = (await res.json()) as EtcaValidacio;
	} catch {
		etca = null;
	}
	// Límits del model (Fase 1): reliability + scatter ETCA↔pernocta + règim dens. Opcional.
	let model: MetodologiaModel | null = null;
	try {
		const res = await fetch('/data/metodologia-model.json');
		if (res.ok) model = (await res.json()) as MetodologiaModel;
	} catch {
		model = null;
	}
	return { dataset, etca, model };
};
