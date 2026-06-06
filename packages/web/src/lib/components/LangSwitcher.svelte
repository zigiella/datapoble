<script lang="ts">
	/**
	 * Selector d'idioma (CA/ES). Manté la ruta actual i només canvia el prefix de locale:
	 * fa servir `localizeHref` per generar la URL localitzada equivalent. La cookie
	 * (estratègia configurada) recorda l'elecció en futures visites.
	 *
	 * Estil: classe `.langer` del design-system (sistema.css + aplicacio.css), perquè
	 * capçalera i peu comparteixin el mateix commutador (DA final, captures 01/07).
	 * És navegació real (enllaços <a> amb reload), no botons: funciona sense JS i conserva
	 * l'accessibilitat (aria-current a l'idioma actiu).
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

<div class="langer" role="group" aria-label={m.lang_switcher_label()}>
	{#each SUPPORTED_LOCALES as locale (locale)}
		<a
			href={hrefFor(locale)}
			class:on={locale === active}
			aria-current={locale === active ? 'true' : undefined}
			hreflang={locale}
			data-sveltekit-reload
		>
			{LOCALE_LABEL[locale]}
		</a>
	{/each}
</div>

<style>
	/* `.langer` (sistema/aplicacio) estilitza <button>; aquí en fem <a> per navegació
	   real. Reproduïm el mateix encaix perquè coincideixi amb el target. */
	.langer a {
		font-family: var(--dp-font-mono);
		font-size: 11px;
		letter-spacing: 0.06em;
		text-decoration: none;
		color: var(--dp-text-subtle);
		background: transparent;
		padding: 6px 10px;
		border-right: 1px solid var(--dp-border);
		display: inline-flex;
		align-items: center;
	}
	.langer a:last-child {
		border-right: none;
	}
	.langer a.on {
		background: var(--dp-text);
		color: var(--dp-bg);
	}
</style>
