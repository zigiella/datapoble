/**
 * Indicadors seleccionables al mapa coroplètic — APARADOR OFICIAL.
 *
 * FASE NOVA · MODEL APARCAT (vot de Bea 2026-07-16 · `docs/ajuntaments/gorra-alcalde-pobla.md` §1
 * + `docs/ajuntaments/fase-nova-aparcaments.md` §A6): el model d'estimació de pernocta (les 3
 * capes) surt del web. El /mapa ES MANTÉ, podat (decisió §F.3): només indicadors OFICIALS amb
 * dada a tot Catalunya. El gap de pernocta i la resta de capes del model no es pinten; el seu
 * rastre metodològic viu a /metodologia (annex de recerca) i a l'experiment geo-rag.
 *
 * Les ETIQUETES no es codifiquen aquí: l'etiqueta editorial curta ve dels missatges i18n
 * (mapa/+page.svelte → INDICATOR_LABEL); la del contracte (MetricDef.label) és el fallback.
 * Aquí només triem QUINES claus i en quin ordre editorial.
 */

import type { MetricKey } from '$lib/contract/types';

/**
 * Claus de mètrica pintables al MAPA PÚBLIC DE CATALUNYA, en ordre editorial. Totes OFICIALS:
 *   1. `pct_noprincipal` — % habitatge no principal (Cens 2021, llegible d'un cop d'ull). DEFECTE.
 *   2. `kg_hab_any` — residus kg/hab/any (mesura directa ARC, amb caveat).
 */
export const MAP_INDICATORS: MetricKey[] = ['pct_noprincipal', 'kg_hab_any'];

/** Indicador per defecte en obrir el mapa: % habitatge no principal (oficial). */
export const DEFAULT_INDICATOR: MetricKey = 'pct_noprincipal';

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
