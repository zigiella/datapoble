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
	import { goto } from '$app/navigation';
	import ContourField from '$lib/components/ContourField.svelte';
	import ChoroplethMap from '$lib/components/ChoroplethMap.svelte';
	import MapTooltip from '$lib/components/MapTooltip.svelte';
	import { MAP_INDICATORS, DEFAULT_INDICATOR, mapValue } from '$lib/map/indicators';
	import { classify, methodFor, classRangeLabels, makeMetricFormatter } from '$lib/map/classify';
	import { divergingColors, rampColors } from '$lib/map/palette';
	import { TIPOLOGIA_ORDER, isCategorical, tipologiaLabel } from '$lib/map/tipologia';
	import { slugForIne5, toSlug } from '$lib/contract/slug';
	import { currentLocale, localizeHref } from '$lib/i18n';
	import { formatInteger } from '$lib/format';
	import type { MetricKey } from '$lib/contract/types';
	import type { PernoctaMuni } from '$lib/contract/pernocta';
	import { m } from '$lib/paraglide/messages';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const geojson = $derived(data.geojson);
	const comarques = $derived(data.comarques);
	const vegueries = $derived(data.vegueries);
	// Presència estimada EN RANG (Nivell C): munis coberts de fora del Berguedà, keyed per ine5.
	const pernocta = $derived(data.pernocta?.munis);
	const locale = $derived(currentLocale());

	// Granularitat del mapa (municipi = coroplètic per indicador; comarca/vegueria = cobertura).
	type Granularity = 'municipi' | 'comarca' | 'vegueria';
	let granularity = $state<Granularity>('municipi');
	const coverageMode = $derived(granularity !== 'municipi');
	const GRAN_OPTS: { key: Granularity; label: () => string }[] = [
		{ key: 'municipi', label: () => m.map_granularity_municipi() },
		{ key: 'comarca', label: () => m.map_granularity_comarca() },
		{ key: 'vegueria', label: () => m.map_granularity_vegueria() }
	];
	// Tàctil (pointer coarse): a mòbil el hover no existeix → el tap mostra la targeta i NO navega;
	// la targeta es fa tocable i el seu CTA «obrir fitxa» és qui obre la fitxa del municipi.
	const coarse = browser && typeof matchMedia !== 'undefined' && matchMedia('(pointer: coarse)').matches;

	let indicator = $state<MetricKey>(DEFAULT_INDICATOR);
	// Color «amb dades» de la llegenda de cobertura (mirall de COVERAGE_FILL del ChoroplethMap).
	const COVERAGE_FILL = '#4FA8A0';

	// Etiqueta editorial de cada indicador del mapa (clau del contracte → text localitzat).
	// Només per a les claus de MAP_INDICATORS; `labelFor` cau a l'etiqueta del contracte si cal.
	// El model de 3 capes: L1 població invisible (pernocta), L2 càrrega total, L3 pressió turística.
	const INDICATOR_LABEL: Partial<Record<MetricKey, () => string>> = {
		tipologia: () => m.map_ind_tipologia(),
		gap_pernocta_pct: () => m.map_ind_pernocta(),
		carrega_total_est: () => m.map_ind_carrega(),
		index_turisme: () => m.map_ind_turisme(),
		restauracio_per_1000hab: () => m.map_ind_restauracio(),
		IETR: () => m.map_ind_ietr(),
		pct_noprincipal: () => m.map_ind_nop(),
		kg_hab_any: () => m.map_ind_res(),
		divergencia_senyals: () => m.map_ind_divergencia()
	};
	const labelFor = (key: MetricKey): string => INDICATOR_LABEL[key]?.() ?? key;

	// Sèrie de valors de l'indicador actiu. La geometria ara és tot Catalunya (947 munis), però
	// només els 31 del Berguedà tenen dada: la resta retornen null i `classify` els ignora, així
	// que els talls són EXACTAMENT els del Berguedà (la classificació és sobre el conjunt amb dada).
	// Passem pel `mapValue` perquè el 0 d'OSM de la restauració (buit de mapejat, no «sense
	// hostaleria») es degradi a null i NO ancori el mínim de Jenks ni entri a cap classe.
	const series = $derived(
		geojson.features.map((f: import('geojson').Feature) => {
			const ine5 = (f.properties?.ine5 as string) ?? '';
			return mapValue(indicator, dataset.municipis[ine5]?.values?.[indicator]);
		})
	);

	const method = $derived(methodFor(indicator));
	const classification = $derived(classify(series, method));
	const def = $derived(dataset.metrics[indicator]);
	// «divMode» = l'indicador és una desviació amb signe (el gap de pernocta) → rampa divergent.
	const divMode = $derived(method === 'diverging');
	// «catMode» = l'indicador és categòric (la tipologia) → coloració per tipus + llegenda categòrica
	// (un color per arquetip, NO rampa). El color comunica QUIN TIPUS de pressió, no «més/menys».
	const catMode = $derived(method === 'categorical');

	// Les tres capes del model v2 són INFERÈNCIA (derived) → caveat d'honestedat propi.
	// L1 (pernocta) ve de l'elèctric; L2 (càrrega) i L3 (pressió turística) tenen el seu matís.
	// La restauració (2n proxy de L3) també porta caveat propi: és recompte d'OSM (mínim, no cens)
	// i VALIDA la pressió del vidre. Per als indicadors oficials directes (% no principal, residus)
	// o l'índex IETR no s'hi aplica.
	const LAYER_KEYS = new Set<MetricKey>([
		'tipologia',
		'gap_pernocta_pct',
		'carrega_total_est',
		'index_turisme',
		'restauracio_per_1000hab'
	]);
	const isLayer = $derived(LAYER_KEYS.has(indicator));
	// Text del caveat principal segons la capa activa (honestedat per indicador).
	const layerCaveat = $derived.by(() => {
		if (indicator === 'tipologia') return m.map_caveat_tipologia();
		if (indicator === 'gap_pernocta_pct') return m.map_caveat_pernocta();
		if (indicator === 'carrega_total_est') return m.map_caveat_carrega();
		if (indicator === 'index_turisme') return m.map_caveat_turisme();
		if (indicator === 'restauracio_per_1000hab') return m.map_caveat_restauracio();
		return '';
	});

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

	// Accessibilitat (spec §1.5): alternativa en TAULA del mapa per a l'indicador actiu.
	// Dades ja al client (els 31 del Berguedà); ordre per valor (numèric, desc) o per nom (categòric).
	let showTable = $state(false);
	const valueFmt = $derived(makeMetricFormatter(indicator, def.format, locale));
	const mapTableRows = $derived.by(() => {
		const rows = Object.values(dataset.municipis).map((muni) => {
			const raw = muni.values[indicator];
			const display =
				raw === null || raw === undefined
					? m.value_not_available()
					: catMode
						? tipologiaLabel(raw)
						: valueFmt(raw as number);
			const confRaw = muni.values.confianca;
			return {
				ine5: muni.ine5,
				nom: muni.nom,
				raw,
				display,
				conf: typeof confRaw === 'string' ? confRaw : m.value_not_available()
			};
		});
		if (catMode) return rows.sort((a, b) => a.nom.localeCompare(b.nom, 'ca'));
		return rows.sort((a, b) => {
			const av = typeof a.raw === 'number' ? a.raw : -Infinity;
			const bv = typeof b.raw === 'number' ? b.raw : -Infinity;
			return bv - av;
		});
	});

	// Corbes del hero amb VALORS reals del gap de PERNOCTA (talls de la classificació, no inventats):
	// el «full topogràfic» mostra les cotes del propi indicador estrella (la població invisible).
	// Formatats com a percentatge amb signe.
	const gapClass = $derived(classify(
		geojson.features.map((f: import('geojson').Feature) => {
			const ine5 = (f.properties?.ine5 as string) ?? '';
			return dataset.municipis[ine5]?.values?.gap_pernocta_pct ?? null;
		}),
		'diverging'
	));
	const heroLabels = $derived.by(() => {
		const fmt = makeMetricFormatter(
			'gap_pernocta_pct',
			dataset.metrics.gap_pernocta_pct.format,
			locale
		);
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
		/** Confiança auditable 0-100 (`confianca_score`); complementa la bandera. */
		confScore: number | null;
		/** True si el municipi és del Berguedà (té dades); fals → «sense dades encara». */
		inBergueda: boolean;
		/** Presència estimada EN RANG (Nivell C) si és un muni cobert de fora del Berguedà; si no, null. */
		pernocta?: PernoctaMuni | null;
		x: number;
		y: number;
	}
	let hover = $state<Hover | null>(null);

	// Clic a un municipi → navega a la seva FITXA completa (`/municipi/[slug]`). Navega per als del
	// Berguedà (dades completes) I per als coberts en rang (Nivell C, la fitxa mostra el rang). Per a
	// la resta de fora, el clic no navega (la fitxa diria «sense dades» i el hover ja ho comunica).
	function onMuniSelect(ine5: string | null) {
		if (!ine5) return;
		if (dataset.municipis[ine5]) {
			goto(localizeHref(`/municipi/${slugForIne5(ine5, dataset)}`));
			return;
		}
		const cov = pernocta?.[ine5];
		if (cov) goto(localizeHref(`/municipi/${toSlug(cov.nom)}`));
	}

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
				{m.map_lede_a()} <b class="warm">{m.map_lede_gap()}</b>{m.map_lede_mid()}
				<b class="warm">{m.map_lede_warm()}</b> {m.map_lede_warm_tail()}
				<b class="cool">{m.map_lede_cool()}</b> {m.map_lede_cool_tail()}
			</p>
		</div>
	</div>

	<div class="ds-main">
		<section class="ds-sec" style="border-top:none">
			<!-- Barra d'eines: commutador de granularitat + selector d'indicador (només a municipi) -->
			<div class="map-toolbar">
				<div class="field">
					<span class="gran-label" id="gran-label">{m.map_granularity_label()}</span>
					<div class="gran-seg" role="group" aria-labelledby="gran-label">
						{#each GRAN_OPTS as o (o.key)}
							<button
								type="button"
								class="gran-seg__btn"
								aria-pressed={granularity === o.key}
								onclick={() => (granularity = o.key)}>{o.label()}</button
							>
						{/each}
					</div>
				</div>
				{#if !coverageMode}
					<div class="field">
						<label for="indicator">{m.map_indicator_label()}</label>
						<select id="indicator" class="select" bind:value={indicator}>
							{#each MAP_INDICATORS as key (key)}
								<option value={key}>{labelFor(key)}</option>
							{/each}
						</select>
					</div>
				{/if}
			</div>

			<!-- Graella: mapa real (esquerra) + lectura del color i llegenda (dreta).
			     Presentacio simple (pre-Fase 2): SENSE marc de paper ni corbes; el MapLibre
			     omple net el seu contenidor i .map-canvaswrap deixa overflow visible perque
			     les targetes/tooltips de municipi no es retallin (decisio Bea). -->
			{#if !coverageMode}
				<div class="map-tablebar">
					<button
						type="button"
						class="map-table-toggle"
						aria-pressed={showTable}
						onclick={() => (showTable = !showTable)}
					>
						{showTable ? m.viz_as_map() : m.viz_as_table()}
					</button>
				</div>
				{/if}
				{#if !showTable || coverageMode}
				<div class="map-wrap">
				<div class="map-canvaswrap">
					{#if browser}
						<ChoroplethMap
							{dataset}
							{geojson}
							{comarques}
							{vegueries}
							{indicator}
							{classification}
							{granularity}
							{pernocta}
							onhover={(p) => (hover = p)}
							onselect={onMuniSelect}
						/>
						{#if hover}
							{#if hover.inBergueda}
								<MapTooltip
									nom={hover.nom}
									metricKey={indicator}
									{def}
									value={hover.value}
									conf={hover.conf}
									confScore={hover.confScore}
									x={hover.x}
									y={hover.y}
									hint={coarse ? m.map_open_fitxa_touch() : m.map_open_fitxa()}
									touchMode={coarse}
									href={localizeHref(`/municipi/${toSlug(hover.nom)}`)}
								/>
							{:else if hover.pernocta}
								<!-- Municipi COBERT EN RANG (Nivell C, fora del Berguedà): presència estimada
								     com a BANDA (rang_baix–rang_alt), ETCA oficial com a validació si n'hi ha, i
								     caveat d'inferència. Reusa l'embolcall `.tip--outside` (to amable, clar). -->
								<div
									class="tip card tip--outside tip--range"
									class:tip--touch={coarse}
									style="left:{hover.x}px; top:{hover.y}px"
									role="tooltip"
									aria-live="polite"
								>
									<div class="tip__place">{hover.nom}</div>
									<div class="tip__out">{m.map_range_eyebrow()}</div>
									<div class="tip__range tnum">
										{formatInteger(hover.pernocta.rang_baix, locale)}<span class="tip__range-dash"
											>–</span
										>{formatInteger(hover.pernocta.rang_alt, locale)}
										<span class="tip__range-unit">{m.map_range_unit()}</span>
									</div>
									{#if hover.pernocta.etca_oficial != null}
										<div class="tip__range-etca">
											{m.map_range_etca()}: <b class="tnum"
												>{formatInteger(hover.pernocta.etca_oficial, locale)}</b
											>
										</div>
									{/if}
									<p class="tip__out-scope">{m.map_range_caveat()}</p>
									{#if coarse}
										<a class="tip__hint tip__hint--link" href={localizeHref(`/municipi/${toSlug(hover.pernocta.nom)}`)}>{m.map_open_fitxa_touch()}</a>
									{:else}
										<p class="tip__hint">{m.map_open_fitxa()}</p>
									{/if}
								</div>
							{:else}
								<!-- Municipi de FORA del Berguedà SENSE cobertura: estat amable «sense dades encara»
								     (NO un tooltip de dada buida; honestedat: no fingim dada). -->
								<div
									class="tip card tip--outside"
									style="left:{hover.x}px; top:{hover.y}px"
									role="tooltip"
									aria-live="polite"
								>
									<div class="tip__place">{hover.nom}</div>
									<div class="tip__out">{m.map_outside_title()}</div>
									<p class="tip__out-sub">{m.map_outside_sub()}</p>
									<p class="tip__out-scope">{m.map_outside_scope()}</p>
								</div>
							{/if}
						{/if}
					{:else}
						<div class="map-ssr" aria-hidden="true">{m.map_loading()}</div>
					{/if}
				</div>

				<aside class="map-side">
					<div class="map-read">
						<p class="map-read__h">{m.map_read_h()}</p>
						<p class="read">
							{#if coverageMode}{m.map_legend_coverage_caveat()}{:else if catMode}{m.map_read_cat()}{:else if divMode}{m.map_read_gap()}{:else}{m.map_read_seq()}{/if}
						</p>
					</div>
					<div class="map-legend">
						{#if coverageMode}
							<!-- Llegenda de COBERTURA honesta (comarca/vegueria): no l'indicador, sinó on hi ha
							     dades. Comarca: Berguedà = completes. Vegueria: Comarques Centrals = parcials. -->
							<div>
								<p class="legend__hd"><span>{m.map_legend_coverage_title()}</span></p>
								<div class="map-cls">
									{#if granularity === 'comarca'}
										<div class="r">
											<i style="background:{COVERAGE_FILL}"></i><span>{m.map_legend_coverage_complete()}</span>
										</div>
									{:else}
										<div class="r">
											<span style="width:26px;height:14px;border-radius:2px;display:inline-block;background-color:{COVERAGE_FILL};background-image:repeating-linear-gradient(45deg,rgba(36,40,46,0.45) 0 1.5px,transparent 1.5px 5px);box-shadow:inset 0 0 0 1px var(--dp-border-strong)"></span><span>{m.map_legend_coverage_partial()}</span>
										</div>
									{/if}
									<div class="r">
										<i style="background:var(--dp-map-land,#F2F1EC);opacity:0.7;box-shadow:inset 0 0 0 1px var(--dp-border)"></i><span>{m.map_legend_coverage_none()}</span>
									</div>
								</div>
							</div>
						{:else if catMode}
							<!-- llegenda CATEGÒRICA (tipologia): un color per arquetip + etiqueta + frase curta.
							     NO és una rampa: el color comunica QUIN TIPUS de pressió, no «més/menys». -->
							<div>
								<p class="legend__hd"><span>{labelFor(indicator)}</span></p>
								<p class="ds-block__lab" style="border:none;margin:0 0 10px;padding:0">
									{m.map_leg_cat_sub({ n: String(TIPOLOGIA_ORDER.length) })}
								</p>
								<div class="map-cls map-cls--cat">
									{#each TIPOLOGIA_ORDER as t (t.value)}
										<div class="r r--cat" class:r--neutral={t.value === 'indeterminat'}>
											<i style="background:{t.color}"></i>
											<span class="cat-lab">{t.label()}</span>
											<span class="cat-blurb">{t.blurb()}</span>
										</div>
									{/each}
								</div>
							</div>
						{:else if divMode}
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

						{#if !coverageMode}
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
							<!-- Catalunya de context: municipis atenuats fora del Berguedà («sense dades encara»). -->
							<div class="legend__nodata" style="margin-top:8px">
								<span
									style="width:26px;height:14px;border-radius:2px;display:inline-block;background:var(--dp-map-land,#F2F1EC);opacity:0.7;border:1px solid var(--dp-border)"
								></span><span>{m.map_legend_dimmed()}</span>
							</div>
						{/if}
					</div>
				</aside>
			</div>

			{:else}
					<div class="viz-table-wrap">
						<table class="viz-table">
							<caption>{labelFor(indicator)}</caption>
							<thead>
								<tr>
									<th scope="col">{m.tbl_municipi()}</th>
									<th scope="col">{m.tbl_valor()}</th>
									<th scope="col">{m.tbl_confianca()}</th>
								</tr>
							</thead>
							<tbody>
								{#each mapTableRows as r (r.ine5)}
									<tr>
										<th scope="row">{r.nom}</th>
										<td>{r.display}</td>
										<td>{r.conf}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}

				<div class="caveats" style="margin-top:20px">
				{#if isLayer}
					<div class="alert"><span class="bar"></span><div>{layerCaveat}</div></div>
				{/if}
				<div class="alert warn"><span class="bar"></span><div>{m.map_caveat_2()}</div></div>
			</div>

			<p class="srcline">{def.source}{#if def.date} · {def.date}{/if} · {m.map_srcline_tail()}</p>
		</section>
	</div>
</section>

<style>
	/* Presentacio simple del mapa (sense marc de paper ni corbes). El gros del chrome ve
	   del design-system; aqui nomes el layout del bloc de mapa i que els tooltips de
	   municipi no es retallin (overflow visible a tota la cadena de contenidors). */
	.map-wrap {
		display: grid;
		grid-template-columns: 1fr 326px;
		gap: 0;
		align-items: stretch;
		/* overflow VISIBLE: a diferencia del .map-grid del design-system, aqui el tooltip
		   pot sobreeixir del marc sense quedar retallat. */
		overflow: visible;
	}
	@media (max-width: 880px) {
		.map-wrap { grid-template-columns: 1fr; }
	}

	/* Commutador de granularitat (municipi/comarca/vegueria): control segmentat. */
	.gran-label {
		display: block;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
		margin-bottom: 5px;
	}
	.gran-seg {
		display: inline-flex;
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-full);
		overflow: hidden;
	}
	.gran-seg__btn {
		font-family: var(--dp-font-mono);
		font-size: 0.72rem;
		letter-spacing: 0.02em;
		padding: 6px 14px;
		border: none;
		background: var(--dp-surface);
		color: var(--dp-text-muted);
		cursor: pointer;
	}
	.gran-seg__btn + .gran-seg__btn {
		border-left: 1px solid var(--dp-border);
	}
	.gran-seg__btn[aria-pressed='true'] {
		background: var(--dp-text);
		color: var(--dp-bg);
	}

	/* Llegenda CATEGÒRICA (tipologia): files amb swatch + etiqueta humana + frase curta.
	   Reutilitza .map-cls/.r del design-system (swatch quadrat 26×14) però apila etiqueta i
	   frase en una graella de dues files perquè la frase curta càpiga sense atapeir. */
	.map-cls--cat .r--cat {
		display: grid;
		grid-template-columns: 26px 1fr;
		grid-template-rows: auto auto;
		column-gap: 10px;
		row-gap: 1px;
		align-items: start;
		padding: 7px 0;
		border-bottom: 1px solid var(--dp-border);
	}
	.map-cls--cat .r--cat:last-child { border-bottom: none; }
	.map-cls--cat .r--cat > i {
		grid-row: 1 / span 2;
		width: 26px;
		height: 14px;
		border-radius: 2px;
		margin-top: 2px;
		/* contorn discret perquè el gris neutre de l'`indeterminat` no es perdi sobre el fons. */
		box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
	}
	.map-cls--cat .cat-lab {
		font-family: var(--dp-font-sans);
		font-weight: 600;
		font-size: 0.78rem;
		color: var(--dp-text);
		line-height: 1.2;
	}
	.map-cls--cat .cat-blurb {
		grid-column: 2;
		font-family: var(--dp-font-sans);
		font-size: 0.68rem;
		line-height: 1.32;
		color: var(--dp-text-subtle);
	}
	/* `indeterminat` és un estat HONEST (territori mixt), no un buit: l'etiqueta va en to apagat
	   perquè es llegeixi com a «el model no força una narració», no com a error. */
	.map-cls--cat .r--neutral .cat-lab { color: var(--dp-text-muted); font-style: italic; }

	/* Contenidor net del mapa en viu: SENSE fons de paper ni corbes. El ChoroplethMap
	   arrela el seu propi .map (amb la seva vora/radi i el canvas); aqui nomes el situem
	   i deixem overflow visible perque el tooltip (germa del mapa) pugui sortir per dalt. */
	.map-canvaswrap {
		position: relative;
		overflow: visible;
		/* block (no flex): el .map intern es block amb width:100% i ompli tot l'ample net del
		   contenidor. Amb flex, el .map quedava al seu ample de contingut (canvas estret). */
		display: block;
		min-width: 0;
	}
	.map-canvaswrap :global(.map) {
		display: block;
		width: 100%;
		min-height: 380px;
	}

	/* Separador discret amb el panell lateral (abans el donava la vora del .map-grid). */
	.map-wrap .map-side {
		border-left: 1px solid var(--dp-border);
	}
	@media (max-width: 880px) {
		.map-wrap .map-side { border-left: none; border-top: 1px solid var(--dp-border); }
	}

	.map-ssr {
		width: 100%;
		min-height: 380px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--dp-text-subtle);
		font-family: var(--dp-font-mono);
		font-size: 0.8rem;
	}

	/* Tooltip «sense dades encara» per als municipis de FORA del Berguedà (Catalunya de context).
	   Reusa l'embolcall `.tip` però en to APAGAT/amable: cap xifra, cap procedència — només l'estat.
	   Igual que MapTooltip, restaura els àlies de superfície (el `.tip` de sistema.css és fosc fix)
	   i neutralitza la fletxa ::after. */
	.tip--outside {
		position: absolute;
		z-index: 20;
		pointer-events: none;
		transform: translate(-50%, calc(-100% - 14px));
		min-width: 150px;
		max-width: 230px;
		padding: 10px 12px;
		box-shadow: var(--dp-shadow-md);
		background: var(--dp-surface);
		color: var(--dp-text);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-md);
	}
	.tip--outside::after {
		display: none;
	}
	.tip--outside .tip__place {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 0.95rem;
		color: var(--dp-text);
		line-height: 1.15;
	}
	.tip__out {
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-muted);
		margin-top: 4px;
	}
	.tip__out-sub {
		margin: 6px 0 0;
		font-family: var(--dp-font-sans);
		font-size: 0.78rem;
		line-height: 1.35;
		color: var(--dp-text-subtle);
	}
	.tip__out-scope {
		margin: 6px 0 0;
		padding-top: 6px;
		border-top: 1px solid var(--dp-border);
		font-family: var(--dp-font-mono);
		font-size: 0.56rem;
		line-height: 1.4;
		color: var(--dp-text-subtle);
	}

	/* Tooltip de PRESÈNCIA EN RANG (munis coberts pel Nivell C). Reusa .tip--outside (clar/amable)
	   però destaca la BANDA com a valor protagonista i hi afegeix l'ETCA de validació + el CTA. */
	.tip--range {
		min-width: 184px;
		max-width: 248px;
	}
	.tip__range {
		margin: 5px 0 0;
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 1.18rem;
		line-height: 1.12;
		color: var(--dp-text);
	}
	.tip__range-dash {
		margin: 0 2px;
		color: var(--dp-text-muted);
		font-weight: 600;
	}
	.tip__range-unit {
		font-family: var(--dp-font-sans);
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--dp-text-subtle);
	}
	.tip__range-etca {
		margin: 5px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.64rem;
		color: var(--dp-text-muted);
	}
	.tip__range-etca b {
		color: var(--dp-text);
		font-weight: 700;
	}
	/* Pista d'acció (clicable) — mirall de la de MapTooltip, redefinida aquí (estil scoped). */
	.tip__hint {
		margin: 7px 0 0;
		padding-top: 6px;
		border-top: 1px solid var(--dp-border);
		font-family: var(--dp-font-mono);
		font-size: 0.58rem;
		letter-spacing: 0.03em;
		line-height: 1.35;
		color: var(--dp-brand, #b5612a);
		font-weight: 600;
	}
	.tip__hint--link {
		display: block;
		text-decoration: none;
		cursor: pointer;
	}
	.tip--touch {
		pointer-events: auto;
	}
	.tip--touch .tip__hint--link {
		margin-top: 9px;
		padding: 8px 0 2px;
	}

	/* Accessibilitat (spec §1.5): toggle + taula alternativa del mapa per a l'indicador actiu. */
	.map-tablebar {
		display: flex;
		justify-content: flex-end;
		margin-bottom: 8px;
	}
	.map-table-toggle {
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		letter-spacing: 0.03em;
		padding: 6px 12px;
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-sm);
		background: transparent;
		color: var(--dp-text-muted);
		cursor: pointer;
	}
	.map-table-toggle:hover {
		background: var(--dp-accent-weak);
		color: var(--dp-text);
	}
	.viz-table-wrap {
		overflow-x: auto;
	}
	.viz-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.84rem;
		font-variant-numeric: tabular-nums;
	}
	.viz-table caption {
		text-align: left;
		font-weight: 600;
		margin-bottom: 8px;
		color: var(--dp-text);
	}
	.viz-table th,
	.viz-table td {
		text-align: right;
		padding: 6px 10px;
		border-bottom: 1px solid var(--dp-border);
	}
	.viz-table thead th {
		color: var(--dp-text-subtle);
		font-weight: 600;
		border-bottom: 1px solid var(--dp-border-strong);
	}
	.viz-table th[scope='row'] {
		text-align: left;
		font-weight: 500;
		color: var(--dp-text);
	}
</style>
