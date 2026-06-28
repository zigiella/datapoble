<script lang="ts">
	/**
	 * HOME «La Llera» (cercador primer) — la portada de riusdegent.
	 *
	 * Decisió Bea: la Home s'articula sobre BUSCADOR + MAPA + TROBALLES; /resum passa a subhome
	 * de comarca. Aquí: hero amb el buscador com a heroi (MuniSearch), tira de TROBALLES
	 * deterministes (extrems honestos del territori, amb procedència), MAPA coroplètic per
	 * TIPOLOGIA (suport, navega a la fitxa) i PORTES DE COMARCA (Berguedà → /resum). Funcional;
	 * el poliment fi anirà a la DA externa. Estil: design-system (classes .ap-hero/.ds-sec/.card/
	 * .dot-- i les noves .home-* d'aplicacio.css). Cap xifra sense procedència.
	 */
	import { goto } from '$app/navigation';
	import ContourField from '$lib/components/ContourField.svelte';
	import ChoroplethMap from '$lib/components/ChoroplethMap.svelte';
	import MuniSearch from '$lib/components/MuniSearch.svelte';
	import Beeswarm from '$lib/components/Beeswarm.svelte';
	import { classify, methodFor } from '$lib/map/classify';
	import { mapValue } from '$lib/map/indicators';
	import { slugForIne5, toSlug } from '$lib/contract/slug';
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import type { MetricKey } from '$lib/contract/types';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const geojson = $derived(data.geojson);
	const comarques = $derived(data.comarques);
	const vegueries = $derived(data.vegueries);
	// Presència estimada EN RANG (Nivell C): munis coberts fora del Berguedà (clau ine5). Pinten al
	// mapa a granularitat municipi i el clic hi navega (la fitxa mostra el rang).
	const pernocta = $derived(data.pernocta?.munis);
	// Catàleg de tots els munis de Catalunya (cerca a tot el país).
	const cataleg = $derived(data.cataleg);

	// Granularitat del mapa de la home. Per defecte COMARCA (decisió Bea): la home dona el cop
	// d'ull de cobertura a tot Catalunya; municipi mostra el detall del Berguedà.
	type Granularity = 'municipi' | 'comarca' | 'vegueria';
	let granularity = $state<Granularity>('comarca');
	const GRAN_OPTS: { key: Granularity; label: () => string }[] = [
		{ key: 'comarca', label: () => m.map_granularity_comarca() },
		{ key: 'vegueria', label: () => m.map_granularity_vegueria() },
		{ key: 'municipi', label: () => m.map_granularity_municipi() }
	];

	// Mapa de suport: % habitatge no principal (oficial, llegible a escala CAT). NO tipologia —els
	// llindars no generalitzen («Barcelona = excursió» trencava la credibilitat (reconducció)).
	const indicator = 'pct_noprincipal' as MetricKey;
	const series = $derived(
		geojson.features.map((f: import('geojson').Feature) =>
			mapValue(indicator, dataset.municipis[(f.properties?.ine5 as string) ?? '']?.values?.[indicator])
		)
	);
	const method = $derived(methodFor(indicator));
	const classification = $derived(classify(series, method));

	function navTo(ine5: string | null) {
		if (!ine5) return;
		if (dataset.municipis[ine5]) {
			goto(localizeHref(`/municipi/${slugForIne5(ine5, dataset)}`));
			return;
		}
		// Muni cobert en rang (Nivell C): la fitxa existeix amb la banda → hi naveguem també.
		const cov = pernocta?.[ine5];
		if (cov) goto(localizeHref(`/municipi/${toSlug(cov.nom)}`));
	}


	const heroSummits = [
		{ cx: 900, cy: 130, r0: 16, step: 23, rings: 9, sq: 0.96, seed: 1.1, lt: 0.03 },
		{ cx: 1080, cy: 290, r0: 14, step: 21, rings: 8, sq: 1.05, seed: 2.7, lt: 0.08 }
	];
	const heroLabels = ['31 municipis', '42°17′N', '1.245 m', '2°01′E'];
</script>

<svelte:head>
	<title>{m.app_name()} · {m.app_tagline()}</title>
	<meta name="description" content={m.home_lede()} />
</svelte:head>

<section data-view="home" class="on">
	<!-- HERO · el buscador com a heroi (P1: la pregunta, sense jerga) -->
	<div class="ap-hero">
		<ContourField class="ap-hero__field" viewBox="0 0 1200 380" summits={heroSummits} divis={null} labels={heroLabels} />
		<div class="ap-hero__in">
			<p class="ap-eyebrow"><span>{m.home_eyebrow()}</span></p>
			<h1>{m.home_h1()}</h1>
			<p class="lede">{m.home_lede()}</p>
			<MuniSearch {cataleg} {dataset} />
		</div>
	</div>

	<div class="ds-main">
		<!-- MAPA · el territori d'un cop d'ull (% habitatge no principal, oficial; clic → fitxa) -->
		<section class="ds-sec">
			<div class="ds-sec__hd"><span class="ref">◵</span><h2>{m.home_map_title()}</h2></div>
			<p class="lead">{m.home_map_hint()}</p>
			<!-- Abast honest «tota Catalunya»: què cobrim i per què (no fingim dada on no n'hi ha). -->
			<p class="home-map__scope">{m.home_map_scope()}</p>
			<div class="home-gran" role="group" aria-label={m.map_granularity_label()}>
				{#each GRAN_OPTS as o (o.key)}
					<button
						type="button"
						class="home-gran__btn"
						aria-pressed={granularity === o.key}
						onclick={() => (granularity = o.key)}>{o.label()}</button
					>
				{/each}
			</div>
			<div class="home-map">
				<ChoroplethMap
					{dataset}
					{geojson}
					{comarques}
					{vegueries}
					{indicator}
					{classification}
					{granularity}
					{pernocta}
					onselect={navTo}
				/>
			</div>
			<p class="home-map__more"><a href={localizeHref('/mapa')}>{m.home_map_more()} →</a></p>
		</section>

		<!-- BEESWARM · el gap padró↔presència de tota Catalunya, d'un cop d'ull (§4 viz) -->
		{#if pernocta}
			<section class="ds-sec">
				<div class="ds-sec__hd"><span class="ref">∿</span><h2>{m.beeswarm_title()}</h2></div>
				<p class="lead">{m.beeswarm_lead()}</p>
				<Beeswarm munis={pernocta} />
			</section>
		{/if}

		<!-- PORTES DE COMARCA · /resum és ara la subhome del Berguedà -->
		<section class="ds-sec">
			<div class="ds-sec__hd"><span class="ref">▦</span><h2>{m.home_portes_title()}</h2></div>
			<div class="home-portes">
				<a class="porta porta--on" href={localizeHref('/resum')}>
					<span class="porta__nom">Berguedà</span>
					<span class="porta__sub">{m.home_porta_bergueda_sub()}</span>
					<span class="porta__cta">{m.home_porta_bergueda_cta()} →</span>
				</a>
				<div class="porta porta--soon" aria-disabled="true">
					<span class="porta__nom">{m.home_porta_proxim()}</span>
					<span class="porta__sub">{m.home_porta_proxim_sub()}</span>
				</div>
			</div>
		</section>
	</div>
</section>

<style>
	/* Línia d'abast honest sota el mapa de la home: què cobrim a tota Catalunya i per què. */
	.home-map__scope {
		margin: -2px 0 14px;
		max-width: 64ch;
		font-size: 0.86rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
	}

	/* Commutador de granularitat del mapa de la home (comarca/vegueria/municipi). */
	.home-gran {
		display: inline-flex;
		margin: 0 0 12px;
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-full);
		overflow: hidden;
	}
	.home-gran__btn {
		font-family: var(--dp-font-mono);
		font-size: 0.72rem;
		letter-spacing: 0.02em;
		padding: 6px 14px;
		border: none;
		background: var(--dp-surface);
		color: var(--dp-text-muted);
		cursor: pointer;
	}
	.home-gran__btn + .home-gran__btn {
		border-left: 1px solid var(--dp-border);
	}
	.home-gran__btn[aria-pressed='true'] {
		background: var(--dp-text);
		color: var(--dp-bg);
	}
</style>
