<script lang="ts">
	/**
	 * Navegació principal entre les sis pantalles de l'observatori.
	 * Els href es localitzen amb `localizeHref` perquè conservin el prefix d'idioma.
	 * Els rètols vénen dels catàlegs i18n (m.*), no es codifiquen aquí.
	 */
	import { page } from '$app/state';
	import { localizeHref } from '$lib/i18n';
	import { m } from '$lib/paraglide/messages';

	type NavItem = { path: string; label: () => string };

	// Rutes CANÒNIQUES (sense prefix de locale). reroute/localize fan la traducció.
	const items: NavItem[] = [
		{ path: '/resum', label: m.nav_resum },
		{ path: '/mapa', label: m.nav_mapa },
		{ path: '/index', label: m.nav_index },
		{ path: '/day-tripper', label: m.nav_daytripper },
		{ path: '/pregunta-li', label: m.nav_preguntale }
	];

	const currentPath = $derived(page.url.pathname);

	function isActive(path: string): boolean {
		return currentPath === path || currentPath.startsWith(path + '/');
	}
</script>

<nav class="mainnav" aria-label="Primary">
	<ul>
		{#each items as item (item.path)}
			<li>
				<a
					href={localizeHref(item.path)}
					class:is-active={isActive(item.path)}
					aria-current={isActive(item.path) ? 'page' : undefined}
				>
					{item.label()}
				</a>
			</li>
		{/each}
	</ul>
</nav>

<style>
	.mainnav ul {
		list-style: none;
		display: flex;
		flex-wrap: wrap;
		gap: var(--dp-space-1);
		margin: 0;
		padding: 0;
	}

	.mainnav a {
		display: inline-block;
		padding: var(--dp-space-2) var(--dp-space-3);
		border-radius: var(--dp-radius-sm);
		text-decoration: none;
		color: var(--dp-text-muted);
		font-size: 0.9rem;
		font-weight: 500;
	}

	.mainnav a:hover {
		background: var(--dp-accent-weak);
		color: var(--dp-text);
	}

	.mainnav a.is-active {
		background: var(--dp-accent-weak);
		color: var(--dp-forest);
		font-weight: 700;
	}
</style>
