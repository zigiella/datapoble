/**
 * Càrrega de la secció Licitacions (`/licitacions` · `/es/licitacions`).
 *
 * Tira de l'artefacte del cabal `data/web/licitacions-bergueda.json` (el genera
 * `tools/export_licitacions.py` des de `packages/signals`, copiat a `static/data/` al
 * prebuild). Prerender-safe: `fetch` de SvelteKit sobre l'actiu estàtic.
 */
import { error } from '@sveltejs/kit';
import type { LicitacionsData } from '$lib/contract/licitacions';
import type { PageLoad } from './$types';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const res = await fetch('/data/licitacions-bergueda.json');
	if (!res.ok) {
		throw error(503, "Falta l'artefacte de licitacions (executa tools/export_licitacions.py).");
	}
	const licitacions = (await res.json()) as LicitacionsData;
	return { licitacions };
};
