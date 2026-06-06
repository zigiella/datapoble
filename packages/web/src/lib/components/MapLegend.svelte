<script lang="ts">
	/**
	 * Llegenda del mapa coroplètic (sistema.css → `.legend`).
	 * Requisits (palette.md §6): capçalera amb MÈTODE + Nº DE CLASSES, cada tram amb el seu
	 * RANG numèric (cifres tabulars), entrada explícita de "sense dada" (tramat), i la
	 * FONT·DATA de la mètrica (contracte: cap número sense procedència).
	 *
	 * Per a la família d'estimació de població (gap / presència real) afegeix:
	 *  - un distintiu "estimació" (procedència morada) al costat del nom;
	 *  - una entrada de "confiança baixa" (el tractament tramat del mapa);
	 *  - un caveat que recorda que és inferència i es llegeix com a rang (contracte).
	 */
	import type { MetricDef, MetricKey } from '$lib/contract/types';
	import type { Classification } from '$lib/map/classify';
	import { classRangeLabels } from '$lib/map/classify';
	import { rampColors, divergingColors, NODATA } from '$lib/map/palette';
	import { pick, currentLocale } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';

	interface Props {
		/** Clau de la mètrica activa (per al format de rangs i les notes d'estimació). */
		metricKey: MetricKey;
		def: MetricDef;
		classification: Classification;
	}
	let { metricKey, def, classification }: Props = $props();

	const locale = $derived(currentLocale());
	const isDiverging = $derived(
		classification.method === 'diverging' && classification.center !== undefined
	);
	const colors = $derived(
		isDiverging
			? divergingColors(classification.domain, classification.center as number)
			: rampColors(classification.classes)
	);
	const ranges = $derived(classRangeLabels(classification, def.format, locale, metricKey));
	const methodLabel = $derived(
		classification.method === 'quantiles'
			? m.map_method_quantiles()
			: classification.method === 'diverging'
				? m.map_method_diverging()
				: m.map_method_jenks()
	);

	/** Capes d'estimació (model v2 de 3 capes + àlies) → mostren el caveat d'inferència. */
	const ESTIMATE_KEYS = new Set<MetricKey>([
		'gap_pernocta_pct',
		'gap_pernocta',
		'poblacio_pernocta_est',
		'carrega_total_est',
		'index_turisme',
		'gap_pct',
		'gap_abs',
		'poblacio_real_est',
		'poblacio_real_rel'
	]);
	const isEstimate = $derived(ESTIMATE_KEYS.has(metricKey));
</script>

<aside class="legend" aria-label="Llegenda del mapa">
	<div class="legend__hd">
		<span class="legend__metric"
			>{pick(def.label, locale)}{#if isEstimate}<span class="legend__est"
					>{m.map_legend_estimate_badge()}</span
				>{/if}</span
		>
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

	{#if isEstimate}
		<div class="legend__nodata legend__lowconf">
			<span class="legend__hatch legend__hatch--lowconf"></span>
			<span>{m.map_legend_lowconf()}</span>
		</div>
	{/if}

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
		{#if isEstimate}
			<p class="legend__caveat legend__caveat--est">{m.map_gap_legend_caveat()}</p>
		{/if}
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
	/* Mostra de confiança baixa: tramat fosc damunt d'un to càlid tènue (com es veu al mapa). */
	.legend__hatch--lowconf {
		background-color: color-mix(in srgb, var(--dp-div-4, #dfc27d) 45%, var(--dp-surface));
		background-image: repeating-linear-gradient(
			45deg,
			transparent 0 2px,
			rgba(36, 40, 46, 0.42) 2px 3px
		);
	}
	.legend__lowconf {
		margin-top: 7px;
	}
	.legend__est {
		display: inline-block;
		margin-left: 6px;
		padding: 1px 5px;
		border-radius: 999px;
		font-family: var(--dp-font-mono);
		font-size: 0.54rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-prov-derived, #7a5ba6);
		background: color-mix(in srgb, var(--dp-prov-derived, #7a5ba6) 14%, transparent);
		vertical-align: middle;
	}
	.legend__caveat--est {
		color: var(--dp-prov-derived, #7a5ba6);
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
