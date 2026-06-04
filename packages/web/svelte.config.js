import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		// adapter-static: `npm run build` genera un site ESTÀTIC (prerender) desplegable
		// a Cloudflare Pages sense servidor. F2 (Mirador). El compte de Pages el configura IT.
		// fallback: SPA shell per a rutes no prerenderitzades (p. ex. la variant /es/* quan
		// el prerender només cobreix les canòniques). 404 personalitzat seguint el contracte.
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: '404.html',
			precompress: false,
			strict: false
		}),
		// Paraglide reescriu la URL localitzada (/es/...) a la ruta canònica (/...).
		// Així el routing basat en fitxers de SvelteKit es manté canònic i no cal
		// duplicar carpetes per idioma. Veure src/hooks.{server,ts} i src/lib/i18n.ts.
		alias: {
			$paraglide: './src/lib/paraglide'
		},
		prerender: {
			// El site és estàtic: cap dependència de servidor en runtime. Els enllaços
			// interns es descobreixen tot sol des de l'entrada arrel.
			handleHttpError: 'warn'
		}
	}
};

export default config;
