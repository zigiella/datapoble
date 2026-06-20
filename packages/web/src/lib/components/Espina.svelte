<script lang="ts">
	/**
	 * Espina territorial (breadcrumb): Catalunya › vegueria › comarca › municipi.
	 *
	 * Dona CONTEXT de situació i navegació amunt/avall a les pàgines territorials (fitxa de municipi,
	 * comarca, vegueria). Rep un `trail` de molles: cadascuna amb `href` (navegable) o sense (el node
	 * ACTUAL, `aria-current`). Així el mateix component serveix a qualsevol nivell.
	 */
	import { m } from '$lib/paraglide/messages';

	interface Crumb {
		label: string;
		/** Destí; si falta, és el nivell actual (no enllaç). */
		href?: string;
	}
	let { trail }: { trail: Crumb[] } = $props();
</script>

<nav class="espina" aria-label={m.espina_aria()}>
	<ol>
		{#each trail as c, i (i)}
			<li>
				{#if c.href}
					<a href={c.href}>{c.label}</a>
				{:else}
					<span class="espina__cur" aria-current="page">{c.label}</span>
				{/if}
			</li>
		{/each}
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
