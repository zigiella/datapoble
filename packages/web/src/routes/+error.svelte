<script lang="ts">
	// Pàgina d'error genèrica (p. ex. 404), localitzada.
	import { page } from '$app/state';
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';
</script>

<section class="err">
	<p class="err__code">{page.status}</p>
	<h1>{m.not_found_title()}</h1>
	<p class="err__body">{m.not_found_body()}</p>
	<a href={localizeHref('/resum')}>← {m.stub_back()}</a>
</section>

<style>
	.err {
		max-width: 40ch;
		display: flex;
		flex-direction: column;
		gap: var(--dp-space-3);
		padding: var(--dp-space-8) 0;
	}

	.err__code {
		font-size: 3rem;
		font-weight: 800;
		color: var(--dp-text-muted);
		margin: 0;
	}

	.err h1 {
		margin: 0;
	}

	.err__body {
		color: var(--dp-text-muted);
		margin: 0;
	}
</style>
