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
 * que esperem rebre. Mentrestant, `src/lib/mock/municipis.ts` la implementa amb dades
 * verificades del prototip (docs/data-sources.md).
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
 * Claus de mètrica del contracte (columnes de `mart_municipi` / `mart_electoral`).
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
	// Turisme
	| 'rtc_total'
	| 'rtc_hut'
	| 'rtc_per_1000hab'
	| 'rtc_per_100hab_viv'
	// Pressió / càrrega real
	| 'kg_hab_any'
	// Energia / rehabilitació
	| 'pct_icaen_EFG'
	// Índex IETR
	| 'IETR'
	| 'IETR_rank'
	// Política (lectura ecològica)
	| 'pct_indep'
	| 'pct_esquerra'
	| 'pct_extrema_dreta'
	| 'guanya';

/**
 * Format de presentació d'una mètrica. Determina com Intl.NumberFormat
 * formata el valor segons el locale actiu (decimals, percentatge, enter...).
 */
export type MetricFormat = 'integer' | 'decimal' | 'percent' | 'ratio' | 'rank' | 'text';

/**
 * Definició d'un indicador (metadades del contracte, independents del municipi).
 * Reflecteix els camps de metrics.yml que la UI necessita per pintar amb procedència.
 */
export interface MetricDef {
	key: MetricKey;
	/** label.ca / label.es del contracte. La UI MAI no codifica això. */
	label: Localized;
	/** Unitat de mesura (unit del contracte). "%" és comú a ambdós locales. */
	unit: Localized;
	dimension: 'demografia' | 'vivenda' | 'turisme' | 'pressio' | 'energia' | 'index' | 'politica';
	format: MetricFormat;
	/** Organisme/producte de la font (sources.* del contracte). */
	source: string;
	/** Any o rang de referència de la dada. */
	date?: string;
	/** Nota/caveat (ex.: lectura ecològica, falàcia ecològica). */
	note?: Localized;
	/** public = visible · planned = definit, encara no calculat. */
	status?: 'public' | 'planned';
}

/**
 * Valor d'una mètrica per a un municipi concret. `null` = no disponible (n. d.).
 * Per a `guanya` (candidatura) el valor és text; la resta són numèrics.
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
