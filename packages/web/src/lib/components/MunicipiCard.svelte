<script lang="ts">
	/**
	 * Fitxa d'un municipi per al "resum": capçalera amb el nom i el rànquing IETR,
	 * i una llista d'indicadors (etiquetes del contracte + valors formatats).
	 * Les caveats del contracte (note.ca/.es) es mostren visibles — especialment
	 * les ecològiques de la dimensió política, com demana la spec.
	 */
	import type { MetricKey, MetricValue, MunicipiRow, MunicipisDataset } from '$lib/contract/types';
	import { currentLocale, pick } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import MetricRow from './MetricRow.svelte';

	interface Props {
		row: MunicipiRow;
		dataset: MunicipisDataset;
		/** Ordre d'indicadors a mostrar a la fitxa. */
		keys: MetricKey[];
	}
	let { row, dataset, keys }: Props = $props();

	const locale = $derived(currentLocale());

	const rankDef = $derived(dataset.metrics.IETR_rank);
	const rankValue = $derived(row.values.IETR_rank);

	// Caveats úniques a mostrar al peu de la fitxa (evitem duplicats de la mateixa nota).
	const notes = $derived(
		Array.from(
			new Map(
				keys
					.map((k) => dataset.metrics[k])
					.filter((d) => d.note && row.values[d.key] !== null && row.values[d.key] !== undefined)
					.map((d) => [pick(d.note!, locale), pick(d.note!, locale)])
			).values()
		)
	);

	function valueOf(k: MetricKey): MetricValue | undefined {
		return row.values[k];
	}
</script>

<article class="card">
	<header class="card__head">
		<h3 class="card__name">{row.nom}</h3>
		<div class="card__rank">
			<span class="card__rank-label">{m.card_rank_label()}</span>
			<span class="card__rank-value">
				{#if rankValue !== null && rankValue !== undefined}
					{m.card_rank_value({ rank: String(rankValue), total: String(dataset.comarca.num_municipis) })}
				{:else}
					{m.value_not_available()}
				{/if}
			</span>
		</div>
		<div class="card__code">INE {row.ine5}</div>
	</header>

	<dl class="card__metrics">
		{#each keys as key (key)}
			<MetricRow def={dataset.metrics[key]} value={valueOf(key)} highlight={key === 'IETR'} />
		{/each}
	</dl>

	{#if notes.length > 0}
		<footer class="card__notes">
			{#each notes as note (note)}
				<p class="card__note">{note}</p>
			{/each}
		</footer>
	{/if}
</article>

<style>
	.card {
		background: var(--dp-color-surface);
		border: 1px solid var(--dp-color-border);
		border-radius: var(--dp-radius);
		padding: var(--dp-space-5);
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-3);
	}

	.card__head {
		display: grid;
		grid-template-columns: 1fr auto;
		align-items: start;
		gap: var(--dp-space-2);
	}

	.card__name {
		margin: 0;
		font-size: 1.4rem;
		grid-column: 1;
	}

	.card__rank {
		grid-column: 2;
		grid-row: 1 / span 2;
		text-align: right;
		display: flex;
		flex-direction: column;
		align-items: flex-end;
	}

	.card__rank-label {
		font-size: 0.68rem;
		color: var(--dp-color-muted);
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.card__rank-value {
		font-size: 1.1rem;
		font-weight: 700;
		color: var(--dp-color-accent);
		font-variant-numeric: tabular-nums;
	}

	.card__code {
		grid-column: 1;
		font-family: var(--dp-font-mono);
		font-size: 0.72rem;
		color: var(--dp-color-muted);
	}

	.card__metrics {
		margin: 0;
	}

	.card__notes {
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-2);
		border-left: 3px solid var(--dp-color-warning);
		padding-left: var(--dp-space-3);
	}

	.card__note {
		margin: 0;
		font-size: 0.78rem;
		color: var(--dp-color-muted);
		font-style: italic;
	}
</style>
