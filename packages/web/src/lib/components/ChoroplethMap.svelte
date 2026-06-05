<script lang="ts">
	/**
	 * Mapa coroplètic del Berguedà (MapLibre GL · F2, Mirador).
	 *
	 * Disseny segons design-system:
	 *  - basemap APAGAT amb tokens --dp-map-* (el dada resalta, el mapa s'apaga);
	 *  - cap dependència de tile-server: estil autocontingut (fons + geometria local) →
	 *    desplegable a Cloudflare Pages estàtic i funcional offline;
	 *  - coroplètic amb la rampa "exposició" (--dp-exposure-*) o, per a desviacions amb signe
	 *    (gap població real↔padró), la rampa DIVERGENT (--dp-div-*) ancorada a 0;
	 *    5 classes per defecte (cuantils per IETR, Jenks per magnituds crues, divergent pel gap);
	 *  - "sense dada" amb TRAMAT (hatch) sobre --dp-nodata, mai relleno pla (secret estadístic);
	 *  - CONFIANÇA BAIXA de l'estimació: opacitat reduïda + tramat damunt del color (honestedat:
	 *    el mapa no afirma un gap sòlid on l'estimació és feble);
	 *  - hover (contorn --dp-map-label) i selecció (--dp-map-highlight).
	 *
	 * Només client: MapLibre toca `window`; el mòdul es carrega a onMount (import dinàmic).
	 * El component emet `hover` i `select` perquè la pàgina pinti el tooltip amb procedència.
	 */
	import { onMount, onDestroy } from 'svelte';
	import type { Map as MlMap, GeoJSONSource, MapGeoJSONFeature } from 'maplibre-gl';
	import type { FeatureCollection } from 'geojson';
	import type { MunicipisDataset, MetricKey } from '$lib/contract/types';
	import { type Classification } from '$lib/map/classify';
	import { rampColors, divergingColors, NODATA, MAP } from '$lib/map/palette';

	/** Nivell de confiança de l'estimació que rep tractament d'honestedat (no es pinta sòlid). */
	const LOW_CONFIDENCE = 'baixa';

	interface HoverPayload {
		ine5: string;
		nom: string;
		value: number | string | null;
		/** Confiança de l'estimació (clau `confianca` del contracte); null si no n'hi ha. */
		conf: string | null;
		x: number;
		y: number;
	}

	interface Props {
		dataset: MunicipisDataset;
		/** GeoJSON dels municipis (properties.ine5 = join key). */
		geojson: FeatureCollection;
		indicator: MetricKey;
		/** Classificació calculada a fora (la pàgina), per compartir-la amb la llegenda. */
		classification: Classification;
		onhover?: (p: HoverPayload | null) => void;
		onselect?: (ine5: string | null) => void;
	}

	let { dataset, geojson, indicator, classification, onhover, onselect }: Props = $props();

	let container: HTMLDivElement;
	let map: MlMap | null = null;
	let ready = $state(false);
	let selected: string | null = $state(null);

	const SRC = 'bergueda';
	const FILL = 'mun-fill';
	const HATCH = 'mun-hatch';
	const LOWCONF = 'mun-lowconf';
	const LINE = 'mun-line';
	const HOVER = 'mun-hover';
	const SELECT = 'mun-select';

	/** Patró de tramat diagonal per a "sense dada" (canvas → addImage). */
	function makeHatch(): ImageData {
		const size = 8;
		const c = document.createElement('canvas');
		c.width = size;
		c.height = size;
		const ctx = c.getContext('2d')!;
		ctx.fillStyle = NODATA;
		ctx.fillRect(0, 0, size, size);
		ctx.strokeStyle = 'rgba(90,96,102,0.55)'; // --dp-map-label, tènue
		ctx.lineWidth = 1.1;
		ctx.beginPath();
		ctx.moveTo(0, size);
		ctx.lineTo(size, 0);
		ctx.moveTo(-2, 2);
		ctx.lineTo(2, -2);
		ctx.moveTo(size - 2, size + 2);
		ctx.lineTo(size + 2, size - 2);
		ctx.stroke();
		return ctx.getImageData(0, 0, size, size);
	}

	/**
	 * Tramat SEMITRANSPARENT per a confiança baixa: s'apila DAMUNT del color del gap perquè
	 * el municipi no es llegeixi com una afirmació sòlida (honestedat visual). El fons és
	 * transparent (deixa veure el color de sota) i només hi ha les ratlles fosques tènues.
	 */
	function makeLowConfHatch(): ImageData {
		const size = 8;
		const c = document.createElement('canvas');
		c.width = size;
		c.height = size;
		const ctx = c.getContext('2d')!;
		ctx.clearRect(0, 0, size, size); // fons transparent → es veu el gap de sota
		ctx.strokeStyle = 'rgba(36,40,46,0.42)'; // --dp-map-highlight, tènue
		ctx.lineWidth = 1;
		ctx.beginPath();
		ctx.moveTo(0, size);
		ctx.lineTo(size, 0);
		ctx.moveTo(-2, 2);
		ctx.lineTo(2, -2);
		ctx.moveTo(size - 2, size + 2);
		ctx.lineTo(size + 2, size - 2);
		ctx.stroke();
		return ctx.getImageData(0, 0, size, size);
	}

	/** Colors per classe segons el mètode: divergent (ancorat a 0) o seqüencial "exposició". */
	function classColors(c: Classification): string[] {
		return c.method === 'diverging' && c.center !== undefined
			? divergingColors(c.domain, c.center)
			: rampColors(c.classes);
	}

	/**
	 * Expressió data-driven de MapLibre per al color de farciment.
	 * Es construeix una rampa step a partir dels talls de la classificació i els colors
	 * mostrejats de la rampa activa. El valor de cada municipi s'injecta com a feature
	 * property `__val` (join amb el dataset) abans de crear la font.
	 */
	function fillColorExpression(c: Classification): unknown {
		const colors = classColors(c);
		if (c.classes <= 1 || c.breaks.length === 0) {
			// una sola classe (o tots iguals): color únic; el "sense dada" el tapa la capa hatch.
			return colors[0] ?? MAP.land;
		}
		// ['step', val, color0, b0, color1, b1, color2, ...]
		const expr: unknown[] = ['step', ['get', '__val'], colors[0]];
		for (let i = 0; i < c.breaks.length; i++) {
			expr.push(c.breaks[i], colors[i + 1]);
		}
		return expr;
	}

	/**
	 * Injecta a cada feature el valor de l'indicador actiu (__val/__hasval) i la confiança de
	 * l'estimació (__conf/__lowconf). La confiança ve del contracte (clau `confianca`) i serveix
	 * per al tractament d'honestedat: els municipis de confiança baixa no es pinten sòlids.
	 */
	function joinValues(fc: FeatureCollection, key: MetricKey): FeatureCollection {
		return {
			...fc,
			features: fc.features.map((f) => {
				const ine5 = (f.properties?.ine5 as string) ?? '';
				const row = dataset.municipis[ine5];
				const raw = row?.values?.[key];
				const hasVal = typeof raw === 'number' && Number.isFinite(raw);
				const conf = (row?.values?.confianca as string | undefined) ?? null;
				return {
					...f,
					id: ine5, // feature-state per hover/select
					properties: {
						...f.properties,
						__val: hasVal ? (raw as number) : null,
						__hasval: hasVal,
						__conf: conf,
						// confiança baixa NOMÉS és rellevant quan hi ha valor a pintar (gap/estimació).
						__lowconf: hasVal && conf === LOW_CONFIDENCE
					}
				};
			})
		};
	}

	function buildData(key: MetricKey) {
		return joinValues(geojson, key);
	}

	async function init() {
		// maplibre-gl v5 no té default export: usem el namespace (Map, NavigationControl…).
		const maplibregl = await import('maplibre-gl');
		await import('maplibre-gl/dist/maplibre-gl.css');

		map = new maplibregl.Map({
			container,
			// Estil mínim autocontingut: fons = aigua/land apagat. Sense fonts de tiles externes
			// ni glyphs (no fem servir etiquetes de text al canvas; els topònims van al tooltip).
			style: {
				version: 8,
				sources: {},
				layers: [{ id: 'bg', type: 'background', paint: { 'background-color': MAP.water } }]
			},
			center: [1.85, 42.15], // Berguedà aprox.
			zoom: 9.2,
			minZoom: 7,
			maxZoom: 13,
			attributionControl: { compact: true },
			dragRotate: false,
			pitchWithRotate: false
		});

		map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
		map.scrollZoom.disable(); // evita segrestar l'scroll de la pàgina; zoom amb botons / +Ctrl
		map.scrollZoom.enable({ around: 'center' });

		map.on('load', () => {
			if (!map) return;
			const img = makeHatch();
			if (!map.hasImage('hatch')) {
				// addImage accepta ImageData a MapLibre v5.
				map.addImage('hatch', img as unknown as ImageBitmap, { pixelRatio: 1 });
			}
			if (!map.hasImage('hatch-lowconf')) {
				map.addImage('hatch-lowconf', makeLowConfHatch() as unknown as ImageBitmap, {
					pixelRatio: 1
				});
			}

			map.addSource(SRC, { type: 'geojson', data: buildData(indicator), promoteId: 'ine5' });

			// Capa "sense dada": tramat sota el color (només es veu on __hasval=false).
			map.addLayer({
				id: HATCH,
				type: 'fill',
				source: SRC,
				filter: ['!', ['get', '__hasval']],
				paint: { 'fill-pattern': 'hatch' }
			});

			// Capa coroplètica: només municipis amb dada. La confiança baixa es pinta amb
			// opacitat reduïda (honestedat: l'estimació és menys ferma) + tramat a sobre (LOWCONF).
			map.addLayer({
				id: FILL,
				type: 'fill',
				source: SRC,
				filter: ['get', '__hasval'],
				paint: {
					'fill-color': fillColorExpression(classification) as never,
					'fill-opacity': ['case', ['boolean', ['get', '__lowconf'], false], 0.55, 0.92]
				}
			});

			// Tractament de CONFIANÇA BAIXA: tramat semitransparent damunt del color del gap,
			// perquè el mapa no sobre-afirmi on l'estimació és feble (mateix gest que "sense dada").
			map.addLayer({
				id: LOWCONF,
				type: 'fill',
				source: SRC,
				filter: ['boolean', ['get', '__lowconf'], false],
				paint: { 'fill-pattern': 'hatch-lowconf' }
			});

			// Contorns de municipi (basemap apagat).
			map.addLayer({
				id: LINE,
				type: 'line',
				source: SRC,
				paint: { 'line-color': MAP.boundary, 'line-width': 0.8 }
			});

			// Hover: contorn més marcat (feature-state).
			map.addLayer({
				id: HOVER,
				type: 'line',
				source: SRC,
				paint: {
					'line-color': MAP.label,
					'line-width': ['case', ['boolean', ['feature-state', 'hover'], false], 2, 0]
				}
			});

			// Selecció: contorn ressaltat.
			map.addLayer({
				id: SELECT,
				type: 'line',
				source: SRC,
				paint: {
					'line-color': MAP.highlight,
					'line-width': ['case', ['boolean', ['feature-state', 'selected'], false], 2.6, 0]
				}
			});

			// Enquadra a la geometria.
			fitToData(maplibregl);
			wireInteractions();
			ready = true;
		});
	}

	function fitToData(maplibregl: typeof import('maplibre-gl')) {
		if (!map) return;
		const b = new maplibregl.LngLatBounds();
		for (const f of geojson.features) {
			const g = f.geometry;
			const eat = (coords: number[]) => b.extend(coords as [number, number]);
			const walk = (arr: unknown): void => {
				if (Array.isArray(arr) && typeof arr[0] === 'number') eat(arr as number[]);
				else if (Array.isArray(arr)) arr.forEach(walk);
			};
			if (g && 'coordinates' in g) walk(g.coordinates);
		}
		if (!b.isEmpty()) map.fitBounds(b, { padding: 24, duration: 0 });
	}

	let hoverId: string | null = null;

	function wireInteractions() {
		if (!map) return;
		// LOWCONF s'apila sobre FILL: cal que també capti el hover dels munis de confiança baixa.
		const interactive = [FILL, LOWCONF, HATCH];

		for (const layer of interactive) {
			map.on('mousemove', layer, (e) => {
				if (!map) return;
				const feat = e.features?.[0] as MapGeoJSONFeature | undefined;
				if (!feat) return;
				const ine5 = (feat.properties?.ine5 as string) ?? '';
				if (hoverId && hoverId !== ine5) {
					map.setFeatureState({ source: SRC, id: hoverId }, { hover: false });
				}
				hoverId = ine5;
				map.setFeatureState({ source: SRC, id: ine5 }, { hover: true });
				map.getCanvas().style.cursor = 'pointer';

				const row = dataset.municipis[ine5];
				const value = (row?.values?.[indicator] ?? null) as number | string | null;
				onhover?.({
					ine5,
					nom: (feat.properties?.nom as string) ?? row?.nom ?? ine5,
					value,
					conf: (row?.values?.confianca as string | undefined) ?? null,
					x: e.point.x,
					y: e.point.y
				});
			});

			map.on('mouseleave', layer, () => {
				if (!map) return;
				if (hoverId) map.setFeatureState({ source: SRC, id: hoverId }, { hover: false });
				hoverId = null;
				map.getCanvas().style.cursor = '';
				onhover?.(null);
			});

			map.on('click', layer, (e) => {
				if (!map) return;
				const feat = e.features?.[0];
				const ine5 = (feat?.properties?.ine5 as string) ?? '';
				if (selected) map.setFeatureState({ source: SRC, id: selected }, { selected: false });
				selected = selected === ine5 ? null : ine5;
				if (selected) map.setFeatureState({ source: SRC, id: selected }, { selected: true });
				onselect?.(selected);
			});
		}
	}

	// Reactiu: en canviar d'indicador, re-join de dades i re-pintat del color.
	$effect(() => {
		// dependències explícites
		const key = indicator;
		const c = classification;
		if (!map || !ready) return;
		const src = map.getSource(SRC) as GeoJSONSource | undefined;
		if (!src) return;
		src.setData(buildData(key) as never);
		if (map.getLayer(FILL)) {
			map.setPaintProperty(FILL, 'fill-color', fillColorExpression(c) as never);
		}
	});

	onMount(() => {
		init();
	});

	onDestroy(() => {
		map?.remove();
		map = null;
	});
</script>

<div class="map" bind:this={container} role="application" aria-label="Mapa coroplètic del Berguedà">
	{#if !ready}
		<div class="map__loading" aria-hidden="true"></div>
	{/if}
</div>

<style>
	.map {
		position: relative;
		width: 100%;
		height: clamp(360px, 60vh, 620px);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-lg);
		overflow: hidden;
		background: var(--dp-map-water, #d8e2e4);
	}

	.map__loading {
		position: absolute;
		inset: 0;
		background: var(--dp-map-land, #f2f1ec);
	}

	/* La capa de land (token) com a teló de fons mentre carrega la geometria. */
	:global(.map .maplibregl-canvas) {
		outline: none;
	}
</style>
