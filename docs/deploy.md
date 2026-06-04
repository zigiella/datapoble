# Desplegament — riusdegent (arquitectura gestionada)

**Decisió (2026-06):** desplegar sobre **plataformes gestionades** —**Cloudflare Pages + Render + GitHub Actions**— i **no** sobre servidor propi (VPS). Validada amb IT i Bea. Confirma i concreta la recomanació del [brief de hosting](brief-hosting.md); el VPS compartit va ser un desviament i queda com a *fallback*.

## Per què gestionat > VPS

| Factor | Gestionat (Cloudflare/Render) | VPS compartit |
|---|---|---|
| **Pics de tràfic** (Marketing/premsa) | CDN global els absorbeix, gratis | una caixa de 4 GB no; risc de caiguda |
| **Ops** | ningú administra res | cal parchejar, Docker, Caddy, SSH, backups |
| **Acoblament** | cada capa aïllada | el nostre ús afecta l'experiment de les companyes (i a l'inrevés) |
| **Cost** | web gratis + API ~7 €/mes + IA per ús | cost fix + la mateixa IA per ús |
| **Residència de dades** | irrellevant: **dades obertes, sense PII** | a Espanya (no aporta res aquí) |

El cost que escala amb l'ús (la IA) és **el mateix** en tots dos casos —és OpenRouter— i el controlem nosaltres (vegeu sota).

## Arquitectura

| Capa | Plataforma | Detall |
|---|---|---|
| **Web** — SvelteKit estàtic: mapa MapLibre, indicadors, i18n ca/es | **Cloudflare Pages** | CDN global, *free tier*. Llegeix **dades estàtiques** (JSON/Parquet) → el gruix del tràfic **no toca l'API**. |
| **API** — FastAPI: text→SQL traçable via OpenRouter | **Render** | Gestionat, deploy auto des de GitHub, HTTPS, **regió EU**. *Free* → **~7 €/mes always-on** quan es publiciti (per no adormir-se). |
| **Refresc de dades** — re-baixar fonts, reconstruir marts/events, publicar | **GitHub Actions** (cron) | Versionat amb el repo, gratis. Publica artefactes estàtics + dispara rebuild de Pages. |
| **Domini** | **Dinahosting** | `riusdegent.cat` + `riusdegent.es` (301). Requisit cultural del `.cat` complert (projecte en català). |

## Control de cost de la IA (innegociable abans de publicitar l'API)

L'únic cost que creix amb l'ús són les trucades a OpenRouter. Disseny perquè escali a poc a poc:

1. **Determinista i cachejat PRIMER.** El router de Brúixola resol els *lookups* de mètrica **sense LLM**. L'LLM només per a text lliure real → la majoria de consultes **no costen res**.
2. **Caché** de preguntes normalitzades (per locale) → resposta + procedència reutilitzada.
3. **Rate-limit** per IP/usuari.
4. **Tope de despesa dur** a OpenRouter (sostre de gasto).
5. **Test de model/preu** amb els **evals de Brúixola** (mateixa infra): qualitat vs cost per model abans de fixar-ne un.

## Secrets

`OPENROUTER_API_KEY` → **Render + GitHub Actions**, mai al repo (ja a `.gitignore`). Per cablejar el deploy calen: **token API de Cloudflare**, **servei a Render**, **DNS a Dinahosting**. (Els aporta Bea/IT.)

## Compliment

Dades obertes de fonts oficials amb **atribució** documentada al repo; capa política **agregada (ecològica)** amb *caveats*; **sense PII** a la capa pública; **logs sense PII**. La clau no va mai al repo.

## Qui fa què

- **Mirador** — build estàtic + config de Cloudflare Pages; el front llegeix les dades estàtiques.
- **Brúixola** — API a Render (Dockerfile) + el control de cost (determinista-primer, caché, rate-limit, tope) + evals multi-model.
- **Sondeig** — publicar marts/events com a **artefactes estàtics** per al CDN.
- **Talaia** — workflow d'Actions (refresc + deploy) + aquest doc.

## Fallback

El VPS compartit (4 vCores/4 GB, Alma 9, Espanya) queda disponible **si un experiment futur necessita pgvector/RAG always-on** o còmput pesat persistent. Ara no cal.
