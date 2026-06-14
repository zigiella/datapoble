import { sveltekit } from '@sveltejs/kit/vite';
import { paraglideVitePlugin } from '@inlang/paraglide-js';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		// Paraglide compila project.inlang + messages/*.json -> src/lib/paraglide/*.
		// strategy: l'ordre de detecció de locale. 'url' llegeix el prefix /ca|/es;
		// 'cookie' recorda l'elecció del selector; 'baseLocale' (ca) és el fallback.
		paraglideVitePlugin({
			project: './project.inlang',
			outdir: './src/lib/paraglide',
			strategy: ['url', 'cookie', 'baseLocale'],
			// Prefix EXPLÍCIT per a TOTES les llengües, també la base (ca): /ca/… i /es/…,
			// cap URL sense prefix d'idioma. Deixa el terreny per a oc (aranès) i en (anglès).
			urlPatterns: [
				{
					pattern: ':protocol://:domain(.*)::port?/:path(.*)?',
					localized: [
						['ca', ':protocol://:domain(.*)::port?/ca/:path(.*)?'],
						['es', ':protocol://:domain(.*)::port?/es/:path(.*)?']
					]
				}
			]
		}),
		sveltekit()
	]
});
