<script lang="ts">
	/**
	 * Selector d'indicador del mapa. Etiquetes del contracte (MetricDef.label), no codificades.
	 * `<select>` accessible (label associat); el valor és una MetricKey.
	 */
	import type { MetricKey, MunicipisDataset } from '$lib/contract/types';
	import { pick, currentLocale } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';

	interface Props {
		dataset: MunicipisDataset;
		options: MetricKey[];
		value: MetricKey;
		onchange?: (key: MetricKey) => void;
	}
	let { dataset, options, value = $bindable(), onchange }: Props = $props();
	const locale = $derived(currentLocale());

	function handle(e: Event) {
		const key = (e.currentTarget as HTMLSelectElement).value as MetricKey;
		value = key;
		onchange?.(key);
	}
</script>

<div class="picker">
	<label class="picker__lbl" for="map-indicator">{m.map_indicator_label()}</label>
	<select id="map-indicator" class="picker__select" value={value} onchange={handle}>
		{#each options as key (key)}
			<option value={key}>{pick(dataset.metrics[key].label, locale)}</option>
		{/each}
	</select>
</div>

<style>
	.picker {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.picker__lbl {
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--dp-text-subtle);
	}
	.picker__select {
		font-family: var(--dp-font-sans);
		font-size: 0.95rem;
		font-weight: 500;
		color: var(--dp-text);
		background: var(--dp-surface);
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-sm);
		padding: 9px 12px;
		min-width: 16rem;
		cursor: pointer;
	}
	.picker__select:focus-visible {
		outline: none;
		box-shadow: var(--dp-shadow-focus);
		border-color: var(--dp-info);
	}
</style>
