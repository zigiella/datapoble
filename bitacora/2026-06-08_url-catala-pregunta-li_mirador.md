# Ruta del «Pregunta-li» en català: `/preguntale` → `/pregunta-li` (+ 301 de l'antiga)

**Fecha:** 2026-06-08
**Autora:** Mirador
**Para:** Talaia (review + merge), Bea
**Tema:** La ruta del «Pregunta-li» era en castellà (`/preguntale`). Bea la vol **en català**:
`/pregunta-li` (i `/es/pregunta-li`), coherent amb la resta de rutes de l'observatori. Renombro el
directori de ruta, actualitzo totes les referències i deixo una **redirecció 301** de l'antiga URL
perquè no es trenquin els enllaços ja compartits.
**Status:** completat (renombrament + redirecció; check/build verds, prerender ca/es verificat)

## Contexto
La pàgina «Pregunta-li» (la cara pública de la IA de Brúixola) vivia a `src/routes/preguntale/`
→ URL `/preguntale` · `/es/preguntale`. La **etiqueta** del nav ja era correcta en cada idioma
(clau i18n `nav_preguntale` → «Pregunta-li» / «Pregúntale»); el que quedava en castellà era el
**path** de la ruta. La resta de rutes de l'observatori són canòniques en català, així que aquesta
desencaixava.

## Qué hicimos / decidimos
1. **`git mv src/routes/preguntale/ → src/routes/pregunta-li/`** (`+page.svelte`, `+page.ts`). El
   routing de SvelteKit és per carpetes i el `reroute` de Paraglide des-localitza genèricament
   (`deLocalizeUrl`, sense mapa de rutes a mà) → renombrar la carpeta **és** renombrar la ruta, tant
   a ca (arrel) com a es (`/es/...`).
2. **Referències al path** `/preguntale` → `/pregunta-li`:
   - `+layout.svelte`: enllaç del nav (`localizeHref` + els dos `isActive`) i enllaç del peu
     (`foot_about_ask`).
   - `Nav.svelte`: el `path` canònic de l'ítem (component de nav alternatiu; també hi era).
   - `svelte.config.js`: la **prerender entry** explícita `'/preguntale/'` → `'/pregunta-li/'`
     (clau: el chrome final no enllaça aquesta ruta des de la capçalera per crawling, es declara a
     mà perquè es prerenderitzi i sigui accessible per URL directa).
   - Comentaris de capçalera + `data-view` de la pàgina, i dues mencions al `README.md` de
     `packages/web`.
   - **L'etiqueta i18n NO es toca:** la clau `nav_preguntale` (= «Pregunta-li»/«Pregúntale») és el
     rètol, no la ruta, i es queda. Grep de `preguntale` a `packages/web/src` net tret d'aquesta clau.
3. **Redirecció 301** (Cloudflare Pages, fitxer `static/_redirects` nou — **no** gitignorat, com
   `_headers`/`robots.txt`):

       /preguntale /pregunta-li 301
       /es/preguntale /es/pregunta-li 301

## Por qué
- Renombrar la carpeta (no afegir un alias) manté **una sola** veritat de ruta i no duplica pàgines.
- La 301 (no 302) perquè el canvi és **permanent**: preserva l'enllaç ja compartit i transfereix el
  senyal als cercadors a la URL bona, sense deixar dues URL vives indexables.
- Calia tocar la `prerender entry` o l'antiga `/preguntale/` hauria deixat de prerenderitzar-se i la
  nova `/pregunta-li/` no s'hauria descobert (no s'enllaça per crawling des del chrome).

## Verificación (build del worktree)
- `npm ci` (a `packages/web` — el `package-lock.json` viu allà; el repo **no** té workspace arrel)
  OK. **`npm run check` → 0 errors, 0 warnings** (998 fitxers).
- **`npm run build` → prerender net** (`adapter-static`). A `build/`:
  - `pregunta-li/index.html` i `es/pregunta-li/index.html` **existeixen**; `preguntale/` i
    `es/preguntale/` **ja no**.
  - `build/_redirects` copiat amb les dues línies 301.
  - Hrefs del nav/peu/LangSwitcher a la sortida apunten a `/pregunta-li` i `/es/pregunta-li`; **0**
    `href` residuals a `/preguntale` (verificat a `pregunta-li`, `es/pregunta-li` i `resum`).
- La 301 és una regla **estàtica de Pages** (`_redirects`); `vite preview` no l'honora, així que no
  és verificable en local — el que val és el contingut del fitxer, que és correcte.

## Jurisdicció
Tot dins `packages/web` (rutes, `+layout.svelte`, `Nav.svelte`, `svelte.config.js`, `README.md`,
`static/_redirects`) + aquesta bitàcola. Cap canvi a `data/`, `semantic/metrics.yml`,
`packages/{ai,signals,ingestion,transform}`, `.github/workflows/ci.yml` ni `.gitignore`.

## Pendiente
- [ ] **Talaia:** revisar i mergear (CI verd esperat: `web build + check`).
- [ ] **IT/Pages:** la redirecció 301 només s'activa en desplegar a Cloudflare Pages (és on s'aplica
      `_redirects`); res a fer al repo.

## Enlaces
- `packages/web/src/routes/pregunta-li/{+page.svelte,+page.ts}` (renombrat des de `preguntale/`)
- `packages/web/src/routes/+layout.svelte` (nav + peu → `/pregunta-li`)
- `packages/web/src/lib/components/Nav.svelte` (path canònic)
- `packages/web/svelte.config.js` (prerender entry `/pregunta-li/`)
- `packages/web/static/_redirects` (nou: 301 ca + es)
- `bitacora/2026-06-07_pregunta-li_mirador.md` (creació original de la pàgina)
