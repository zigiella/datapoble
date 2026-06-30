<script lang="ts">
	/**
	 * Glossari públic (`/glossari` · `/es/glossari`) — EL CONTRACTE, LLEGIBLE PER HUMANS.
	 *
	 * És el DICCIONARI de referència de l'observatori: cada indicador del contracte, definit i
	 * escanejable, AGRUPAT PER DIMENSIÓ. A diferència de la metodologia (l'assaig: com funciona
	 * l'observatori, el model de 3 capes, què es mesura vs què s'infereix), aquí cada terme es
	 * defineix de pressa, per consultar.
	 *
	 * Principi rector: ZERO codificat a mà. Terme (label), definició (definicio→note), unitat,
	 * font, data i procedència surten TOTS del dataset (= contracte semàntic, semantic/metrics.yml),
	 * el mateix que pinta la resta del web → sempre sincronitzat. L'únic copy i18n d'aquesta pàgina
	 * és el CHROME (títol, intro, etiquetes de dimensió/camp i el vocabulari de format de presentació).
	 *
	 * Nota honesta sobre la definició: l'export actual del dataset
	 * (`tools/export_web_municipis.py`, jurisdicció Sondeig) encara NO emet el camp `definicio`
	 * de metrics.yml; per això la definició recau en `note` quan no hi és. El dia que l'export
	 * l'inclogui, la definició canònica apareix sola, sense tocar aquesta pàgina (handoff a la bitàcola).
	 */
	import ContourField from '$lib/components/ContourField.svelte';
	import { currentLocale, pick } from '$lib/i18n';
	import { provenanceOf } from '$lib/map/provenance';
	import { m } from '$lib/paraglide/messages';
	import type { MetricDef, MetricFormat } from '$lib/contract/types';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const locale = $derived(currentLocale());

	// Ordre de presentació de les dimensions del contracte (les que no apareguin al dataset
	// se salten soles). Les etiquetes són chrome i18n; les CLAUS són del contracte (MetricDef.dimension).
	const DIM_ORDER = [
		'demografia',
		'vivenda',
		'turisme',
		'serveis',
		'pressio',
		'index',
		'energia'
	] as const;
	type Dim = (typeof DIM_ORDER)[number];
	const DIM_LABEL: Record<Dim, () => string> = {
		demografia: () => m.glo_dim_demografia(),
		vivenda: () => m.glo_dim_vivenda(),
		turisme: () => m.glo_dim_turisme(),
		serveis: () => m.glo_dim_serveis(),
		pressio: () => m.glo_dim_pressio(),
		index: () => m.glo_dim_index(),
		energia: () => m.glo_dim_energia()
	};

	// Vocabulari humà del `format` del contracte (presentació, com els noms de mètode del mapa;
	// NO és una definició de mètrica). Acompanya la unitat per dir QUINA MENA de valor és.
	const FMT_LABEL: Record<MetricFormat, () => string> = {
		integer: () => m.glo_fmt_integer(),
		decimal: () => m.glo_fmt_decimal(),
		percent: () => m.glo_fmt_percent(),
		ratio: () => m.glo_fmt_ratio(),
		rank: () => m.glo_fmt_rank(),
		text: () => m.glo_fmt_text()
	};

	// Agrupació dinàmica: recorre TOT el catàleg del contracte i agrupa per dimensió, en l'ordre
	// de DIM_ORDER i conservant l'ordre del contracte dins de cada grup (diffs estables). No es
	// codifica cap llista de mètriques: el que hi hagi al dataset és el que es pinta.
	interface Group {
		dim: Dim;
		label: () => string;
		entries: MetricDef[];
	}
	// Indicadors retirats del públic (no surten al diccionari): l'IETR i la seva família (retirat del
	// mapa i col·lapsat de la fitxa), el model d'una sola capa antic (duplicats confusos del gap
	// reenquadrat) i els scores interns (massa tècnics per a un diccionari). La dada segueix al
	// contracte; només no es publica aquí.
	const HIDDEN = new Set<string>([
		'IETR', 'IETR_rank', 'IETR_stock', 'IETR_impact',
		'poblacio_real_est', 'gap_abs', 'gap_pct', 'poblacio_real_rel',
		'confianca_score', 'divergencia_senyals'
	]);
	const groups = $derived.by<Group[]>(() => {
		const all = Object.values(dataset.metrics);
		const out: Group[] = [];
		for (const dim of DIM_ORDER) {
			const entries = all.filter((d) => d.dimension === dim && !HIDDEN.has(d.key));
			if (entries.length) out.push({ dim, label: DIM_LABEL[dim], entries });
		}
		return out;
	});
	// Recompte per a la línia de capçalera (tot des del dataset).
	const totalMetrics = $derived(Object.keys(dataset.metrics).length);
	const totalDims = $derived(groups.length);

	// Procedència (oficial 🟦 / inferència 🟪) per la mateixa regla que metodologia/mapa.
	function provOf(def: MetricDef) {
		return provenanceOf(def, true);
	}
	function provLabel(def: MetricDef): string {
		return provOf(def) === 'derived' ? m.met_badge_derived() : m.met_badge_measured();
	}
	// Definició: la canònica del contracte (`definicio`) si l'export l'emet; si no, el `note`
	// (l'anotació pròpia del contracte). Mai text escrit a mà aquí.
	function definition(def: MetricDef): string | null {
		if (def.definicio) return pick(def.definicio, locale);
		if (def.note) return pick(def.note, locale);
		return null;
	}
	// Caveat: només si hi ha `note` I a més ja tenim una definició pròpia (`definicio`), perquè
	// el `note` no es repeteixi com a definició i com a advertiment alhora.
	function caveat(def: MetricDef): string | null {
		if (def.definicio && def.note) return pick(def.note, locale);
		return null;
	}
	// Unitat + mena de valor (tot contracte/presentació).
	function typeLine(def: MetricDef): string {
		const unit = pick(def.unit, locale);
		const fmt = FMT_LABEL[def.format]?.() ?? def.format;
		return unit ? `${unit} · ${fmt}` : fmt;
	}
	// Font · data del contracte (cap font codificada a mà).
	function srcLine(def: MetricDef): string {
		return def.date ? `${def.source} · ${def.date}` : def.source;
	}
	function isPlanned(def: MetricDef): boolean {
		return def.status === 'planned';
	}

	// Cims del hero (rètols del diccionari, no xifres de cap municipi).
	const heroSummits = [
		{ cx: 900, cy: 150, r0: 15, step: 22, rings: 10, sq: 0.98, seed: 1.1, lt: 0.04 },
		{ cx: 1075, cy: 295, r0: 13, step: 20, rings: 8, sq: 1.06, seed: 3.1, lt: 0.1 }
	];
	const heroDivis = { cx: 760, cy: 230, r: 148, sq: 1.16, seed: 0.7 };
	const heroLabels = ['terme', 'definició', 'font', 'procedència', 'A–Z'];
</script>

<svelte:head>
	<title>{m.glo_title()} · {m.app_name()}</title>
	<meta name="description" content={m.glo_meta_desc()} />
</svelte:head>

<section data-view="glossari" class="on">
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
				<span>{m.glo_eyebrow_a()}</span><span class="sep">/</span><span>{m.glo_eyebrow_b()}</span>
			</p>
			<h1>{m.glo_h1_a()} <span class="q">{m.glo_h1_b()}</span>.</h1>
			<p class="lede">{m.glo_lede()}</p>
			<div class="glo-key">
				<span class="glo-count">{m.glo_count({ n: totalMetrics, dims: totalDims })}</span>
				<span class="prov prov--measured"><span class="dot"></span>{m.met_badge_measured()}</span>
				<span class="prov prov--derived"><span class="dot"></span>{m.met_badge_derived()}</span>
			</div>
		</div>
	</div>

	<div class="ds-main">
		<section class="ds-sec first">
			<p class="lead glo-distinct">{m.glo_intro_note()}</p>
		</section>

		{#each groups as group (group.dim)}
			<section class="ds-sec">
				<div class="ds-sec__hd">
					<span class="ref">{group.entries.length}</span><h2>{group.label()}</h2>
				</div>
				<dl class="glo-list">
					{#each group.entries as def (def.key)}
						{@const defn = definition(def)}
						{@const cav = caveat(def)}
						<div class="glo-term prov-edge--{provOf(def)}" class:planned={isPlanned(def)}>
							<dt class="glo-term__hd">
								<span class="glo-term__name">{pick(def.label, locale)}</span>
								<span class="prov prov--{provOf(def)} glo-term__prov">
									<span class="dot"></span>{provLabel(def)}
								</span>
							</dt>
							<dd class="glo-term__body">
								{#if isPlanned(def)}
									<p class="glo-term__planned">{m.glo_planned()}</p>
								{/if}
								{#if defn}
									<p class="glo-term__def">{defn}</p>
								{/if}
								<p class="glo-term__meta">
									<span class="glo-meta-item"
										><span class="glo-meta-lbl">{m.glo_lbl_type()}</span>{typeLine(def)}</span
									>
									<span class="glo-meta-item"
										><span class="glo-meta-lbl">{m.glo_lbl_src()}</span>{srcLine(def)}</span
									>
								</p>
								{#if cav}
									<p class="glo-term__note">
										<span class="glo-meta-lbl">{m.glo_lbl_note()}</span>{cav}
									</p>
								{/if}
							</dd>
						</div>
					{/each}
				</dl>
			</section>
		{/each}

		<section class="ds-sec">
			<p class="srcline">{m.glo_srcline()}</p>
		</section>
	</div>
</section>

<style>
	/* El chrome (.ap-hero, .ds-main, .ds-sec, .prov, .srcline…) ve del design-system.
	   Aquí només la llista del diccionari i els seus detalls propis. */
	.glo-key {
		display: flex;
		gap: 18px;
		flex-wrap: wrap;
		align-items: center;
		margin: 18px 0 0;
	}
	.glo-key .prov {
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
	}
	.glo-count {
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
		letter-spacing: 0.04em;
		color: var(--dp-text-subtle);
		padding-right: 4px;
	}

	.ds-sec.first {
		border-top: none;
	}
	/* Frase que separa glossari (diccionari) de metodologia (assaig). */
	.glo-distinct {
		margin-bottom: 4px;
	}

	.glo-list {
		margin: 6px 0 0;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: 14px;
	}

	.glo-term {
		background: var(--dp-surface);
		border: 1px solid var(--dp-border);
		border-left: 3px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-lg);
		padding: 14px 16px 15px;
	}
	/* La vora esquerra codifica la procedència (mateixa signatura que metodologia). */
	.glo-term.prov-edge--measured {
		border-left-color: var(--dp-prov-measured);
	}
	.glo-term.prov-edge--derived {
		border-left-color: var(--dp-prov-derived);
	}
	.glo-term.prov-edge--negative {
		border-left-color: var(--dp-prov-negative);
	}
	.glo-term.planned {
		opacity: 0.82;
	}

	.glo-term__hd {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 10px;
		flex-wrap: wrap;
		margin: 0 0 7px;
	}
	.glo-term__name {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 1.02rem;
		line-height: 1.2;
		color: var(--dp-text);
	}
	.glo-term__prov {
		font-family: var(--dp-font-mono);
		font-size: 0.56rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		white-space: nowrap;
	}
	.glo-term__planned {
		margin: 0 0 6px;
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-warning, #b5612a);
	}

	.glo-term__body {
		margin: 0;
	}
	.glo-term__def {
		margin: 0 0 8px;
		font-size: 0.9rem;
		line-height: 1.55;
		color: var(--dp-text-muted);
		text-wrap: pretty;
	}
	.glo-term__meta {
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.glo-meta-item {
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		line-height: 1.45;
		color: var(--dp-text-subtle);
	}
	.glo-meta-lbl {
		display: inline-block;
		min-width: 4.2em;
		margin-right: 8px;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		font-size: 0.56rem;
		color: var(--dp-text-subtle);
		opacity: 0.85;
	}
	.glo-term__note {
		margin: 9px 0 0;
		padding-top: 9px;
		border-top: 1px dashed var(--dp-border);
		font-size: 0.78rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
	}
	.glo-term__note .glo-meta-lbl {
		color: var(--dp-prov-derived);
		opacity: 1;
	}

	@media (max-width: 520px) {
		.glo-list {
			grid-template-columns: 1fr;
		}
	}
</style>
