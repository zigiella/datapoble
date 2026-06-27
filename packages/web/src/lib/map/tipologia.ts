/**
 * Diccionari de presentació de la `tipologia` d'habitança (datapoble · Fase 1, Mirador).
 *
 * `tipologia` és una mètrica CATEGÒRICA (no «més/menys»): classifica cada municipi amb un NOM
 * que diu QUIN TIPUS de pressió hi ha. És la joia narrativa del mapa. El classificador (regles
 * sobre z-scores comarcals) viu al mart (docs/tipologia-municipal.md); aquí NOMÉS la presentació:
 *  - l'ORDRE editorial dels arquetips (de més «ple/estructural» a més «buit», amb l'honest al final);
 *  - un COLOR categòric per tipus (no rampa) — paleta neta, distingible i coherent amb la marca;
 *  - les ETIQUETES i FRASES curtes localitzades (ca/es), via missatges i18n (no es codifiquen aquí
 *    les cadenes: vénen de `$lib/paraglide/messages`, com la resta del producte).
 *
 * Honestedat: `indeterminat` NO és un buit lleig. És un estat HONEST (territori mixt, 15 dels 31
 * municipis del Berguedà): senyals ambigus on forçar un calaix seria inventar una narració. Per
 * això va en NEUTRE (gris càlid), llegible com a «el model no ho força», no com a «sense dada»
 * (que és el tramat). És l'únic to no saturat de la paleta.
 *
 * La PALETA (decisió de disseny, CVD-raonable — provada amb deuteranopia/protanopia/tritanopia
 * simulades; vegeu la bitàcola). Es manté SEPARADA de les rampes de dada (--dp-exposure / --dp-div2):
 * la categòrica no comunica ordre, comunica identitat. Tot i així lliga amb la marca i amb la
 * procedència del projecte:
 *  - `capital_serveis`  → OCRE de marca (--dp-brand): la pressió estructural «de debò», l'àncora càlida.
 *  - `excursio`         → groc/ambre (exposure-2): activitat de DIA, transitòria; càlid però clar,
 *                          ben separat de l'ocre per lluminositat.
 *  - `segona_residencia`→ PORPRA (--dp-prov-derived): llits que s'omplen = població que el padró no
 *                          veu = inferència; el mateix to que la procedència «derivada».
 *  - `dormitori_invisible`→ verd-teal: hi dormen sense constar, amb poca hostaleria; fred, distingible
 *                          de la porpra.
 *  - `buit_administratiu`→ ÀLIES de UI: es presenta com `indeterminat` (decisió 2026-06-10). La
 *                          paraula «buit» sobre munis amb petjada ALTA (Fígols, 760 kg/hab) era
 *                          insostenible. La dada i el classificador NO canvien; pendent del rework de tipologia.
 *  - `indeterminat`     → GRIS CÀLID neutre: estat honest (vegeu sobre).
 */

import type { MetricKey } from '$lib/contract/types';
import { m } from '$lib/paraglide/messages';

/** Valor canònic (snake_case) de la `tipologia` tal com l'emet el mart. */
export type TipologiaValue =
	| 'capital_serveis'
	| 'segona_residencia'
	| 'excursio'
	| 'dormitori_invisible'
	| 'buit_administratiu'
	| 'indeterminat';

/** Descriptor de presentació d'un arquetip de tipologia. */
export interface TipologiaMeta {
	value: TipologiaValue;
	/** Color categòric (hex literal: el canvas de MapLibre no resol les custom properties). */
	color: string;
	/** Etiqueta humana localitzada (ca/es), via i18n. */
	label: () => string;
	/** Frase curta del que vol dir (ca/es), via i18n — el «què és» d'una línia. */
	blurb: () => string;
}

/**
 * Els 5 arquetips en ORDRE editorial (de més estructural/ple a més buit; l'honest `indeterminat`
 * tanca). Aquest ordre el segueix la LLEGENDA categòrica. Els colors són literals (sincronitzats
 * amb els tokens de marca/procedència del design-system, però no poden ser var() dins del canvas).
 */
export const TIPOLOGIA_ORDER: readonly TipologiaMeta[] = [
	{
		value: 'capital_serveis',
		color: '#B5612A', // --dp-brand (ocre de marca)
		label: () => m.tipo_capital_serveis_label(),
		blurb: () => m.tipo_capital_serveis_blurb()
	},
	{
		value: 'segona_residencia',
		color: '#7A5BA6', // --dp-prov-derived (porpra · inferència / població invisible)
		label: () => m.tipo_segona_residencia_label(),
		blurb: () => m.tipo_segona_residencia_blurb()
	},
	{
		value: 'excursio',
		color: '#E1A23A', // ambre (família exposure-2, clar i càlid; ≠ ocre de marca)
		label: () => m.tipo_excursio_label(),
		blurb: () => m.tipo_excursio_blurb()
	},
	{
		value: 'dormitori_invisible',
		color: '#3E9B8E', // verd-teal (fred, distingible de la porpra)
		label: () => m.tipo_dormitori_invisible_label(),
		blurb: () => m.tipo_dormitori_invisible_blurb()
	},
	{
		value: 'indeterminat',
		color: '#ADA89B', // GRIS CÀLID neutre — estat honest (territori mixt), no «buit lleig»
		label: () => m.tipo_indeterminat_label(),
		blurb: () => m.tipo_indeterminat_blurb()
	}
] as const;

/** Color «sense classificar» (valor de tipologia desconegut/absent): gris neutre fred, tramat a part. */
const TIPOLOGIA_UNKNOWN_COLOR = '#C9C6BF';

const BY_VALUE: ReadonlyMap<string, TipologiaMeta> = new Map(
	TIPOLOGIA_ORDER.map((t) => [t.value, t])
);

/** La clau de mètrica que ès categòrica (avui només `tipologia`). */
export const CATEGORICAL_KEY: MetricKey = 'tipologia';

/** True si la clau de mètrica es pinta de forma categòrica (no rampa). */
export function isCategorical(key: MetricKey): boolean {
	return key === CATEGORICAL_KEY;
}

/**
 * Àlies de PRESENTACIÓ (no de dada): valors que el mart emet però que la UI col·lapsa en un altre
 * arquetip. `buit_administratiu`→`indeterminat` (decisió 2026-06-10, pendent del rework de tipologia):
 * «buit» sobre munis amb petjada alta (Fígols) era insostenible. El classificador i la dada no canvien.
 */
const UI_ALIAS: Readonly<Record<string, TipologiaValue>> = {
	buit_administratiu: 'indeterminat'
};

/** Metadades d'un valor de tipologia (o undefined si el valor no és conegut). Aplica UI_ALIAS. */
export function tipologiaMeta(value: unknown): TipologiaMeta | undefined {
	if (typeof value !== 'string') return undefined;
	return BY_VALUE.get(UI_ALIAS[value] ?? value);
}

/** Color categòric d'un valor de tipologia; cau al neutre desconegut si el valor no és vàlid. */
export function tipologiaColor(value: unknown): string {
	return tipologiaMeta(value)?.color ?? TIPOLOGIA_UNKNOWN_COLOR;
}

/** Etiqueta humana d'un valor de tipologia (o el valor cru com a últim recurs). */
export function tipologiaLabel(value: unknown): string {
	const meta = tipologiaMeta(value);
	return meta ? meta.label() : typeof value === 'string' ? value : '';
}

/** Frase curta («què és») d'un valor de tipologia (o cadena buida si no es coneix). */
export function tipologiaBlurb(value: unknown): string {
	return tipologiaMeta(value)?.blurb() ?? '';
}

/**
 * Expressió `match` de MapLibre per al color categòric de la tipologia: mapa valor→color
 * sobre la feature property `__cat` (la cadena de tipologia injectada al join). El fallback és
 * el neutre desconegut. Es construeix amb l'ordre editorial perquè sigui determinista.
 */
export function tipologiaMatchExpression(valExpr: unknown = ['get', '__cat']): unknown {
	const pairs: unknown[] = [];
	for (const t of TIPOLOGIA_ORDER) {
		pairs.push(t.value, t.color);
	}
	// Àlies de UI: el valor de dada (p.ex. buit_administratiu) s'acoloreix com el seu arquetip de presentació.
	for (const [alias, target] of Object.entries(UI_ALIAS)) {
		const meta = BY_VALUE.get(target);
		if (meta) pairs.push(alias, meta.color);
	}
	// `valExpr` = on llegir l'arquetip: `__cat` (Berguedà, capa FILL) o `__covcat` (coberts, capa COVERED).
	return ['match', valExpr, ...pairs, TIPOLOGIA_UNKNOWN_COLOR];
}
