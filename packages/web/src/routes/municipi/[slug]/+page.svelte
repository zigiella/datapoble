<script lang="ts">
	/**
	 * FITXA DE MUNICIPI (`/municipi/[ine5]` · `/es/municipi/[ine5]`).
	 *
	 * Generalitza a QUALSEVOL dels 31 municipis del Berguedà la fitxa rica que el Resum només
	 * donava als dos extrems (Berga 08022, Castellar de n'Hug 08052). Mateixa presentació i
	 * mateixa honestedat: nom + pastilla de TIPOLOGIA (arquetip categòric) + bandera de CONFIANÇA
	 * i score auditable 0-100, i TOTES les mètriques del municipi agrupades editorialment (KPI
	 * bàsics, senyals físics per càpita, les 3 capes inferides, IETR + stock/impact, energia,
	 * política), cadascuna amb la seva PROCEDÈNCIA (punt mesura/inferència) i la unitat del
	 * contracte.
	 *
	 * Disciplina de dades (com al Resum/Mapa/Glossari): CAP xifra, etiqueta, unitat ni font es
	 * codifica a la UI — tot surt del dataset real (= contracte semàntic) via `formatMetric`/`pick`.
	 * La procedència (slate=mesurada, porpra=inferència) la dedueix `provenanceOf` del `source`. Les
	 * 3 capes són inferència; el 0 d'OSM de la restauració es mostra «sense dada», no «0,0» (honestedat).
	 *
	 * Si l'`ine5` no és al dataset (resta de Catalunya) → estat AMABLE «sense dades encara» (mateix
	 * gest que el tooltip «fora del Berguedà» del mapa), mai una fitxa buida ni un error lleig.
	 *
	 * Chrome del design-system (.ap-hero + .ds-main/.ds-sec); el text nou és i18n ca/es.
	 */
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import ContourField from '$lib/components/ContourField.svelte';
	import { currentLocale, pick, localizeHref } from '$lib/i18n';
	import { formatMetric, formatDecimal, formatInteger } from '$lib/format';
	import { SIGNED_PCT_KEYS } from '$lib/map/classify';
	import { provenanceOf } from '$lib/map/provenance';
	import { tipologiaMeta } from '$lib/map/tipologia';
	import { toSlug, slugForIne5 } from '$lib/contract/slug';
	import Espina from '$lib/components/Espina.svelte';
	import MirallConstel from '$lib/components/MirallConstel.svelte';
	import { m } from '$lib/paraglide/messages';
	import type { MetricDef, MetricKey, MetricValue, MunicipiRow } from '$lib/contract/types';
	import type { LectTo } from '$lib/contract/lectures';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const dataset = $derived(data.dataset);
	const row = $derived(data.row);
	const ine5 = $derived(data.ine5);
	const pernocta = $derived(data.pernocta); // presència estimada EN RANG (munis coberts fora del Berguedà)
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
		},
		{
			ref: 'E',
			title: () => m.muni_blk_capes(),
			sub: () => m.muni_blk_capes_sub(),
			keys: [
				'poblacio_pernocta_est',
				'gap_pernocta',
				'gap_pernocta_pct',
				'carrega_total_est',
				'carrega_funcional_est',
				'index_turisme'
			]
		},
		{
			ref: 'F',
			title: () => m.muni_blk_ietr(),
			sub: () => m.muni_blk_ietr_sub(),
			keys: ['IETR', 'IETR_rank', 'IETR_stock', 'IETR_impact', 'pct_icaen_EFG']
		},
		{
			ref: 'G',
			title: () => m.muni_blk_politica(),
			sub: () => m.muni_blk_politica_sub(),
			keys: ['guanya', 'pct_indep', 'pct_esquerra', 'pct_extrema_dreta']
		}
	];

	// Files ressaltades: els proxies de pernocta/no-principal i la mètrica estrella (gap pernocta,
	// la població invisible) + l'IETR. Mateix criteri editorial que el Resum.
	// Alerta de divergència L1>L2: la pernocta elèctrica supera la càrrega per residus
	// (residus/càpita baixos o base mal calibrada) → la càrrega per residus no és un sostre.
	const l1GtL2 = $derived(
		typeof row?.values.poblacio_pernocta_est === 'number' &&
			typeof row?.values.carrega_total_est === 'number' &&
			row.values.poblacio_pernocta_est > row.values.carrega_total_est
	);

	// Infra-mapeig OSM: vidre alt amb restauració = 0 → el 0 és buit de mapa, no absència real.
	const osmSospita = $derived(
		typeof row?.values.vidre_hab === 'number' &&
			row.values.vidre_hab > 30 &&
			(row?.values.restauracio_estab === 0 || row?.values.restauracio_estab == null)
	);
	// Ràtio de càrrega: equivalents de presència per cada empadronat (denominador funcional / padró).
	const ratioCarrega = $derived.by<number | null>(() => {
		const c = row?.values.carrega_funcional_est;
		const p = row?.values.poblacio;
		return typeof c === 'number' && typeof p === 'number' && p > 0 ? c / p : null;
	});
	// «Lectura per a serveis» (consultor #4): quin denominador hauria d'usar cada servei municipal.
	const serveisLectura = $derived.by(() => {
		const v = row?.values ?? {};
		const num = (k: MetricKey) => (typeof v[k] === 'number' ? (v[k] as number) : null);
		return [
			{ servei: m.muni_serv_residus(), denom: m.muni_serv_d_carrega(), val: num('carrega_funcional_est'), unit: 'hab.' },
			{ servei: m.muni_serv_aigua(), denom: m.muni_serv_d_l1(), val: num('poblacio_pernocta_est'), unit: 'hab.' },
			{ servei: m.muni_serv_vivenda(), denom: m.muni_serv_d_padro_np(), val: null, unit: '' },
			{ servei: m.muni_serv_turisme(), denom: m.muni_serv_d_turisme(), val: num('IETR'), unit: 'IETR' },
			{ servei: m.muni_serv_socials(), denom: m.muni_serv_d_socials(), val: null, unit: '' },
			{ servei: m.muni_serv_seguretat(), denom: m.muni_serv_d_seguretat(), val: null, unit: '' }
		];
	});

	const highlightRows = new Set<MetricKey>([
		'pct_noprincipal',
		'rtc_per_1000hab',
		'bretxa_naturalitzacio',
		'gap_pernocta_pct',
		'carrega_funcional_est',
		'IETR'
	]);

	// ——— Pas 0 · «el rang és la dada» (spec consultora 2 §10) ———
	// La família pernocta (qui dorm / gap) és inferència: es mostra en RANG, no com a punt.
	// Banda interim = sensibilitat de la base ±10% (multiplicativa); §2 la substituirà pel
	// p10–p90 del model d'esperats. Com que pernocta_est ∝ 1/base, la banda és
	// [est/(1+s), est/(1−s)]. Si el rang del gap CREUA el 0, el signe no és concloent
	// (cas Berga −2%, Puig-reig −5%): es diu «≈0 · no concloent», mai un número amb signe.
	const GAP_SENSITIVITY = 0.1;
	const PERNOCTA_RANGE_KEYS = new Set<MetricKey>([
		'poblacio_pernocta_est',
		'gap_pernocta',
		'gap_pernocta_pct'
	]);
	const pernoctaBand = $derived.by(() => {
		const est = row?.values.poblacio_pernocta_est;
		const padro = row?.values.poblacio;
		if (typeof est !== 'number' || typeof padro !== 'number' || padro <= 0) return null;
		const s = GAP_SENSITIVITY;
		const estLow = est / (1 + s);
		const estHigh = est / (1 - s);
		const pctLow = (estLow / padro - 1) * 100;
		const pctHigh = (estHigh / padro - 1) * 100;
		return {
			inconcludent: pctLow < 0 && pctHigh > 0,
			estLow, estHigh, est,
			gapAbsLow: estLow - padro, gapAbsHigh: estHigh - padro, gapAbs: est - padro,
			pctLow, pctHigh, pct: (est / padro - 1) * 100
		};
	});
	// Enter localitzat (recomptes) i amb signe explícit (gaps), 0 decimals.
	const fInt = (v: number): string => formatDecimal(v, locale, 0);
	const fSign = (v: number): string =>
		new Intl.NumberFormat(locale === 'es' ? 'es-ES' : 'ca-ES', {
			signDisplay: 'exceptZero',
			maximumFractionDigits: 0
		}).format(v);

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
		poblacio_pernocta_est: 'hab.',
		carrega_total_est: 'hab.',
		carrega_funcional_est: 'hab.',
		gap_pernocta: 'hab.',
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

	// Valor d'una mètrica per al municipi, formatat al locale (sense unitat). Cas especial: les
	// desviacions amb signe (gaps de pernocta) amb +/− explícit; el valor ja ve 0-100, no es reescala.
	// Mateix conveni que el Resum i el mapa.
	function fmt(r: MunicipiRow, key: MetricKey): string {
		const value = effectiveValue(r, key);
		if (SIGNED_PCT_KEYS.has(key) && typeof value === 'number') {
			const loc = locale === 'es' ? 'es-ES' : 'ca-ES';
			return new Intl.NumberFormat(loc, {
				signDisplay: 'exceptZero',
				maximumFractionDigits: 0
			}).format(value);
		}
		return fmtValue(value, dataset.metrics[key]);
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

	// ── Capçalera del municipi: tipologia + confiança (idèntica lectura que el Resum) ─────────
	const tipo = $derived(row ? tipologiaMeta(row.values.tipologia) : undefined);
	// Pobles mirall a escala Catalunya: bessons funcionals (no geogràfics) de tot el país, resolts al
	// loader des de l'artefacte `municipis-mirall.json` (Nivell C). Per a QUALSEVOL muni, no només Berguedà.
	const miralls = $derived(data.miralls ?? []);
	const score = $derived.by<number | null>(() => {
		const s = row?.values.confianca_score;
		return typeof s === 'number' && Number.isFinite(s) ? s : null;
	});
	const confFlag = $derived(row?.values.confianca as string | undefined);
	const confLabel = $derived.by<string | null>(() => {
		if (confFlag === 'alta') return m.map_confidence_high();
		if (confFlag === 'mitjana') return m.map_confidence_mid();
		if (confFlag === 'baixa') return m.map_confidence_low();
		return null;
	});

	// Divergència dels senyals (0-100): 0 concordants · 100 màxima discrepància. El «per què»
	// AUDITABLE de la confiança (el component de concordança del score, exposat sol).
	const diverg = $derived.by<number | null>(() => {
		const v = row?.values.divergencia_senyals;
		return typeof v === 'number' && Number.isFinite(v) ? v : null;
	});
	// «Per què» de la confiança: fragments de la DADA real (concordança dels senyals + mida del padró).
	const confWhy = $derived.by<string[]>(() => {
		const out: string[] = [];
		if (diverg !== null)
			out.push(
				diverg <= 33 ? m.conf_sig_converg() : diverg >= 67 ? m.conf_sig_diverg() : m.conf_sig_partial()
			);
		const pop = row?.values.poblacio;
		if (typeof pop === 'number' && pop < 200) out.push(m.conf_padro_small());
		return out;
	});

	// IETR per al rètol gran de la capçalera (1 decimal) i el rang.
	const ietr = $derived.by<number | null>(() => {
		const v = row?.values.IETR;
		return typeof v === 'number' ? v : null;
	});
	const ietrRank = $derived(row?.values.IETR_rank ?? null);
	const numMunis = $derived(dataset.comarca.num_municipis);

	// Lectura IETR-família: estructura (stock) × empremta (impact) → quadrant, reusant la
	// MATEIXA semàntica que la constel·lació del Resum (claus i18n constel_q_*). Treu l'IETR
	// de número únic («no només 26,0»): diu QUIN tipus d'exposició, no només quant.
	const ietrReading = $derived.by(() => {
		const s = typeof row?.values.IETR_stock === 'number' ? row.values.IETR_stock : null;
		const i = typeof row?.values.IETR_impact === 'number' ? row.values.IETR_impact : null;
		if (s === null || i === null) return null;
		const q =
			s >= 50 && i >= 50
				? { name: m.constel_q_consolidada(), help: m.constel_q_consolidada_help() }
				: s >= 50
					? { name: m.constel_q_latent(), help: m.constel_q_latent_help() }
					: i >= 50
						? { name: m.constel_q_sense_stock(), help: m.constel_q_sense_stock_help() }
						: { name: m.constel_q_baixa(), help: m.constel_q_baixa_help() };
		return { stock: s, impact: i, name: q.name, help: q.help };
	});

	// Nom del municipi (topònim, igual en ambdós locales): del dataset (Berguedà), del rang (cobert)
	// o del CATÀLEG de tota Catalunya (`data.nom`, qualsevol poble); en últim cas, el codi.
	const muniNom = $derived(row?.nom ?? pernocta?.nom ?? data.nom ?? ine5 ?? '');
	// Enter localitzat per a les xifres del rang.
	const fNum = (v: number) => formatInteger(v, locale);

	// ── Selector de municipi: salta a un altre dels 31 (ordenat per nom, localitzat) ──────────
	// Es deriva del dataset (no llista codificada). El canvi navega a la fitxa corresponent.
	const muniOptions = $derived.by(() => {
		const items = Object.values(dataset.municipis).map((mr) => ({ ine5: mr.ine5, nom: mr.nom }));
		const coll = new Intl.Collator(locale === 'es' ? 'es-ES' : 'ca-ES');
		return items.sort((a, b) => coll.compare(a.nom, b.nom));
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
	const heroLabels = ['INE', 'tipologia', 'confiança', '31', 'mètriques', 'procedència', 'fitxa'];
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
		{#if PERNOCTA_RANGE_KEYS.has(key) && pernoctaBand}
			{#if pernoctaBand.inconcludent && (key === 'gap_pernocta' || key === 'gap_pernocta_pct')}
				<span class="val val--neutral">{m.ficha_inconcludent()}</span>
			{:else if key === 'poblacio_pernocta_est'}
				<span class="val"
					>{fInt(pernoctaBand.estLow)} … {fInt(pernoctaBand.estHigh)}<span class="u">hab.</span>
					<span class="val-mid">({m.ficha_midpoint()} {fInt(pernoctaBand.est)})</span></span
				>
			{:else if key === 'gap_pernocta'}
				<span class="val"
					>{fSign(pernoctaBand.gapAbsLow)} … {fSign(pernoctaBand.gapAbsHigh)}<span class="u">hab.</span>
					<span class="val-mid">({m.ficha_midpoint()} {fSign(pernoctaBand.gapAbs)})</span></span
				>
			{:else}
				<span class="val"
					>{fSign(pernoctaBand.pctLow)} … {fSign(pernoctaBand.pctHigh)}<span class="u">%</span>
					<span class="val-mid">({m.ficha_midpoint()} {fSign(pernoctaBand.pct)})</span></span
				>
			{/if}
		{:else}
			<span class="val"
				>{fmt(r, key)}{#if isPct}<span class="u">%</span>{:else if unit}<span class="u">{unit}</span
					>{/if}</span
			>
		{/if}
	</div>
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
			{#if row}
				<p class="lede">{m.muni_lede()}</p>
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

			<!-- Capçalera de dades: rang IETR + valor gran, tipologia (pastilla) i confiança + score.
			     És la MATEIXA lectura destacada que les fitxes dels extrems del Resum, ara per a
			     qualsevol municipi. -->
			<section class="ds-sec">
				<div class="muni-card">
					<div class="muni-card__top">
						<span class="muni-card__rank"
							>{m.resum_rank()} <b>{ietrRank ?? '—'}</b> {m.resum_rank_of()} {formatInteger(numMunis, locale)}</span
						>
						{#if ietr !== null}
							<div class="muni-card__ietr">
								<span class="v tnum">{formatDecimal(ietr, locale, 1)}</span><span class="u"
									>{m.resum_ietr_scale()}</span
								>
							</div>
						{/if}
					</div>
					{#if ietrReading}
						<p class="muni-card__ietr-reading" style="margin:6px 0 0; display:flex; flex-wrap:wrap; gap:4px 10px; align-items:baseline; font-size:13px;">
							<span style="font-family:var(--dp-font-mono); color:var(--dp-text-muted)">stock {formatDecimal(ietrReading.stock, locale, 0)} · impact {formatDecimal(ietrReading.impact, locale, 0)}</span>
							<span style="color:var(--dp-text)"><b>{ietrReading.name}</b> · {ietrReading.help}</span>
						</p>
					{/if}
					<p class="muni-card__meta">
						<span>INE {ine5}</span>
						{#if typeof row.values.poblacio === 'number'}<span
								>{formatInteger(row.values.poblacio, locale)} hab.</span
							>{/if}
						{#if row.idescat6}<span>Idescat {row.idescat6}</span>{/if}
					</p>

					<!-- Tipologia (Fase 1): la LECTURA narrativa — quin TIPUS de pressió. Pastilla amb el
					     color categòric de l'arquetip + etiqueta humana + frase curta (reusa tipologia.ts). -->
					{#if tipo}
						<div class="muni-card__tipo">
							<span class="muni-card__tipo-badge" style="--tipo-c:{tipo.color}">
								<span class="dot"></span>{tipo.label()}
							</span>
							<p class="muni-card__tipo-blurb">{tipo.blurb()}</p>
						</div>
					{/if}

					<!-- Confiança (consultor #2): bandera GRAN + «per què» (concordança/padró) + divergència
					     dels senyals 0-100 + riscos. Que ningú confongui la qualitat amb una xifra opaca. -->
					{#if confLabel || score !== null}
						<div class="muni-card__conf">
							<div class="muni-card__conf-head">
								<span class="muni-card__conf-lbl">{m.map_confidence_label()}</span>
								{#if confLabel}<span class="muni-card__conf-flag muni-card__conf-flag--{confFlag}">{confLabel}</span>{/if}
								{#if score !== null}<span class="muni-card__conf-global" title={m.map_confidence_score_label()}>{m.conf_global_label()} {formatDecimal(score, locale, 0)}<span class="muni-card__conf-scale">/100</span></span>{/if}
							</div>
							{#if confWhy.length}
								<p class="muni-card__conf-line">
									<span class="muni-card__conf-k">{m.conf_why_label()}</span>
									{#each confWhy as w}<span class="muni-card__conf-chip">{w}</span>{/each}
								</p>
							{/if}
							{#if diverg !== null}
								<p class="muni-card__conf-line">
									<span class="muni-card__conf-k">{m.conf_diverg_label()}</span>
									<span class="muni-card__conf-diverg">{formatDecimal(diverg, locale, 0)}<span class="muni-card__conf-scale">/100</span></span>
								</p>
							{/if}
							<p class="muni-card__conf-line">
								<span class="muni-card__conf-k">{m.conf_risks_label()}</span>
								<span class="muni-card__conf-v">{m.conf_risk_noseries()} · {m.conf_risk_osm()}</span>
							</p>
						</div>
					{/if}
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

			<!-- P2 · L'EVIDÈNCIA: els cinc números (del dataset). El «qui hi dorm» és inferència i
			     es mostra en RANG (el rang és la dada, spec §10). -->
			<section class="ds-sec">
				<div class="ds-sec__hd"><span class="ref">5</span><h2>{m.muni_5num_title()}</h2></div>
				<div class="muni-5num tnum">
					<div class="n5">
						<span class="n5__lab"><span class="pd dot--measured"></span>{m.muni_num_padro()}</span>
						<span class="n5__v">{typeof row.values.poblacio === 'number' ? formatInteger(row.values.poblacio, locale) : '—'}</span>
					</div>
					<div class="n5">
						<span class="n5__lab"><span class="pd dot--derived"></span>{m.muni_num_dorm()}</span>
						<span class="n5__v">{#if pernoctaBand}{fInt(pernoctaBand.estLow)}–{fInt(pernoctaBand.estHigh)}{:else}—{/if}</span>
					</div>
					<div class="n5">
						<span class="n5__lab"><span class="pd dot--derived"></span>{m.muni_num_carrega()}</span>
						<span class="n5__v">{typeof row.values.carrega_total_est === 'number' ? fInt(row.values.carrega_total_est) : '—'}</span>
					</div>
					<div class="n5">
						<span class="n5__lab"><span class="pd dot--measured"></span>{m.muni_num_nop()}</span>
						<span class="n5__v">{typeof row.values.pct_noprincipal === 'number' ? formatDecimal(row.values.pct_noprincipal, locale, 0) : '—'}<span class="n5__u">%</span></span>
					</div>
					<div class="n5">
						<span class="n5__lab"><span class="pd dot--derived"></span>{m.muni_num_expo()}</span>
						<span class="n5__v">{ietr !== null ? formatDecimal(ietr, locale, 0) : '—'}<span class="n5__u">/100{#if ietrRank} · {ietrRank}è{/if}</span></span>
					</div>
				</div>
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
					{#if block.ref === 'E'}
						<p class="muni-sec__rangenote">{m.ficha_range_note()}</p>
					{/if}
					{#if block.ref === 'E' && l1GtL2}
						<div class="alert" style="margin-top:10px">
							<span class="bar"></span><div>{m.muni_capes_divergence()}</div>
						</div>
					{/if}
					{#if block.ref === 'D' && osmSospita}
						<div class="alert warn" style="margin-top:10px">
							<span class="bar"></span><div>{m.muni_osm_sospita()}</div>
						</div>
					{/if}
					<p class="muni-sec__src">{srcLine(dataset.metrics[block.keys[0]])}</p>
				</details>
			{/each}

			<section class="ds-sec">
				<div class="ds-sec__hd"><span class="ref">⚙</span><h2>{m.muni_serv_title()}</h2></div>
				<p class="muni-sec__sub">{m.muni_serv_sub()}</p>
				{#if ratioCarrega}
					<p class="muni-serv__punch">{m.muni_serv_ratio({ x: formatDecimal(ratioCarrega, locale, 1) })}</p>
				{/if}
				<dl class="muni-serv">
					{#each serveisLectura as s (s.servei)}
						<div class="muni-serv__row">
							<dt>{s.servei}</dt>
							<dd>{s.denom}{#if s.val != null} · <strong>{formatDecimal(s.val, locale, 0)}</strong>{#if s.unit} {s.unit}{/if}{/if}</dd>
						</div>
					{/each}
				</dl>
			</section>

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
		{:else if pernocta}
			<!-- Municipi COBERT pel Nivell C (fora del Berguedà): encara no té la fitxa completa, però
			     sí una PRESÈNCIA ESTIMADA EN RANG. Honestedat: el rang és la dada, no la xifra; l'ETCA
			     oficial es mostra com a validació; tot enllaça a la metodologia. -->
			<section class="ds-sec">
				<div class="muni-rang">
					<p class="muni-rang__badge">{m.muni_rang_badge()}</p>
					<p class="muni-rang__lede">{m.muni_rang_lede()}</p>
					<div class="muni-rang__big tnum">
						{#if pernocta.etca_oficial != null}
							<!-- On hi ha ETCA oficial (≥1.000 hab), ella és el titular (presència real oficial);
							     la nostra estimació en rang va com a mètode propi validat. -->
							<span class="muni-rang__k">{m.muni_rang_etca_label()}</span>
							<span class="muni-rang__range">{fNum(pernocta.etca_oficial)}</span>
							<span class="muni-rang__central"
								>{m.muni_rang_model()}: {fNum(pernocta.rang_baix)} – {fNum(pernocta.rang_alt)}</span
							>
						{:else}
							<!-- Sense ETCA (munis <1.000 hab): el nostre rang és l'estimació de presència. -->
							<span class="muni-rang__k">{m.muni_rang_label()}</span>
							<span class="muni-rang__range">{fNum(pernocta.rang_baix)} – {fNum(pernocta.rang_alt)}</span>
							<span class="muni-rang__central">{m.muni_rang_central()} {fNum(pernocta.estimacio)}</span>
						{/if}
					</div>
					{#if pernocta.padro != null}
						<dl class="muni-serv">
							<div class="muni-serv__row">
								<dt>{m.muni_num_padro()}</dt>
								<dd class="tnum">{fNum(pernocta.padro)}</dd>
							</div>
						</dl>
					{/if}
					<div class="alert" style="margin-top:12px">
						<span class="bar"></span><div>{m.muni_rang_caveat()}</div>
					</div>
					<div class="muni-empty__actions" style="margin-top:14px">
						<a class="muni-empty__link" href={localizeHref('/metodologia')}>{m.muni_rang_method_link()}</a>
						<a class="muni-empty__link muni-empty__link--alt" href={localizeHref('/mapa')}>{m.muni_pick_map()}</a>
					</div>
				</div>
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
						<a class="muni-empty__link muni-empty__link--alt" href={localizeHref('/resum')}
							>← {m.stub_back()}</a
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
	   dades del municipi (pastilla de tipologia + confiança, reusant el gest del Resum), els
	   subtítols de bloc i l'estat «sense dades». */

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
	.muni-card__rank {
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
	}
	.muni-card__rank b {
		color: var(--dp-text);
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

	/* Pastilla de tipologia (mateixa pell que .ex__tipo del Resum). */
	.muni-card__tipo {
		margin: 14px 0 0;
	}
	.muni-card__tipo-badge {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 4px 11px 4px 9px;
		border-radius: 999px;
		background: color-mix(in srgb, var(--tipo-c) 14%, var(--dp-surface));
		border: 1px solid color-mix(in srgb, var(--tipo-c) 40%, var(--dp-border));
		font-family: 'Archivo', var(--dp-font-sans);
		font-weight: 700;
		font-size: 0.95rem;
		letter-spacing: -0.01em;
		color: var(--dp-text);
		line-height: 1.15;
	}
	.muni-card__tipo-badge .dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--tipo-c);
		flex: none;
		box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
	}
	.muni-card__tipo-blurb {
		margin: 7px 0 0;
		font-family: var(--dp-font-sans);
		font-size: 0.85rem;
		line-height: 1.45;
		color: var(--dp-text-muted);
		max-width: 52ch;
	}

	/* Bloc de confiança (consultor #2): bandera + per què + divergència + riscos, en files.
	   Que ningú confongui la qualitat (bandera) amb una puntuació opaca. Gest mono del Resum. */
	.muni-card__conf {
		margin: 12px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
		display: grid;
		gap: 4px;
	}
	.muni-card__conf-head {
		display: flex;
		align-items: baseline;
		gap: 8px;
		flex-wrap: wrap;
	}
	.muni-card__conf-lbl {
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
	}
	.muni-card__conf-flag {
		font-weight: 700;
		color: var(--dp-text);
	}
	.muni-card__conf-flag--alta {
		color: var(--dp-success, #2f6b4f);
	}
	.muni-card__conf-flag--baixa {
		color: var(--dp-warning, #b5612a);
	}
	.muni-card__conf-global {
		margin-left: auto;
		color: var(--dp-text-subtle);
		font-feature-settings: 'tnum' 1;
	}
	.muni-card__conf-line {
		margin: 0;
		display: flex;
		gap: 6px;
		flex-wrap: wrap;
		align-items: baseline;
		line-height: 1.5;
	}
	.muni-card__conf-k {
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
		min-width: 8.5em;
	}
	.muni-card__conf-v {
		color: var(--dp-text-muted);
	}
	.muni-card__conf-chip {
		color: var(--dp-text);
		background: var(--dp-surface-2, color-mix(in srgb, var(--dp-text) 6%, transparent));
		border-radius: var(--dp-radius-sm);
		padding: 1px 7px;
	}
	.muni-card__conf-diverg {
		font-weight: 700;
		color: var(--dp-text);
		font-feature-settings: 'tnum' 1;
	}
	.muni-card__conf-scale {
		font-weight: 500;
		color: var(--dp-text-subtle);
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
	/* Pas 0 · nota de rang (família pernocta): explica que la inferència es publica en rang. */
	.muni-sec__rangenote {
		margin: 8px 0 0;
		font-size: 0.74rem;
		line-height: 1.4;
		color: var(--dp-text-muted);
	}
	/* Valor «no concloent» (rang que creua 0): neutre, sense signe. */
	.val--neutral {
		color: var(--dp-text-subtle);
		font-weight: 600;
	}
	/* Punt mig (cortesia): el rang és la dada; el punt, secundari. */
	.val-mid {
		font-size: 0.82em;
		font-weight: 500;
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

	/* P2 · els cinc números. */
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

	/* Caixeta «Lectura per a serveis» (consultor #4): quin denominador toca a cada servei. */
	.muni-serv__punch {
		margin: 4px 0 12px;
		font-size: 0.92rem;
		line-height: 1.5;
		color: var(--dp-text);
	}
	.muni-serv {
		margin: 0;
		display: grid;
		gap: 1px;
		background: var(--dp-border);
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-md);
		overflow: hidden;
	}
	.muni-serv__row {
		display: flex;
		justify-content: space-between;
		gap: 14px;
		align-items: baseline;
		background: var(--dp-surface);
		padding: 9px 13px;
	}
	.muni-serv__row dt {
		font-family: var(--dp-font-mono);
		font-size: 0.64rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
		white-space: nowrap;
	}
	.muni-serv__row dd {
		margin: 0;
		text-align: right;
		font-size: 0.84rem;
		color: var(--dp-text-muted);
	}
	.muni-serv__row dd strong {
		color: var(--dp-text);
		font-feature-settings: 'tnum' 1;
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

	/* Targeta de PRESÈNCIA ESTIMADA EN RANG (munis coberts pel Nivell C, fora del Berguedà). */
	.muni-rang {
		max-width: 60ch;
	}
	.muni-rang__badge {
		display: inline-block;
		margin: 0 0 10px;
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-muted);
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-sm);
		padding: 3px 9px;
	}
	.muni-rang__lede {
		margin: 0 0 16px;
		font-size: 0.95rem;
		line-height: 1.55;
		color: var(--dp-text-muted);
	}
	.muni-rang__big {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin: 0 0 16px;
	}
	.muni-rang__k {
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
	}
	.muni-rang__range {
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 800;
		font-size: 2rem;
		line-height: 1.05;
		color: var(--dp-text);
	}
	.muni-rang__central {
		font-family: var(--dp-font-mono);
		font-size: 0.74rem;
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
</style>
