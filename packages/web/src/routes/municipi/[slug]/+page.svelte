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
	import { formatMetric, formatDecimal, formatInteger, formatBoardValue } from '$lib/format';
	import { provenanceOf } from '$lib/map/provenance';
	import { toSlug, slugForIne5, nomCanonic, nomIndex } from '$lib/contract/slug';
	// W2 · l'article de la comarca («del Berguedà», «de l'Alt Empordà»): taula lèxica + una
	// funció, compartida amb el llistat per comarca i exercida sobre les 43 pel verificador.
	import { deComarca } from '$lib/contract/comarca-nom.js';
	import Espina from '$lib/components/Espina.svelte';
	import MirallConstel from '$lib/components/MirallConstel.svelte';
	import { m } from '$lib/paraglide/messages';
	import type { Frescor, MetricDef, MetricKey, MetricValue, MunicipiRow } from '$lib/contract/types';
	import type { LectTo } from '$lib/contract/lectures';
	import {
		GOVERN_KPIS,
		GOVERN_RANK_KEYS,
		PRESENCIA_KEY,
		EDATS_BANDS,
		NAIX_BAR_KEYS,
		E13_KEYS,
		E13_LLINDAR,
		GOVERN_DENOM_REASON,
		GOVERN_DENOM_REASON_DEFAULT,
		GOVERN_RECOMPTE,
		GOVERN_RECOMPTE_BASE,
		governReferences,
		governUnit,
		metricaSlug,
		provenanceLine
	} from '$lib/govern/kpis';
	import type { GovernCell, GovernEntry } from '$lib/contract/govern';
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
	// B3 · quants municipis té la comarca (amb dada o sense): el denominador de referència que fa
	// llegible el «k de n». 0 = no s'ha pogut comptar → la targeta no diu res (mai un total fals).
	const comarcaMunis = $derived(data.comarcaMunis ?? 0);
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
	// P1 (veredicte) i P2 (lectura narrativa) OCULTS de moment (decisió de Bea, 2026-07-20): es
	// refaran en uns dies sobre mètriques CITABLES (E7b — avui només 164 de 532 frases servides
	// compleixen la regla d'evidència). La maquetació es conserva SENCERA aquí sota; això només
	// tanca la porta. Quan E7b torni amb les lectures regenerades, es torna a posar a `true`.
	// (Les preguntes suggerides NO són P1/P2: es queden, però des d'avui sense enllaç — vegeu avall.)
	const MOSTRA_LECTURES_IA = false;
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

	// Preguntes suggerides, capades a 6. Des del 2026-07-20 (decisió de Bea) es mostren com a text
	// ESTÀTIC, sense enllaç a /pregunta-li: són exemples del que es podrà preguntar, no un botó que
	// dispari una consulta al xat encara. Per això ja no hi ha `preguntaHref`.
	const preguntesFlat = $derived.by<string[]>(() => {
		const p = hasLectura ? lectura?.preguntes : null;
		if (!p) return [];
		return [...(p.propies ?? []), ...(p.comarca ?? []), ...(p.miralls ?? [])]
			.map((q) => q.trim())
			.filter(Boolean)
			.slice(0, 6);
	});

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
	// (La regla viu a `$lib/format` perquè el LLISTAT per comarca (W2) formati la MATEIXA xifra
	// exactament igual: dues còpies serien la mateixa dada amb dos nombres de decimals.)
	function fmtValue(value: MetricValue | undefined, def: MetricDef): string {
		return formatBoardValue(value, def, locale) ?? m.value_not_available();
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
	// Els 4 grups del tauler v3 (ordre FIX, C6 §7 — cap KPI es reordena per enterrar-lo), amb els
	// rètols del redisseny aprovat: «La gent» · «Les cases» · «Feina i renda» · «El dia a dia»
	// (el D inclou ara comerç/serveis: és vida diària, no macroeconomia).
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
	// W2: la taula viu a `kpis.js` (`GOVERN_UNIT`/`governUnit`) perquè el LLISTAT per comarca
	// pinti la mateixa unitat sota la mateixa xifra; aquí només s'hi lliga la def del contracte.
	function gUnit(key: string): string {
		return governUnit(key, gDef(key));
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

	// ── B3 · EL DENOMINADOR DEL RANG, LLEGIBLE (esmena de Bea, 2026-07-31) ────────────────────
	// Quan el denominador del rang és més petit que la comarca sencera, «6 de 27» al costat de
	// «8 de 31» sembla arbitrari si no s'explica. Per això la targeta ho diu i en dona el MOTIU
	// (`kpis.js` el declara per mètrica; els motius són diferents i confondre'ls seria mentir amb
	// bona intenció). Res d'això calcula cap rang: es compara `n_amb_dada` —LLEGIT del mart— amb
	// el nombre de municipis de la comarca, i es tria un text. (C6 §4 intacte.)
	//
	// 2026-08-01 · LA PREGUNTA DE BEA A B3 ES TANCA A L'ARREL. «El rang de nacionalitat al
	// Berguedà no pot ser sobre 27»: ja no ho és. Retirat el llindar mínim N (vot de Bea), els
	// percentatges d'origen es publiquen per als 947 i la nacionalitat de la Pobla és «8 de 31»,
	// amb la Quar 2a de la comarca. La causa 'gov_denom_minn' ha desaparegut d'aquest mapa i el
	// seu text, dels catàlegs i18n. El mecanisme es queda viu perquè els altres DOS motius sí que
	// tenen forats de veritat: la renda que la FONT calla i la divisió impossible de
	// l'envelliment. Àncora nova: la Febró (43057) porta els dos a la mateixa fitxa.
	const GOV_DENOM: Record<string, () => string> = {
		gov_denom_font: () => m.gov_denom_font(),
		gov_denom_ratio: () => m.gov_denom_ratio(),
		gov_denom_nd: () => m.gov_denom_nd()
	};
	/** Motiu de l'absència d'una mètrica; el neutre si no en sabem la causa (mai una d'inventada). */
	const denomReason = (key: string | undefined): string =>
		GOV_DENOM[
			(key && GOVERN_DENOM_REASON[key]) || GOVERN_DENOM_REASON_DEFAULT
		]?.() ?? '';
	/** La comarca té més municipis que els que tenen la xifra → cal explicar el denominador. */
	const denomIncomplet = (n: number | undefined): boolean =>
		comarcaMunis > 0 && typeof n === 'number' && n > 0 && n < comarcaMunis;

	// ── EL RECOMPTE AL COSTAT DEL PERCENTATGE (2026-08-01) ───────────────────────────────────
	// Retirat el llindar, la nacionalitat estrangera es publica als 947 — també allà on el
	// percentatge és el més fràgil. Als pobles petits el numerador diu més que el quocient: «7 de
	// 44 habitants» s'entén i «15,91 %» sobre 44 persones enganya la vista. Les DUES xifres es
	// pinten: el % gran (que és el que el rang ordena) i el recompte a sota, amb el seu rètol
	// —«passaport no espanyol»— perquè no es confongui amb els «nascuts a l'estranger» de la
	// targeta del costat, que a la Quar són 6 i no 7 (conjunts diferents).
	// Cap càlcul (C6 §4): les dues xifres venen servides i el mapa de `kpis.js` diu quina va amb
	// quina; `verify-govern` comprova als 947 que el % servit és exactament aquest quocient.
	const GOV_RECOMPTE_MSG: Record<string, (a: { n: string; total: string }) => string> = {
		gov_nac_recompte: (a) => m.gov_nac_recompte(a)
	};
	function recompteLinia(key: string | undefined): string | null {
		const spec = key ? GOVERN_RECOMPTE[key] : undefined;
		if (!spec || !row) return null;
		const n = row.values[spec.comptador as MetricKey];
		const total = row.values[GOVERN_RECOMPTE_BASE as MetricKey];
		if (typeof n !== 'number' || typeof total !== 'number') return null;
		return (
			GOV_RECOMPTE_MSG[spec.msg]?.({
				n: formatInteger(n, locale),
				total: formatInteger(total, locale)
			}) ?? null
		);
	}

	// ── R-PINTA · LES DUES REFERÈNCIES DE LA TARGETA (vot de Bea: «farem B+D») ────────────────
	// Doctrina al capçal de `semantic/metrics.yml` («QUINES ES PINTEN»), mecànica a `kpis.js`
	// (`governReferences`, funció pura que el verificador exerceix sobre els 947). Aquí NOMÉS
	// es resolen els textos i es formaten les xifres: cap càlcul (C6 §4), cap denominador
	// escrit a mà (C6 §8.1). La xifra es formata amb la MATEIXA def del contracte que el valor
	// gran de la targeta, perquè les tres siguin comparables dígit a dígit.
	//
	// VOT DE BEA (2026-07-31): la mediana duu el NOM DE LA COMARCA escrit — «mediana del
	// Berguedà», no «mediana comarcal». Això arrossegava `gov_rang_cap` (que deia « · per valor a
	// {comarca}» just a sobre) i hauria pintat el nom DUES vegades a la mateixa targeta; per això
	// `gov_rang_cap` ha passat a « · per valor» i la comarca es diu UNA sola vegada, aquí, on
	// també importa (una mediana sense el seu perímetre no vol dir res). L'article el resol
	// `deComarca` amb la seva taula de gènere: una funció, no un `if` per comarca. Si la comarca
	// no hi és, es cau al rètol sense nom (`gov_ref_comarca_nd`) en comptes d'inventar l'article.
	const REF_LABEL: Record<string, () => string> = {
		gov_ref_comarca: () => {
			const c = deComarca(govern?.comarca ?? '', locale);
			return c ? m.gov_ref_comarca({ comarca: c }) : m.gov_ref_comarca_nd();
		},
		gov_ref_catalunya: () => m.gov_ref_catalunya()
	};
	// El denominador d'una MEDIANA es diu en municipis; el d'una PONDERADA, en unitats del seu
	// pes — i el pes NO sempre són habitants (`pct_noprincipal` es pondera per habitatges;
	// `index_envelliment`, per menors de 15). Cada pes porta el seu nom o no es pinta.
	const REF_DENOM: Record<string, (n: string) => string> = {
		gov_ref_denom_munis: (n) => m.gov_ref_denom_munis({ n }),
		gov_ref_denom_hab: (n) => m.gov_ref_denom_hab({ n }),
		gov_ref_denom_habitatges: (n) => m.gov_ref_denom_habitatges({ n }),
		gov_ref_denom_menors15: (n) => m.gov_ref_denom_menors15({ n })
	};
	type RefPintada = { id: string; label: string; value: string; unit: string; denom: string };
	/** Les referències d'una cel·la, ja formatades. Buida = no n'hi ha cap de pintable. */
	function refsPintades(cell: GovernCell | null, key: string | undefined): RefPintada[] {
		const def = key ? gDef(key) : undefined;
		if (!def) return [];
		const out: RefPintada[] = [];
		for (const r of governReferences(cell)) {
			const label = REF_LABEL[r.labelKey]?.();
			const denom = REF_DENOM[r.denomKey]?.(formatInteger(r.denom, locale));
			// Sense rètol o sense denominador NO es pinta: mai una xifra òrfena de procedència.
			if (!label || !denom) continue;
			out.push({ id: r.id, label, value: fmtValue(r.value, def), unit: gUnit(key as string), denom });
		}
		return out;
	}
	// ── W2 · EL RANG, CLICABLE (petició de Bea: «hem de poder clicar cada vegada que posi rang») ─
	// Destí: el llistat d'aquella mètrica a aquella comarca. Es construeix del NOM de comarca que
	// serveix el mart i de la CLAU de la mètrica (`metricaSlug`, derivada del contracte): cap URL
	// escrita a mà, i per tant cap manera que l'enllaç i la pàgina parlin de coses diferents.
	// Retorna `null` —i el rang es pinta sense enllaç— si falta la comarca o si la clau no és
	// rankejable: un enllaç trencat seria pitjor que cap enllaç.
	const rankKeys = new Set<string>(GOVERN_RANK_KEYS);
	function rangHref(key: string | undefined): string | null {
		const com = govern?.comarca;
		if (!com || !key || !rankKeys.has(key)) return null;
		return localizeHref(`/comarca/${toSlug(com)}/${metricaSlug(key)}`);
	}

	// Prefixa el signe a una variació ja formatada (la negativa ja porta el «−» d'Intl).
	function signed(s: string): string {
		return s.startsWith('-') || s.startsWith('−') ? s : `+${s}`;
	}

	// ── V3 · BARRES APILADES (edats i «d'on venim») ──────────────────────────────────────────
	// Cada barra és una PARTICIÓ del padró (suma exacta, verificada als 947 i re-verificada per
	// verify-govern sobre el dataset servit). El % de cada segment és la mateixa operació que
	// l'amplada del segment: la PRESENTACIÓ dels recomptes servits contra el padró servit — cap
	// dada nova es fabrica al front (les xifres citables són els recomptes, que segueixen al DOM).
	// La barra només es pinta si TOTS els components i el padró són números: cap segment inventat.
	type BarSeg = { key: MetricKey; band: string; v: number; pct: number };
	function barSegments(defs: { key: string; band: string }[]): BarSeg[] | null {
		if (!row || typeof row.values.poblacio !== 'number' || row.values.poblacio <= 0) return null;
		const total = row.values.poblacio;
		const segs: BarSeg[] = [];
		for (const d of defs) {
			const v = row.values[d.key as MetricKey];
			if (typeof v !== 'number') return null;
			segs.push({ key: d.key as MetricKey, band: d.band, v, pct: (v / total) * 100 });
		}
		return segs;
	}
	const edatsSegs = $derived(barSegments(EDATS_BANDS));
	const naixBands = $derived([
		{ key: NAIX_BAR_KEYS[0], band: m.gov_naix_cat() },
		{ key: NAIX_BAR_KEYS[1], band: m.gov_naix_resta() },
		{ key: NAIX_BAR_KEYS[2], band: m.gov_naix_estranger() }
	]);
	const naixSegs = $derived(barSegments(naixBands));

	// ── V3 · E13 — caveat de micromunicipi (doctrina al capçal de metrics.yml) ───────────────
	// Padró < 250 → les targetes per càpita físiques i les ràtios de recomptes petits porten la
	// nota visible (caveat, MAI emmascarar: el número incòmode és el senyal). El text exacte està
	// PENDENT DEL VOT de Bea (el concepte està votat; la frase, no).
	const isMicro = $derived(
		typeof row?.values.poblacio === 'number' && row.values.poblacio < E13_LLINDAR
	);
	const e13Keys = new Set<string>(E13_KEYS);
	const showE13 = (key: string | undefined): boolean => !!key && isMicro && e13Keys.has(key);

	// V3 §10 · frase plana de l'índex d'envelliment: «X persones de 65 o més per cada 100 menors
	// de 15» (X = el valor arrodonit a enter; la fórmula del contracte segueix a la procedència).
	function envellFrase(): string | null {
		const v = row?.values.index_envelliment;
		return typeof v === 'number' ? m.gov_envell_frase({ x: formatInteger(Math.round(v), locale) }) : null;
	}

	// V3 · capçalera de presència: la def del padró (contracte) i la seva cel·la de rang (mart).
	const presDef = $derived(gDef(PRESENCIA_KEY));
	const presCell = $derived(govern?.metrics?.[PRESENCIA_KEY] ?? null);

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

	// ── D9 · FRESCOR PER TARGETA (E5, esmenada per V3) ────────────────────────────────────────
	// Regla vinculant: la frescor va A CADA TARGETA, mai a un peu de pàgina global. Els vintages
	// NO són iguals (població 2025, habitatges 2021) i una sola data els aplanaria en una mentida.
	// V3 (vot de Bea, 2026-07-29): la línia de targeta és «cadència · darrera càrrega DD-MM-YYYY»
	// — el PROCÉS de refresc («sense procés automàtic» / la ruta del workflow) és cuina interna i
	// es MOU a /metodologia (la fitxa de cada mètrica el segueix dient; la informació no s'esborra
	// del sistema, canvia de planta). `actualitzacio: null` (derivades sense `origin_source` al
	// contracte) tampoc s'arrodoneix a un «anual» de consol: es diu que no està declarada.
	function cadenciaLabel(c: string | null): string {
		if (c === 'mensual') return m.gov_frescor_mensual();
		if (c === 'anual') return m.gov_frescor_anual();
		if (c === 'puntual') return m.gov_frescor_puntual();
		if (c === 'irregular') return m.gov_frescor_irregular();
		if (!c) return m.gov_frescor_nd();
		return c;
	}
	/** Data de càrrega ISO (YYYY-MM-DD, com viu al contracte) → DD-MM-YYYY per al lector
	 *  (decisió de Bea, 2026-07-29). El contracte no es toca: només la presentació. */
	function dataCarrega(iso: string): string {
		const m2 = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
		return m2 ? `${m2[3]}-${m2[2]}-${m2[1]}` : iso;
	}
	/** Línia de frescor d'una targeta: cadència · darrera càrrega DD-MM-YYYY (V3: el procés de
	 *  refresc ja NO s'hi diu — viu a la fitxa de /metodologia). */
	function frescorLine(f: Frescor | null | undefined): string {
		if (!f) return '';
		const parts = [cadenciaLabel(f.actualitzacio)];
		if (f.darrera_carrega) parts.push(m.gov_frescor_carrega({ data: dataCarrega(f.darrera_carrega) }));
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

	// ── Selector de municipi: salta a QUALSEVOL dels 947 (ordenat per nom, localitzat) ────────
	// W1 (esmena de Bea, 2026-07-31): «un cop seleccionat un municipi, des de dins només es poden
	// seleccionar municipis del Berguedà». Era cert i pitjor del que semblava: la llista es derivava
	// de `dataset.municipis` (els 31 del pilot), així que a la fitxa de Barcelona o de Girona el
	// municipi que s'està mirant NI TAN SOLS sortia a la seva pròpia llista. Ara la font és el
	// CATÀLEG dels 947 (cens de noms+codis de la geometria oficial), que és la mateixa columna
	// vertebral que ja resolia els slugs, els veïns i els miralls.
	// Degradació honesta: si el catàleg no arriba (artefacte absent), la llista cau als municipis
	// del dataset en comptes de quedar-se buida — mai una llista muda.
	// Es MOSTRA la forma corrent («la Pobla de Lillet») i s'ORDENA per la forma d'ÍNDEX
	// («Pobla de Lillet, la»): és justament per a què serveix, perquè l'article no apili els 131
	// municipis amb article sota les lletres «L» i «E». Cap de les dues formes canvia la URL
	// (`toSlug` les fa convergir; `verify-govern.mjs` ho exerceix sobre els 947).
	const cataleg = $derived(data.cataleg ?? []);
	const muniOptions = $derived.by(() => {
		const font: { ine5: string; nom: string }[] = cataleg.length
			? cataleg
			: Object.values(dataset.municipis).map((mr) => ({ ine5: mr.ine5, nom: mr.nom }));
		const items = font.map((mn) => ({
			ine5: mn.ine5,
			nom: nomCanonic(mn.nom),
			ordre: nomIndex(mn.nom),
			slug: toSlug(mn.nom)
		}));
		const coll = new Intl.Collator(locale === 'es' ? 'es-ES' : 'ca-ES');
		return items.sort((a, b) => coll.compare(a.ordre, b.ordre));
	});
	// L'`ine5` segueix sent la clau interna del selector (el `value` de cada opció); el slug només
	// és la cara pública de la URL, i es resol amb el mateix índex que ha construït la llista.
	const slugPerIne5 = $derived(new Map(muniOptions.map((o) => [o.ine5, o.slug])));
	function onPickMuni(e: Event) {
		const v = (e.currentTarget as HTMLSelectElement).value; // value = ine5 (clau interna)
		if (!v) return;
		const slug = slugPerIne5.get(v) ?? slugForIne5(v, dataset);
		goto(localizeHref(`/municipi/${slug}`));
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

<!-- RANG COMARCAL «k de n» (C6 §4: LLEGIT del mart, mai calculat aquí) + —B3, esmena de Bea—
     la línia que fa LLEGIBLE el denominador quan no és tota la comarca. Els tres llocs que
     pinten rang (capçalera de presència, targeta de mètrica, % de la barra de naixement)
     comparteixen aquest snippet perquè no puguin divergir: fins avui era el mateix marcatge
     copiat tres vegades. `key` només serveix per triar el MOTIU de l'absència.

     W2 (petició de Bea, 2026-07-31): «hem de poder clicar cada vegada que posi rang i accedir a
     cada llistat». Com que TOTS els rangs de la fitxa passen per aquí, fer-ho clicable en aquest
     únic lloc ho fa clicable a TOTS — no hi ha cap rang pintat fora d'aquest snippet, i
     `verify-govern.mjs` ho vigila. L'enllaç porta a `/comarca/<comarca>/<metrica>/`, on el «k de
     n» s'obre en la llista sencera. El destí es construeix del NOM de la comarca que serveix el
     mart i de la CLAU de la mètrica: cap URL escrita a mà. Si la clau no és rankejable (cas
     impossible amb `rang != null`, però la doctrina no depèn de la sort), es pinta el rang tal
     com abans, sense enllaç: un enllaç trencat és pitjor que cap enllaç. -->
<!-- El COS del rang («k de n» + el seu rètol), en un snippet propi perquè l'enllaç de W2 el
     pugui embolcallar sense DUPLICAR el marcatge: amb dues còpies (amb enllaç i sense) tornaria
     a ser possible que una divergís de l'altra, que és el que aquest snippet existeix per
     impedir. `verify-govern.mjs` compta que el marcatge hi surti UNA sola vegada. -->
{#snippet rangCos(cell: GovernCell)}
	<span class="gov-kpi__rankk"
		>{m.gov_rang_val({ k: String(cell.rang), n: String(cell.n_amb_dada) })}</span
	>
	<span class="gov-kpi__rankl"
		>{m.gov_rang_label()}{#if cell.empat} · {m.gov_rang_empat()}{/if}{m.gov_rang_cap()}</span
	>
{/snippet}

{#snippet rangComarcal(cell: GovernCell | null, key: string | undefined)}
	{#if cell && cell.rang != null}
		{@const href = rangHref(key)}
		<p class="gov-kpi__rank">
			{#if href}
				<a
					class="gov-kpi__ranka"
					{href}
					aria-label={m.gov_rang_llink({
						n: String(cell.n_amb_dada),
						comarca: deComarca(govern?.comarca ?? '', locale) ?? (govern?.comarca ?? '')
					})}
				>
					{@render rangCos(cell)}
				</a>
			{:else}
				{@render rangCos(cell)}
			{/if}
		</p>
		{#if denomIncomplet(cell.n_amb_dada)}
			<p class="gov-kpi__denom">
				{m.gov_denom_line({ n: String(cell.n_amb_dada), total: String(comarcaMunis) })}
				{denomReason(key)}
			</p>
		{/if}
		<!-- R-PINTA · LES DUES REFERÈNCIES (vot de Bea: «farem B+D»). Van DINS el bloc del rang,
		     no en un lloc propi: la comparació és la mateixa pregunta que el «k de n» —«contra
		     qui»— i separar-les tornaria a obrir la porta a tres còpies divergents. Així hereten
		     la posició del rang a cada punt de crida i, sobretot, la seva ADJACÈNCIA.
		     VOT DE BEA (2026-07-31): el rètol de la mediana duu ara el NOM DE LA COMARCA escrit
		     («mediana del Berguedà»), i és AQUÍ on la targeta el diu — una sola vegada. Per això
		     `gov_rang_cap`, la línia de sobre, ha deixat de dir-lo (« · per valor a {comarca}» →
		     « · per valor»): amb les dues, el nom hi sortia dues vegades seguides.
		     Ordre: la COMARCAL primer (mateix perímetre que el rang: el lector acaba de llegir
		     «de 31» i la mediana d'aquests mateixos 31 és la lectura següent), la CATALANA a
		     sota com a ancoratge igual a totes les targetes.
		     Cada xifra amb el seu denominador NOMENAT (C6 §8.1): la mediana en municipis, la
		     ponderada en unitats del seu pes. A `poblacio` només hi ha la comarcal (no té
		     ponderada) i la llista simplement en té una: cap buit, cap «n. d.» decoratiu. -->
		{@const refs = refsPintades(cell, key)}
		{#if refs.length}
			<div class="gov-kpi__refs">
				{#each refs as r (r.id)}
					<p class="gov-kpi__ref">
						<span class="gov-kpi__refv"
							>{r.value}{#if r.unit}<span class="u">{r.unit}</span>{/if}</span
						>
						<span class="gov-kpi__refx">
							<span class="gov-kpi__refl">{r.label}</span>
							<span class="gov-kpi__refd">{r.denom}</span>
						</span>
					</p>
				{/each}
			</div>
		{/if}
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

		<!-- Selector per saltar a QUALSEVOL municipi de Catalunya (W1; sempre disponible). -->
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
			     de Bea (C6 §8.1). P-947 (Bea, 2026-07-27): el tauler ja NO és exclusiu del Berguedà —
			     es pinta per a QUALSEVOL dels 947 que tingui l'artefacte (rang de la SEVA comarca via
			     `govern.catalunya.json`, tauler pel shard del municipi). Es mostra quan hi ha dada de
			     tauler (`govern`/`tauler`); en un entorn sense els artefactes (CI sense dades)
			     simplement no es pinta, mai una graella buida. -->
			{#if govern || tauler}
				<section class="ds-sec gov-board" aria-labelledby="gov-board-h">
					<div class="ds-sec__hd"><span class="ref">◆</span><h2 id="gov-board-h">{m.gov_board_title()}</h2></div>
					<p class="muni-sec__sub">{m.gov_board_sub()}</p>

					<!-- V3 · CAPÇALERA DE PRESÈNCIA: padró + ETCA JUNTS, a dalt de tot. Són la mateixa
					     pregunta —«quanta gent hi ha?»— amb dues respostes oficials: els empadronats i
					     la presència equivalent. Si divergeixen, el lector ho veu SOL — no ho
					     interpretem (P1/P2 ho reprendran quan E7b aterri). Absorbeix la targeta gran
					     del padró i la targeta ETCA del grup A (fora duplicats). La capçalera juga amb
					     les mateixes regles que qualsevol targeta (C6 §8.1): font, rang LLEGIT del
					     mart, motiu honest de no tenir sèrie i frescor. -->
					<div class="gov-pres tnum">
						<div class="gov-pres__col">
							<p class="gov-kpi__lab">
								<span class="pd dot--measured"></span>{m.muni_num_padro()}{#if presDef?.date}
									· {presDef.date}{/if}
							</p>
							{#if typeof row.values.poblacio === 'number'}
								<p class="gov-pres__v">
									{formatInteger(row.values.poblacio, locale)}<span class="u">{m.gov_pres_padro_u()}</span>
								</p>
							{:else}
								<p class="gov-pres__v gov-kpi__v--absent">{m.value_not_available()}</p>
							{/if}
							{@render rangComarcal(presCell, PRESENCIA_KEY)}
							{@render tendencia(trendsOf(PRESENCIA_KEY))}
							<p class="gov-kpi__src">{provenanceLine(presDef).src}</p>
							{@render frescor(presDef?.frescor)}
						</div>
						<div class="gov-pres__col">
							<p class="gov-kpi__lab"><span class="pd dot--measured"></span>{m.muni_num_etca()}</p>
							{#if etca !== null}
								<p class="gov-pres__v">{formatInteger(etca, locale)}<span class="u">hab.</span></p>
							{:else}
								<p class="gov-pres__v gov-kpi__v--absent">{m.muni_sense_dada_oficial()}</p>
							{/if}
							<!-- Text pla d'ETCA APROVAT per Bea (2026-07-29); on no n'hi ha, el motiu real. -->
							<p class="gov-pres__txt">{m.gov_pres_etca_txt()}</p>
							{#if etca === null}
								<p class="gov-pres__txt gov-pres__txt--absent">{m.gov_pres_etca_absent()}</p>
							{/if}
							<p class="gov-kpi__src">
								{m.gov_pres_etca_src()} · <a class="gov-pres__met" href={localizeHref('/metodologia')}>{m.gov_pres_etca_met()}</a>
							</p>
						</div>
						<p class="gov-pres__meta">
							<span>INE {ine5}</span>
							{#if row.idescat6}<span>Idescat {row.idescat6}</span>{/if}
						</p>
					</div>

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
										<!-- EL RECOMPTE, al costat del percentatge (2026-08-01) · retirat el llindar
										     mínim N, la xifra es publica als 947 i als pobles petits el NUMERADOR és
										     el que es pot llegir: «7 de 44 habitants» diu més que «15,91 %». Va amb
										     el seu rètol («passaport no espanyol») per no confondre's amb els
										     nascuts a l'estranger de la targeta del costat: a la Quar, 7 i 6. -->
										{#if recompteLinia(kpi.key)}
											<p class="gov-kpi__cru gov-kpi__cru--rec">{recompteLinia(kpi.key)}</p>
										{/if}
										<!-- V3 §10 · la traducció humana de l'índex d'envelliment (la fórmula ja hi és;
										     la frase plana, no hi era). -->
										{#if kpi.key === 'index_envelliment' && envellFrase()}
											<p class="gov-kpi__frase">{envellFrase()}</p>
										{/if}
										<!-- V3 §6 (vot de Bea: HUT sí) · el cru al costat del rati: el rati sol amaga
										     que a molts pobles «turisme reglat» vol dir pisos turístics. Les dues
										     xifres ja arriben servides; la seva font (única, C6 §8.1) es diu avall. -->
										{#if kpi.hut && typeof row.values.rtc_total === 'number' && typeof row.values.rtc_hut === 'number'}
											<p class="gov-kpi__cru">
												{m.gov_hut_cru({
													n: formatInteger(row.values.rtc_total, locale),
													hut: formatInteger(row.values.rtc_hut, locale)
												})}
											</p>
										{/if}
										<!-- E6/E11 · la tendència, amb el seu període SEMPRE (o el motiu de no tenir-ne). -->
										{@render tendencia(trendsOf(kpi.trendKey ?? kpi.key))}
										<!-- D11 · el límit que la dada NO diu de si mateixa: va DARRERE la tendència
										     perquè és el que la interpreta (el mecànic «no és al mart» primer, la
										     raó editorial després). Lloc de naixement = foto; l'única sèrie del
										     bloc és de nacionalitat, i la seva targeta ho declara. -->
										{#if kpi.note}
											<p class="gov-kpi__note">{govNote(kpi.note)}</p>
										{/if}
										<!-- V3 §9 · E13: caveat de micromunicipi (padró < 250) als per càpita físics
										     i a les ràtios de recomptes petits. Caveat, MAI emmascarar: el número
										     incòmode és el senyal. Text PENDENT DEL VOT de Bea. -->
										{#if showE13(kpi.key)}
											<p class="gov-kpi__note gov-kpi__note--e13">{m.gov_e13_micro()}</p>
										{/if}
										{#if cell && cell.rang != null}
											{@render rangComarcal(cell, kpi.key)}
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
										<!-- V3 §6 · la font del CRU («N establiments, M són HUT»): la font única del
										     registre (C6 §8.1) — el rati de dalt ja porta la seva fórmula. -->
										{#if kpi.hut}
											<p class="gov-kpi__src">{srcLine(gDef('rtc_total'))}</p>
										{/if}
										{@render frescor(def.frescor)}
									</article>
								{:else if kpi.kind === 'edats'}
									<!-- V3 §3 · ESTRUCTURA D'EDATS: UNA targeta amb barra apilada horitzontal
									     (0-14 · 15-64 · 65-84 · 85+). La barra diu la FORMA; les 8 xifres
									     (recompte i % per franja) segueixen al DOM i són citables. Procedència:
									     les 3 franges mesurades amb la seva font; la 15-64 amb la seva fórmula
									     de resta (C6 §8.1 no s'estova) i el seu caveat del contracte accessible. -->
									{@const d1564 = gDef('pob_15_64')}
									{@const p1564 = provenanceLine(d1564)}
									<article class="gov-kpi gov-kpi--bar">
										<p class="gov-kpi__lab"><span class="pd dot--measured"></span>{m.gov_kpi_edats()}</p>
										{#if edatsSegs}
											<div class="gov-bar" aria-hidden="true">
												{#each edatsSegs as s, i (s.key)}
													<span class="gov-bar__seg gov-bar__c{i}" style="flex-grow:{Math.max(s.v, 0.0001)}"></span>
												{/each}
											</div>
											<ul class="gov-bar__legend tnum">
												{#each edatsSegs as s, i (s.key)}
													<li>
														<span class="gov-bar__dot gov-bar__c{i}"></span>
														<span class="gov-bar__band">{s.band}</span>
														<span class="gov-bar__n">{formatInteger(s.v, locale)}</span>
														<span class="gov-bar__pct">{formatDecimal(s.pct, locale, 1)} %</span>
													</li>
												{/each}
											</ul>
										{:else}
											<p class="gov-kpi__v gov-kpi__v--absent">{m.value_not_available()}</p>
										{/if}
										<!-- El motiu de no tenir sèrie (límit de la FONT), UNA vegada per a la
										     partició sencera: les quatre franges comparteixen font i motiu. -->
										{@render tendencia(trendsOf('pob_0_14'))}
										<p class="gov-kpi__prov"><span class="gov-kpi__provk">ƒ</span> 15-64: {p1564.formula}</p>
										<p class="gov-kpi__src">{srcLine(gDef('pob_0_14'))}</p>
										{#if d1564.note}
											<!-- El caveat del contracte de la franja derivada, accessible sense
											     ocupar la targeta sencera. -->
											<details class="gov-kpi__caveat">
												<summary>{m.gov_edats_caveat_sum()}</summary>
												<p>{pick(d1564.note, locale)}</p>
											</details>
										{/if}
										{@render frescor(gDef('pob_0_14').frescor)}
									</article>
								{:else if kpi.kind === 'naixement'}
									<!-- V3 §3 · «D'ON VENIM»: UNA targeta amb barra apilada (Catalunya · resta
									     d'Espanya · estranger) + el % nascuts a l'estranger SERVIT (amb el seu
									     pendingRank). La nota «foto, no sèrie» hi va UNA vegada. V3-CONTRACTE:
									     els tres recomptes són MESURATS (formula: directe) → font sense ƒ. -->
									{@const pctDef = gDef('pct_nascuda_estranger')}
									{@const pctPrv = provenanceLine(pctDef)}
									{@const pctCell = govern?.metrics?.['pct_nascuda_estranger'] ?? null}
									<article class="gov-kpi gov-kpi--bar">
										<p class="gov-kpi__lab"><span class="pd dot--measured"></span>{m.gov_kpi_naixement()}</p>
										{#if naixSegs}
											<div class="gov-bar" aria-hidden="true">
												{#each naixSegs as s, i (s.key)}
													<span class="gov-bar__seg gov-bar__c{i}" style="flex-grow:{Math.max(s.v, 0.0001)}"></span>
												{/each}
											</div>
											<ul class="gov-bar__legend tnum">
												{#each naixSegs as s, i (s.key)}
													<li>
														<span class="gov-bar__dot gov-bar__c{i}"></span>
														<span class="gov-bar__band">{s.band}</span>
														<span class="gov-bar__n">{formatInteger(s.v, locale)}<span class="u">hab.</span></span>
													</li>
												{/each}
											</ul>
										{:else}
											<p class="gov-kpi__v gov-kpi__v--absent">{m.value_not_available()}</p>
										{/if}
										<!-- El % nascuts a l'estranger: xifra SERVIDA (no la recalculem aquí). -->
										{#if typeof row.values.pct_nascuda_estranger === 'number'}
											<p class="gov-naix__pct">
												<span class="k">{pick(pctDef.label, locale)}</span>
												<span class="v">{fmt(row, 'pct_nascuda_estranger')}<span class="u">%</span></span>
											</p>
										{/if}
										<!-- El motiu de no tenir sèrie (dada del mart), UNA vegada per la partició. -->
										{@render tendencia(trendsOf(NAIX_BAR_KEYS[0]))}
										{#if kpi.note}
											<p class="gov-kpi__note">{govNote(kpi.note)}</p>
										{/if}
										{#if pctCell && pctCell.rang != null}
											{@render rangComarcal(pctCell, 'pct_nascuda_estranger')}
										{:else if kpi.pendingRank}
											<p class="gov-kpi__norank">{m.gov_nova_norank()}</p>
										{/if}
										<p class="gov-kpi__prov"><span class="gov-kpi__provk">ƒ</span> {pctPrv.formula}</p>
										<p class="gov-kpi__src">{srcLine(gDef(NAIX_BAR_KEYS[0]))}</p>
										{@render frescor(gDef(NAIX_BAR_KEYS[0]).frescor)}
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
						{#if grp.g === 'A'}
							<!-- V3 §11 · la nota ÚNICA del grup: les dues particions (edats i lloc de
							     naixement) sumen exactament el padró — verificat als 947 (i re-verificat
							     per verify-govern sobre el dataset servit). UNA línia al peu del grup,
							     no quatre repeticions per targeta. -->
							<p class="gov-grp__nota">{m.gov_grp_a_nota()}</p>
						{/if}
					{/each}
					<p class="gov-board__foot">{m.muni_srcline()}</p>
				</section>
			{/if}

			<!-- P1 · EL VEREDICTE: la frase-mare de la IA (verificada), el primer cop d'ull. Només si
			     la lectura ve del model; si és reserva o no hi és, s'omet (degradació honesta).
			     OCULT per `MOSTRA_LECTURES_IA` fins a E7b (vegeu el <script>); la maquetació es conserva. -->
			{#if MOSTRA_LECTURES_IA && veredicte}
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

			<!-- V3 §7 · FORA DUPLICATS: la targeta gran del padró que vivia aquí està ABSORBIDA per la
			     capçalera de presència del tauler (padró + ETCA junts, a dalt de tot), inclosos els
			     identificadors INE/Idescat. -->

			<!-- P2 · LA LECTURA: la narració de la IA (verificada), per perfil. Cada afirmació porta la
			     seva naturalesa (mesura/inferència/interpretació) i la seva evidència (mètriques).
			     OCULT per `MOSTRA_LECTURES_IA` fins a E7b (vegeu el <script>); la maquetació es conserva. -->
			{#if MOSTRA_LECTURES_IA && hasLectures}
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

			<!-- V3 §7 · «ELS NÚMEROS CLAU» ELIMINADA SENCERA: les seves 4 xifres (padró, ETCA,
			     % no principal, renda) ja són al tauler — dues d'elles a la capçalera de presència.
			     Era duplicació estructural, no informació. -->

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
							<li><span class="preg__chip">{q}</span></li>
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

	/* (La capçalera de dades del municipi —.muni-card— va desaparèixer amb V3 §7: absorbida per
	   la capçalera de presència del tauler, .gov-pres.) */

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

	/* (La secció «Els números clau» i els seus estils s'han eliminat amb V3 §7: duplicava
	   4 xifres que ja són al tauler i a la capçalera de presència.) */

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

	/* Pregunta-li (preguntes suggerides). Pastilles de text ESTÀTIC des del 2026-07-20 (decisió de
	   Bea): no enllacen, així que no porten hover ni cap senyal d'interacció. */
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
		color: var(--dp-text);
		font-size: 0.92rem;
		line-height: 1.4;
	}
	.preg__chip::before {
		content: '? ';
		color: var(--dp-text-subtle);
		font-family: var(--dp-font-mono);
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
	/* W2 · el rang, clicable cap al llistat de la comarca. L'enllaç ABRAÇA el «k de n» i el seu
	   rètol perquè la zona de clic sigui tot el bloc, i es marca amb un subratllat discret al
	   rètol: el número ja crida prou l'atenció i no volem que sembli una altra xifra. */
	.gov-kpi__ranka {
		display: flex;
		align-items: baseline;
		gap: 7px;
		flex-wrap: wrap;
		text-decoration: none;
		color: inherit;
		border-radius: var(--dp-radius-sm);
	}
	.gov-kpi__ranka .gov-kpi__rankl {
		border-bottom: 1px dotted var(--dp-border-strong);
	}
	.gov-kpi__ranka:hover .gov-kpi__rankk {
		background: color-mix(in srgb, var(--dp-forest) 24%, var(--dp-bg));
	}
	.gov-kpi__ranka:hover .gov-kpi__rankl {
		color: var(--dp-text);
		border-bottom-style: solid;
	}
	.gov-kpi__ranka:focus-visible {
		outline: 2px solid var(--dp-border-strong);
		outline-offset: 2px;
	}
	.gov-kpi__norank {
		margin: 2px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		color: var(--dp-text-subtle);
		line-height: 1.4;
	}
	/* R-PINTA · les dues referències. UNA sola graella per a les dues files (cada `<p>` és
	   `display: contents`), i no una graella per fila: així les dues xifres cauen a la MATEIXA
	   columna, alineades a la dreta, i el contrast es llegeix d'una passada vertical amb el
	   valor gran de la targeta i el «k de n» (la Pobla, vidre: 48,6 · 49,8 · 22,9).
	   El rètol i el denominador van a DUES línies pròpies i no en una de sola que s'embolica:
	   mesurat a la targeta real (269 px), la versió d'una línia trencava de manera irregular i
	   ocupava 95 px; aquesta n'ocupa 61 amb el mateix text i sense cap salt lleig. Sense filet
	   ni caixa: la targeta ja porta prou capes i el brief avisa de no fer-ne un mur. */
	.gov-kpi__refs {
		display: grid;
		grid-template-columns: auto 1fr;
		column-gap: 7px;
		row-gap: 2px;
		align-items: baseline;
		margin: 4px 0 0;
	}
	.gov-kpi__ref {
		display: contents;
	}
	/* Un punt menys de pes que el «k de n»: la posició del municipi mana, la referència
	   acompanya. Mateixa família de display perquè les xifres s'alineïn òpticament. */
	.gov-kpi__refv {
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 600;
		font-size: 0.82rem;
		color: var(--dp-text-muted);
		text-align: right;
	}
	.gov-kpi__refv .u {
		font-family: var(--dp-font-mono);
		font-size: 0.55rem;
		color: var(--dp-text-subtle);
		margin-left: 2px;
	}
	.gov-kpi__refx {
		min-width: 0;
	}
	.gov-kpi__refl {
		display: block;
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		color: var(--dp-text-subtle);
		line-height: 1.35;
	}
	/* El denominador (C6 §8.1) va un pèl més tènue que el rètol, però mai amagat: és el que fa
	   que la xifra es pugui citar. Qui llegeix ràpid en salta; qui comprova, el troba. */
	.gov-kpi__refd {
		display: block;
		font-family: var(--dp-font-mono);
		font-size: 0.56rem;
		color: var(--dp-text-subtle);
		opacity: 0.85;
		line-height: 1.35;
	}
	/* B3 · el denominador del rang, explicat. Va enganxat al «k de n» (no és una nota de lectura
	   com `.gov-kpi__note`: és la lletra petita del número que hi ha just a sobre), en prosa i no
	   en versaleta de mono, perquè és una frase per llegir, no una etiqueta. */
	.gov-kpi__denom {
		margin: 3px 0 0;
		font-family: var(--dp-font-sans);
		font-size: 0.66rem;
		color: var(--dp-text-muted);
		line-height: 1.45;
		text-wrap: pretty;
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

	/* ── V3 · Capçalera de presència (padró + ETCA junts, a dalt del tauler) ─────────────── */
	.gov-pres {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
		gap: 12px 24px;
		padding: 15px 16px;
		margin: 4px 0 14px;
		background: var(--dp-surface);
		border: 1px solid var(--dp-border-strong);
		border-radius: var(--dp-radius-lg);
	}
	.gov-pres__col {
		display: flex;
		flex-direction: column;
		gap: 6px;
		min-width: 0;
	}
	.gov-pres__v {
		margin: 0;
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 800;
		font-size: 1.9rem;
		line-height: 1;
		color: var(--dp-text);
	}
	.gov-pres__v .u {
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--dp-text-subtle);
		margin-left: 5px;
	}
	/* La frase plana d'ETCA (text aprovat per Bea) i el motiu on Idescat no la publica. */
	.gov-pres__txt {
		margin: 0;
		font-size: 0.78rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
		max-width: 48ch;
		text-wrap: pretty;
	}
	.gov-pres__txt--absent {
		color: var(--dp-text-subtle);
	}
	.gov-pres__met {
		color: inherit;
	}
	.gov-pres__meta {
		grid-column: 1 / -1;
		margin: 2px 0 0;
		display: flex;
		gap: 14px;
		flex-wrap: wrap;
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		color: var(--dp-text-subtle);
	}

	/* ── V3 · Barres apilades (edats i «d'on venim») ─────────────────────────────────────── */
	/* La targeta de barra ocupa una mica més d'espai que una targeta estàndard. */
	.gov-kpi--bar {
		grid-column: span 2;
	}
	@media (max-width: 560px) {
		.gov-kpi--bar {
			grid-column: auto;
		}
	}
	.gov-bar {
		display: flex;
		height: 16px;
		border-radius: var(--dp-radius-sm);
		overflow: hidden;
		margin: 2px 0 0;
	}
	.gov-bar__seg {
		flex-basis: 0;
		min-width: 2px;
	}
	/* Escala de 4 tons sobre el verd de marca: la forma es llegeix sense semàfor de judici. */
	.gov-bar__c0 {
		background: color-mix(in srgb, var(--dp-forest, #2f6b4f) 88%, var(--dp-bg));
	}
	.gov-bar__c1 {
		background: color-mix(in srgb, var(--dp-forest, #2f6b4f) 55%, var(--dp-bg));
	}
	.gov-bar__c2 {
		background: color-mix(in srgb, var(--dp-forest, #2f6b4f) 32%, var(--dp-bg));
	}
	.gov-bar__c3 {
		background: color-mix(in srgb, var(--dp-forest, #2f6b4f) 16%, var(--dp-bg));
	}
	.gov-bar__legend {
		list-style: none;
		margin: 4px 0 0;
		padding: 0;
		display: grid;
		gap: 3px;
	}
	.gov-bar__legend li {
		display: flex;
		align-items: baseline;
		gap: 8px;
		font-size: 0.8rem;
		line-height: 1.4;
		color: var(--dp-text-muted);
	}
	.gov-bar__dot {
		width: 9px;
		height: 9px;
		border-radius: 2px;
		flex: none;
		align-self: center;
	}
	.gov-bar__band {
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
		color: var(--dp-text-muted);
		min-width: 5ch;
	}
	.gov-bar__n {
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 700;
		font-size: 0.95rem;
		color: var(--dp-text);
	}
	.gov-bar__n .u {
		font-family: var(--dp-font-mono);
		font-size: 0.58rem;
		color: var(--dp-text-subtle);
		margin-left: 3px;
	}
	.gov-bar__pct {
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		color: var(--dp-text-subtle);
	}
	/* El % nascuts a l'estranger (xifra servida) dins la targeta «d'on venim». */
	.gov-naix__pct {
		margin: 4px 0 0;
		display: flex;
		align-items: baseline;
		gap: 8px;
		flex-wrap: wrap;
	}
	.gov-naix__pct .k {
		font-size: 0.78rem;
		color: var(--dp-text-muted);
	}
	.gov-naix__pct .v {
		font-family: 'Archivo', var(--dp-font-display);
		font-weight: 700;
		font-size: 1.15rem;
		color: var(--dp-text);
	}
	.gov-naix__pct .u {
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		color: var(--dp-text-subtle);
		margin-left: 2px;
	}
	/* El caveat del contracte de la 15-64, accessible sense ocupar la targeta. */
	.gov-kpi__caveat {
		margin: 2px 0 0;
	}
	.gov-kpi__caveat summary {
		cursor: pointer;
		font-family: var(--dp-font-mono);
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--dp-text-subtle);
	}
	.gov-kpi__caveat p {
		margin: 4px 0 0;
		font-size: 0.72rem;
		line-height: 1.5;
		color: var(--dp-text-muted);
		text-wrap: pretty;
	}

	/* V3 §10 · la frase plana de l'índex d'envelliment (la traducció humana de la ràtio). */
	.gov-kpi__frase {
		margin: 0;
		font-size: 0.78rem;
		line-height: 1.45;
		color: var(--dp-text-muted);
		text-wrap: pretty;
	}
	/* V3 §6 · el cru de turisme («N establiments, M són HUT»). */
	.gov-kpi__cru {
		margin: 0;
		font-size: 0.78rem;
		line-height: 1.45;
		color: var(--dp-text-muted);
	}
	/* El RECOMPTE que acompanya un percentatge no és una nota al peu: als micromunicipis és la
	   xifra que de debò es pot llegir («7 de 44 habitants» contra «15,91 %»). Va just sota el
	   número gran i amb el color del text normal, no amb el de les fonts. */
	.gov-kpi__cru--rec {
		font-size: 0.83rem;
		color: var(--dp-text);
	}
	/* V3 §9 · E13: el caveat de micromunicipi, amb filet d'avís (no d'error). */
	.gov-kpi__note--e13 {
		border-left-color: var(--dp-warning, #b5612a);
	}
	/* V3 §11 · la nota única del grup «La gent» (les particions sumen el padró). */
	.gov-grp__nota {
		margin: 8px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		color: var(--dp-text-subtle);
		line-height: 1.45;
	}
</style>
