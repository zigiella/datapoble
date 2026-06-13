<script lang="ts">
	/**
	 * Secció Licitacions (`/licitacions`) — el pilar 2 (el cabal) al web.
	 *
	 * «Una licitació és una confessió administrativa»: el que un ajuntament contracta revela
	 * el que espera. Mostra el resum comarcal (taxonomia de 1.295 contractes + dependència
	 * supramunicipal) amb l'enquadrament HONEST: «no contracta res propi» = centralització al
	 * Consell + biaix de font, MAI mala gestió. Dada del cabal (data/web/licitacions-bergueda.json).
	 */
	import ContourField from '$lib/components/ContourField.svelte';
	import { currentLocale } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import { temaLabel, lecturaLabel, eurCurt } from '$lib/format/licitacions';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const lic = $derived(data.licitacions);
	const locale = $derived(currentLocale());
	const intl = $derived(locale === 'es' ? 'es-ES' : 'ca-ES');

	// Format i etiquetes compartits amb el bloc de la fitxa ($lib/format/licitacions).
	const eur = (v: number | null) => eurCurt(v, intl);
	const intf = (v: number | null) => (v == null ? '—' : v.toLocaleString(intl));

	const temes = $derived(lic.comarca.temes);
	const maxN = $derived(Math.max(1, ...temes.map((t) => t.n)));
	// Taula per municipi: per població descendent (familiar; el relat de dependència es llegeix sol).
	const munis = $derived([...lic.municipis].sort((a, b) => (b.poblacio ?? 0) - (a.poblacio ?? 0)));
	const nNoPropi = $derived(lic.comarca.dependencia?.no_contracta_propi ?? 0);

	const heroSummits = [
		{ cx: 880, cy: 150, r0: 16, step: 23, rings: 10, sq: 0.96, seed: 1.4, lt: 0.03 },
		{ cx: 1080, cy: 300, r0: 14, step: 21, rings: 9, sq: 1.05, seed: 3.0, lt: 0.1 }
	];
	const heroDivis = { cx: 760, cy: 225, r: 150, sq: 1.18, seed: 0.9 };
	const heroLabels = ['1.295', '695 comarcals', '600 municipals', '12 temes', '€'];
</script>

<svelte:head>
	<title>{m.lic_title()} · {m.app_name()}</title>
	<meta name="description" content={m.lic_meta_desc()} />
</svelte:head>

<section data-view="licitacions" class="on">
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
				<span>{m.lic_eyebrow_a()}</span><span class="sep">/</span><span>{m.lic_eyebrow_b()}</span>
			</p>
			<h1>{m.lic_h1()}</h1>
			<p class="lede">{m.lic_lede()}</p>
			<p class="tesi">{m.lic_tesi()}</p>
		</div>
	</div>

	<div class="ds-main">
		<!-- P1 · El veredicte: la dependència supramunicipal, amb el caveat de seguida. -->
		<section class="ds-sec first">
			<div class="lic-verdict">
				<span class="lic-verdict__big">{nNoPropi} <span class="lic-verdict__of">/ 31</span></span>
				<div class="lic-verdict__txt">
					<p class="lic-verdict__lead">{m.lic_verdict_lead()}</p>
					<p class="lic-verdict__caveat">{m.lic_verdict_caveat()}</p>
				</div>
			</div>
		</section>

		<!-- Taxonomia: què contracta el territori, per tema. -->
		<section class="ds-sec">
			<div class="ds-sec__hd"><span class="ref">A</span><h2>{m.lic_block_temes()}</h2></div>
			<p class="lead">
				{m.lic_temes_intro({ total: lic.comarca.n_contractes, comarcal: lic.comarca.n_comarcal, municipal: lic.comarca.n_municipal, import: eur(lic.comarca.import_total) })}
			</p>
			<ul class="lic-temes">
				{#each temes as t (t.tema)}
					<li class="lic-tema">
						<span class="lic-tema__nom">{temaLabel(t.tema)}</span>
						<span class="lic-tema__bar"><span class="lic-tema__fill" style="width:{(t.n / maxN) * 100}%"></span></span>
						<span class="lic-tema__n tnum">{t.n}</span>
						<span class="lic-tema__eur tnum">{eur(t.import)}</span>
					</li>
				{/each}
			</ul>
		</section>

		<!-- Dependència supramunicipal per municipi. -->
		<section class="ds-sec">
			<div class="ds-sec__hd"><span class="ref">B</span><h2>{m.lic_block_dependencia()}</h2></div>
			<p class="lead">{m.lic_dependencia_intro()}</p>
			<div class="lic-table-wrap">
				<table class="lic-table">
					<thead>
						<tr>
							<th scope="col">{m.tbl_municipi()}</th>
							<th scope="col">{m.lic_th_propis()}</th>
							<th scope="col">{m.lic_th_import_propi()}</th>
							<th scope="col">{m.lic_th_serveis()}</th>
							<th scope="col">{m.lic_th_lectura()}</th>
						</tr>
					</thead>
					<tbody>
						{#each munis as muni (muni.ine5)}
							<tr>
								<th scope="row">{muni.nom}</th>
								<td class="tnum">{intf(muni.n_contractes_municipal)}</td>
								<td class="tnum">{eur(muni.import_municipal_directe)}</td>
								<td class="tnum">{eur(muni.import_serveis_comarcals)}</td>
								<td class="lic-lectura lic-lectura--{muni.dependencia_lectura}">{lecturaLabel(muni.dependencia_lectura)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>

		<!-- Frontera honesta (innegociable). -->
		<section class="ds-sec">
			<div class="ds-sec__hd"><span class="ref">★</span><h2>{m.lic_honesty_title()}</h2></div>
			<div class="caveats">
				<div class="alert"><span class="bar"></span><div>{m.lic_honesty_1()}</div></div>
				<div class="alert warn"><span class="bar"></span><div>{m.lic_honesty_2()}</div></div>
			</div>
			<p class="srcline">{m.lic_srcline({ font: lic.font })}</p>
		</section>
	</div>
</section>

<style>
	.ds-sec.first {
		border-top: none;
	}
	.tesi {
		margin: 16px 0 0;
		padding-left: 14px;
		border-left: 3px solid var(--dp-brand, var(--dp-border-strong));
		font-size: 1.05rem;
		line-height: 1.5;
		color: var(--dp-text);
		max-width: 56ch;
		font-weight: 500;
		font-style: italic;
	}

	/* Veredicte: la xifra gran + la lectura, amb el caveat enganxat. */
	.lic-verdict {
		display: flex;
		gap: 20px;
		align-items: center;
		flex-wrap: wrap;
	}
	.lic-verdict__big {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 3.4rem;
		line-height: 1;
		color: var(--dp-brand, var(--dp-text));
		font-variant-numeric: tabular-nums;
	}
	.lic-verdict__of {
		font-size: 1.4rem;
		color: var(--dp-text-subtle);
	}
	.lic-verdict__txt {
		flex: 1;
		min-width: 260px;
	}
	.lic-verdict__lead {
		margin: 0;
		font-size: 1.05rem;
		font-weight: 600;
		color: var(--dp-text);
		line-height: 1.4;
	}
	.lic-verdict__caveat {
		margin: 6px 0 0;
		font-size: 0.86rem;
		color: var(--dp-text-muted);
		line-height: 1.45;
	}

	/* Barres de tema. */
	.lic-temes {
		list-style: none;
		margin: 8px 0 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 7px;
	}
	.lic-tema {
		display: grid;
		grid-template-columns: 12ch 1fr auto auto;
		align-items: center;
		gap: 12px;
		font-size: 0.86rem;
	}
	.lic-tema__nom {
		color: var(--dp-text);
		font-weight: 500;
	}
	.lic-tema__bar {
		height: 9px;
		background: var(--dp-surface-2, color-mix(in srgb, var(--dp-text) 6%, transparent));
		border-radius: 5px;
		overflow: hidden;
	}
	.lic-tema__fill {
		display: block;
		height: 100%;
		background: var(--dp-prov-derived, var(--dp-brand, #8a6cab));
		border-radius: 5px;
	}
	.lic-tema__n {
		color: var(--dp-text);
		font-weight: 600;
		min-width: 4ch;
		text-align: right;
	}
	.lic-tema__eur {
		color: var(--dp-text-subtle);
		font-size: 0.78rem;
		min-width: 7ch;
		text-align: right;
	}

	/* Taula de dependència. */
	.lic-table-wrap {
		overflow-x: auto;
		margin-top: 4px;
	}
	.lic-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.84rem;
		font-variant-numeric: tabular-nums;
	}
	.lic-table th,
	.lic-table td {
		text-align: right;
		padding: 6px 10px;
		border-bottom: 1px solid var(--dp-border);
	}
	.lic-table thead th {
		color: var(--dp-text-subtle);
		font-weight: 600;
		border-bottom: 1px solid var(--dp-border-strong);
	}
	.lic-table th[scope='row'] {
		text-align: left;
		font-weight: 500;
		color: var(--dp-text);
	}
	.lic-lectura {
		font-family: var(--dp-font-mono);
		font-size: 0.66rem;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		color: var(--dp-text-muted);
	}
	.lic-lectura--autonom {
		color: var(--dp-forest, #2f6b4f);
		font-weight: 700;
	}

	.srcline {
		margin: 14px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.64rem;
		color: var(--dp-text-subtle);
		line-height: 1.5;
	}

	@media (max-width: 560px) {
		.lic-tema {
			grid-template-columns: 10ch 1fr auto;
		}
		.lic-tema__eur {
			display: none;
		}
	}
</style>
