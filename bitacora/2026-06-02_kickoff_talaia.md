# Kickoff datapoble

**Fecha:** 2026-06-02 (día 1)
**Autora:** Talaia (coordinación)
**Tema:** nacimiento del repo de producción; decisiones fundacionales fijadas con Bea.
**Status:** decisión

## Contexto
Venimos de un prototipo validado (laboratorio): base DuckDB, índice IETR validado (r=0,87 vs residuos), modelo day-tripper, capa política y un dashboard + capa de IA trazable. Bea pide subir el listón a producción con equipo multiagente. Yo (Talaia) asumo el oficio de coordinación del TRANSFER_KIT.

## Qué decidimos
- **Despliegue:** observatorio **público** (Cloudflare Pages + dominio; IA en API pequeña; refresh programado).
- **Frontend:** **SvelteKit + MapLibre** (control de marca).
- **Alcance investigación:** **escalar a Catalunya** (~947 municipios) para *extrema derecha × edad*; Berga y Castellar como casos destacados.
- **Equipo: 4 agentes** + Talaia + Bea. Naming **cartográfico**.
- **Foco político:** de independentismo → **extrema derecha (Vox + Aliança Catalana) + estructura de edad**, lectura ecológica y honesta.
- **IA:** vía **OpenRouter** (agnóstico de modelo; key como secreto, pendiente).
- **Idiomas:** UI **ca + es** siempre, **en + fr** ampliables → el contrato semántico lleva etiquetas multilingües.
- **Marca:** la propone Llegenda desde cero.
- **Sin auditora (Plomada)** por ahora.

## Identidades git (identity-inline obligatorio)
| Rol | Nombre | email |
|---|---|---|
| Coordinación + investigación | Talaia | talaia@datapoble.local |
| Datos / pipeline | Sondeig | sondeig@datapoble.local |
| IA / semántica | Brúixola | bruixola@datapoble.local |
| Frontend | Mirador | mirador@datapoble.local |
| Dirección de arte | Llegenda | llegenda@datapoble.local |
| Dirección humana | Bea | bea@datapoble.local |

GitHub: cuenta **zigiella** (push vía gh). Repo público `datapoble`.

## Por qué
Right-sizing: el dato es pequeño; la seniority está en contratos, tests, linaje, diseño y coordinación — no en infra pesada. Contracts-first: Talaia escribe la capa semántica y las specs; las 4 agentes paralelizan contra ellas sin pisarse.

## Pendiente
- [ ] `semantic/metrics.yml` multilingüe (contrato).
- [ ] CI completa (lint, dbt, evals, build web).
- [ ] Primera spec de Sondeig, Brúixola, Mirador, Llegenda.
- [ ] Migrar marts del prototipo de forma reproducible (F1).
- [ ] Recibir key de OpenRouter (secreto).

## Enlaces
- docs/architecture.md · docs/team-method.md · docs/art-direction.md
