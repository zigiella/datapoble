<script lang="ts">
	/**
	 * Una línia "etiqueta — valor (unitat)" dins d'una fitxa de municipi.
	 * L'etiqueta surt del contracte (def.label); el valor es formata segons
	 * def.format i el locale. Si la mètrica és `planned` o el valor és null,
	 * es mostra "n. d." de manera accessible.
	 */
	import type { MetricDef, MetricValue } from '$lib/contract/types';
	import { currentLocale, pick } from '$lib/i18n';
	import { formatMetric } from '$lib/format';
	import { m } from '$lib/paraglide/messages';

	interface Props {
		def: MetricDef;
		value: MetricValue | undefined;
		/** Ressalta la fila (p. ex. l'IETR, mètrica protagonista). */
		highlight?: boolean;
	}
	let { def, value, highlight = false }: Props = $props();

	const locale = $derived(currentLocale());
	const label = $derived(pick(def.label, locale));
	const unit = $derived(pick(def.unit, locale));
	const formatted = $derived(formatMetric(value, def, locale));
	const showUnit = $derived(def.format !== 'percent' && unit && unit !== '%');
</script>

<div class="row" class:row--hl={highlight}>
	<dt class="row__label">
		{label}
		{#if def.status === 'planned'}<abbr class="row__planned" title="planned">●</abbr>{/if}
	</dt>
	<dd class="row__value">
		{#if formatted !== null}
			<span class="row__num">{formatted}</span>{#if showUnit}<span class="row__unit"
					>&nbsp;{unit}</span
				>{/if}
		{:else}
			<span class="row__na">{m.value_not_available()}</span>
		{/if}
	</dd>
</div>

<style>
	.row {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: var(--dp-space-3);
		padding: var(--dp-space-2) 0;
		border-bottom: 1px solid var(--dp-color-border);
	}

	.row--hl {
		background: var(--dp-color-accent-weak);
		margin: 0 calc(-1 * var(--dp-space-3));
		padding-left: var(--dp-space-3);
		padding-right: var(--dp-space-3);
		border-radius: var(--dp-radius-sm);
		border-bottom-color: transparent;
	}

	.row__label {
		margin: 0;
		font-size: 0.88rem;
		color: var(--dp-color-muted);
	}

	.row__planned {
		color: var(--dp-color-warning);
		font-size: 0.6rem;
		vertical-align: middle;
		text-decoration: none;
		cursor: help;
	}

	.row__value {
		margin: 0;
		text-align: right;
		white-space: nowrap;
	}

	.row__num {
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}

	.row--hl .row__num {
		color: var(--dp-color-accent);
		font-size: 1.15rem;
	}

	.row__unit {
		font-size: 0.78rem;
		color: var(--dp-color-muted);
	}

	.row__na {
		color: var(--dp-color-muted);
		font-style: italic;
	}
</style>
