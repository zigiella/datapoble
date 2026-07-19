# D5 — la vista de govern a `municipi/[slug]` (`?vista=govern`)

**Agent:** Mirador (web) · **Data:** 2026-07-19 · **Tasca:** D5 de la cua (desbloquejada per D4 ✅ #268) · **PR:** (per obrir)

La mateixa fitxa pública, amb un commutador que posa els KPIs de la gorra §3 al capdamunt i el
**rang comarcal «k de n»** a cada mètrica mesurada — LLEGIT del mart de D4, mai calculat al front.

## Què s'ha fet

### 1. Commutador `?vista=govern` (C6 §1, §10.1)
Segmented control de dos enllaços (Veïnal | Govern), reflectit a la URL, compartible. S'ofereix
**només al Berguedà** (C6 §1.2). Reactiu a `page.url` al **client** (`$app/state`); el prerender
(adapter-static) surt sempre en veïnal i el client hi aplica el commutador en hidratar —SvelteKit
prohibeix `url.searchParams` en prerender, així que va darrere de la guarda `browser`. **Paritat
verificada:** la mateixa URL amb i sense el paràmetre mostra les MATEIXES xifres (el tauler reusa
`row.values`); només canvia l'ordenació i l'èmfasi.

### 2. Tauler de govern: 11 dels 12 «caps» de la gorra §3, amb rang comarcal
Els KPIs en **ordre fix** (C6 §7, font única `src/lib/govern/kpis.js` compartida amb el test).
Rang «k de n» **llegit del mart** via `data.govern` (D4) — el codi de D5 no conté cap funció de
rang ni de percentil (C6 §4, grep-comprovable: l'únic `.sort()` és el selector de noms de municipi).
Byte-match amb la gorra §2 a la Pobla: envelliment **6/31**, padró **8/31**, %no-principal **10/31**,
renda **19/31**, residus **24/31** (+ rtc 21/31, kwh 27/31). Empat i denominador honestos (C6 §3.2–3.3).

**Els 12 slots, honestament:** 10 KPIs mesurats + ETCA es renderitzen; **radar (slot 11) OMÈS** (porta
del §4 no superada, C6 §5 — cap string del radar); **licitacions (slot 12)** segueix com a secció
aparcada (el KPI mesurable del bloc D és residus, que sí que hi és); **atur (slot 8)** encara no està
servit al web (sèrie mensual de `mart_pols_mensual`) → targeta honesta «pendent» amb la seva font.
Total: **11 targetes**, dins del marge de C6 §2 («mínim 10 si una font falla»).

### 3. Regla de ferro de Bea (C6 §8.1): cada targeta amb font O fórmula
Res codificat a la UI: font, data i fórmula surten del contracte (`metrics[key]`). Regla: fórmula
≠ `directe` → **INFERIDA** (mostra la fórmula llegible + la font de les entrades); `directe`/absent →
**MESURADA** (mostra font · data). Verificat al DOM: **cap targeta sense línia de procedència**.

### 4. Doctrina del percentil (C6 §3)
Rang només sobre mesurades. La **pernocta estimada NO surt** (aparcada, gorra §1). «Nova població»
(% nacionalitat estrangera) es mostra **sense rang** —retingut fins al vot narratiu de Bea— amb el
marc de **renovació demogràfica** (gorra §3.3). ETCA i atur, sense rang (absoluta / interval mensual).

### 5. Neteja
`index_turisme` fora del tipus `MetricKey` (`contract/types.ts`) — ja deprecat i fora del JSON (#267/#268).
`/metodologia` NO cal tocar-la: el forat del 500 que D4 va marcar ja està tancat a main (la guarda
`if (!def) return ''` a `srcLine` + `index_turisme` fora del bloc C; verificat que les 4 claus del
bloc resolen). Serrell B3 del copy del refús («(Berguedà)» vs Catalunya-947) és de `packages/ai`
(fora del meu abast) → **handoff a Brúixola** (ja a la seva cua).

### 6. Test §10.7 + verificació
`scripts/verify-govern.mjs` (offline, importa el descriptor compartit): cada KPI té font o fórmula,
les 7 claus rankejables són al mart, paritat dataset↔mart a la Pobla, i18n ca/es complet,
`index_turisme` fora. **Verd.**

## Llistó (C6 §10)
- `npm run check` → **0 errors, 0 warnings**.
- `npm run build` → **verd, 0 errors [500]** (el bug de `searchParams` en prerender, destapat pel
  build, esmenat amb la guarda `browser`).
- **i18n ca/es** complet (23 claus `gov_*` × 2), AA: commutador amb `aria-current`, `role="group"`,
  `focus-visible`, contrast via tokens del design-system.
- **Verificació al DOM real** (build servit, no fetch en fred): la Pobla en mode govern mostra els
  11 KPIs, cada un amb la seva procedència; els 7 mesurats amb rang comarcal «k de n». [ca] i [es]
  verificats (VECINAL|GOBIERNO, «El panel de gobierno», rangs «6 de 31 · por valor en Berguedà»).
  Sense errors de consola / hidratació.
  - **Nota d'entorn:** els servidors dev/preview dels ports compartits (4174/5183) servien builds
    RANCIS de germans del worktree; la verificació fiable va ser servint el meu `build/` propi en un
    port net. El `build/` és l'autoritat i porta el commutador correcte.

## Copy nou — VOT NARRATIU DE BEA PENDENT
KPI «nova població» (% nacionalitat estrangera), marc de renovació demogràfica (gorra §3.3):
- **ca:** «Renovació demogràfica: l'entrada de gent nova que fa possible el relleu del poble.»
- **es:** «Renovación demográfica: la entrada de gente nueva que hace posible el relevo del pueblo.»
- Etiqueta «rang retingut»: «Rang comarcal retingut fins al vot narratiu de Bea.» / «Rango comarcal
  retenido hasta el voto narrativo de Bea.»

## Serralls / handoffs
- **➡️ Sondeig (dades):** vaig haver de crear el **pont** `tools/export_govern_web.py` +
  `data/web/govern.bergueda.json` perquè D4 va emetre el rang com a **parquet** (`mart_govern.parquet`)
  però cap JSON servible, i el front no pot calcular el rang (C6 §4). El generador és determinista
  des del parquet versionat i porta `--check`. **`tools/*` és jurisdicció de Sondeig** → reviseu la
  propietat i cablegeu-lo a la data-job com els altres `--check`. Abast actual = Berguedà (`SCOPE_COMARCA`);
  per multi-comarca, poseu-lo a `None` i amplieu la porta de la vista.
- **➡️ Talaia:** el commutador el veu tothom però la vista només s'ofereix al Berguedà (C6 §1.2). Si es
  vol multi-municipi (Gombrèn/Ripollès, gorra §5), cal (a) exportar el mart sencer i (b) obrir la porta
  `isBergueda` a qualsevol muni amb dada — ho deixo escrit, no ho faig (costat conservador).
- **Atur al tauler:** quan hi hagi export web de `mart_pols_mensual`, la targeta d'atur passa de
  «pendent» a valor mensual amb la doctrina «<5» (interval [1,4]).
