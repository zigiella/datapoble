import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter(),
		// Paraglide reescriu la URL localitzada (/es/...) a la ruta canònica (/...).
		// Així el routing basat en fitxers de SvelteKit es manté canònic i no cal
		// duplicar carpetes per idioma. Veure src/hooks.{server,ts} i src/lib/i18n.ts.
		alias: {
			$paraglide: './src/lib/paraglide'
		}
	}
};

export default config;
