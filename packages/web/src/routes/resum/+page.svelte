<script lang="ts">
	/**
	 * Pàgina «Resum comarcal» a alta fidelitat (DA final · captures 01 i 02).
	 *
	 * Estructura del target:
	 *  · Hero amb eyebrow mono (coordenada + comarca), H1 Archivo «Resum comarcal»
	 *    (comarcal en accent) i corbes de nivell etiquetades al marge dret.
	 *  · Bloc A — 5 fitxes KPI comarcals amb punt de procedència (mesurada/derivada) i font.
	 *  · Bloc B — «Dos extrems»: eix IETR 0-100 (Berga ↔ Castellar) + 2 fitxes de municipi.
	 *
	 * Disciplina de dades: el MARKUP és fidel al target, però CAP xifra és inventada ni cap
	 * etiqueta codificada: valors, labels, unitats i fonts surten del dataset real (contracte
	 * semàntic) via `formatMetric`/`pick`. La procedència (slate=mesurada, porpra=derivada) es
	 * dedueix del `source` amb `provenanceOf` (mateixa regla que el mapa). El CSS és del
	 * design-system (aplicacio.css): classes .ap-hero, .kpi-grid, .axis, .extremes.
	 */
	import ContourField from '$lib/components/ContourField.svelte';
	import { currentLocale, pick } from '$lib/i18n';
	import { formatMetric, formatDecimal } from '$lib/format';
	import { provenanceOf } from '$lib/map/provenance';
	import { m } from '$lib/paraglide/messages';
	import type { MetricDef, MetricKey, MetricValue, MunicipiRow } from '$lib/contract/types';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const featured = $derived(data.featured);
	const locale = $derived(currentLocale());

	// KPIs comarcals (ordre editorial del target). El nombre de municipis va a l'eyebrow/lede.
	const comarcaKpis: MetricKey[] = [
		'poblacio',
		'rtc_total',
		'rtc_per_1000hab',
		'pct_noprincipal',
		'kg_hab_any'
	];

	// Indicadors de cada fitxa de municipi (ordre del target). hl = files ressaltades.
	const fichaKeys: MetricKey[] = [
		'poblacio',
		'hab_total',
		'hab_noprincipal',
		'pct_noprincipal',
		'hab_per_hab',
		'rtc_total',
		'rtc_hut',
		'rtc_per_1000hab',
		'kg_hab_any'
	];
	const highlightRows = new Set<MetricKey>(['pct_noprincipal', 'rtc_per_1000hab']);

	// Unitats curtes que mostra el target a la línia de cada xifra (compactes, no del contracte:
	// el contracte dona la unitat llarga; aquí en triem la forma curta editorial que es veu a la
	// captura). Buida = sense unitat visible.
	const SHORT_UNIT: Partial<Record<MetricKey, string>> = {
		poblacio: 'hab.',
		rtc_per_1000hab: '‰'
	};

	const provDotClass = (p: ReturnType<typeof provenanceOf>) =>
		p === 'derived' ? 'dot--derived' : 'dot--measured';

	// Formata un valor SENSE el símbol de percentatge: el «%» (i la resta d'unitats curtes)
	// el posa el markup com a unitat petita, com al target. Així el «%» no surt duplicat
	// (formatMetric/percent ja l'afegiria). Per la resta de formats, delega a formatMetric.
	function fmtValue(value: MetricValue | undefined, def: MetricDef): string {
		if (value === null || value === undefined) return m.value_not_available();
		if (def.format === 'percent' && typeof value === 'number') {
			return formatDecimal(value, locale, 1);
		}
		return formatMetric(value, def, locale) ?? m.value_not_available();
	}

	// Valor d'una mètrica per a un municipi, ja formatat al locale (sense unitat).
	function fmt(row: MunicipiRow, key: MetricKey): string {
		return fmtValue(row.values[key], dataset.metrics[key]);
	}

	// Procedència d'una mètrica per a un municipi (per pintar el punt).
	function prov(row: MunicipiRow, key: MetricKey) {
		const v = row.values[key];
		return provenanceOf(dataset.metrics[key], v !== null && v !== undefined);
	}

	// Línia de font curta per a un KPI: "Font · data" amb la mateixa forma del target.
	function srcLine(def: MetricDef): string {
		return def.date ? `${def.source} · ${def.date}` : def.source;
	}

	// Valors comarcals (precalculats al dataset) ja formatats (sense unitat).
	function comarcaFmt(key: MetricKey): string {
		return fmtValue(dataset.comarca.values[key], dataset.metrics[key]);
	}
	function comarcaProv(key: MetricKey) {
		const v = dataset.comarca.values[key];
		return provenanceOf(dataset.metrics[key], v !== null && v !== undefined);
	}

	const castellar = $derived(featured.castellar);
	const berga = $derived(featured.berga);

	// IETR formatat per a l'eix i el rètol gran (1 decimal, localitzat).
	const ietrCastellar = $derived(
		typeof castellar.values.IETR === 'number' ? castellar.values.IETR : 0
	);
	const ietrBerga = $derived(typeof berga.values.IETR === 'number' ? berga.values.IETR : 0);
	const fmtIetr = (v: number) => formatDecimal(v, locale, 1);

	// Caveat (note del contracte) de l'IETR, com al target.
	const ietrNote = $derived(pick(dataset.metrics.IETR.note ?? { ca: '', es: '' }, locale));

	// Corbes del hero (cims + divisòria + etiquetes de dada real), valors del target.
	const heroSummits = [
		{ cx: 890, cy: 150, r0: 16, step: 23, rings: 11, sq: 0.95, seed: 0.6, lt: 0.03 },
		{ cx: 1085, cy: 300, r0: 14, step: 21, rings: 9, sq: 1.05, seed: 2.3, lt: 0.1 }
	];
	const heroDivis = { cx: 770, cy: 230, r: 150, sq: 1.18, seed: 1.4 };
	const heroLabels = ['41.523', '33,8 %', '14,3 ‰', '452,4', '166', '593', '1.245 m'];
</script>

<svelte:head>
	<title>{m.resum_title()} · {m.app_name()}</title>
</svelte:head>

<section data-view="resum" class="on">
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
				<span>{m.resum_eyebrow_obs()}</span><span class="sep">/</span><span
					>{m.resum_eyebrow_comarca()}</span
				><span class="sep">/</span><span>42°16′N · 1°53′E</span>
			</p>
			<h1>{m.resum_h1_a()} <span class="q">{m.resum_h1_b()}</span>.</h1>
			<p class="lede">
				{m.resum_lede_a()} <b class="warm">{m.resum_lede_extrems()}</b>
				{m.resum_lede_b()}
			</p>
		</div>
	</div>

	<div class="ds-main">
		<!-- Bloc A · Indicadors comarcals -->
		<section class="ds-sec" style="border-top:none">
			<div class="ds-sec__hd">
				<span class="ref">A</span><h2>{m.resum_kpis_title()}</h2>
			</div>
			<div class="kpi-grid">
				{#each comarcaKpis as key (key)}
					{@const def = dataset.metrics[key]}
					{@const isPct = def.format === 'percent'}
					{@const unit = SHORT_UNIT[key]}
					<div class="kpi">
						<div class="n tnum">
							{comarcaFmt(key)}{#if isPct}<span class="u">%</span>{:else if unit}<span class="u"
									>{unit}</span
								>{/if}
						</div>
						<div class="lab">{pick(def.label, locale)}</div>
						<div class="src">
							<span class="dot {provDotClass(comarcaProv(key))}"></span>
							<span>{srcLine(def)}</span>
						</div>
					</div>
				{/each}
			</div>
			<div class="prov-key">
				<span><span class="dot dot--measured"></span><span>{m.prov_key_measured()}</span></span>
				<span><span class="dot dot--derived"></span><span>{m.prov_key_derived()}</span></span>
			</div>
		</section>

		<!-- Bloc B · Dos extrems -->
		<section class="ds-sec">
			<div class="ds-sec__hd">
				<span class="ref">B</span><h2>{m.resum_compare_title()}</h2>
			</div>
			<p class="lead">{m.resum_compare_lede()}</p>

			<!-- eix IETR 0–100 amb els dos municipis plotejats -->
			<div class="axis">
				<div class="axis__track">
					<div class="axis__pin up" style="left:{ietrCastellar}%">
						<span class="tag"
							><b>{castellar.nom.split(' ')[0]}</b> · <span class="v">{fmtIetr(ietrCastellar)}</span></span
						><span class="dot"></span>
					</div>
					<div class="axis__pin dn" style="left:{ietrBerga}%">
						<span class="tag"><b>{berga.nom}</b> · <span class="v">{fmtIetr(ietrBerga)}</span></span
						><span class="dot"></span>
					</div>
				</div>
				<div class="axis__ends">
					<span>{m.resum_axis_lo()}</span><span>{m.resum_axis_hi()}</span>
				</div>
			</div>

			<div class="extremes">
				{#each [{ row: castellar, variant: 'high' }, { row: berga, variant: 'low' }] as ex (ex.row.ine5)}
					{@const ietr = typeof ex.row.values.IETR === 'number' ? ex.row.values.IETR : 0}
					{@const rank = ex.row.values.IETR_rank}
					{@const elev = ex.row.ine5 === '08052' ? '1.245 m' : ex.row.ine5 === '08022' ? '704 m' : ''}
					<article class="ex ex--{ex.variant}">
						<div class="ex__hd">
							<span class="ex__rank"
								>{m.resum_rank()} <b>{rank ?? '—'}</b> {m.resum_rank_of()}</span
							>
							<div class="ex__ietr">
								<span class="v tnum">{fmtIetr(ietr)}</span><span class="u">{m.resum_ietr_scale()}</span>
							</div>
							<h3 class="ex__name">{ex.row.nom}</h3>
							<p class="ex__meta">
								<span>INE {ex.row.ine5}</span><span
									>{formatMetric(ex.row.values.poblacio, dataset.metrics.poblacio, locale)} hab.</span
								>{#if elev}<span>{elev}</span>{/if}
							</p>
						</div>
						<div class="ex__rows tnum">
							{#each fichaKeys as key (key)}
								{@const def = dataset.metrics[key]}
								{@const isPct = def.format === 'percent'}
								{@const unit = SHORT_UNIT[key]}
								<div class="ex__row" class:hl={highlightRows.has(key)}>
									<span class="k"
										><span class="pd {provDotClass(prov(ex.row, key))}"></span><span
											>{pick(def.label, locale)}</span
										></span
									>
									<span class="val"
										>{fmt(ex.row, key)}{#if isPct}<span class="u">%</span>{:else if unit}<span
												class="u">{unit}</span
											>{/if}</span
									>
								</div>
							{/each}
						</div>
					</article>
				{/each}
			</div>

			<div class="caveats">
				<div class="alert"><span class="bar"></span><div>{ietrNote}</div></div>
			</div>

			<p class="srcline">{m.resum_srcline()}</p>
		</section>
	</div>
</section>
