<script lang="ts" module>
	/**
	 * Generador de corbes de nivell (full topogràfic) — port de l'algorisme de la DA
	 * (packages/design-system/aplicacio/aplicacio.js · drawField), en TS pur i determinista.
	 *
	 * Dibuixa anells concèntrics deformats al voltant d'uns «cims» (summits); cada 3a corba
	 * és «índex» i pot portar una etiqueta de DADA REAL escrita com una cota (la línia es
	 * trenca darrere el número). Una corba terracota puntejada fa de «divisòria» (motiu de
	 * marca: el llit sec). És purament decoratiu (aria-hidden) i SSR-safe (no toca window).
	 */

	export interface Summit {
		cx: number;
		cy: number;
		r0: number;
		step: number;
		rings: number;
		sq: number;
		seed: number;
		/** Posició relativa (0-1) on penjar l'etiqueta sobre la corba índex. */
		lt: number;
	}
	export interface Divis {
		cx: number;
		cy: number;
		r: number;
		sq: number;
		seed: number;
	}

	type Pt = [number, number];

	function ringPts(cx: number, cy: number, r: number, sq: number, seed: number): Pt[] {
		const P = 54;
		const pts: Pt[] = [];
		for (let a = 0; a <= P; a++) {
			const ang = (a / P) * Math.PI * 2;
			const n = 1 + 0.1 * Math.sin(seed + ang * 3) + 0.055 * Math.cos(seed * 1.7 + ang * 5);
			pts.push([cx + Math.cos(ang) * r * n, cy + Math.sin(ang) * r * sq * n]);
		}
		return pts;
	}

	function pathOf(pts: Pt[]): string {
		let s = '';
		for (let i = 0; i < pts.length; i++) {
			s += (i ? 'L' : 'M') + pts[i][0].toFixed(1) + ' ' + pts[i][1].toFixed(1);
		}
		return s + 'Z';
	}

	/** Una primitiva de dibuix llesta per pintar amb {@html} dins de l'SVG. */
	type Shape =
		| { kind: 'path'; d: string; stroke: string; w: number; op: number; dash?: string }
		| { kind: 'label'; x: number; y: number; rot: number; w: number; text: string };

	export interface FieldColors {
		contour: string;
		contourIndex: string;
		label: string;
		plate: string;
		divide: string;
	}

	/** Construeix la llista de formes del camp (anells + etiquetes + divisòria). */
	export function buildField(
		summits: Summit[],
		divis: Divis | null,
		labels: string[],
		colors: FieldColors
	): Shape[] {
		const out: Shape[] = [];
		let li = 0;
		for (const su of summits) {
			for (let i = 1; i <= su.rings; i++) {
				const r = su.r0 + i * su.step;
				const idx = i % 3 === 0;
				const pts = ringPts(su.cx, su.cy, r, su.sq, su.seed + i * 0.3);
				out.push({
					kind: 'path',
					d: pathOf(pts),
					stroke: idx ? colors.contourIndex : colors.contour,
					w: idx ? 1.5 : 0.9,
					op: idx ? 0.95 : 0.7
				});
				if (idx && li < labels.length && i >= 3) {
					const t = Math.floor(pts.length * su.lt) % pts.length;
					const p = pts[t];
					const q = pts[(t + 2) % pts.length];
					let ang = (Math.atan2(q[1] - p[1], q[0] - p[0]) * 180) / Math.PI;
					if (ang > 90) ang -= 180;
					if (ang < -90) ang += 180;
					const text = labels[li++];
					const w = text.length * 6.3 + 6;
					out.push({ kind: 'label', x: p[0], y: p[1], rot: ang, w, text });
				}
			}
		}
		if (divis) {
			out.push({
				kind: 'path',
				d: pathOf(ringPts(divis.cx, divis.cy, divis.r, divis.sq, divis.seed)),
				stroke: colors.divide,
				w: 1.7,
				op: 0.85,
				dash: '0.1 7'
			});
		}
		return out;
	}
</script>

<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		summits: Summit[];
		divis?: Divis | null;
		labels?: string[];
		viewBox?: string;
		/** Variant de placa de fons per a les etiquetes: hero/peu (paper) vs map (terra). */
		plate?: 'paper' | 'map';
		class?: string;
	}
	let {
		summits,
		divis = null,
		labels = [],
		viewBox = '0 0 1200 380',
		plate = 'paper',
		class: className = ''
	}: Props = $props();

	// Colors: en SSR fem servir els valors del tema clar (literals de sistema.css) perquè
	// el primer pintat ja surti correcte; en muntar, els rellegim de les CSS custom props
	// reals i tornem a generar (i reaccionem als canvis de data-theme).
	const LIGHT: FieldColors = {
		contour: '#C2C7BC',
		contourIndex: '#9aa093',
		label: '#A07A4C',
		plate: '#F2F1EC',
		divide: '#C75D34'
	};

	let colors = $state<FieldColors>(LIGHT);

	function readColors(): FieldColors {
		const cs = getComputedStyle(document.documentElement);
		const dark = document.documentElement.getAttribute('data-theme') === 'dark';
		const get = (v: string, fallback: string) => (cs.getPropertyValue(v) || '').trim() || fallback;
		return {
			contour: get('--contour', LIGHT.contour),
			contourIndex: get('--contour-i', LIGHT.contourIndex),
			label: dark ? '#C79A63' : '#A07A4C',
			plate: plate === 'map' ? (dark ? '#0C1014' : '#F2F1EC') : get('--paper', LIGHT.plate),
			divide: '#C75D34'
		};
	}

	onMount(() => {
		colors = readColors();
		const obs = new MutationObserver(() => {
			colors = readColors();
		});
		obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
		return () => obs.disconnect();
	});

	const shapes = $derived(buildField(summits, divis, labels, colors));
</script>

<svg
	class={className}
	{viewBox}
	preserveAspectRatio="xMidYMid slice"
	aria-hidden="true"
	xmlns="http://www.w3.org/2000/svg"
>
	{#each shapes as s, i (i)}
		{#if s.kind === 'path'}
			<path
				d={s.d}
				fill="none"
				stroke={s.stroke}
				stroke-width={s.w}
				vector-effect="non-scaling-stroke"
				opacity={s.op}
				stroke-dasharray={s.dash}
				stroke-linecap={s.dash ? 'round' : undefined}
			/>
		{:else}
			<g transform="translate({s.x.toFixed(1)} {s.y.toFixed(1)}) rotate({s.rot.toFixed(1)})">
				<rect x={-s.w / 2} y="-7.5" width={s.w} height="15" fill={colors.plate} />
				<text
					x="0"
					y="3.4"
					text-anchor="middle"
					font-family="'IBM Plex Mono', monospace"
					font-size="11"
					font-weight="500"
					fill={colors.label}>{s.text}</text
				>
			</g>
		{/if}
	{/each}
</svg>
