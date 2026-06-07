# Nav superior — estat actiu (pestanya `.on`) restaurat a `/es/*`

**Fecha:** 2026-06-07
**Autora:** Mirador
**Para:** Talaia (review + merge), Bea
**Tema:** El nav superior no marcava **cap** pestanya activa quan es navegava per les rutes en
castellà (`/es/*`). Ara `isActive` compara contra la ruta **des-localitzada**, així que la pestanya
correcta s'il·lumina tant a ca (arrel) com a es (`/es/...`), per als cinc enllaços.
**Status:** completat (fix d'1 línia de comportament + comentari)

## Contexto
Bug menor pre-existent (flagejat a l'estat de Talaia: «el nav no marca pestanya activa a `/es/*`»).
`+layout.svelte` definia:

    const path = $derived(page.url.pathname);
    function isActive(p) { return path === p || path.startsWith(p + '/'); }

i el nav crida `isActive('/resum')`, `isActive('/mapa')`, … sempre amb la ruta **canònica sense
prefix de locale**. Però `page.url.pathname` **conserva** el prefix a castellà (`/es/resum/`):
el `reroute` de Paraglide des-localitza el *routing de fitxers*, no la URL observable.
Conseqüència: a `/es/resum/`, ni `=== '/resum'` ni `startsWith('/resum/')` casen → `.ds-nav a.on`
buit. A ca (`/resum/`) funcionava de rebot via la branca `startsWith`.

## Qué hicimos / decidimos
**Una sola línia de comportament:** des-localitzar la URL abans de comparar.

    import { localizeHref, deLocalizeUrl } from '$lib/i18n';
    ...
    const path = $derived(deLocalizeUrl(page.url).pathname);

`deLocalizeUrl` ja era al runtime de Paraglide i **reexportat per `$lib/i18n`** (és el simètric de
`localizeHref`, que aquest mateix layout ja fa servir per als `href`). Amb el patró d'URL per
defecte (`/:locale/*`; **no hi ha `urlPatterns`** a `vite.config.ts`) **clona** la URL —no muta
`page.url`— i treu el segment de locale capdavanter:
- `/es/resum/` → `/resum` → `isActive('/resum')` casa per `=== '/resum'`.
- `/resum/` (ca, sense prefix) → intacte → casa per `startsWith('/resum/')`.

`isActive` i el markup del nav **no es toquen**. El comentari s'actualitza (deia «rutes canòniques…
reroute/localize fan la traducció», cosa que induïa a error: el reroute NO toca `page.url.pathname`).

## Por qué
- És el simètric net de `localizeHref`: el layout localitza els `href` de sortida i des-localitza el
  pathname d'entrada amb **la mateixa font** (`$lib/i18n`). Cap heurística de prefixos a mà ni segona
  font de veritat de rutes, ni duplicar la llista de locales.
- `deLocalizeUrl` **clona** (no muta `page.url`) → cap efecte secundari reactiu; el `$derived` recalcula
  bé en cada navegació.

## Verificación (vite dev del worktree, port 5174)
- `npm ci` OK. **`npm run check` → 0 errors, 0 warnings** (998 fitxers). **`npm run build` →
  prerender net** amb `adapter-static`.
- **SSR de les 10 rutes** (5 enllaços × ca/es), inspeccionant `.ds-nav a.on`: cadascuna marca
  **exactament 1** pestanya activa, la correcta, amb `aria-current="page"`:
  - ca: `/resum/`→Resum · `/mapa/`→Mapa · `/metodologia/`→Metodologia · `/glossari/`→Glossari · `/preguntale/`→Pregunta-li.
  - es: `/es/resum/`→Resumen · `/es/mapa/`→Mapa · `/es/metodologia/`→Metodología · `/es/glossari/`→Glosario · `/es/preguntale/`→Pregúntale.
  - Cap sobre-coincidència (1 activa per pàgina, mai 0 ni 2). **0 logs de consola.**

## Jurisdicció
Tot dins `packages/web` (1 fitxer: `+layout.svelte`) + aquesta bitàcola. Cap canvi a `data/`,
`semantic/`, `tools/`, workflows ni a la resta de `packages/`.

## Pendiente
- [ ] **Talaia:** revisar i mergear (CI verd esperat: `web build + check`).

## Enlaces
- `packages/web/src/routes/+layout.svelte` (import `deLocalizeUrl`; `path` des-localitzat; comentari)
- `packages/web/src/lib/i18n.ts` (ja reexportava `deLocalizeUrl`; sense canvis)
