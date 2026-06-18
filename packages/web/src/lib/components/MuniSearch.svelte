<script lang="ts">
	/**
	 * Buscador de municipis — el cor de la Home «La Llera» (cercador primer).
	 *
	 * Cerca client-side sobre el CATÀLEG de TOTS els municipis de Catalunya (~947), no només els
	 * del dataset: qualsevol poble es pot trobar i la seva fitxa mostra dada/rang o un «sense dades
	 * encara» digne. Insensible a accents/apòstrofs via `toSlug`. Triar un resultat (clic o Enter)
	 * navega a /municipi/<slug>. Els municipis amb dades del Berguedà porten el xip de TIPOLOGIA.
	 * Estil: classes `.home-search*` (Llegenda). Accessible: combobox amb fletxes + activedescendant.
	 */
	import { goto } from '$app/navigation';
	import { toSlug } from '$lib/contract/slug';
	import { tipologiaLabel, tipologiaColor } from '$lib/map/tipologia';
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import type { MunicipisDataset } from '$lib/contract/types';
	import type { MuniCataleg } from '$lib/contract/cataleg';

	// `cataleg` = tots els munis (cens de noms+codis); `dataset` = els que tenen dades (xip tipologia).
	let { cataleg, dataset }: { cataleg: MuniCataleg[]; dataset: MunicipisDataset } = $props();

	const norm = (s: string) => toSlug(s).replace(/-/g, ' ');

	// Índex de cerca (estable): tot el catàleg. El slug es deriva del nom (toSlug); coincideix amb
	// el dels enllaços del Berguedà i dels coberts (convergeixen, vegeu `contract/slug`).
	const index = $derived(
		cataleg
			.map((muni) => ({
				ine5: muni.ine5,
				nom: muni.nom,
				slug: toSlug(muni.nom),
				norm: norm(muni.nom),
				tipologia: dataset.municipis[muni.ine5]?.values?.tipologia
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
