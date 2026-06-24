/**
 * Indicadors a escala CATALUNYA per al mapa — forma de `data/indicadors-catalunya.json`.
 *
 * El genera `tools/export_indicadors_cat.py`. Per a cada municipi, els valors dels indicadors que
 * tenim a TOT Catalunya (no només el Berguedà), amb la MATEIXA clau de mètrica que el selector del
 * mapa, perquè la vista municipi pugui pintar tots els munis pel mateix indicador:
 *   · `gap_pernocta_pct` (presència vs padró, %)  · `kg_hab_any` (residus kg/hab/any)
 * Els indicadors només-Berguedà (tipologia, IETR, restauració…) NO hi són → la resta de Catalunya
 * queda «sense dada» honesta per a aquests.
 *
 * A més, `conf` (confiança baixa/mitjana/alta) per a cada muni — per a les TRAMES del mapa (confiança
 * baixa velada, igual que al Berguedà) i el tooltip uniforme. Clau `conf` (no `confianca`) per no xocar
 * amb la MetricKey homònima del contracte.
 */
import type { MetricKey } from './types';

export type IndicadorsCatData = Record<
	string,
	Partial<Record<MetricKey, number>> & { conf?: string }
>;
