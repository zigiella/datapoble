<script lang="ts">
	/**
	 * Pantalla provisional (stub) per a les cinc vistes encara no implementades.
	 * Existeix perquè la navegació i les rutes funcionin de punta a punta des del
	 * primer PR; el contingut real (mapa, índex, day-tripper, política, pregunta-li)
	 * arribarà en PRs posteriors. El títol es passa ja localitzat.
	 */
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';

	interface Props {
		/** Títol de la pantalla, ja resolt al locale actiu (m.screen_*()). */
		title: string;
	}
	let { title }: Props = $props();
</script>

<svelte:head>
	<title>{title} · {m.app_name()}</title>
</svelte:head>

<section class="stub">
	<p class="stub__badge">stub</p>
	<h1>{m.stub_title({ screen: title })}</h1>
	<p class="stub__body">{m.stub_body()}</p>
	<a class="stub__back" href={localizeHref('/resum')}>← {m.stub_back()}</a>
</section>

<style>
	.stub {
		max-width: 48ch;
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-3);
		padding: var(--dp-space-6) 0;
	}

	.stub__badge {
		align-self: flex-start;
		margin: 0;
		font-family: var(--dp-font-mono);
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--dp-warning);
		border: 1px solid var(--dp-warning);
		border-radius: var(--dp-radius-sm);
		padding: 2px var(--dp-space-2);
	}

	.stub h1 {
		font-size: 1.8rem;
		margin: 0;
	}

	.stub__body {
		color: var(--dp-text-muted);
		margin: 0;
	}

	.stub__back {
		font-weight: 600;
		text-decoration: none;
		align-self: flex-start;
	}
</style>
