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
 */
export const prerender = true;
export const trailingSlash = 'always';
