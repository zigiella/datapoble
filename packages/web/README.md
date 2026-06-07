<!-- Document bilingüe · Documento bilingüe — CA primer, ES després -->

# web · Mirador

Frontend de l'observatori **datapoble**: **SvelteKit + TypeScript**, i18n **ca/es** amb **Paraglide (inlang)**.

Frontend del observatorio **datapoble**: **SvelteKit + TypeScript**, i18n **ca/es** con **Paraglide (inlang)**.

> **Estat / Estado:** primer PR — *scaffold* + **una** pantalla («Resum»). Les altres cinc són *stubs* navegables. El sistema de disseny (tokens) és de **Llegenda**; els mapes (MapLibre), els gràfics (Observable Plot) i la pantalla «Pregunta-li» (API de Brúixola) arribaran en PRs posteriors.

---

## CA · Com executar

Requisits: **Node ≥ 20** i **npm** (o pnpm). Des de `packages/web`:

```bash
npm install        # instal·la dependències i compila la i18n (script "prepare")
npm run dev        # servidor de desenvolupament (Vite) → http://localhost:5173
```

Altres ordres:

```bash
npm run paraglide  # (re)compila els missatges i18n a src/lib/paraglide/
npm run build      # build de producció
npm run preview    # serveix el build
npm run check      # type-check (svelte-check)
```

> La carpeta `src/lib/paraglide/` és **generada** (artefacte de build, git-ignored). Si l'editor es queixa d'imports de `$lib/paraglide/...` abans de cap build, executa `npm run paraglide`.

## ES · Cómo ejecutar

Requisitos: **Node ≥ 20** y **npm** (o pnpm). Desde `packages/web`:

```bash
npm install        # instala dependencias y compila la i18n (script "prepare")
npm run dev        # servidor de desarrollo (Vite) → http://localhost:5173
```

Mismas órdenes `paraglide` / `build` / `preview` / `check` que arriba.

---

## Arquitectura del scaffold

```
packages/web/
  project.inlang/settings.json   # config inlang: baseLocale=ca, locales=[ca,es]
  messages/{ca,es}.json          # catàlegs de missatges d'INTERFÍCIE (chrome)
  src/
    hooks.ts                     # reroute: URL localitzada (/es/…) → ruta canònica
    hooks.server.ts              # paraglideMiddleware + <html lang> per SSR
    app.html                     # placeholder %paraglide.lang%
    app.css                      # estils base — TODO(tokens · Llegenda)
    lib/
      contract/types.ts          # tipus del CONTRATO (mirall de semantic/metrics.yml)
      mock/municipis.ts          # dades mock amb forma de contracte (Castellar/Berga)
      i18n.ts                    # pont Paraglide ↔ SvelteKit (locale, pick, localize)
      format.ts                  # Intl: enters, decimals, %, segons locale
      paraglide/                 # GENERAT per Paraglide (git-ignored)
      components/                # LangSwitcher, Nav, KpiCard, MunicipiCard, MetricRow…
    routes/
      +layout.svelte             # capçalera (marca + nav + selector idioma) + peu
      +page.ts                   # / → redirigeix a /resum (localitzat)
      resum/                     # ← l'ÚNICA pantalla implementada
      mapa | index | day-tripper | politica | preguntale/   # stubs navegables
```

### i18n (Paraglide / inlang)

- **Locales:** `ca` (per defecte) + `es`. `en`/`fr` són ampliables afegint-los a `project.inlang/settings.json` i un `messages/{locale}.json`.
- **Rutes per idioma:** URLs localitzades `/ca/...` i `/es/...`. Les rutes del sistema de fitxers es mantenen **canòniques** (un sol arbre); `reroute` (a `src/hooks.ts`) des-localitza la URL entrant i `localizeHref`/`localizeUrl` localitzen els enllaços sortints. Estratègia de detecció: **URL → cookie → baseLocale** (`vite.config.ts`).
- **Selector d'idioma:** `LangSwitcher.svelte` (conserva la ruta, canvia el prefix; la cookie recorda l'elecció).
- **Xifres:** `src/lib/format.ts` fa servir `Intl.NumberFormat` segons el locale (separadors, %, decimals).

### API de «Pregunta-li» (`PUBLIC_API_BASE`)

La pàgina **`/preguntale`** (la cara pública de la IA de Brúixola) consulta l'API **des del navegador** (el web és estàtic, `adapter-static`: no hi ha servidor que faci de proxy). La base de l'API es configura amb una variable d'entorn **pública** de SvelteKit:

```bash
# .env (local) o variable d'entorn del build a Cloudflare Pages
PUBLIC_API_BASE="https://datapoble-api.onrender.com"   # sense barra final
```

- Es llegeix amb `$env/dynamic/public` (a `src/lib/ask/api.ts`), de manera que **si no es defineix, el build no peta**: la pàgina mostra l'estat amable «el servei encara no està actiu».
- En **desenvolupament** (`vite dev`), si no es defineix, s'usa `http://localhost:8000` per defecte.
- En **producció estàtica** sense la variable, queda buida → la pàgina degrada amablement (mai una pantalla trencada). El build i el prerender funcionen **sense API viva**.
- Contracte consumit (NO inventat): `POST {API_BASE}/ask` amb `{ question, locale }` → `{ kind, text, backend, data, provenance, refusal_reason, metric_key }`; HTTP **429** → refús `rate_limited` (capçalera `Retry-After`).

> `.env*` està a `.gitignore`: la variable no es versiona; es defineix a l'entorn de build (Cloudflare Pages) o en un `.env` local.

### Contracte i dades

- Les **etiquetes dels indicadors NO es codifiquen** a la UI ni als catàlegs i18n: vénen del **contracte** (`semantic/metrics.yml`, camps `label.ca`/`label.es`), reflectit a `src/lib/contract/types.ts` i poblat a `src/lib/mock/municipis.ts`.
- El mock du **valors verificats** de **Castellar de n'Hug (INE 08052)** i **Berga (INE 08022)** (vegeu `docs/data-sources.md`). Els agregats comarcals i alguns derivats hi van marcats com a *il·lustratius* fins que el pipeline (Sondeig) publiqui el mart real.
- **Punt d'enganxament:** `src/routes/resum/+page.ts` i `src/lib/mock/municipis.ts` són els dos llocs a canviar quan arribi l'artefacte/API. La forma (`MunicipisDataset`) no canvia.

---

## Honest boundaries (què hi ha i què no)

- ✅ **Implementat:** scaffold SvelteKit + TS, i18n ca/es amb rutes per idioma i selector, formatatge `Intl`, contracte tipat, mock amb forma de contracte (Castellar↔Berga), pantalla **Resum** (KPIs comarcals + dues fitxes), stubs navegables de les altres 5.
- 🟡 **Provisional:** tokens de disseny (valors *placeholder* a `app.css`, marcats `TODO(tokens)`); agregats comarcals i derivats del mock marcats *il·lustratius*.
- 🚧 **Pendent (PRs següents):** MapLibre (mapa coroplètic), Observable Plot (gràfics + taula-alternativa AA), pantalla «Pregunta-li» contra l'API de Brúixola, tests (vitest + Playwright a11y), i el cablejat real de dades.

Detall de la decisió: vegeu `bitacora/2026-06-02_scaffold-web_mirador.md`.
