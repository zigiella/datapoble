<script lang="ts">
	/**
	 * Tooltip del mapa: nom del municipi + valor de l'indicador + PROCEDÈNCIA.
	 * La procedència fa servir la signatura `.prov` del design-system (sistema.css):
	 * cada número arrossega el seu origen (contracte editorial). "Sense dada" és explícit.
	 */
	import type { MetricDef } from '$lib/contract/types';
	import { makeFormatter } from '$lib/map/classify';
	import { provenanceOf } from '$lib/map/provenance';
	import { pick, currentLocale } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';

	interface Props {
		nom: string;
		def: MetricDef;
		value: number | string | null;
		/** Posició en píxels dins del contenidor del mapa. */
		x: number;
		y: number;
	}
	let { nom, def, value, x, y }: Props = $props();

	const locale = $derived(currentLocale());
	const hasVal = $derived(typeof value === 'number' && Number.isFinite(value));
	const prov = $derived(provenanceOf(def, hasVal));
	const formatted = $derived.by(() => {
		if (typeof value === 'number') return makeFormatter(def.format, locale)(value);
		if (typeof value === 'string') return value;
		return m.value_not_available();
	});
	const unit = $derived(pick(def.unit, locale));
	// Mostra la unitat només quan és un nom de magnitud (habitants, establiments, kg/hab/any…).
	// L'amaga per a percentatges (ja duen %), rànquings i escales d'índex ("0-100", "posició"),
	// on enganxar la "unitat" al número el faria confús (p. ex. IETR "41,00 0-100").
	const showUnit = $derived(
		hasVal &&
			(def.format === 'integer' || def.format === 'decimal' || def.format === 'ratio') &&
			!!unit &&
			unit !== '%' &&
			!/^\s*\d/.test(unit) // descarta unitats que comencen amb dígit (escales tipus "0-100")
	);
	const provLabel = $derived(
		prov === 'derived'
			? m.map_prov_derived()
			: prov === 'negative'
				? m.map_prov_nodata()
				: m.map_prov_measured()
	);
</script>

<div
	class="tip card"
	style="left:{x}px; top:{y}px"
	role="tooltip"
	aria-live="polite"
>
	<div class="tip__place">{nom}</div>
	<div class="tip__metric">{pick(def.label, locale)}</div>
	{#if hasVal}
		<div class="tip__val tnum">
			{formatted}{#if showUnit}<span class="tip__unit"> {unit}</span>{/if}
		</div>
	{:else}
		<div class="tip__val tip__val--nodata">{m.map_tooltip_nodata()}</div>
	{/if}
	<div class="prov prov--{prov}">
		<span class="dot"></span>{provLabel}
	</div>
</div>

<style>
	.tip {
		position: absolute;
		z-index: 20;
		pointer-events: none;
		transform: translate(-50%, calc(-100% - 14px));
		min-width: 160px;
		max-width: 240px;
		padding: 10px 12px;
		box-shadow: var(--dp-shadow-md);
	}
	.tip__place {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 0.95rem;
		color: var(--dp-text);
		line-height: 1.15;
	}
	.tip__metric {
		font-family: var(--dp-font-mono);
		font-size: 0.62rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dp-text-subtle);
		margin-top: 3px;
	}
	.tip__val {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 1.4rem;
		color: var(--dp-text);
		line-height: 1.1;
		margin: 2px 0 6px;
	}
	.tip__unit {
		font-family: var(--dp-font-sans);
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--dp-text-subtle);
	}
	.tip__val--nodata {
		font-family: var(--dp-font-sans);
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--dp-text-muted);
	}
</style>
