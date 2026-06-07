# CORS a l'API: que el front (Mirador) la pugui cridar des del navegador

**Fecha:** 2026-06-07
**Autora:** Brúixola
**Para:** Talaia (review/merge)
**Tema:** afegir CORS a `api.py` perquè el front públic «Pregunta-li» (Mirador, `adapter-static`) pugui cridar `/ask`,`/metrics`,`/health` cross-origin sense que el navegador les bloquegi.
**Status:** avance / handoff

## Contexto
Mirador és un build **estàtic** (`adapter-static`) servit des d'un origen **diferent** del de l'API (Render): `https://riusdegent.cat` i Cloudflare Pages (`*.pages.dev`). Les crides a l'API surten **del navegador**, així que són cross-origin. Fins ara `api.py` **no tenia CORS** → el navegador bloquejaria les respostes (no hi ha capçalera `Access-Control-Allow-Origin`). Calia afegir-lo, i res més de funcional.

## Qué hicimos / decidimos
Tot a `packages/ai/src/datapoble_ai/api.py` (i README + un test nou). No vaig tocar cap altra peça de l'API.

- **Middleware CORS** afegit a l'`app` mòdul-level: `app.add_middleware(CORSMiddleware, **cors_config_from_env())`. Es llegeix l'entorn **un cop a l'arrencada**, igual que `CostControl.from_env`.
- **Orígens per defecte (explícits, MAI `["*"]`):** `https://riusdegent.cat`, `https://riusdegent.pages.dev`, i dev local `http://localhost:5173` (Vite dev), `http://localhost:4173` (Vite preview), `http://127.0.0.1:5173`. Constant `DEFAULT_CORS_ORIGINS`.
- **Configurable per env** amb un helper net `cors_config_from_env(env=None)`:
  - `AI_CORS_ORIGINS` — llista separada per comes; si es fixa (no buida) **substitueix** els defaults (trim + descarta buits); si no, defaults.
  - `AI_CORS_ORIGIN_REGEX` — regex per a orígens dinàmics. Default `r"https://.*\.pages\.dev"` perquè les **preview de Cloudflare Pages** (`https://<hash>.riusdegent.pages.dev`) funcionin de sèrie; `""` el desactiva.
- **Mètodes** `GET,POST,OPTIONS`; **headers** `Content-Type`, `X-Datapoble-User` (el hint d'identitat que `_client_identity` ja llegeix per al rate-limit); **`allow_credentials=False`** (no fem servir cookies — és el que fa segura la allowlist d'orígens explícits).
- **Docs:** docstring del mòdul ampliat + README secció Render: nova subsecció *CORS*, dues files a la taula d'env vars, i la línia a «On Render» («posa `AI_CORS_ORIGINS` amb els dominis del web»).
- **Test offline** nou `tests/test_cors.py` (11 casos), `TestClient`:
  - origen permès (GET i preflight `OPTIONS`) rep `access-control-allow-origin` correcte i `POST` als mètodes permesos;
  - origen **no permès** NO rep la capçalera (el navegador bloquejaria);
  - `allow-credentials` mai surt;
  - preview `*.pages.dev` permès pel regex per defecte;
  - parsing del helper (defaults, override, blanc→default, regex buit→desactivat) i un app efímer end-to-end provant que `AI_CORS_ORIGINS` substitueix els defaults.

## Por qué
El front és estàtic i cross-origin: sense CORS la API és inaccessible des del navegador, per molt que respongui bé amb `curl`. Defaults **explícits i no `*`** perquè un deploy sense configurar ja serveixi el front real (i les preview) i **res més** — coherent amb la disciplina "fallar segur" de la resta de `costcontrol`. El regex de Pages és necessari perquè cada preview deploy té un host únic (impossible enumerar-los). `allow_credentials=False` perquè no hi ha cookies i així la allowlist d'orígens té sentit (CORS no permet `*` amb credencials, i tampoc el volem).

## Disciplina respetada
- **Gate `ai-evals` intacto:** offline/determinista/sense xarxa/sense key. Suite **96 passed** (eren 85, +11 de CORS), `ruff check src evals tests` net (mateixos passos que CI, Python 3.11).
- Contracte text→SQL i endpoints existents **sense canvis funcionals** (només s'afegeix middleware).
- **No** vaig tocar `packages/web`, `data/`, `semantic/metrics.yml`, altres packages, `ci.yml` ni `.gitignore`. Només `api.py`, `README.md` i el test nou.
- **Cap secret al codi** (la key és runtime). Identity-inline, sense co-autor IA, rama + PR, mai a main.

## Pendiente
- [ ] A **Render**: fixar `AI_CORS_ORIGINS` amb els dominis reals del web quan estiguin tancats (p.ex. `https://riusdegent.cat,https://riusdegent.pages.dev`). Sense fixar-lo, els defaults ja cobreixen el web i les preview.
- [ ] Si el domini final del front canvia (o s'afegeix un domini propi de Pages), actualitzar `AI_CORS_ORIGINS` (env, no codi).

## Enlaces
- `packages/ai/src/datapoble_ai/api.py` (constants `DEFAULT_CORS_*`, helper `cors_config_from_env`, `add_middleware`)
- `packages/ai/tests/test_cors.py`
- `packages/ai/README.md` (secció "Desplegament a Render + control de cost" → subsecció *CORS*)
