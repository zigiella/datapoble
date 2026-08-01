<script lang="ts">
	/**
	 * W2 · LLISTAT D'UNA MÈTRICA A UNA COMARCA — el destí de cada rang clicable.
	 *
	 * Petició de Bea: «hem de poder clicar cada vegada que posi rang i accedir a cada llistat».
	 * Aquí hi ha els municipis de la comarca ordenats pel valor d'una mètrica, amb el seu rang,
	 * i cadascun navegable cap a la seva fitxa.
	 *
	 * LA DOCTRINA DE LA TARGETA VAL IGUAL AQUÍ (no s'afluixa perquè la pàgina sigui nova):
	 *  · **El rang i les referències es LLEGEIXEN** (C6 §4). L'ordre de la llista és el `rang`
	 *    del mart, no un `sort` pel valor fet aquí; les dues referències surten de la MATEIXA
	 *    funció pura que les pinta a la fitxa (`governReferences`), no d'una còpia.
	 *  · **Cada xifra amb font O fórmula i el seu denominador** (C6 §8.1): la procedència de la
	 *    mètrica surt del contracte (viatja amb l'artefacte), la mediana es diu sobre els
	 *    MUNICIPIS del rang i la ponderada sobre les unitats del seu propi pes.
	 *  · **El denominador honest**: si la comarca té 31 municipis i 27 tenen la xifra, es diu, i
	 *    els 4 que no la tenen **hi surten igualment** amb el motiu (n'hi ha TRES de diferents).
	 *    Van en un bloc a part al FINAL i SENSE ordenar (esmena de Bea): «no vol dir zero» —
	 *    la Quar, tractada com un 0, sortiria l'ÚLTIMA quan pel seu recompte seria la 2a (7 de 44
	 *    hab; xifra del MART, encara no servida al web, i per això aquí no es pot pintar).
	 *  · **Els empats no pinten un guanyador fals**: `empat` ve del mart i es marca a la fila.
	 */
	import Espina from '$lib/components/Espina.svelte';
	import { localizeHref, currentLocale, pick } from '$lib/i18n';
	import { toSlug } from '$lib/contract/slug';
	import { deComarca, laComarca } from '$lib/contract/comarca-nom.js';
	import { formatBoardValue, formatInteger } from '$lib/format';
	import {
		GOVERN_DENOM_REASON,
		GOVERN_DENOM_REASON_DEFAULT,
		GOVERN_DENOM_MIN_N,
		governReferences,
		governUnit,
		metricaSlug,
		provenanceLine
	} from '$lib/govern/kpis';
	import { m } from '$lib/paraglide/messages';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const locale = $derived(currentLocale());
	const ll = $derived(data.llista);
	const def = $derived(ll.def);

	const metricaLabel = $derived(pick(def.label, locale));
	const unit = $derived(governUnit(ll.metrica, def));
	/** Procedència de la mètrica: fórmula si és derivada, font · data si és mesurada (C6 §8.1). */
	const prov = $derived(provenanceLine(def));

	// El nom de la comarca amb el seu article. Si la taula no el sap (comarca nova, nom canviat),
	// es cau al nom pelat: abans quedar-nos curts que inventar-li un article.
	const deCom = $derived(deComarca(ll.comarca, locale) ?? ll.comarca);
	const laCom = $derived(laComarca(ll.comarca, locale) ?? ll.comarca);

	const trail = $derived([
		{ label: m.espina_catalunya(), href: localizeHref('/') },
		...(ll.vegueria
			? [{ label: ll.vegueria, href: localizeHref(`/vegueria/${toSlug(ll.vegueria)}`) }]
			: []),
		{ label: ll.comarca, href: localizeHref(`/comarca/${toSlug(ll.comarca)}`) },
		{ label: metricaLabel }
	]);

	/** Denominador incomplet → cal explicar-lo, amb el motiu REAL de la mètrica (mai un d'inventat). */
	const denomIncomplet = $derived(ll.n_amb_dada > 0 && ll.n_amb_dada < ll.n_comarca);
	const DENOM_TXT: Record<string, () => string> = {
		gov_denom_minn: () => m.gov_denom_minn({ n: String(GOVERN_DENOM_MIN_N) }),
		gov_denom_font: () => m.gov_denom_font(),
		gov_denom_ratio: () => m.gov_denom_ratio(),
		gov_denom_nd: () => m.gov_denom_nd()
	};
	const denomReason = $derived(
		DENOM_TXT[GOVERN_DENOM_REASON[ll.metrica] ?? GOVERN_DENOM_REASON_DEFAULT]?.() ?? ''
	);

	// ── LES DUES REFERÈNCIES (B+D), de la MATEIXA funció pura que les pinta a la fitxa ────────
	// L'artefacte del llistat porta exactament els camps que `governReferences` llegeix
	// (`mediana_comarca` + `n_amb_dada`, `ponderada_catalunya` + el seu denominador i el seu pes),
	// així que aquí no hi ha cap regla nova: la mateixa, exercida sobre la mateixa dada.
	const REF_LABEL: Record<string, (c: string) => string> = {
		gov_ref_comarca: (c) => (c ? m.gov_ref_comarca({ comarca: c }) : m.gov_ref_comarca_nd()),
		gov_ref_catalunya: () => m.gov_ref_catalunya()
	};
	const REF_DENOM: Record<string, (n: string) => string> = {
		gov_ref_denom_munis: (n) => m.gov_ref_denom_munis({ n }),
		gov_ref_denom_hab: (n) => m.gov_ref_denom_hab({ n }),
		gov_ref_denom_habitatges: (n) => m.gov_ref_denom_habitatges({ n }),
		gov_ref_denom_menors15: (n) => m.gov_ref_denom_menors15({ n })
	};
	const refs = $derived(
		governReferences(ll)
			.map((r) => {
				const label = REF_LABEL[r.labelKey]?.(deComarca(ll.comarca, locale) ?? '');
				const denom = REF_DENOM[r.denomKey]?.(formatInteger(r.denom, locale));
				// Sense rètol o sense denominador NO es pinta: mai una xifra òrfena de procedència.
				if (!label || !denom) return null;
				return {
					id: r.id,
					label,
					denom,
					value: formatBoardValue(r.value, def, locale) ?? ''
				};
			})
			.filter((r) => r !== null)
	);

	/** Les altres mètriques amb rang de la MATEIXA comarca (navegació lateral). El rètol ve del
	 *  contracte via l'artefacte: aquí no se n'escriu cap. */
	const altres = $derived(
		ll.altres.map((a) => ({
			key: a.metrica,
			label: pick(a.label, locale),
			href: localizeHref(`/comarca/${toSlug(ll.comarca)}/${metricaSlug(a.metrica)}`)
		}))
	);

	const fmt = (v: number) => formatBoardValue(v, def, locale) ?? '';
</script>

<svelte:head>
	<title>{m.llistat_title({ metrica: metricaLabel, comarca: laCom })} · {m.app_name()}</title>
	<meta
		name="description"
		content={m.llistat_meta({ metrica: metricaLabel, comarca: deCom })}
	/>
</svelte:head>

<section data-view="llistat-comarca" class="on">
	<div class="ds-main">
		<Espina {trail} />

		<header class="lst-hd">
			<p class="ap-eyebrow">
				<span>{m.llistat_eyebrow()}</span><span class="sep">/</span><span>{laCom}</span>
			</p>
			<h1>{metricaLabel}</h1>
			<p class="lead">
				{#if denomIncomplet}
					{m.llistat_lead_parcial({
						n: String(ll.n_amb_dada),
						total: String(ll.n_comarca),
						comarca: deCom
					})}
				{:else}
					{m.llistat_lead_tots({ total: String(ll.n_amb_dada), comarca: deCom })}
				{/if}
			</p>
			<!-- REGLA DE FERRO (C6 §8.1): la xifra no entra sense font O fórmula. La derivada mostra
			     la FÓRMULA i la font de les entrades; la mesurada, la FONT · data. Del contracte. -->
			<p class="lst-prov">
				{#if prov.formula}<span class="lst-prov__f">ƒ {prov.formula}</span>{/if}
				{#if prov.src}<span class="lst-prov__s">{prov.src}</span>{/if}
			</p>
		</header>

		<!-- LES DUES REFERÈNCIES (B+D), cadascuna amb el seu denominador NOMENAT: la mediana en
		     municipis (els mateixos que ordena el rang), la ponderada en unitats del seu pes. -->
		{#if refs.length}
			<div class="lst-refs">
				{#each refs as r (r.id)}
					<p class="lst-ref">
						<span class="lst-ref__v">{r.value}{#if unit}<span class="u">{unit}</span>{/if}</span>
						<span class="lst-ref__x">
							<span class="lst-ref__l">{r.label}</span>
							<span class="lst-ref__d">{r.denom}</span>
						</span>
					</p>
				{/each}
			</div>
		{/if}

		<section class="ds-sec">
			<div class="ds-sec__hd">
				<span class="ref">▦</span>
				<h2>{m.llistat_taula_title({ n: String(ll.n_amb_dada) })}</h2>
			</div>
			<!-- El denominador honest. El MOTIU no es repeteix aquí: viu al bloc dels que no en
			     tenen, que és on el lector els té davant. (A la targeta van junts perquè allà no hi
			     ha cap llista on ensenyar-los.) -->
			{#if denomIncomplet}
				<p class="lst-denom">
					{m.gov_denom_line({ n: String(ll.n_amb_dada), total: String(ll.n_comarca) })}
				</p>
			{/if}

			<ol class="lst-rows">
				{#each ll.munis as mu (mu.ine5)}
					<li>
						<a
							class="lst-row"
							class:lst-row--empat={mu.empat}
							href={localizeHref(`/municipi/${mu.slug}`)}
							aria-label={m.llistat_muni_aria({ nom: mu.nom })}
						>
							<span class="lst-row__k">{mu.rang}</span>
							<span class="lst-row__n">{mu.nom}</span>
							<!-- L'empat ve del mart: dos municipis amb el mateix rang no poden pintar un
							     guanyador que el mart no ha declarat. -->
							{#if mu.empat}<span class="lst-row__e">{m.gov_rang_empat()}</span>{/if}
							<span class="lst-row__v"
								>{fmt(mu.valor)}{#if unit}<span class="u">{unit}</span>{/if}</span
							>
						</a>
					</li>
				{/each}
			</ol>
		</section>

		<!-- ELS QUE NO EN TENEN (esmena de Bea): al FINAL, en un bloc a part i SENSE rang. No
		     desapareixen i no s'ordenen com si el seu valor fos zero.
		     VOT DE BEA (2026-08-01): aquí NO s'explica el motiu — «posem sense dada i no expliquem».
		     La doctrina es manté sencera (hi surten, no s'ordenen, diuen «sense dada» i mai un 0);
		     el que es retira és NOMÉS la prosa del perquè, que en una llista era soroll. L'explicació
		     segueix VIVA a la targeta de la fitxa, que és on Bea la va demanar («no vol dir zero»). -->
		{#if ll.sense.length}
			<section class="ds-sec">
				<div class="ds-sec__hd">
					<span class="ref">◌</span>
					<h2>{m.llistat_sense_title({ n: String(ll.sense.length) })}</h2>
				</div>
				<ul class="lst-rows lst-rows--sense">
					{#each ll.sense as mu (mu.ine5)}
						<li>
							<a
								class="lst-row lst-row--sense"
								href={localizeHref(`/municipi/${mu.slug}`)}
								aria-label={m.llistat_muni_aria({ nom: mu.nom })}
							>
								<span class="lst-row__k lst-row__k--buit" aria-hidden="true">—</span>
								<span class="lst-row__n">{mu.nom}</span>
								<span class="lst-row__v lst-row__v--sense">{m.llistat_sense_val()}</span>
							</a>
						</li>
					{/each}
				</ul>
			</section>
		{/if}

		<section class="ds-sec">
			<div class="ds-sec__hd">
				<span class="ref">◷</span>
				<h2>{m.llistat_altres({ comarca: deCom })}</h2>
			</div>
			<ul class="lst-altres">
				{#each altres as a (a.key)}
					<li><a href={a.href}>{a.label}</a></li>
				{/each}
			</ul>
			<p class="lst-foot">
				<a href={localizeHref(`/comarca/${toSlug(ll.comarca)}`)}>{m.llistat_tornar()} →</a>
			</p>
		</section>
	</div>
</section>

<style>
	.lst-hd {
		margin-bottom: 10px;
	}
	.lst-prov {
		margin: 6px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.72rem;
		color: var(--dp-text-muted);
		display: flex;
		flex-wrap: wrap;
		gap: 10px;
	}
	.lst-prov__f {
		color: var(--dp-text-subtle);
	}
	.lst-refs {
		display: flex;
		flex-wrap: wrap;
		gap: 10px 26px;
		margin: 12px 0 0;
		padding: 10px 14px;
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-sm);
		background: var(--dp-surface);
	}
	.lst-ref {
		margin: 0;
		display: flex;
		align-items: baseline;
		gap: 8px;
	}
	.lst-ref__v {
		font-family: var(--dp-font-mono);
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}
	.lst-ref__x {
		display: flex;
		flex-direction: column;
	}
	.lst-ref__l {
		font-size: 0.8rem;
	}
	/* El denominador es VEU: amagar-lo deixaria una xifra sense procedència (C6 §8.1). */
	.lst-ref__d {
		font-family: var(--dp-font-mono);
		font-size: 0.68rem;
		color: var(--dp-text-subtle);
	}
	.lst-denom {
		margin: 4px 0 10px;
		font-size: 0.8rem;
		color: var(--dp-text-muted);
		max-width: 62ch;
	}
	.lst-rows {
		list-style: none;
		margin: 8px 0 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 4px;
		counter-reset: none;
	}
	.lst-row {
		display: grid;
		grid-template-columns: 3.2rem 1fr auto auto;
		align-items: baseline;
		gap: 10px;
		padding: 7px 12px;
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-sm);
		background: var(--dp-surface);
		text-decoration: none;
		color: var(--dp-text);
	}
	.lst-row:hover {
		border-color: var(--dp-border-strong);
		background: var(--dp-accent-weak);
	}
	.lst-row--sense {
		grid-template-columns: 3.2rem 1fr auto;
	}
	.lst-row__k {
		font-family: var(--dp-font-mono);
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		color: var(--dp-text-subtle);
	}
	.lst-row__k--buit {
		color: var(--dp-text-muted);
	}
	.lst-row__n {
		font-weight: 500;
		font-size: 0.92rem;
	}
	.lst-row__e {
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		color: var(--dp-text-subtle);
		white-space: nowrap;
	}
	.lst-row__v {
		font-family: var(--dp-font-mono);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.lst-row__v--sense {
		font-size: 0.75rem;
		color: var(--dp-text-muted);
	}
	.lst-row__v .u {
		font-size: 0.68rem;
		color: var(--dp-text-subtle);
		margin-left: 2px;
	}
	.lst-ref__v .u {
		font-size: 0.68rem;
		color: var(--dp-text-subtle);
		margin-left: 2px;
	}
	.lst-altres {
		list-style: none;
		margin: 8px 0 0;
		padding: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 7px;
	}
	.lst-altres a {
		display: inline-block;
		padding: 5px 10px;
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-sm);
		background: var(--dp-surface);
		text-decoration: none;
		color: var(--dp-text);
		font-family: var(--dp-font-mono);
		font-size: 0.72rem;
	}
	.lst-altres a:hover {
		border-color: var(--dp-border-strong);
		background: var(--dp-accent-weak);
	}
	.lst-foot {
		margin: 14px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.8rem;
	}
</style>
