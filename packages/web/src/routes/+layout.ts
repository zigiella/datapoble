/**
 * Config de prerender per a tota l'app (adapter-static · Cloudflare Pages, F2).
 *
 * `prerender = true`: cada ruta es renderitza a HTML estàtic en build. El site no
 * depèn de cap servidor en runtime (Pages serveix fitxers). El mapa (MapLibre) toca
 * `window`, així que el seu mòdul es carrega NOMÉS al client (onMount + import dinàmic);
 * el prerender d'aquesta ruta entrega el shell i el mapa s'hidrata al navegador.
 *
 * `trailingSlash = 'always'`: genera `ruta/index.html` (compatible amb el routing
 * d'arxius estàtics de Pages i amb el rewrite de locale de Paraglide).
 *
 * PREFIX DE LLENGUA: amb `urlPatterns` (vite.config) totes les URLs porten prefix /ca|/es.
 * Les rutes canòniques (sense prefix) es generen igualment com a fallback en ca, però NO
 * s'enllacen enlloc (tots els enllaços passen per `localizeHref`) i el host les redirigeix
 * a /ca via `static/_redirects`. La redirecció es fa al host (no a un `load` universal):
 * fer-la al layout trenca el prerender de SvelteKit (fetch + redirect = «Body already read»).
 */
export const prerender = true;
export const trailingSlash = 'always';
