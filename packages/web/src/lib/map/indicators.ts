/**
 * Indicadors seleccionables al mapa coroplètic (model de 3 capes · v2).
 *
 * L'indicador estrella de riusdegent ha evolucionat a TRES CAPES (docs/poblacio-real-metode.md v2)
 * que separen fenòmens diferents i NO s'han de confondre:
 *  - **L1 gap_pernocta_pct** — la «població invisible»: qui PERNOCTA al territori sense constar
 *    al padró (via consum elèctric domèstic). És una desviació amb signe → DIVERGENT centrat a 0
 *    (rampa teal↔porpra --dp-div2; porpra = positiu = població que el padró no veu). DEFECTE.
 *  - **L2 carrega_total_est** — la càrrega humana TOTAL (via residus, inclou excursionistes de
 *    dia). NO és «població»: és càrrega. Magnitud crua → seqüencial terra --dp-exposure (Jenks).
 *  - **L3 index_turisme** — la PRESSIÓ turística (hostaleria, via vidre/hab, 0-100). NO és
 *    població ni càrrega de persones. Índex normalitzat → seqüencial terra --dp-exposure.
 *
 * A més, la lectura territorial clàssica: IETR (índex), % habitatge no principal i residus kg/hab.
 *
 * S'ha RETIRAT del selector el `gap_pct` antic (gap de CÀRREGA d'una sola capa): ara és redundant
 * amb `carrega_total_est` i, dit «gap», es confondria amb el gap de pernocta. Queda al contracte
 * com a àlies de compatibilitat, però no es pinta (evitem dos «gap» al mapa).
 *
 * Les ETIQUETES no es codifiquen aquí: l'etiqueta editorial curta ve dels missatges i18n
 * (mapa/+page.svelte → INDICATOR_LABEL); la del contracte (MetricDef.label) és el fallback.
 * Aquí només triem QUINES claus i en quin ordre editorial.
 */

import type { MetricKey } from '$lib/contract/types';

/**
 * Claus de mètrica pintables al mapa, en ordre editorial.
 * Encapçala el gap de pernocta (L1, «població invisible»): és la nova signatura del projecte
 * i el que es veu primer en obrir el mapa. Després les altres dues capes (càrrega, pressió
 * turística) i la lectura territorial estructural.
 */
export const MAP_INDICATORS: MetricKey[] = [
	// Encapçala la TIPOLOGIA (Fase 1): la joia narrativa — diu QUIN TIPUS de pressió hi ha
	// (capital de serveis, segona residència, excursió, dormitori invisible, buit administratiu,
	// indeterminat), no «més/menys». Coloració CATEGÒRICA (un color per tipus), no rampa.
	'tipologia',
	'gap_pernocta_pct',
	'carrega_total_est',
	'index_turisme',
	// 2n proxy de la capa L3 (pressió turística): densitat de restauració d'OSM. Va al costat
	// d'`index_turisme` perquè el VALIDA (Spearman ≈ 0,54 vs vidre/hab i index_turisme). Densitat
	// 0+ (més = més hostaleria) → seqüencial terra --dp-exposure, igual que kg_hab_any.
	'restauracio_per_1000hab',
	'IETR',
	'pct_noprincipal',
	'kg_hab_any',
	// Densitat de població (hab/km², EMEX) — covariable estructural i driver de la base del model;
	// pintable a TOT CAT (F5). Magnitud positiva de rang ampli → seqüencial terra (Jenks).
	'densitat_hab_km2',
	// Atles de contradiccions: divergència dels 3 senyals de presència (0-100). Fosc = els
	// senyals físics es contradiuen → llegir amb prudència. Converteix la incertesa en producte.
	'divergencia_senyals'
];

/** Indicador per defecte en obrir el mapa: la població invisible (gap de pernocta, L1). */
export const DEFAULT_INDICATOR: MetricKey = 'gap_pernocta_pct';

/**
 * HONESTEDAT CARTOGRÀFICA — el 0 d'OSM NO és «sense hostaleria».
 *
 * `restauracio_per_1000hab` ve d'un recompte d'OpenStreetMap (via Overpass): un **MÍNIM
 * observat, no un cens**. OSM infra-mapeja el rural, així que 6 micromunicipis (Castell de
 * l'Areny, Fígols, Montclar, la Quar, Sant Jaume de Frontanyà, Viver i Serrateix) surten amb
 * compte 0 tot i que 4-5 tenen `vidre_hab` alt (senyal d'hostaleria present). Pintar aquests 0
 * com «la classe més baixa» seria FALS: és buit de mapejat, no absència real.
 *
 * Regla específica d'aquest indicador: tractem el **valor 0 com a sense-dada-fiable**. La funció
 * `mapValue` retorna `null` per a aquests casos, de manera que:
 *  - la CLASSIFICACIÓ (Jenks) no els pren com a mínim i no els assigna a cap classe de color;
 *  - el MAPA els renderitza amb el **tramat de «sense dada»** que ja existeix (via `__hasval`
 *    fals al join del ChoroplethMap), no amb el color de classe baixa;
 *  - el TOOLTIP els mostra com a «sense dada» en comptes de «0,0 per mil».
 * La llegenda/caveat ho deixa explícit. (És l'única clau amb aquest tractament; per a la resta
 * un 0 real és un 0.)
 */
export const OSM_COUNT_ZERO_AS_NODATA: ReadonlySet<MetricKey> = new Set(['restauracio_per_1000hab']);

/**
 * Valor «efectiu» d'un indicador per al mapa: idèntic al cru EXCEPTE per a les claus de recompte
 * d'OSM (vegeu `OSM_COUNT_ZERO_AS_NODATA`), on un 0 és buit de mapejat i es degrada a `null`
 * (sense-dada-fiable) perquè classificació, pintat i tooltip el tractin com a tal i no com a
 * «classe més baixa». Centralitzat aquí perquè les tres vies de render coincideixin.
 */
export function mapValue(
	key: MetricKey,
	raw: number | string | null | undefined
): number | string | null {
	if (OSM_COUNT_ZERO_AS_NODATA.has(key) && raw === 0) return null;
	return raw ?? null;
}
