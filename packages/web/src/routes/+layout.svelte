<script lang="ts">
	/**
	 * Layout arrel. Estructura comuna a totes les pantalles: enllaç "salta al contingut",
	 * capçalera (marca + navegació + selector d'idioma) i peu amb la nota de procedència.
	 * No defineix disseny propi més enllà de placeholders; els tokens són de Llegenda.
	 */
	import '../app.css';
	import Nav from '$lib/components/Nav.svelte';
	import LangSwitcher from '$lib/components/LangSwitcher.svelte';
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';

	let { children } = $props();
</script>

<a class="skip-link" href="#main">{m.skip_to_content()}</a>

<div class="shell">
	<header class="shell__header">
		<div class="shell__bar">
			<a class="brand" href={localizeHref('/resum')}>
				<span class="brand__name">{m.app_name()}</span>
				<span class="brand__tag">{m.app_tagline()}</span>
			</a>
			<LangSwitcher />
		</div>
		<Nav />
	</header>

	<main id="main" class="shell__main" tabindex="-1">
		{@render children?.()}
	</main>

	<footer class="shell__footer">
		<p>{m.footer_note()}</p>
		<p class="shell__footer-data">{m.footer_data_note()}</p>
	</footer>
</div>

<style>
	.shell {
		max-width: var(--dp-maxw);
		margin: 0 auto;
		padding: var(--dp-space-4);
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-5);
	}

	.shell__header {
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-4);
		padding-bottom: var(--dp-space-4);
		border-bottom: 1px solid var(--dp-color-border);
	}

	.shell__bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--dp-space-4);
		flex-wrap: wrap;
	}

	.brand {
		text-decoration: none;
		color: inherit;
		display: flex;
		flex-direction: column;
	}

	.brand__name {
		font-size: 1.35rem;
		font-weight: 800;
		letter-spacing: -0.01em;
		color: var(--dp-color-accent);
	}

	.brand__tag {
		font-size: 0.8rem;
		color: var(--dp-color-muted);
	}

	.shell__main {
		flex: 1;
		outline: none;
	}

	.shell__footer {
		border-top: 1px solid var(--dp-color-border);
		padding-top: var(--dp-space-4);
		font-size: 0.78rem;
		color: var(--dp-color-muted);
	}

	.shell__footer p {
		margin: 0 0 var(--dp-space-1);
	}

	.shell__footer-data {
		opacity: 0.85;
	}
</style>
