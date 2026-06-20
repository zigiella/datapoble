<script lang="ts">
	/**
	 * Pàgina de COMARCA (§5): breadcrumb navegable + el gap de la comarca (beeswarm) + els seus
	 * municipis (enllaç a fitxa). Nivell intermedi de l'espina territorial; tot SVG/HTML verificable.
	 */
	import Espina from '$lib/components/Espina.svelte';
	import Beeswarm from '$lib/components/Beeswarm.svelte';
	import { localizeHref } from '$lib/i18n';
	import { toSlug } from '$lib/contract/slug';
	import { m } from '$lib/paraglide/messages';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const comarca = $derived(data.comarca);
	const munis = $derived(data.munis);
	const pernSub = $derived(data.pernSub);
	const coberts = $derived(data.coberts);

	const trail = $derived([
		{ label: m.espina_catalunya(), href: localizeHref('/') },
		{ label: comarca.vegueria, href: localizeHref(`/vegueria/${toSlug(comarca.vegueria)}`) },
		{ label: comarca.nom }
	]);

	const gapTxt = (g: number | null) => (g === null ? '—' : `${g > 0 ? '+' : ''}${Math.round(g)}%`);
</script>

<svelte:head>
	<title>{comarca.nom} · {m.app_name()}</title>
	<meta name="description" content={m.comarca_meta({ nom: comarca.nom, vegueria: comarca.vegueria })} />
</svelte:head>

<section data-view="comarca" class="on">
	<div class="ds-main">
		<Espina {trail} />

		<header class="com-hd">
			<p class="ap-eyebrow"><span>{m.comarca_eyebrow()}</span><span class="sep">/</span><span>{comarca.vegueria}</span></p>
			<h1>{comarca.nom}</h1>
			<p class="lead">{m.comarca_sub({ total: String(munis.length), coberts: String(coberts) })}</p>
		</header>

		{#if coberts >= 3}
			<section class="ds-sec">
				<div class="ds-sec__hd"><span class="ref">∿</span><h2>{m.comarca_gap_title()}</h2></div>
				<Beeswarm munis={pernSub} />
			</section>
		{/if}

		<section class="ds-sec">
			<div class="ds-sec__hd"><span class="ref">▦</span><h2>{m.comarca_munis_title({ n: String(munis.length) })}</h2></div>
			<ul class="com-munis">
				{#each munis as mu (mu.ine5)}
					<li>
						<a class="com-muni" href={localizeHref(`/municipi/${mu.slug}`)}>
							<span class="com-muni__nom">{mu.nom}</span>
							<span class="com-muni__gap" class:on={mu.gap !== null}>{gapTxt(mu.gap)}</span>
						</a>
					</li>
				{/each}
			</ul>
			<p class="com-foot"><a href={localizeHref('/mapa')}>{m.muni_pick_map()} →</a></p>
		</section>
	</div>
</section>

<style>
	.com-hd {
		margin-bottom: 8px;
	}
	.com-munis {
		list-style: none;
		margin: 8px 0 0;
		padding: 0;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 7px;
	}
	.com-muni {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 10px;
		padding: 8px 12px;
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-sm);
		background: var(--dp-surface);
		text-decoration: none;
		color: var(--dp-text);
	}
	.com-muni:hover {
		border-color: var(--dp-border-strong);
		background: var(--dp-accent-weak);
	}
	.com-muni__nom {
		font-weight: 500;
		font-size: 0.9rem;
	}
	.com-muni__gap {
		font-family: var(--dp-font-mono);
		font-size: 0.74rem;
		color: var(--dp-text-subtle);
		font-variant-numeric: tabular-nums;
	}
	.com-muni__gap.on {
		color: var(--dp-text-muted);
	}
	.com-foot {
		margin: 14px 0 0;
		font-family: var(--dp-font-mono);
		font-size: 0.8rem;
	}
</style>
