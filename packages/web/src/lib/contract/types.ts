/**
 * Tipus del contracte semàntic (datapoble).
 *
 * Mirall en TypeScript de `semantic/metrics.yml` — el CONTRATO ÚNICO que comparteixen
 * el pipeline (Sondeig/transform), la IA (Brúixola) i el frontend (Mirador).
 *
 * Regla del contracte: cap mètrica sense `label` (ca+es), `source` i (quan escau) `date`.
 * Les etiquetes NO es codifiquen a la UI ni als catàlegs i18n del producte: vénen d'aquí,
 * que reflecteix `label.ca` / `label.es` de metrics.yml. La traducció d'idioma de
 * l'etiqueta és, doncs, dada del contracte, no missatge d'interfície.
 *
 * Quan el pipeline publiqui els marts (parquet/JSON) o l'API, aquesta forma és el
 * que esperem rebre. El loader real (`src/lib/data/dataset.ts`) carrega l'artefacte
 * `data/web/municipis.bergueda.json` (generat per Sondeig des dels marts) amb aquesta
 * mateixa forma; els 31 municipis del Berguedà amb dades reals.
 */

/** Locales del producte. en/fr són ampliables via catàlegs i18n. */
export type Locale = 'ca' | 'es';

/** Text traduïble tal com apareix al contracte (label/unit/definicio). */
export type Localized = Record<Locale, string>;

/**
 * Clau d'unió: codi INE de 5 dígits (`join_key: ine5` al contracte).
 * Atenció a la trampa de codis: Castellar de n'Hug = "08052" a INE/Idescat
 * però "08051" a Catastro. Aquí sempre fem servir l'INE5.
 */
export type Ine5 = string;

/**
 * Claus de mètrica del contracte (columnes de `mart_municipi`).
 * Mantingudes 1:1 amb `metrics.yml` perquè el join amb el mart sigui directe.
 */
export type MetricKey =
	// Demografia / vivenda
	| 'poblacio'
	| 'hab_total'
	| 'hab_principal'
	| 'hab_noprincipal'
	| 'pct_noprincipal'
	| 'hab_per_hab'
	| 'index_envelliment'
	| 'densitat_hab_km2'
	| 'renda_neta_persona'
	// Franges d'edat (D7 · E12 de Bea): ja s'ingerien d'EMEX i el mart les llençava. `pob_15_64`
	// i `pob_65_mes` són DERIVADES (la primera per resta, i pot ser `null` si algun dia no quadra);
	// la seva línia de procedència és, doncs, FÓRMULA, no font (C6 §8.1).
	| 'pob_0_14'
	| 'pob_15_64'
	| 'pob_65_84'
	| 'pob_85_mes'
	| 'pob_65_mes'
	// Origen: composició i arrelament (capa sensible; lectura ecològica, mai individual)
	| 'poblacio_nascuda_catalunya'
	| 'poblacio_nascuda_resta_espanya'
	| 'poblacio_nascuda_estranger'
	| 'pct_nascuda_estranger'
	| 'pct_nacionalitat_estrangera'
	| 'bretxa_naturalitzacio'
	| 'delta_pct_estrangera_finestra'
	| 'confianca_origen'
	// Turisme
	| 'rtc_total'
	| 'rtc_hut'
	| 'rtc_per_1000hab'
	| 'rtc_per_100hab_viv'
	// Pressió / càrrega real
	| 'kg_hab_any'
	// Senyals físics per càpita (inputs de les 3 capes)
	| 'kwh_hab'
	| 'vidre_hab'
	// Base-ratios: pressió absoluta vs base residencial (×base)
	| 'residu_base_ratio'
	| 'kwh_base_ratio'
	| 'vidre_base_ratio'
	// 2n proxy d'hostaleria de la capa L3 (restauració OSM, complement del vidre)
	| 'restauracio_estab'
	| 'restauracio_per_1000hab'
	// Senyal de centralitat funcional (comerç i serveis, OSM): redefineix capital_serveis.
	| 'serveis_estab'
	| 'serveis_per_1000hab'
	// Indicador estrella — MODEL DE 3 CAPES (mètode v2 a docs/poblacio-real-metode.md):
	//  L1 població que PERNOCTA (via elèctric) → la «població invisible»
	| 'poblacio_pernocta_est'
	| 'gap_pernocta'
	| 'gap_pernocta_pct'
	//  L2 CÀRREGA per residus (via residus, inclou excursionistes de dia; pot ser < L1)
	| 'carrega_total_est'
	//  Denominador funcional: max(L1, L2) — el sostre per governar serveis
	| 'carrega_funcional_est'
	// (`index_turisme` DEPRECAT i FORA dels publicadors —#267/#268, D4—: satura a 100 en 47
	//  municipis; substituït per `kwh_hab`/`vidre_hab`. Retirat del tipus: ja no és al JSON.)
	// Compatibilitat (model d'una sola capa, reenquadrat com a càrrega) + confiança
	| 'poblacio_real_est'
	| 'poblacio_real_rel'
	| 'gap_abs'
	| 'gap_pct'
	| 'confianca'
	// Fase 1 — endurir el model (derivats sobre senyals existents, docs/tipologia-municipal.md):
	//  · tipologia: CATEGÒRICA — quin TIPUS de pressió (no «més/menys»); la joia narrativa.
	//  · confianca_score: 0-100 auditable, complementa la bandera `confianca` (alta/mitjana/baixa).
	//  · IETR dual: els dos costats de l'IETR (estructural/stock + pressió realitzada/impacte).
	| 'tipologia'
	| 'confianca_score'
	//  · divergencia_senyals: 0-100, el component de concordança exposat sol (auditar el «per què»).
	| 'divergencia_senyals'
	// Energia / rehabilitació
	| 'pct_icaen_EFG'
	// Índex IETR
	| 'IETR'
	| 'IETR_rank'
	| 'IETR_stock'
	| 'IETR_impact';

/**
 * Format de presentació d'una mètrica. Determina com Intl.NumberFormat
 * formata el valor segons el locale actiu (decimals, percentatge, enter...).
 */
export type MetricFormat = 'integer' | 'decimal' | 'percent' | 'ratio' | 'rank' | 'text';

/**
 * FRESCOR d'una mètrica (D7 · E5 de Bea): les dues coses que la frescor és, separades —
 * la CADÈNCIA declarada i el PROCÉS que la refresca de veritat.
 *
 * Ve de `sources.<font>` del contracte, amb override per mètrica quan la seva cadència no és
 * la de la font (p. ex. els habitatges: font anual, però Cens decennal → `puntual`).
 *
 * Honestedat (E5): `proces_refresc: "cap"` NO és un forat a amagar, és la declaració que cal
 * ensenyar — «anual · darrera càrrega 2026-06-21 · sense procés automàtic». I `actualitzacio:
 * null` (les 5 mètriques compostes amb `font_frescor: "datapoble"`, que creuen fonts) tampoc
 * s'arrodoneix: es diu que la cadència no està declarada.
 */
export interface Frescor {
	/** Cadència declarada: `mensual|anual|puntual|irregular`. `null` = no declarada al contracte. */
	actualitzacio: string | null;
	/** Data (ISO) de l'última càrrega de la font al pipeline. */
	darrera_carrega: string | null;
	/** Procés que la refresca: ruta del workflow, `"cap"` si no n'hi ha, `null` si no es declara. */
	proces_refresc: string | null;
	/** Clau de la font de la qual s'hereta la frescor (`datapoble` = mètrica composta). */
	font_frescor: string | null;
}

/**
 * Definició d'un indicador (metadades del contracte, independents del municipi).
 * Reflecteix els camps de metrics.yml que la UI necessita per pintar amb procedència.
 */
export interface MetricDef {
	key: MetricKey;
	/** label.ca / label.es del contracte. La UI MAI no codifica això. */
	label: Localized;
	/**
	 * Definició canònica del contracte (definicio.ca/.es de metrics.yml) — el text del
	 * «diccionari» que pinta el glossari. Opcional perquè l'export actual del dataset
	 * (`tools/export_web_municipis.py`) encara NO l'emet (handoff a Sondeig); el glossari
	 * la llegeix si hi és i, si no, recau en `note`. Mai es codifica a la UI.
	 */
	definicio?: Localized;
	/** Unitat de mesura (unit del contracte). "%" és comú a ambdós locales. */
	unit: Localized;
	dimension:
		| 'demografia'
		| 'vivenda'
		| 'turisme'
		| 'serveis'
		| 'pressio'
		| 'energia'
		| 'index';
	format: MetricFormat;
	/** Organisme/producte de la font (sources.* del contracte). */
	source: string;
	/** Any o rang de referència de la dada. */
	date?: string;
	/**
	 * Fórmula del contracte (formula de metrics.yml): cadena plana ("hab_noprincipal /
	 * hab_total * 100" o "directe"). Regla de ferro de Bea (C6 §8.1): cada xifra amb la
	 * seva font O fórmula. Opcional perquè és additiu (l'emet `export_web_municipis.py`
	 * des de D4); la vista de govern (D5) mostra font per a les mesurades i fórmula per a
	 * les inferides. No és `Localized`: la fórmula és la mateixa en tots dos locales.
	 */
	formula?: string;
	/**
	 * Cadència + procés de refresc (D7 · E5). Opcional perquè és additiu; el tauler la mostra
	 * PER TARGETA i mai de forma global: els vintages NO són iguals (població 2025 vs habitatges
	 * 2021) i una sola data de peu de pàgina els aplanaria.
	 */
	frescor?: Frescor;
	/** Nota/caveat (ex.: lectura ecològica, falàcia ecològica). */
	note?: Localized;
	/** public = visible · planned = definit, encara no calculat. */
	status?: 'public' | 'planned';
}

/**
 * Valor d'una mètrica per a un municipi concret. `null` = no disponible (n. d.).
 * Per a les categòriques (p. ex. `tipologia`, `confianca`) el valor és text; la resta, numèrics.
 */
export type MetricValue = number | string | null;

/** Fila del mart per municipi: identitat + mapa de valors per clau de mètrica. */
export interface MunicipiRow {
	ine5: Ine5;
	/** Nom oficial del municipi (topònim; igual en ambdós locales). */
	nom: string;
	/** Codi Idescat de 6 dígits (per a l'API EMEX). Derivat, no és la join key. */
	idescat6?: string;
	values: Partial<Record<MetricKey, MetricValue>>;
}

/**
 * Artefacte que consumeix la pantalla "resum": catàleg d'indicadors (del contracte)
 * + files de municipis (del mart). És la forma que esperem del pipeline/API.
 */
export interface MunicipisDataset {
	/** Versió del contracte semàntic (meta.version a metrics.yml). */
	contractVersion: string;
	/** Àmbit del dataset (meta.scope). */
	scope: string;
	/** Catàleg de definicions d'indicador, indexat per clau. */
	metrics: Record<MetricKey, MetricDef>;
	/** Files per municipi, indexades per INE5. */
	municipis: Record<Ine5, MunicipiRow>;
	/** Resum comarcal precalculat (KPIs agregats). */
	comarca: ComarcaSummary;
}

/** KPIs a escala comarcal (Berguedà). En producció els calcula el pipeline. */
export interface ComarcaSummary {
	label: Localized;
	/** Nombre de municipis de la comarca. */
	num_municipis: number;
	/** Valors agregats per clau de mètrica (mitjana/suma segons la mètrica). */
	values: Partial<Record<MetricKey, MetricValue>>;
}
