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
			strategy: ['url', 'cookie', 'baseLocale']
		}),
		sveltekit()
	]
});
