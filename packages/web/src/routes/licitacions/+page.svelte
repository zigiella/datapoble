<script lang="ts">
	/**
	 * `/licitacions` — PÀGINA EN CONSTRUCCIÓ (decisió Bea, 2026-06-18).
	 *
	 * Per al llançament el cabal de licitacions no publica càlculs encara. En comptes d'amagar la
	 * secció (deixaria un buit), mostrem una pàgina honesta «en construcció» que explica QUÈ vindrà
	 * i PER QUÈ encara no hi és (cobrir totes les fases, creuar fonts; cap xifra sense procedència).
	 * Enllaçada des del peu. La maquinària de dades es conserva per a la Fase 2.
	 */
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
</script>

<svelte:head>
	<title>{m.lic_wip_h1()} · {m.app_name()}</title>
	<meta name="description" content={m.lic_wip_lead()} />
</svelte:head>

<section class="wip">
	<p class="wip__eyebrow">{m.lic_wip_eyebrow()}</p>
	<h1 class="wip__h1">{m.lic_wip_h1()}</h1>
	<p class="wip__lead">{m.lic_wip_lead()}</p>
	<p class="wip__body">{m.lic_wip_body()}</p>
	<div class="wip__actions">
		<a class="wip__cta" href={localizeHref('/')}>{m.lic_wip_back()}</a>
		<a class="wip__link" href={localizeHref('/metodologia')}>{m.lic_wip_method()}</a>
	</div>
</section>

<style>
	/* Pàgina «en construcció» digna (no el segell «stub»): respira, to de marca, honesta. */
	.wip {
		max-width: 56ch;
		margin: 0 auto;
		padding: clamp(48px, 9vw, 110px) 0;
		display: flex;
		flex-direction: column;
		gap: 14px;
	}
	.wip__eyebrow {
		margin: 0;
		font-family: var(--dp-font-mono);
		font-size: 0.72rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--dp-text-subtle);
	}
	.wip__h1 {
		margin: 0;
		font-family: var(--dp-font-display);
		font-size: clamp(2rem, 5vw, 2.8rem);
		line-height: 1.05;
		color: var(--dp-text);
	}
	.wip__lead {
		margin: 4px 0 0;
		font-size: 1.08rem;
		line-height: 1.5;
		color: var(--dp-text);
	}
	.wip__body {
		margin: 0;
		font-size: 0.96rem;
		line-height: 1.55;
		color: var(--dp-text-muted);
	}
	.wip__actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 18px;
		margin-top: 10px;
	}
	.wip__cta {
		font-weight: 600;
		text-decoration: none;
		color: var(--dp-text);
	}
	.wip__link {
		font-family: var(--dp-font-mono);
		font-size: 0.82rem;
		text-decoration: none;
		color: var(--dp-brand, #b5612a);
	}
	.wip__cta:hover,
	.wip__link:hover {
		text-decoration: underline;
	}
</style>
