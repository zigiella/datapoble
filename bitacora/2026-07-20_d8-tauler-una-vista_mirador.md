# D8 — el tauler d'una sola vista (esmenes de Bea que no depenen de dada nova)

**Agent:** Mirador (web) · **Data:** 2026-07-20 · **Tasca:** D8 de la cua · **PR:** (per obrir)

Abast d'aquesta passada: les esmenes de `docs/ajuntaments/tauler-v2-esmenes-bea.md` que **no
necessiten dada nova** — E1, E2, E3, E9, E10 i la part de UI d'E8. Les que depenen de camps nous
(E4/E5/E6/E11/E12) les prepara Sondeig a D7; hi haurà una segona passada meva quan existeixin.

## Esmena per esmena

### E1 · Una sola vista, «Tauler de dades» — ✅ FET
Fora el commutador Veïnal|Govern (marcatge, i18n i CSS retirats). El que era «mode govern» —KPIs
amb rang comarcal, ordre fix, política editorial— **és ara la fitxa**, sense `?vista=govern`.

- **Paritat de dades:** deixa de ser un risc perquè ja no hi ha una segona vista amb què discrepar.
  Les xifres surten d'on sortien (`row.values` + rang llegit del mart).
- **Enllaços ja compartits:** `?vista=govern` **no trenca res** (la pàgina és la mateixa amb i sense
  el paràmetre) i, en hidratar, el paràmetre es **neteja de la URL** amb `replaceState` — no navega
  i no embruta l'historial. Verificat en viu: entrant a `…/la-pobla-de-lillet/?vista=govern` la URL
  final és `…/la-pobla-de-lillet/`.
- **Efecte lateral bo:** el tauler ja no depèn de `browser` (abans `isGovern` exigia hidratació), així
  que ara surt al **HTML prerenderitzat**, no només després d'hidratar.
- **Abast conservador:** el tauler es manté al Berguedà (`isBergueda`), que és on existeix
  `data.govern` (C6 §1.2) — igual que abans. La resta de Catalunya conserva la seva espina.

### E2 · Els indicadors de «vida», junts — ✅ FET
Bloc D reconvertit en el grup de vida: **Residus kg/hab/any + Elèctric domèstic kWh/hab + Vidre
kg/hab/any**, els tres seguits, cadascun amb la seva font (C6 §8.1). `kwh_hab` ha baixat del bloc B.
El **vidre surt sense rang** perquè el mart no el rankeja (no és a les 7): és la lectura honesta, no
un forat — el front no s'inventa cap rang (C6 §4).

### E3 · «Establiments turístics / 1.000 hab» — ⛔ NO TOCAT (jurisdicció de dades) → handoff
**Verificat: l'etiqueta ve del CONTRACTE, no de la UI.** A `semantic/metrics.yml`:

```
rtc_per_1000hab:
  label: {ca: Establiments / 1000 hab, es: Establecimientos / 1000 hab}
```

La targeta la pinta amb `pick(def.label, locale)`. Segons la consigna, si ve del contracte no la
canvio jo. **➡️ Handoff a Sondeig/Talaia** (sota).

### E9 · Rang comarcal al «% nacionalitat estrangera» — ⛔ BLOQUEJAT PER DADA → handoff
El vot de Bea **ja hi és** i el retard ja no és narratiu. Però el rang **no existeix al que serveix
el web**, i el front no se'l pot inventar (C6 §4 és frontera dura). Verificat:

- `data/web/govern.bergueda.json` conté **exactament 7 mètriques** a tots 31 municipis
  (`index_envelliment`, `poblacio`, `pct_noprincipal`, `rtc_per_1000hab`, `kwh_hab`,
  `renda_neta_persona`, `kg_hab_any`). `pct_nacionalitat_estrangera` **no hi és**.
- `tools/export_govern_web.py` → `RANK_METRICS` són aquestes mateixes 7.
- La mètrica viu a `mart_demografia`, **no a `mart_govern`** (que és qui rankeja).

Fet, doncs, el que sí que es pot fer sense mentir: la targeta **diu el motiu real** en comptes de
la frase antiga, que ja era falsa («retingut fins al vot narratiu de Bea» — el vot ja hi és):

> «Sense rang comarcal encara: aquesta mètrica no la rankeja el mart de govern, i aquí no la calculem.»

Quan Sondeig l'afegeixi al mart i a `RANK_METRICS`, la segona passada meva és treure `pendingRank`
del descriptor i afegir la clau a `GOVERN_RANK_KEYS`: el rang apareix sol.

### E10 · Fora la frase de «renovació demogràfica» — ✅ FET
Retirades les claus `gov_kpi_nova_frame` (ca+es) i, amb ella, `gov_bea_pending` (el distintiu «vot
de Bea pendent» que només acompanyava aquella frase), el marcatge i el CSS (`.gov-kpi__bea`,
`.gov-tag`). El KPI es queda amb el seu nom, el seu valor, la seva variació i la seva procedència,
**sense frase interpretativa**.

### E8 (part UI) · «Confiança mitjana» — ⛔ NO TOCAT (és dada generada) → handoff
**Verificat: no és una etiqueta de la UI.** «Confiança mitjana» és text **dins del veredicte generat**
per gen_fitxa, a `data/web/lectures.bergueda.json` (p. ex. la Pobla: «…i una pernoctació que només
afegeix càrrega moderada. Confiança mitjana.»), en ambdós idiomes («Confianza media»). La fitxa el
renderitza tal com ve. Segons la consigna, no el toco: **➡️ handoff a gen_fitxa (E7)**.

## Llistó

- `npm run check` → **0 errors, 0 warnings** (1222 fitxers).
- `npm run build` → **verd**.
- `node scripts/verify-govern.mjs` → **OK**: 12 KPIs (tots amb font O fórmula), 7 amb rang comarcal
  llegit del mart, paritat dataset↔mart a la Pobla, i18n ca/es complet **i sense claus òrfenes**.
  S'hi ha afegit un bloc nou (4b) que falla si una clau retirada torna a aparèixer als catàlegs.
- **i18n ca+es** sincronitzats: 5 claus retirades a totes dues, cap òrfena, cap clau només en un idioma.

### Verificació al DOM (build propi)

**Nota d'entorn (es repeteix la trampa de D5):** el port compartit **4174 servia el build RANC del
repo principal** (762.570 B) i no el meu (1.019.212 B) — la pàgina servida encara portava el
marcatge antic. La verificació bona és amb el meu `build/` en un **port net (4199)**, on els bytes
servits coincideixen exactament amb el meu artefacte.

A `/municipi/la-pobla-de-lillet/` (ca) i `/es/municipi/la-pobla-de-lillet/` (es):

- Títol del tauler **«Tauler de dades»** / «Panel de datos»; `.gov-switch` **absent**; «Veïnal» i
  «Govern» (i «Vecinal») **absents**.
- Grups en ordre: «Qui hi ha (i qui hi haurà)» · «Les cases» · «El pols i l'economia» ·
  **«El pols de la vida diària»**.
- Grup de vida amb els **tres** indicadors i la seva procedència:
  Residus 458,6 kg (rang 24 de 31) · Elèctric domèstic 1.375,1 kWh (rang 27 de 31) ·
  **Vidre 48,6 kg (sense rang, amb fórmula `vidre_tones * 1000 / poblacio` i font ARC)**.
- «% nacionalitat estrangera» 9,6 % · +5,6 pts · la línia de motiu real del rang · font Idescat.
- **12 targetes, 0 sense línia de procedència** (regla de ferro C6 §8.1 intacta).
- Frase «Renovació demogràfica» / «Renovación demográfica» **absent**; «vot de Bea pendent» **absent**.
- `?vista=govern` → URL final neta, sense el paràmetre. Sense errors de consola.
- Etiqueta d'establiments: segueix «Establiments / 1000 hab» — **correcte**, ve del contracte (E3).

## Copy nou — VOT NARRATIU DE BEA PENDENT

- **Títol del tauler** — ca: «Tauler de dades» · es: «Panel de datos».
- **Subtítol** — ca: «Els indicadors del poble, amb el seu rang dins la comarca quan el tenim. Cada
  xifra porta d'on surt: la font si és mesurada, la fórmula si és calculada.» · es: «Los indicadores
  del pueblo, con su rango dentro de la comarca cuando lo tenemos. Cada cifra lleva de dónde sale:
  la fuente si es medida, la fórmula si es calculada.»
- **Grup de vida** — ca: «El pols de la vida diària» · es: «El pulso de la vida diaria». (Bea el va
  descriure com «el pols de la vida diària del poble»; això n'és la versió curta d'etiqueta.)
- **Motiu del rang absent** — ca: «Sense rang comarcal encara: aquesta mètrica no la rankeja el mart
  de govern, i aquí no la calculem.» · es: «Sin rango comarcal todavía: esta métrica no la rankea el
  mart de gobierno, y aquí no la calculamos.»

## Handoffs

- **➡️ Sondeig/Talaia (contracte) · E3:** l'etiqueta de `rtc_per_1000hab` a `semantic/metrics.yml` és
  imprecisa. La mètrica és el **Registre de Turisme de Catalunya**, així que hauria de dir
  **«Establiments turístics / 1.000 hab»** (es: «Establecimientos turísticos / 1.000 hab»). No la
  toco perquè el `label` és jurisdicció de dades. En canviar-la, la fitxa l'agafa sola (la UI llegeix
  `def.label`); reviseu també si `/metodologia` i el xat en depenen.
- **➡️ Sondeig (dades) · E9:** perquè el «% nacionalitat estrangera» tingui rang cal que
  `mart_govern` el rankegi i que `RANK_METRICS` de `tools/export_govern_web.py` l'inclogui (avui la
  mètrica viu a `mart_demografia`). Fet això, avisa'm: la segona passada del front és de dues línies.
  **Mateix cas per a `vidre_hab`**, que ara surt sense rang al grup de vida nou.
- **➡️ gen_fitxa (E7/E8):** «Confiança mitjana» és text del **veredicte generat**, no una etiqueta de
  la UI. Bea diu que un usuari normal no sap què vol dir: o s'explica dins del text generat, o
  s'elimina del prompt. És a `data/web/lectures.bergueda.json` (ca i es), no al front.
- **Segona passada de Mirador (rere D7):** franges d'edat, tendència, frescor i atur (E4/E5/E6/E11/E12)
  quan els camps existeixin al web.
