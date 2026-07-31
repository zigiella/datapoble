<script lang="ts">
	/**
	 * ÍNDEX DE COMARQUES (W5): les comarques de Catalunya agrupades per vegueria, cadascuna amb el
	 * seu nombre de municipis i enllaç a la seva pàgina. És el destí de la porta que la home tenia
	 * morta («properament») i el nivell «tota Catalunya» que faltava a l'espina territorial.
	 *
	 * Cap xifra escrita aquí: totals i recomptes es COMPTEN de `comarques.json` al loader.
	 * Reutilitza la pell de la pàgina de vegueria (mateixa graella de targetes) perquè els dos
	 * nivells de l'espina es llegeixin igual.
	 */
	import Espina from '$lib/components/Espina.svelte';
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const vegueries = $derived(data.vegueries);
	const totalComarques = $derived(data.totalComarques);
	const totalMunis = $derived(data.totalMunis);
	const totalVegueries = $derived(data.totalVegueries);

	const trail = $derived([
		{ label: m.espina_catalunya(), href: localizeHref('/') },
		{ label: m.comarques_title() }
	]);
</script>

<svelte:head>
	<title>{m.comarques_title()} · {m.app_name()}</title>
	<meta name="description" content={m.comarques_meta()} />
</svelte:head>

<section data-view="comarques" class="on">
	<div class="ds-main">
		<Espina {trail} />

		<header class="coms-hd">
			<p class="ap-eyebrow"><span>{m.comarques_eyebrow()}</span></p>
			<h1>{m.comarques_title()}</h1>
			<p class="lead">
				{m.comarques_sub({
					comarques: String(totalComarques),
					vegueries: String(totalVegueries),
					munis: String(totalMunis)
				})}
			</p>
		</header>

		{#each vegueries as v (v.nom)}
			<section class="ds-sec">
				<div class="ds-sec__hd">
					<span class="ref">▦</span>
					{#if v.nom}
						<h2><a class="coms-veg" href={localizeHref(`/vegueria/${v.slug}`)}>{v.nom}</a></h2>
					{:else}
						<!-- Cap comarca es perd en silenci: si l'artefacte no li dona vegueria, surt igual. -->
						<h2>{m.comarques_sense_vegueria()}</h2>
					{/if}
				</div>
				<ul class="coms-list">
					{#each v.comarques as c (c.slug)}
						<li>
							<a class="coms-item" href={localizeHref(`/comarca/${c.slug}`)}>
								<span class="coms-item__nom">{c.nom}</span>
								<span class="coms-item__n">{m.vegueria_n_munis({ n: String(c.nMunis) })}</span>
							</a>
						</li>
					{/each}
				</ul>
			</section>
		{/each}
	</div>
</section>

<style>
	.coms-hd {
		margin-bottom: 8px;
	}
	.coms-veg {
		color: inherit;
		text-decoration: none;
		border-bottom: 1px solid var(--dp-border-strong);
	}
	.coms-veg:hover {
		color: var(--dp-text);
	}
	.coms-list {
		list-style: none;
		margin: 8px 0 0;
		padding: 0;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 9px;
	}
	.coms-item {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 10px;
		padding: 12px 14px;
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-md);
		background: var(--dp-surface);
		text-decoration: none;
		color: var(--dp-text);
	}
	.coms-item:hover {
		border-color: var(--dp-border-strong);
		background: var(--dp-accent-weak);
	}
	.coms-item__nom {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 0.95rem;
	}
	.coms-item__n {
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		color: var(--dp-text-subtle);
		white-space: nowrap;
	}
</style>
