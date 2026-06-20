<script lang="ts">
	/**
	 * Constel·lació egocèntrica de pobles MIRALL (backlog #6d): el municipi al centre, els seus
	 * bessons funcionals de TOTA Catalunya en òrbita. Radi ∝ dissimilitud (com més a prop del centre,
	 * més s'assemblen); cada radi diu QUIN senyal els agermana. Clic → fitxa del bessó.
	 *
	 * SVG prerenderitzat (layout determinista al servidor): funciona sense JS, verificable. És un
	 * «mapa mental», no una mesura (similitud funcional, no geogràfica) — caveat a la fitxa.
	 */
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import type { MirallVei } from '$lib/contract/mirall';

	interface Props {
		/** Nom del municipi central. */
		center: string;
		/** Bessons (ja resolts: nom, slug, dist, codi de senyal). */
		veins: MirallVei[];
	}
	let { center, veins }: Props = $props();

	const W = 600;
	const H = 410;
	const CX = W / 2;
	const CY = 205;
	const RIN = 80;
	const ROUT = 138;

	function sigLabel(code: string): string {
		if (code === 'd') return m.mirall_sig_densitat();
		if (code === 'r') return m.mirall_sig_renda();
		if (code === 'g') return m.mirall_sig_gas();
		if (code === 'p') return m.mirall_sig_presencia();
		if (code === 't') return m.mirall_sig_turisme();
		return '';
	}

	const placed = $derived.by(() => {
		const n = veins.length;
		if (!n) return [];
		const ds = veins.map((v) => v.dist);
		const dmin = Math.min(...ds);
		const dmax = Math.max(...ds);
		const rOf = (d: number) => (dmax === dmin ? (RIN + ROUT) / 2 : RIN + ((d - dmin) / (dmax - dmin)) * (ROUT - RIN));
		return veins.map((v, i) => {
			const ang = (-90 + (i * 360) / n) * (Math.PI / 180);
			const r = rOf(v.dist);
			const x = CX + r * Math.cos(ang);
			const y = CY + r * Math.sin(ang);
			const c = Math.cos(ang);
			const anchor = c > 0.34 ? 'start' : c < -0.34 ? 'end' : 'middle';
			const lx = x + (anchor === 'start' ? 9 : anchor === 'end' ? -9 : 0);
			return { ...v, x, y, lx, anchor, sig: sigLabel(v.signal) };
		});
	});
</script>

<figure class="mc">
	<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label={m.mirall_aria({ nom: center })} preserveAspectRatio="xMidYMid meet">
		<!-- Radis (centre → bessó), amb l'etiqueta del senyal que els agermana al mig. -->
		{#each placed as p (p.slug)}
			<line x1={CX} y1={CY} x2={p.x} y2={p.y} stroke="var(--dp-border-strong)" stroke-width="1" opacity="0.5" />
		{/each}

		<!-- Bessons -->
		{#each placed as p (p.slug)}
			<a href={localizeHref(`/municipi/${p.slug}`)} class="mc__twin">
				<circle cx={p.x} cy={p.y} r="6" fill="var(--dp-accent-500, #4FA8A0)" />
				<text x={p.lx} y={p.y - 1} text-anchor={p.anchor} class="mc__nom">{p.nom}</text>
				<text x={p.lx} y={p.y + 11} text-anchor={p.anchor} class="mc__sig">{p.sig}</text>
				<title>{p.nom}</title>
			</a>
		{/each}

		<!-- Centre: el municipi -->
		<circle cx={CX} cy={CY} r="10" fill="var(--dp-text)" />
		<text x={CX} y={CY + 26} text-anchor="middle" class="mc__center">{center}</text>
	</svg>
	<figcaption class="mc__foot">{m.mirall_caveat()}</figcaption>
</figure>

<style>
	.mc {
		margin: 0;
	}
	.mc svg {
		display: block;
		overflow: visible;
	}
	.mc__center {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 13px;
		fill: var(--dp-text);
	}
	.mc__nom {
		font-family: var(--dp-font-sans);
		font-weight: 600;
		font-size: 12px;
		fill: var(--dp-text);
	}
	.mc__sig {
		font-family: var(--dp-font-mono);
		font-size: 9.5px;
		fill: var(--dp-text-subtle);
	}
	.mc__twin circle {
		transition: r 0.12s ease;
		cursor: pointer;
	}
	.mc__twin:hover circle,
	.mc__twin:focus circle {
		r: 8;
		outline: none;
	}
	.mc__twin:hover .mc__nom {
		text-decoration: underline;
	}
	.mc__foot {
		margin: 6px 0 0;
		font-family: var(--dp-font-sans);
		font-size: 0.76rem;
		line-height: 1.4;
		color: var(--dp-text-subtle);
	}
</style>
