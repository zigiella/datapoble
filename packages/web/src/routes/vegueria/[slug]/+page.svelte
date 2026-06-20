<script lang="ts">
	/**
	 * Pàgina de VEGUERIA (§5): breadcrumb + les comarques de la vegueria (enllaç a cada pàgina de
	 * comarca). Nivell més alt de l'espina territorial.
	 */
	import Espina from '$lib/components/Espina.svelte';
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const vegueria = $derived(data.vegueria);
	const comarques = $derived(data.comarques);
	const totalMunis = $derived(data.totalMunis);

	const trail = $derived([{ label: m.espina_catalunya(), href: localizeHref('/') }, { label: vegueria.nom }]);
</script>

<svelte:head>
	<title>{vegueria.nom} · {m.app_name()}</title>
	<meta name="description" content={m.vegueria_meta({ nom: vegueria.nom })} />
</svelte:head>

<section data-view="vegueria" class="on">
	<div class="ds-main">
		<Espina {trail} />

		<header class="veg-hd">
			<p class="ap-eyebrow"><span>{m.vegueria_eyebrow()}</span></p>
			<h1>{vegueria.nom}</h1>
			<p class="lead">{m.vegueria_sub({ comarques: String(comarques.length), munis: String(totalMunis) })}</p>
		</header>

		<section class="ds-sec">
			<div class="ds-sec__hd"><span class="ref">▦</span><h2>{m.vegueria_comarques_title()}</h2></div>
			<ul class="veg-coms">
				{#each comarques as c (c.slug)}
					<li>
						<a class="veg-com" href={localizeHref(`/comarca/${c.slug}`)}>
							<span class="veg-com__nom">{c.nom}</span>
							<span class="veg-com__n">{m.vegueria_n_munis({ n: String(c.nMunis) })}</span>
						</a>
					</li>
				{/each}
			</ul>
		</section>
	</div>
</section>

<style>
	.veg-hd {
		margin-bottom: 8px;
	}
	.veg-coms {
		list-style: none;
		margin: 8px 0 0;
		padding: 0;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 9px;
	}
	.veg-com {
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
	.veg-com:hover {
		border-color: var(--dp-border-strong);
		background: var(--dp-accent-weak);
	}
	.veg-com__nom {
		font-family: var(--dp-font-display);
		font-weight: 700;
		font-size: 1.02rem;
	}
	.veg-com__n {
		font-family: var(--dp-font-mono);
		font-size: 0.72rem;
		color: var(--dp-text-subtle);
	}
</style>
