<script lang="ts">
	/**
	 * FITXA DE MUNICIPI (`/municipi/[ine5]` · `/es/municipi/[ine5]`).
	 *
	 * Generalitza a QUALSEVOL dels 31 municipis del Berguedà la fitxa rica que el Resum només
	 * donava als dos extrems (Berga 08022, Castellar de n'Hug 08052). Mateixa presentació i
	 * mateixa honestedat: nom + pastilla de TIPOLOGIA (arquetip categòric) + bandera de CONFIANÇA
	 * i score auditable 0-100, i TOTES les mètriques del municipi agrupades editorialment (KPI
	 * bàsics, senyals físics per càpita, les 3 capes inferides, IETR + stock/impact, energia,
	 * política), cadascuna amb la seva PROCEDÈNCIA (punt mesura/inferència) i la unitat del
	 * contracte.
	 *
	 * Disciplina de dades (com al Resum/Mapa/Glossari): CAP xifra, etiqueta, unitat ni font es
	 * codifica a la UI — tot surt del dataset real (= contracte semàntic) via `formatMetric`/`pick`.
	 * La procedència (slate=mesurada, porpra=inferència) la dedueix `provenanceOf` del `source`. Les
	 * 3 capes són inferència; el 0 d'OSM de la restauració es mostra «sense dada», no «0,0» (honestedat).
	 *
	 * Si l'`ine5` no és al dataset (resta de Catalunya) → estat AMABLE «sense dades encara» (mateix
	 * gest que el tooltip «fora del Berguedà» del mapa), mai una fitxa buida ni un error lleig.
	 *
	 * Chrome del design-system (.ap-hero + .ds-main/.ds-sec); el text nou és i18n ca/es.
	 */
	import { goto } from '$app/navigation';
	import ContourField from '$lib/components/ContourField.svelte';
	import { currentLocale, pick, localizeHref } from '$lib/i18n';
	import { formatMetric, formatDecimal, formatInteger } from '$lib/format';
	import { SIGNED_PCT_KEYS } from '$lib/map/classify';
	import { provenanceOf } from '$lib/map/provenance';
	import { tipologiaMeta } from '$lib/map/tipologia';
	import { m } from '$lib/paraglide/messages';
	import type { MetricDef, MetricKey, MetricValue, MunicipiRow } from '$lib/contract/types';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const row = $derived(data.row);
	const ine5 = $derived(data.ine5);
	const locale = $derived(currentLocale());

	// ── Blocs editorials que cobreixen TOT el catàleg del contracte ──────────────────────────
	// Mateix esperit que la metodologia/Resum, però aquí l'objectiu és NO deixar fora cap mètrica
	// del municipi. Les claus van en ordre editorial (de mesurat → inferit). El subtítol distingeix
	// senyal físic (mesura) d'inferència (les 3 capes), com els subgrups del Resum.
	type FichaBlock = {
		ref: string;
		title: () => string;
		sub?: () => string;
		keys: MetricKey[];
	};
	const blocks: FichaBlock[] = [
		{
			ref: 'A',
			title: () => m.muni_blk_demografia(),
			keys: ['poblacio', 'hab_total', 'hab_principal', 'hab_noprincipal', 'pct_noprincipal', 'hab_per_hab', 'index_envelliment']
		},
		{
			ref: 'B',
			title: () => m.muni_blk_origen(),
			sub: () => m.muni_blk_origen_sub(),
			keys: [
				'poblacio_nascuda_catalunya',
				'poblacio_nascuda_resta_espanya',
				'poblacio_nascuda_estranger',
				'pct_nascuda_estranger',
				'pct_nacionalitat_estrangera',
				'bretxa_naturalitzacio',
				'delta_pct_estrangera_finestra',
				'confianca_origen'
			]
		},
		{
			ref: 'C',
			title: () => m.muni_blk_turisme(),
			keys: ['rtc_total', 'rtc_hut', 'rtc_per_1000hab', 'rtc_per_100hab_viv']
		},
		{
			ref: 'D',
			title: () => m.muni_blk_fisics(),
			sub: () => m.resum_grp_fisics(),
			keys: ['kg_hab_any', 'kwh_hab', 'vidre_hab', 'restauracio_estab', 'restauracio_per_1000hab']
		},
		{
			ref: 'E',
			title: () => m.muni_blk_capes(),
			sub: () => m.muni_blk_capes_sub(),
			keys: [
				'poblacio_pernocta_est',
				'gap_pernocta',
				'gap_pernocta_pct',
				'carrega_total_est',
				'index_turisme'
			]
		},
		{
			ref: 'F',
			title: () => m.muni_blk_ietr(),
			sub: () => m.muni_blk_ietr_sub(),
			keys: ['IETR', 'IETR_rank', 'IETR_stock', 'IETR_impact', 'pct_icaen_EFG']
		},
		{
			ref: 'G',
			title: () => m.muni_blk_politica(),
			sub: () => m.muni_blk_politica_sub(),
			keys: ['guanya', 'pct_indep', 'pct_esquerra', 'pct_extrema_dreta']
		}
	];

	// Files ressaltades: els proxies de pernocta/no-principal i la mètrica estrella (gap pernocta,
	// la població invisible) + l'IETR. Mateix criteri editorial que el Resum.
	const highlightRows = new Set<MetricKey>([
		'pct_noprincipal',
		'rtc_per_1000hab',
		'bretxa_naturalitzacio',
		'gap_pernocta_pct',
		'IETR'
	]);

	// Mètriques on un 0 NO és dada sinó absència de mapeig (recompte mínim d'OSM, no cens): es
	// mostren «sense dada», no «0,0». Mateixa regla d'honestedat que el Resum i el mapa.
	const ZERO_IS_ABSENT = new Set<MetricKey>(['restauracio_per_1000hab', 'restauracio_estab']);

	// Unitats curtes editorials a la línia de cada xifra (com al Resum: el contracte dona la unitat
	// llarga; aquí la forma curta de la captura). Buida = sense unitat curta (cau a la del contracte).
	const SHORT_UNIT: Partial<Record<MetricKey, string>> = {
		poblacio: 'hab.',
		hab_total: 'hab.',
		hab_principal: 'hab.',
		hab_noprincipal: 'hab.',
		poblacio_pernocta_est: 'hab.',
		carrega_total_est: 'hab.',
		gap_pernocta: 'hab.',
		poblacio_nascuda_catalunya: 'hab.',
		poblacio_nascuda_resta_espanya: 'hab.',
		poblacio_nascuda_estranger: 'hab.',
		bretxa_naturalitzacio: 'pts',
		delta_pct_estrangera_finestra: 'pts',
		rtc_per_1000hab: '‰'
	};

	const provDotClass = (p: ReturnType<typeof provenanceOf>) =>
		p === 'derived' ? 'dot--derived' : 'dot--measured';

	// Valor efectiu d'una mètrica: aplica la regla d'honestedat del 0-com-a-buit (OSM).
	function effectiveValue(r: MunicipiRow, key: MetricKey): MetricValue | undefined {
		const v = r.values[key];
		if (ZERO_IS_ABSENT.has(key) && v === 0) return null;
		return v;
	}

	// Formata SENSE el símbol de percentatge (el «%» el posa el markup com a unitat petita, com al
	// Resum, per no duplicar-lo). La resta de formats deleguen a formatMetric (contracte).
	function fmtValue(value: MetricValue | undefined, def: MetricDef): string {
		if (value === null || value === undefined) return m.value_not_available();
		if (def.format === 'percent' && typeof value === 'number') {
			return formatDecimal(value, locale, 1);
		}
		return formatMetric(value, def, locale) ?? m.value_not_available();
	}

	// Valor d'una mètrica per al municipi, formatat al locale (sense unitat). Cas especial: les
	// desviacions amb signe (gaps de pernocta) amb +/− explícit; el valor ja ve 0-100, no es reescala.
	// Mateix conveni que el Resum i el mapa.
	function fmt(r: MunicipiRow, key: MetricKey): string {
		const value = effectiveValue(r, key);
		if (SIGNED_PCT_KEYS.has(key) && typeof value === 'number') {
			const loc = locale === 'es' ? 'es-ES' : 'ca-ES';
			return new Intl.NumberFormat(loc, {
				signDisplay: 'exceptZero',
				maximumFractionDigits: 0
			}).format(value);
		}
		return fmtValue(value, dataset.metrics[key]);
	}

	// Procedència d'una mètrica per al municipi (per pintar el punt). Valor absent (incl. 0-OSM) →
	// «sense dada».
	function prov(r: MunicipiRow, key: MetricKey) {
		const v = effectiveValue(r, key);
		return provenanceOf(dataset.metrics[key], v !== null && v !== undefined);
	}

	// Font · data del contracte (per a la línia de procedència de cada bloc).
	function srcLine(def: MetricDef): string {
		return def.date ? `${def.source} · ${def.date}` : def.source;
	}

	// ── Capçalera del municipi: tipologia + confiança (idèntica lectura que el Resum) ─────────
	const tipo = $derived(row ? tipologiaMeta(row.values.tipologia) : undefined);
	const score = $derived.by<number | null>(() => {
		const s = row?.values.confianca_score;
		return typeof s === 'number' && Number.isFinite(s) ? s : null;
	});
	const confFlag = $derived(row?.values.confianca as string | undefined);
	const confLabel = $derived.by<string | null>(() => {
		if (confFlag === 'alta') return m.map_confidence_high();
		if (confFlag === 'mitjana') return m.map_confidence_mid();
		if (confFlag === 'baixa') return m.map_confidence_low();
		return null;
	});

	// IETR per al rètol gran de la capçalera (1 decimal) i el rang.
	const ietr = $derived.by<number | null>(() => {
		const v = row?.values.IETR;
		return typeof v === 'number' ? v : null;
	});
	const ietrRank = $derived(row?.values.IETR_rank ?? null);
	const numMunis = $derived(dataset.comarca.num_municipis);

	// Nom del municipi (topònim, igual en ambdós locales) o, sense dada, el codi.
	const muniNom = $derived(row?.nom ?? ine5);

	// ── Selector de municipi: salta a un altre dels 31 (ordenat per nom, localitzat) ──────────
	// Es deriva del dataset (no llista codificada). El canvi navega a la fitxa corresponent.
	const muniOptions = $derived.by(() => {
		const items = Object.values(dataset.municipis).map((mr) => ({ ine5: mr.ine5, nom: mr.nom }));
		const coll = new Intl.Collator(locale === 'es' ? 'es-ES' : 'ca-ES');
		return items.sort((a, b) => coll.compare(a.nom, b.nom));
	});
	function onPickMuni(e: Event) {
		const v = (e.currentTarget as HTMLSelectElement).value;
		if (v) goto(localizeHref(`/municipi/${v}`));
	}

	// Corbes del hero (rètols editorials del full topogràfic; no xifres de cap municipi concret).
	const heroSummits = [
		{ cx: 895, cy: 148, r0: 15, step: 22, rings: 10, sq: 0.97, seed: 0.9, lt: 0.03 },
		{ cx: 1078, cy: 300, r0: 13, step: 20, rings: 8, sq: 1.06, seed: 2.7, lt: 0.1 }
	];
	const heroDivis = { cx: 768, cy: 228, r: 150, sq: 1.18, seed: 1.2 };
	const heroLabels = ['INE', 'tipologia', 'confiança', '31', 'mètriques', 'procedència', 'fitxa'];
</script>

<!-- Una fila d'indicador (clau + punt de procedència + valor amb unitat curta). Reutilitza la
     pell de `.ex__row` del Resum perquè la fitxa sigui visualment idèntica. -->
{#snippet fichaRow(r: MunicipiRow, key: MetricKey)}
	{@const def = dataset.metrics[key]}
	{@const isPct = def.format === 'percent'}
	{@const unit = SHORT_UNIT[key]}
	<div class="ex__row" class:hl={highlightRows.has(key)}>
		<span class="k"
			><span class="pd {provDotClass(prov(r, key))}"></span><span>{pick(def.label, locale)}</span
			></span
		>
		<span class="val"
			>{fmt(r, key)}{#if isPct}<span class="u">%</span>{:else if unit}<span class="u">{unit}</span
				>{/if}</span
		>
	</div>
{/snippet}

<svelte:head>
	<title>{muniNom} · {m.muni_title()} · {m.app_name()}</title>
	<meta name="description" content={m.muni_meta_desc({ nom: muniNom })} />
</svelte:head>

<section data-view="municipi" class="on">
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
				<span>{m.muni_eyebrow_a()}</span><span class="sep">/</span><span
					>{m.muni_eyebrow_b({ comarca: pick(dataset.comarca.label, locale) })}</span
				><span class="sep">/</span><span>INE {ine5}</span>
			</p>
			<h1>{muniNom}</h1>
			{#if row}
				<p class="lede">{m.muni_lede()}</p>
			{:else}
				<p class="lede">{m.muni_outside_lede()}</p>
			{/if}
		</div>
	</div>

	<div class="ds-main">
		<!-- Selector per saltar a un altre municipi del Berguedà (sempre disponible). -->
		<section class="ds-sec" style="border-top:none">
			<div class="muni-pick">
				<label for="muni-select">{m.muni_pick_label()}</label>
				<select id="muni-select" class="select" value={ine5} onchange={onPickMuni}>
					{#each muniOptions as o (o.ine5)}
						<option value={o.ine5}>{o.nom}</option>
					{/each}
				</select>
				<a class="muni-pick__map" href={localizeHref('/mapa')}>{m.muni_pick_map()}</a>
			</div>
		</section>

		{#if row}
			<!-- Capçalera de dades: rang IETR + valor gran, tipologia (pastilla) i confiança + score.
			     És la MATEIXA lectura destacada que les fitxes dels extrems del Resum, ara per a
			     qualsevol municipi. -->
			<section class="ds-sec">
				<div class="muni-card">
					<div class="muni-card__top">
						<span class="muni-card__rank"
							>{m.resum_rank()} <b>{ietrRank ?? '—'}</b> {m.resum_rank_of()} {formatInteger(numMunis, locale)}</span
						>
						{#if ietr !== null}
							<div class="muni-card__ietr">
								<span class="v tnum">{formatDecimal(ietr, locale, 1)}</span><span class="u"
									>{m.resum_ietr_scale()}</span
								>
							</div>
						{/if}
					</div>
					<p class="muni-card__meta">
						<span>INE {ine5}</span>
						{#if typeof row.values.poblacio === 'number'}<span
								>{formatInteger(row.values.poblacio, locale)} hab.</span
							>{/if}
						{#if row.idescat6}<span>Idescat {row.idescat6}</span>{/if}
					</p>

					<!-- Tipologia (Fase 1): la LECTURA narrativa — quin TIPUS de pressió. Pastilla amb el
					     color categòric de l'arquetip + etiqueta humana + frase curta (reusa tipologia.ts). -->
					{#if tipo}
						<div class="muni-card__tipo">
							<span class="muni-card__tipo-badge" style="--tipo-c:{tipo.color}">
								<span class="dot"></span>{tipo.label()}
							</span>
							<p class="muni-card__tipo-blurb">{tipo.blurb()}</p>
						</div>
					{/if}

					<!-- Confiança: bandera (alta/mitjana/baixa) + score auditable 0-100. Es mostren TOTS DOS
					     perquè poden divergir (el costat fi i honest de la tensió dels senyals). -->
					{#if confLabel || score !== null}
						<div class="muni-card__conf">
							<span class="muni-card__conf-lbl">{m.map_confidence_label()}</span>
							{#if confLabel}<span class="muni-card__conf-flag muni-card__conf-flag--{confFlag}"
									>{confLabel}</span
								>{/if}
							{#if score !== null}
								<span class="muni-card__conf-score" title={m.map_confidence_score_label()}
									>{formatDecimal(score, locale, 0)}<span class="muni-card__conf-scale">/100</span
									></span
								>
							{/if}
						</div>
					{/if}
				</div>
			</section>

			<!-- TOTES les mètriques, en blocs editorials. Cap mètrica del municipi queda fora; cada
			     fila porta el seu punt de procedència (mesura/inferència) del contracte. -->
			{#each blocks as block (block.ref)}
				<section class="ds-sec">
					<div class="ds-sec__hd">
						<span class="ref">{block.ref}</span><h2>{block.title()}</h2>
					</div>
					{#if block.sub}<p class="muni-sec__sub">{block.sub()}</p>{/if}
					<div class="ex__rows tnum">
						{#each block.keys as key (key)}
							{@render fichaRow(row, key)}
						{/each}
					</div>
					<p class="muni-sec__src">{srcLine(dataset.metrics[block.keys[0]])}</p>
				</section>
			{/each}

			<section class="ds-sec">
				<div class="prov-key">
					<span><span class="dot dot--measured"></span><span>{m.prov_key_measured()}</span></span>
					<span><span class="dot dot--derived"></span><span>{m.prov_key_derived()}</span></span>
				</div>
				<div class="caveats" style="margin-top:14px">
					<div class="alert"><span class="bar"></span><div>{m.muni_honesty()}</div></div>
				</div>
				<p class="srcline">{m.muni_srcline()}</p>
			</section>
		{:else}
			<!-- Municipi de FORA del Berguedà: estat AMABLE «sense dades encara» (mateixa honestedat que
			     el tooltip del mapa). Cap fitxa buida, cap xifra fingida — només l'estat i una sortida. -->
			<section class="ds-sec">
				<div class="muni-empty">
					<p class="muni-empty__badge">{m.map_outside_title()}</p>
					<h2>{m.muni_outside_h2({ nom: muniNom })}</h2>
					<p class="muni-empty__body">{m.map_outside_sub()}</p>
					<p class="muni-empty__scope">{m.map_outside_scope()}</p>
					<div class="muni-empty__actions">
						<a class="muni-empty__link" href={localizeHref('/mapa')}>{m.muni_pick_map()}</a>
						<a class="muni-empty__link muni-empty__link--alt" href={localizeHref('/resum')}
							>← {m.stub_back()}</a
						>
					</div>
				</div>
			</section>
		{/if}
	</div>
</section>

<style>
	/* Chrome (.ap-hero, .ds-main, .ds-sec, .prov-key, .caveats, .ex__row/.ex__rows…) ve del
	   design-system; aquí només els elements propis de la fitxa: el selector, la capçalera de
	   dades del municipi (pastilla de tipologia + confiança, reusant el gest del Resum), els
	   subtítols de bloc i l'estat «sense dades». */

	/* Selector de municipi. */
	.muni-pick {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-wrap: wrap;
	}
	.muni-pick label {
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
	}
	.muni-pick .select {
		min-width: 220px;
	}
	.muni-pick__map {
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		color: var(--dp-text-muted);
		text-decoration: none;
		border-bottom: 1px solid var(--dp-border-strong);
		padding-bottom: 1px;
	}
	.muni-pick__map:hover {
		color: var(--dp-text);
	}

	/* Capçalera de dades del municipi (idèntica lectura a la .ex__hd dels extrems del Resum). */
	.muni-card {
		position: relative;
	}
	.muni-card__top {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 14px;
		flex-wrap: wrap;
	}
	.muni-card__rank {
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
	}
	.muni-card__rank b {
		color: var(--dp-text);
	}
	.muni-card__ietr {
		display: flex;
		align-items: baseline;
		gap: 5px;
	}
	.muni-card__ietr .v {
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 800;
		font-size: 2rem;
		line-height: 1;
		color: var(--dp-text);
		font-feature-settings: 'tnum' 1;
	}
	.muni-card__ietr .u {
		font-family: var(--dp-font-mono);
		font-size: 0.64rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
	}
	.muni-card__meta {
		margin: 8px 0 0;
		display: flex;
		gap: 14px;
		flex-wrap: wrap;
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
		color: var(--dp-text-muted);
	}

	/* Pastilla de tipologia (mateixa pell que .ex__tipo del Resum). */
	.muni-card__tipo {
		margin: 14px 0 0;
	}
	.muni-card__tipo-badge {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 4px 11px 4px 9px;
		border-radius: 999px;
		background: color-mix(in srgb, var(--tipo-c) 14%, var(--dp-surface));
		border: 1px solid color-mix(in srgb, var(--tipo-c) 40%, var(--dp-border));
		font-family: 'Archivo', var(--dp-font-sans);
		font-weight: 700;
		font-size: 0.95rem;
		letter-spacing: -0.01em;
		color: var(--dp-text);
		line-height: 1.15;
	}
	.muni-card__tipo-badge .dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--tipo-c);
		flex: none;
		box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
	}
	.muni-card__tipo-blurb {
		margin: 7px 0 0;
		font-family: var(--dp-font-sans);
		font-size: 0.85rem;
		line-height: 1.45;
		color: var(--dp-text-muted);
		max-width: 52ch;
	}

	/* Línia de confiança (bandera + score), mateix gest que .ex__conf del Resum. */
	.muni-card__conf {
		display: flex;
		align-items: baseline;
		gap: 8px;
		margin: 12px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
	}
	.muni-card__conf-lbl {
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
	}
	.muni-card__conf-flag {
		font-weight: 700;
		color: var(--dp-text);
	}
	.muni-card__conf-flag--alta {
		color: var(--dp-success, #2f6b4f);
	}
	.muni-card__conf-flag--baixa {
		color: var(--dp-warning, #b5612a);
	}
	.muni-card__conf-score {
		font-weight: 700;
		color: var(--dp-text);
		font-feature-settings: 'tnum' 1;
	}
	.muni-card__conf-scale {
		font-weight: 500;
		color: var(--dp-text-subtle);
	}

	/* Subtítol de bloc (distingeix mesura d'inferència, com els subgrups del Resum). */
	.muni-sec__sub {
		margin: -2px 0 10px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
	}
	/* Línia de font per bloc. */
	.muni-sec__src {
		margin: 12px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.64rem;
		color: var(--dp-text-subtle);
		line-height: 1.45;
	}

	/* Estat «sense dades encara» (fora del Berguedà). To apagat i amable; cap xifra. */
	.muni-empty {
		max-width: 56ch;
		padding: var(--dp-space-4) 0;
	}
	.muni-empty__badge {
		display: inline-block;
		margin: 0 0 12px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-muted);
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-sm);
		padding: 3px 9px;
	}
	.muni-empty h2 {
		margin: 0 0 10px;
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 1.4rem;
		line-height: 1.2;
		color: var(--dp-text);
	}
	.muni-empty__body {
		margin: 0 0 8px;
		font-size: 0.95rem;
		line-height: 1.55;
		color: var(--dp-text-muted);
	}
	.muni-empty__scope {
		margin: 0 0 18px;
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		line-height: 1.5;
		color: var(--dp-text-subtle);
	}
	.muni-empty__actions {
		display: flex;
		gap: 18px;
		flex-wrap: wrap;
	}
	.muni-empty__link {
		font-family: var(--dp-font-mono);
		font-size: 0.74rem;
		color: var(--dp-text);
		text-decoration: none;
		border-bottom: 1px solid var(--dp-border-strong);
		padding-bottom: 1px;
	}
	.muni-empty__link--alt {
		color: var(--dp-text-muted);
	}
	.muni-empty__link:hover {
		color: var(--dp-forest);
	}
</style>
