<script lang="ts">
	/**
	 * Pàgina de metodologia pública (`/metodologia` · `/es/metodologia`).
	 *
	 * Explica, un per un, cada indicador de l'observatori: QUÈ mesura · COM es calcula (fórmula)
	 * · FONT i data · si és dada OFICIAL 🟦 o INFERÈNCIA 🟪. El contingut surt de dues fonts:
	 *  - el dataset real (contracte) → label, DEFINICIÓ (`definicio`), FÓRMULA (`formula`),
	 *    ADVERTIMENT (`note`), unitat, font, data i procedència de cada mètrica; així cap
	 *    font/data/definició es codifica a mà: és el mateix contracte que pinta la resta del web.
	 *  - copy i18n de funcionalitat (WHAT/HOW) NOMÉS on el contracte no en diu prou (fitxes
	 *    velles i annex del model); per a la resta mana el fallback del contracte.
	 *
	 * P-DOC (2026-07-27): la COMPOSICIÓ dels blocs (refs + claus + annex) viu a
	 * `$lib/metodologia/blocs.js` (font única amb `scripts/verify-docs.mjs`). La pàgina FILTRA
	 * les claus que el dataset no serveix (avís al build, mai un 500 en render: la guarda del
	 * verificador és qui cau) i pinta el `note` del contracte com a advertiment de cada fitxa.
	 *
	 * Estètica coherent amb el lloc: hero + .ds-main/.ds-sec del design-system, Archivo als
	 * titulars, tokens --dp-*; procedència amb la signatura `.prov` (slate=oficial, porpra=inferència).
	 */
	import ContourField from '$lib/components/ContourField.svelte';
	import MetodologiaModel from '$lib/components/MetodologiaModel.svelte';
	import { currentLocale, pick } from '$lib/i18n';
	import { METODOLOGIA_BLOCS } from '$lib/metodologia/blocs.js';
	import { provenanceOf } from '$lib/map/provenance';
	import { m } from '$lib/paraglide/messages';
	import type { MetricDef, MetricKey } from '$lib/contract/types';
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
	// P-DOC: NOMÉS on el contracte no en diu prou; la resta de fitxes usen `def.definicio`
	// (fallback del render). Els indicadors de vida (kg/kwh/vidre/restauració) ja NO hi són:
	// el seu copy antic els emmarcava com a senyals L1/L2/L3 del model aparcat, i són targetes
	// vives del tauler — ara parla el contracte.
	const WHAT: Partial<Record<MetricKey, () => string>> = {
		poblacio: () => m.met_poblacio_what(),
		hab_noprincipal: () => m.met_habnop_what(),
		pct_noprincipal: () => m.met_pctnop_what(),
		hab_per_hab: () => m.met_habperhab_what(),
		rtc_total: () => m.met_rtc_what(),
		rtc_per_1000hab: () => m.met_rtcratio_what(),
		gap_pernocta_pct: () => m.met_pernocta_what(),
		carrega_total_est: () => m.met_carrega_what(),
		confianca: () => m.met_confianca_what(),
		pct_icaen_EFG: () => m.met_efg_what()
	};
	// «Com es calcula» (fórmula llegible) per clau — fidel a semantic/metrics.yml.
	const HOW: Partial<Record<MetricKey, () => string>> = {
		poblacio: () => m.met_poblacio_how(),
		hab_noprincipal: () => m.met_habnop_how(),
		pct_noprincipal: () => m.met_pctnop_how(),
		hab_per_hab: () => m.met_habperhab_how(),
		rtc_total: () => m.met_rtc_how(),
		rtc_per_1000hab: () => m.met_rtcratio_how(),
		gap_pernocta_pct: () => m.met_pernocta_how(),
		carrega_total_est: () => m.met_carrega_how(),
		confianca: () => m.met_confianca_how(),
		pct_icaen_EFG: () => m.met_efg_how()
	};
	// Fórmula curta (codi, sense i18n: idèntica ca/es) com a segon recurs del «com es calcula».
	const FORMULA: Partial<Record<MetricKey, string>> = {
		kwh_base_ratio: 'kwh_hab / 1224',
		residu_base_ratio: 'kg_hab_any / 410',
		vidre_base_ratio: 'vidre_hab / 26,5',
		carrega_funcional_est: 'max(L1 pernocta, L2 càrrega)'
	};
	// «Com es calcula», en cascada honesta (P-DOC): copy i18n → fórmula curta → la FÓRMULA DEL
	// CONTRACTE (`def.formula`, que l'export emet a 55/55). `directe` no és una fórmula sinó la
	// declaració que la xifra es LLEGEIX de la font: es diu amb paraules, no es pinta el literal.
	// El «—» queda com a darrer recurs real (contracte sense fórmula), no com a resposta habitual.
	function howLine(key: MetricKey, def: MetricDef): string {
		const own = HOW[key]?.() ?? FORMULA[key];
		if (own) return own;
		if (def.formula && def.formula !== 'directe') return def.formula;
		if (def.formula === 'directe') return m.met_how_directe();
		return '—';
	}

	// Blocs editorials de la metodologia: la COMPOSICIÓ (refs + claus + annex) viu a
	// `$lib/metodologia/blocs.js` (font única amb verify-docs.mjs); aquí només s'hi cablen
	// títol i intro i18n per `ref`. `annex`: el bloc documenta el MODEL D'ESTIMACIÓ DE
	// PERNOCTA, aparcat del web (vot de Bea 2026-07-16). NO s'esborra — la metodologia és el
	// rastre honest — però s'etiqueta com a annex de recerca.
	interface Block {
		ref: string;
		title: () => string;
		intro?: () => string;
		keys: MetricKey[];
		annex?: boolean;
	}
	const BLOC_TITLE: Record<string, () => string> = {
		A: () => m.met_block_demo(),
		B: () => m.met_block_treball(),
		C: () => m.met_block_turisme(),
		D: () => m.met_block_serveis(),
		E: () => m.met_block_vida(),
		F: () => m.met_block_energia(),
		G: () => m.met_block_origen(),
		H: () => m.met_block_capes()
	};
	const BLOC_INTRO: Partial<Record<string, () => string>> = {
		G: () => m.met_origen_intro(),
		H: () => m.met_capes_intro()
	};
	// GUARDA DEL 500 LATENT (P-DOC): abans es renderitzava `dataset.metrics[key]` sense xarxa —
	// una clau fantasma als blocs petava la pàgina amb el build verd (va passar amb
	// index_turisme). Ara les claus absents es FILTREN amb un avís al build (prerender) i és
	// `verify-docs.mjs` qui cau en local/CI; la pàgina mai.
	const blocks = $derived.by<Block[]>(() =>
		METODOLOGIA_BLOCS.map((b) => {
			const keys = (b.keys as MetricKey[]).filter((k) => {
				if (dataset.metrics[k]) return true;
				console.warn(
					`[metodologia] clau '${k}' del bloc ${b.ref} absent del dataset — fitxa omesa (verify-docs.mjs ha de caure)`
				);
				return false;
			});
			return {
				ref: b.ref,
				title: BLOC_TITLE[b.ref] ?? (() => b.ref),
				intro: BLOC_INTRO[b.ref],
				keys,
				annex: b.annex
			};
		}).filter((b) => b.keys.length > 0)
	);

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
		if (!def) return ''; // clau retirada del catàleg (mètrica deprecada) → sense font, mai un 500
		return def.date ? `${def.source} · ${def.date}` : def.source;
	}
	// Algunes mètriques del catàleg poden estar marcades `planned` (definides, encara no calculades).
	function isPlanned(key: MetricKey): boolean {
		return dataset.metrics[key]?.status === 'planned';
	}

	// ── V3 (vot de Bea 2026-07-29) · ACTUALITZACIÓ I PROCÉS DE REFRESC ─────────────────────────
	// La línia de frescor de les targetes del tauler queda «cadència · darrera càrrega»; el COM
	// la refresquem nosaltres (el procés, o la seva absència declarada) és cuina interna i viu
	// AQUÍ, a la fitxa metodològica de cada mètrica. La informació no s'esborra del sistema:
	// canvia de planta. Tot surt del bloc `frescor` del contracte; res s'escriu a mà.
	function cadenciaLabel(c: string | null): string {
		if (c === 'mensual') return m.gov_frescor_mensual();
		if (c === 'anual') return m.gov_frescor_anual();
		if (c === 'puntual') return m.gov_frescor_puntual();
		if (c === 'irregular') return m.gov_frescor_irregular();
		if (!c) return m.gov_frescor_nd();
		return c;
	}
	/** Data de càrrega ISO → DD-MM-YYYY (decisió de Bea, 2026-07-29; el contracte no es toca). */
	function dataCarrega(iso: string): string {
		const m2 = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
		return m2 ? `${m2[3]}-${m2[2]}-${m2[1]}` : iso;
	}
	/** Línia sencera: cadència · darrera càrrega · procés de refresc (o la seva absència). */
	function frescLine(key: MetricKey): string {
		const f = dataset.metrics[key]?.frescor;
		if (!f) return '';
		const parts = [cadenciaLabel(f.actualitzacio)];
		if (f.darrera_carrega) parts.push(m.gov_frescor_carrega({ data: dataCarrega(f.darrera_carrega) }));
		if (f.proces_refresc === 'cap') parts.push(m.met_fresc_sense_proces());
		else if (f.proces_refresc) parts.push(m.met_fresc_proces({ ruta: f.proces_refresc }));
		return parts.join(' · ');
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
					{#if block.annex}<span class="met-annex-badge">{m.met_annex_badge()}</span>{/if}
				</div>
				{#if block.annex}
					<p class="met-annex-note">{m.met_annex_note()}</p>
				{/if}
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
								<dd class="met-card__how">{howLine(key, def)}</dd>
								<dt>{m.met_lbl_src()}</dt>
								<dd class="met-card__src">{srcLine(key)}</dd>
								{#if frescLine(key)}
									<!-- V3: el procés de refresc (o la seva absència declarada) viu aquí, no a
									     la targeta del tauler. -->
									<dt>{m.met_lbl_fresc()}</dt>
									<dd class="met-card__src">{frescLine(key)}</dd>
								{/if}
								{#if def.note}
									<!-- P-DOC: l'ADVERTIMENT del contracte (`note` = el caveat renombrat) a la
									     fitxa — aquí viuen la doctrina del «<5» de l'atur, la barreja de
									     vintages de la penetració sobre el parc o el «MÍNIM, no cens» d'OSM. -->
									<dt>{m.glo_lbl_note()}</dt>
									<dd class="met-card__note">{pick(def.note, locale)}</dd>
								{/if}
							</dl>
						</article>
					{/each}
				</div>
			</section>
		{/each}

		{#if model}
			<section class="ds-sec">
				<div class="ds-sec__hd">
					<span class="ref">I</span><h2>{m.met_model_title()}</h2>
					<span class="met-annex-badge">{m.met_annex_badge()}</span>
				</div>
				<p class="met-annex-note">{m.met_annex_note()}</p>
				<p class="lead">{m.met_model_intro()}</p>
				<MetodologiaModel {model} />
			</section>
		{/if}

		{#if etca?.pernocta_vs_etca}
			{@const s = etca.pernocta_vs_etca}
			<section class="ds-sec">
				<div class="ds-sec__hd">
					<span class="ref">J</span><h2>{m.met_block_validacio()}</h2>
					<span class="met-annex-badge">{m.met_annex_badge()}</span>
				</div>
				<p class="met-annex-note">{m.met_annex_note()}</p>
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
				<p class="val-nucli">{m.met_val_nucli_fet({ n: etca.municipis.filter((x) => x.covered).length })}</p>
				<p class="val-llindar">
					{m.met_val_llindar()} ρ ≥ {dec(etca.go_no_go.rho_min)} · {m.met_val_err()} ≤ {etca.go_no_go.error_max_pct}%
				</p>
				<p class="lead">{m.met_valid_canon()}</p>
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
				<span class="ref">K</span><h2>{m.met_rang_title()}</h2>
				<span class="met-annex-badge">{m.met_annex_badge()}</span>
			</div>
			<p class="met-annex-note">{m.met_annex_note()}</p>
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

	/* «Model aparcat (annex de recerca)»: la pastilla que marca les seccions del model. La
	   metodologia és el rastre honest — no s'esborra, s'etiqueta. */
	.met-annex-badge {
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 700;
		color: var(--dp-warning, #b5612a);
		border: 1px solid currentColor;
		border-radius: var(--dp-radius-sm);
		padding: 2px 8px;
		white-space: nowrap;
	}
	.met-annex-note {
		margin: 6px 0 12px;
		font-size: 0.84rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
		max-width: 64ch;
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
	/* L'advertiment del contracte (`note`): mateixa veu discreta que al glossari. */
	.met-card__note {
		font-size: 0.78rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
		text-wrap: pretty;
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
	.val-nucli {
		margin: 8px 0 4px;
		font-size: 1rem;
		font-weight: 700;
		color: var(--dp-text);
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
