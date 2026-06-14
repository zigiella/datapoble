<script lang="ts">
	/**
	 * Buscador de municipis — el cor de la Home «La Llera» (cercador primer).
	 *
	 * Cerca client-side sobre els municipis del dataset (avui els 31 del Berguedà; el mateix
	 * component escala a 947 sense canviar la UX). Insensible a accents/apòstrofs via `toSlug`.
	 * Triar un resultat (clic o Enter) navega a la fitxa /municipi/<slug>. Cada resultat porta
	 * el nom + el xip de TIPOLOGIA (color categòric del design-system). Estil: classes
	 * `.home-search*` de design-system/aplicacio.css (Llegenda). Accessible: combobox amb
	 * aria-activedescendant i navegació amb fletxes.
	 */
	import { goto } from '$app/navigation';
	import { slugForIne5, toSlug } from '$lib/contract/slug';
	import { tipologiaLabel, tipologiaColor } from '$lib/map/tipologia';
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import type { MunicipisDataset } from '$lib/contract/types';

	let { dataset }: { dataset: MunicipisDataset } = $props();

	const norm = (s: string) => toSlug(s).replace(/-/g, ' ');

	// Índex de cerca (estable): nom + forma normalitzada + slug + tipologia.
	const index = $derived(
		Object.entries(dataset.municipis)
			.map(([ine5, row]) => ({
				ine5,
				nom: row.nom,
				slug: slugForIne5(ine5, dataset),
				norm: norm(row.nom),
				tipologia: row.values?.tipologia
			}))
			.sort((a, b) => a.nom.localeCompare(b.nom, 'ca'))
	);

	let q = $state('');
	let active = $state(0);

	const results = $derived.by(() => {
		const needle = norm(q.trim());
		if (!needle) return [];
		return index.filter((m) => m.norm.includes(needle)).slice(0, 7);
	});

	$effect(() => {
		// reinicia el cursor quan canvia la cerca
		void results;
		active = 0;
	});

	const hrefFor = (slug: string) => localizeHref(`/municipi/${slug}`);

	function onkeydown(e: KeyboardEvent) {
		if (!results.length) return;
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			active = (active + 1) % results.length;
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			active = (active - 1 + results.length) % results.length;
		} else if (e.key === 'Enter') {
			e.preventDefault();
			const sel = results[active];
			if (sel) goto(hrefFor(sel.slug));
		}
	}
</script>

<div class="home-search">
	<div class="home-search__box">
		<i class="home-search__icon" aria-hidden="true">⌕</i>
		<input
			class="home-search__input"
			type="search"
			role="combobox"
			aria-expanded={results.length > 0}
			aria-controls="home-search-results"
			aria-label={m.home_search_aria()}
			placeholder={m.home_search_placeholder()}
			bind:value={q}
			{onkeydown}
			autocomplete="off"
		/>
	</div>

	{#if q.trim() && results.length === 0}
		<p class="home-search__empty">{m.home_search_empty()}</p>
	{:else if results.length}
		<ul class="home-results" id="home-search-results" role="listbox">
			{#each results as r, i (r.ine5)}
				<li role="option" aria-selected={i === active}>
					<a class="home-result" class:on={i === active} href={hrefFor(r.slug)}>
						<span class="home-result__nom">{r.nom}</span>
						{#if r.tipologia}
							<span
								class="home-result__tipo"
								style="--tipo:{tipologiaColor(r.tipologia)}">{tipologiaLabel(r.tipologia)}</span
							>
						{/if}
					</a>
				</li>
			{/each}
		</ul>
	{/if}

	<p class="home-search__scope">{m.home_search_scope()}</p>
</div>
