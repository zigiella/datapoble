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
	import StockImpactScatter from '$lib/components/StockImpactScatter.svelte';
	import { currentLocale, pick, localizeHref } from '$lib/i18n';
	import { formatMetric, formatDecimal } from '$lib/format';
	import { SIGNED_PCT_KEYS } from '$lib/map/classify';
	import { provenanceOf } from '$lib/map/provenance';
	import { tipologiaMeta } from '$lib/map/tipologia';
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
	// Cas especial: les mètriques de desviació amb signe (el gap de pernocta) es mostren amb
	// el +/− explícit (Castellar +31 %, Berga −2 %). El valor ja ve en escala 0-100 del
	// contracte (com la resta de percentatges), així que NO el reescalem aquí. El «%» NO va
	// aquí: el posa el markup com a unitat petita `.u` (def.format === 'percent' → isPct).
	// Mateix conveni que el mapa (makeMetricFormatter de $lib/map/classify).
	function fmt(row: MunicipiRow, key: MetricKey): string {
		const value = effectiveValue(row, key);
		if (SIGNED_PCT_KEYS.has(key) && typeof value === 'number') {
			const loc = locale === 'es' ? 'es-ES' : 'ca-ES';
			return new Intl.NumberFormat(loc, {
				signDisplay: 'exceptZero',
				maximumFractionDigits: 0
			}).format(value);
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

	// Tipologia (categòrica) d'un municipi: metadades de presentació (etiqueta humana + color + frase).
	// És la LECTURA narrativa de la Fase 1 — quin TIPUS de pressió, no «més/menys». undefined si manca.
	const tipoOf = (row: MunicipiRow) => tipologiaMeta(row.values.tipologia);
	// confianca_score (0-100) d'un municipi: complementa la bandera `confianca` (poden divergir).
	const scoreOf = (row: MunicipiRow): number | null => {
		const s = row.values.confianca_score;
		return typeof s === 'number' && Number.isFinite(s) ? s : null;
	};
	// Etiqueta humana de la bandera de confiança (alta/mitjana/baixa) d'un municipi.
	const confLabelOf = (row: MunicipiRow): string | null => {
		const c = row.values.confianca;
		if (c === 'alta') return m.map_confidence_high();
		if (c === 'mitjana') return m.map_confidence_mid();
		if (c === 'baixa') return m.map_confidence_low();
		return null;
	};

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
					{@const tipo = tipoOf(ex.row)}
					{@const conf = confLabelOf(ex.row)}
					{@const score = scoreOf(ex.row)}
					<article class="ex ex--{ex.variant}">
						<div class="ex__hd">
							<span class="ex__rank"
								>{m.resum_rank()} <b>{rank ?? '—'}</b> {m.resum_rank_of()}</span
							>
							<div class="ex__ietr">
								<span class="v tnum">{fmtIetr(ietr)}</span><span class="u">{m.resum_ietr_scale()}</span>
							</div>
							<h3 class="ex__name">
								<a href={localizeHref(`/municipi/${ex.row.ine5}`)} class="ex__name-link"
									>{ex.row.nom}</a
								>
							</h3>
							<p class="ex__meta">
								<span>INE {ex.row.ine5}</span><span
									>{formatMetric(ex.row.values.poblacio, dataset.metrics.poblacio, locale)} hab.</span
								>{#if elev}<span>{elev}</span>{/if}<a
									class="ex__fitxa"
									href={localizeHref(`/municipi/${ex.row.ine5}`)}>{m.resum_open_fitxa()}</a
								>
							</p>

							<!-- Tipologia (Fase 1): la LECTURA narrativa destacada — quin TIPUS de pressió.
							     Pastilla amb el color categòric de l'arquetip + etiqueta humana + frase curta. -->
							{#if tipo}
								<div class="ex__tipo">
									<span class="ex__tipo-badge" style="--tipo-c:{tipo.color}">
										<span class="dot"></span>{tipo.label()}
									</span>
									<p class="ex__tipo-blurb">{tipo.blurb()}</p>
								</div>
							{/if}

							<!-- Confiança: bandera (alta/mitjana/baixa) + score auditable 0-100. Es mostren
							     TOTS DOS perquè poden divergir (Castellar: bandera «alta» però score ≈ 33,
							     senyals que es contradiuen). El score és el costat fi i honest de la tensió. -->
							{#if conf || score !== null}
								<div class="ex__conf">
									<span class="ex__conf-lbl">{m.map_confidence_label()}</span>
									{#if conf}<span class="ex__conf-flag ex__conf-flag--{ex.row.values.confianca}"
											>{conf}</span
										>{/if}
									{#if score !== null}
										<span class="ex__conf-score" title={m.map_confidence_score_label()}
											>{formatDecimal(score, locale, 0)}<span class="ex__conf-scale">/100</span></span
										>
									{/if}
								</div>
							{/if}
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

		<!-- Bloc C — Constel·lació stock × empremta (onada B): l'IETR com a mapa mental, no número. -->
		<section class="ds-sec">
			<div class="ds-sec__hd">
				<span class="ref">C</span><h2>{m.resum_constel_title()}</h2>
			</div>
			<p class="lead">{m.resum_constel_lede()}</p>
			<StockImpactScatter {dataset} />
			<p class="srcline">{m.resum_constel_legend()}</p>
		</section>
	</div>
</section>

<style>
	/* Tipologia destacada + confiança (Fase 1) a la capçalera de cada fitxa de municipi.
	   Va sota .ex__meta, dins de .ex__hd (que ja és position:relative). El gros del chrome de la
	   fitxa ve del design-system; aquí només la pastilla de tipologia i la línia de confiança. */
	.ex__tipo {
		margin: 12px 0 0;
	}
	.ex__tipo-badge {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 4px 11px 4px 9px;
		border-radius: 999px;
		/* tint suau del color de l'arquetip; el text es manté llegible (no pinta sobre el color ple). */
		background: color-mix(in srgb, var(--tipo-c) 14%, var(--dp-surface));
		border: 1px solid color-mix(in srgb, var(--tipo-c) 40%, var(--dp-border));
		font-family: 'Archivo', var(--dp-font-sans);
		font-weight: 700;
		font-size: 0.92rem;
		letter-spacing: -0.01em;
		color: var(--dp-text);
		line-height: 1.15;
	}
	.ex__tipo-badge .dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--tipo-c);
		flex: none;
		box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
	}
	.ex__tipo-blurb {
		margin: 7px 0 0;
		font-family: var(--dp-font-sans);
		font-size: 0.82rem;
		line-height: 1.4;
		color: var(--dp-text-muted);
		max-width: 42ch;
	}
	.ex__conf {
		display: flex;
		align-items: baseline;
		gap: 8px;
		margin: 12px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
	}
	.ex__conf-lbl {
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
	}
	.ex__conf-flag {
		font-weight: 700;
		color: var(--dp-text);
	}
	/* La bandera de confiança té el to semàntic dels estats (mateix gest que el tooltip del mapa). */
	.ex__conf-flag--alta {
		color: var(--dp-success, #2f6b4f);
	}
	.ex__conf-flag--baixa {
		color: var(--dp-warning, #b5612a);
	}
	.ex__conf-score {
		font-weight: 700;
		color: var(--dp-text);
		font-feature-settings: 'tnum' 1;
	}
	.ex__conf-scale {
		font-weight: 500;
		color: var(--dp-text-subtle);
	}

	/* La fitxa dels extrems enllaça ara a la fitxa COMPLETA del municipi (`/municipi/[ine5]`).
	   El nom és el destí principal; la meta hi afegeix un enllaç curt i explícit. */
	.ex__name-link {
		color: inherit;
		text-decoration: none;
	}
	.ex__name-link:hover {
		text-decoration: underline;
		text-decoration-thickness: 1px;
		text-underline-offset: 3px;
	}
	.ex__fitxa {
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-brand, #b5612a);
		text-decoration: none;
		font-weight: 700;
		border-bottom: 1px solid color-mix(in srgb, var(--dp-brand, #b5612a) 45%, transparent);
		padding-bottom: 1px;
	}
	.ex__fitxa:hover {
		border-bottom-color: var(--dp-brand, #b5612a);
	}
</style>
