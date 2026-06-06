<script lang="ts">
	/**
	 * Pantalla «Mapa coroplètic» a ALTA FIDELITAT (DA final · captures 03/04/06).
	 *
	 * Estructura del target (handoff `reference/da-final` + paquet de revisió):
	 *  · Hero amb corbes de nivell etiquetades amb VALORS DE GAP reals, eyebrow mono
	 *    («Cartografia / 31 municipis · geometria INE/IGN») i H1 Archivo «Mapa coroplètic».
	 *  · Barra d'eines amb el selector d'indicador.
	 *  · .map-grid: a l'esquerra el .map-stage amb el MAPA COROPLÈTIC REAL (MapLibre, els 31
	 *    municipis); a la dreta .map-side amb el panell «com es llegeix el color» (.map-read,
	 *    canvia segons indicador) i la .map-legend que COMMUTA divergent↔seqüencial amb els
	 *    talls REALS de la classificació.
	 *  · .pal-spec: «Paletes per visualització» (§B.3, el lliurable clau) — 3 targetes + taula
	 *    indicador→paleta; la targeta de la paleta de l'indicador actiu queda destacada (.on).
	 *  · Caveats + línia de font.
	 *
	 * Color (palette.md, DA final ronda 2): el GAP usa la rampa divergent teal↔porpra
	 * `--dp-div2-*` (porpra = població que el padró no veu); la resta, la seqüencial «terra»
	 * `--dp-exposure-*`. Tractament honest: confiança baixa velada/tramada, «sense dada» amb
	 * tramat (mai farciment pla). CAP xifra inventada: tot ve del dataset real i la classificació.
	 *
	 * CSS: design-system/aplicacio.css (.ap-hero, .map-toolbar, .map-grid, .map-stage,
	 * .map-read, .map-legend, .map-cls, .pal-spec…). Aquí només estructura + dades + wiring.
	 */
	import { browser } from '$app/environment';
	import ContourField from '$lib/components/ContourField.svelte';
	import ChoroplethMap from '$lib/components/ChoroplethMap.svelte';
	import MapTooltip from '$lib/components/MapTooltip.svelte';
	import { MAP_INDICATORS, DEFAULT_INDICATOR } from '$lib/map/indicators';
	import { classify, methodFor, classRangeLabels, makeMetricFormatter } from '$lib/map/classify';
	import { divergingColors, rampColors } from '$lib/map/palette';
	import { currentLocale } from '$lib/i18n';
	import type { MetricKey } from '$lib/contract/types';
	import { m } from '$lib/paraglide/messages';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const geojson = $derived(data.geojson);
	const locale = $derived(currentLocale());

	let indicator = $state<MetricKey>(DEFAULT_INDICATOR);

	// Etiqueta editorial de cada indicador del mapa (clau del contracte → text localitzat).
	// Només per a les claus de MAP_INDICATORS; `labelFor` cau a l'etiqueta del contracte si cal.
	const INDICATOR_LABEL: Partial<Record<MetricKey, () => string>> = {
		gap_pct: () => m.map_ind_gap(),
		poblacio_real_est: () => m.map_ind_real(),
		IETR: () => m.map_ind_ietr(),
		pct_noprincipal: () => m.map_ind_nop(),
		rtc_per_1000hab: () => m.map_ind_ratio(),
		kg_hab_any: () => m.map_ind_res()
	};
	const labelFor = (key: MetricKey): string => INDICATOR_LABEL[key]?.() ?? key;

	// Sèrie de valors de l'indicador actiu sobre TOTS els municipis de la geometria
	// (no només els del mock amb dada): la classificació és sobre el conjunt real.
	const series = $derived(
		geojson.features.map((f: import('geojson').Feature) => {
			const ine5 = (f.properties?.ine5 as string) ?? '';
			return dataset.municipis[ine5]?.values?.[indicator] ?? null;
		})
	);

	const method = $derived(methodFor(indicator));
	const classification = $derived(classify(series, method));
	const def = $derived(dataset.metrics[indicator]);
	// «divMode» = l'indicador és una desviació amb signe (el gap) → rampa divergent.
	const divMode = $derived(method === 'diverging');

	// Colors per classe de la rampa activa (els mateixos que pinta el canvas), per a la llegenda.
	const legendColors = $derived(
		divMode && classification.center !== undefined
			? divergingColors(classification.domain, classification.center)
			: rampColors(classification.classes)
	);
	// Etiquetes de rang de cada classe (formatades al locale i a la clau de mètrica).
	const rangeLabels = $derived(
		classRangeLabels(classification, def.format, locale, indicator)
	);

	// Mètode llegible per al subtítol de la llegenda seqüencial (Jenks / cuantils).
	const methodCaption = $derived(
		method === 'quantiles' ? m.map_method_quantiles() : m.map_method_jenks()
	);

	// Corbes del hero amb VALORS DE GAP reals (talls de la classificació del gap, no inventats):
	// el «full topogràfic» mostra les cotes del propi indicador estrella. Formatats amb signe.
	const gapClass = $derived(classify(
		geojson.features.map((f: import('geojson').Feature) => {
			const ine5 = (f.properties?.ine5 as string) ?? '';
			return dataset.municipis[ine5]?.values?.gap_pct ?? null;
		}),
		'diverging'
	));
	const heroLabels = $derived.by(() => {
		const fmt = makeMetricFormatter('gap_pct', dataset.metrics.gap_pct.format, locale);
		// extrems + talls reals del gap, com a cotes; l'última és la paraula «gap» (rètol del full).
		const vals = [gapClass.max, ...gapClass.breaks, gapClass.min]
			.filter((v, i, a) => a.indexOf(v) === i)
			.slice(0, 6)
			.map((v) => fmt(v));
		return [...vals, m.map_h1_b()].slice(0, 7);
	});
	const heroSummits = [
		{ cx: 900, cy: 140, r0: 15, step: 22, rings: 11, sq: 0.96, seed: 1.1, lt: 0.03 },
		{ cx: 1075, cy: 305, r0: 14, step: 20, rings: 9, sq: 1.06, seed: 3.1, lt: 0.1 }
	];
	const heroDivis = { cx: 775, cy: 225, r: 150, sq: 1.2, seed: 0.7 };

	// Tooltip (posició + contingut), emès pel mapa.
	interface Hover {
		ine5: string;
		nom: string;
		value: number | string | null;
		conf: string | null;
		x: number;
		y: number;
	}
	let hover = $state<Hover | null>(null);

	// Paletes de l'especificació: quina queda destacada (.on) segons l'indicador actiu.
	const activePal = $derived(divMode ? 'div' : 'seq');
</script>

<svelte:head>
	<title>{m.map_title()} · {m.app_name()}</title>
</svelte:head>

<section data-view="mapa" class="on">
	<div class="ap-hero">
		<ContourField
			class="ap-hero__field"
			viewBox="0 0 1200 380"
			summits={heroSummits}
			divis={heroDivis}
			labels={heroLabels}
		/>
		<div class="ap-hero__in">
			<p class="ap-eyebrow">
				<span>{m.map_eyebrow_a()}</span><span class="sep">/</span><span>{m.map_eyebrow_b()}</span>
			</p>
			<h1>{m.map_h1_a()} <span class="q">{m.map_h1_b()}</span>.</h1>
			<p class="lede">
				{m.map_lede_a()} <b class="warm">{m.map_lede_gap()}</b> {m.map_lede_mid()}
				<b class="warm">{m.map_lede_warm()}</b> {m.map_lede_warm_tail()}
				<b class="cool">{m.map_lede_cool()}</b> {m.map_lede_cool_tail()}
			</p>
		</div>
	</div>

	<div class="ds-main">
		<section class="ds-sec" style="border-top:none">
			<!-- Barra d'eines: selector d'indicador -->
			<div class="map-toolbar">
				<div class="field">
					<label for="indicator">{m.map_indicator_label()}</label>
					<select id="indicator" class="select" bind:value={indicator}>
						{#each MAP_INDICATORS as key (key)}
							<option value={key}>{labelFor(key)}</option>
						{/each}
					</select>
				</div>
			</div>

			<!-- Graella: mapa real (esquerra) + lectura del color i llegenda (dreta) -->
			<div class="map-grid">
				<div class="map-stage">
					<ContourField
						class="map-stage__contours"
						viewBox="0 0 760 600"
						summits={[
							{ cx: 230, cy: 190, r0: 18, step: 26, rings: 9, sq: 0.95, seed: 0.6, lt: 0 },
							{ cx: 560, cy: 420, r0: 16, step: 24, rings: 8, sq: 1.04, seed: 2.3, lt: 0 }
						]}
						divis={{ cx: 400, cy: 300, r: 170, sq: 1.15, seed: 1.4 }}
						labels={[]}
					/>
					<div class="map-stage__live">
						{#if browser}
							<ChoroplethMap
								{dataset}
								{geojson}
								{indicator}
								{classification}
								onhover={(p) => (hover = p)}
							/>
							{#if hover}
								<MapTooltip
									nom={hover.nom}
									metricKey={indicator}
									{def}
									value={hover.value}
									conf={hover.conf}
									x={hover.x}
									y={hover.y}
								/>
							{/if}
						{:else}
							<div class="map-stage__ssr" aria-hidden="true">{m.map_loading()}</div>
						{/if}
					</div>
				</div>

				<aside class="map-side">
					<div class="map-read">
						<p class="map-read__h">{m.map_read_h()}</p>
						<p class="read">
							{#if divMode}{m.map_read_gap()}{:else}{m.map_read_seq()}{/if}
						</p>
					</div>
					<div class="map-legend">
						{#if divMode}
							<!-- llegenda DIVERGENT (gap) amb talls reals -->
							<div>
								<p class="legend__hd"><span>{labelFor(indicator)}</span></p>
								<p
									class="ds-block__lab"
									style="border:none;margin:0 0 10px;padding:0"
								>
									{m.map_leg_div_sub({ n: String(classification.classes) })}
								</p>
								<div class="legend__bar" style="border-radius:2px;overflow:hidden">
									{#each legendColors as c, ci (ci)}
										<i style="background:{c}"></i>
									{/each}
								</div>
								<div class="map-cls">
									{#each rangeLabels as label, i (i)}
										<div class="r">
											<i style="background:{legendColors[i]}"></i><span>{i + 1} · {label}</span>
										</div>
									{/each}
								</div>
								<div class="legend__nodata" style="margin-top:13px">
									<span
										style="width:26px;height:14px;border-radius:2px;display:inline-block;background:var(--dp-div2-3);border:1px solid var(--dp-border-strong)"
									></span><span>{m.map_leg_neutral()}</span>
								</div>
							</div>
						{:else}
							<!-- llegenda SEQÜENCIAL (resta d'indicadors) amb talls reals -->
							<div>
								<p class="legend__hd"><span>{labelFor(indicator)}</span></p>
								<p
									class="ds-block__lab"
									style="border:none;margin:0 0 10px;padding:0"
								>
									{m.map_leg_seq_sub({ n: String(classification.classes), method: methodCaption })}
								</p>
								<div class="legend__bar" style="border-radius:2px;overflow:hidden">
									{#each legendColors as c, ci (ci)}
										<i style="background:{c}"></i>
									{/each}
								</div>
								<div class="map-cls">
									{#each rangeLabels as label, i (i)}
										<div class="r">
											<i style="background:{legendColors[i]}"></i><span>{i + 1} · {label}</span>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<div class="legend__nodata" style="margin-top:13px">
							<span class="hatch-cell" style="width:26px;height:14px"></span><span
								>{m.map_legend_lowconf()}</span
							>
						</div>
						<div class="legend__nodata" style="margin-top:8px">
							<span
								style="width:26px;height:14px;border-radius:2px;display:inline-block;background:#E3E3DE;background-image:repeating-linear-gradient(45deg,#94A0AF 0 1.5px,transparent 1.5px 5px);border:1px solid var(--dp-border-strong)"
							></span><span>{m.map_legend_nodata()}</span>
						</div>
					</div>
				</aside>
			</div>

			<!-- ============ PALETES PER VISUALITZACIÓ (especificació · §B.3) ============ -->
			<section class="pal-spec">
				<div class="ds-sec__hd" style="margin-top:8px">
					<span class="ref">C</span><h2>{m.map_pal_title()}</h2>
				</div>
				<p class="lead">{m.map_pal_lede()}</p>

				<div class="pal-grid">
					<!-- DIVERGENT -->
					<article class="pal" class:on={activePal === 'div'} data-pal="div">
						<div class="pal__hd">
							<p class="pal__t">{m.map_pal_div_t()}</p>
							<span class="pal__active">{m.map_pal_active()}</span>
						</div>
						<div class="pal-ramp">
							<span style="background:var(--dp-div2-0)"></span><span
								style="background:var(--dp-div2-1)"
							></span><span style="background:var(--dp-div2-2)"></span><span
								style="background:var(--dp-div2-3)"
							></span><span style="background:var(--dp-div2-4)"></span><span
								style="background:var(--dp-div2-5)"
							></span><span style="background:var(--dp-div2-6)"></span>
						</div>
						<p class="pal-tok mono">{m.map_pal_div_tok()}</p>
						<p class="pal__use">{m.map_pal_div_use()}</p>
						<p class="pal__cvd mono"><span class="okdot"></span><span>{m.map_pal_div_cvd()}</span></p>
					</article>

					<!-- SEQÜENCIAL -->
					<article class="pal" class:on={activePal === 'seq'} data-pal="seq">
						<div class="pal__hd">
							<p class="pal__t">{m.map_pal_seq_t()}</p>
							<span class="pal__active">{m.map_pal_active()}</span>
						</div>
						<div class="pal-ramp">
							<span style="background:var(--dp-exposure-0)"></span><span
								style="background:var(--dp-exposure-1)"
							></span><span style="background:var(--dp-exposure-2)"></span><span
								style="background:var(--dp-exposure-3)"
							></span><span style="background:var(--dp-exposure-4)"></span><span
								style="background:var(--dp-exposure-5)"
							></span>
						</div>
						<p class="pal-tok mono">{m.map_pal_seq_tok()}</p>
						<p class="pal__use">{m.map_pal_seq_use()}</p>
						<p class="pal__cvd mono"><span class="okdot"></span><span>{m.map_pal_seq_cvd()}</span></p>
					</article>

					<!-- QUALITATIVA (mai activa per als indicadors actuals; documenta el contracte) -->
					<article class="pal" data-pal="cat">
						<div class="pal__hd">
							<p class="pal__t">{m.map_pal_cat_t()}</p>
						</div>
						<div class="pal-ramp">
							<span style="background:var(--dp-cat-1)"></span><span
								style="background:var(--dp-cat-2)"
							></span><span style="background:var(--dp-cat-3)"></span><span
								style="background:var(--dp-cat-4)"
							></span><span style="background:var(--dp-cat-5)"></span><span
								style="background:var(--dp-cat-6)"
							></span><span style="background:var(--dp-cat-7)"></span><span
								style="background:var(--dp-cat-8)"
							></span>
						</div>
						<p class="pal-tok mono">{m.map_pal_cat_tok()}</p>
						<p class="pal__use">{m.map_pal_cat_use()}</p>
						<p class="pal__cvd mono"><span class="okdot"></span><span>{m.map_pal_cat_cvd()}</span></p>
					</article>
				</div>

				<div class="pal-map">
					<p class="ds-block__lab">{m.map_pal_map_t()}</p>
					<div class="pal-map__rows">
						<div class="pmr">
							<span class="nm">{m.map_ind_gap()}</span><span class="tag div"
								><span>{m.map_pal_tag_div()}</span></span
							>
						</div>
						<div class="pmr">
							<span class="nm">{m.map_ind_real()}</span><span class="tag seq"
								><span>{m.map_pal_tag_seq()}</span></span
							>
						</div>
						<div class="pmr">
							<span class="nm">{m.map_ind_ietr()}</span><span class="tag seq"
								><span>{m.map_pal_tag_seq()}</span></span
							>
						</div>
						<div class="pmr">
							<span class="nm">{m.map_ind_nop()}</span><span class="tag seq"
								><span>{m.map_pal_tag_seq()}</span></span
							>
						</div>
						<div class="pmr">
							<span class="nm">{m.map_ind_ratio()}</span><span class="tag seq"
								><span>{m.map_pal_tag_seq()}</span></span
							>
						</div>
						<div class="pmr">
							<span class="nm">{m.map_ind_res()}</span><span class="tag seq"
								><span>{m.map_pal_tag_seq()}</span></span
							>
						</div>
					</div>
				</div>

				<p class="srcline">{m.map_pal_note()}</p>
			</section>

			<div class="caveats" style="margin-top:20px">
				<div class="alert"><span class="bar"></span><div>{m.map_caveat_1()}</div></div>
				<div class="alert warn"><span class="bar"></span><div>{m.map_caveat_2()}</div></div>
			</div>

			<p class="srcline">{m.map_srcline()}</p>
		</section>
	</div>
</section>

<style>
	/* El gros del CSS ve del design-system (.ap-hero, .map-grid, .map-stage, .pal-spec…).
	   Aquí només encaixem el component de mapa REAL dins del .map-stage: que ompli el marc
	   (el .map-stage ja porta min-height i el padding del target). */
	.map-stage__live {
		position: relative;
		z-index: 1;
		width: 100%;
		max-width: 620px;
		align-self: stretch;
		display: flex;
	}
	/* El ChoroplethMap arrela el seu propi .map (alçada pròpia); aquí l'estirem perquè
	   ompli l'amplada del marc i tingui una alçada de lectura mínima generosa. */
	.map-stage__live :global(.map) {
		width: 100%;
		min-height: 380px;
	}
	.map-stage__ssr {
		width: 100%;
		min-height: 380px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--dp-text-subtle);
		font-family: var(--dp-font-mono);
		font-size: 0.8rem;
	}
</style>
