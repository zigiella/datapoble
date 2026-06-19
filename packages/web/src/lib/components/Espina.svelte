<script lang="ts">
	/**
	 * Espina territorial (breadcrumb): Catalunya › vegueria › comarca › municipi.
	 *
	 * Dona CONTEXT de situació a la fitxa de qualsevol dels ~947 municipis. «Catalunya» enllaça a la
	 * home; vegueria i comarca són text (encara no tenen pàgina pròpia — vindran amb les pàgines de
	 * comarca); el municipi és el node actual (`aria-current`). Si no hi ha territori (cas rar), només
	 * mostra Catalunya › municipi.
	 */
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';

	interface Props {
		vegueria?: string | null;
		comarca?: string | null;
		muni: string;
	}
	let { vegueria = null, comarca = null, muni }: Props = $props();
</script>

<nav class="espina" aria-label={m.espina_aria()}>
	<ol>
		<li><a href={localizeHref('/')}>{m.espina_catalunya()}</a></li>
		{#if vegueria}<li><span>{vegueria}</span></li>{/if}
		{#if comarca}<li><span>{comarca}</span></li>{/if}
		<li><span class="espina__cur" aria-current="page">{muni}</span></li>
	</ol>
</nav>

<style>
	.espina {
		font-family: var(--dp-font-mono);
		font-size: 0.72rem;
		color: var(--dp-text-subtle);
		margin-bottom: 10px;
	}
	.espina ol {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.espina li {
		display: inline-flex;
		align-items: center;
	}
	/* Separador › entre nivells (no abans del primer). */
	.espina li + li::before {
		content: '›';
		margin: 0 7px;
		color: var(--dp-border-strong, var(--dp-text-subtle));
		opacity: 0.7;
	}
	.espina a {
		color: var(--dp-text-muted);
		text-decoration: none;
	}
	.espina a:hover {
		color: var(--dp-text);
		text-decoration: underline;
	}
	.espina__cur {
		color: var(--dp-text);
		font-weight: 600;
	}
</style>
