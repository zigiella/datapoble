<script lang="ts">
	/**
	 * Commutador de tema (clar/fosc) amb icones sol/lluna, segons la DA final.
	 * Aplica `data-theme` a <html> (els tokens --dp-* reaccionen) i persisteix la tria
	 * a localStorage (`rdg-theme`). El parpelleig inicial el preveu l'script anti-FOUC
	 * d'app.html, que fixa el tema abans del primer pintat; aquí només el sincronitzem
	 * cap a l'estat reactiu i el commutem en clicar.
	 *
	 * Estil: classe `.themer` del design-system (sistema.css + aplicacio.css), compartida
	 * amb la rèplica del peu. Markup d'icones idèntic al target (captures 01/07).
	 */
	import { onMount } from 'svelte';
	import { m } from '$lib/paraglide/messages';

	type Theme = 'light' | 'dark';

	// Estat reactiu del tema. S'inicialitza a 'light' i es reconcilia a onMount amb el
	// que ja hi ha a <html> (posat per l'anti-FOUC), per no divergir del DOM real.
	let theme = $state<Theme>('light');

	onMount(() => {
		const current = document.documentElement.getAttribute('data-theme');
		theme = current === 'dark' ? 'dark' : 'light';
	});

	function setTheme(next: Theme) {
		theme = next;
		document.documentElement.setAttribute('data-theme', next);
		try {
			localStorage.setItem('rdg-theme', next);
		} catch {
			/* localStorage pot fallar (mode privat): el tema segueix aplicat a la sessió. */
		}
	}
</script>

<div class="themer" role="group" aria-label={m.theme_switcher_label()}>
	<button
		type="button"
		class:on={theme === 'light'}
		aria-pressed={theme === 'light'}
		title={m.theme_light()}
		aria-label={m.theme_light()}
		onclick={() => setTheme('light')}
	>
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
			<circle cx="12" cy="12" r="4.2"></circle>
			<path
				d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"
			></path>
		</svg>
	</button>
	<button
		type="button"
		class:on={theme === 'dark'}
		aria-pressed={theme === 'dark'}
		title={m.theme_dark()}
		aria-label={m.theme_dark()}
		onclick={() => setTheme('dark')}
	>
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
			<path d="M20 14.5A8 8 0 0 1 9.5 4 6.5 6.5 0 1 0 20 14.5z"></path>
		</svg>
	</button>
</div>
