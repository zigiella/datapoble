<script lang="ts">
	/**
	 * Tooltip del mapa: nom del municipi + valor de l'indicador + PROCEDÈNCIA.
	 * La procedència fa servir la signatura `.prov` del design-system (sistema.css):
	 * cada número arrossega el seu origen (contracte editorial). "Sense dada" és explícit.
	 *
	 * Per a la família d'estimació de població (gap / presència real) afegeix, a més:
	 *  - la CONFIANÇA del municipi (alta/mitjana/baixa, clau `confianca` del contracte);
	 *  - un recordatori que és INFERÈNCIA (no cens), reforçant la procedència morada.
	 */
	import type { MetricDef, MetricKey } from '$lib/contract/types';
	import { makeMetricFormatter } from '$lib/map/classify';
	import { provenanceOf } from '$lib/map/provenance';
	import { isCategorical, tipologiaLabel, tipologiaBlurb } from '$lib/map/tipologia';
	import { formatDecimal } from '$lib/format';
	import { pick, currentLocale } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';

	interface Props {
		nom: string;
		/** Clau de la mètrica activa (per al format específic del gap i el caveat d'inferència). */
		metricKey: MetricKey;
		def: MetricDef;
		value: number | string | null;
		/** Confiança de l'estimació (clau `confianca`); només es mostra per a estimacions. */
		conf?: string | null;
		/** Confiança auditable 0-100 (`confianca_score`); complementa la bandera. */
		confScore?: number | null;
		/** Posició en píxels dins del contenidor del mapa. */
		x: number;
		y: number;
		/** Pista d'acció opcional (p. ex. «Clica per obrir la fitxa»). Buida = no es mostra. */
		hint?: string | null;
		/** Enllaç a la fitxa del municipi. Si hi és, la pista d'acció esdevé un enllaç tocable. */
		href?: string | null;
		/** Tàctil: la targeta capta el toc (pointer-events) perquè el CTA «obrir fitxa» sigui tocable. */
		touchMode?: boolean;
	}
	let {
		nom,
		metricKey,
		def,
		value,
		conf = null,
		confScore = null,
		x,
		y,
		hint = null,
		href = null,
		touchMode = false
	}: Props = $props();

	const locale = $derived(currentLocale());
	// La tipologia és CATEGÒRICA: el valor és una cadena d'arquetip → es mostra l'etiqueta HUMANA
	// (no el snake_case) i una frase curta del que vol dir. La resta de mètriques, format numèric.
	const isTipologia = $derived(isCategorical(metricKey));
	const hasVal = $derived(
		isTipologia ? typeof value === 'string' && value !== '' : typeof value === 'number' && Number.isFinite(value)
	);
	const prov = $derived(provenanceOf(def, hasVal));
	const formatted = $derived.by(() => {
		if (isTipologia) return typeof value === 'string' ? tipologiaLabel(value) : m.value_not_available();
		if (typeof value === 'number') return makeMetricFormatter(metricKey, def.format, locale)(value);
		if (typeof value === 'string') return value;
		return m.value_not_available();
	});
	/** Frase curta de l'arquetip de tipologia (només en mode tipologia). */
	const tipoBlurb = $derived(isTipologia && typeof value === 'string' ? tipologiaBlurb(value) : '');

	/**
	 * És una mètrica d'ESTIMACIÓ de les 3 capes (inferència)? En aquest cas el tooltip recorda
	 * que és inferència (no cens) i mostra la confiança del municipi. Inclou les tres capes del
	 * model v2 (pernocta/càrrega/pressió turística) i els àlies de compatibilitat.
	 */
	const ESTIMATE_KEYS = new Set<MetricKey>([
		'tipologia',
		'gap_pernocta_pct',
		'gap_pernocta',
		'poblacio_pernocta_est',
		'carrega_total_est',
		'index_turisme',
		'gap_pct',
		'gap_abs',
		'poblacio_real_est',
		'poblacio_real_rel'
	]);
	const isEstimate = $derived(ESTIMATE_KEYS.has(metricKey));
	/** Hi ha score auditable 0-100 a mostrar? Es complementa amb la bandera (no la substitueix). */
	const hasScore = $derived(typeof confScore === 'number' && Number.isFinite(confScore));
	/** Etiqueta localitzada del nivell de confiança (alta/mitjana/baixa). */
	const confLabel = $derived.by(() => {
		if (conf === 'alta') return m.map_confidence_high();
		if (conf === 'mitjana') return m.map_confidence_mid();
		if (conf === 'baixa') return m.map_confidence_low();
		return null;
	});
	const unit = $derived(pick(def.unit, locale));
	// Mostra la unitat només quan és un nom de magnitud (habitants, establiments, kg/hab/any…).
	// L'amaga per a percentatges (ja duen %), rànquings i escales d'índex ("0-100", "posició"),
	// on enganxar la "unitat" al número el faria confús (p. ex. IETR "41,00 0-100").
	const showUnit = $derived(
		hasVal &&
			(def.format === 'integer' || def.format === 'decimal' || def.format === 'ratio') &&
			!!unit &&
			unit !== '%' &&
			!/^\s*\d/.test(unit) // descarta unitats que comencen amb dígit (escales tipus "0-100")
	);
	const provLabel = $derived(
		prov === 'derived'
			? m.map_prov_derived()
			: prov === 'negative'
				? m.map_prov_nodata()
				: m.map_prov_measured()
	);
</script>

<div
	class="tip card"
	class:tip--touch={touchMode}
	style="left:{x}px; top:{y}px"
	role="tooltip"
	aria-live="polite"
>
	<div class="tip__place">{nom}</div>
	<div class="tip__metric">{pick(def.label, locale)}</div>
	{#if hasVal}
		<div class="tip__val tnum" class:tip__val--cat={isTipologia}>
			{formatted}{#if showUnit}<span class="tip__unit"> {unit}</span>{/if}
		</div>
		{#if isTipologia && tipoBlurb}
			<!-- Frase curta del que vol dir l'arquetip (la tipologia diu QUIN TIPUS de pressió). -->
			<p class="tip__blurb">{tipoBlurb}</p>
		{/if}
	{:else}
		<div class="tip__val tip__val--nodata">{m.map_tooltip_nodata()}</div>
	{/if}

	{#if isEstimate && hasVal && (confLabel || hasScore)}
		<!-- Confiança: la BANDERA (alta/mitjana/baixa) i el SCORE auditable 0-100 es mostren TOTS
		     DOS — poden divergir (Castellar: bandera «alta» però score ≈ 33 per senyals que es
		     contradiuen). Veure els dos és l'honestedat: el score és el costat fi de la tensió. -->
		<div class="tip__conf tip__conf--{conf}">
			{#if confLabel}
				<span class="tip__conf-lbl">{m.map_confidence_label()}:</span>
				<span class="tip__conf-val">{confLabel}</span>
			{/if}
			{#if hasScore}
				<span class="tip__conf-score" title={m.map_confidence_score_label()}
					>· {formatDecimal(confScore as number, locale, 0)}<span class="tip__conf-score-scale"
						>/100</span
					></span
				>
			{/if}
		</div>
	{/if}

	<div class="prov prov--{prov}">
		<span class="dot"></span>{provLabel}
	</div>

	{#if hasVal && isTipologia}
		<p class="tip__caveat">{m.map_tipologia_tooltip_caveat()}</p>
	{:else if isEstimate && hasVal}
		<p class="tip__caveat">{m.map_gap_tooltip_caveat()}</p>
	{/if}

	{#if hint}
		<!-- Pista d'acció: obre la fitxa completa. A tàctil és un ENLLAÇ tocable (la targeta
		     capta el toc); a escriptori, text (el clic al mapa ja navega). -->
		{#if href}
			<a class="tip__hint tip__hint--link" {href}>{hint}</a>
		{:else}
			<p class="tip__hint">{hint}</p>
		{/if}
	{/if}
</div>

<style>
	.tip {
		position: absolute;
		z-index: 20;
		pointer-events: none;
		transform: translate(-50%, calc(-100% - 14px));
		min-width: 160px;
		max-width: 240px;
		padding: 10px 12px;
		box-shadow: var(--dp-shadow-md);
		/* El tooltip ha de SEGUIR EL TEMA: clar en clar, fosc en fosc. `.tip` de sistema.css
		   és un mock fosc fix (--dp-neutral-900); aquí restaurem els àlies de superfície perquè
		   en [data-theme=light] surti clar. El selector scoped de Svelte hi guanya en especificitat. */
		background: var(--dp-surface);
		color: var(--dp-text);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-md);
	}
	/* Neutralitza la fletxa ::after del `.tip` mock de sistema.css (heretava el fons fosc i
	   quedava fora de lloc amb el nostre posicionament propi del tooltip). */
	.tip::after {
		display: none;
	}
	.tip__place {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 0.95rem;
		color: var(--dp-text);
		line-height: 1.15;
	}
	.tip__metric {
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
		margin-top: 3px;
	}
	.tip__val {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 1.4rem;
		color: var(--dp-text);
		line-height: 1.1;
		margin: 2px 0 6px;
	}
	.tip__unit {
		font-family: var(--dp-font-sans);
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--dp-text-subtle);
	}
	.tip__val--nodata {
		font-family: var(--dp-font-sans);
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--dp-text-muted);
	}
	/* Tipologia: el «valor» és una etiqueta humana (text), no un número gran. Mida menor i
	   interlletratge normal perquè un nom llarg («Poble de segona residència») respiri. */
	.tip__val--cat {
		font-family: var(--dp-font-display);
		font-size: 1.06rem;
		line-height: 1.18;
		margin-bottom: 3px;
	}
	.tip__blurb {
		margin: 0 0 7px;
		font-family: var(--dp-font-sans);
		font-size: 0.72rem;
		line-height: 1.35;
		color: var(--dp-text-muted);
	}
	/* Score auditable 0-100 al costat de la bandera de confiança. */
	.tip__conf-score {
		font-weight: 700;
		color: var(--dp-text);
	}
	.tip__conf-score-scale {
		font-weight: 500;
		color: var(--dp-text-subtle);
	}
	.tip__conf {
		display: flex;
		align-items: baseline;
		gap: 5px;
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		margin: 0 0 6px;
	}
	.tip__conf-lbl {
		color: var(--dp-text-subtle);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.tip__conf-val {
		font-weight: 700;
		color: var(--dp-text);
	}
	/* La confiança baixa es marca en càlid d'avís perquè es llegeixi com a senyal feble. */
	.tip__conf--baixa .tip__conf-val {
		color: var(--dp-warning, #b5612a);
	}
	.tip__conf--alta .tip__conf-val {
		color: var(--dp-success, #2f6b4f);
	}
	.tip__caveat {
		margin: 7px 0 0;
		padding-top: 6px;
		border-top: 1px solid var(--dp-border);
		font-family: var(--dp-font-mono);
		font-size: 0.56rem;
		line-height: 1.4;
		color: var(--dp-text-subtle);
		max-width: 220px;
	}
	/* Pista d'acció (clicable): to de marca, discreta, sota tot. */
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
	/* Mode tàctil: la targeta capta el toc (per defecte és pointer-events:none, hover d'escriptori). */
	.tip--touch {
		pointer-events: auto;
	}
	/* CTA tocable: el «obrir fitxa» com a enllaç de bloc, àrea de toc còmoda. */
	.tip__hint--link {
		display: block;
		text-decoration: none;
		cursor: pointer;
	}
	.tip--touch .tip__hint--link {
		margin-top: 9px;
		padding: 8px 0 2px;
	}
</style>
