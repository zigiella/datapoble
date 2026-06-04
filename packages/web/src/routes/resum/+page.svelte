<script lang="ts">
	/**
	 * Pantalla "Resum" (la primera implementada).
	 * Dos blocs: (1) KPIs comarcals i (2) la comparativa de dos extrems del Berguedà,
	 * Castellar de n'Hug ↔ Berga. Tot llegit del dataset (mock amb forma de contracte)
	 * i etiquetat amb les labels del contracte (no hardcodejades) + i18n a la resta.
	 */
	import KpiCard from '$lib/components/KpiCard.svelte';
	import MunicipiCard from '$lib/components/MunicipiCard.svelte';
	import { m } from '$lib/paraglide/messages';
	import type { MetricKey } from '$lib/contract/types';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	// $derived perquè es reactivi en navegació client (no capturar només el valor inicial).
	const dataset = $derived(data.dataset);
	const featured = $derived(data.featured);

	// KPIs comarcals a destacar (subconjunt del catàleg, ordre editorial).
	// El nombre de municipis es comunica al text d'intro (no és una MetricDef).
	const comarcaKpis: MetricKey[] = [
		'poblacio',
		'rtc_total',
		'rtc_per_1000hab',
		'pct_noprincipal',
		'kg_hab_any'
	];

	// Indicadors que mostra cada fitxa de municipi (ordre editorial).
	const fichaKeys: MetricKey[] = [
		'IETR',
		'poblacio',
		'hab_total',
		'hab_noprincipal',
		'pct_noprincipal',
		'hab_per_hab',
		'rtc_total',
		'rtc_hut',
		'rtc_per_1000hab',
		'kg_hab_any',
		'pct_indep'
	];
</script>

<svelte:head>
	<title>{m.resum_title()} · {m.app_name()}</title>
</svelte:head>

<section class="resum">
	<header class="resum__header">
		<h1>{m.resum_title()}</h1>
		<p class="resum__intro">
			{m.resum_intro({ count: String(dataset.comarca.num_municipis) })}
		</p>
	</header>

	<!-- Bloc 1: KPIs comarcals -->
	<section aria-labelledby="kpis-title">
		<h2 id="kpis-title">{m.resum_kpis_title()}</h2>
		<div class="kpis">
			{#each comarcaKpis as key (key)}
				<KpiCard def={dataset.metrics[key]} value={dataset.comarca.values[key]} />
			{/each}
		</div>
	</section>

	<!-- Bloc 2: comparativa Castellar ↔ Berga -->
	<section aria-labelledby="compare-title">
		<h2 id="compare-title">{m.resum_compare_title()}</h2>
		<p class="resum__hint">{m.resum_compare_hint()}</p>
		<div class="compare">
			<MunicipiCard row={featured.castellar} {dataset} keys={fichaKeys} />
			<MunicipiCard row={featured.berga} {dataset} keys={fichaKeys} />
		</div>
	</section>
</section>

<style>
	.resum {
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-6);
	}

	.resum__header h1 {
		font-size: 2rem;
	}

	.resum__intro {
		max-width: 52ch;
		color: var(--dp-text-muted);
		margin: 0;
	}

	.resum__hint {
		max-width: 60ch;
		color: var(--dp-text-muted);
		font-size: 0.9rem;
		margin: 0 0 var(--dp-space-4);
	}

	h2 {
		font-size: 1.25rem;
		margin-bottom: var(--dp-space-4);
	}

	.kpis {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: var(--dp-space-4);
	}

	.compare {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: var(--dp-space-5);
		align-items: start;
	}
</style>
