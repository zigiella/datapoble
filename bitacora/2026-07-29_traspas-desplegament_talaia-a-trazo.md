# Traspàs de desplegament · Talaia → Trazo (2026-07-29)

**Commit a desplegar: `822ed83`** (cap de `main`).
Res d'això s'ha desplegat encara: les GitHub Actions no funcionen fins el dia 1, així que **fusionat
≠ online**. Tot el que hi ha aquí està verificat **en local** (no per CI): tipus, guardes, build de
producció i comprovació al navegador.

---

## Superfície 1 · WEB (Cloudflare Pages, projecte `riusdegent`)

### Què hi ha de nou
- Dashboard municipal per als **947 municipis** de Catalunya (abans 31), amb rang comparatiu **per
  comarca de cada municipi**.
- Redisseny del tauler (v3): capçalera padró+ETCA, 4 grups nous, barres apilades d'edats i origen.
- Glossari (26 → 35 indicadors) i Metodologia (38 fitxes) al dia.
- Lectures P1/P2 ocultes i preguntes suggerides sense enllaç.
- Data de càrrega en format DD-MM-YYYY.

### Com desplegar-ho
Hi ha workflow (`.github/workflows/deploy-web.yml`) però està **dorment**: li falten dos secrets.
Dues vies, tria la que et convingui:

**(a) Activar el workflow** — afegir a Settings → Secrets and variables → Actions:
- `CLOUDFLARE_API_TOKEN` (permís *Cloudflare Pages — Edit*)
- `CLOUDFLARE_ACCOUNT_ID`
…i llançar-lo per `workflow_dispatch` **quan les Actions tornin (dia 1)**.

**(b) Desplegar a mà ara** (no depèn de les Actions):
```
npm --prefix packages/web ci
npm --prefix packages/web run build
npx wrangler pages deploy packages/web/build --project-name=riusdegent --branch=main
```

### Xifres del build (mesurades, no estimades)
| | |
|---|---|
| Fitxers | **5.931** (sostre de Pages: 20.000 ✔) |
| Fitxer més gros | **1,8 MB** (límit per fitxer: 25 MiB ✔) |
| Pàgines HTML | 3.013 |
| Pes total | **2,3 GB** |

⚠️ **2,3 GB és un build gran.** Cap límit de Pages es traspassa, però la pujada trigarà força més
del que estàs acostumada. Si el deploy peta o es penja, avisa'ns abans de retocar res: la mida ve
de prerenderitzar 947 municipis × 3 locales, i tenim maneres de reduir-la (menys prerender, més
càrrega sota demanda) — és decisió d'arquitectura nostra, no un paràmetre teu.

### Variable opcional
- `PUBLIC_API_BASE` (Settings → Variables) = URL pública de l'API de Render. **Sense valor el web
  no es trenca**: el «Pregunta-li» surt en estat *standby*. Amb valor, el següent deploy l'enllaça.

### 🔴 NO TOCAR
`packages/web/static/_headers` porta `X-Robots-Tag: noindex, nofollow`. **S'ha de quedar.** El
llançament públic és decisió de Bea i encara no ha arribat. No treguis el bloc ni el robots.txt.

---

## Superfície 2 · API d'IA (Render, servei `riusdegent-api`)

### Què hi ha de nou — i per què importa
S'ha **revocat del tot el mecanisme de vot polític**: el xat ja no pot respondre preguntes
d'orientació de vot per cap via, i s'ha eliminat la clau de runtime que abans les obria.

### ⚠️ Dues coses per verificar (no ho sé des d'aquí, ho has de mirar tu)
1. **`render.yaml` té `autoDeploy: true`.** Els deploys de Render **no depenen de les GitHub
   Actions**, així que aquest canvi **pot haver-se desplegat sol** en fer push a `main`.
   → Comprova al Dashboard que el darrer deploy inclou `822ed83`. Si no, llança'l a mà.
2. **Si a l'entorn del servei hi ha la variable `AI_POLITICS_UNLOCK`, esborra-la.** Ara ja és codi
   mort (no obre res), però una variable de desbloqueig que sobreviu al seu mecanisme és exactament
   el que no volem trobar-nos dins de sis mesos. **Aquesta és l'única acció de seguretat pendent.**

### NO TOCAR
`OPENROUTER_API_KEY` es queda **només** al Dashboard de Render, mai al repo. Els topalls de despesa
(`AI_DAILY_USD`, `AI_MONTHLY_USD`) tampoc s'han de pujar sense dir-ho.

---

## Com saber que ha anat bé (verificació post-deploy)

**Web** — obre tres fitxes i mira que:
- `/ca/municipi/barcelona` → surt el dashboard, població 1.713.247, i el rang diu **«de 5»**
  (municipis del Barcelonès), mai «de 31» ni «de 947».
- `/ca/municipi/sant-jaume-de-frontanya` → hi ha un avís de municipi petit a les targetes de
  residus, elèctric, vidre, turisme i envelliment.
- `/ca/glossari` → capçalera **«35 indicadors»**.
- Qualsevol fitxa: **no** hi ha d'aparèixer cap secció «Els números clau» (s'ha eliminat).

**API** — `GET /health` respon, i una pregunta d'orientació de vot rep el refús neutre
(«no responem preguntes sobre orientació de vot»), sense anomenar cap indicador.

Si alguna d'aquestes falla, **no ho arreglis tu**: escriu-ho i ho mirem. Són comprovacions de
doctrina, no de configuració.

---

## Si alguna cosa et bloqueja
Deixa-ho escrit a la bitàcola (o obre issue) — no en silenci. El repo és la veritat; el que no hi
és, no ha passat.
