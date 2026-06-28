<script lang="ts">
	/**
	 * «Límits del model» — els tres gràfics germans de /metodologia (Fase 1), tots SVG
	 * prerenderitzables (deterministes, verificables per HTML):
	 *  1. Reliability diagram — l'interval nominal del X% conté la veritat ~X% dels cops (held-out).
	 *  2. Scatter ETCA↔pernocta — 486 munis; la BANDA DE SOROLL és la protagonista: la majoria dels
	 *     de signe oposat hi cauen dins (el nostre marge), 8 són senyal real. Cap nom destacat.
	 *  3. Règim dens — consum domèstic/càpita vs densitat; els nuclis densos cauen sota la mediana →
	 *     l'estimació no és fiable allà. És el límit, i el marquem nosaltres.
	 */
	import { m } from '$lib/paraglide/messages';
	import type { MetodologiaModel } from '$lib/contract/metodologia';

	let { model }: { model: MetodologiaModel } = $props();

	const W = 360;
	const H = 260;
	const P = { l: 46, r: 14, t: 16, b: 40 };
	const iw = W - P.l - P.r;
	const ih = H - P.t - P.b;

	// 1 · Reliability (0–100 als dos eixos).
	const rx = (v: number) => P.l + (v / 100) * iw;
	const ry = (v: number) => P.t + (1 - v / 100) * ih;
	const reliabPath = $derived(
		model.reliability.map((p, i) => `${i ? 'L' : 'M'}${rx(p.n).toFixed(1)} ${ry(p.e).toFixed(1)}`).join(' ')
	);

	// 2 · Scatter (gap %, retallat a una finestra llegible).
	const SMIN = -60;
	const SMAX = 90;
	const sc = (v: number) => Math.max(SMIN, Math.min(SMAX, v));
	const sx = (v: number) => P.l + ((sc(v) - SMIN) / (SMAX - SMIN)) * iw;
	const sy = (v: number) => P.t + (1 - (sc(v) - SMIN) / (SMAX - SMIN)) * ih;
	const NB_X = 8; // marge nostre (≈ error medià Berguedà / classe neutra)
	const NB_Y = $derived(model.discrepancia.etca_min); // |ETCA| mínim declarat
	// Ordre de pintat: primer soroll/coincident (massa grisa), després senyal (a sobre, destacat).
	const ptsSorted = $derived([...model.discrepancia.punts].sort((a) => (a.cls === 's' ? 1 : -1)));

	// 3 · Règim dens (x = log10 densitat, y = kWh domèstic/càpita).
	const DMAX = 20000;
	const KMAX = 3000;
	const lx = (d: number) => P.l + (Math.log10(Math.max(1, d)) / Math.log10(DMAX)) * iw;
	const ly = (k: number) => P.t + (1 - Math.min(k, KMAX) / KMAX) * ih;
	const densTicks = [1, 10, 100, 1000, 10000];
	const med = $derived(model.regim.mediana ?? 0);
</script>

<div class="mm">
	<!-- 1 · RELIABILITY -->
	<figure class="mm__fig">
		<figcaption class="mm__cap">{m.met_reliab_title()}</figcaption>
		<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label={m.met_reliab_title()}>
			<line x1={P.l} y1={P.t} x2={rx(100)} y2={ry(100)} class="mm__diag" />
			<line x1={P.l} y1={P.t + ih} x2={P.l + iw} y2={P.t + ih} class="mm__axis" />
			<line x1={P.l} y1={P.t} x2={P.l} y2={P.t + ih} class="mm__axis" />
			{#each [0, 50, 100] as t (t)}
				<text x={rx(t)} y={P.t + ih + 16} class="mm__tk" text-anchor="middle">{t}</text>
				<text x={P.l - 6} y={ry(t) + 3} class="mm__tk" text-anchor="end">{t}</text>
			{/each}
			<path d={reliabPath} class="mm__line" fill="none" />
			{#each model.reliability as p (p.n)}
				<circle cx={rx(p.n)} cy={ry(p.e)} r="3.2" class="mm__dot" />
			{/each}
			<text x={P.l + iw / 2} y={H - 4} class="mm__axl" text-anchor="middle">{m.met_ax_nominal()}</text>
		</svg>
		<p class="mm__txt">{m.met_reliab_cap({ v: String(model.interval80 ?? '—') })}</p>
	</figure>

	<!-- 2 · SCATTER ETCA ↔ PERNOCTA (banda de soroll protagonista) -->
	<figure class="mm__fig">
		<figcaption class="mm__cap">{m.met_scatter_title()}</figcaption>
		<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label={m.met_scatter_title()}>
			<!-- Banda de soroll: el nostre marge. Protagonista visual. -->
			<rect
				x={sx(-NB_X)}
				y={sy(NB_Y)}
				width={sx(NB_X) - sx(-NB_X)}
				height={sy(-NB_Y) - sy(NB_Y)}
				class="mm__band"
			/>
			<line x1={sx(SMIN)} y1={sy(SMIN)} x2={sx(SMAX)} y2={sy(SMAX)} class="mm__diag" />
			<line x1={sx(0)} y1={P.t} x2={sx(0)} y2={P.t + ih} class="mm__zero" />
			<line x1={P.l} y1={sy(0)} x2={P.l + iw} y2={sy(0)} class="mm__zero" />
			{#each ptsSorted as p, i (i)}
				<circle cx={sx(p.x)} cy={sy(p.y)} r={p.cls === 's' ? 3 : 1.6} class="mm__pt mm__pt--{p.cls}" />
			{/each}
			<text x={sx(NB_X) + 3} y={sy(NB_Y) + 9} class="mm__band-lab">{m.met_scatter_band()}</text>
			<text x={P.l + iw / 2} y={H - 4} class="mm__axl" text-anchor="middle">{m.met_ax_our()}</text>
		</svg>
		<p class="mm__txt">{m.met_scatter_cap()}</p>
	</figure>

	<!-- 3 · RÈGIM DENS -->
	<figure class="mm__fig">
		<figcaption class="mm__cap">{m.met_regim_title()}</figcaption>
		<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label={m.met_regim_title()}>
			<line x1={P.l} y1={P.t + ih} x2={P.l + iw} y2={P.t + ih} class="mm__axis" />
			<line x1={P.l} y1={P.t} x2={P.l} y2={P.t + ih} class="mm__axis" />
			{#each densTicks as t (t)}
				<text x={lx(t)} y={P.t + ih + 16} class="mm__tk" text-anchor="middle"
					>{t >= 1000 ? `${t / 1000}k` : t}</text
				>
			{/each}
			{#each model.regim.punts as p, i (i)}
				<circle cx={lx(p.d)} cy={ly(p.k)} r="1.5" class="mm__pt mm__pt--c" />
			{/each}
			{#if med}
				<line x1={P.l} y1={ly(med)} x2={P.l + iw} y2={ly(med)} class="mm__median" />
				<text x={P.l + iw} y={ly(med) - 4} class="mm__band-lab" text-anchor="end"
					>{m.met_regim_median()} · {med}</text
				>
			{/if}
			<text x={P.l + iw / 2} y={H - 4} class="mm__axl" text-anchor="middle">{m.met_ax_dens()}</text>
		</svg>
		<p class="mm__txt">{m.met_regim_cap()}</p>
	</figure>
</div>

<style>
	.mm {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 22px 20px;
	}
	.mm__fig {
		margin: 0;
	}
	.mm__cap {
		font-family: var(--dp-font-display, var(--dp-font-sans));
		font-weight: 700;
		font-size: 0.95rem;
		color: var(--dp-text);
		margin-bottom: 6px;
	}
	.mm__txt {
		margin: 6px 0 0;
		font-family: var(--dp-font-sans);
		font-size: 0.76rem;
		line-height: 1.45;
		color: var(--dp-text-subtle);
	}
	.mm svg {
		display: block;
		background: var(--dp-surface, transparent);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-sm);
	}
	.mm__axis {
		stroke: var(--dp-border-strong);
		stroke-width: 1;
	}
	.mm__diag {
		stroke: var(--dp-text-subtle);
		stroke-width: 1;
		stroke-dasharray: 3 3;
		opacity: 0.6;
	}
	.mm__zero {
		stroke: var(--dp-border-strong);
		stroke-width: 1;
		stroke-dasharray: 2 3;
		opacity: 0.7;
	}
	.mm__line {
		stroke: var(--dp-forest, var(--dp-text));
		stroke-width: 2;
	}
	.mm__dot {
		fill: var(--dp-forest, var(--dp-text));
	}
	.mm__median {
		stroke: var(--dp-warm, #b5651d);
		stroke-width: 1.6;
		stroke-dasharray: 5 3;
	}
	.mm__band {
		fill: var(--dp-accent-weak, rgba(180, 140, 90, 0.18));
		stroke: var(--dp-border-strong);
		stroke-width: 1;
		stroke-dasharray: 3 2;
	}
	.mm__band-lab {
		font-family: var(--dp-font-mono);
		font-size: 9px;
		fill: var(--dp-text-muted);
	}
	.mm__pt--c,
	.mm__pt--n {
		fill: var(--dp-text-subtle);
		opacity: 0.42;
	}
	.mm__pt--s {
		fill: var(--dp-warm, #b5651d);
		opacity: 0.95;
	}
	.mm__tk {
		font-family: var(--dp-font-mono);
		font-size: 9px;
		fill: var(--dp-text-subtle);
	}
	.mm__axl {
		font-family: var(--dp-font-mono);
		font-size: 10px;
		fill: var(--dp-text-muted);
	}
</style>
