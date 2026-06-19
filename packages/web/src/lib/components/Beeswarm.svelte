<script lang="ts">
	/**
	 * Beeswarm del GAP padró ↔ presència real, a tota Catalunya (§4 viz nova).
	 *
	 * Un punt per municipi, col·locat segons el seu gap (% que la presència estimada s'aparta del
	 * padró): a l'esquerra, menys gent que el padró diu; a la dreta, MÉS gent —la població que el
	 * padró no veu—. És la tesi del projecte com a paisatge d'un cop d'ull, amb les dades de Nivell C
	 * (presència estimada en rang) de ~927 municipis.
	 *
	 * SVG prerenderitzable (el layout es calcula al servidor, determinista): funciona sense JS i és
	 * verificable per HTML. Color = paleta divergent del gap (`--dp-div2-*`, com el mapa): teal =
	 * menys; porpra = més. Cada punt enllaça a la seva fitxa; `title` natiu per al hover.
	 *
	 * Honestedat: és inferència (rang). Els extrems del gap solen ser micromunicipis (<1.000 hab) amb
	 * banda ampla i sense validació oficial — el caption ho diu; el detall, a cada fitxa.
	 */
	import { localizeHref } from '$lib/i18n';
	import { toSlug } from '$lib/contract/slug';
	import { m } from '$lib/paraglide/messages';
	import type { PernoctaMuni } from '$lib/contract/pernocta';

	interface Props {
		/** Municipis coberts (clau ine5 → fila de presència en rang). */
		munis: Record<string, PernoctaMuni>;
	}
	let { munis }: Props = $props();

	// Geometria del llenç (viewBox; s'escala responsiu via CSS width:100%).
	const W = 760;
	const M = { top: 16, right: 20, bottom: 40, left: 20 };
	const R = 3; // radi del punt
	const STEP = 2 * R + 0.5; // separació entre punts apilats
	const GMIN = -70;
	const GMAX = 160; // domini del gap (%); els extrems es retallen a la vora (p99 ≈ 128)
	const innerW = W - M.left - M.right;

	const clamp = (g: number) => Math.max(GMIN, Math.min(GMAX, g));
	const xOf = (g: number) => M.left + ((clamp(g) - GMIN) / (GMAX - GMIN)) * innerW;

	// Color divergent per signe del gap (mateixa semàntica que el mapa: porpra = més presència).
	function colorOf(g: number): string {
		if (g <= -30) return 'var(--dp-div2-0)';
		if (g <= -12) return 'var(--dp-div2-1)';
		if (g <= -3) return 'var(--dp-div2-2)';
		if (g < 3) return 'var(--dp-div2-3)';
		if (g < 20) return 'var(--dp-div2-4)';
		if (g < 60) return 'var(--dp-div2-5)';
		return 'var(--dp-div2-6)';
	}

	// Layout beeswarm: ordena per gap, col·loca per bins (amplada = punt) i apila alternant amunt/avall.
	const placed = $derived.by(() => {
		const pts = Object.values(munis)
			.filter((mu) => mu.padro && mu.padro > 0)
			.map((mu) => ({
				nom: mu.nom,
				slug: toSlug(mu.nom),
				gap: ((mu.estimacio - (mu.padro as number)) / (mu.padro as number)) * 100,
				clamped: false
			}))
			.map((p) => ({ ...p, clamped: p.gap < GMIN || p.gap > GMAX }))
			.sort((a, b) => a.gap - b.gap);
		const bins = new Map<number, number>();
		let maxUnits = 0;
		const out = pts.map((p) => {
			const cx = xOf(p.gap);
			const bi = Math.round(cx / STEP);
			const k = bins.get(bi) ?? 0;
			bins.set(bi, k + 1);
			const units = k === 0 ? 0 : Math.ceil(k / 2) * (k % 2 === 1 ? 1 : -1);
			if (Math.abs(units) > maxUnits) maxUnits = Math.abs(units);
			return { ...p, cx, units, color: colorOf(p.gap) };
		});
		const centerY = M.top + maxUnits * STEP + R;
		const H = M.top + 2 * maxUnits * STEP + 2 * R + M.bottom;
		return { dots: out.map((d) => ({ ...d, cy: centerY + d.units * STEP })), H, centerY };
	});

	const ticks = [-50, 0, 50, 100, 150];
	const total = $derived(placed.dots.length);
</script>

<figure class="bsw">
	<svg
		viewBox="0 0 {W} {placed.H}"
		width="100%"
		role="img"
		aria-label={m.beeswarm_aria({ n: String(total) })}
		preserveAspectRatio="xMidYMid meet"
	>
		<!-- Línia del PADRÓ (gap = 0): la referència. -->
		<line
			x1={xOf(0)}
			x2={xOf(0)}
			y1={M.top - 4}
			y2={placed.H - M.bottom + 6}
			stroke="var(--dp-border-strong)"
			stroke-width="1"
			stroke-dasharray="3 3"
		/>
		<!-- Eix de gap (%) -->
		{#each ticks as t (t)}
			<text
				x={xOf(t)}
				y={placed.H - M.bottom + 20}
				text-anchor="middle"
				class="bsw__tick">{t > 0 ? `+${t}` : t}%</text
			>
		{/each}
		<text x={M.left} y={placed.H - 6} text-anchor="start" class="bsw__cap">{m.beeswarm_left()}</text>
		<text x={W - M.right} y={placed.H - 6} text-anchor="end" class="bsw__cap">{m.beeswarm_right()}</text>

		<!-- Punts: un per municipi. Enllaç a la fitxa + title natiu (hover). -->
		{#each placed.dots as d (d.slug)}
			<a href={localizeHref(`/municipi/${d.slug}`)} class="bsw__dot">
				<circle cx={d.cx} cy={d.cy} r={R} fill={d.color} />
				<title>{d.nom}: {d.gap > 0 ? '+' : ''}{Math.round(d.gap)}%</title>
			</a>
		{/each}
	</svg>
	<figcaption class="bsw__foot">{m.beeswarm_foot()}</figcaption>
</figure>

<style>
	.bsw {
		margin: 0;
	}
	.bsw svg {
		display: block;
		overflow: visible;
	}
	.bsw__tick {
		font-family: var(--dp-font-mono);
		font-size: 11px;
		fill: var(--dp-text-subtle);
	}
	.bsw__cap {
		font-family: var(--dp-font-mono);
		font-size: 10px;
		fill: var(--dp-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.bsw__dot circle {
		transition:
			r 0.12s ease,
			stroke 0.12s ease;
		cursor: pointer;
	}
	.bsw__dot:hover circle,
	.bsw__dot:focus circle {
		r: 5;
		stroke: var(--dp-text);
		stroke-width: 1.2;
		outline: none;
	}
	.bsw__foot {
		margin: 8px 0 0;
		font-family: var(--dp-font-sans);
		font-size: 0.78rem;
		line-height: 1.45;
		color: var(--dp-text-subtle);
	}
</style>
