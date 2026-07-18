# B3 — Xips de /pregunta-li re-basats en KPIs OFICIALS (i els 3 forats que la prova va destapar)

**Front:** Brúixola · **Data:** 2026-07-18 · **Tasca:** B3 (cua post-#256)

## Què demanava B3

Després dels aparcaments (#256) el model d'estimació és fora del web, però els xips d'exemple del
xat encara citaven `gap` (clau i18n `pl_ex_gap`, i `gap_pernocta_pct` dins `EXAMPLE_KEYS`) i IETR
(clau llegada `pl_ex_ietr`). Calia: triar 4–6 exemples que (a) siguin KPIs oficials del tauler de
govern (`docs/ajuntaments/gorra-alcalde-pobla.md` §3), (b) **resolguin de veritat**, (c) sonin a
pregunta de veí o d'alcalde.

## La doctrina de la tasca era la clau: «prova-ho — cap xip que porti a un refús»

Provar els xips candidats contra l'OfflineBackend **amb els marts reals** (no només fixtures) va
destapar que el xat de producció avui **menteix o refusa** en tres llocs:

1. **El pols mensual responia un mes arbitrari.** `mart_pols_mensual` real és una sèrie llarga
   (237 mesos × 947 municipis, 2006→2026). El lookup del router no era month-aware: «Quantes
   persones a l'atur té la Pobla de Lillet?» responia **72** (un mes de 2006 servit com a actual,
   amb `date: 2026-06` a la procedència!). El real de juny 2026 és **31**.
2. **Els topònims amb article no resolien.** El `mart_municipi` real escriu els noms a l'estil
   registre («Pobla de Lillet, la»); la gent pregunta «la Pobla de Lillet» → **refús** per a CADA
   mètrica municipal del municipi de la demo (i de tot municipi amb article: el Prat, l'Hospitalet…).
   Les fixtures (forma natural) ho **amagaven**: el gate offline passava i producció refusava.
3. **El xip viu de residus responia la mètrica equivocada.** «Quants quilos de residus per
   habitant genera Berga?» responia **habitatges per habitant** (`hab_per_hab`): la variant
   derivada del label («Habitatges per habitant» menys el lead word → «per habitant») guanyava per
   longitud al sinònim «residus». El xip publicat avui a producció respon una altra cosa.

## Què s'ha fet (tot al mateix PR, tot amb test)

**Router (`packages/ai`):**
- Lookup/ranking/tie/correlació sobre marts amb columna `date` ancorats a `MAX(date)` (el darrer
  mes carregat, que és el que documenta el `date:` del contracte). `Warehouse.columns()` nou.
- Índex de municipis **per taula** amb variants d'article INE («Pobla de Lillet, la» ↔ «la Pobla
  de Lillet»; «Espunyola, l'» ↔ «l'Espunyola»). Cada lookup lliga `$muni` amb el nom **tal com
  l'escriu la taula que consulta** (el pols i el municipal no coincideixen — fidel als marts
  reals). El path LLM resol contra la taula de la mètrica triada.
- Les variants derivades que queden en qualificador pelat («per habitant», «/ 1000 hab») ja no es
  generen (`catalog.match_terms`).
- Prosa amb nom natural («la Pobla de Lillet»); les files de dades conserven la grafia exacta del
  mart (traça byte-fidel).

**Fixtures (mirall fidel del real):** noms d'article a l'estil registre al municipal/electoral
(com el real); pols amb **dos mesos reals transcrits** (2026-05 + 2026-06, el mes ranci primer al
fitxer perquè una regressió al lookup naïf surti vermella); columna `renda_neta_persona`
il·lustrativa. README de fixtures actualitzat.

**Xips (contingut, ca+es — ⚠️ copy nou, vot narratiu de Bea PENDENT):** 6 preguntes curades, totes
KPIs oficials de la gorra §3, totes verificades als DOS móns (fixtures i marts reals):

| Xip (ca) | KPI § gorra | Mètrica | Resposta real avui |
|---|---|---|---|
| Quants habitants té la Pobla de Lillet? | 2 · padró | `poblacio` | 1.106 habitants |
| Quin percentatge d'habitatge no principal té Castellar de n'Hug? | 5 · el nus | `pct_noprincipal` | 74,28% |
| Quants establiments turístics té Gósol? | 6 · RTC | `rtc_total` | 20 establiments |
| Quantes persones hi ha a l'atur a la Pobla de Lillet? | 8 · el pols | `atur_registrat` | 31 persones (2026-06) |
| Quina és la renda neta per persona a Berga? | 9 · renda | `renda_neta_persona` | 15.449 €/persona |
| Quants quilos de residus per habitant genera Bagà? | 12 · residus | `kg_hab_any` | 444,73 kg/hab/any |

`EXAMPLE_KEYS` (xips-plantilla de reserva del contracte) ara és tot-oficial amb `kwh_hab` primer
(energia, l'únic KPI oficial sense xip curat — sonava massa tècnic com a pregunta de veí). Els
curats van primer; les plantilles queden de reserva. Claus `pl_ex_ietr`/`pl_ex_gap` esborrades.

**Gate nou (`tests/test_chips.py`):** llegeix el copy REAL dels xips dels catàlegs i18n del web
(ca+es) i l'executa contra l'OfflineBackend — si algú reescriu un xip cap a una pregunta que no
resol, vermell; + el contrapès: la pregunta lliure fora de catàleg segueix refusant honestament
(`out_of_catalog`); + cap xip pot citar una inferència aparcada.

**Verificació:** 210 tests offline verds (15 nous) · 15/15 evals · ruff net · svelte-check 0
errors · SSR del worktree renderitza els 6 xips ca+es (verificat per fetch; el pane de preview
degradat, lliçó coneguda) · 12/12 respostes correctes contra els marts reals.

## Handoffs i serrells

- **➡️ Handoff a: Talaia** — `index_envelliment` (KPI 1 del tauler!) és **`status: planned` al
  contracte** però la columna JA és al mart real amb dades. Fins que el contracte no l'alliberi, el
  xat el refusa i no pot ser xip. Decisió de contracte, no meva.
- **➡️ Handoff a: Talaia/D4** — els marts reals no coincideixen en la grafia dels topònims (pols
  «la Pobla de Lillet» vs municipal «Pobla de Lillet, la»). El router ara ho gestiona per taula,
  però una correlació entre marts fa `JOIN USING (municipi)` i **perd les files amb article**. La
  unificació de noms és cosa del mart (D4/Sondeig); mentrestant la vora queda documentada aquí.
- **Serrell meu (proper torn):** el copy del refús `unknown_municipality` diu «dins l'àmbit de
  dades (Berguedà)» i el mart ja és Catalunya-947 — text obsolet a `packages/ai/i18n.py` (i les
  claus germanes del web). Petit, però és copy → millor amb vot de Bea.
- La vora «taxa de paro resol al recompte» segueix on era (cua de Talaia, decisió D4).
