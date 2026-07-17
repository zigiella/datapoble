<script lang="ts">
	/**
	 * Pantalla «Mapa coroplètic» — APARADOR OFICIAL (fase nova, model aparcat).
	 *
	 * FASE NOVA (vot de Bea 2026-07-16 · `docs/ajuntaments/fase-nova-aparcaments.md` §A6 + §F.3):
	 * el model d'estimació de pernocta està APARCAT del web. El mapa ES MANTÉ, podat: només
	 * indicadors OFICIALS amb dada a tot Catalunya (% habitatge no principal, residus kg/hab/any).
	 * Fora: el gap de pernocta (selector i defecte), el tooltip de banda/confiança del model, la
	 * vista de cobertura del Nivell C i les llegendes divergent/categòrica que només servien el
	 * model. El rastre metodològic del model viu a /metodologia (annex de recerca).
	 *
	 * Estructura: hero amb corbes de nivell etiquetades amb els TALLS reals de l'indicador actiu,
	 * barra d'eines amb el selector, mapa real (MapLibre, 947 municipis) + panell «com es llegeix
	 * el color» + llegenda seqüencial amb talls reals. Caveats + línia de font. CAP xifra
	 * inventada: tot ve del dataset/artefactes reals i la classificació.
	 *
	 * CSS: design-system/aplicacio.css (.ap-hero, .map-toolbar, .map-stage, .map-read,
	 * .map-legend, .map-cls…). Aquí només estructura + dades + wiring.
	 */
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import ContourField from '$lib/components/ContourField.svelte';
	import ChoroplethMap from '$lib/components/ChoroplethMap.svelte';
	import MapTooltip from '$lib/components/MapTooltip.svelte';
	import { MAP_INDICATORS, DEFAULT_INDICATOR, mapValue } from '$lib/map/indicators';
	import { classify, methodFor, classRangeLabels, makeMetricFormatter } from '$lib/map/classify';
	import { rampColors } from '$lib/map/palette';
	import { slugForIne5, toSlug } from '$lib/contract/slug';
	import { currentLocale, localizeHref } from '$lib/i18n';
	import type { MetricKey } from '$lib/contract/types';
	import { m } from '$lib/paraglide/messages';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const geojson = $derived(data.geojson);
	const comarques = $derived(data.comarques);
	// Indicadors OFICIALS a escala Catalunya per pintar tots els municipis del país.
	const catValues = $derived(data.catValues);
	// Catàleg de noms (ine5 → nom) per navegar a la fitxa de qualsevol municipi.
	const cataleg = $derived(data.cataleg ?? []);
	const locale = $derived(currentLocale());

	// Tàctil (pointer coarse): a mòbil el hover no existeix → el tap mostra la targeta i NO navega;
	// la targeta es fa tocable i el seu CTA «obrir fitxa» és qui obre la fitxa del municipi.
	const coarse = browser && typeof matchMedia !== 'undefined' && matchMedia('(pointer: coarse)').matches;

	let indicator = $state<MetricKey>(DEFAULT_INDICATOR);

	// Etiqueta editorial de cada indicador del mapa (clau del contracte → text localitzat).
	// Només per a les claus de MAP_INDICATORS; `labelFor` cau a la clau si cal.
	const INDICATOR_LABEL: Partial<Record<MetricKey, () => string>> = {
		pct_noprincipal: () => m.map_ind_nop(),
		kg_hab_any: () => m.map_ind_res()
	};
	const labelFor = (key: MetricKey): string => INDICATOR_LABEL[key]?.() ?? key;

	// Sèrie de valors de l'indicador actiu sobre TOT Catalunya: valor del Berguedà (dataset) o,
	// si no, el de catValues (escala CAT), perquè els talls/colors abastin tots els municipis.
	// `mapValue` degrada el 0 d'OSM a null on toca (no ancora el mínim de Jenks).
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
	const def = $derived(dataset.metrics[indicator]);

	// Colors per classe de la rampa seqüencial (els mateixos que pinta el canvas), per a la llegenda.
	const legendColors = $derived(rampColors(classification.classes));
	// Etiquetes de rang de cada classe (formatades al locale i a la clau de mètrica).
	const rangeLabels = $derived(classRangeLabels(classification, def.format, locale, indicator));

	// Mètode llegible per al subtítol de la llegenda seqüencial (Jenks / cuantils).
	const methodCaption = $derived(
		method === 'quantiles' ? m.map_method_quantiles() : m.map_method_jenks()
	);

	// Accessibilitat (spec §1.5): alternativa en TAULA del mapa per a l'indicador actiu.
	// Dades del Berguedà (dataset ric); ordre per valor (numèric, desc).
	let showTable = $state(false);
	const valueFmt = $derived(makeMetricFormatter(indicator, def.format, locale));
	const mapTableRows = $derived.by(() => {
		const rows = Object.values(dataset.municipis).map((muni) => {
			const raw = muni.values[indicator];
			const display =
				raw === null || raw === undefined ? m.value_not_available() : valueFmt(raw as number);
			return { ine5: muni.ine5, nom: muni.nom, raw, display };
		});
		return rows.sort((a, b) => {
			const av = typeof a.raw === 'number' ? a.raw : -Infinity;
			const bv = typeof b.raw === 'number' ? b.raw : -Infinity;
			return bv - av;
		});
	});

	// Corbes del hero amb els TALLS reals de l'indicador actiu (cotes del full topogràfic, no
	// xifres inventades); l'última etiqueta és el rètol del full.
	const heroLabels = $derived.by(() => {
		const fmt = makeMetricFormatter(indicator, def.format, locale);
		const vals = [classification.max, ...classification.breaks, classification.min]
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
		/** True si el municipi té dada per a l'indicador actiu; fals → «sense dada». */
		inBergueda: boolean;
		x: number;
		y: number;
	}
	let hover = $state<Hover | null>(null);

	// Clic a un municipi → navega a la seva FITXA (`/municipi/[slug]`): els 947 la tenen
	// (prerenderitzada, amb les dades oficials del muni). El nom surt del catàleg.
	function onMuniSelect(ine5: string | null) {
		if (!ine5) return;
		if (dataset.municipis[ine5]) {
			goto(localizeHref(`/municipi/${slugForIne5(ine5, dataset)}`));
			return;
		}
		const hit = cataleg.find((c) => c.ine5 === ine5);
		if (hit) goto(localizeHref(`/municipi/${toSlug(hit.nom)}`));
	}
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
				<span>{m.map_eyebrow_a()}</span><span class="sep">·</span><span>{m.map_eyebrow_b()}</span>
			</p>
			<h1>{m.map_h1_a()} <span class="q">{m.map_h1_b()}</span>.</h1>
			<p class="lede">{m.map_lede()}</p>
		</div>
	</div>

	<div class="ds-main">
		<section class="ds-sec" style="border-top:none">
			<!-- Barra d'eines: selector d'indicador (només oficials). -->
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

			<!-- Graella: mapa real (esquerra) + lectura del color i llegenda (dreta).
			     Presentacio simple: SENSE marc de paper ni corbes; el MapLibre omple net el seu
			     contenidor i .map-canvaswrap deixa overflow visible perque les targetes/tooltips
			     de municipi no es retallin (decisio Bea). -->
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
			{#if !showTable}
				<div class="map-wrap">
					<div class="map-canvaswrap">
						{#if browser}
							<ChoroplethMap
								{dataset}
								{geojson}
								{comarques}
								{indicator}
								{classification}
								{catValues}
								fitTo="catalunya"
								onhover={(p) => (hover = p)}
								onselect={onMuniSelect}
							/>
							{#if hover}
								{#if hover.value != null}
									<!-- UN SOL tooltip per a tot Catalunya: indicador oficial + procedència. -->
									<MapTooltip
										nom={hover.nom}
										metricKey={indicator}
										{def}
										value={hover.value}
										x={hover.x}
										y={hover.y}
										hint={coarse ? m.map_open_fitxa_touch() : m.map_open_fitxa()}
										touchMode={coarse}
										href={localizeHref(`/municipi/${toSlug(hover.nom)}`)}
									/>
								{:else}
									<!-- Municipi SENSE dada de l'indicador actiu: estat amable «sense dada»
									     (NO un tooltip de dada buida; honestedat: no fingim dada). -->
									<div
										class="tip card tip--outside"
										style="left:{hover.x}px; top:{hover.y}px"
										role="tooltip"
										aria-live="polite"
									>
										<div class="tip__place">{hover.nom}</div>
										<div class="tip__out">{m.map_tooltip_nodata()}</div>
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
							<p class="read">{m.map_read_seq()}</p>
						</div>
						<div class="map-legend">
							<!-- llegenda SEQÜENCIAL amb talls reals -->
							<div>
								<p class="legend__hd"><span>{labelFor(indicator)}</span></p>
								<p class="ds-block__lab" style="border:none;margin:0 0 10px;padding:0">
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

							<div class="legend__nodata" style="margin-top:13px">
								<span
									style="width:26px;height:14px;border-radius:2px;display:inline-block;background:#E3E3DE;background-image:repeating-linear-gradient(45deg,#94A0AF 0 1.5px,transparent 1.5px 5px);border:1px solid var(--dp-border-strong)"
								></span><span>{m.map_legend_nodata()}</span>
							</div>
							<!-- Municipis sense dada de l'indicador actiu: atenuats, mai acolorits. -->
							<div class="legend__nodata" style="margin-top:8px">
								<span
									style="width:26px;height:14px;border-radius:2px;display:inline-block;background:var(--dp-map-land,#F2F1EC);opacity:0.7;border:1px solid var(--dp-border)"
								></span><span>{m.map_legend_dimmed()}</span>
							</div>
							<p class="legend__estimat">{m.map_legend_estimat()}</p>
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
							</tr>
						</thead>
						<tbody>
							{#each mapTableRows as r (r.ine5)}
								<tr>
									<th scope="row">{r.nom}</th>
									<td>{r.display}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}

			<div class="caveats" style="margin-top:20px">
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

	/* Nota d'honestedat de la llegenda: on falta la dada, el municipi queda atenuat. */
	.legend__estimat {
		margin: 13px 0 0;
		font-family: var(--dp-font-sans);
		font-size: 0.68rem;
		line-height: 1.4;
		color: var(--dp-text-subtle);
	}

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
		min-height: 600px;
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
		min-height: 600px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--dp-text-subtle);
		font-family: var(--dp-font-mono);
		font-size: 0.8rem;
	}

	/* Tooltip «sense dada» per als municipis sense valor de l'indicador actiu.
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
	.tip__out-scope {
		margin: 6px 0 0;
		padding-top: 6px;
		border-top: 1px solid var(--dp-border);
		font-family: var(--dp-font-mono);
		font-size: 0.56rem;
		line-height: 1.4;
		color: var(--dp-text-subtle);
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
