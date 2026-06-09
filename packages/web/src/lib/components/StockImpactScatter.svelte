<script lang="ts">
	/**
	 * Constel·lació STOCK × EMPREMTA (IETR_stock × IETR_impact) — la «constelación stock-impact»
	 * del consultor. Treu l'IETR de número fetitxe i el torna un mapa mental: cada municipi és un
	 * punt; X = estructura PREPARADA (stock: habitatge no principal + reglat), Y = empremta
	 * OBSERVADA (impact: residus/vidre). Quatre quadrants amb lectura. Color = tipologia, mida =
	 * població, halo = confiança baixa. Cap xifra inventada: tot surt del dataset (contracte).
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
</script>

<figure class="constel">
	<svg viewBox="0 0 {W} {H}" role="img" aria-label={m.constel_aria()} preserveAspectRatio="xMidYMid meet">
		<!-- Línies de quadrant (a stock=50 i impact=50) -->
		<line x1={sx(50)} y1={MT} x2={sx(50)} y2={MT + PH} class="grid" />
		<line x1={ML} y1={sy(50)} x2={ML + PW} y2={sy(50)} class="grid" />

		<!-- Etiquetes de quadrant -->
		<text x={sx(74)} y={sy(94)} class="q">{m.constel_q_consolidada()}</text>
		<text x={sx(74)} y={sy(6)} class="q">{m.constel_q_latent()}</text>
		<text x={sx(26)} y={sy(94)} class="q">{m.constel_q_sense_stock()}</text>
		<text x={sx(26)} y={sy(6)} class="q">{m.constel_q_baixa()}</text>

		<!-- Punts (halo de confiança baixa a sota) -->
		{#each pts as p (p.ine5)}
			{#if p.baixa}
				<circle cx={sx(p.stock)} cy={sy(p.impact)} r={radius(p.pob) + 3.5} class="halo" />
			{/if}
			<circle
				cx={sx(p.stock)}
				cy={sy(p.impact)}
				r={radius(p.pob)}
				fill={color(p.tipologia)}
				class="pt"
			>
				<title>{p.nom} · stock {Math.round(p.stock)} · empremta {Math.round(p.impact)}</title>
			</circle>
			{#if labelled.has(p.ine5)}
				<text x={sx(p.stock)} y={sy(p.impact) - radius(p.pob) - 4} class="lbl">{p.nom}</text>
			{/if}
		{/each}

		<!-- Etiquetes d'eix -->
		<text x={ML + PW} y={H - 8} class="axis" text-anchor="end">{m.constel_x()} →</text>
		<text x={ML + 2} y={MT + 12} class="axis" text-anchor="start">↑ {m.constel_y()}</text>
	</svg>
</figure>

<style>
	.constel {
		margin: 0;
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
	.pt {
		stroke: var(--dp-surface);
		stroke-width: 1.2;
		opacity: 0.9;
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
</style>
