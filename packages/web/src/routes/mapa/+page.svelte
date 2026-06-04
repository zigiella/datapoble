<script lang="ts">
	/**
	 * Pantalla "Mapa coroplètic" (F2, Mirador) — pilot Berguedà.
	 *
	 * Coroplètic amb la rampa "exposició" (5 classes per defecte; cuantils per IETR, Jenks per
	 * magnituds crues — palette.md §5), tramat per "sense dada", basemap apagat (--dp-map-*),
	 * llegenda amb mètode·classes·font·data, selector d'indicador i tooltip amb procedència.
	 *
	 * Dades: dataset MOCK amb forma de contracte (es cablejarà al mart/API real). Geometria:
	 * GeoJSON oficial dels municipis (INE/IGN), carregat com a actiu estàtic.
	 */
	import { browser } from '$app/environment';
	import ChoroplethMap from '$lib/components/ChoroplethMap.svelte';
	import MapLegend from '$lib/components/MapLegend.svelte';
	import MapIndicatorPicker from '$lib/components/MapIndicatorPicker.svelte';
	import MapTooltip from '$lib/components/MapTooltip.svelte';
	import { MAP_INDICATORS, DEFAULT_INDICATOR } from '$lib/map/indicators';
	import { classify, methodFor } from '$lib/map/classify';
	import type { MetricKey } from '$lib/contract/types';
	import { m } from '$lib/paraglide/messages';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const geojson = $derived(data.geojson);

	let indicator = $state<MetricKey>(DEFAULT_INDICATOR);

	// Sèrie de valors de l'indicador actiu sobre TOTS els municipis de la geometria
	// (no només els del mock amb dada): així la classificació és sobre el conjunt real.
	const series = $derived(
		geojson.features.map((f: import('geojson').Feature) => {
			const ine5 = (f.properties?.ine5 as string) ?? '';
			return dataset.municipis[ine5]?.values?.[indicator] ?? null;
		})
	);

	const classification = $derived(classify(series, methodFor(indicator)));
	const def = $derived(dataset.metrics[indicator]);

	// Tooltip (posició + contingut), emès pel mapa.
	interface Hover {
		ine5: string;
		nom: string;
		value: number | string | null;
		x: number;
		y: number;
	}
	let hover = $state<Hover | null>(null);
</script>

<svelte:head>
	<title>{m.map_title()} · {m.app_name()}</title>
</svelte:head>

<section class="mapscreen">
	<header class="mapscreen__head">
		<h1>{m.map_title()}</h1>
		<p class="mapscreen__intro">
			{m.map_intro({ count: String(dataset.comarca.num_municipis) })}
		</p>
	</header>

	<div class="mapscreen__controls">
		<MapIndicatorPicker {dataset} options={MAP_INDICATORS} bind:value={indicator} />
	</div>

	<div class="mapscreen__grid">
		<div class="mapscreen__mapwrap">
			{#if browser}
				<ChoroplethMap
					{dataset}
					{geojson}
					{indicator}
					{classification}
					onhover={(p) => (hover = p)}
				/>
				{#if hover}
					<MapTooltip nom={hover.nom} {def} value={hover.value} x={hover.x} y={hover.y} />
				{/if}
			{:else}
				<div class="mapscreen__ssr" aria-hidden="true">{m.map_loading()}</div>
			{/if}
		</div>

		<div class="mapscreen__side">
			<MapLegend {def} {classification} />
			<p class="mapscreen__caveat">{m.map_data_caveat()}</p>
		</div>
	</div>
</section>

<style>
	.mapscreen {
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-5);
	}
	.mapscreen__head h1 {
		font-size: 2rem;
	}
	.mapscreen__intro {
		max-width: 62ch;
		color: var(--dp-text-muted);
		margin: 0;
	}
	.mapscreen__grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: var(--dp-space-5);
	}
	.mapscreen__mapwrap {
		position: relative;
	}
	.mapscreen__ssr {
		width: 100%;
		height: clamp(360px, 60vh, 620px);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--dp-text-subtle);
		background: var(--dp-map-land, #f2f1ec);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-lg);
		font-family: var(--dp-font-mono);
		font-size: 0.8rem;
	}
	.mapscreen__side {
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-3);
	}
	.mapscreen__caveat {
		max-width: 360px;
		margin: 0;
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		line-height: 1.5;
		color: var(--dp-text-subtle);
	}

	@media (min-width: 64rem) {
		.mapscreen__grid {
			grid-template-columns: minmax(0, 1fr) 360px;
			align-items: start;
		}
	}
</style>
