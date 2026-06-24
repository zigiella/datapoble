<script lang="ts">
	/**
	 * Mapa de Catalunya amb el Berguedà ACTIU (MapLibre GL · Fase 0 de l'escala Catalunya, Mirador).
	 *
	 * Disseny segons design-system + decisions de Bea (honestedat visual):
	 *  - basemap APAGAT amb tokens --dp-map-* (el dada resalta, el mapa s'apaga);
	 *  - cap dependència de tile-server: estil autocontingut (fons + geometria local) →
	 *    desplegable a Cloudflare Pages estàtic i funcional offline;
	 *  - TOT CATALUNYA visible (els 947 municipis): els que NO són del Berguedà van ATENUATS
	 *    (fill neutre clar, «sense dades encara»), MAI acolorits per l'indicador — no fingim dada
	 *    on no n'hi ha. Capa base d'atenuat (filtre `!__inberg`) per sota de tot;
	 *  - BERGUEDÀ actiu: els seus 31 municipis acolorits pel coroplètic (rampa "exposició"
	 *    --dp-exposure-*, o per a desviacions amb signe —gap població real↔padró— la rampa
	 *    DIVERGENT teal↔porpra --dp-div2-* ancorada a 0). 5 classes per defecte;
	 *  - dins del Berguedà, «sense dada» de l'indicador → TRAMAT (hatch), mai relleno pla
	 *    (secret estadístic); CONFIANÇA BAIXA → opacitat reduïda + tramat damunt (honestedat);
	 *  - LÍMITS DE COMARCA suaus a sobre (de catalunya-comarques.geojson) per orientar;
	 *  - els 31 del Berguedà amb contorn una mica més marcat per distingir-los del context atenuat;
	 *  - hover/selecció a tot el país: dins del Berguedà → dada + procedència; fora → estat amable
	 *    «sense dades encara» (el component emet `inBergueda` perquè la pàgina triï el tooltip);
	 *  - ENQUADRAMENT inicial a la bbox dels 31 municipis del Berguedà (Catalunya queda de context
	 *    al voltant; el zoom-out revela tot el país atenuat).
	 *
	 * Rendiment: una sola source de municipis (947 polígons simplificats, ~1 MB) i una de comarques;
	 * el color es resol per EXPRESSIÓ data-driven (step sobre `__val`) i pels filtres `__inberg`/
	 * `__hasval`, sense duplicar geometria ni re-crear capes en canviar d'indicador.
	 *
	 * Només client: MapLibre toca `window`; el mòdul es carrega a onMount (import dinàmic).
	 */
	import { onMount, onDestroy } from 'svelte';
	import type { Map as MlMap, GeoJSONSource, MapGeoJSONFeature } from 'maplibre-gl';
	import type { FeatureCollection, Feature, Polygon, MultiPolygon } from 'geojson';
	import type { MunicipisDataset, MetricKey } from '$lib/contract/types';
	import type { PernoctaMuni } from '$lib/contract/pernocta';
	import { type Classification } from '$lib/map/classify';
	import { mapValue } from '$lib/map/indicators';
	import { rampColors, divergingColors, NODATA, MAP } from '$lib/map/palette';
	import { isCategorical, tipologiaMeta, tipologiaMatchExpression } from '$lib/map/tipologia';
	import type { IndicadorsCatData } from '$lib/contract/indicadors';

	/** Nivell de confiança de l'estimació que rep tractament d'honestedat (no es pinta sòlid). */
	const LOW_CONFIDENCE = 'baixa';

	interface HoverPayload {
		ine5: string;
		nom: string;
		value: number | string | null;
		/** Confiança de l'estimació (clau `confianca` del contracte); null si no n'hi ha. */
		conf: string | null;
		/** Confiança auditable 0-100 (`confianca_score`); complementa la bandera. null si no n'hi ha. */
		confScore: number | null;
		/** True si el municipi és del Berguedà (té dades); fals → «sense dades encara» (atenuat). */
		inBergueda: boolean;
		/** Presència estimada EN RANG (munis coberts pel Nivell C fora del Berguedà); null si no. */
		pernocta?: PernoctaMuni | null;
		x: number;
		y: number;
	}

	/** Granularitat del mapa: municipi (coroplètic per indicador) o comarca/vegueria (cobertura). */
	type Granularity = 'municipi' | 'comarca' | 'vegueria';

	interface Props {
		dataset: MunicipisDataset;
		/** GeoJSON de TOTS els municipis de Catalunya (947; properties.ine5 = join key). */
		geojson: FeatureCollection;
		/** GeoJSON de les 43 comarques (límits suaus d'orientació + capa de cobertura). */
		comarques: FeatureCollection;
		/** GeoJSON de les 8 vegueries (capa de cobertura; opcional). */
		vegueries?: FeatureCollection;
		indicator: MetricKey;
		/** Classificació calculada a fora (la pàgina), per compartir-la amb la llegenda. */
		classification: Classification;
		/** Nivell de granularitat actiu (per defecte municipi). */
		granularity?: Granularity;
		/** Presència estimada EN RANG dels munis coberts fora del Berguedà (ine5 → dada). Opcional. */
		pernocta?: Record<string, PernoctaMuni>;
		/** Valors d'indicadors a escala Catalunya (ine5 → {clau → valor} + `conf`) per pintar i TRAMAR
		 * els coberts pel mateix indicador i tractament de confiança que el Berguedà. Opcional. */
		catValues?: IndicadorsCatData;
		onhover?: (p: HoverPayload | null) => void;
		onselect?: (ine5: string | null) => void;
	}

	let {
		dataset,
		geojson,
		comarques,
		vegueries,
		indicator,
		classification,
		granularity = 'municipi',
		pernocta,
		catValues,
		onhover,
		onselect
	}: Props = $props();

	let container: HTMLDivElement;
	let map: MlMap | null = null;
	let ready = $state(false);
	let selected: string | null = $state(null);
	/**
	 * Observa la mida del contenidor. CRÍTIC: si MapLibre s'inicialitza quan el contenidor
	 * encara té amplada/alçada 0 (hidratació de SvelteKit abans que el grid resolgui la mida,
	 * o contenidor momentàniament colapsat), el canvas WebGL no completa la primera renderització
	 * i l'esdeveniment `load` NO es dispara mai → `ready` es queda fals → la pàgina mostra
	 * "Carregant el mapa…" per sempre. En cridar `map.resize()` quan el contenidor passa a tenir
	 * mida > 0, MapLibre re-mesura, pinta i `load` arriba. També manté el canvas net en
	 * redimensionaments de la finestra (responsivitat). Vegeu bitàcora F2 (bug del render).
	 */
	let resizeObs: ResizeObserver | null = null;

	const SRC = 'municipis'; // tots els municipis de Catalunya (947)
	const SRC_COM = 'comarques'; // límits comarcals
	const SRC_VEG = 'vegueries'; // 8 àmbits (capa de cobertura)
	const BASE = 'mun-base'; // atenuat: municipis sense dades (no Berguedà)
	const BASELINE = 'mun-baseline'; // contorn tènue de tot Catalunya
	const FILL = 'mun-fill'; // coroplètic: Berguedà amb dada
	const HATCH = 'mun-hatch'; // Berguedà sense dada de l'indicador
	const LOWCONF = 'mun-lowconf'; // Berguedà confiança baixa
	const LINE = 'mun-line'; // contorn marcat dels 31 del Berguedà
	const COMLINE = 'com-line'; // límits de comarca (suaus)
	const HOVER = 'mun-hover';
	const SELECT = 'mun-select';
	const COVERED = 'mun-covered'; // munis amb presència estimada EN RANG (Nivell C, fora del Berguedà)
	// Capes de COBERTURA (granularitat comarca/vegueria): cobertura honesta, no l'indicador.
	const COV_COM_FILL = 'cov-com-fill';
	const COV_COM_LINE = 'cov-com-line';
	const COV_VEG_FILL = 'cov-veg-fill';
	const COV_VEG_LINE = 'cov-veg-line';
	// Capes municipals (es mostren a 'municipi', s'amaguen a comarca/vegueria). COMLINE es gestiona a part.
	const MUN_LAYERS = [BASE, BASELINE, COVERED, HATCH, FILL, LOWCONF, LINE, HOVER, SELECT];

	// Color «amb dades del projecte» (teal calmat, espill de --dp-div2-1; distint de les rampes
	// d'indicador perquè a cobertura no es mostra cap rampa). Hex literal: el canvas no resol CSS vars.
	const COVERAGE_FILL = '#4FA8A0';
	// Quines features tenen dades a cada nivell (constants: tots els 31 munis del dataset són del
	// Berguedà → comarca «Berguedà»; vegueria «Comarques Centrals», PARCIAL perquè només el Berguedà hi és).
	const COV_COMARCA = 'Berguedà';
	const COV_VEGUERIA = 'Comarques Centrals';

	let mlgl: typeof import('maplibre-gl') | null = null; // ref per re-enquadrar en canviar de nivell

	/**
	 * Conjunt de codis INE5 amb dades = els municipis del Berguedà (les claus del dataset són
	 * exactament els 31). Es deriva del dataset perquè la frontera «té dades / no en té» segueixi
	 * la font de dades, no una llista codificada. El dia que entrin més comarques, s'amplia sol.
	 */
	const bergSet = $derived(new Set(Object.keys(dataset.municipis)));
	// Munis amb presència estimada EN RANG fora del Berguedà (Nivell C): es pinten distints de
	// l'atenuat «sense dades», però NO per l'indicador (no el tenim per a ells) — un tint propi.
	const coveredSet = $derived(
		new Set(Object.keys(pernocta ?? {}).filter((i) => !bergSet.has(i)))
	);

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
	 *
	 * CATEGÒRIC (tipologia): `match` sobre la cadena d'arquetip `__cat` → un color per tipus
	 * (diccionari de tipologia), no rampa. El color comunica IDENTITAT, no ordre.
	 *
	 * SEQÜENCIAL / DIVERGENT: rampa `step` a partir dels talls de la classificació i els colors
	 * mostrejats de la rampa activa. El valor numèric de cada municipi s'injecta com a feature
	 * property `__val` (join amb el dataset) abans de crear la font.
	 */
	function fillColorExpression(c: Classification, key: MetricKey, valExpr: unknown = ['get', '__val']): unknown {
		if (c.method === 'categorical' || isCategorical(key)) return tipologiaMatchExpression();
		const colors = classColors(c);
		if (c.classes <= 1 || c.breaks.length === 0) {
			// una sola classe (o tots iguals): color únic; el "sense dada" el tapa la capa hatch.
			return colors[0] ?? MAP.land;
		}
		// ['step', val, color0, b0, color1, b1, color2, ...]
		const expr: unknown[] = ['step', valExpr, colors[0]];
		for (let i = 0; i < c.breaks.length; i++) {
			expr.push(c.breaks[i], colors[i + 1]);
		}
		return expr;
	}

	/**
	 * Color de la capa COBERTS: pel valor de l'indicador a escala Catalunya (`__covval`), amb la
	 * MATEIXA classificació i colors que el Berguedà (escala compartida → comparables). Si `__covval`
	 * és null (indicador només-Berguedà), color base atenuat (amb opacitat 0 queda transparent).
	 */
	function coveredColorExpr(c: Classification, key: MetricKey): unknown {
		return [
			'case',
			['==', ['get', '__covval'], null],
			MAP.land,
			fillColorExpression(c, key, ['get', '__covval'])
		];
	}

	/**
	 * Injecta a cada feature: si és del Berguedà (__inberg), el valor de l'indicador actiu
	 * (__val/__hasval) i la confiança (__conf/__lowconf). Els municipis de FORA del Berguedà
	 * no porten valor (van a la capa base atenuada): __inberg=false i prou.
	 */
	function joinValues(fc: FeatureCollection, key: MetricKey): FeatureCollection {
		const berg = bergSet;
		const cov = coveredSet;
		const categorical = isCategorical(key);
		return {
			...fc,
			features: fc.features.map((f) => {
				const ine5 = (f.properties?.ine5 as string) ?? '';
				const inBerg = berg.has(ine5);
				const covered = !inBerg && cov.has(ine5); // presència estimada en rang (fora del Berguedà)
				// Valor de l'INDICADOR ACTIU per al muni cobert (de catValues, escala Catalunya): pinta
				// el seu color a la vista municipi pel MATEIX indicador que el Berguedà, on en tenim
				// (gap, residus). null si l'indicador és només-Berguedà → el muni queda atenuat (honest).
				const covval = covered ? (catValues?.[ine5]?.[key] ?? null) : null;
				const row = inBerg ? dataset.municipis[ine5] : undefined;
				// Confiança: del Berguedà (dataset) o, per als coberts, de l'artefacte compacte (catValues.conf).
				// Així la TRAMA de confiança baixa s'aplica a tot Catalunya, no només al Berguedà.
				const conf = inBerg
					? ((row?.values?.confianca as string | undefined) ?? null)
					: covered
						? (catValues?.[ine5]?.conf ?? null)
						: null;

				if (categorical) {
					// CATEGÒRIC (tipologia): el valor és una cadena d'arquetip. __cat la transporta
					// (la fa servir l'expressió `match` del color); __hasval és cert si l'arquetip és
					// conegut (inclou `indeterminat`, que és un estat HONEST i SÍ es pinta, en neutre,
					// no com a tramat «sense dada»). Si el valor falta o no és reconegut → tramat.
					const catRaw = inBerg ? row?.values?.[key] : null;
					const hasCat = inBerg && typeof catRaw === 'string' && !!tipologiaMeta(catRaw);
					return {
						...f,
						id: ine5,
						properties: {
							...f.properties,
							__inberg: inBerg,
							__covered: covered,
							__covval: covval,
							__val: null,
							__cat: hasCat ? (catRaw as string) : null,
							__hasval: hasCat,
							__conf: conf,
							// confiança baixa també vela la tipologia (honestedat: arquetip menys ferm).
							__lowconf: hasCat && conf === LOW_CONFIDENCE
						}
					};
				}

				// `mapValue` degrada a null el 0 d'OSM de la restauració (buit de mapejat): així
				// __hasval és fals i el municipi del Berguedà cau a la capa de tramat «sense dada»,
				// no al color de classe baixa (honestedat: 0 d'OSM ≠ 0 real d'hostaleria).
				const raw = inBerg ? mapValue(key, row?.values?.[key]) : null;
				const hasVal = typeof raw === 'number' && Number.isFinite(raw);
				return {
					...f,
					id: ine5, // feature-state per hover/select
					properties: {
						...f.properties,
						__inberg: inBerg,
						__covered: covered,
						__covval: covval,
						__val: hasVal ? (raw as number) : null,
						__cat: null,
						__hasval: hasVal,
						__conf: conf,
						// confiança baixa NOMÉS és rellevant quan hi ha valor a pintar: al Berguedà (hasVal)
						// o a un muni cobert amb valor de l'indicador (covval) → trama a tot Catalunya.
						__lowconf: (hasVal || (covered && covval !== null)) && conf === LOW_CONFIDENCE
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
		mlgl = maplibregl;
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
			center: [1.85, 42.15], // Berguedà aprox. (es reenquadra a fitToBergueda al load)
			zoom: 9.2,
			minZoom: 6, // permet allunyar-se per veure tot Catalunya atenuat
			maxZoom: 13,
			attributionControl: { compact: true },
			dragRotate: false,
			pitchWithRotate: false
		});

		map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
		map.scrollZoom.disable(); // evita segrestar l'scroll de la pàgina; zoom amb botons / +Ctrl
		map.scrollZoom.enable({ around: 'center' });

		// Desbloqueja el `load` si el mapa va néixer amb el contenidor a 0px (vegeu `resizeObs`):
		// quan el contenidor adquireix mida real, re-mesurem el canvas. Mantenir-ho viu després
		// del load també fa el mapa responsiu als canvis de mida de la finestra/columna.
		if (typeof ResizeObserver !== 'undefined') {
			let lastW = 0;
			let lastH = 0;
			resizeObs = new ResizeObserver((entries) => {
				const box = entries[0]?.contentRect;
				if (!map || !box) return;
				// Només re-mesurem si la mida ha canviat de debò i és no-degenerada (>0).
				if (box.width > 0 && box.height > 0 && (box.width !== lastW || box.height !== lastH)) {
					lastW = box.width;
					lastH = box.height;
					map.resize();
				}
			});
			resizeObs.observe(container);
		}

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
			map.addSource(SRC_COM, { type: 'geojson', data: comarques });
			if (vegueries) map.addSource(SRC_VEG, { type: 'geojson', data: vegueries });

			// Capa BASE atenuada: tots els municipis SENSE dades (no Berguedà) amb fill neutre clar.
			// «Sense dades encara»: visible però apagat, mai acolorit per l'indicador.
			map.addLayer({
				id: BASE,
				type: 'fill',
				source: SRC,
				filter: ['!', ['get', '__inberg']],
				paint: { 'fill-color': MAP.land, 'fill-opacity': 0.55 }
			});

			// Capa COBERTS: municipis FORA del Berguedà amb dada a escala Catalunya (Nivell C). Es pinten
			// pel MATEIX indicador actiu que el Berguedà (mateixa classificació i colors), on en tenim
			// (`__covval`); si l'indicador és només-Berguedà, `__covval` és null → opacitat 0 (queden
			// atenuats sobre la capa BASE, honest «sense dada»). Només a granularitat municipi.
			map.addLayer({
				id: COVERED,
				type: 'fill',
				source: SRC,
				filter: ['all', ['!', ['get', '__inberg']], ['boolean', ['get', '__covered'], false]],
				paint: {
					'fill-color': coveredColorExpr(classification, indicator) as never,
					// Sense valor → invisible; confiança baixa → opacitat reduïda (la trama hatch-lowconf s'hi
					// apila a sobre, mateix gest d'honestedat que al Berguedà); altrament, ple.
					'fill-opacity': [
						'case',
						['==', ['get', '__covval'], null], 0,
						['boolean', ['get', '__lowconf'], false], 0.55,
						0.78
					] as never
				}
			});

			// Contorn tènue de TOTS els municipis (estructura de fons, molt suau).
			map.addLayer({
				id: BASELINE,
				type: 'line',
				source: SRC,
				paint: { 'line-color': MAP.boundary, 'line-width': 0.4, 'line-opacity': 0.5 }
			});

			// Capa "sense dada" del Berguedà: tramat sota el color (Berguedà + __hasval=false).
			map.addLayer({
				id: HATCH,
				type: 'fill',
				source: SRC,
				filter: ['all', ['get', '__inberg'], ['!', ['get', '__hasval']]],
				paint: { 'fill-pattern': 'hatch' }
			});

			// Capa coroplètica: només municipis del Berguedà amb dada. La confiança baixa es pinta
			// amb opacitat reduïda (honestedat: l'estimació és menys ferma) + tramat a sobre (LOWCONF).
			map.addLayer({
				id: FILL,
				type: 'fill',
				source: SRC,
				filter: ['all', ['get', '__inberg'], ['get', '__hasval']],
				paint: {
					'fill-color': fillColorExpression(classification, indicator) as never,
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

			// Contorn marcat dels 31 municipis del Berguedà (els distingeix del context atenuat).
			map.addLayer({
				id: LINE,
				type: 'line',
				source: SRC,
				filter: ['get', '__inberg'],
				paint: { 'line-color': MAP.boundary, 'line-width': 0.8 }
			});

			// Límits de COMARCA (línia suau) per orientar dins de Catalunya.
			map.addLayer({
				id: COMLINE,
				type: 'line',
				source: SRC_COM,
				paint: { 'line-color': MAP.label, 'line-width': 0.7, 'line-opacity': 0.35 }
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

			// ── Capes de COBERTURA (granularitat comarca/vegueria) ──────────────────────────────
			// Cobertura HONESTA, no l'indicador. Amb el Nivell C estès a tota Catalunya (#152), la
			// cobertura ja NO és «només el Berguedà»: el Berguedà té dades COMPLETES (teal sòlid) i la
			// RESTA de comarques tenen presència estimada EN RANG (teal més clar). El detall per poble
			// —i els forats puntuals «sense dades»— es veu a granularitat municipi. visibility 'none';
			// applyGranularity les commuta.
			const covExpr = (nom: string) => ['==', ['get', 'nom'], nom];
			map.addLayer({
				id: COV_COM_FILL,
				type: 'fill',
				source: SRC_COM,
				layout: { visibility: 'none' },
				paint: {
					// Berguedà = completa (sòlid); resta = en rang (mateix teal, més clar). Cap gris.
					'fill-color': COVERAGE_FILL,
					'fill-opacity': ['case', covExpr(COV_COMARCA), 0.85, 0.4] as never
				}
			});
			map.addLayer({
				id: COV_COM_LINE,
				type: 'line',
				source: SRC_COM,
				layout: { visibility: 'none' },
				paint: { 'line-color': MAP.boundary, 'line-width': 0.9 }
			});
			if (vegueries) {
				map.addLayer({
					id: COV_VEG_FILL,
					type: 'fill',
					source: SRC_VEG,
					layout: { visibility: 'none' },
					// Totes les vegueries tenen presència estimada en rang (el Nivell C cobreix ~tot CAT).
					paint: { 'fill-color': COVERAGE_FILL, 'fill-opacity': 0.4 }
				});
				map.addLayer({
					id: COV_VEG_LINE,
					type: 'line',
					source: SRC_VEG,
					layout: { visibility: 'none' },
					paint: { 'line-color': MAP.boundary, 'line-width': 1.1 }
				});
			}

			// Salvaguarda: assegura que el canvas té la mida del contenidor abans d'enquadrar
			// (per si el `load` ha arribat amb una mida intermèdia). Vegeu `resizeObs`.
			map.resize();
			// Aplica la granularitat inicial (municipi per defecte) + enquadrament corresponent.
			applyGranularity(granularity);
			wireInteractions();
			ready = true;
		});
	}

	/** Enquadra a la bbox de les features que passen el predicat (o totes). */
	function fitToFeatures(fc: FeatureCollection, keep?: (f: Feature) => boolean) {
		if (!map || !mlgl) return;
		const b = new mlgl.LngLatBounds();
		for (const f of fc.features) {
			if (keep && !keep(f)) continue;
			const g = f.geometry;
			const eat = (coords: number[]) => b.extend(coords as [number, number]);
			const walk = (arr: unknown): void => {
				if (Array.isArray(arr) && typeof arr[0] === 'number') eat(arr as number[]);
				else if (Array.isArray(arr)) arr.forEach(walk);
			};
			if (g && 'coordinates' in g) walk((g as Polygon | MultiPolygon).coordinates);
		}
		if (!b.isEmpty()) map.fitBounds(b, { padding: 36, duration: 300 });
	}

	/** Enquadra a la bbox dels municipis del BERGUEDÀ (els que tenen dades) — vista municipi. */
	function fitToBergueda() {
		fitToFeatures(geojson, (f) => bergSet.has((f.properties?.ine5 as string) ?? ''));
	}

	/**
	 * Commuta la granularitat: mostra/amaga capes per `visibility` (cap re-join; tornar a municipi
	 * és instantani). A municipi → capes municipals + COMLINE; a comarca/vegueria → capes de
	 * cobertura (l'indicador NO es pinta, només cobertura honesta). Re-enquadra segons el nivell.
	 */
	function applyGranularity(g: Granularity) {
		if (!map) return;
		const show = (id: string, on: boolean) => {
			if (map!.getLayer(id)) map!.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none');
		};
		const isMun = g === 'municipi';
		for (const id of MUN_LAYERS) show(id, isMun);
		show(COMLINE, isMun); // a cobertura, les línies pròpies de cada nivell orienten
		show(COV_COM_FILL, g === 'comarca');
		show(COV_COM_LINE, g === 'comarca');
		show(COV_VEG_FILL, g === 'vegueria');
		show(COV_VEG_LINE, g === 'vegueria');
		// Enquadrament: municipi → Berguedà (context); cobertura → tot Catalunya.
		if (isMun) fitToBergueda();
		else fitToFeatures(comarques);
	}

	let hoverId: string | null = null;

	function wireInteractions() {
		if (!map) return;
		// Capes interactives: el coroplètic i el tramat del Berguedà + la base atenuada de fora
		// (LOWCONF s'apila sobre FILL → també ha de captar el hover dels munis de confiança baixa).
		const interactive = [FILL, LOWCONF, HATCH, BASE];
		// Tàctil (pointer coarse): a mòbil NO hi ha hover → el tap mostra la targeta i no navega;
		// el CTA «obrir fitxa» de la targeta és qui navega, i un tap al fons la tanca.
		const coarse = typeof matchMedia !== 'undefined' && matchMedia('(pointer: coarse)').matches;

		// Càrrega del tooltip per a una feature (compartida per hover d'escriptori i tap mòbil).
		const buildHover = (feat: MapGeoJSONFeature, point: { x: number; y: number }) => {
			const ine5 = (feat.properties?.ine5 as string) ?? '';
			const inBerg = bergSet.has(ine5);
			const row = inBerg ? dataset.municipis[ine5] : undefined;
			const covered = !inBerg && coveredSet.has(ine5);
			// Valor de l'indicador actiu: del Berguedà (dataset) o, per als coberts, de catValues (escala
			// CAT) → el tooltip dels coberts mostra el MATEIX indicador que el Berguedà (tooltip uniforme).
			// El 0 d'OSM de la restauració es mostra «sense dada» (buit de mapejat, no absència real).
			const value = inBerg
				? mapValue(indicator, row?.values?.[indicator])
				: covered
					? (catValues?.[ine5]?.[indicator] ?? null)
					: null;
			const cs = row?.values?.confianca_score;
			// Presència estimada EN RANG per als munis coberts de fora del Berguedà (Nivell C).
			const cover = covered ? (pernocta?.[ine5] ?? null) : null;
			return {
				ine5,
				nom: (feat.properties?.nom as string) ?? row?.nom ?? cover?.nom ?? ine5,
				value,
				conf: inBerg
					? ((row?.values?.confianca as string | undefined) ?? null)
					: covered
						? (catValues?.[ine5]?.conf ?? null)
						: null,
				confScore: typeof cs === 'number' ? cs : null,
				inBergueda: inBerg,
				pernocta: cover,
				x: point.x,
				y: point.y
			};
		};

		for (const layer of interactive) {
			map.on('mousemove', layer, (e) => {
				if (!map || granularity !== 'municipi') return; // a cobertura no hi ha tooltip de municipi
				const feat = e.features?.[0] as MapGeoJSONFeature | undefined;
				if (!feat) return;
				const ine5 = (feat.properties?.ine5 as string) ?? '';
				if (hoverId && hoverId !== ine5) {
					map.setFeatureState({ source: SRC, id: hoverId }, { hover: false });
				}
				hoverId = ine5;
				map.setFeatureState({ source: SRC, id: ine5 }, { hover: true });
				map.getCanvas().style.cursor = 'pointer';
				onhover?.(buildHover(feat, e.point));
			});

			map.on('mouseleave', layer, () => {
				if (!map) return;
				if (hoverId) map.setFeatureState({ source: SRC, id: hoverId }, { hover: false });
				hoverId = null;
				map.getCanvas().style.cursor = '';
				onhover?.(null);
			});

			map.on('click', layer, (e) => {
				if (!map || granularity !== 'municipi') return;
				const feat = e.features?.[0] as MapGeoJSONFeature | undefined;
				const ine5 = (feat?.properties?.ine5 as string) ?? '';
				if (selected) map.setFeatureState({ source: SRC, id: selected }, { selected: false });
				if (coarse) {
					// Mòbil: el tap selecciona i MOSTRA la targeta; no navega (ho fa el CTA de la targeta).
					selected = ine5 || null;
					if (selected) map.setFeatureState({ source: SRC, id: selected }, { selected: true });
					if (feat) onhover?.(buildHover(feat, e.point));
					return;
				}
				selected = selected === ine5 ? null : ine5;
				if (selected) map.setFeatureState({ source: SRC, id: selected }, { selected: true });
				onselect?.(selected);
			});
		}

		// Mòbil: tap al fons (sense municipi) → tanca la targeta i treu la selecció.
		map.on('click', (e) => {
			if (!map || !coarse) return;
			if (map.queryRenderedFeatures(e.point, { layers: interactive }).length) return;
			if (selected) {
				map.setFeatureState({ source: SRC, id: selected }, { selected: false });
				selected = null;
			}
			onhover?.(null);
		});
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
			map.setPaintProperty(FILL, 'fill-color', fillColorExpression(c, key) as never);
		}
		// Els coberts segueixen el MATEIX indicador (mateixa classificació); re-pinta en canviar-lo.
		if (map.getLayer(COVERED)) {
			map.setPaintProperty(COVERED, 'fill-color', coveredColorExpr(c, key) as never);
		}
	});

	// Reactiu: en canviar de granularitat, commuta visibilitat de capes + re-enquadra.
	$effect(() => {
		const g = granularity;
		if (!map || !ready) return;
		applyGranularity(g);
	});

	onMount(() => {
		// Si la inicialització de MapLibre falla, no deixem la UI penjada al teló de càrrega:
		// l'error es propaga a la consola perquè es vegi a producció (en lloc d'un "Carregant…" mut).
		init().catch((err) => console.error('[ChoroplethMap] init failed:', err));
	});

	onDestroy(() => {
		resizeObs?.disconnect();
		resizeObs = null;
		map?.remove();
		map = null;
	});
</script>

<div
	class="map"
	bind:this={container}
	role="application"
	aria-label="Mapa de Catalunya amb el Berguedà actiu"
>
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
