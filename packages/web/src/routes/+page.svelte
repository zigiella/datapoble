<script lang="ts">
	/**
	 * HOME «La Llera» (cercador primer) — la portada de riusdegent.
	 *
	 * S'articula sobre BUSCADOR + MAPA + PORTES. Aquí: hero amb el cercador com a heroi
	 * (MuniSearch, tota Catalunya), MAPA coroplètic de TOT CATALUNYA per % habitatge no principal
	 * (oficial; clic → fitxa) i PORTES DE COMARCA (Berguedà → /comarca/bergueda, el nucli que
	 * treballem a fons). Cap xifra sense procedència.
	 *
	 * El WAVEFORM del gap (Beeswarm) està APARCAT amb el model d'estimació de pernocta (vot de
	 * Bea 2026-07-16 · `docs/ajuntaments/gorra-alcalde-pobla.md` §1): la home va només amb oficials.
	 */
	import { goto } from '$app/navigation';
	import ContourField from '$lib/components/ContourField.svelte';
	import ChoroplethMap from '$lib/components/ChoroplethMap.svelte';
	import MuniSearch from '$lib/components/MuniSearch.svelte';
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
	// Catàleg de tots els munis de Catalunya (cerca a tot el país + navegació del mapa).
	const cataleg = $derived(data.cataleg);
	// Xifres de les PORTES (W5): COMPTADES de l'agrupació territorial, mai escrites al copy — una
	// xifra escrita al text es queda estale EN SILENCI, que és exactament el que li va passar al
	// «947 municipis» de la porta morta. Si l'artefacte no arriba, el loader retorna 0 i la porta
	// s'ensenya SENSE subtítol: preferim quedar-nos curts a pintar un número que no hem comptat.
	const totalComarques = $derived(data.totalComarques);
	const totalMunis = $derived(data.totalMunis);
	const berguedaMunis = $derived(data.berguedaMunis);
	// Indicadors OFICIALS a escala Catalunya (pinten TOTS els municipis).
	const catValues = $derived(data.catValues);

	// Mapa de la home: TOTA CATALUNYA per % habitatge no principal (oficial, llegible a escala CAT i
	// amb dada per a tots els munis). NO tipologia —els llindars no generalitzen («Barcelona =
	// excursió» trencava la credibilitat (reconducció))—. Sense commutador de granularitat (decisió
	// Bea): un sol mapa de país; el detall per comarca viu a /comarca i el mapa complet a /mapa.
	const indicator = 'pct_noprincipal' as MetricKey;
	// Sèrie sobre TOT Catalunya: valor del Berguedà (dataset) o, si no, el de catValues (escala CAT),
	// perquè els talls/colors abastin tots els municipis (mirall de /mapa).
	const series = $derived(
		geojson.features.map((f: import('geojson').Feature) => {
			const ine5 = (f.properties?.ine5 as string) ?? '';
			const dv = mapValue(indicator, dataset.municipis[ine5]?.values?.[indicator]);
			if (dv !== null && dv !== undefined) return dv;
			return catValues?.[ine5]?.[indicator] ?? null;
		})
	);
	const method = $derived(methodFor(indicator));
	const classification = $derived(classify(series, method));

	function navTo(ine5: string | null) {
		if (!ine5) return;
		if (dataset.municipis[ine5]) {
			goto(localizeHref(`/municipi/${slugForIne5(ine5, dataset)}`));
			return;
		}
		// Qualsevol altre municipi de Catalunya: la fitxa existeix (947 prerenderitzades, dades
		// oficials per muni) → hi naveguem via el catàleg de noms.
		const hit = cataleg.find((c) => c.ine5 === ine5);
		if (hit) goto(localizeHref(`/municipi/${toSlug(hit.nom)}`));
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
			<div class="home-map">
				<ChoroplethMap
					{dataset}
					{geojson}
					{comarques}
					{indicator}
					{classification}
					{catValues}
					fitTo="catalunya"
					onselect={navTo}
				/>
			</div>
			<p class="home-map__more"><a href={localizeHref('/mapa')}>{m.home_map_more()} →</a></p>
		</section>

		<!-- PORTES DE COMARCA · el Berguedà aterra a /comarca/bergueda (la vitrina passa a les fitxes)
		     i la segona porta, a l'índex de TOTES les comarques.

		     W5 (esmena de Bea, 2026-07-31): la segona porta era un `porta--soon` amb
		     `aria-disabled="true"` («Resta de Catalunya · 947 municipis»). Deia dues coses falses:
		     que allò era «properament», quan des de P-947 les 43 comarques tenen pàgina i els 947
		     municipis tenen fitxa; i que 947 era la «resta», quan 947 és el TOTAL de Catalunya (la
		     resta serien 916). Ara la porta és clicable i porta a /comarca, i les xifres es COMPTEN
		     de `comarques.json` en comptes d'anar escrites al copy. -->
		<section class="ds-sec">
			<div class="ds-sec__hd"><span class="ref">▦</span><h2>{m.home_portes_title()}</h2></div>
			<div class="home-portes">
				<a class="porta porta--on" href={localizeHref('/comarca/bergueda')}>
					<span class="porta__nom">Berguedà</span>
					{#if berguedaMunis}
						<span class="porta__sub">{m.home_porta_bergueda_sub({ munis: String(berguedaMunis) })}</span>
					{/if}
					<span class="porta__cta">{m.home_porta_bergueda_cta()} →</span>
				</a>
				<a class="porta porta--on" href={localizeHref('/comarca')}>
					<span class="porta__nom">{m.home_porta_cat()}</span>
					{#if totalComarques && totalMunis}
						<span class="porta__sub"
							>{m.home_porta_cat_sub({
								comarques: String(totalComarques),
								munis: String(totalMunis)
							})}</span
						>
					{/if}
					<span class="porta__cta">{m.home_porta_cat_cta()} →</span>
				</a>
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
</style>
