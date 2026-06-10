<script lang="ts">
	/**
	 * Constel·lació STOCK × EMPREMTA (IETR_stock × IETR_impact) — la «constelación stock-impact»
	 * del consultor. Treu l'IETR de número fetitxe i el torna un mapa mental: cada municipi és un
	 * punt; X = estructura PREPARADA (stock: habitatge no principal + reglat), Y = empremta
	 * OBSERVADA (impact: residus/vidre). Quatre quadrants amb lectura. Color = tipologia, mida =
	 * població, halo = confiança baixa. Cap xifra inventada: tot surt del dataset (contracte).
	 *
	 * Mantenim els termes `stock`/`impact` (vocabulari del projecte) però els ACOMPANYEM amb text
	 * planer als eixos, als quadrants (gloss) i al tooltip, perquè un usuari que entra fred entengui
	 * QUÈ mira. El tooltip és HTML real (substitueix el <title> SVG natiu, lent i poc fiable):
	 * apareix a l'instant amb el ratolí, el dit (tàctil) i el focus de teclat.
	 */
	import { tipologiaColor } from '$lib/map/tipologia';
	import { m } from '$lib/paraglide/messages';
	import type { MunicipisDataset } from '$lib/contract/types';

	let { dataset }: { dataset: MunicipisDataset } = $props();

	// Geometria (viewBox). Marges per als eixos.
	const W = 640;
	const H = 480;
	const ML = 30;
	const MR = 16;
	const MT = 16;
	const MB = 34;
	const PW = W - ML - MR;
	const PH = H - MT - MB;
	const sx = (stock: number) => ML + (stock / 100) * PW;
	const sy = (impact: number) => MT + (1 - impact / 100) * PH; // impact alt → a dalt

	type Pt = {
		ine5: string;
		nom: string;
		stock: number;
		impact: number;
		pob: number;
		tipologia: string | null;
		baixa: boolean;
	};

	const pts = $derived(
		Object.values(dataset.municipis)
			.map((r) => ({
				ine5: r.ine5,
				nom: r.nom,
				stock: r.values.IETR_stock,
				impact: r.values.IETR_impact,
				pob: typeof r.values.poblacio === 'number' ? r.values.poblacio : 0,
				tipologia: typeof r.values.tipologia === 'string' ? r.values.tipologia : null,
				baixa: r.values.confianca === 'baixa'
			}))
			.filter((p): p is Pt => typeof p.stock === 'number' && typeof p.impact === 'number')
	);

	// Radi ~ arrel quadrada de la població (àrea proporcional a la població), acotat.
	const maxPob = $derived(Math.max(1, ...pts.map((p) => p.pob)));
	const radius = (pob: number) => 4 + 11 * Math.sqrt(pob / maxPob);

	// Etiquetem només els 7 més «extrems» (lluny del centre 50,50) per no saturar.
	const labelled = $derived(
		new Set(
			pts
				.map((p) => ({ ine5: p.ine5, d: Math.hypot(p.stock - 50, p.impact - 50) }))
				.sort((a, b) => b.d - a.d)
				.slice(0, 7)
				.map((s) => s.ine5)
		)
	);

	const color = (tip: string | null) => tipologiaColor(tip);

	// Lectura planera del quadrant (la mateixa gloss que les etiquetes dels quadrants).
	const quadHelp = (p: Pt) =>
		p.stock >= 50
			? p.impact >= 50
				? m.constel_q_consolidada_help()
				: m.constel_q_latent_help()
			: p.impact >= 50
				? m.constel_q_sense_stock_help()
				: m.constel_q_baixa_help();

	// Tooltip HTML (posició relativa a la <figure>). Substitueix el <title> SVG natiu.
	let figEl: HTMLElement | undefined = $state();
	let hovered = $state<Pt | null>(null);
	let tx = $state(0);
	let ty = $state(0);

	function moveTo(clientX: number, clientY: number) {
		if (!figEl) return;
		const r = figEl.getBoundingClientRect();
		tx = clientX - r.left;
		ty = clientY - r.top;
	}
	function show(p: Pt, e: PointerEvent) {
		hovered = p;
		moveTo(e.clientX, e.clientY);
	}
	function track(e: PointerEvent) {
		if (hovered) moveTo(e.clientX, e.clientY);
	}
	function hide() {
		hovered = null;
	}
</script>

<figure class="constel" bind:this={figEl}>
	<svg viewBox="0 0 {W} {H}" role="img" aria-label={m.constel_aria()} preserveAspectRatio="xMidYMid meet">
		<!-- Línies de quadrant (a stock=50 i impact=50) -->
		<line x1={sx(50)} y1={MT} x2={sx(50)} y2={MT + PH} class="grid" />
		<line x1={ML} y1={sy(50)} x2={ML + PW} y2={sy(50)} class="grid" />

		<!-- Etiquetes de quadrant: nom tècnic + gloss planera -->
		<text x={sx(74)} y={sy(96)} class="q">{m.constel_q_consolidada()}</text>
		<text x={sx(74)} y={sy(96) + 13} class="qh">{m.constel_q_consolidada_help()}</text>
		<text x={sx(74)} y={sy(4)} class="q">{m.constel_q_latent()}</text>
		<text x={sx(74)} y={sy(4) + 13} class="qh">{m.constel_q_latent_help()}</text>
		<text x={sx(26)} y={sy(96)} class="q">{m.constel_q_sense_stock()}</text>
		<text x={sx(26)} y={sy(96) + 13} class="qh">{m.constel_q_sense_stock_help()}</text>
		<text x={sx(26)} y={sy(4)} class="q">{m.constel_q_baixa()}</text>
		<text x={sx(26)} y={sy(4) + 13} class="qh">{m.constel_q_baixa_help()}</text>

		<!-- Punts (halo de confiança baixa a sota) -->
		{#each pts as p (p.ine5)}
			{#if p.baixa}
				<circle cx={sx(p.stock)} cy={sy(p.impact)} r={radius(p.pob) + 3.5} class="halo" />
			{/if}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<circle
				cx={sx(p.stock)}
				cy={sy(p.impact)}
				r={radius(p.pob)}
				fill={color(p.tipologia)}
				class="pt"
				onpointerenter={(e) => show(p, e)}
				onpointermove={track}
				onpointerleave={hide}
			></circle>
			{#if labelled.has(p.ine5)}
				<text x={sx(p.stock)} y={sy(p.impact) - radius(p.pob) - 4} class="lbl">{p.nom}</text>
			{/if}
		{/each}

		<!-- Etiquetes d'eix: X centrada a baix; Y VERTICAL a l'esquerra (evita encavalcar amb els quadrants) -->
		<text x={ML + PW / 2} y={H - 8} class="axis" text-anchor="middle">{m.constel_x()} →</text>
		<text x={12} y={MT + PH / 2} class="axis" text-anchor="middle" transform="rotate(-90 12 {MT + PH / 2})">{m.constel_y()} ↑</text>
	</svg>

	{#if hovered}
		<div class="tip" style="left:{tx}px; top:{ty}px" aria-hidden="true">
			<span class="tip__nom">{hovered.nom}</span>
			<span class="tip__row">{m.constel_x()}: <b>{Math.round(hovered.stock)}</b>/100</span>
			<span class="tip__row">{m.constel_y()}: <b>{Math.round(hovered.impact)}</b>/100</span>
			<span class="tip__q">{quadHelp(hovered)}</span>
		</div>
	{/if}
</figure>

<style>
	.constel {
		margin: 0;
		position: relative;
	}
	.constel svg {
		width: 100%;
		height: auto;
		display: block;
		overflow: visible;
	}
	.grid {
		stroke: var(--dp-border-strong);
		stroke-width: 1;
		stroke-dasharray: 3 4;
		opacity: 0.7;
	}
	.q {
		font-family: var(--dp-font-mono);
		font-size: 11px;
		fill: var(--dp-text-subtle);
		text-anchor: middle;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.qh {
		font-family: var(--dp-font-sans);
		font-size: 10px;
		fill: var(--dp-text-muted);
		text-anchor: middle;
	}
	.pt {
		stroke: var(--dp-surface);
		stroke-width: 1.2;
		opacity: 0.9;
		cursor: pointer;
	}
	.halo {
		fill: none;
		stroke: var(--dp-text-subtle);
		stroke-width: 1;
		stroke-dasharray: 2 2;
		opacity: 0.6;
	}
	.lbl {
		font-family: var(--dp-font-sans);
		font-size: 11px;
		fill: var(--dp-text);
		text-anchor: middle;
		paint-order: stroke;
		stroke: var(--dp-surface);
		stroke-width: 3px;
	}
	.axis {
		font-family: var(--dp-font-mono);
		font-size: 11px;
		fill: var(--dp-text-muted);
		letter-spacing: 0.04em;
	}
	.tip {
		position: absolute;
		transform: translate(-50%, calc(-100% - 14px));
		pointer-events: none;
		z-index: 5;
		min-width: 150px;
		max-width: 240px;
		padding: 8px 10px;
		background: var(--dp-surface);
		border: 1px solid var(--dp-border-strong);
		border-radius: 8px;
		box-shadow: 0 4px 14px rgb(0 0 0 / 12%);
		display: flex;
		flex-direction: column;
		gap: 2px;
		font-family: var(--dp-font-sans);
	}
	.tip__nom {
		font-weight: 600;
		font-size: 13px;
		color: var(--dp-text);
		margin-bottom: 2px;
	}
	.tip__row {
		font-size: 12px;
		color: var(--dp-text-muted);
	}
	.tip__row b {
		color: var(--dp-text);
		font-weight: 600;
	}
	.tip__q {
		font-size: 12px;
		color: var(--dp-text-subtle);
		margin-top: 3px;
		font-style: italic;
	}
</style>
