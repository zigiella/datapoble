# D9 · treure a la superfície el que D7 ja serveix — Mirador (2026-07-20)

Capa de WEB de les esmenes **E4, E5, E6, E11, E12** de
`docs/ajuntaments/tauler-v2-esmenes-bea.md`. La dada la va deixar servida i verificada D7
(#276, Sondeig · bitàcola `2026-07-20_d7-dada-tauler-v2_sondeig.md`); aquí només es LLEGEIX.

**Resum en una línia:** l'atur ja no és una targeta que diu «pendent» —és un número, una sèrie
i **dues** comparacions que discrepen—; cada targeta diu de quan és la seva xifra i qui la
refresca (o que ningú); i on no hi ha sèrie, el tauler pinta el **motiu escrit pel mart**, no
una fletxa grisa.

---

## 1. Què s'ha pintat

| Esmena | Què surt ara a `/municipi/[slug]` |
|---|---|
| **E4** atur | Darrer mes (o **interval** si el SEPE l'emmascara) + el mes al qual correspon + les **dues** comparacions + **sparkline de 25 mesos**. Targeta a fila sencera perquè hi càpiga la sèrie. |
| **E6** tendència | Una línia per entrada de `tauler.tendencia[metric][]`: fletxa (només si el mart afirma direcció), magnitud, unitat i **sempre** els dos períodes. |
| **E5** frescor | Línia per targeta: cadència · darrera càrrega · **procés que la refresca o la seva absència**. Mai un peu de pàgina global. |
| **E12** franges | `pob_0_14`, `pob_15_64`, `pob_65_84`, `pob_85_mes` com a targetes del bloc «Qui hi ha (i qui hi haurà)», just darrere de la població de la qual són la partició. |
| **E11** motiu | Població i franges surten amb el motiu literal: «EMEX serveix només el darrer període…». L'origen SÍ té sèrie i es pinta: **↑ +5,61 punts · finestra · 2021 → 2025**. |

### Les quatre regles de pintura, i com estan cablades

1. **Cap fletxa sense període.** Els períodes surten de `periode_actual`/`periode_anterior` i
   es formaten amb `Intl` al locale actiu (`2026-06` → «juny del 2026» / «junio de 2026»).
   **Cap període està escrit a cap missatge d'i18n.** De fet aquest PR **retira**
   `gov_nova_delta_label` («variació 2021→»), que era exactament el pecat: el període dins el
   copy. La mateixa xifra (+5,61) ara ve de la tendència, amb el seu període a la dada.
2. **L'atur porta les DUES comparacions.** La Pobla, juny de 2026: **↑ +4 vs el mes anterior**
   i **↓ −3 vs el mateix mes de l'any anterior**, una sota l'altra. Triar-ne una és triar la
   narrativa; el verificador cau si algun dia només se'n pinta una (§4).
3. **`sense_serie` → el motiu, mai una fletxa.** Text literal del mart, amb l'etiqueta
   «Sense sèrie:» al davant. Ni guionet mut, ni 0, ni fletxa grisa.
4. **«<5» → interval, mai zero.** Capolat, juny de 2026: valor **«entre 1 i 4 persones»**;
   Δ contra el mateix mes de l'any anterior **«↑ entre +1 i +4»**; Δ contra el mes anterior
   **«· no es pot dir: entre −3 i +3»** (l'interval travessa el zero → cap direcció).
   A la sparkline, un mes emmascarat **no és un punt**: és una banda `[min,max]`, i la línia
   es **trenca** allà — no s'interpola damunt del que la font no publica.

### Serrell cosmètic resolt
`nomCanonic()` a `$lib/contract/slug.ts`: el nom arribava en dues formes segons la fila
(«Pobla de Lillet, la» dels marts vs «la Pobla de Lillet» de la geometria i del tauler). El
`<h1>`, el `<title>` i el selector ja mostren la forma corrent. Reutilitza la **mateixa** regla
d'article que `toSlug`, així que els slugs no es mouen ni un byte; el selector segueix
**ordenant** per la forma d'índex, que és per a què serveix (l'article no apila mig Berguedà
sota la «L»).

---

## 2. Què s'ha decidit NO pintar (i per què)

- **`pob_65_mes`.** És exactament `pob_65_84 + pob_85_mes`, que ja són al mateix bloc. Pintar-la
  seria comptar la mateixa gent dues vegades a la mateixa pantalla. Segueix al catàleg i és el
  numerador de l'índex d'envelliment, que sí que hi és **amb la seva fórmula**.
- **Cap rang per a `pct_nacionalitat_estrangera` ni per a `vidre_hab`.** `mart_govern` en rankeja
  7 i cap de les dues hi és. El front no rankeja (C6 §4 és frontera dura). La primera conserva la
  marca honesta `pendingRank` amb el motiu real; la segona surt sense rang, com D8 ja va decidir.
  *(Matís del brief: `vidre_hab` **no** porta `pendingRank` avui, i no s'hi ha posat — E9 de Bea
  demanava el rang per a l'estrangera, no per al vidre.)*
- **Cap tendència de «nascuts fora de Catalunya» ni de «nascuts a l'estranger».** Vegeu §3: no
  existeixen a `mart_tendencia`. Posar-hi la de **nacionalitat** sota aquest títol seria
  precisament la confusió que el contracte prohibeix a la seva pròpia nota.
- **Frescor a la targeta d'ETCA.** La presència oficial no ve del catàleg de mètriques sinó de
  `pernocta-catalunya.json`, que no porta bloc `frescor`. La targeta segueix declarant font i
  abast a la seva línia; no se li ha inventat cap cadència.

---

## 3. Premisses del brief que he trobat FALSES, i altres troballes

### Falses (verificades)

1. **`docs/equipo/mirador_role.md` NO EXISTEIX.** A `docs/equipo/` només hi ha `talaia_role.md`.
   M'he reconstruït des del repo (Charter §III): `.cambium/CHARTER.md` + `.cambium/REGLAS.md` +
   `CONTRIBUTING.md` §1, que és on viu de veritat el mapa de jurisdiccions (Mirador →
   `packages/web`). **Handoff a: Talaia** — o s'escriu el `role.md` de cada agent, o el Charter
   §III (reconstrucció-des-del-repo) no es pot complir tal com està escrit.
2. **`bitacora/next.md` NO té cap secció «🟡 COLA DE MIRADOR — SEGÜENT: D9».** La cua viva de
   Mirador segueix dient «D5 ✅ FUSIONAT (#271)». La tasca va arribar **pel latido, no pel repo**,
   que és l'antipatró que el Charter §IV nomena explícitament («si el latido lleva la tasca i el
   repo no, l'assignació encara no existeix»). No he parat per això —la feina era clara i
   verificable— però queda escrit, i **aquest PR escriu D9 a `next.md`**.

### Altres (afecten la dada, no la pintura)

3. **El `motiu` de `mart_tendencia` és NOMÉS EN CATALÀ.** El tauler el pinta literal, també a
   `/es/…` (marcat `lang="ca"` al marcatge, que és el mínim honest). No es tradueix al front:
   traduir dada a la UI és inventar-la. **➡️ Handoff a: Sondeig** — el `motiu` hauria de ser
   `{ca, es}` com ja ho són `label` i `definicio` al contracte.
4. **5 mètriques arriben amb `frescor.actualitzacio: null`**, i una d'elles —`rtc_per_1000hab`—
   **és una targeta del tauler**. No és un bug de l'export: `resolve_frescor()` fa exactament el
   que promet («mai inventa una cadència per a una derivada») i el contracte declara
   `datapoble.actualitzacio: derivada` + `proces_refresc: "hereta de l'origin_source"`. El que
   falta és l'`origin_source` al contracte. El tauler ho diu tal com és: **«cadència no
   declarada»**. **➡️ Handoff a: Sondeig / Talaia** (`semantic/metrics.yml`, fora de la meva
   jurisdicció): `rtc_per_1000hab` i `rtc_per_100hab_viv` → `origin_source: rtc`; `hab_per_hab`
   → `idescat_emex`. `IETR` i `IETR_rank` creuen fonts: el `null` **hi és honest**, no s'ha de
   tapar.
5. **`serveis_estab` i `restauracio_estab` (OSM) no són a `mart_tendencia` en absolut** — ni amb
   sèrie ni com a `sense_serie` amb motiu. Com que una absència muda es llegeix com un «no ha
   canviat», el front declara el seu propi punt cec: «Sense tendència declarada: aquesta mètrica
   encara no és al mart de tendències». **➡️ Handoff a: Sondeig** — o hi entren amb motiu escrit,
   com les altres 12, o es declara que no hi han d'entrar.
6. **E11 només es pot satisfer a MITGES, i el motiu és de fons.** Bea demana l'evolució de
   «nascuts fora de Catalunya» i «nascuts a l'estranger». A `mart_tendencia` hi ha
   `pct_nacionalitat_estrangera` i `poblacio_nacionalitat_estrangera` — que són **nacionalitat**,
   no **lloc de naixement**, i el mateix contracte avisa que confondre-les és el marc de
   l'«extranjería» (`pct_nacionalitat_estrangera.note`). `poblacio_nascuda_estranger` i
   `pct_nascuda_estranger` **no tenen cap fila** a `mart_tendencia`. **➡️ Handoff a: Sondeig.**
7. **`atur_registrat` no és al contracte semàntic** (viu a `mart_pols_mensual`, no a
   `mart_municipi`), així que la seva etiqueta i la seva font són **les dues úniques cadenes del
   tauler que no surten del contracte** (`gov_kpi_atur`, `gov_kpi_atur_src`). **➡️ Handoff a:
   Talaia / Sondeig** — amb `atur_registrat` al contracte, també aquesta targeta llegiria
   etiqueta i font d'on toca.

### Premisses del brief que SÍ s'han confirmat
Àncora de la Pobla (+4 vs maig, −3 vs juny de 2025) · el `<5` de Capolat com a interval i com a
`indeterminat` · les 5 claus noves absents de `MetricKey` i `frescor?` absent de `MetricDef` ·
les franges quadren (98 + 609 + 322 + 77 = 1.106) · `pct_nacionalitat_estrangera` no és a les 7
del mart de govern · el nom en dues formes. `_meta.atur.frescor` porta, a més dels quatre camps
del brief, un `date: "2026-06"`.

---

## 4. Llistó (què s'ha verificat, i què no)

- **`npm run check`: 1.243 fitxers, 0 errors, 0 warnings.** **`npm run build`: verd** (site
  prerenderitzat sencer, 947 × 2 fitxes).
- **`verify-govern.mjs` ampliat** — no només comprova el que ja comprovava (procedència de cada
  KPI, rang llegit del mart, paritat, i18n sense òrfenes): ara **guarda les regles de pintura
  sobre la dada que el front consumeix**:
  · cap entrada amb direcció i sense els dos períodes · cap `sense_serie` sense motiu (ni amb
  direcció) · cap Δ emmascarat sense interval · **l'atur de la Pobla ha de portar 2 comparacions
  i han de discrepar** (si algú en pinta una sola, cau) · població i les 4 franges amb motiu
  declarat · paritat `delta_pct_estrangera_finestra` ↔ tendència de l'origen · cap punt d'atur
  nul sense `emmascarat` + `[min,max]` · cada KPI de mètrica amb bloc `frescor`.
  Sortida: **16 KPIs, 7 amb rang, 15 mètriques amb tendència**.
- **Verificació al HTML PRERENDERITZAT del build propi**, no per navegador (cicatriu del port
  compartit de D8): `build/municipi/la-pobla-de-lillet/index.html`,
  `build/municipi/capolat/index.html` i les seves bessones `/es/`. Llegit i comprovat a mà: les
  dues fletxes oposades de l'atur, l'interval de Capolat, l'`indeterminat`, els 10 motius de
  `sense_serie`, la frescor per targeta amb «sense procés automàtic» a 9 fonts i «amb procés
  automàtic» només a l'atur, i «cadència no declarada» al RTC.
- **NO verificat**: res del carril de dades (no s'ha tocat cap fitxer de `tools/`,
  `packages/transform/`, `packages/ingestion/` ni `semantic/`); la resta de jobs del CI els
  ha de dir el CI.
- **Copy nou (ca+es) amb VOT NARRATIU DE BEA PENDENT**: etiquetes de comparació, de cadència,
  el text del «<5» a la targeta d'atur i les dues declaracions de punt cec («Sense tendència
  declarada», «cadència no declarada»).

---

## 5. Fitxers

`packages/web/src/lib/contract/tauler.ts` (nou) · `…/contract/types.ts` (5 claus + `Frescor`) ·
`…/contract/slug.ts` (`nomCanonic`) · `…/govern/kpis.js` · `…/routes/municipi/[slug]/+page.ts` ·
`…/routes/municipi/[slug]/+page.svelte` · `packages/web/scripts/copy-data.mjs` ·
`packages/web/scripts/verify-govern.mjs` · `packages/web/messages/{ca,es}.json`.

## 6. Idees per a la cua (proposo, no actuo)

- Quan arribi la sèrie de població (`censph`, encuada per D7), les 5 targetes de població i
  franges passen de `sense_serie` a fletxa: al front són **zero línies** de canvi — el motiu
  desapareix sol perquè el pinta la dada.
- La sparkline d'atur és avui l'única sèrie visible del tauler. Si entren les sèries de
  residus/ICAEN/renda (encuades per D7), el mateix component les serveix sense tocar-lo.
- **noindex intacte**, com mana la cua.
