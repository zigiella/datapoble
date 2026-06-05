# Mapa i resum amb dades REALS (31 municipis) — swap del mock pel JSON de Sondeig

**Fecha:** 2026-06-05
**Autora:** Mirador
**Para:** Talaia (review + merge), Sondeig (font del JSON)
**Tema:** `packages/web` consumeix `data/web/municipis.bergueda.json` (els 31 municipis del Berguedà amb dades reals, forma `MunicipisDataset`) en lloc del mock de 2 municipis. El mapa coroplètic i el resum passen a dades reals; la llegenda passa a **5 classes plenes**.
**Status:** avance / handoff

## Contexto
Sondeig (PR #17, bitàcora `2026-06-05_electric-webdata_sondeig.md`) va publicar
`data/web/municipis.bergueda.json` amb la forma **exacta** `MunicipisDataset`
(`packages/web/src/lib/contract/types.ts`): 31 municipis, 19 mètriques, KPIs
comarcals calculats de debò. El web (mapa F2 de la PR #15 + resum) encara arrencava
contra `src/lib/mock/municipis.ts` (2 municipis: Castellar i Berga, amb derivats
il·lustratius). El handoff de Sondeig demanava explícitament: *"Mirador: substituir el
loader del mock per la càrrega de `data/web/municipis.bergueda.json` (mateixa forma;
no cal tocar tipus ni UI)."* Aquesta entrada ho fa.

## Qué hicimos / decidimos

**1. Com agafa el build el JSON (és FORA de `packages/web`).**
- Pas de **prebuild** cross-platform: `packages/web/scripts/copy-data.mjs` (Node, sense
  `cp`/`copy`) copia `data/web/municipis.bergueda.json` → `packages/web/static/data/`.
  Enganxat a npm via `prebuild`, `predev` i `precheck` (+ script `copy-data`).
- **Per què aquest camí i no un import:** el site és 100% prerenderitzat
  (`adapter-static`, `prerender = true`). El `fetch('/data/…')` del `load` corre **en
  build**; servir-ho des de `static/` és idèntic a com ja es serveix la geometria
  (`static/geo/…`) i funciona igual en prerender i al client, sense acoblar el bundle a
  una ruta relativa fora del package. Mateix patró mental que `build-bergueda-geojson.mjs`.
- **Frontera honesta:** el JSON és la FONT (de Sondeig). El copio, **no el modifico**.
  La còpia a `static/data/` és un artefacte de build → afegida al `.gitignore` **del
  package** (`packages/web/.gitignore`, NO el de l'arrel). Regenerable amb `npm run copy-data`.
- **CI verd garantit:** `data/web/municipis.bergueda.json` està **versionat** (PR #17) i
  el job `web build + check` fa `actions/checkout@v4` (repo sencer) → la font hi és, tres
  nivells amunt de `packages/web`. El `REPO_ROOT` de l'script resol `../../..`. Hi ha un
  *fallback no-fatal* (si la font no existeix, avisa i `exit 0`) per a clons sparse.

**2. Loader real en lloc del mock.**
- Nou `src/lib/data/dataset.ts`: `loadMunicipisDataset(fetch)` fa `fetch('/data/municipis.bergueda.json')`
  i el tipa com `MunicipisDataset`. Reexporta `FEATURED_INE5` (Castellar 08052 ↔ Berga
  08022) i `getMunicipi()`, que el mock proveïa.
- `routes/mapa/+page.ts` i `routes/resum/+page.ts`: substituït `getMunicipisDataset()`
  (síncron, mock) per `await loadMunicipisDataset(fetch)`. La forma i la UI **no canvien**.
- **Mock eliminat** (`git rm src/lib/mock/municipis.ts`): ja no l'importa ningú i els seus
  derivats il·lustratius contradiuen el principi "cap xifra sense procedència". Comentari
  de `contract/types.ts` actualitzat per apuntar al loader real.

**3. Join `ine5` verificat.** Els 31 codis del dataset quadren **1:1** amb
`static/geo/bergueda-municipis.geojson` (0 orfes a banda i banda). Els 4 indicadors del
mapa tenen cobertura **31/31** no nul·la → la llegenda omple les 5 classes de debò.

**4. i18n ca/es actualitzada (text que va quedar fals amb dades reals).**
- `map_data_caveat` i `footer_data_note`: deien *"Dades de demostració (mock)… Pendent de
  connectar al mart real"* → ara *"Dades reals dels 31 municipis (marts de datapoble)…"*.
- `resum_compare_hint`: deia *"Berga (~17.160 hab.)"* → **17.539** (població real del dataset).

## Verificación (headless Chromium)
- `npm ci` → OK. `npm run check` → **0 errors, 0 warnings** (764 fitxers).
  `npm run build` → prerender net (cap warning de 404), `build/data/municipis.bergueda.json`
  byte-idèntic a la font, 31 municipis.
- Preview (`vite preview`) en Chromium:
  - Mapa `/mapa/`: canvas viu, **31 municipis pintats** amb rampa de 5 classes.
  - Llegenda IETR: *"Cuantils · 5 classes"* amb rangs reals `0,3–21,06 / 21,06–31,14 /
    31,14–44,14 / 44,14–56,15 / 56,15–89,45` (= min/max reals del dataset, no els 2 del mock).
  - Selector → `kg_hab_any`: *"Jenks · 5 classes"*, rangs `323,51 … 1.132,47`, font
    *"Agència de Residus de Catalunya (ARC) · Data: 2024"*. Re-pinta correctament.
  - Resum `/resum/`: KPIs comarcals reals (41.523 hab., 593 establiments, 33,8% hab. no
    principal, 452,4 kg/hab/any) amb procedència. Caveat sense "mock". Sense errors de consola.
- **Nota de routing (no és bug):** en `vite preview` la ruta canònica ca és `/mapa/`
  (no `/ca/mapa/`); el prefix `/ca/` el reescriu Paraglide en runtime via hooks, que el
  preview estàtic no executa. A Cloudflare Pages el comportament esperat no canvia.

## Decisiones para Talaia (revisión)
1. **Camí del JSON = prebuild copy** (no import ni symlink): el recomano com a definitiu;
   és cross-platform, prerender-safe i no toca `data/` (jurisdicció Sondeig). Si en el
   futur hi ha API en runtime, només canvia el cos de `loadMunicipisDataset`.
2. **Còpia gitignorada al package**: `static/data/` no es versiona (és artefacte). Si
   prefereixes versionar-la per a deploys sense pas de build, és un canvi d'una línia.
3. **Mock esborrat**: decisió meva per coherència ("cap xifra sense procedència"). Si el
   volies com a fixture offline, es pot recuperar de l'historial (PR #15).
4. **`pct_icaen_EFG` = null als 31** (buit honest de Sondeig, falta el connector de
   certificats ICAEN): el mapa no l'ofereix com a indicador i les fitxes el mostren "n. d.".
   Quan arribi, només cal afegir-lo a `MAP_INDICATORS` si es vol al coroplètic.

## Pendiente
- [ ] **Talaia:** validar el pas de prebuild i mergear.
- [ ] (futur) tooltips/fitxes per a `index_envelliment` i `pct_extrema_dreta`, que ara
      ja porten dades reals al dataset però no estan a les llistes editorials de pantalla.
- [ ] vitest + Playwright (a11y) del mapa — segueix pendent d'un PR posterior (com a F2).

## Enlaces
- `packages/web/scripts/copy-data.mjs` (prebuild) · `package.json` (`prebuild`/`predev`/`precheck`)
- `packages/web/src/lib/data/dataset.ts` (loader real) · `routes/mapa/+page.ts` · `routes/resum/+page.ts`
- `packages/web/messages/{ca,es}.json` (caveats + població real)
- `packages/web/.gitignore` (`/static/data/`)
- Font: `data/web/municipis.bergueda.json` (Sondeig, PR #17) · `bitacora/2026-06-05_electric-webdata_sondeig.md`
