<script lang="ts">
	/**
	 * FITXA DE MUNICIPI (`/municipi/[ine5]` · `/es/municipi/[ine5]`).
	 *
	 * Fitxa amb DADES OFICIALS per a qualsevol municipi de Catalunya: totes les mètriques del
	 * municipi agrupades editorialment (demografia i habitatge, transformació demogràfica,
	 * turisme reglat, senyals físics), cadascuna amb la seva PROCEDÈNCIA (punt mesura/inferència)
	 * i la unitat del contracte.
	 *
	 * EL MODEL D'ESTIMACIÓ DE PERNOCTA ESTÀ APARCAT del web (vot de Bea 2026-07-16 ·
	 * `docs/ajuntaments/gorra-alcalde-pobla.md` §1): cap banda, cap registre, cap veu del gap.
	 * La presència es mostra NOMÉS com a dada oficial (ETCA, Idescat) o «sense dada oficial»
	 * als municipis on Idescat no la publica (<1.000 hab). El rastre metodològic del model viu
	 * a /metodologia (annex de recerca) i a l'experiment geo-rag.
	 *
	 * Disciplina de dades (com al Mapa/Glossari): CAP xifra, etiqueta, unitat ni font es
	 * codifica a la UI — tot surt del dataset real (= contracte semàntic) via `formatMetric`/`pick`.
	 * La procedència (slate=mesurada, porpra=inferència) la dedueix `provenanceOf` del `source`.
	 * El 0 d'OSM de la restauració es mostra «sense dada», no «0,0» (honestedat).
	 *
	 * Si l'`ine5` no és al dataset (resta de Catalunya) → estat AMABLE «sense dades encara» (mateix
	 * gest que el tooltip «fora del Berguedà» del mapa), mai una fitxa buida ni un error lleig.
	 *
	 * Chrome del design-system (.ap-hero + .ds-main/.ds-sec); el text nou és i18n ca/es.
	 */
	import { goto, replaceState } from '$app/navigation';
	import { page } from '$app/state';
	import { browser } from '$app/environment';
	import ContourField from '$lib/components/ContourField.svelte';
	import { currentLocale, pick, localizeHref } from '$lib/i18n';
	import { formatMetric, formatDecimal, formatInteger } from '$lib/format';
	import { provenanceOf } from '$lib/map/provenance';
	import { toSlug, slugForIne5, nomCanonic } from '$lib/contract/slug';
	import Espina from '$lib/components/Espina.svelte';
	import MirallConstel from '$lib/components/MirallConstel.svelte';
	import { m } from '$lib/paraglide/messages';
	import type { Frescor, MetricDef, MetricKey, MetricValue, MunicipiRow } from '$lib/contract/types';
	import type { LectTo } from '$lib/contract/lectures';
	import { GOVERN_KPIS, provenanceLine } from '$lib/govern/kpis';
	import type { GovernEntry } from '$lib/contract/govern';
	import type { AturPunt, TaulerEntry, TaulerMeta, TendenciaEntry } from '$lib/contract/tauler';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const row = $derived(data.row);
	const ine5 = $derived(data.ine5);
	// PRESÈNCIA OFICIAL (ETCA, Idescat): l'única dada de presència que la fitxa mostra (model
	// aparcat). null = Idescat no la publica (<1.000 hab) → «sense dada oficial».
	const etca = $derived(data.etca ?? null);
	const isBergueda = $derived(data.isBergueda ?? false); // pilot profund vs espina CAT (lede honest)
	// ── Tauler de dades (D8 · E1 de Bea) ─────────────────────────────────────────────────────
	// UNA SOLA VISTA. El commutador Veïnal|Govern s'ha retirat: el que era «mode govern» —KPIs
	// amb rang comarcal, ordre fix, política editorial— ÉS ara la fitxa. Com que ja no hi ha dues
	// vistes, la paritat de xifres (§10.1) deixa de ser un risc: no hi ha cap segona lectura amb
	// què discrepar. El rang «k de n» es LLEGEIX del mart via `data.govern` (D4) — el front no
	// calcula cap rang (C6 §4).
	const govern = $derived<GovernEntry | null>(data.govern ?? null);
	// TAULER v2 (D7 · E4/E6/E11): atur mensual + tendència amb PERÍODE. Mateixa frontera dura que
	// el rang: es LLEGEIX, no es calcula (cap delta, cap direcció, cap interval es deriva aquí).
	const tauler = $derived<TaulerEntry | null>(data.tauler ?? null);
	const taulerMeta = $derived<TaulerMeta | null>(data.taulerMeta ?? null);
	// Compatibilitat d'enllaços ja compartits: `?vista=govern` NO trenca res (la pàgina és la
	// mateixa amb i sense el paràmetre). En hidratar, si el paràmetre hi és, es neteja de la URL
	// amb `replaceState` (no navega, no toca l'historial) perquè l'enllaç canònic quedi net.
	$effect(() => {
		if (!browser) return;
		if (!page.url.searchParams.has('vista')) return;
		const u = new URL(page.url);
		u.searchParams.delete('vista');
		replaceState(`${u.pathname}${u.search}${u.hash}`, page.state);
	});
	// Espina territorial: comarca/vegueria del muni + municipis veïns de la comarca (navegació).
	const territori = $derived(data.territori);
	const veins = $derived(data.veins ?? []);
	const veinsTotal = $derived(data.veinsTotal ?? 0);
	const locale = $derived(currentLocale());
	// Breadcrumb navegable: Catalunya › vegueria › comarca › municipi (l'últim és l'actual, sense href).
	const espinaTrail = $derived.by(() => {
		const t: { label: string; href?: string }[] = [
			{ label: m.espina_catalunya(), href: localizeHref('/') }
		];
		if (territori?.vegueria)
			t.push({ label: territori.vegueria, href: localizeHref(`/vegueria/${toSlug(territori.vegueria)}`) });
		if (territori?.comarca)
			t.push({ label: territori.comarca, href: localizeHref(`/comarca/${toSlug(territori.comarca)}`) });
		t.push({ label: muniNom });
		return t;
	});

	// ── Lectura-IA (§3) ─────────────────────────────────────────────────────────────────────
	// Branca del locale actiu de l'artefacte `lectures.bergueda.json` (la genera gen_fitxa.py:
	// escriptor opus-4.8 es → traductor sonnet-4.6 ca, amb verificació de xifres). Si no hi és
	// o és reserva (`_gen="fallback"`), la fitxa degrada: cap veredicte/lectura narrativa, només
	// els cinc números i la maquinària. Mai una al·lucinació, mai una pantalla trencada.
	const lectura = $derived(locale === 'es' ? (data.lectura?.es ?? null) : (data.lectura?.ca ?? null));
	const hasLectura = $derived(!!lectura && lectura._gen !== 'fallback');
	const veredicte = $derived(hasLectura && lectura?.veredicte?.text ? lectura.veredicte : null);
	const lectClaims = $derived(hasLectura ? (lectura?.lectures ?? null) : null);
	const hasCiutadania = $derived((lectClaims?.ciutadania?.length ?? 0) > 0);
	const hasVisitant = $derived((lectClaims?.visitant?.length ?? 0) > 0);
	const hasLectures = $derived(hasCiutadania || hasVisitant);
	const contraLectura = $derived(
		hasLectura && lectura?.contra_lectura?.text ? lectura.contra_lectura : null
	);
	// Perfils de lectura (ciutadania + visitant): cada perfil amb les seves afirmacions. Es
	// renderitzen TOTS DOS llistats (estàtics) i la pestanya activa només commuta quin és visible
	// via `hidden` — mateix mecanisme provat que el toggle «mode dades» (`open={modeDades}`).
	const lectGroups = $derived(
		[
			{ key: 'ciutadania' as const, label: m.muni_lect_tab_ciutadania(), claims: lectClaims?.ciutadania ?? [] },
			{ key: 'visitant' as const, label: m.muni_lect_tab_visitant(), claims: lectClaims?.visitant ?? [] }
		].filter((g) => g.claims.length > 0)
	);

	// Naturalesa epistèmica d'un claim → etiqueta + punt de procedència (mateix codi que el mapa).
	function toLabel(to: LectTo): string {
		return to === 'mesura'
			? m.muni_to_mesura()
			: to === 'inferencia'
				? m.muni_to_inferencia()
				: m.muni_to_interpretacio();
	}
	const toDot = (to: LectTo) => (to === 'mesura' ? 'dot--measured' : 'dot--derived');

	// Claus d'evidència → etiquetes humanes. Primer mètriques del contracte; després els fets
	// COMPOSTOS (pernocta en rang, validació ETCA, tipus de territori) que el relat cita però que
	// no són mètriques; la resta, tal qual (mai una clau snake_case crua a l'usuari si es pot evitar).
	const EV_COMPOSITE: Record<string, () => string> = {
		pernocta_rang: () => m.muni_ev_pernocta_rang(),
		etca_idescat: () => m.muni_ev_etca_idescat(),
		tipus_territorial: () => m.muni_ev_tipus_territorial()
	};
	function evidLabels(keys: string[] | undefined): string[] {
		return (keys ?? []).map((k) => {
			const def = dataset.metrics[k as MetricKey];
			if (def) return pick(def.label, locale);
			return EV_COMPOSITE[k]?.() ?? k;
		});
	}

	// Preguntes suggerides → enllaç a Pregunta-li amb la consulta precarregada (?q=). Capades a 6.
	const preguntesFlat = $derived.by<string[]>(() => {
		const p = hasLectura ? lectura?.preguntes : null;
		if (!p) return [];
		return [...(p.propies ?? []), ...(p.comarca ?? []), ...(p.miralls ?? [])]
			.map((q) => q.trim())
			.filter(Boolean)
			.slice(0, 6);
	});
	const preguntaHref = (q: string) => localizeHref(`/pregunta-li?q=${encodeURIComponent(q)}`);

	// «Mode dades» (spec §1.2): desplega la P3 (la maquinària) per defecte i es recorda.
	let modeDades = $state(browser ? localStorage.getItem('rdg-dades') === '1' : false);
	$effect(() => {
		if (browser) localStorage.setItem('rdg-dades', modeDades ? '1' : '0');
	});

	// ── Blocs editorials que cobreixen TOT el catàleg del contracte ──────────────────────────
	// Mateix esperit que la metodologia/Resum, però aquí l'objectiu és NO deixar fora cap mètrica
	// del municipi. Les claus van en ordre editorial (de mesurat → inferit). El subtítol distingeix
	// senyal físic (mesura) d'inferència (les 3 capes), com els subgrups del Resum.
	type FichaBlock = {
		ref: string;
		title: () => string;
		sub?: () => string;
		keys: MetricKey[];
	};
	const blocks: FichaBlock[] = [
		{
			ref: 'A',
			title: () => m.muni_blk_demografia(),
			keys: ['poblacio', 'hab_total', 'hab_principal', 'hab_noprincipal', 'pct_noprincipal', 'hab_per_hab', 'index_envelliment']
		},
		{
			ref: 'B',
			title: () => m.muni_blk_origen(),
			sub: () => m.muni_blk_origen_sub(),
			keys: [
				'poblacio_nascuda_catalunya',
				'poblacio_nascuda_resta_espanya',
				'poblacio_nascuda_estranger',
				'pct_nascuda_estranger',
				'pct_nacionalitat_estrangera',
				'bretxa_naturalitzacio',
				'delta_pct_estrangera_finestra',
				'confianca_origen'
			]
		},
		{
			ref: 'C',
			title: () => m.muni_blk_turisme(),
			keys: ['rtc_total', 'rtc_hut', 'rtc_per_1000hab', 'rtc_per_100hab_viv']
		},
		{
			ref: 'D',
			title: () => m.muni_blk_fisics(),
			sub: () => m.resum_grp_fisics(),
			keys: ['kg_hab_any', 'kwh_hab', 'vidre_hab', 'restauracio_estab', 'restauracio_per_1000hab']
		}
	];
	// (El bloc E «les 3 capes» —pernocta, càrrega, índex de turisme— està APARCAT amb el model.)

	// Infra-mapeig OSM: vidre alt amb restauració = 0 → el 0 és buit de mapa, no absència real.
	const osmSospita = $derived(
		typeof row?.values.vidre_hab === 'number' &&
			row.values.vidre_hab > 30 &&
			(row?.values.restauracio_estab === 0 || row?.values.restauracio_estab == null)
	);

	const highlightRows = new Set<MetricKey>([
		'pct_noprincipal',
		'rtc_per_1000hab',
		'bretxa_naturalitzacio'
	]);

	// Mètriques on un 0 NO és dada sinó absència de mapeig (recompte mínim d'OSM, no cens): es
	// mostren «sense dada», no «0,0». Mateixa regla d'honestedat que el Resum i el mapa.
	const ZERO_IS_ABSENT = new Set<MetricKey>(['restauracio_per_1000hab', 'restauracio_estab']);

	// Unitats curtes editorials a la línia de cada xifra (com al Resum: el contracte dona la unitat
	// llarga; aquí la forma curta de la captura). Buida = sense unitat curta (cau a la del contracte).
	const SHORT_UNIT: Partial<Record<MetricKey, string>> = {
		poblacio: 'hab.',
		hab_total: 'hab.',
		hab_principal: 'hab.',
		hab_noprincipal: 'hab.',
		poblacio_nascuda_catalunya: 'hab.',
		poblacio_nascuda_resta_espanya: 'hab.',
		poblacio_nascuda_estranger: 'hab.',
		bretxa_naturalitzacio: 'pts',
		delta_pct_estrangera_finestra: 'pts',
		rtc_per_1000hab: '‰'
	};

	const provDotClass = (p: ReturnType<typeof provenanceOf>) =>
		p === 'derived' ? 'dot--derived' : 'dot--measured';

	// Valor efectiu d'una mètrica: aplica la regla d'honestedat del 0-com-a-buit (OSM).
	function effectiveValue(r: MunicipiRow, key: MetricKey): MetricValue | undefined {
		const v = r.values[key];
		if (ZERO_IS_ABSENT.has(key) && v === 0) return null;
		return v;
	}

	// Formata SENSE el símbol de percentatge (el «%» el posa el markup com a unitat petita, com al
	// Resum, per no duplicar-lo). La resta de formats deleguen a formatMetric (contracte).
	function fmtValue(value: MetricValue | undefined, def: MetricDef): string {
		if (value === null || value === undefined) return m.value_not_available();
		if (def.format === 'percent' && typeof value === 'number') {
			return formatDecimal(value, locale, 1);
		}
		return formatMetric(value, def, locale) ?? m.value_not_available();
	}

	// Valor d'una mètrica per al municipi, formatat al locale (sense unitat).
	function fmt(r: MunicipiRow, key: MetricKey): string {
		return fmtValue(effectiveValue(r, key), dataset.metrics[key]);
	}

	// Procedència d'una mètrica per al municipi (per pintar el punt). Valor absent (incl. 0-OSM) →
	// «sense dada».
	function prov(r: MunicipiRow, key: MetricKey) {
		const v = effectiveValue(r, key);
		return provenanceOf(dataset.metrics[key], v !== null && v !== undefined);
	}

	// Font · data del contracte (per a la línia de procedència de cada bloc).
	function srcLine(def: MetricDef): string {
		return def.date ? `${def.source} · ${def.date}` : def.source;
	}

	// ── Ajudes del tauler de dades ────────────────────────────────────────────────────────────
	// Els 4 blocs de la gorra §3 (ordre FIX, C6 §7 — cap KPI es reordena per enterrar-lo). El bloc
	// D és, des de l'E2 de Bea, el grup de «vida»: residus + elèctric domèstic + vidre junts.
	const GOV_GROUPS = [
		{ g: 'A', label: () => m.gov_grp_a() },
		{ g: 'B', label: () => m.gov_grp_b() },
		{ g: 'C', label: () => m.gov_grp_c() },
		{ g: 'D', label: () => m.gov_grp_d() }
	] as const;
	const kpisOf = (g: string) => GOVERN_KPIS.filter((k) => k.group === g);
	// Def del contracte per a una clau (les claus del descriptor són strings JS).
	const gDef = (key: string): MetricDef => dataset.metrics[key as MetricKey];
	// Unitat curta editorial per a la targeta (mateixa pràctica que SHORT_UNIT; % pel format).
	const GOV_UNIT: Record<string, string> = {
		poblacio: 'hab.',
		renda_neta_persona: '€',
		kwh_hab: 'kWh',
		kg_hab_any: 'kg',
		vidre_hab: 'kg',
		rtc_per_1000hab: '‰',
		// D11 · les tres xifres de lloc de naixement són persones, com la població de la qual són
		// partició (nascuts a Catalunya + resta d'Espanya + estranger = `poblacio`, exacte als 947).
		poblacio_nascuda_catalunya: 'hab.',
		poblacio_nascuda_resta_espanya: 'hab.',
		poblacio_nascuda_estranger: 'hab.'
	};
	function gUnit(key: string): string {
		if (gDef(key)?.format === 'percent') return '%';
		return GOV_UNIT[key] ?? '';
	}

	// ── D11 · NOTES DE LÍMIT per targeta (E11) ────────────────────────────────────────────────
	// Alguns límits no es dedueixen de la dada i s'han de DIR: que d'una xifra en tenim la foto i
	// no la sèrie, o que la sèrie que acompanya una targeta mesura una altra cosa que l'etiqueta
	// del costat. El descriptor (`kpis.js`) només porta la CLAU i18n; el text viu als catàlegs
	// ca/es, com la resta del copy. Una clau sense entrada aquí no pintaria res: `verify-govern`
	// comprova que totes les que el descriptor declara existeixen i estan cablejades.
	const GOV_NOTE: Record<string, () => string> = {
		gov_naix_foto: () => m.gov_naix_foto(),
		gov_nac_serie_es_nacionalitat: () => m.gov_nac_serie_es_nacionalitat()
	};
	const govNote = (k: string | undefined): string => (k ? (GOV_NOTE[k]?.() ?? '') : '');
	// Prefixa el signe a una variació ja formatada (la negativa ja porta el «−» d'Intl).
	function signed(s: string): string {
		return s.startsWith('-') || s.startsWith('−') ? s : `+${s}`;
	}

	// ── D9 · TENDÈNCIA (E6/E11) ───────────────────────────────────────────────────────────────
	// Quatre regles de pintura, i totes surten de la dada, no del copy:
	//  1. Cap fletxa sense període: els dos períodes vénen del JSON (`periode_actual` /
	//     `periode_anterior`) i es pinten SEMPRE. Cap període escrit a mà a un missatge.
	//  2. L'atur porta DUES comparacions i sovint apunten en sentits contraris (la Pobla, juny
	//     2026: +4 contra maig, −3 contra juny de 2025). Es pinten LES DUES. Triar-ne una seria
	//     triar la narrativa.
	//  3. `sense_serie` → es pinta el `motiu` literal del mart. Mai una fletxa grisa, un guionet
	//     mut ni un 0.
	//  4. `delta_emmascarat` → INTERVAL [min,max], mai un número; i si l'interval travessa el
	//     zero, el mart diu `indeterminat` i aquí no es pinta cap direcció.

	/** Període del JSON → text llegible. `2026-06` → «juny 2026»; `2025` → `2025`. */
	function fmtPeriode(p: string | null): string {
		if (!p) return '';
		const mm = /^(\d{4})-(\d{2})$/.exec(p);
		if (!mm) return p;
		const d = new Date(Date.UTC(Number(mm[1]), Number(mm[2]) - 1, 1));
		return new Intl.DateTimeFormat(locale === 'es' ? 'es-ES' : 'ca-ES', {
			month: 'long',
			year: 'numeric',
			timeZone: 'UTC'
		}).format(d);
	}

	/** Entrades de tendència d'una clau (llista: l'atur en té dues). Buida si no n'hi ha cap. */
	function trendsOf(key: string | undefined): TendenciaEntry[] {
		if (!key) return [];
		return tauler?.tendencia?.[key] ?? [];
	}

	/** Fletxa segons la direcció AFIRMADA pel mart. `indeterminat` no en té: no es pot afirmar. */
	function trendArrow(dir: TendenciaEntry['direccio']): string {
		return dir === 'puja' ? '↑' : dir === 'baixa' ? '↓' : dir === 'igual' ? '=' : '·';
	}

	/** Unitat del delta (l'emet el mart); només se'n localitza l'etiqueta curta. */
	function trendUnit(u: string | null): string {
		if (u === 'persones') return m.gov_tend_u_persones();
		if (u === 'punts_percentuals') return m.gov_tend_u_punts();
		return u ?? '';
	}

	/** Un número del delta segons la seva unitat (enter per a persones, 2 decimals per a punts). */
	function fmtDeltaNum(v: number, unit: string | null): string {
		return unit === 'punts_percentuals' ? formatDecimal(v, locale, 2) : formatInteger(v, locale);
	}

	/**
	 * Magnitud del canvi: número si el mart en dona un; INTERVAL si el «<5» l'ha emmascarat.
	 * Mai un 0 de consol, mai un buit, mai un NaN (doctrina del «<5», D1/D7).
	 */
	function trendMagnitude(e: TendenciaEntry): string {
		if (e.delta !== null) return signed(fmtDeltaNum(e.delta, e.unitat_delta));
		if (e.delta_min !== null && e.delta_max !== null) {
			return m.gov_tend_interval({
				min: signed(fmtDeltaNum(e.delta_min, e.unitat_delta)),
				max: signed(fmtDeltaNum(e.delta_max, e.unitat_delta))
			});
		}
		return m.value_not_available();
	}

	/** Etiqueta de QUINA comparació és (l'enum el fixa el mart; aquí només se'n tradueix el nom). */
	function trendCmpLabel(c: TendenciaEntry['comparacio']): string {
		if (c === 'mes_anterior') return m.gov_tend_cmp_mes();
		if (c === 'mateix_mes_any_anterior') return m.gov_tend_cmp_any();
		if (c === 'finestra_anual') return m.gov_tend_cmp_finestra();
		return '';
	}

	// ── D9 · FRESCOR PER TARGETA (E5) ─────────────────────────────────────────────────────────
	// Regla vinculant: la frescor va A CADA TARGETA, mai a un peu de pàgina global. Els vintages
	// NO són iguals (població 2025, habitatges 2021) i una sola data els aplanaria en una mentida.
	// Es diu la veritat sencera: cadència, darrera càrrega i SI hi ha procés que la refresqui
	// (avui, 1 font de 10). `actualitzacio: null` (derivades sense `origin_source` al contracte)
	// tampoc s'arrodoneix a un «anual» de consol: es diu que no està declarada.
	function cadenciaLabel(c: string | null): string {
		if (c === 'mensual') return m.gov_frescor_mensual();
		if (c === 'anual') return m.gov_frescor_anual();
		if (c === 'puntual') return m.gov_frescor_puntual();
		if (c === 'irregular') return m.gov_frescor_irregular();
		if (!c) return m.gov_frescor_nd();
		return c;
	}
	/** Línia de frescor d'una targeta: cadència · darrera càrrega · procés (o la seva absència). */
	function frescorLine(f: Frescor | null | undefined): string {
		if (!f) return '';
		const parts = [cadenciaLabel(f.actualitzacio)];
		if (f.darrera_carrega) parts.push(m.gov_frescor_carrega({ data: f.darrera_carrega }));
		if (f.proces_refresc === 'cap') parts.push(m.gov_frescor_sense_proces());
		else if (f.proces_refresc) parts.push(m.gov_frescor_amb_proces());
		return parts.join(' · ');
	}

	// ── D9 · ATUR (E4) ────────────────────────────────────────────────────────────────────────
	const atur = $derived(tauler?.atur ?? null);
	const aturFrescor = $derived(taulerMeta?.atur?.frescor ?? null);

	/** Valor d'un punt d'atur: xifra, o INTERVAL si el SEPE l'emmascara. Mai un zero. */
	function aturValor(p: AturPunt): string {
		if (p.valor !== null) return formatInteger(p.valor, locale);
		return m.gov_tend_interval({
			min: formatInteger(p.min, locale),
			max: formatInteger(p.max, locale)
		});
	}

	/**
	 * Sparkline de la sèrie d'atur (25 mesos), SVG inline sense cap dependència.
	 * Honestedat del traç: un mes emmascarat NO és un punt —seria inventar-ne el valor—, és una
	 * BANDA vertical [min,max]; i la línia es trenca allà on no hi ha xifra exacta, en comptes de
	 * travessar-la com si la sabéssim.
	 */
	const SPARK_W = 260;
	const SPARK_H = 46;
	const spark = $derived.by(() => {
		const s = atur?.serie ?? [];
		if (s.length < 2) return null;
		const lo = Math.min(...s.map((p) => p.min));
		const hi = Math.max(...s.map((p) => p.max));
		const span = hi - lo || 1;
		const x = (i: number) => (i / (s.length - 1)) * SPARK_W;
		const y = (v: number) => SPARK_H - ((v - lo) / span) * SPARK_H;
		// Segments continus només entre mesos amb xifra exacta consecutius (la sèrie es trenca
		// als emmascarats: no s'interpola sobre el que no sabem).
		const segs: string[] = [];
		let cur: string[] = [];
		s.forEach((p, i) => {
			if (p.valor === null) {
				if (cur.length > 1) segs.push(cur.join(' '));
				cur = [];
			} else cur.push(`${x(i).toFixed(1)},${y(p.valor).toFixed(1)}`);
		});
		if (cur.length > 1) segs.push(cur.join(' '));
		const bands = s
			.map((p, i) => (p.valor === null ? { x: x(i), y1: y(p.max), y2: y(p.min) } : null))
			.filter((b): b is { x: number; y1: number; y2: number } => b !== null);
		const last = s[s.length - 1];
		return {
			segs,
			bands,
			lo,
			hi,
			first: s[0].date,
			lastDate: last.date,
			lastPt: last.valor !== null ? { x: x(s.length - 1), y: y(last.valor) } : null
		};
	});

	// Pobles mirall a escala Catalunya: bessons funcionals (no geogràfics) de tot el país, resolts al
	// loader des de l'artefacte `municipis-mirall.json` (Nivell C). Per a QUALSEVOL muni, no només Berguedà.
	// (La confiança del model —score, divergència, validats— està APARCADA amb el model: les dades
	// oficials porten font i data, no bandera.)
	const miralls = $derived(data.miralls ?? []);

	// Nom del municipi (topònim, igual en ambdós locales): del dataset (Berguedà) o del CATÀLEG de
	// tota Catalunya (`data.nom`, qualsevol poble); en últim cas, el codi.
	// D9 · serrell: el nom arriba en DUES formes segons la fila —«Pobla de Lillet, la» (marts) vs
	// «la Pobla de Lillet» (geometria oficial i tauler)—. La clau del join és l'`ine5`, així que
	// cap xifra en depèn; però el títol es pinta en la forma corrent, no en la d'índex.
	const muniNom = $derived(nomCanonic(row?.nom ?? data.nom ?? ine5 ?? ''));

	// ── Selector de municipi: salta a un altre dels 31 (ordenat per nom, localitzat) ──────────
	// Es deriva del dataset (no llista codificada). El canvi navega a la fitxa corresponent.
	// Es MOSTRA la forma corrent («la Pobla de Lillet») però s'ORDENA per la forma d'índex del
	// dataset («Pobla de Lillet, la»), que és justament per a què serveix: l'article final no ha
	// d'apilar mig Berguedà sota la lletra «L».
	const muniOptions = $derived.by(() => {
		const items = Object.values(dataset.municipis).map((mr) => ({
			ine5: mr.ine5,
			nom: nomCanonic(mr.nom),
			ordre: mr.nom
		}));
		const coll = new Intl.Collator(locale === 'es' ? 'es-ES' : 'ca-ES');
		return items.sort((a, b) => coll.compare(a.ordre, b.ordre));
	});
	function onPickMuni(e: Event) {
		const v = (e.currentTarget as HTMLSelectElement).value; // value = ine5 (clau interna)
		if (v) goto(localizeHref(`/municipi/${slugForIne5(v, dataset)}`));
	}

	// Corbes del hero (rètols editorials del full topogràfic; no xifres de cap municipi concret).
	const heroSummits = [
		{ cx: 895, cy: 148, r0: 15, step: 22, rings: 10, sq: 0.97, seed: 0.9, lt: 0.03 },
		{ cx: 1078, cy: 300, r0: 13, step: 20, rings: 8, sq: 1.06, seed: 2.7, lt: 0.1 }
	];
	const heroDivis = { cx: 768, cy: 228, r: 150, sq: 1.18, seed: 1.2 };
	const heroLabels = ['INE', 'padró', 'font', '947', 'mètriques', 'procedència', 'fitxa'];
</script>

<!-- Una fila d'indicador (clau + punt de procedència + valor amb unitat curta). Reutilitza la
     pell de `.ex__row` del Resum perquè la fitxa sigui visualment idèntica. -->
{#snippet fichaRow(r: MunicipiRow, key: MetricKey)}
	{@const def = dataset.metrics[key]}
	{@const isPct = def.format === 'percent'}
	{@const unit = SHORT_UNIT[key]}
	<div class="ex__row" class:hl={highlightRows.has(key)}>
		<span class="k"
			><span class="pd {provDotClass(prov(r, key))}"></span><span>{pick(def.label, locale)}</span
			></span
		>
		<span class="val"
			>{fmt(r, key)}{#if isPct}<span class="u">%</span>{:else if unit}<span class="u">{unit}</span
				>{/if}</span
		>
	</div>
{/snippet}

<!-- TENDÈNCIA d'una targeta (D9 · E6/E11). Una entrada = una comparació; l'atur en té DUES i
     es pinten totes. Cap fletxa sense el seu període, i el període surt del JSON.
     `sense_serie` → el motiu literal del mart; mai una fletxa grisa ni un 0. -->
{#snippet tendencia(entries: TendenciaEntry[])}
	{#if entries.length}
		<div class="gov-tend">
			{#each entries as e, i (e.comparacio ?? `s${i}`)}
				{#if e.estat === 'sense_serie'}
					<!-- E11 · l'absència es DECLARA amb el seu motiu (la població i les franges hi són
					     per límit de la font: l'API d'EMEX no serveix sèrie). El motiu és dada del
					     mart i encara arriba només en català → handoff a Sondeig per localitzar-lo. -->
					<p class="gov-tend__no" lang="ca">
						<span class="gov-tend__nok">{m.gov_tend_sense_serie()}</span>{e.motiu}
					</p>
				{:else}
					<p class="gov-tend__l">
						<span class="gov-tend__ar gov-tend__ar--{e.direccio ?? 'nd'}" aria-hidden="true"
							>{trendArrow(e.direccio)}</span
						>
						{#if e.direccio === 'indeterminat'}
							<span class="gov-tend__ind">{m.gov_tend_indeterminat()}</span>
							<span class="gov-tend__d">{trendMagnitude(e)} {trendUnit(e.unitat_delta)}</span>
						{:else}
							<span class="gov-tend__d">{trendMagnitude(e)} {trendUnit(e.unitat_delta)}</span>
						{/if}
						<span class="gov-tend__p"
							>{trendCmpLabel(e.comparacio)} · {fmtPeriode(e.periode_anterior)} → {fmtPeriode(
								e.periode_actual
							)}</span
						>
					</p>
				{/if}
			{/each}
		</div>
	{:else}
		<!-- Ni sèrie ni motiu: la mètrica no és a `mart_tendencia`. Es diu, en comptes de callar
		     (una absència muda es llegeix com un «no ha canviat»). Handoff a Sondeig. -->
		<p class="gov-tend__no"><span class="gov-tend__nok">{m.gov_tend_no_declarada()}</span></p>
	{/if}
{/snippet}

<!-- FRESCOR d'una targeta (D9 · E5): cadència · darrera càrrega · procés que la refresca (o la
     seva absència declarada). Per targeta i mai global: els vintages no són iguals. -->
{#snippet frescor(f: Frescor | null | undefined)}
	{#if f}
		<p class="gov-kpi__fresc">{frescorLine(f)}</p>
	{/if}
{/snippet}

<svelte:head>
	<title>{muniNom} · {m.muni_title()} · {m.app_name()}</title>
	<meta name="description" content={m.muni_meta_desc({ nom: muniNom })} />
</svelte:head>

<section data-view="municipi" class="on">
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
				<span>{m.muni_eyebrow_a()}</span><span class="sep">/</span><span
					>{m.muni_eyebrow_b({ comarca: territori?.comarca ?? pick(dataset.comarca.label, locale) })}</span
				><span class="sep">/</span><span>INE {ine5}</span>
			</p>
			<h1>{muniNom}</h1>
			{#if isBergueda}
				<p class="lede">{m.muni_lede()}</p>
			{:else if row}
				<p class="lede">{m.muni_lede_cat()}</p>
			{:else}
				<p class="lede">{m.muni_outside_lede()}</p>
			{/if}
		</div>
	</div>

	<div class="ds-main">
		<!-- Espina territorial NAVEGABLE: Catalunya › vegueria › comarca › municipi (el muni és l'actual). -->
		<Espina trail={espinaTrail} />

		<!-- Selector per saltar a un altre municipi del Berguedà (sempre disponible). -->
		<section class="ds-sec" style="border-top:none">
			<div class="muni-pick">
				<label for="muni-select">{m.muni_pick_label()}</label>
				<select id="muni-select" class="select" value={ine5} onchange={onPickMuni}>
					{#each muniOptions as o (o.ine5)}
						<option value={o.ine5}>{o.nom}</option>
					{/each}
				</select>
				<a class="muni-pick__map" href={localizeHref('/mapa')}>{m.muni_pick_map()}</a>
			</div>
		</section>

		{#if row}
			<!-- TAULER DE DADES (D8 · E1): UNA SOLA VISTA. Els KPIs de la gorra §3 al capdamunt, amb
			     el rang comarcal «k de n» LLEGIT del mart (C6 §4, mai calculat aquí) i, a cada
			     targeta, la seva procedència: FONT (mesurada) o FÓRMULA (inferida) — regla de ferro
			     de Bea (C6 §8.1). Abast del rang = Berguedà (C6 §1.2), que és on `data.govern` existeix;
			     per això el tauler es manté al pilot i la resta de Catalunya conserva la seva espina. -->
			{#if isBergueda}
				<section class="ds-sec gov-board" aria-labelledby="gov-board-h">
					<div class="ds-sec__hd"><span class="ref">◆</span><h2 id="gov-board-h">{m.gov_board_title()}</h2></div>
					<p class="muni-sec__sub">{m.gov_board_sub()}</p>
					{#each GOV_GROUPS as grp (grp.g)}
						<h3 class="gov-grp">{grp.label()}</h3>
						<div class="gov-grid tnum">
							{#each kpisOf(grp.g) as kpi (kpi.kind + (kpi.key ?? ''))}
								{#if kpi.kind === 'metric' && kpi.key}
									{@const def = gDef(kpi.key)}
									{@const cell = govern?.metrics?.[kpi.key] ?? null}
									{@const prv = provenanceLine(def)}
									<article class="gov-kpi">
										<p class="gov-kpi__lab">
											<span class="pd {provDotClass(prov(row, kpi.key as MetricKey))}"></span>{pick(def.label, locale)}
										</p>
										<p class="gov-kpi__v">
											{fmt(row, kpi.key as MetricKey)}{#if gUnit(kpi.key)}<span class="u">{gUnit(kpi.key)}</span>{/if}
										</p>
										<!-- E6/E11 · la tendència, amb el seu període SEMPRE (o el motiu de no tenir-ne). -->
										{@render tendencia(trendsOf(kpi.trendKey ?? kpi.key))}
										<!-- D11 · el límit que la dada NO diu de si mateixa: va DARRERE la tendència
										     perquè és el que la interpreta (el mecànic «no és al mart» primer, la
										     raó editorial després). Lloc de naixement = foto; l'única sèrie del
										     bloc és de nacionalitat, i la seva targeta ho declara. -->
										{#if kpi.note}
											<p class="gov-kpi__note">{govNote(kpi.note)}</p>
										{/if}
										{#if cell && cell.rang != null}
											<p class="gov-kpi__rank">
												<span class="gov-kpi__rankk">{m.gov_rang_val({ k: String(cell.rang), n: String(cell.n_amb_dada) })}</span>
												<span class="gov-kpi__rankl">{m.gov_rang_label()}{#if cell.empat} · {m.gov_rang_empat()}{/if}{m.gov_rang_cap({ comarca: govern?.comarca ?? '' })}</span>
											</p>
										{:else if kpi.pendingRank}
											<!-- E9: el vot de Bea ja hi és, però el rang encara no el serveix el mart
											     (`mart_govern` no rankeja aquesta mètrica). Es diu el motiu REAL en
											     comptes de calcular-lo aquí (C6 §4). -->
											<p class="gov-kpi__norank">{m.gov_nova_norank()}</p>
										{/if}
										{#if prv.formula}
											<p class="gov-kpi__prov"><span class="gov-kpi__provk">ƒ</span> {prv.formula}</p>
											<p class="gov-kpi__src">{prv.src}</p>
										{:else}
											<p class="gov-kpi__src">{prv.src}</p>
										{/if}
										{@render frescor(def.frescor)}
									</article>
								{:else if kpi.kind === 'etca'}
									<article class="gov-kpi">
										<p class="gov-kpi__lab"><span class="pd dot--measured"></span>{m.muni_num_etca()}</p>
										{#if etca !== null}
											<p class="gov-kpi__v">{formatInteger(etca, locale)}<span class="u">hab.</span></p>
										{:else}
											<p class="gov-kpi__v gov-kpi__v--absent">{m.muni_sense_dada_oficial()}</p>
										{/if}
										<p class="gov-kpi__src">{m.muni_etca_srcline()}</p>
									</article>
								{:else if kpi.kind === 'atur'}
									<!-- E4 · L'ATUR, servit de veritat (D7): darrer mes + 25 mesos de sèrie + les
									     DUES comparacions. La targeta ocupa tota l'amplada perquè hi càpiga la
									     sèrie sense encongir la resta de la graella. -->
									<article class="gov-kpi gov-kpi--wide">
										<p class="gov-kpi__lab"><span class="pd dot--measured"></span>{m.gov_kpi_atur()}</p>
										{#if atur}
											<p class="gov-kpi__v">
												{aturValor(atur.darrer)}<span class="u">{m.gov_atur_u()}</span>
											</p>
											<p class="gov-kpi__delta">{fmtPeriode(atur.darrer.date)}</p>
											{#if atur.darrer.emmascarat}
												<!-- Doctrina del «<5»: interval, MAI un zero ni un buit. -->
												<p class="gov-kpi__norank">{m.gov_atur_masked()}</p>
											{/if}
											{@render tendencia(trendsOf(kpi.trendKey))}
											{#if spark}
												<figure class="gov-spark">
													<svg
														viewBox="0 0 {SPARK_W} {SPARK_H}"
														preserveAspectRatio="none"
														role="img"
														aria-label={m.gov_atur_serie_alt({
															n: String(atur.serie.length),
															ini: fmtPeriode(spark.first),
															fi: fmtPeriode(spark.lastDate),
															min: formatInteger(spark.lo, locale),
															max: formatInteger(spark.hi, locale)
														})}
													>
														<!-- Mesos emmascarats: BANDA [min,max], no un punt inventat. -->
														{#each spark.bands as b, i (i)}
															<line
																class="gov-spark__band"
																x1={b.x}
																x2={b.x}
																y1={b.y1}
																y2={b.y2}
															/>
														{/each}
														{#each spark.segs as pts, i (i)}
															<polyline class="gov-spark__ln" points={pts} />
														{/each}
														{#if spark.lastPt}
															<circle class="gov-spark__pt" cx={spark.lastPt.x} cy={spark.lastPt.y} r="2.6" />
														{/if}
													</svg>
													<figcaption class="gov-spark__cap">
														{m.gov_atur_serie_cap({
															n: String(atur.serie.length),
															ini: fmtPeriode(spark.first),
															fi: fmtPeriode(spark.lastDate)
														})}
													</figcaption>
												</figure>
											{/if}
										{:else}
											<!-- Sense l'artefacte del tauler no s'inventa cap xifra: es diu. -->
											<p class="gov-kpi__v gov-kpi__v--absent">{m.gov_atur_absent()}</p>
										{/if}
										<p class="gov-kpi__src">{m.gov_kpi_atur_src()}</p>
										{@render frescor(aturFrescor)}
									</article>
								{:else if kpi.kind === 'serveis'}
									{@const sDef = gDef('serveis_estab')}
									<article class="gov-kpi">
										<p class="gov-kpi__lab"><span class="pd dot--measured"></span>{m.gov_kpi_serveis()}</p>
										<p class="gov-kpi__v">
											{fmt(row, 'serveis_estab')}<span class="u">{m.gov_kpi_serveis_a()}</span> · {fmt(row, 'restauracio_estab')}<span class="u">{m.gov_kpi_serveis_b()}</span>
										</p>
										{@render tendencia(trendsOf('serveis_estab'))}
										<p class="gov-kpi__src">{srcLine(sDef)}</p>
										{@render frescor(sDef.frescor)}
									</article>
								{/if}
							{/each}
						</div>
					{/each}
					<p class="gov-board__foot">{m.muni_srcline()}</p>
				</section>
			{/if}

			<!-- P1 · EL VEREDICTE: la frase-mare de la IA (verificada), el primer cop d'ull. Només si
			     la lectura ve del model; si és reserva o no hi és, s'omet (degradació honesta). -->
			{#if veredicte}
				<section class="ds-sec muni-vd">
					<p class="muni-vd__cap"><span class="ref">P1</span>{m.muni_veredicte_cap()}</p>
					<p class="muni-vd__text">{veredicte.text}</p>
					{#if veredicte.evidencia?.length}
						<p class="muni-vd__evid">
							{#each evidLabels(veredicte.evidencia) as e (e)}<span class="lect__evchip">{e}</span>{/each}
						</p>
					{/if}
				</section>
			{/if}

			<!-- Capçalera de dades: la dada OFICIAL gran (padró) + identificadors. Les dades oficials
			     porten font i data, no bandera de confiança (el model i la seva confiança, aparcats). -->
			<section class="ds-sec">
				<div class="muni-card">
					<div class="muni-card__top">
						{#if typeof row.values.poblacio === 'number'}
							<div class="muni-card__ietr">
								<span class="v tnum">{formatInteger(row.values.poblacio, locale)}</span><span class="u"
									>{m.muni_hab_padro()}</span
								>
							</div>
						{/if}
					</div>
					<p class="muni-card__meta">
						<span>INE {ine5}</span>
						{#if row.idescat6}<span>Idescat {row.idescat6}</span>{/if}
					</p>
				</div>
			</section>

			<!-- P2 · LA LECTURA: la narració de la IA (verificada), per perfil. Cada afirmació porta la
			     seva naturalesa (mesura/inferència/interpretació) i la seva evidència (mètriques). -->
			{#if hasLectures}
				<section class="ds-sec">
					<div class="ds-sec__hd"><span class="ref">P2</span><h2>{m.muni_lect_title()}</h2></div>
					<p class="muni-sec__sub">{m.muni_lect_ai_note()}</p>
					<!-- Toggle CSS pur: radios (estat natiu del navegador) + `:checked ~` mostra el panell.
					     Sense JS ni $state: robust i funciona encara que la hidratació falli. La pestanya
					     activa per defecte és la primera (ciutadania). -->
					{#each lectGroups as g, i (g.key)}
						<input
							type="radio"
							name="lecttab"
							id="lecttab-{g.key}"
							class="lect__radio"
							checked={i === 0}
						/>
					{/each}
					<div class="lect__tabs" role="tablist" aria-label={m.muni_lect_title()}>
						{#each lectGroups as g (g.key)}
							<label for="lecttab-{g.key}" class="lect__tab">{g.label}</label>
						{/each}
					</div>
					{#each lectGroups as g (g.key)}
						<ul class="lect__list lect__list--{g.key}">
							{#each g.claims as c, i (g.key + i)}
								<li class="lect__claim">
									<span class="lect__to lect__to--{c.to}"
										><span class="pd {toDot(c.to)}"></span>{toLabel(c.to)}</span
									>
									<p class="lect__text">{c.text}</p>
									{#if c.evidencia?.length}
										<p class="lect__evid">
											{#each evidLabels(c.evidencia) as e (e)}<span class="lect__evchip">{e}</span
												>{/each}
										</p>
									{/if}
								</li>
							{/each}
						</ul>
					{/each}
					{#if contraLectura}
						<div class="alert" style="margin-top:6px">
							<span class="bar"></span>
							<div><strong>{m.muni_lect_contra()}:</strong> {contraLectura.text}</div>
						</div>
					{/if}
				</section>
			{/if}

			<!-- P2 · L'EVIDÈNCIA: els números que manen (del dataset). La presència, NOMÉS com a dada
			     oficial: ETCA (Idescat) on n'hi ha; «sense dada oficial» on Idescat no la publica. -->
			<section class="ds-sec">
				<div class="ds-sec__hd"><span class="ref">№</span><h2>{m.muni_nums_title()}</h2></div>
				<div class="muni-5num tnum">
					<div class="n5">
						<span class="n5__lab"><span class="pd dot--measured"></span>{m.muni_num_padro()}</span>
						<span class="n5__v">{typeof row.values.poblacio === 'number' ? formatInteger(row.values.poblacio, locale) : '—'}</span>
					</div>
					<div class="n5">
						<span class="n5__lab"><span class="pd dot--measured"></span>{m.muni_num_etca()}</span>
						{#if etca !== null}
							<span class="n5__v">{formatInteger(etca, locale)}<span class="n5__u">hab.</span></span>
						{:else}
							<span class="n5__v n5__v--absent">{m.muni_sense_dada_oficial()}</span>
						{/if}
					</div>
					<div class="n5">
						<span class="n5__lab"><span class="pd dot--measured"></span>{m.muni_num_nop()}</span>
						<span class="n5__v">{typeof row.values.pct_noprincipal === 'number' ? formatDecimal(row.values.pct_noprincipal, locale, 0) : '—'}<span class="n5__u">%</span></span>
					</div>
					<div class="n5">
						<span class="n5__lab"><span class="pd dot--measured"></span>{m.muni_num_renda()}</span>
						<span class="n5__v">{typeof row.values.renda_neta_persona === 'number' ? formatInteger(row.values.renda_neta_persona, locale) : '—'}<span class="n5__u">€</span></span>
					</div>
				</div>
				<p class="muni-sec__src">{m.muni_etca_srcline()}</p>
			</section>

			<!-- P3 · LA MAQUINÀRIA: la fitxa completa, plegada en acordions (oberts amb «mode dades»).
			     «No traiem res, ho baixem de planta»: cada mètrica del municipi amb la seva procedència. -->
			<section class="ds-sec muni-p3cap">
				<div class="ds-sec__hd"><span class="ref">P3</span><h2>{m.muni_p3_cap()}</h2></div>
				<div class="muni-p3cap__row">
					<p class="muni-sec__sub" style="margin:0">{m.muni_p3_sub()}</p>
					<button type="button" class="muni-mode" aria-pressed={modeDades} onclick={() => (modeDades = !modeDades)}>{m.muni_mode_dades()}</button>
				</div>
			</section>
			{#each blocks as block (block.ref)}
				<details class="ds-sec acc" open={modeDades}>
					<summary class="ds-sec__hd acc__sum">
						<span class="ref">{block.ref}</span><h2>{block.title()}</h2>
					</summary>
					{#if block.sub}<p class="muni-sec__sub">{block.sub()}</p>{/if}
					<div class="ex__rows tnum">
						{#each block.keys as key (key)}
							{@render fichaRow(row, key)}
						{/each}
					</div>
					{#if block.ref === 'D' && osmSospita}
						<div class="alert warn" style="margin-top:10px">
							<span class="bar"></span><div>{m.muni_osm_sospita()}</div>
						</div>
					{/if}
					<p class="muni-sec__src">{srcLine(dataset.metrics[block.keys[0]])}</p>
				</details>
			{/each}

			<!-- «Lectura per a serveis» APARCADA amb el model: els seus denominadors eren les
			     estimacions de pernocta/càrrega. Tornarà, si torna, amb dades oficials. -->

			<!-- Pobles mirall: ara és la constel·lació cat-escala, fora del bloc {#if row} (per a TOTS
			     els munis). Vegeu la secció més avall, després dels veïns de comarca. -->

			<!-- Secció de Licitacions aparcada per al llançament (decisió Bea): /licitacions queda
			     «en construcció». La maquinària i el markup es conserven a l'historial per a la Fase 2. -->

			{#if preguntesFlat.length}
				<section class="ds-sec">
					<div class="ds-sec__hd"><span class="ref">?</span><h2>{m.muni_preg_title()}</h2></div>
					<p class="muni-sec__sub">{m.muni_preg_sub()}</p>
					<ul class="preg">
						{#each preguntesFlat as q (q)}
							<li><a class="preg__chip" href={preguntaHref(q)}>{q}</a></li>
						{/each}
					</ul>
				</section>
			{/if}

			<section class="ds-sec">
				<div class="prov-key">
					<span><span class="dot dot--measured"></span><span>{m.prov_key_measured()}</span></span>
					<span><span class="dot dot--derived"></span><span>{m.prov_key_derived()}</span></span>
				</div>
				<div class="caveats" style="margin-top:14px">
					<div class="alert"><span class="bar"></span><div>{m.muni_honesty()}</div></div>
				</div>
				<p class="srcline">{m.muni_srcline()}</p>
			</section>
		{:else}
			<!-- Municipi de FORA del Berguedà: estat AMABLE «sense dades encara» (mateixa honestedat que
			     el tooltip del mapa). Cap fitxa buida, cap xifra fingida — només l'estat i una sortida. -->
			<section class="ds-sec">
				<div class="muni-empty">
					<p class="muni-empty__badge">{m.map_outside_title()}</p>
					<h2>{m.muni_outside_h2({ nom: muniNom })}</h2>
					<p class="muni-empty__body">{m.map_outside_sub()}</p>
					<p class="muni-empty__scope">{m.map_outside_scope()}</p>
					<div class="muni-empty__actions">
						<a class="muni-empty__link" href={localizeHref('/mapa')}>{m.muni_pick_map()}</a>
						<a class="muni-empty__link muni-empty__link--alt" href={localizeHref('/')}
							>← {m.nav_inici()}</a
						>
					</div>
				</div>
			</section>
		{/if}

		<!-- Municipis VEÏNS de la mateixa comarca (navegació territorial, per a TOTS els munis). -->
		{#if veins.length}
			<section class="ds-sec">
				<div class="ds-sec__hd">
					<span class="ref">⌖</span><h2>{m.muni_veins_title({ comarca: territori?.comarca ?? '' })}</h2>
				</div>
				{#if veinsTotal > veins.length}
					<p class="muni-sec__sub">
						{m.muni_veins_count({ shown: String(veins.length), total: String(veinsTotal) })}
					</p>
				{/if}
				<ul class="veins">
					{#each veins as v (v.slug)}
						<li><a class="veins__chip" href={localizeHref(`/municipi/${v.slug}`)}>{v.nom}</a></li>
					{/each}
				</ul>
			</section>
		{/if}

		<!-- Pobles MIRALL a escala Catalunya: constel·lació egocèntrica (bessons funcionals de tot CAT). -->
		{#if miralls.length}
			<section class="ds-sec">
				<div class="ds-sec__hd"><span class="ref">✦</span><h2>{m.mirall_title()}</h2></div>
				<p class="muni-sec__sub">{m.mirall_lead()}</p>
				<MirallConstel center={muniNom} veins={miralls} />
			</section>
		{/if}
	</div>
</section>

<style>
	/* Chrome (.ap-hero, .ds-main, .ds-sec, .prov-key, .caveats, .ex__row/.ex__rows…) ve del
	   design-system; aquí només els elements propis de la fitxa: el selector, la capçalera de
	   dades del municipi, els subtítols de bloc i l'estat «sense dades». */

	/* Selector de municipi. */
	.muni-pick {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-wrap: wrap;
	}
	.muni-pick label {
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
	}
	.muni-pick .select {
		min-width: 220px;
	}
	.muni-pick__map {
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		color: var(--dp-text-muted);
		text-decoration: none;
		border-bottom: 1px solid var(--dp-border-strong);
		padding-bottom: 1px;
	}
	.muni-pick__map:hover {
		color: var(--dp-text);
	}

	/* Capçalera de dades del municipi (idèntica lectura a la .ex__hd dels extrems del Resum). */
	.muni-card {
		position: relative;
	}
	.muni-card__top {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 14px;
		flex-wrap: wrap;
	}
	.muni-card__ietr {
		display: flex;
		align-items: baseline;
		gap: 5px;
	}
	.muni-card__ietr .v {
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 800;
		font-size: 2rem;
		line-height: 1;
		color: var(--dp-text);
		font-feature-settings: 'tnum' 1;
	}
	.muni-card__ietr .u {
		font-family: var(--dp-font-mono);
		font-size: 0.64rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
	}
	.muni-card__meta {
		margin: 8px 0 0;
		display: flex;
		gap: 14px;
		flex-wrap: wrap;
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
		color: var(--dp-text-muted);
	}

	/* Subtítol de bloc (distingeix mesura d'inferència, com els subgrups del Resum). */
	.muni-sec__sub {
		margin: -2px 0 10px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
	}
	/* Línia de font per bloc. */
	.muni-sec__src {
		margin: 12px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.64rem;
		color: var(--dp-text-subtle);
		line-height: 1.45;
	}

	/* P2 · els números que manen. */
	.muni-5num {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 10px;
	}
	.n5 {
		background: var(--dp-surface);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-md);
		padding: 11px 13px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.n5__lab {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 0.74rem;
		color: var(--dp-text-muted);
	}
	.n5__lab .pd {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex: none;
	}
	.n5__v {
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 700;
		font-size: 1.4rem;
		line-height: 1;
		color: var(--dp-text);
	}
	/* «Sense dada oficial»: honest i apagat, mai un zero fingit ni un guió mut. */
	.n5__v--absent {
		font-family: var(--dp-font-sans);
		font-weight: 600;
		font-size: 0.88rem;
		line-height: 1.3;
		color: var(--dp-text-muted);
	}
	.n5__u {
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		color: var(--dp-text-subtle);
		margin-left: 3px;
	}

	/* P1 · veredicte (frase-mare de la IA). Lead destacat, sobri. */
	.muni-vd__cap {
		display: flex;
		align-items: center;
		gap: 8px;
		margin: 0 0 8px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
	}
	.muni-vd__text {
		margin: 0;
		font-family: var(--dp-font-display);
		font-weight: 600;
		font-size: 1.25rem;
		line-height: 1.4;
		color: var(--dp-text);
		max-width: 60ch;
	}
	.muni-vd__evid,
	.lect__evid {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin: 10px 0 0;
	}
	.lect__evchip {
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		color: var(--dp-text-muted);
		background: var(--dp-surface-2, color-mix(in srgb, var(--dp-text) 6%, transparent));
		border-radius: var(--dp-radius-sm);
		padding: 2px 8px;
	}

	/* P2 · lectures (narració de la IA per perfil). Toggle CSS pur: radios amagats + `:checked ~`. */
	.lect__radio {
		position: absolute;
		width: 1px;
		height: 1px;
		opacity: 0;
		pointer-events: none;
	}
	.lect__tabs {
		display: flex;
		gap: 8px;
		margin: 0 0 14px;
		flex-wrap: wrap;
	}
	.lect__tab {
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		letter-spacing: 0.03em;
		padding: 6px 14px;
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-full);
		background: var(--dp-surface);
		color: var(--dp-text-muted);
		cursor: pointer;
	}
	/* Pestanya activa = la del radio marcat. */
	#lecttab-ciutadania:checked ~ .lect__tabs label[for='lecttab-ciutadania'],
	#lecttab-visitant:checked ~ .lect__tabs label[for='lecttab-visitant'] {
		background: var(--dp-text);
		color: var(--dp-bg);
		border-color: var(--dp-text);
	}
	/* Focus de teclat: ressalta la label del radio enfocat (els radios estan amagats). */
	#lecttab-ciutadania:focus-visible ~ .lect__tabs label[for='lecttab-ciutadania'],
	#lecttab-visitant:focus-visible ~ .lect__tabs label[for='lecttab-visitant'] {
		outline: 2px solid var(--dp-focus, var(--dp-forest));
		outline-offset: 2px;
	}
	/* Panells: amagats per defecte; es mostra el del radio marcat (classe doble per especificitat
	   sobre la base `.lect__list`, independent de l'ordre; `grid` per mantenir el layout base). */
	.lect__list.lect__list--ciutadania,
	.lect__list.lect__list--visitant {
		display: none;
	}
	#lecttab-ciutadania:checked ~ .lect__list.lect__list--ciutadania,
	#lecttab-visitant:checked ~ .lect__list.lect__list--visitant {
		display: grid;
	}
	.lect__list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 16px;
	}
	.lect__claim {
		display: grid;
		gap: 6px;
	}
	.lect__to {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		width: fit-content;
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
	}
	.lect__to .pd {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex: none;
	}
	.lect__text {
		margin: 0;
		font-size: 0.98rem;
		line-height: 1.55;
		color: var(--dp-text);
		max-width: 64ch;
	}

	/* Pregunta-li (preguntes suggerides → IA). Pastilles enllaçades. */
	.preg {
		list-style: none;
		margin: 8px 0 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.preg__chip {
		display: block;
		padding: 10px 14px;
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-md);
		background: var(--dp-surface);
		text-decoration: none;
		color: var(--dp-text);
		font-size: 0.92rem;
		line-height: 1.4;
		transition:
			border-color 0.15s ease,
			background 0.15s ease;
	}
	.preg__chip::before {
		content: '? ';
		color: var(--dp-text-subtle);
		font-family: var(--dp-font-mono);
	}
	.preg__chip:hover {
		border-color: var(--dp-border-strong);
		background: var(--dp-accent-weak);
	}

	/* Municipis veïns de la comarca: llista compacta de xips-enllaç (navegació territorial). */
	.veins {
		list-style: none;
		margin: 10px 0 0;
		padding: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 7px;
	}
	.veins__chip {
		display: inline-block;
		padding: 5px 11px;
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-full, 999px);
		background: var(--dp-surface);
		text-decoration: none;
		color: var(--dp-text-muted);
		font-size: 0.84rem;
		line-height: 1.3;
		transition:
			border-color 0.15s ease,
			color 0.15s ease,
			background 0.15s ease;
	}
	.veins__chip:hover {
		border-color: var(--dp-border-strong);
		background: var(--dp-accent-weak);
		color: var(--dp-text);
	}

	/* P3 · capçalera + toggle «mode dades». */
	.muni-p3cap__row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		flex-wrap: wrap;
	}
	.muni-mode {
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		padding: 5px 12px;
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-full);
		background: var(--dp-surface);
		color: var(--dp-text-muted);
		cursor: pointer;
	}
	.muni-mode[aria-pressed='true'] {
		background: var(--dp-text);
		color: var(--dp-bg);
		border-color: var(--dp-text);
	}

	/* P3 · acordions (la fitxa d'ara, plegada). */
	.acc__sum {
		cursor: pointer;
		list-style: none;
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.acc__sum::-webkit-details-marker {
		display: none;
	}
	.acc__sum::after {
		content: '';
		margin-left: auto;
		width: 8px;
		height: 8px;
		border-right: 2px solid var(--dp-text-subtle);
		border-bottom: 2px solid var(--dp-text-subtle);
		transform: rotate(45deg);
		transition: transform 0.15s ease;
	}
	.acc[open] .acc__sum::after {
		transform: rotate(-135deg);
	}

	/* Estat «sense dades encara» (fora del Berguedà). To apagat i amable; cap xifra. */
	.muni-empty {
		max-width: 56ch;
		padding: var(--dp-space-4) 0;
	}
	.muni-empty__badge {
		display: inline-block;
		margin: 0 0 12px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-muted);
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-sm);
		padding: 3px 9px;
	}
	.muni-empty h2 {
		margin: 0 0 10px;
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 1.4rem;
		line-height: 1.2;
		color: var(--dp-text);
	}
	.muni-empty__body {
		margin: 0 0 8px;
		font-size: 0.95rem;
		line-height: 1.55;
		color: var(--dp-text-muted);
	}
	.muni-empty__scope {
		margin: 0 0 18px;
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		line-height: 1.5;
		color: var(--dp-text-subtle);
	}

	.muni-empty__actions {
		display: flex;
		gap: 18px;
		flex-wrap: wrap;
	}
	.muni-empty__link {
		font-family: var(--dp-font-mono);
		font-size: 0.74rem;
		color: var(--dp-text);
		text-decoration: none;
		border-bottom: 1px solid var(--dp-border-strong);
		padding-bottom: 1px;
	}
	.muni-empty__link--alt {
		color: var(--dp-text-muted);
	}
	.muni-empty__link:hover {
		color: var(--dp-forest);
	}
	/* (El mirall ara és la constel·lació cat-escala —MirallConstel.svelte—, amb estil propi.) */

	/* ── Tauler de dades (D5, vista única des de D8 · E1) ────────────────────────────────── */
	/* (El commutador Veïnal|Govern i el seu estil s'han retirat amb l'E1: una sola vista.) */

	/* Tauler: grups de la gorra §3 + graella de targetes de KPI. */
	.gov-grp {
		margin: 18px 0 8px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
	}
	.gov-grp:first-of-type {
		margin-top: 6px;
	}
	.gov-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 12px;
	}
	.gov-kpi {
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding: 13px 14px;
		background: var(--dp-surface);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-md);
	}
	/* L'atur (E4) ocupa la fila sencera: hi cap la sèrie de 25 mesos sense encongir la graella. */
	.gov-kpi--wide {
		grid-column: 1 / -1;
	}
	.gov-kpi__lab {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		margin: 0;
		font-size: 0.78rem;
		line-height: 1.3;
		color: var(--dp-text-muted);
	}
	.gov-kpi__lab .pd {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex: none;
	}
	.gov-kpi__v {
		margin: 0;
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 700;
		font-size: 1.5rem;
		line-height: 1;
		color: var(--dp-text);
	}
	.gov-kpi__v .u {
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		color: var(--dp-text-subtle);
		margin-left: 3px;
	}
	.gov-kpi__v--absent {
		font-family: var(--dp-font-sans);
		font-weight: 600;
		font-size: 0.9rem;
		color: var(--dp-text-muted);
	}
	.gov-kpi__delta {
		margin: 0;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		color: var(--dp-text-subtle);
	}
	/* Rang comarcal «k de n» (LLEGIT del mart, C6 §4 — mai calculat al front). */
	.gov-kpi__rank {
		margin: 2px 0 0;
		display: flex;
		align-items: baseline;
		gap: 7px;
		flex-wrap: wrap;
	}
	.gov-kpi__rankk {
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 700;
		font-size: 0.95rem;
		color: var(--dp-text);
		background: var(--dp-accent-weak);
		border-radius: var(--dp-radius-sm);
		padding: 1px 7px;
	}
	.gov-kpi__rankl {
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--dp-text-subtle);
	}
	.gov-kpi__norank {
		margin: 2px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		color: var(--dp-text-subtle);
		line-height: 1.4;
	}
	/* D11 · nota de LÍMIT de lectura (E11): el que la xifra no diu de si mateixa. Filet a
	   l'esquerra perquè es llegeixi com una advertència de la targeta i no com més procedència. */
	.gov-kpi__note {
		margin: 4px 0 0;
		padding-left: 7px;
		border-left: 2px solid var(--dp-accent-weak);
		font-family: var(--dp-font-sans);
		font-size: 0.66rem;
		color: var(--dp-text-muted);
		line-height: 1.45;
		text-wrap: pretty;
	}
	/* Procedència (regla de ferro C6 §8.1): fórmula (inferida) o font (mesurada). */
	.gov-kpi__prov {
		margin: 4px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		color: var(--dp-text-muted);
		line-height: 1.4;
		word-break: break-word;
	}
	.gov-kpi__provk {
		color: var(--dp-forest);
		font-style: italic;
		margin-right: 2px;
	}
	.gov-kpi__src {
		margin: 0;
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		color: var(--dp-text-subtle);
		line-height: 1.4;
	}
	/* Frescor per targeta (E5): cadència · darrera càrrega · procés (o la seva absència). Va
	   SEMPRE a cada targeta i mai a un peu global — els vintages no són iguals. */
	.gov-kpi__fresc {
		margin: 0;
		font-family: var(--dp-font-mono);
		font-size: 0.58rem;
		letter-spacing: 0.02em;
		color: var(--dp-text-subtle);
		line-height: 1.4;
		opacity: 0.85;
	}

	/* ── Tendència (E6/E11) ─────────────────────────────────────────────────────────────── */
	/* Cap fletxa sense període; l'atur en porta DUES (mes anterior i mateix mes de l'any
	   anterior), que sovint apunten en sentits oposats: es pinten totes dues. */
	.gov-tend {
		display: grid;
		gap: 3px;
		margin: 2px 0 0;
	}
	.gov-tend__l {
		margin: 0;
		display: flex;
		align-items: baseline;
		flex-wrap: wrap;
		gap: 5px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		line-height: 1.35;
		color: var(--dp-text-muted);
	}
	.gov-tend__ar {
		font-weight: 700;
		font-size: 0.8rem;
		line-height: 1;
		color: var(--dp-text-subtle);
	}
	/* La direcció no és «bona» ni «dolenta» (puja l'atur, puja la població): el color marca
	   sentit, no judici — mateix to per a les dues, i apagat per a l'indeterminat. */
	.gov-tend__ar--puja,
	.gov-tend__ar--baixa,
	.gov-tend__ar--igual {
		color: var(--dp-text);
	}
	.gov-tend__ar--indeterminat,
	.gov-tend__ar--nd {
		color: var(--dp-text-subtle);
	}
	.gov-tend__d {
		color: var(--dp-text);
		font-weight: 600;
	}
	/* «No es pot dir»: l'interval del «<5» travessa el zero. És una resposta, no un buit. */
	.gov-tend__ind {
		font-style: italic;
		color: var(--dp-text-muted);
	}
	.gov-tend__p {
		color: var(--dp-text-subtle);
	}
	/* `sense_serie`: el MOTIU literal del mart. Mai una fletxa grisa, mai un guionet mut. */
	.gov-tend__no {
		margin: 2px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		line-height: 1.45;
		color: var(--dp-text-subtle);
	}
	.gov-tend__nok {
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-muted);
		margin-right: 5px;
	}

	/* Sèrie d'atur (25 mesos). El traç es TRENCA als mesos emmascarats i aquests es dibuixen
	   com una banda [min,max]: no s'interpola damunt del que el SEPE no publica. */
	.gov-spark {
		margin: 6px 0 0;
	}
	.gov-spark svg {
		display: block;
		width: 100%;
		height: 46px;
		overflow: visible;
	}
	.gov-spark__ln {
		fill: none;
		stroke: var(--dp-forest, currentColor);
		stroke-width: 1.4;
		vector-effect: non-scaling-stroke;
		stroke-linejoin: round;
	}
	.gov-spark__band {
		stroke: var(--dp-text-subtle);
		stroke-width: 3;
		opacity: 0.4;
		vector-effect: non-scaling-stroke;
	}
	.gov-spark__pt {
		fill: var(--dp-forest, currentColor);
	}
	.gov-spark__cap {
		margin: 4px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.58rem;
		color: var(--dp-text-subtle);
	}

	/* (`.gov-kpi__bea` i `.gov-tag` retirats amb l'E10: la frase interpretativa ja no es
	   renderitza i el seu distintiu de «vot pendent» se n'anava amb ella.) */
	.gov-board__foot {
		margin: 16px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		color: var(--dp-text-subtle);
	}
</style>
