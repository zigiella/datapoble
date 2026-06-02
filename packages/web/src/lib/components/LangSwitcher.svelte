<script lang="ts">
	/**
	 * Selector d'idioma. Manté la ruta actual i només canvia el prefix de locale:
	 * fa servir `localizeHref` per generar la URL localitzada equivalent. La cookie
	 * (estratègia configurada) recorda l'elecció en futures visites.
	 *
	 * Accessibilitat: és un grup de navegació amb aria-current a l'idioma actiu.
	 */
	import { page } from '$app/state';
	import { SUPPORTED_LOCALES, LOCALE_LABEL, currentLocale, localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
	import type { Locale } from '$lib/contract/types';

	const active = $derived(currentLocale());

	// Ruta canònica actual (sense prefix de locale), per re-localitzar a cada idioma.
	const canonicalPath = $derived(page.url.pathname);

	function hrefFor(locale: Locale): string {
		return localizeHref(canonicalPath, { locale });
	}
</script>

<nav class="lang" aria-label={m.lang_switcher_label()}>
	{#each SUPPORTED_LOCALES as locale (locale)}
		<a
			href={hrefFor(locale)}
			class="lang__item"
			class:is-active={locale === active}
			aria-current={locale === active ? 'true' : undefined}
			hreflang={locale}
			data-sveltekit-reload
		>
			{LOCALE_LABEL[locale]}
		</a>
	{/each}
</nav>

<style>
	.lang {
		display: inline-flex;
		gap: 2px;
		border: 1px solid var(--dp-color-border);
		border-radius: var(--dp-radius-sm);
		overflow: hidden;
	}

	.lang__item {
		padding: var(--dp-space-1) var(--dp-space-3);
		font-size: 0.8rem;
		font-weight: 600;
		text-decoration: none;
		color: var(--dp-color-muted);
		background: var(--dp-color-surface);
	}

	.lang__item.is-active {
		background: var(--dp-color-accent);
		color: #fff;
	}
</style>
