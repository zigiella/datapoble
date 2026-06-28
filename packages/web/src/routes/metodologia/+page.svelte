<script lang="ts">
	/**
	 * Pàgina de metodologia pública (`/metodologia` · `/es/metodologia`).
	 *
	 * Explica, un per un, cada indicador de l'observatori: QUÈ mesura · COM es calcula (fórmula)
	 * · FONT i data · si és dada OFICIAL 🟦 o INFERÈNCIA 🟪. El contingut surt de dues fonts:
	 *  - docs/poblacio-real-metode.md (v2, les 3 capes, el catch del vidre, l'honestedat) i
	 *    semantic/metrics.yml (fórmules, fonts, caveats) → text explicatiu (copy i18n nou).
	 *  - el dataset real (contracte) → label, unitat, font, data i procedència de cada mètrica;
	 *    així cap font/data es codifica a mà: és el mateix contracte que pinta la resta del web.
	 *
	 * Estètica coherent amb el lloc: hero + .ds-main/.ds-sec del design-system, Archivo als
	 * titulars, tokens --dp-*; procedència amb la signatura `.prov` (slate=oficial, porpra=inferència).
	 */
	import ContourField from '$lib/components/ContourField.svelte';
	import MetodologiaModel from '$lib/components/MetodologiaModel.svelte';
	import { currentLocale, pick } from '$lib/i18n';
	import { provenanceOf } from '$lib/map/provenance';
	import { m } from '$lib/paraglide/messages';
	import type { MetricKey } from '$lib/contract/types';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const locale = $derived(currentLocale());
	// Validació externa contra ETCA (Pas 4): artefacte opcional (data/web/etca-validacio.json).
	const etca = $derived(data.etca);
	// Límits del model (Fase 1): reliability + scatter ETCA↔pernocta + règim dens. Opcional.
	const model = $derived(data.model);
	const intl = $derived(locale === 'es' ? 'es-ES' : 'ca-ES');
	const dec = (v: number, n = 1) =>
		v.toLocaleString(intl, { minimumFractionDigits: n, maximumFractionDigits: n });
	const intf = (v: number | null) => (v == null ? '—' : v.toLocaleString(intl));
	const sgn = (v: number | null) => (v == null ? '—' : `${v > 0 ? '+' : ''}${dec(v)}%`);

	// «Què mesura» (definició curta i clara) per clau de mètrica — copy i18n de funcionalitat.
	const WHAT: Partial<Record<MetricKey, () => string>> = {
		poblacio: () => m.met_poblacio_what(),
		hab_noprincipal: () => m.met_habnop_what(),
		pct_noprincipal: () => m.met_pctnop_what(),
		hab_per_hab: () => m.met_habperhab_what(),
		rtc_total: () => m.met_rtc_what(),
		rtc_per_1000hab: () => m.met_rtcratio_what(),
		kwh_hab: () => m.met_kwh_what(),
		vidre_hab: () => m.met_vidre_what(),
		kg_hab_any: () => m.met_residus_what(),
		gap_pernocta_pct: () => m.met_pernocta_what(),
		carrega_total_est: () => m.met_carrega_what(),
		index_turisme: () => m.met_turisme_what(),
		restauracio_per_1000hab: () => m.met_restauracio_what(),
		restauracio_estab: () => m.met_restauracio_what(),
		confianca: () => m.met_confianca_what(),
		IETR: () => m.met_ietr_what(),
		pct_icaen_EFG: () => m.met_efg_what(),
		pct_indep: () => m.met_indep_what(),
		pct_extrema_dreta: () => m.met_xd_what()
	};
	// «Com es calcula» (fórmula llegible) per clau — fidel a semantic/metrics.yml.
	const HOW: Partial<Record<MetricKey, () => string>> = {
		poblacio: () => m.met_poblacio_how(),
		hab_noprincipal: () => m.met_habnop_how(),
		pct_noprincipal: () => m.met_pctnop_how(),
		hab_per_hab: () => m.met_habperhab_how(),
		rtc_total: () => m.met_rtc_how(),
		rtc_per_1000hab: () => m.met_rtcratio_how(),
		kwh_hab: () => m.met_kwh_how(),
		vidre_hab: () => m.met_vidre_how(),
		kg_hab_any: () => m.met_residus_how(),
		gap_pernocta_pct: () => m.met_pernocta_how(),
		carrega_total_est: () => m.met_carrega_how(),
		index_turisme: () => m.met_turisme_how(),
		restauracio_per_1000hab: () => m.met_restauracio_how(),
		restauracio_estab: () => m.met_restauracio_how(),
		confianca: () => m.met_confianca_how(),
		IETR: () => m.met_ietr_how(),
		pct_icaen_EFG: () => m.met_efg_how(),
		pct_indep: () => m.met_indep_how(),
		pct_extrema_dreta: () => m.met_xd_how()
	};
	// Fórmula curta (codi, sense i18n: idèntica ca/es) com a darrer recurs del «com es calcula».
	const FORMULA: Partial<Record<MetricKey, string>> = {
		kwh_base_ratio: 'kwh_hab / 1224',
		residu_base_ratio: 'kg_hab_any / 410',
		vidre_base_ratio: 'vidre_hab / 26,5',
		carrega_funcional_est: 'max(L1 pernocta, L2 càrrega)'
	};

	// Blocs editorials de la metodologia (referència + títol + llista de claus, en ordre).
	interface Block {
		ref: string;
		title: () => string;
		intro?: () => string;
		keys: MetricKey[];
	}
	const blocks: Block[] = [
		{
			ref: 'A',
			title: () => m.met_block_demo(),
			keys: ['poblacio', 'hab_noprincipal', 'pct_noprincipal', 'hab_per_hab']
		},
		{
			ref: 'B',
			title: () => m.met_block_turisme(),
			keys: ['rtc_total', 'rtc_per_1000hab']
		},
		{
			ref: 'C',
			title: () => m.met_block_capes(),
			intro: () => m.met_capes_intro(),
			keys: ['kwh_hab', 'kwh_base_ratio', 'gap_pernocta_pct', 'kg_hab_any', 'residu_base_ratio', 'carrega_total_est', 'carrega_funcional_est', 'vidre_hab', 'vidre_base_ratio', 'index_turisme', 'restauracio_per_1000hab', 'restauracio_estab', 'confianca']
		},
		{
			ref: 'D',
			title: () => m.met_block_ietr(),
			keys: ['IETR']
		},
		{
			ref: 'E',
			title: () => m.met_block_energia(),
			keys: ['pct_icaen_EFG']
		},
		{
			ref: 'F',
			title: () => m.met_block_origen(),
			intro: () => m.met_origen_intro(),
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
		}
	];

	// Procedència d'una mètrica (oficial vs inferència) a partir del seu `source` (mateixa regla
	// que el mapa i el resum). Assumim que la mètrica «existeix» per a la fitxa metodològica.
	function provOf(key: MetricKey) {
		return provenanceOf(dataset.metrics[key], true);
	}
	function provLabel(key: MetricKey): string {
		return provOf(key) === 'derived' ? m.met_badge_derived() : m.met_badge_measured();
	}
	// Font · data del contracte (cap font codificada a mà).
	function srcLine(key: MetricKey): string {
		const def = dataset.metrics[key];
		return def.date ? `${def.source} · ${def.date}` : def.source;
	}
	// Algunes mètriques del catàleg poden estar marcades `planned` (definides, encara no calculades).
	function isPlanned(key: MetricKey): boolean {
		return dataset.metrics[key]?.status === 'planned';
	}

	const heroSummits = [
		{ cx: 880, cy: 145, r0: 16, step: 23, rings: 10, sq: 0.96, seed: 0.8, lt: 0.03 },
		{ cx: 1080, cy: 300, r0: 14, step: 21, rings: 9, sq: 1.05, seed: 2.6, lt: 0.1 }
	];
	const heroDivis = { cx: 765, cy: 228, r: 150, sq: 1.18, seed: 1.2 };
	// Cotes del hero: 3 capes + senyals físics (no xifres de cap municipi; són rètols del mètode).
	const heroLabels = ['L1 · pernocta', 'L2 · càrrega', 'L3 · turisme', '410', '1.224', '26,5', 'kg·kWh'];
</script>

<svelte:head>
	<title>{m.met_title()} · {m.app_name()}</title>
	<meta name="description" content={m.met_meta_desc()} />
</svelte:head>

<section data-view="metodologia" class="on">
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
				<span>{m.met_eyebrow_a()}</span><span class="sep">/</span><span>{m.met_eyebrow_b()}</span>
			</p>
			<h1>{m.met_h1_a()} <span class="q">{m.met_h1_b()}</span>.</h1>
			<p class="lede">{m.met_lede()}</p>
				<p class="tesi" style="margin:16px 0 0; padding-left:14px; border-left:3px solid var(--dp-brand, var(--dp-border-strong)); font-size:18px; line-height:1.5; color:var(--dp-text); max-width:56ch; font-weight:500;">{m.narrativa_mare()}</p>
			<div class="met-key">
				<span class="prov prov--measured"><span class="dot"></span>{m.met_badge_measured()}</span>
				<span class="prov prov--derived"><span class="dot"></span>{m.met_badge_derived()}</span>
			</div>
		</div>
	</div>

	<div class="ds-main">
		{#each blocks as block (block.ref)}
			<section class="ds-sec" class:first={block.ref === 'A'}>
				<div class="ds-sec__hd">
					<span class="ref">{block.ref}</span><h2>{block.title()}</h2>
				</div>
				{#if block.intro}
					<p class="lead">{block.intro()}</p>
				{/if}
				<div class="met-grid">
					{#each block.keys as key (key)}
						{@const def = dataset.metrics[key]}
						<article class="met-card prov-edge--{provOf(key)}">
							<header class="met-card__hd">
								<h3>{pick(def.label, locale)}</h3>
								<span class="prov prov--{provOf(key)} met-card__badge">
									<span class="dot"></span>{provLabel(key)}
								</span>
							</header>
							{#if isPlanned(key)}
								<p class="met-card__planned">{m.met_planned()}</p>
							{/if}
							<dl class="met-card__body">
								<dt>{m.met_lbl_what()}</dt>
								<dd>{WHAT[key]?.() ?? (def.definicio ? pick(def.definicio, locale) : pick(def.label, locale))}</dd>
								<dt>{m.met_lbl_how()}</dt>
								<dd class="met-card__how">{HOW[key]?.() ?? FORMULA[key] ?? '—'}</dd>
								<dt>{m.met_lbl_src()}</dt>
								<dd class="met-card__src">{srcLine(key)}</dd>
							</dl>
						</article>
					{/each}
				</div>
			</section>
		{/each}

		{#if model}
			<section class="ds-sec">
				<div class="ds-sec__hd">
					<span class="ref">G</span><h2>{m.met_model_title()}</h2>
				</div>
				<p class="lead">{m.met_model_intro()}</p>
				<MetodologiaModel {model} />
			</section>
		{/if}

		{#if etca?.pernocta_vs_etca}
			{@const s = etca.pernocta_vs_etca}
			<section class="ds-sec">
				<div class="ds-sec__hd">
					<span class="ref">H</span><h2>{m.met_block_validacio()}</h2>
				</div>
				<p class="lead">{m.met_validacio_intro()}</p>
				<div class="val-headline" class:val-headline--ok={s.passa}>
					<span class="val-headline__metric"
						>{m.met_val_rho()} <b>{dec(s.spearman)}</b></span
					>
					<span class="val-headline__metric"
						>{m.met_val_err()} <b>{dec(s.error_median_pct)}%</b></span
					>
					<span class="val-headline__verdict"
						>{s.passa ? m.met_val_passa() : m.met_val_nopassa()}</span
					>
				</div>
				<p class="val-llindar">
					{m.met_val_llindar()} ρ ≥ {dec(etca.go_no_go.rho_min)} · {m.met_val_err()} ≤ {etca.go_no_go.error_max_pct}%
				</p>
				<div class="val-table-wrap">
					<table class="val-table">
						<thead>
							<tr>
								<th scope="col">{m.tbl_municipi()}</th>
								<th scope="col">{m.met_val_th_padro()}</th>
								<th scope="col">{m.met_val_th_etca()}</th>
								<th scope="col">{m.met_val_th_nostra()}</th>
								<th scope="col">{m.met_val_th_error()}</th>
							</tr>
						</thead>
						<tbody>
							{#each etca.municipis.filter((x) => x.covered) as r (r.ine5)}
								<tr>
									<th scope="row">{r.municipi}</th>
									<td>{intf(r.padro)}</td>
									<td>{intf(r.etca)}</td>
									<td>{intf(r.pernocta_est)}</td>
									<td class="val-err">{sgn(r.err_pernocta_pct)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				<p class="val-nota">{m.met_validacio_nota()}</p>
				<p class="met-card__src val-font">
					{m.met_validacio_font({ base: etca.base ?? '', any: etca.any ?? '' })}
				</p>
			</section>
		{/if}

		<!-- Nivell C · presència estimada a Catalunya, EN RANG (escala més enllà del Berguedà). -->
		<section class="ds-sec">
			<div class="ds-sec__hd">
				<span class="ref">I</span><h2>{m.met_rang_title()}</h2>
			</div>
			<p class="lead">{m.met_rang_1()}</p>
			<p class="lead">{m.met_rang_2()}</p>
			<p class="lead">{m.met_rang_3()}</p>
			<div class="caveats">
				<div class="alert"><span class="bar"></span><div>{m.met_rang_caveat()}</div></div>
			</div>
		</section>

		<section class="ds-sec">
			<div class="ds-sec__hd">
				<span class="ref">★</span><h2>{m.met_honesty_title()}</h2>
			</div>
			<div class="caveats">
				<div class="alert"><span class="bar"></span><div>{m.met_honesty_1()}</div></div>
				<div class="alert warn"><span class="bar"></span><div>{m.met_honesty_2()}</div></div>
			</div>
			<p class="srcline">{m.met_srcline()}</p>
		</section>
	</div>
</section>

<style>
	/* La pell de chrome ve del design-system (.ap-hero, .ds-main, .ds-sec, .prov, .alert…).
	   Aquí només la graella de fitxes de metodologia i els seus detalls propis. */
	.met-key {
		display: flex;
		gap: 18px;
		flex-wrap: wrap;
		margin: 18px 0 0;
	}
	.met-key .prov {
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
	}

	/* La primera secció no duu la vora superior (ja la separa el hero). */
	.ds-sec.first {
		border-top: none;
	}

	.met-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 16px;
		margin-top: 6px;
	}

	.met-card {
		background: var(--dp-surface);
		border: 1px solid var(--dp-border);
		border-left: 3px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-lg);
		padding: 16px 18px 18px;
	}
	/* La vora esquerra codifica la procedència: slate=oficial, porpra=inferència, gris=sense dada. */
	.met-card.prov-edge--measured {
		border-left-color: var(--dp-prov-measured);
	}
	.met-card.prov-edge--derived {
		border-left-color: var(--dp-prov-derived);
	}
	.met-card.prov-edge--negative {
		border-left-color: var(--dp-prov-negative);
	}

	.met-card__hd {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 10px;
		flex-wrap: wrap;
		margin-bottom: 10px;
	}
	.met-card__hd h3 {
		margin: 0;
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 1.04rem;
		line-height: 1.2;
		color: var(--dp-text);
	}
	.met-card__badge {
		font-family: var(--dp-font-mono);
		font-size: 0.58rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		white-space: nowrap;
	}
	.met-card__planned {
		margin: 0 0 8px;
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-warning, #b5612a);
	}

	.met-card__body {
		margin: 0;
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 4px 12px;
		align-items: baseline;
	}
	.met-card__body dt {
		font-family: var(--dp-font-mono);
		font-size: 0.56rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
		padding-top: 3px;
	}
	.met-card__body dd {
		margin: 0;
		font-size: 0.86rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
	}
	.met-card__how {
		font-family: var(--dp-font-mono);
		font-size: 0.74rem;
		color: var(--dp-text);
		background: var(--dp-surface-2, color-mix(in srgb, var(--dp-text) 5%, transparent));
		border-radius: var(--dp-radius-sm);
		padding: 3px 7px;
	}
	.met-card__src {
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		color: var(--dp-text-subtle);
		line-height: 1.45;
	}

	/* ——— Validació externa ETCA (Pas 4) ——— */
	.val-headline {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 10px 22px;
		margin: 10px 0 4px;
		padding: 12px 16px;
		border: 1px solid var(--dp-border);
		border-left: 3px solid var(--dp-prov-derived, var(--dp-border-strong));
		border-radius: var(--dp-radius-lg);
		background: var(--dp-surface);
	}
	.val-headline--ok {
		border-left-color: var(--dp-forest, #2f6b4f);
	}
	.val-headline__metric {
		font-size: 0.82rem;
		color: var(--dp-text-muted);
	}
	.val-headline__metric b {
		font-family: var(--dp-font-mono);
		font-size: 1.05rem;
		color: var(--dp-text);
	}
	.val-headline__verdict {
		margin-left: auto;
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 700;
		color: var(--dp-forest, #2f6b4f);
	}
	.val-llindar {
		margin: 0 0 12px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		color: var(--dp-text-subtle);
	}
	.val-table-wrap {
		overflow-x: auto;
	}
	.val-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.84rem;
		font-variant-numeric: tabular-nums;
	}
	.val-table th,
	.val-table td {
		text-align: right;
		padding: 6px 10px;
		border-bottom: 1px solid var(--dp-border);
	}
	.val-table thead th {
		color: var(--dp-text-subtle);
		font-weight: 600;
		border-bottom: 1px solid var(--dp-border-strong);
	}
	.val-table th[scope='row'] {
		text-align: left;
		font-weight: 500;
		color: var(--dp-text);
	}
	.val-table .val-err {
		color: var(--dp-text-muted);
	}
	.val-nota {
		margin: 14px 0 0;
		font-size: 0.84rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
	}
	.val-font {
		margin-top: 8px;
	}

	@media (max-width: 520px) {
		.met-card__body {
			grid-template-columns: 1fr;
			gap: 2px;
		}
		.met-card__body dt {
			padding-top: 7px;
		}
	}
</style>
