<script lang="ts">
	/**
	 * «Pregunta-li» (`/preguntale` · `/es/preguntale`) — LA CARA PÚBLICA DE LA IA.
	 *
	 * Canvi de pilar respecte de la resta del web: aquí no pintem marts precalculats sinó
	 * que consultem la Brúixola (IA de riusdegent) EN VIU: text en llenguatge natural → SQL
	 * TRAÇABLE. La gràcia del projecte és que cap resposta arriba sense origen, i que el «no»
	 * honest (refús) és una FEATURE, no un error.
	 *
	 * Com que el web és estàtic (adapter-static, sense servidor), la crida a `/ask` és
	 * CLIENT-SIDE (fetch des del navegador, vegeu `$lib/ask/api`), a una URL pública
	 * configurable (`PUBLIC_API_BASE`). El build i el prerender han de funcionar SENSE l'API
	 * viva: si no respon (Render dormint, CORS, sense connexió), mostrem un avís amable, mai
	 * una pantalla trencada.
	 *
	 * Estructura visual = chrome del design-system (hero .ap-hero + .ds-main/.ds-sec, tokens
	 * --dp-*), com el glossari/metodologia. El copi nou és tot i18n ca/es. Accessibilitat:
	 * label a l'input, region aria-live per a la resposta, estats de càrrega anunciats.
	 */
	import ContourField from '$lib/components/ContourField.svelte';
	import { currentLocale } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import { ask, type AskOutcome, type AskResponse, type RefusalReason } from '$lib/ask/api';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const locale = $derived(currentLocale());

	// ── Estat de la consulta ───────────────────────────────────────────────────
	// 'idle' abans de res · 'loading' mentre esperem · 'answer'/'refusal' segons el
	// cos de l'API · 'rate_limited' (HTTP 429) · 'unreachable' (xarxa/servei caigut).
	type View =
		| { kind: 'idle' }
		| { kind: 'loading' }
		| { kind: 'answer'; res: AskResponse }
		| { kind: 'refusal'; reason: RefusalReason | null; res: AskResponse | null }
		| { kind: 'rate_limited'; retryAfter: number | null }
		| { kind: 'unreachable' };

	let question = $state('');
	let view = $state<View>({ kind: 'idle' });
	let pending: AbortController | null = null;

	const isLoading = $derived(view.kind === 'loading');
	const canSubmit = $derived(question.trim().length > 0 && !isLoading);

	// ── Xips d'exemple ──────────────────────────────────────────────────────────
	// Preferim construir-los del contracte (les etiquetes reals d'indicador que el
	// loader llegeix del dataset, equivalent al /metrics de l'API). Sempre hi ha, a
	// més, un conjunt canònic de reserva coherent amb les dades (població, IETR, gap,
	// residus) perquè la pàgina mai es quedi sense exemples encara que falti el dataset.
	const cannedExamples = $derived([
		m.pl_ex_poblacio(),
		m.pl_ex_ietr(),
		m.pl_ex_gap(),
		m.pl_ex_residus()
	]);
	const metricExamples = $derived(
		(data.metricLabels ?? []).map((mtc) => m.pl_ex_metric_tpl({ label: mtc.label[locale] }))
	);
	// Mostrem com a màxim 4 xips: si tenim etiquetes del contracte, en prenem un parell
	// i completem amb canònics; si no, només canònics.
	const examples = $derived(
		(metricExamples.length
			? [...metricExamples.slice(0, 2), ...cannedExamples]
			: cannedExamples
		).slice(0, 4)
	);

	// ── Etiquetes derivades ─────────────────────────────────────────────────────
	function backendLabel(b: AskResponse['backend']): string {
		return b === 'openrouter' ? m.pl_backend_openrouter() : m.pl_backend_offline();
	}
	function refusalMessage(reason: RefusalReason | null): string {
		switch (reason) {
			case 'out_of_catalog':
				return m.pl_refusal_out_of_catalog();
			case 'metric_planned':
				return m.pl_refusal_metric_planned();
			case 'unknown_municipality':
				return m.pl_refusal_unknown_municipality();
			case 'unsupported_question':
				return m.pl_refusal_unsupported_question();
			case 'guardrail_violation':
				return m.pl_refusal_guardrail_violation();
			case 'budget_exceeded':
				return m.pl_refusal_budget_exceeded();
			case 'rate_limited':
				return m.pl_refusal_rate_limited();
			default:
				return m.pl_refusal_generic();
		}
	}

	// Mapeja el resultat normalitzat de l'API a l'estat de vista.
	function applyOutcome(outcome: AskOutcome): void {
		if (outcome.kind === 'unreachable') {
			view = { kind: 'unreachable' };
			return;
		}
		if (outcome.kind === 'rate_limited') {
			view = { kind: 'rate_limited', retryAfter: outcome.retryAfter };
			return;
		}
		const res = outcome.response;
		if (res.kind === 'refusal') {
			view = { kind: 'refusal', reason: res.refusal_reason, res };
		} else {
			view = { kind: 'answer', res };
		}
	}

	async function submit(): Promise<void> {
		const q = question.trim();
		if (!q || isLoading) return;
		// Cancel·la una petició anterior encara en vol (l'usuari ha tornat a preguntar).
		pending?.abort();
		pending = new AbortController();
		view = { kind: 'loading' };
		try {
			const outcome = await ask(q, locale, pending.signal);
			applyOutcome(outcome);
		} catch (e) {
			// AbortError d'una petició substituïda: ignora (ja hi ha una de nova en marxa).
			if (e instanceof DOMException && e.name === 'AbortError') return;
			view = { kind: 'unreachable' };
		}
	}

	function onSubmit(event: SubmitEvent): void {
		event.preventDefault();
		void submit();
	}

	function useExample(ex: string): void {
		question = ex;
		void submit();
	}

	// Files de la taula opcional de dades crues: capem a 8 per no inundar la UI.
	const MAX_ROWS = 8;
	function rowColumns(rows: Record<string, unknown>[]): string[] {
		return rows.length ? Object.keys(rows[0]) : [];
	}
	function cell(value: unknown): string {
		if (value === null || value === undefined) return '—';
		if (typeof value === 'object') return JSON.stringify(value);
		return String(value);
	}

	// Hero decoratiu (mateix motiu topogràfic que la resta de pàgines).
	const heroSummits = [
		{ cx: 905, cy: 150, r0: 15, step: 22, rings: 10, sq: 0.98, seed: 1.4, lt: 0.05 },
		{ cx: 1070, cy: 300, r0: 13, step: 20, rings: 8, sq: 1.05, seed: 2.7, lt: 0.1 }
	];
	const heroDivis = { cx: 770, cy: 235, r: 150, sq: 1.14, seed: 0.9 };
	const heroLabels = ['text', 'SQL', 'font', 'procedència', 'ca/es'];
</script>

<svelte:head>
	<title>{m.pl_title()} · {m.app_name()}</title>
	<meta name="description" content={m.pl_meta_desc()} />
</svelte:head>

<section data-view="preguntale" class="on">
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
				<span>{m.pl_eyebrow_a()}</span><span class="sep">/</span><span>{m.pl_eyebrow_b()}</span>
			</p>
			<h1>{m.pl_h1_a()} <span class="q">{m.pl_h1_b()}</span>.</h1>
			<p class="lede">{m.pl_lede()}</p>
		</div>
	</div>

	<div class="ds-main">
		<!-- ── Formulari de pregunta ─────────────────────────────────────────── -->
		<section class="ds-sec first">
			<form class="pl-form" onsubmit={onSubmit}>
				<label class="pl-form__label" for="pl-q">{m.pl_input_label()}</label>
				<div class="pl-form__row">
					<input
						id="pl-q"
						class="pl-input"
						type="text"
						name="question"
						autocomplete="off"
						bind:value={question}
						placeholder={m.pl_input_placeholder()}
						disabled={isLoading}
						aria-describedby="pl-hint"
					/>
					<button class="btn btn-primary pl-submit" type="submit" disabled={!canSubmit}>
						{isLoading ? m.pl_asking() : m.pl_ask()}
					</button>
				</div>
				<p id="pl-hint" class="pl-hint">{m.pl_input_hint()}</p>
			</form>

			<!-- Xips d'exemple (del contracte si n'hi ha; si no, canònics). -->
			<div class="pl-ex">
				<span class="pl-ex__lbl">{m.pl_examples_label()}</span>
				<ul class="pl-ex__list">
					{#each examples as ex (ex)}
						<li>
							<button
								type="button"
								class="pl-chip"
								onclick={() => useExample(ex)}
								disabled={isLoading}
							>
								{ex}
							</button>
						</li>
					{/each}
				</ul>
			</div>
		</section>

		<!-- ── Resultat (region viva per a lectors de pantalla) ──────────────── -->
		<section
			class="ds-sec pl-result"
			aria-live="polite"
			aria-busy={isLoading}
			class:is-empty={view.kind === 'idle'}
		>
			{#if view.kind === 'loading'}
				<p class="pl-loading">
					<span class="pl-spinner" aria-hidden="true"></span>{m.pl_loading()}
				</p>
			{:else if view.kind === 'answer'}
				{@const res = view.res}
				<div class="pl-answer">
					<div class="pl-answer__hd">
						<span class="pl-tag">{m.pl_answer_label()}</span>
						<span class="pl-backend">
							<span class="pl-backend__lbl">{m.pl_backend_lbl()}</span>{backendLabel(res.backend)}
						</span>
						{#if res.provenance?.is_fixture}
							<span class="pl-fixture" title={m.pl_fixture_note()}>{m.pl_fixture_badge()}</span>
						{/if}
					</div>

					<p class="pl-answer__text">{res.text}</p>

					{#if res.provenance}
						{@const p = res.provenance}
						<!-- PROCEDÈNCIA prominent: la traça és el cor de la proposta. -->
						<div class="pl-prov">
							<div class="pl-prov__hd">
								<span class="prov prov--derived"><span class="dot"></span>{m.pl_prov_title()}</span>
								<span class="pl-prov__intro">{m.pl_prov_intro()}</span>
							</div>

							<dl class="pl-prov__grid">
								{#if p.metric_label || p.metric}
									<div class="pl-prov__item">
										<dt>{m.pl_prov_metric()}</dt>
										<dd>{p.metric_label ?? p.metric}</dd>
									</div>
								{/if}
								{#if p.source}
									<div class="pl-prov__item">
										<dt>{m.pl_prov_source()}</dt>
										<dd>{p.source}{p.source_key ? ` · ${p.source_key}` : ''}</dd>
									</div>
								{/if}
								{#if p.date}
									<div class="pl-prov__item">
										<dt>{m.pl_prov_date()}</dt>
										<dd>{p.date}</dd>
									</div>
								{/if}
								{#if p.license}
									<div class="pl-prov__item">
										<dt>{m.pl_prov_license()}</dt>
										<dd>{p.license}</dd>
									</div>
								{/if}
								{#if p.formula}
									<div class="pl-prov__item pl-prov__item--wide">
										<dt>{m.pl_prov_formula()}</dt>
										<dd class="mono">{p.formula}</dd>
									</div>
								{/if}
							</dl>

							{#if p.query}
								<!-- La consulta SQL EXACTA, en mono: la signatura de confiança. -->
								<div class="pl-query">
									<div class="pl-query__hd">
										<span class="pl-query__lbl">{m.pl_prov_query()}</span>
										<span class="pl-query__hint">{m.pl_prov_query_hint()}</span>
									</div>
									<pre class="pl-query__code"><code>{p.query}</code></pre>
									{#if p.params && Object.keys(p.params).length}
										<p class="pl-query__params">
											<span class="pl-meta-lbl">{m.pl_prov_params()}</span>
											<span class="mono">{JSON.stringify(p.params)}</span>
										</p>
									{/if}
								</div>
							{/if}

							{#if p.note}
								<p class="pl-prov__note">
									<span class="pl-meta-lbl">{m.pl_prov_note()}</span>{p.note}
								</p>
							{/if}
							{#if p.is_fixture}
								<p class="pl-prov__fixture-note">{m.pl_fixture_note()}</p>
							{/if}
						</div>
					{/if}

					<!-- Taula opcional de dades crues darrere la resposta. -->
					{#if res.data && res.data.length}
						{@const cols = rowColumns(res.data)}
						<details class="pl-data">
							<summary>
								<span class="pl-data__title">{m.pl_data_title()}</span>
								<span class="pl-data__count">{m.pl_data_rows({ n: res.data.length })}</span>
							</summary>
							{#if cols.length}
								<div class="tbl-wrap pl-data__wrap">
									<table class="tbl">
										<thead>
											<tr>{#each cols as c (c)}<th>{c}</th>{/each}</tr>
										</thead>
										<tbody>
											{#each res.data.slice(0, MAX_ROWS) as row, i (i)}
												<tr>{#each cols as c (c)}<td class="num">{cell(row[c])}</td>{/each}</tr>
											{/each}
										</tbody>
									</table>
								</div>
								{#if res.data.length > MAX_ROWS}
									<p class="pl-data__more">{m.pl_data_more({ n: res.data.length - MAX_ROWS })}</p>
								{/if}
							{/if}
						</details>
					{/if}
				</div>
			{:else if view.kind === 'refusal' || view.kind === 'rate_limited'}
				{@const reason = view.kind === 'rate_limited' ? 'rate_limited' : view.reason}
				{@const retry = view.kind === 'rate_limited' ? view.retryAfter : null}
				<!-- Refús com a FEATURE d'honestedat: missatge amable segons el motiu. -->
				<div class="pl-refusal">
					<div class="pl-refusal__hd">
						<span class="prov prov--negative"><span class="dot"></span>{m.pl_refusal_title()}</span>
					</div>
					<p class="pl-refusal__lede">{m.pl_refusal_intro()}</p>
					<p class="pl-refusal__msg">
						{#if reason === 'rate_limited' && retry}
							{m.pl_refusal_rate_limited_wait({ seconds: retry })}
						{:else}
							{refusalMessage(reason)}
						{/if}
					</p>
					{#if view.kind === 'refusal' && view.res?.text}
						<p class="pl-refusal__detail">{view.res.text}</p>
					{/if}
				</div>
			{:else if view.kind === 'unreachable'}
				<!-- API no disponible: avís amable, mai una pantalla trencada. -->
				<div class="pl-offline">
					<h2 class="pl-offline__h">{m.pl_unreachable_title()}</h2>
					<p class="pl-offline__body">{m.pl_unreachable_body()}</p>
					<button type="button" class="btn btn-outline btn-sm" onclick={() => void submit()}>
						{m.pl_unreachable_retry()}
					</button>
				</div>
			{/if}
		</section>

		<section class="ds-sec">
			<p class="srcline">{m.pl_srcline()}</p>
		</section>
	</div>
</section>

<style>
	/* El chrome (.ap-hero, .ds-main, .ds-sec, .prov, .srcline, .btn, .tbl…) ve del
	   design-system. Aquí només el formulari de pregunta i la presentació de la
	   resposta/procedència/refús (propis d'aquesta pàgina). */

	.ds-sec.first {
		border-top: none;
	}

	/* ── Formulari ───────────────────────────────────────────────────────────── */
	.pl-form {
		margin: 0;
	}
	.pl-form__label {
		display: block;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--dp-text-subtle);
		margin: 0 0 8px;
	}
	.pl-form__row {
		display: flex;
		gap: 10px;
		align-items: stretch;
		flex-wrap: wrap;
	}
	.pl-input {
		flex: 1 1 280px;
		min-width: 0;
		font-family: var(--dp-font-sans);
		font-size: 1rem;
		color: var(--dp-text);
		background: var(--dp-surface);
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-lg);
		padding: 13px 16px;
		line-height: 1.3;
	}
	.pl-input::placeholder {
		color: var(--dp-text-subtle);
	}
	.pl-input:focus-visible {
		outline: 2px solid var(--dp-link);
		outline-offset: 1px;
		border-color: var(--dp-link);
	}
	.pl-input:disabled {
		opacity: 0.6;
	}
	.pl-submit {
		flex: 0 0 auto;
		padding-inline: 22px;
	}
	.pl-hint {
		margin: 9px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		line-height: 1.5;
		color: var(--dp-text-subtle);
	}

	/* ── Xips d'exemple ──────────────────────────────────────────────────────── */
	.pl-ex {
		margin: 20px 0 0;
	}
	.pl-ex__lbl {
		display: block;
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--dp-text-subtle);
		margin: 0 0 9px;
	}
	.pl-ex__list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}
	.pl-chip {
		font-family: var(--dp-font-sans);
		font-size: 0.84rem;
		line-height: 1.2;
		color: var(--dp-text-muted);
		background: var(--dp-surface);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-full);
		padding: 7px 14px;
		cursor: pointer;
		transition:
			background var(--dp-dur-fast, 0.15s) var(--dp-ease-out, ease),
			color var(--dp-dur-fast, 0.15s) var(--dp-ease-out, ease),
			border-color var(--dp-dur-fast, 0.15s) var(--dp-ease-out, ease);
	}
	.pl-chip:hover:not(:disabled) {
		background: var(--dp-accent-weak);
		color: var(--dp-text);
		border-color: var(--dp-border-strong);
	}
	.pl-chip:focus-visible {
		outline: 2px solid var(--dp-link);
		outline-offset: 2px;
	}
	.pl-chip:disabled {
		opacity: 0.5;
		cursor: default;
	}

	/* ── Region de resultat ──────────────────────────────────────────────────── */
	.pl-result.is-empty {
		display: none;
	}
	.pl-loading {
		display: flex;
		align-items: center;
		gap: 11px;
		font-family: var(--dp-font-mono);
		font-size: 0.8rem;
		color: var(--dp-text-muted);
		margin: 0;
	}
	.pl-spinner {
		width: 15px;
		height: 15px;
		border: 2px solid var(--dp-border-strong);
		border-top-color: var(--dp-accent-600);
		border-radius: 50%;
		animation: pl-spin 0.7s linear infinite;
	}
	@keyframes pl-spin {
		to {
			transform: rotate(360deg);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.pl-spinner {
			animation-duration: 1.4s;
		}
	}

	/* ── Resposta ────────────────────────────────────────────────────────────── */
	.pl-answer__hd {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-wrap: wrap;
		margin: 0 0 12px;
	}
	.pl-tag {
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--dp-accent-600);
		font-weight: 600;
	}
	[data-theme='dark'] .pl-tag {
		color: var(--dp-accent-300);
	}
	.pl-backend {
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		color: var(--dp-text-subtle);
	}
	.pl-backend__lbl {
		text-transform: uppercase;
		letter-spacing: 0.06em;
		margin-right: 7px;
		opacity: 0.85;
	}
	.pl-fixture {
		font-family: var(--dp-font-mono);
		font-size: 0.56rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--dp-brand-ink, var(--dp-brand));
		background: color-mix(in srgb, var(--dp-brand) 14%, transparent);
		border-radius: var(--dp-radius-full);
		padding: 3px 10px;
		cursor: help;
	}
	.pl-answer__text {
		font-size: 1.18rem;
		line-height: 1.55;
		color: var(--dp-text);
		margin: 0 0 22px;
		text-wrap: pretty;
	}

	/* ── Procedència (bloc prominent) ────────────────────────────────────────── */
	.pl-prov {
		background: var(--dp-surface);
		border: 1px solid var(--dp-border);
		border-left: 3px solid var(--dp-prov-derived);
		border-radius: var(--dp-radius-lg);
		padding: 18px 20px 20px;
	}
	.pl-prov__hd {
		display: flex;
		align-items: baseline;
		gap: 12px;
		flex-wrap: wrap;
		margin: 0 0 14px;
	}
	.pl-prov__intro {
		font-size: 0.84rem;
		color: var(--dp-text-muted);
	}
	.pl-prov__grid {
		margin: 0 0 14px;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 12px 18px;
	}
	.pl-prov__item--wide {
		grid-column: 1 / -1;
	}
	.pl-prov__item dt {
		font-family: var(--dp-font-mono);
		font-size: 0.56rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--dp-text-subtle);
		margin: 0 0 3px;
	}
	.pl-prov__item dd {
		margin: 0;
		font-size: 0.9rem;
		line-height: 1.45;
		color: var(--dp-text);
	}
	.pl-prov__item dd.mono {
		font-family: var(--dp-font-mono);
		font-size: 0.82rem;
		color: var(--dp-text-muted);
	}

	/* La consulta SQL: el moment de la veritat. Es mostra sencera, monoespaiada. */
	.pl-query {
		margin: 0;
	}
	.pl-query__hd {
		display: flex;
		align-items: baseline;
		gap: 10px;
		flex-wrap: wrap;
		margin: 0 0 7px;
	}
	.pl-query__lbl {
		font-family: var(--dp-font-mono);
		font-size: 0.58rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--dp-prov-derived);
		font-weight: 600;
	}
	.pl-query__hint {
		font-size: 0.74rem;
		color: var(--dp-text-subtle);
	}
	.pl-query__code {
		margin: 0;
		background: var(--dp-bg-subtle);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-sm);
		padding: 13px 15px;
		overflow-x: auto;
		font-family: var(--dp-font-mono);
		font-size: 0.82rem;
		line-height: 1.6;
		color: var(--dp-text);
		white-space: pre;
		tab-size: 2;
	}
	.pl-query__code code {
		font-family: inherit;
	}
	.pl-query__params {
		margin: 9px 0 0;
		font-size: 0.72rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
		word-break: break-word;
	}
	.pl-query__params .mono {
		font-family: var(--dp-font-mono);
		color: var(--dp-text-subtle);
	}

	.pl-meta-lbl {
		display: inline-block;
		margin-right: 8px;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		font-size: 0.56rem;
		color: var(--dp-text-subtle);
	}
	.pl-prov__note {
		margin: 14px 0 0;
		padding-top: 12px;
		border-top: 1px dashed var(--dp-border);
		font-size: 0.84rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
	}
	.pl-prov__note .pl-meta-lbl {
		color: var(--dp-prov-derived);
	}
	.pl-prov__fixture-note {
		margin: 11px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
		line-height: 1.5;
		color: var(--dp-brand-ink, var(--dp-brand));
	}

	/* ── Taula opcional de dades crues ───────────────────────────────────────── */
	.pl-data {
		margin: 16px 0 0;
	}
	.pl-data summary {
		cursor: pointer;
		display: inline-flex;
		align-items: baseline;
		gap: 10px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		letter-spacing: 0.06em;
		color: var(--dp-text-muted);
	}
	.pl-data summary:hover {
		color: var(--dp-text);
	}
	.pl-data__title {
		text-transform: uppercase;
	}
	.pl-data__count {
		color: var(--dp-text-subtle);
	}
	.pl-data__wrap {
		margin: 12px 0 0;
		overflow-x: auto;
	}
	.pl-data__more {
		margin: 8px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		color: var(--dp-text-subtle);
	}

	/* ── Refús (honest) ──────────────────────────────────────────────────────── */
	.pl-refusal {
		background: var(--dp-surface);
		border: 1px solid var(--dp-border);
		border-left: 3px solid var(--dp-prov-negative, var(--dp-brand));
		border-radius: var(--dp-radius-lg);
		padding: 18px 20px 20px;
	}
	.pl-refusal__hd {
		margin: 0 0 12px;
	}
	.pl-refusal__lede {
		margin: 0 0 10px;
		font-size: 0.86rem;
		color: var(--dp-text-subtle);
	}
	.pl-refusal__msg {
		margin: 0;
		font-size: 1.05rem;
		line-height: 1.55;
		color: var(--dp-text);
		text-wrap: pretty;
	}
	.pl-refusal__detail {
		margin: 12px 0 0;
		padding-top: 12px;
		border-top: 1px dashed var(--dp-border);
		font-size: 0.88rem;
		line-height: 1.55;
		color: var(--dp-text-muted);
	}

	/* ── API no disponible (degradació amable) ───────────────────────────────── */
	.pl-offline {
		background: var(--dp-bg-subtle);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-lg);
		padding: 24px 22px;
	}
	.pl-offline__h {
		font-family: var(--dp-font-display);
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--dp-text);
		margin: 0 0 9px;
	}
	.pl-offline__body {
		margin: 0 0 16px;
		font-size: 0.96rem;
		line-height: 1.6;
		color: var(--dp-text-muted);
		max-width: 60ch;
		text-wrap: pretty;
	}

	@media (max-width: 560px) {
		.pl-prov__grid {
			grid-template-columns: 1fr;
		}
		.pl-submit {
			flex: 1 1 100%;
		}
	}
</style>
