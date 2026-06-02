# Brief de hosting e infraestructura — Observatorio datapoble

**Para:** Sistemas · **De:** coordinación del proyecto (por encargo de Bea) · **Fecha:** 2026-06

## Naturaleza técnica (resumen)
Observatorio público con **tres piezas** y un rasgo que lo simplifica todo: es **dato pequeño** (de decenas a ~947 municipios; todo cabe en ficheros). En consecuencia:
- **No** hay base de datos servidor (usamos **DuckDB + Parquet**, ficheros).
- **No** hay sistema transaccional ni **datos personales** en la capa pública.
- El repo es **público** (`github.com/zigiella/datapoble`), código abierto + datos abiertos.

| # | Pieza | Qué es |
|---|---|---|
| 1 | **Web estática** | SvelteKit compilado a estático: mapas (MapLibre), indicadores, i18n **ca/es** (en/fr ampliable) |
| 2 | **API de IA pequeña** | FastAPI, texto→SQL **trazable**; responde preguntas en lenguaje natural vía **OpenRouter** |
| 3 | **Pipeline programado** | re-descarga las APIs abiertas, reconstruye los datos y publica |

## Necesidades de hosting

| Pieza | Necesidad | Recomendación | Coste aprox. |
|---|---|---|---|
| Web estática + CDN + SSL | hosting estático con dominio propio | **Cloudflare Pages** (alt.: Netlify / Vercel) | free tier |
| API de IA | contenedor/serverless pequeño, con secreto + salida a `openrouter.ai` | **Fly.io** / Render (alt.: CF Workers) | ~pocos €/mes |
| Pipeline programado | cron que ejecuta el rebuild y publica | **GitHub Actions** (cron) | incluido |
| Dominio + DNS | el **.cat** que fije Marketing | registrador .cat + DNS en el CDN | ~20 €/año |
| Secretos | `OPENROUTER_API_KEY` (y futuros) | secrets de GitHub Actions + del host de la API | — |

Sin servidor de BD, sin VM persistente, sin almacenamiento grande.

## Qué necesitamos de Sistemas
1. **Registrar el dominio** (.cat) cuando Marketing fije el nombre, + configurar **DNS**.
2. **Cuenta/proyecto en el host estático** (Cloudflare Pages recomendado) conectado al repo de GitHub.
3. **Host para la API de IA** (Fly.io / Render) + provisión del secreto **`OPENROUTER_API_KEY`** (lo aporta Bea; **nunca** va al repo).
4. **Confirmar minutos de GitHub Actions** para el refresh programado.
5. Revisar la **postura de cumplimiento** (abajo).

## Seguridad y cumplimiento
- **Datos abiertos** de fuentes oficiales (Catastro, ICGC, Idescat, Dades Obertes de Catalunya, INE, datos electorales): cada una con su **licencia/atribución**, documentadas en el repo.
- **Sin datos personales en la capa pública.** La capa política es **ecológica y agregada** (no individual), con caveats explícitos; el voto a nivel municipio es dato público oficial.
- **IA / OpenRouter:** a OpenRouter solo se envía la **pregunta del usuario + el esquema de métricas**; **no** se envían datos personales. Revisar la política de tratamiento de OpenRouter; **minimizar/anonimizar logs** (RGPD).
- **Secretos** fuera del repo (ya en `.gitignore`). HTTPS en todo.

## Coste total estimado (orden de magnitud)
Web + pipeline ≈ **0 €** (free tier). API ≈ **pocos €/mes**. Dominio ≈ **20 €/año**. **OpenRouter = pago por uso** según volumen de consultas IA → recomendable **fijar un límite de gasto** desde el primer día.
