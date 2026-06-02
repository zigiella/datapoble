# datapoble · Plan de arquitectura v2

**Autora:** Talaia (arquitecta · investigadora · coordinadora)
**Estado:** propuesta para revisión · **Fecha:** 2026-06
**De:** prototipo de laboratorio (scripts + DuckDB + HTML estático)
**A:** observatorio territorial de producción, reproducible, diseñado y multiagente.

---

## 0. Mi rol (Talaia) y cómo trabajo

No escribo el grueso del código. **Defino la arquitectura y los contratos, redaccto las specs/ADRs, abro y triо las issues, reviso los PRs e integro.** Cada agente especialista es dueña de su paquete y trabaja contra contratos estables (esquemas, capa semántica, API, design tokens), no contra las tripas de las demás. Eso es lo que permite paralelizar sin pisarnos.

Flujo de una mejora: *Talaia escribe la issue/spec → agente dueña implementa en su worktree aislado → CI valida contra el contrato → Talaia revisa e integra → deploy*. 

---

## 1. Re-encuadre del proyecto

Dejamos de ser "experimentos en un cajón" para ser un **observatorio territorial de producción**: abierto, reproducible, citable, bien diseñado y honesto. Principios no negociables (lo que da seniority de verdad):

1. **Right-sizing.** El dato es *pequeño* (31 municipios hoy; ~947 de Catalunya en el techo = sigue siendo pequeño). **Nada de Spark/Snowflake/Kafka.** La seniority está en el rigor, los contratos, los tests, el diseño y la coordinación — no en infraestructura pesada. Resistir la sobre-ingeniería es una decisión senior.
2. **Reproducibilidad.** De la fuente cruda a la pantalla, todo se reconstruye con un comando. Datos versionados, linaje explícito.
3. **Trazabilidad.** Ningún número sin fuente, fecha y fórmula. La capa semántica es la única fuente de verdad y el contrato con la IA.
4. **Diseño como producto.** El observatorio tiene dirección de arte, sistema de diseño y lenguaje cartográfico propio. No "gráficos por defecto".
5. **Honestidad incl. resultados negativos.** Si la hipótesis no se sostiene (como pasó con touristificación × voto), se publica el "no". 
6. **Privacidad y ética by design.** Lectura ecológica, no individual; cautela en micromunicipios; minimización.
7. **Accesibilidad** (WCAG AA) y **rendimiento** (presupuesto explícito) como requisitos, no extras.
8. **Abierto.** Repo público, datos abiertos, metodología auditable.

---

## 2. Diagnóstico honesto del prototipo

Lo que construimos funciona y validó la tesis, pero **no es producción**:

| Dimensión | Prototipo (hoy) | Carencia |
|---|---|---|
| Ingesta | scripts imperativos ad-hoc | sin idempotencia formal, sin esquema validado, rutas hardcodeadas |
| Transformación | pandas imperativo | sin tests, sin linaje, lógica mezclada con ingesta |
| Almacén | DuckDB + CSV sueltos | sin capas (raw/staging/marts), sin versionado de datos |
| Semántica | catálogo JSON | bien encaminado, pero no es *single source of truth* consumido por todos |
| IA | `ask.py` router por keywords | sin LLM real, sin evals, sin guardarraíles formales |
| Frontend | un HTML con JSON embebido | sin sistema de diseño, sin componentes, sin build, sin tests |
| Infra | mi portátil, sandbox | sin CI/CD, sin secretos gestionados, sin deploy, sin orquestación |
| Equipo | 1 (yo, a mano) | sin estructura para paralelizar agentes |

El prototipo es el **walking skeleton** perfecto: prueba que toda la cadena funciona. v2 lo industrializa.

---

## 3. Arquitectura objetivo

```
 FUENTES        Idescat · RTC · ARC · ICAEN · IMD · Electoral · Wikipedia
 (APIs)         · Catastro INSPIRE · ICGC
                      │  connectors (Python/dlt) + metadatos de procedencia
 INGESTA        ┌─────▼─────────────────────────────┐
                │  raw/   (tal cual, versionado)      │
 TRANSFORM      ├─────▼─────────────────────────────┤
 (dbt+DuckDB)   │  staging → intermediate → marts     │  + spatial + tests + linaje
 CAPA           ├─────▼─────────────────────────────┤
 SEMÁNTICA      │  métricas.yml = ÚNICA FUENTE VERDAD  │ ◀── contrato (def·fórmula·fuente·fecha)
                └──┬──────────────────────────┬──────┘
        build-time │                          │ runtime
            ┌──────▼──────────┐        ┌──────▼───────────────┐
 SALIDAS    │ artefactos       │        │ API (FastAPI)         │
            │ estáticos        │        │ + IA texto→SQL        │
            │ (Parquet/JSON/geo)│       │   trazable (Claude)   │
            └──────┬───────────┘        └──────┬───────────────┘
            ┌──────▼───────────────────────────▼──────┐
 FRONTEND   │ SvelteKit + MapLibre + Observable Plot   │ ◀── design system (dir. arte)
 (prod)     │ scrollytelling · a11y · responsive       │
            └──────────────────────────────────────────┘
   Orquesta: Dagster/GitHub Actions · CI/CD · datos versionados · monorepo
```

Capas con frontera clara = ownership clara = paralelización.

---

## 4. Decisiones técnicas (ADRs resumidas)

**ADR-01 · Almacén: DuckDB + Parquet, no warehouse.** El dato es pequeño; DuckDB (con extensión `spatial`) da SQL analítico + geo en un fichero. Parquet/GeoParquet como formato de intercambio. *Alternativa descartada:* Postgres/PostGIS (innecesario salvo que haya concurrencia de escritura; lo reservamos para si hay backend transaccional).

**ADR-02 · Transformación: dbt-duckdb.** Modelos SQL versionados, **tests de calidad**, **linaje**, **docs** autogeneradas, `exposures`. Capas `staging → intermediate → marts`. Sustituye al pandas imperativo. *Por qué:* convierte la lógica en activos testeables y documentados.

**ADR-03 · Ingesta: connectors Python + `dlt`.** Un connector por fuente, idempotente, con **procedencia** (source, url, fetched_at, licencia) y validación de esquema (`pydantic`/`pandera`). `dlt` aporta state, incrementalidad y evolución de esquema sin montar nada pesado.

**ADR-04 · Orquestación: Dagster (con salida lean = Make + Actions).** Assets definidos por software → linaje de punta a punta, integra dbt y DuckDB. Si el equipo prefiere mínimo: `Makefile` + cron de GitHub Actions. *Recomiendo Dagster* por el encuadre "producto de datos".

**ADR-05 · Capa semántica = única fuente de verdad.** Las métricas se definen **una vez** (`semantic/metrics.yml`, evolución del catálogo actual) y las consumen **API, IA y frontend**. CI falla si datos y catálogo se desincronizan. Es la pieza que hace la IA fiable y el front coherente.

**ADR-06 · IA: Claude (Anthropic API) con tool-use sobre la capa semántica.** Texto→SQL **restringido a las marts y a métricas declaradas** (sin SQL arbitrario), respuesta **siempre con procedencia**, **evals** (set pregunta→esperado) en CI, caché. *Guardarraíles:* solo lectura, parametrizado, solo métricas del contrato. `ask.py` evoluciona a esto.

**ADR-07 · Salidas híbridas.** El dashboard consume **artefactos estáticos** (Parquet/JSON pre-construidos en build → baratísimo, CDN, rápido). La **IA conversacional** vive en una **API pequeña** (FastAPI) sólo cuando hace falta runtime. Lo mejor de ambos.

**ADR-08 · Frontend: SvelteKit + MapLibre GL + Observable Plot.** Control de diseño total para la dirección de arte, mapas vectoriales bonitos y abiertos (sin tiles de pago), charts declarativos. TypeScript. Adapter estático para deploy barato. *Alternativa:* Astro (si pesa más lo editorial) u Observable Framework (más rápido, menos control de marca).

**ADR-09 · Diseño: Figma → tokens → código.** Figma como fuente de verdad de diseño; **design tokens** (Style Dictionary) → variables CSS/tema; **Storybook** para la librería de componentes; **regresión visual** (Chromatic/Playwright) en CI.

**ADR-10 · Infra/deploy.** Web estática → **Cloudflare Pages** (gratis, CDN). IA/API → **Fly.io**/Workers (pequeño). Pipeline → **GitHub Actions** programado: re-pull fuentes → rebuild marts → tests → commit de datos versionados → deploy. **Datos versionados en el repo** (son pequeños) o DVC.

**ADR-11 · Monorepo + DevEx.** `pnpm` workspaces (JS) + `uv` (Python), `Taskfile`/`Makefile`, `pre-commit` (ruff, black, eslint, prettier), devcontainer. Un comando para levantar todo.

---

## 5. Repo en GitHub y modelo de coordinación

**Repo:** `datapoble` (monorepo, público). Estructura:

```
datapoble/
├─ README.md                  · visión + quickstart
├─ docs/
│  ├─ architecture.md         · este documento, vivo
│  ├─ adr/                     · decisiones (una por fichero)
│  ├─ research-agenda.md       · preguntas + metodología
│  └─ design-system.md         · brief de dirección de arte
├─ .github/
│  ├─ workflows/               · ci, data-refresh (cron), deploy, visual-regression
│  ├─ CODEOWNERS               · ownership por ruta (= por agente)
│  ├─ ISSUE_TEMPLATE/ · PULL_REQUEST_TEMPLATE.md
├─ packages/
│  ├─ ingestion/               · connectors (dlt) + procedencia        [agente Datos]
│  ├─ transform/               · proyecto dbt (staging→marts)          [agente Datos/Análisis]
│  ├─ semantic/                · metrics.yml (única fuente de verdad)  [Talaia + agente IA]
│  ├─ ai/                      · texto→SQL trazable + evals (FastAPI)  [agente IA]
│  ├─ web/                     · SvelteKit + MapLibre                  [agente Frontend]
│  └─ design-system/           · tokens + componentes + Storybook      [Dir. de Arte]
├─ data/  raw/ staging/ marts/ geo/   · artefactos versionados
├─ catalog/                    · diccionario semántico (legado→semantic/)
├─ pipelines/                  · Dagster assets (o Makefile lean)
└─ Taskfile.yml · pyproject.toml · pnpm-workspace.yaml · .pre-commit-config.yaml
```

**Coordinación:**
- **CODEOWNERS por ruta** → cada PR pide revisión automática de su dueña + de Talaia para cambios de contrato.
- **Trunk-based** + ramas cortas + PR obligatorio + **CI como gate** (lint, types, pytest, dbt build+test, evals IA, build web, regresión visual).
- **GitHub Projects** (tablero): Talaia mantiene el backlog, escribe issues-spec con criterios de aceptación, tria y prioriza.
- **ADRs** en `docs/adr/`: las decisiones con rationale quedan escritas (no en la cabeza de nadie).
- **Worktrees aislados** para que las agentes trabajen en paralelo sin colisión (cada feature, su worktree).
- **Definition of Done**, guía de contribución y plantillas de PR/issue desde el día 1.

---

## 6. El equipo (agentes) y la dirección de arte

| Rol | Dueña de | Contrato que respeta |
|---|---|---|
| **Talaia** (arquitecta/coordinadora) | arquitectura, capa semántica, research, review, integración | — define los contratos |
| **Agente Datos** | `ingestion/`, `transform/` (staging) | esquemas de fuente + marts |
| **Agente Análisis/Investigación** | marts, indicadores, IETR, agenda política | capa semántica |
| **Agente IA** | `ai/` (texto→SQL, evals) | capa semántica (solo métricas declaradas) |
| **Agente Frontend** | `web/` | API/artefactos + design tokens |
| **Directora de Arte** | `design-system/`, cartografía, dataviz, marca | tokens + a11y + perf budget |
| **Agente QA/Datos** *(opc.)* | tests, CI, calidad de dato | DoD |
| **Agente Editorial** *(opc.)* | informes narrativos, fact-check de la IA | trazabilidad |

La **Directora de Arte** no "pinta al final": define el sistema desde el principio (ver §7) y empareja con la Agente Frontend. Talaia arbitra el equilibrio diseño↔ingeniería (presupuesto de rendimiento, complejidad).

---

## 7. Diseño en producción (brief para la Dirección de Arte)

1. **Marca e identidad.** Nombre, logo, voz. Un observatorio serio pero legible por un alcalde y por un vecino.
2. **Design tokens** (color, tipografía, espacio, radios, sombras) como única fuente, exportados de Figma → consumidos por código. Coherencia garantizada.
3. **Lenguaje cartográfico propio.** Basemap MapLibre **custom** (apagado, para que el dato resalte). Paletas coropléticas **perceptualmente uniformes + seguras para daltonismo + con significado** (una escala de "exposición/presión"). El mapa es un objeto diseñado, no tiles por defecto.
4. **Lenguaje de dataviz.** Componentes de gráfico consistentes, estilo de anotación, formato numérico (locale ca/es), unidades, la narrativa "dos extremos" (Castellar↔Berga) como patrón.
5. **Capa editorial / scrollytelling.** El observatorio *cuenta historias verdaderas* (el day-tripper, el índice, la extrema derecha). Enlaza con los "informes narrativos" de la spec.
6. **Accesibilidad AA**: navegación por teclado, alternativa en tabla para cada gráfico (lectores de pantalla), `prefers-reduced-motion`, contraste.
7. **Responsive + presupuesto de rendimiento**: funciona en el móvil del alcalde; mapas pesados con lazy-load; budget acordado con Frontend.
8. **Pipeline Figma → Storybook → regresión visual** en CI (el diseño no se rompe en silencio).

---

## 8. Agenda de investigación (incl. política ampliada)

**Cambio de foco político pedido:** de "independentismo" a **extrema derecha + edades**.

**8.1 · Indicador de extrema derecha (nuevo).**
- `pct_extrema_dreta` = (Vox + **Aliança Catalana** + PxC[histórico] + España2000/otros) / voto válido, **por municipio y por convocatoria** (2010s → 2024). Fuente: electoral `ntc4-rnwr` (ya verificada, tenemos todas las candidaturas por mesa/municipio).
- **La historia es Aliança Catalana**: extrema derecha independentista, *emergente y rural*. En Castellar fue 2ª fuerza (~25%) en 2024. Serie temporal 2021→2024 para capturar la **irrupción**.

**8.2 · Estructura de edad (nuevo).**
- Por municipio: tramos 0-14 / 15-64 / 65-84 / 85+, **índice de envejecimiento** (65+/0-14), edad media. Fuente: Idescat EMEX (tabla `t25`, verificada) + Censo INE.

**8.3 · Cruce (ecológico, honesto).**
- Extrema derecha × envejecimiento × despoblación × % no principal × tamaño × IETR. Spearman + **correlaciones parciales controlando por tamaño** (aprendimos que el tamaño confunde).
- **Honestidad metodológica obligatoria:** es **ecológico** (correlación territorial), **no individual** — no podemos decir "los mayores votan a la extrema derecha" (falacia ecológica); solo "los municipios con estructura X muestran cuota Y". Micromunicipios = N pequeño = volátil.
- **Potencia estadística:** la comarca (31) es poca muestra. Para la pregunta extrema-derecha × edad, **escalar a los ~947 municipios de Catalunya** (el dato está todo en `ntc4-rnwr` + Idescat) → n real. Berga y Castellar quedan como casos destacados dentro de la distribución catalana.

**8.4 · Otros workstreams de investigación.**
- **Capa física/geo** (Catastro INSPIRE + ICGC): edificios, parcelas, antigüedad, pendientes → riqueza territorial real en el mapa.
- **Gap registro-vs-observado** (alojamiento informal): conteo manual, universo de decenas.
- **Participación/abstención** (dataset de participación electoral) como capa cívica.

---

## 9. Roadmap por fases

- **F0 · Fundación (Talaia + Datos).** Crear repo, monorepo, CI esqueleto, CODEOWNERS, ADRs, devcontainer, Taskfile. Migrar el catálogo a `semantic/metrics.yml`.
- **F1 · Pipeline (Datos).** Connectors `dlt` + dbt staging→marts + tests, reproduciendo lo actual con linaje y calidad. Datos versionados.
- **F2 · Semántica + IA (IA + Talaia).** Métricas como contrato; texto→SQL trazable con Claude + evals + guardarraíles.
- **F3 · Diseño + Frontend (Dir. Arte + Frontend).** Design system, cartografía custom, SvelteKit + MapLibre; portar las 6 pantallas; scrollytelling.
- **F4 · Investigación ampliada (Análisis).** Extrema derecha + edades a escala Catalunya; capa física/geo.
- **F5 · Producción.** Deploy (Cloudflare + Fly), refresh programado, observabilidad, dominio.

Las fases se solapan donde los contratos lo permiten (Diseño puede empezar en F1 contra datos mock).

---

## 10. Decisiones que necesito de ti

1. **Ambición/hosting:** ¿observatorio público desplegado (dominio + CDN), o privado/demo por ahora? (define infra y presupuesto — todo lo propuesto cabe en *free tier*).
2. **GitHub:** ¿org/usuario y nombre de repo? ¿público desde el principio?
3. **Frontend:** ¿priorizamos **control de marca** (SvelteKit, mi recomendación) o **velocidad** (Observable Framework)?
4. **Roster de agentes:** ¿arrancamos con Datos + IA + Frontend + Dirección de Arte, o más ligero?
5. **Dirección de la marca:** ¿hay nombre/identidad visual deseada para el observatorio, o la propone la Directora de Arte desde cero?
6. **Alcance geográfico:** ¿nos quedamos en el Berguedà o escalamos a Catalunya para la investigación de extrema derecha × edad (recomendado por potencia estadística)?
