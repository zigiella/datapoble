# «Pregunta-li» (`/preguntale`) — la cara pública de la IA traçable

**Fecha:** 2026-06-07
**Autora:** Mirador
**Para:** Talaia (review + merge), Brúixola (contracte `/ask` consumit; deps deploy), Bea (vot narratiu)
**Tema:** `packages/web` — neix la pàgina **«Pregunta-li»** (`/preguntale` · `/es/preguntale`): text en llenguatge natural → resposta amb **procedència** (la query SQL exacta) i **refusos honestos**. Crida client-side a l'API de Brúixola, configurable per entorn.
**Status:** avance / handoff (front llest; espera l'API en viu)
**Branca:** `feat/mirador-pregunta-li`

## Contexto
Fins ara el web pintava marts precalculats. «Pregunta-li» és un **canvi de pilar**: la IA EN VIU. La gràcia del projecte és que **cap resposta arriba sense origen** i que el **«no» honest (refús) és una feature**. Com que el web és estàtic (`adapter-static`, sense servidor), la crida a `/ask` és **client-side** (fetch des del navegador) a una URL pública configurable. El build i el prerender han de funcionar **sense API viva**. **Cap canvi a `data/`, `semantic/`, `tools/`, `packages/{signals,ingestion,transform,ai}`, `ci.yml` ni `.gitignore`.** Tot dins `packages/web` (+ `messages/`).

## Què he fet

### 1. Client de l'API (`src/lib/ask/api.ts`) — el contracte, tipat
Frontera única entre el web i el servei. Tipa **EXACTAMENT** el contracte de Brúixola (no inventat): `AskResponse{ kind, text, backend, data, provenance{metric,…,query,…,is_fixture}, refusal_reason, metric_key }`, amb `RefusalReason` com a unió tancada dels 7 motius.
- `ask(question, locale, signal)` → `AskOutcome` **normalitzat**: mai llança per condicions esperades. Tradueix a estats: `ok` (answer|refusal del cos), `rate_limited` (HTTP **429**, llegint `Retry-After`), `unreachable` (fetch fallit: DNS/CORS/offline/Render dormint, o JSON dolent, o qualsevol HTTP no contemplat). Suporta `AbortController` (cancel·la la petició anterior si l'usuari torna a preguntar).
- **`PUBLIC_API_BASE`** via **`$env/dynamic/public`** (no `static`): una variable absent **no trenca el build**. Default `http://localhost:8000` només en `import.meta.env.DEV`; en estàtic pur queda buida → `unreachable` → avís amable. Es normalitza la barra final.

### 2. Pàgina (`routes/preguntale/{+page.ts,+page.svelte}`)
Reescriu el stub. Chrome del design-system (hero `.ap-hero` + `ContourField`, `.ds-main`/`.ds-sec`, `.prov`, `.srcline`, `.btn`, `.tbl`, tokens `--dp-*`), com glossari/metodologia.
- **Input** + botó «Pregunta» (label associat, `aria-describedby` al hint). **4 xips d'exemple**: si el dataset (= contracte, equivalent al `/metrics` de l'API) carrega, **2 surten de les etiquetes reals d'indicador** (`Població`, `Gap pernocta (%)`, localitzades) + 2 canònics (IETR, població). Si el dataset falta, 4 canònics de reserva. Mai sense exemples.
- **Estats** (màquina d'estats `View`): `idle` (region oculta) · `loading` (spinner + aria-busy) · `answer` · `refusal` · `rate_limited` · `unreachable`. La region de resultat és **`aria-live="polite"`** (lectors de pantalla anuncien la resposta).
- **Resposta:** `text` prominent + etiqueta de **backend** (offline / OpenRouter). Si `is_fixture` → **badge «dada de prova»** + nota explícita (honestedat).
- **PROCEDÈNCIA (el cor):** targeta amb vora esquerra **porpra** (`--dp-prov-derived` = inferència) i badge `prov--derived`. Graella amb Indicador · Font (+`source_key`) · Data · Llicència · Fórmula. I, prominent, la **CONSULTA SQL EXACTA en `<pre>` mono** amb salts de línia preservats — *la signatura de confiança* — amb hint i `Paràmetres` (JSON). `note` sota divisòria. **Cap resposta sense aquest bloc** (si `provenance` és null no es pinta, però la resta del producte garanteix origen).
- **Taula opcional** de `data` (`<details>` plegable, `.tbl` del DS, capada a 8 files amb «… i N més»).
- **Refús com a FEATURE:** badge `prov--negative` «Sense resposta (i és honest)» + lede + **missatge amable per `refusal_reason`** (out_of_catalog → «Això no és al catàleg…»; metric_planned → «definida però encara no calculada»; unknown_municipality; unsupported_question; guardrail_violation; budget_exceeded → «límit diari d'IA»; rate_limited, amb **compte enrere** si hi ha `Retry-After`). El `text` de l'API es mostra com a detall. **No s'amaga**: és part de la proposta.
- **API no disponible:** `unreachable` → bloc amable «El servei de preguntes encara no està actiu» + caveat «arriba molt aviat» + botó «Torna-ho a provar». **Mai una pantalla trencada.**

### 3. Navegació
- **Nav superior** (`+layout.svelte`): l'slot `nav_preguntale`, abans `.nav-inert`, ara és **enllaç actiu** `<a href={localizeHref('/preguntale')}>` amb el patró `isActive`/`class:on`/`aria-current`, just després de «Glossari». Queden 3 inerts (Índex, Excursionista, Política).
- **Peu**: `foot_about_ask` («Pregunta-li a les dades»), abans `<span>` inert, ara **enllaç real**.

### 4. i18n ca/es
~55 claus noves `pl_*` (hero, input, xips, estats, etiquetes de procedència, els 7 refusos + variant amb segons, unreachable, srcline) + 4 exemples canònics + 1 plantilla d'exemple del contracte. Tot el copi nou és **chrome i18n**; els **labels d'indicador dels xips vénen del contracte** (`def.label[locale]`), no d'i18n.

## Com es configura `PUBLIC_API_BASE`
```bash
# .env local o variable d'entorn del build a Cloudflare Pages (sense barra final)
PUBLIC_API_BASE="https://datapoble-api.onrender.com"
```
- Documentat al **README de `packages/web`** (secció nova). **No hi ha `.env.example`** perquè `.gitignore` ja ignora `.env*` (i NO el toco): la variable es defineix a l'entorn de build o en un `.env` local.
- Sense la variable: dev usa `localhost:8000`; estàtic pur → buida → la pàgina degrada amablement. El front es pot desplegar **abans** que l'API estigui viva.

## Verificació
- **`npm run check`** → **0 errors, 0 warnings** (998 fitxers; paraglide compila les claus noves). **`npm run build`** → static OK; `build/preguntale/index.html` i `build/es/preguntale/index.html` prerenderitzats. (El prerender entrega el shell + form; els estats de resposta són client-side, com toca.)
- **Preview** (`mirador-wt`, port 5174). Estats validats al navegador real (els d'API via **mock temporal de `fetch` només al context del navegador** — mai a codi font; tret abans de commitejar, tree net):
  - **idle**: form + label + placeholder + botó «Pregunta» + 4 xips (2 del contracte: «Població», «Gap pernocta (%)»), region oculta.
  - **answer**: text prominent; backend «motor determinista (offline)» i «model de llenguatge (OpenRouter)» segons `backend`; **badge «dada de prova»** + nota només si `is_fixture`; bloc procedència amb tots els camps i **la SQL multilínia en mono** + Paràmetres + Nota; taula `data` plegable.
  - **refusal** (`out_of_catalog`): «Sense resposta (i és honest)» + «Això no és al catàleg de dades de l'observatori…» + detall.
  - **429**: llegeix `Retry-After: 45` → «Massa preguntes seguides. Torna-ho a provar d'aquí 45 s.»
  - **unreachable** (submit real sense API a `localhost:8000`): «El servei de preguntes encara no està actiu» + botó reintentar.
  - **i18n**: `/es/preguntale` → `html lang=es`, H1 «Pregúntale a los datos.», xips i refusos en castellà (HTTP 200). **dark mode**: procedència i SQL llegibles, contrast AA.
  - **0 logs d'error** de consola.

## Notes / decisions per a Talaia (review)
- **Dependència de deploy (no-codi, fora jurisdicció Mirador):** la pàgina només respon de debò quan (a) es **rota `OPENROUTER_API_KEY`** i (b) **IT connecta l'API a Render** + es posa `PUBLIC_API_BASE` a l'entorn de Pages **i** es permet l'origen del web al **CORS** de FastAPI. Fins llavors, producció mostra l'estat amable «encara no actiu» (és el comportament desitjat, no un bug).
- **`provenance` pot ser `null`** al contracte: si arriba un answer sense procedència, es pinta el text sense el bloc. No és el cas normal (Brúixola ancora o rebutja), però el front no peta.
- **Estat actiu del nav a `/es/*`:** he detectat que `isActive` compara contra rutes canòniques, així que a `/es/...` **cap** pestanya queda marcada activa (Resum, Mapa, Glossari… i ara Pregunta-li, tots igual). **És pre-existent**, no ho introdueixo jo; a l'arrel ca funciona. Ho deixo com a **tasca a part** (no toco el layout compartit en aquest PR).
- **Xips del contracte:** trio `poblacio`, `gap_pernocta_pct`, `IETR`, `kg_hab_any` (coherents amb el brief). Si Brúixola prefereix uns exemples concrets que sàpiga respondre segur, és canviar `EXAMPLE_KEYS` a `+page.ts` (1 línia) o els canned a `messages/`.
- El bloc de procedència reutilitza la **vora porpra + badge `prov--derived`** del DS (mateixa signatura visual que mapa/metodologia/glossari per a la inferència): coherència de marca «cap número sense origen».
