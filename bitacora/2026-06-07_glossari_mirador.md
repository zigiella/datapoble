# Glossari públic (`/glossari`) + restauració al Bloc C de la metodologia

**Fecha:** 2026-06-07
**Autora:** Mirador
**Para:** Talaia (review + merge), Sondeig (handoff `definicio` al contracte/export), Llegenda (consum del design-system)
**Tema:** `packages/web` — neix el **glossari públic** (`/glossari` · `/es/glossari`), generat DES DEL CONTRACTE, i la **restauració (OSM)** entra a «Les 3 capes» de la metodologia com a 2n proxy d'hostaleria.
**Status:** avance / handoff
**Branca:** `feat/mirador-glossari`

## Contexto
La metodologia és **l'assaig** (com funciona l'observatori, el model de 3 capes, què es mesura vs què s'infereix, l'honestedat). Faltava **el diccionari**: una pàgina de referència escanejable amb **cada terme del contracte definit**, per dimensió. Aquest PR la crea. **Cap canvi a `data/`, `semantic/`, `tools/`, `packages/{signals,ingestion,transform,ai}` ni als workflows.** Tot dins `packages/web` (i `messages/`).

## Què he fet

### 1. Pàgina de glossari (`/glossari`, ca/es) — el contracte, llegible
Nova ruta `routes/glossari/{+page.ts,+page.svelte}`. El `+page.ts` replica EXACTAMENT el patró de la metodologia: `load` → `loadMunicipisDataset(fetch)` → `data.dataset`. El castellà `/es/glossari` surt sol pel reroute/localize existent (verificat HTTP 200).
- **Agrupació dinàmica per `dimension`** (DIM_ORDER: demografia · habitatge · turisme · pressió · índexs · energia · política). **Cap llista de mètriques codificada**: recorro `Object.values(dataset.metrics)` i agrupo; el que hi hagi al dataset és el que es pinta. Resultat: **33 indicadors, 7 dimensions**.
- Cada entrada: **terme** (`pick(def.label)`) · **definició** · **línia unitat·tipus** (unitat del contracte + vocabulari humà del `format`, presentació com els noms de mètode del mapa) · **font · data** (`def.source · def.date`) · **badge de procedència** (`provenanceOf`, mateixa regla que metodologia/mapa: 15 oficial / 18 inferència) · **caveat** (`note`) quan escau. Les `status:'planned'` (2: `index_envelliment`, `pct_extrema_dreta`) van **marcades** com fa la metodologia.
- **Chrome del design-system**: hero + `ContourField`, `.ds-main`/`.ds-sec`/`.ds-sec__hd .ref`, `.prov` + punts, `.srcline`, tokens `--dp-*`. Es llegeix net amb 33 mètriques (graella `auto-fill` minmax 320px).
- **Intro curta** (`glo_intro_note`) que marca la **distinció** explícita: «si busques COM funciona → metodologia; aquí tens el diccionari». No es duplica cap WHAT/HOW de la metodologia.

### 2. Navegació
- **Nav superior** (`+layout.svelte`): «Glossari» **just després de «Metodologia»**, enllaç actiu amb el mateix patró `isActive`/`localizeHref`/`class:on`. Verificat: `class="on"` a `/glossari`.
- **Peu**: l'enllaç «Glossari» (`foot_link_glossary`), abans `<span>` inert, ara és `<a href={localizeHref('/glossari')}>` real.

### 3. Restauració al Bloc C de la metodologia
`metodologia/+page.svelte`: afegits `restauracio_per_1000hab` i `restauracio_estab` a WHAT/HOW i a les `keys` del Bloc C, **just després de `index_turisme`** (el seu germà L3). Claus i18n noves `met_restauracio_what`/`met_restauracio_how` (ca+es):
- **WHAT**: locals de restauració (restaurants, bars, cafeteries, menjars ràpids, pubs…) per municipi — **2n proxy d'hostaleria**, complement del vidre.
- **HOW**: recompte de POIs d'**OpenStreetMap** (`amenity=restaurant/bar/cafe/fast_food/pub…`) assignats per geometria real; densitat = locals/1000 hab. **Valida L3**: correlaciona amb el vidre/hab (**Spearman ≈ 0,54**) → 2 senyals INDEPENDENTS confirmen la pressió turística; límit honest: **OSM = mínim observat, no cens** (infra-mapeja el rural; recompte 0 = buit de mapejat, no absència real).
- La densitat surt com a **inferència 🟪** (source «datapoble (calculat)»); el recompte com a **oficial 🟦** (source OSM). Coherent amb `provenanceOf`.

### 4. i18n ca/es
Nomes el **chrome** del glossari (títol, meta, eyebrow, h1, lede, intro-distinció, 7 etiquetes de dimensió, vocabulari de `format`, etiquetes de camp, `glo_count`, `glo_srcline`, `nav_glossari`) + les 2 claus de restauració. Els **labels i definicions de mètrica vénen del contracte**, no d'i18n.

## ⚠️ Handoff clau a Sondeig — `definicio` no arriba al dataset
El brief demanava la definició via el camp **`definicio`** del contracte. **`metrics.yml` SÍ que té `definicio` (ca/es) per a cada mètrica, però l'export `tools/export_web_municipis.py` NO l'emet** al JSON web (només label/unit/dimension/format/source/date/note/status). Per tant, ara mateix l'artefacte `data/web/municipis.bergueda.json` **no porta cap `definicio`**.

Decisió (dins la meva jurisdicció, respectant «NO toquis `data/`/`semantic/`/`tools/`»):
- El glossari **llegeix `def.definicio` si hi és** i, si no, **recau en `note`**. He afegit `definicio?: Localized` (opcional) a `MetricDef` (`contract/types.ts`, `packages/web`). Avui es pinten **3 definicions** (les úniques 3 mètriques amb `note`: IETR, % indep, % extrema dreta); la resta d'entrades surten amb terme + unitat·tipus + font + procedència (un stub de diccionari vàlid).
- **El dia que l'export emeti `definicio`, les 33 definicions canòniques apareixen soles, sense tocar aquesta pàgina.** És exactament la sincronització que demana el brief.

**Petició a Sondeig (1 línia al `build_metrics` de l'export):** emetre `definicio` (i, si es vol, `visibility`) des de `metrics.yml`, com ja fa amb `nota`→`note`:
```python
definicio = _localized(spec.get("definicio"))
if definicio:
    m["definicio"] = definicio
```
Vaig provar-ho localment (els marts del worktree regeneren l'artefacte byte-a-byte amb `--check`, i amb el canvi totes 33 portaven `definicio`), però **ho he revertit** per no creuar la frontera `data/`/`tools/`: és **decisió de Sondeig/Talaia**, no meva. Mentrestant el glossari ja és funcional i 100% contracte.

## Verificació
- **`npm run check`** → **0 errors, 0 warnings** (941 fitxers; paraglide compila les claus noves). **`npm run build`** → static OK, prerender complet; `build/glossari/index.html` i `build/es/glossari/index.html` existeixen.
- **Preview** (`mirador-wt`, port 5174, DOM determinista; screenshot no fiable amb el hero SVG, patró conegut → verifico per DOM/consola):
  - `/glossari` (ca): **33 term cards**, **7 seccions de dimensió** + intro + srcline, comptador «33 indicadors públics · 7 dimensions», **15 oficial / 18 inferència** (vores de procedència), 2 planned marcats, hero/lede/intro/srcline amb alçada real, **0 logs de consola**.
  - **Nav superior «Glossari» = actiu** a `/glossari`; **peu «Glossari» = enllaç real** a `/glossari`. `/es/glossari` → HTTP 200 (Glosario / Vivienda / Presión y carga).
  - `/metodologia` (ca): Bloc C ara amb **9 fitxes** incloses «Restauració / 1000 hab» i «Establiments de restauració» (després de «Pressió turística»), HOW amb **Spearman ≈ 0,54** + mètode OSM + «mínim observat». **0 logs de consola.**
- **Spearman verificat numèricament** sobre els 31 municipis del dataset: ρ = **0,544** (rest/1000 vs vidre/hab); excloent els 6 amb OSM=0 puja a 0,74 → reforça el caveat «OSM infra-mapeja el rural».

## Notes / decisions per a Talaia (review)
- **Filtre «public»**: el brief deia `visibility === 'public'`, però l'artefacte no porta `visibility` (l'export el col·lapsa a `status` public/planned). Renderitzo **tot el catàleg** marcant els 2 `planned`, que és el comportament de la metodologia i dona el diccionari més complet. Si vols ocultar els planned del glossari, és una línia al filtre.
- El glossari **no toca** la metodologia ni en duplica el WHAT/HOW: la línia unitat·tipus i la definició (note→definicio) són una vista de referència, no l'assaig.
- `definicio` a `MetricDef` queda **opcional** a propòsit (l'export encara no l'emet); no trenca tipus ni el `--check` de l'export.
