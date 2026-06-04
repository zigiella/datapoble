<script lang="ts">
	/**
	 * Targeta KPI: una xifra comarcal amb la seva etiqueta (del contracte),
	 * unitat i procedència. L'etiqueta i la unitat es prenen de `MetricDef`
	 * (label.ca/.es), MAI es codifiquen al component.
	 */
	import type { MetricDef, MetricValue } from '$lib/contract/types';
	import { currentLocale, pick } from '$lib/i18n';
	import { formatMetric } from '$lib/format';
	import { m } from '$lib/paraglide/messages';

	interface Props {
		def: MetricDef;
		value: MetricValue | undefined;
	}
	let { def, value }: Props = $props();

	const locale = $derived(currentLocale());
	const label = $derived(pick(def.label, locale));
	const unit = $derived(pick(def.unit, locale));
	const formatted = $derived(formatMetric(value, def, locale));
</script>

<div class="kpi">
	<div class="kpi__value">
		{#if formatted !== null}
			<span class="kpi__num">{formatted}</span>
			{#if def.format === 'percent'}{:else if unit && unit !== '%'}<span class="kpi__unit"
					>{unit}</span
				>{/if}
		{:else}
			<span class="kpi__num kpi__na">{m.value_not_available()}</span>
		{/if}
	</div>
	<div class="kpi__label">{label}</div>
	<div class="kpi__meta">
		<span>{m.metric_source()}: {def.source}</span>
		{#if def.date}<span>· {m.metric_date()}: {def.date}</span>{/if}
	</div>
</div>

<style>
	.kpi {
		background: var(--dp-surface);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius);
		padding: var(--dp-space-4);
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-1);
	}

	.kpi__value {
		display: flex;
		align-items: baseline;
		gap: var(--dp-space-2);
	}

	.kpi__num {
		font-size: 1.9rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		color: var(--dp-forest);
	}

	.kpi__na {
		color: var(--dp-text-muted);
		font-weight: 600;
	}

	.kpi__unit {
		font-size: 0.85rem;
		color: var(--dp-text-muted);
	}

	.kpi__label {
		font-weight: 600;
		font-size: 0.95rem;
	}

	.kpi__meta {
		font-size: 0.72rem;
		color: var(--dp-text-muted);
		display: flex;
		flex-wrap: wrap;
		gap: var(--dp-space-1);
	}
</style>
