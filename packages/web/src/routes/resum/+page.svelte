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
	import { SIGNED_RATIO_PCT_KEYS } from '$lib/map/classify';
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
	// Bloc 1: senyals MESURATS (es queden tal qual, els de sempre).
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

	// Subgrups afegits sota els mesurats, separats pedagògicament (mesura → inferència).
	// El punt de procedència NO es força: el determina el contracte via `provenanceOf`
	// (els inputs físics surten slate si la seva font és oficial; les 3 capes, porpra,
	// perquè la seva font és "datapoble (calculat)"). `restauracio_per_1000hab` és un
	// derivat OSM, així que el seu punt seguirà igualment el contracte.
	type FichaGroup = { label: () => string; keys: MetricKey[] };
	const fichaGroups: FichaGroup[] = [
		{ label: m.resum_grp_fisics, keys: ['kwh_hab', 'vidre_hab', 'restauracio_per_1000hab'] },
		{ label: m.resum_grp_capes, keys: ['gap_pernocta_pct', 'carrega_total_est', 'index_turisme'] }
	];

	// Files ressaltades: els proxies de pernocta/no-principal i la mètrica estrella del
	// bloc inferit, `gap_pernocta_pct` (la població invisible).
	const highlightRows = new Set<MetricKey>([
		'pct_noprincipal',
		'rtc_per_1000hab',
		'gap_pernocta_pct'
	]);

	// Mètriques on un 0 NO és una dada sinó absència de mapeig (recompte mínim d'OSM,
	// no cens): es mostren com a «sense dada», no com a «0,0». Honestedat de procedència.
	const ZERO_IS_ABSENT = new Set<MetricKey>(['restauracio_per_1000hab']);

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

	// Valor efectiu d'una mètrica per a un municipi, aplicant la regla d'honestedat:
	// per a les claus de ZERO_IS_ABSENT un 0 és buit de mapeig (OSM), no una dada, i es
	// tracta com a absent (null). Centralitzat perquè `fmt` i `prov` siguin coherents.
	function effectiveValue(row: MunicipiRow, key: MetricKey): MetricValue | undefined {
		const v = row.values[key];
		if (ZERO_IS_ABSENT.has(key) && v === 0) return null;
		return v;
	}

	// Valor d'una mètrica per a un municipi, ja formatat al locale (sense unitat).
	// Cas especial: les mètriques de ràtio amb signe (el gap de pernocta) es publiquen al
	// contracte com a ràtio 0-1 (Castellar 0,313 → +31 %); cal multiplicar-les per 100 i
	// marcar el +/− abans del camí genèric. El «%» NO va aquí: el posa el markup com a unitat
	// petita `.u` (def.format === 'percent' → isPct), igual que la resta de percentatges. Mateix
	// conveni que el mapa (makeMetricFormatter de $lib/map/classify), sense duplicar el ×100.
	function fmt(row: MunicipiRow, key: MetricKey): string {
		const value = effectiveValue(row, key);
		if (SIGNED_RATIO_PCT_KEYS.has(key) && typeof value === 'number') {
			const loc = locale === 'es' ? 'es-ES' : 'ca-ES';
			return new Intl.NumberFormat(loc, {
				signDisplay: 'exceptZero',
				maximumFractionDigits: 0
			}).format(value * 100);
		}
		return fmtValue(value, dataset.metrics[key]);
	}

	// Procedència d'una mètrica per a un municipi (per pintar el punt). Si el valor
	// efectiu és absent (incl. el 0-com-a-buit d'OSM), surt com a «sense dada».
	function prov(row: MunicipiRow, key: MetricKey) {
		const v = effectiveValue(row, key);
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

<!-- Una fila d'indicador d'una fitxa (clau + valor amb unitat curta i punt de
     procedència). Reutilitzada pels mesurats i pels dos subgrups inferits perquè
     comparteixin exactament la pell de `.ex__row`. -->
{#snippet fichaRow(row: MunicipiRow, key: MetricKey)}
	{@const def = dataset.metrics[key]}
	{@const isPct = def.format === 'percent'}
	{@const unit = SHORT_UNIT[key]}
	<div class="ex__row" class:hl={highlightRows.has(key)}>
		<span class="k"
			><span class="pd {provDotClass(prov(row, key))}"></span><span>{pick(def.label, locale)}</span
			></span
		>
		<span class="val"
			>{fmt(row, key)}{#if isPct}<span class="u">%</span>{:else if unit}<span class="u">{unit}</span
				>{/if}</span
		>
	</div>
{/snippet}

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
								{@render fichaRow(ex.row, key)}
							{/each}
							<!-- Senyals inferits: 2 subgrups amb rètol mono, separats dels mesurats.
							     Mostra què és senyal físic (punt slate via contracte) i què és
							     inferència / les 3 capes (punt porpra). -->
							{#each fichaGroups as group (group.label)}
								<div class="ex__grp">{group.label()}</div>
								{#each group.keys as key (key)}
									{@render fichaRow(ex.row, key)}
								{/each}
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
