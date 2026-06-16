# datapoble · Método de equipo v1

> **Actualitzat (2026-06-16):** el mètode canònic és ara **Cambium Charter v0.3.1**, vendoritzat a
> [`.cambium/CHARTER.md`](../.cambium/CHARTER.md) (sello a `.cambium/VERSION`). Aquest document queda
> com a **registre històric** de l'adopció inicial (TRANSFER_KIT) + decisions pròpies; per a la
> doctrina vigent, vegeu el Charter i `.cambium/REGLAS.md`.

Oficio de coordinación adoptado del **TRANSFER_KIT** (proyectos Sprout/Savia, rol Cambium) + decisiones propias de datapoble (idiomas, IA). Semilla del futuro `CONTRIBUTING.md`.

> Crédito: la metodología multiagente viene del kit de Bea. Aquí queda lo que **adopto tal cual**, lo que **adapto** y lo que **descarto**.

---

## 1. Prácticas que adopto tal cual

1. **Jurisdicción acotada.** Cada agente decide en su frente; escala lo que cruza frentes. Nadie edita código fuera de su zona sin *handoff*. *Refusal as a feature*: si no tengo autoridad, rechazo con razón. (CODEOWNERS por carpeta materializa esto.)
2. **Bitácora-as-contract.** El repo es la memoria; el chat es resumen. Decisiones en `bitacora/YYYY-MM-DD_<tema>_<autora>.md`. **Si chat y bitácora divergen, gana la bitácora.** No se borran (evidencia de proceso).
3. **Identity-inline git.** Nunca `git config --global`. Cada commit firma con `-c`: `git -c user.name="Talaia" -c user.email="talaia@datapoble.local" commit …`. Crítico con varias agentes sobre el mismo `.git`.
4. **Worktrees por agente.** Un `.git` central, una carpeta+rama por agente. Aísla sin duplicar repo y elimina casi toda la fricción de clone compartido.
5. **Triple-verify pre-commit.** `git status` + `git branch --show-current` + `git stash list` antes de cada commit. Stash con prefijo `[autora]`.
6. **Spec-to-agent self-contained.** Cuando encargo trabajo, escribo spec que se implementa **sin pedirme nada más**: cita código actual, mockup ASCII si hay UI, *out of scope* explícito (mata el scope creep), sección de coordinación (rama, PR, plazo).
7. **Handoff escrito > corrección unilateral** cuando algo cruza jurisdicciones (diff stat, opciones A/B con comandos exactos, recomendación; decide quien recibe).
8. **PR review como gate.** Ningún PR a `main` con CI en rojo. Talaia es *gatekeeper* de `main`. Review como conversación, con cita concreta. Sin sycophancy (regla del kit: "OK" sobrio, no "¡genial!").
9. **Honest boundaries.** Cada claim marca categoría: *validado* / *contrato demostrado* / *roadmap*. Nunca "soporta X" sin matiz. (Encaja con nuestro principio de publicar hasta los negativos.)
10. **No push directo a `main`** sin permiso de Bea. Lo narrativo (marca, copy, qué se publica) es voto final de Bea; yo propongo 2-3 opciones razonadas.

## 2. Lo que adapto
- **Estructura de repo** del kit → nuestro **monorepo** (packages/ por frente) en vez de `code/<frente>/`. Mantengo `docs/` numerado, `bitacora/`, y "lo que NO va al repo" (secretos, binarios >50MB, el `CAJON/` personal en `.gitignore`).
- **Auditor (Felógeno):** lo adapto a **Plomada** (la plomada comprueba que algo está a plomo = verdadero). Audita **mis** artefactos y los *claims* de trazabilidad/calidad de dato con `affects_decision=false`; sus objeciones recurrentes se promueven a reglas. *Encaja perfecto con un proyecto cuyo eje es la honestidad del dato.* (Recomiendo sumarla; decides tú.)

## 3. Lo que descarto
- Capas `hardware/`, `video/` del kit (no aplican; `media/` y editorial sí).
- R16 (estados systemd) — no usamos systemd.
- Bits muy específicos de hackathon (SUBMISSION para jurado, etc.).

---

## 4. Identidades git del equipo  (familia cartográfica, propuesta)

| Rol | Nombre propuesto | Metáfora | email |
|---|---|---|---|
| Coordinación | **Talaia** | torre de vigía | `talaia@datapoble.local` |
| Datos/pipeline | **Sondeig** | sondeo/perforación que extrae el dato | `sondeig@datapoble.local` |
| Análisis/investigación | **Isohipsa** | curva de nivel que revela la forma | `isohipsa@datapoble.local` |
| IA / semántica | **Brúixola** | brújula: orienta y responde | `bruixola@datapoble.local` |
| Frontend | **Mirador** | el mirador público | `mirador@datapoble.local` |
| Dirección de Arte | **Llegenda** | la leyenda del mapa | `llegenda@datapoble.local` |
| Auditoría | **Plomada** | comprueba que está a plomo | `plomada@datapoble.local` |
| Dirección humana | **Bea** | project lead | `bea@datapoble.local` |

*Naming adaptable — es tu voto. Alternativa: mantener la familia botánica de Sprout/Savia por continuidad.*

---

## 5. Política de idiomas  — DOS capas distintas

### 5a · Idiomas del repo / desarrollo
| Zona | Idioma |
|---|---|
| `README.md`, `CONTRIBUTING.md` | bilingüe **ca + es** (puerta pública catalana) |
| `docs/` | **ca o es** canonical (la primera que se escriba manda), no doble columna |
| `bitacora/` | **libre ca/es** (voz viva del equipo) |
| commits / issues / PRs | libres |
| Código (identifiers/comentarios) | libre, **consistente dentro de cada módulo** |

### 5b · Idiomas del PRODUCTO (interfaz)  ← tu requisito
- **ca + es siempre** disponibles, con selector. **en + fr ampliables** (estructura lista, traducciones después).
- **Default:** `ca` (es un observatorio catalán), con detección de navegador y `es` siempre a un clic.
- **Arquitectura:** i18n con **Paraglide (inlang)** en SvelteKit; catálogos de mensajes por locale (`ca`, `es`, `en`, `fr`); **rutas por idioma** (`/ca`, `/es`) para SEO y enlaces compartibles.
- **Consecuencia en el contrato semántico:** las **métricas llevan etiqueta multilingüe** (`label_ca`, `label_es`, …) — el dashboard y la IA responden en el idioma activo. Cifras/fechas vía `Intl` con locale. Los nombres de municipio son topónimos oficiales catalanes (no se traducen).

---

## 6. Capa de IA — vía OpenRouter

- **Gateway:** **OpenRouter** (API compatible OpenAI, un solo key a muchos modelos). Nos hace **agnósticos de modelo**: elegimos el mejor para ca/es y coste, y comparamos en *evals* sin reescribir.
- **Key:** la das después; vive como **secreto** (env / GitHub Actions secret / secreto de Fly·Cloudflare). **Nunca** en el repo.
- **Patrón:** texto→SQL **restringido a la capa semántica** (solo métricas declaradas, solo lectura), respuesta **siempre con procedencia** (fuente·fecha·fórmula·consulta), **evals** en CI, caché. La IA **responde en el idioma activo** usando las etiquetas localizadas del catálogo.
- `ask.py` del prototipo es el esqueleto; `packages/ai/` lo industrializa contra OpenRouter.

---

## 7. Día 1 del repo (cuando des go)
1. Creo repo `datapoble` (tu usuario, git ya configurado), público, monorepo + `.gitignore` (incluye `CAJON/`).
2. Estructura mínima: `README` bilingüe, `LICENSE`, `CONTRIBUTING.md` (este método), `docs/`, `bitacora/README.md`, `semantic/metrics.yml` (catálogo → contrato multilingüe), `.github/` (CODEOWNERS + CI esqueleto + templates).
3. Bitácora kickoff + tabla de identidades.
4. Reglas vivas: triple-verify, identity-inline, worktrees, PR gate.
5. Escribo la **primera spec** de cada agente y las levanto en worktrees.
