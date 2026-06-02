# CI: job `web` (build + type-check) del frontend

**Fecha:** 2026-06-02
**Autora:** Mirador
**Para:** Talaia (gatekeeper de `main` / CI), Llegenda (su job es el siguiente TODO)
**Tema:** sustituir el `# TODO(Mirador)` de `.github/workflows/ci.yml` por un job real que construye y type-checkea `packages/web`.
**Status:** decisión / avance

## Contexto
El esqueleto de CI dejaba `# TODO(Mirador): pnpm install + build + vitest + playwright (a11y)`. Ya existe `packages/web` (scaffold SvelteKit + i18n, PR #2 mergeado). Quedaba pendiente desde el scaffold «añadir job `web` al CI» (ver bitácora de scaffold, Pendiente). La regla del repo es **ningún PR a `main` con CI en rojo**, así que el frente frontend necesita su gate.

## Qué hicimos / decidimos
- Nuevo job **`web`** (`web build + check`) en `ci.yml`, en la jurisdicción de Mirador (reemplaza el `TODO(Mirador)`; el `TODO(Llegenda)` queda intacto).
- **Gestor: npm, no pnpm.** Pasos: `npm ci` → `npm run check` (svelte-check) → `npm run build` (build de producción).
  - `npm ci` ejecuta el script `prepare` (compila Paraglide + `svelte-kit sync`); además `check` y `build` recompilan Paraglide por sí mismos. No hace falta un paso `paraglide` aparte.
- **Node 22** vía `actions/setup-node@v4` (app requiere Node ≥ 20; Vite 8 pide ≥ 20.19/22.12; desarrollada en Node 24). `cache: npm` con `cache-dependency-path: packages/web/package-lock.json` (el lockfile no está en la raíz).
- **Sin vitest ni playwright (a11y) todavía** — esos tests aún no existen; llegan en un PR posterior, como dice el propio TODO.
- Verificado en local antes de abrir PR: `npm ci && npm run check && npm run build` en `packages/web` → check 0 errores, build verde.

## Por qué
- **npm y no pnpm**: no hay `package.json` ni `pnpm-workspace.yaml`/`pnpm-lock.yaml` en la raíz — no existe workspace pnpm. `packages/web` tiene su `package-lock.json` commiteado y la app se desarrolló con npm (ausencia de pnpm en el entorno). Un job pnpm hoy sería sobre una config inexistente. Elegimos lo mínimo que funciona y es reproducible.
- **`working-directory: packages/web`** (vía `defaults.run`): mismo patrón que el job `ai-evals` de Brúixola → CI consistente entre frentes.

## Honest boundaries
- Si más adelante se adopta **pnpm workspaces** en la raíz (lo mencionan specs de otros frentes, sin confirmar), este job debe revisarse: `pnpm/action-setup` + `pnpm install` + filtros de workspace. Decisión de gestor del monorepo sigue **pendiente con Talaia**.
- El gate cubre **build + type-check**, no comportamiento ni a11y todavía.

## Pendiente
- [ ] **Talaia:** confirmar gestor del monorepo (npm vs pnpm workspaces). Si pnpm, migrar este job.
- [ ] **Mirador:** añadir vitest + Playwright (a11y) al job `web` cuando existan los tests.
- [ ] **Llegenda:** su job de regresión visual (siguiente TODO en `ci.yml`).

## Enlaces
- Workflow: `.github/workflows/ci.yml` (job `web`)
- Scaffold previo: `bitacora/2026-06-02_scaffold-web_mirador.md` (Pendiente: «añadir job `web` al CI»)
- Rama: `feat/mirador-ci`
