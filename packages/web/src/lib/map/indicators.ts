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
 * Claus de mètrica pintables al MAPA PÚBLIC DE CATALUNYA, en ordre editorial.
 *
 * RECONDUCCIÓ · FASE 0 (2026-06, `docs/dossier-consultoria-2026-06/01-reconduccio.md` §4): el mapa
 * públic NOMÉS mostra el que aguanta **sense llegenda defensiva**. Dels 11 indicadors que es
 * pintaven a tot CAT en queden TRES:
 *   1. `gap_pernocta_pct` — la població invisible (l'estrella, reenquadrada com a hipòtesi). DEFECTE.
 *   2. `pct_noprincipal` — % habitatge no principal (oficial, llegible d'un cop d'ull).
 *   3. `kg_hab_any` — residus kg/hab/any (mesura directa ARC, amb caveat).
 *
 * RETIRATS del mapa públic CAT (baixen a Berguedà o a context de fitxa en fases posteriors —no es
 * perden, es curen):
 *   · `tipologia` — els llindars no generalitzen fora del Berguedà (Barcelona=excursió). → Berguedà.
 *   · `index_turisme` — el proxy no capta la gran ciutat («Barcelona no té pressió»). → Berguedà/fora.
 *   · `carrega_total_est` — es confon amb el gap; difícil d'explicar. → fitxa interna/fora.
 *   · `restauracio_per_1000hab` — OSM infra-mapa el rural: mínim observat, no cens. → context de fitxa.
 *   · `IETR` — no s'entén a escala Catalunya. → Berguedà/fitxa.
 *   · `densitat_hab_km2` — Barcelona domina l'escala lineal; tornarà al mapa amb escala log (Fase 3).
 *   · `renda_neta_persona` — aporta poc al conjunt del mapa; distreu. → fitxa.
 *   · `divergencia_senyals` — no s'entén com a mapa; reconvertir en bandera interna de confiança.
 *
 * Les etiquetes/caveats d'aquests indicadors es conserven a `mapa/+page.svelte` perquè es reutilitzin
 * quan tornin a la vista Berguedà o a la fitxa; aquí, la llista és l'única font del que s'ofereix.
 */
export const MAP_INDICATORS: MetricKey[] = ['gap_pernocta_pct', 'pct_noprincipal', 'kg_hab_any'];

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
