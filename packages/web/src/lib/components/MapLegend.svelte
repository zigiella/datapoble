<script lang="ts">
	/**
	 * Llegenda del mapa coroplètic (sistema.css → `.legend`).
	 * Requisits (palette.md §6): capçalera amb MÈTODE + Nº DE CLASSES, cada tram amb el seu
	 * RANG numèric (cifres tabulars), entrada explícita de "sense dada" (tramat), i la
	 * FONT·DATA de la mètrica (contracte: cap número sense procedència).
	 */
	import type { MetricDef } from '$lib/contract/types';
	import type { Classification } from '$lib/map/classify';
	import { classRangeLabels } from '$lib/map/classify';
	import { rampColors, NODATA } from '$lib/map/palette';
	import { pick, currentLocale } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';

	interface Props {
		def: MetricDef;
		classification: Classification;
	}
	let { def, classification }: Props = $props();

	const locale = $derived(currentLocale());
	const colors = $derived(rampColors(classification.classes));
	const ranges = $derived(classRangeLabels(classification, def.format, locale));
	const methodLabel = $derived(
		classification.method === 'quantiles' ? m.map_method_quantiles() : m.map_method_jenks()
	);
</script>

<aside class="legend" aria-label="Llegenda del mapa">
	<div class="legend__hd">
		<span class="legend__metric">{pick(def.label, locale)}</span>
		<span class="legend__method"
			>{m.map_legend_method_caption({
				method: methodLabel,
				classes: m.map_legend_classes({ n: String(classification.classes) })
			})}</span
		>
	</div>

	<div class="legend__bar">
		{#each colors as c, i (i)}
			<i style="background:{c}" title={ranges[i]}></i>
		{/each}
	</div>

	<ol class="legend__ranges tnum">
		{#each ranges as r, i (i)}
			<li><span class="legend__chip" style="background:{colors[i]}"></span>{r}</li>
		{/each}
	</ol>

	<div class="legend__nodata">
		<span class="legend__hatch" style="background-color:{NODATA}"></span>
		<span>{m.map_legend_nodata()}</span>
	</div>

	<div class="legend__foot">
		<div>
			<span class="legend__lbl">{m.map_legend_source()}:</span>
			{def.source}{#if def.date}<span class="legend__sep">·</span><span class="legend__lbl"
					>{m.map_legend_date()}:</span
				> {def.date}{/if}
		</div>
		<p class="legend__caveat">{m.map_classes_note()}</p>
	</div>
</aside>

<style>
	/* Reaprofitem `.legend*` de sistema.css; afegim el detall propi de Mirador. */
	.legend__metric {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 0.92rem;
		color: var(--dp-text);
		text-transform: none;
		letter-spacing: 0;
		display: block;
		margin-bottom: 2px;
	}
	.legend__method {
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		color: var(--dp-text-subtle);
		text-transform: none;
		letter-spacing: 0;
	}
	.legend__ranges {
		list-style: none;
		margin: 10px 0 0;
		padding: 0;
		display: grid;
		gap: 3px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		color: var(--dp-text-muted);
	}
	.legend__ranges li {
		display: flex;
		align-items: center;
		gap: 7px;
	}
	.legend__chip {
		width: 11px;
		height: 11px;
		border-radius: 2px;
		flex: none;
		border: 1px solid color-mix(in srgb, var(--dp-text) 12%, transparent);
	}
	.legend__hatch {
		width: 14px;
		height: 14px;
		border-radius: 2px;
		flex: none;
		border: 1px solid var(--dp-border-strong);
		background-image: repeating-linear-gradient(
			45deg,
			transparent 0 2px,
			rgba(90, 96, 102, 0.55) 2px 3px
		);
	}
	.legend__lbl {
		color: var(--dp-text-subtle);
	}
	.legend__sep {
		margin: 0 6px;
		color: var(--dp-border-strong);
	}
	.legend__caveat {
		margin: 6px 0 0;
		font-size: 0.6rem;
		color: var(--dp-text-subtle);
		line-height: 1.4;
		text-transform: none;
		letter-spacing: 0;
	}
</style>
