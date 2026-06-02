# Scaffold del frontend (SvelteKit + i18n) + pantalla «Resum»

**Fecha:** 2026-06-02
**Autora:** Mirador
**Para:** Talaia (review), Llegenda (tokens), Brúixola (API)
**Tema:** primer PR de `packages/web` — scaffold SvelteKit + TS, i18n ca/es con Paraglide, mock con forma de contrato y la pantalla «Resum» (KPIs comarcales + Castellar↔Berga).
**Status:** avance / handoff

## Contexto
La spec `2026-06-02_spec-frontend_talaia-a-mirador.md` pide portar las 6 pantallas del prototipo a SvelteKit + MapLibre + Observable Plot con i18n ca/es y A11y AA. Esto es demasiado para un PR. Acotamos el primer entregable a **scaffold + UNA pantalla** («Resum»), dejando las otras cinco como stubs navegables, para poder integrar pronto y que Talaia revise la base.

## Qué hicimos / decidimos
- **App SvelteKit + TypeScript** en `packages/web` (adapter-auto, Vite 7, Svelte 5 con runes).
- **i18n con Paraglide v2 (inlang):**
  - `baseLocale: ca`, `locales: [ca, es]`; `en`/`fr` ampliables vía `settings.json` + `messages/{locale}.json`.
  - **Rutas por idioma** `/ca` `/es` con rutas de ficheros **canónicas**: `reroute` (en `src/hooks.ts`) des-localiza la URL entrante; `localizeHref/localizeUrl` localizan los enlaces. Estrategia de detección **url → cookie → baseLocale**.
  - `hooks.server.ts` usa `paraglideMiddleware` (AsyncLocalStorage) e inyecta `<html lang>`.
  - Selector de idioma (`LangSwitcher.svelte`) que conserva la ruta.
  - Cifras con `Intl.NumberFormat` por locale (`src/lib/format.ts`).
- **Contrato tipado** (`src/lib/contract/types.ts`): espejo de `semantic/metrics.yml` (claves de métrica = columnas del mart, labels ca/es, source, date, note, status).
- **Mock con forma de contrato** (`src/lib/mock/municipis.ts`): Castellar de n'Hug (INE **08052**) y Berga (INE **08022**) con **valores verificados** de `docs/data-sources.md`. Agregados comarcales y algunos derivados van marcados *ilustrativos* hasta que el mart real los calcule.
- **Pantalla «Resum»**: KPIs comarcales + dos fichas Castellar↔Berga, leyendo el mock. **Las labels vienen del contrato**, no se hardcodean; solo el chrome (nav, botones, títulos) está en los catálogos i18n.
- **Stubs navegables** de las otras 5 (mapa, índice, day-tripper, política, pregúntale) vía `StubScreen.svelte`.

## Por qué
- **Paraglide v2, no el adaptador legacy.** El antiguo `@inlang/paraglide-sveltekit` (0.16.x) está deprecado; en v2 la integración SvelteKit es el plugin de Vite + `reroute` + `paraglideMiddleware`. Documentado para no reintroducir el paquete viejo.
- **Labels desde el contrato.** Es regla de la spec y del contrato («ningún número sin procedencia», labels en `label.ca/.es`). Separar *chrome* (i18n) de *datos del dominio* (contrato) evita divergencias cuando cambie `metrics.yml`.
- **Rutas canónicas + reroute.** Evita duplicar carpetas por idioma; un solo árbol de rutas escala a en/fr sin tocar el filesystem.
- **Forma de contrato fija.** `resum/+page.ts` y el mock son los dos únicos puntos a cambiar cuando llegue el artefacto/API; `MunicipisDataset` no cambia.

## Honest boundaries
- Tokens de diseño = **placeholders** en `app.css` (marcados `TODO(tokens)`); son de Llegenda.
- Agregados comarcales y derivados per cápita del mock = *ilustrativos*.
- Sin MapLibre / Observable Plot / API de Brúixola / tests todavía (PRs siguientes).
- Build: ver REPORTE del PR (si corrió o solo scaffold) — honest boundary explícita.

## Pendiente
- [ ] **Llegenda:** publicar tokens (Style Dictionary → CSS custom properties) para sustituir el `:root` provisional de `app.css`.
- [ ] **Sondeig:** mart real (parquet/JSON) con la forma de `MunicipisDataset` para reemplazar el mock.
- [ ] **Brúixola:** contrato de la API «Pregúntale» (request/response + procedencia).
- [ ] Mirador: MapLibre (mapa coroplético, 31 municipios), Observable Plot + tabla-alternativa (A11y AA), pantalla «Pregúntale», vitest + Playwright (a11y), añadir job `web` al CI (`pnpm/npm install + build + check`).
- [ ] Confirmar gestor del monorepo (pnpm workspaces vs npm) con Talaia; aquí se usó npm por ausencia de pnpm en el entorno.

## Enlaces
- Spec: `bitacora/2026-06-02_spec-frontend_talaia-a-mirador.md`
- Contrato: `semantic/metrics.yml`
- Datos verificados: `docs/data-sources.md`
- Rama: `feat/mirador-web`
