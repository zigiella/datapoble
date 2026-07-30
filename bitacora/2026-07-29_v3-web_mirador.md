# V3-WEB — el redisseny del tauler, executat (Mirador, 2026-07-29)

**Tasca:** V3-WEB del vot de Bea (2026-07-29, «tot ok. HUT sí»). Document vinculant:
`docs/ajuntaments/redisseny-tauler-v3.md`. Branca: `mirador/v3-web`. **No fusiono jo.**

## Què hi ha al PR

### 1 · Capçalera de presència (padró + ETCA junts, a dalt del tauler)
- Nova franja `gov-pres` al capdamunt del Tauler de dades: **padró** (amb la data del contracte,
  «N empadronats») i **ETCA** (o «sense dada oficial») costat per costat. Si divergeixen, el
  lector ho veu sol — cap interpretació nostra.
- Text pla d'ETCA **aprovat per Bea**, pintat literal: «Equivalent a temps complet: quanta gent
  hi és de mitjana al llarg de l'any, comptant-hi segones residències i visitants.» On Idescat
  no la publica: «Idescat només la publica per a municipis ≥1.000 hab.»
- **Cap xifra perduda** en absorbir les dues targetes velles: el padró conserva a la capçalera
  el seu **rang comarcal** («k de n», llegit del mart), el seu **motiu de no tenir sèrie** (dada
  del mart), la seva **font** i la seva **frescor**; els identificadors INE/Idescat de la
  targeta gran vella també hi viuen ara. La línia llarga d'ETCA (`muni_etca_srcline`) s'ha
  partit com proposava el doc (§5): frase plana + font curta + enllaç a /metodologia.

### 2 · Reagrupació i rètols
- **La gent** (edats · envelliment · d'on venim · nacionalitat) · **Les cases** (% no principal ·
  turisme) · **Feina i renda** (atur · renda) · **El dia a dia** (comerç/serveis · residus ·
  elèctric · vidre). El comerç/serveis puja del grup C al D (vida diària, no macroeconomia).
- L'envelliment **deixa de ser la primera targeta**: va darrere de les edats de què deriva, i
  porta la frase plana nova (§10 del doc): «X persones de 65 o més per cada 100 menors de 15.»

### 3 · Barres apilades
- **Estructura d'edats**: UNA targeta amb barra apilada (0-14 · 15-64 · 65-84 · 85+); llegenda
  amb **recompte i % per franja** (les 8 xifres al DOM). Procedència per C6 §8.1: les tres
  franges mesurades amb la font; la **15-64 amb la seva ƒ de resta** pintada a la targeta, i el
  seu **caveat del contracte accessible** (un `<details>` a la targeta mateixa, a més de la
  fitxa de /metodologia). El motiu de `sense_serie` (límit de la font) es pinta UNA vegada per
  a la partició, no quatre.
- **D'on venim**: UNA targeta amb barra apilada (Catalunya · resta d'Espanya · estranger) amb
  els tres recomptes + el **% nascuts a l'estranger SERVIT** (`pct_nascuda_estranger`, amb el
  seu pendingRank com fins ara). La nota «foto, no sèrie» hi va UNA vegada. Amb V3-CONTRACTE
  els tres recomptes són `formula: directe` → es pinten com a **mesurats** («Idescat — EMEX /
  Cens 2021 · 2025»), sense ƒ; el % conserva la seva ƒ.
- **Decisió de layout** (el doc no ho fixava): a la llegenda de «d'on venim» NO pinto un % per
  segment — el % que hi ha és el SERVIT (12,12 % a la Pobla), i posar-hi al costat un 12,1 %
  presentacional (recompte/padró arrodonit diferent) seria convidar a la confusió. A les edats
  sí que hi ha % per franja (el doc ho demana explícitament: «recompte i % per franja»); és la
  mateixa operació que l'amplada del segment — presentació dels recomptes servits contra el
  padró servit, cap dada nova fabricada al front.
- Les dues targetes de barra ocupen `span 2` a la graella (la forma es llegeix; a mòbil, una
  columna com la resta).

### 4 · Nacionalitat, HUT, E13, nota de grup
- **Nacionalitat**: es queda com a targeta pròpia amb la seva evolució (l'única del bloc amb
  sèrie) i la seva nota D11.
- **HUT** (vot: sí): la targeta de turisme pinta el cru — «31 establiments, 24 són HUT
  (habitatges d'ús turístic).» a la Pobla — de `rtc_total`/`rtc_hut`, amb la **font del
  registre** com a segona línia de font (el rati manté la seva ƒ i la seva font de derivat).
- **E13** (padró < 250): nota visible a `kg_hab_any`, `kwh_hab`, `vidre_hab`,
  `rtc_per_1000hab` i `index_envelliment` — la llista i el llindar del capçal de
  `semantic/metrics.yml`, exportats de `kpis.js` i guardats contra la doctrina. **⚠️ COPY
  PENDENT DEL VOT DE BEA** (el concepte està votat; la frase exacta, no):
  - ca: «Municipi de menys de 250 empadronats: una sola persona o casa mou aquest número.
    Llegeix-lo com a ordre de magnitud.»
  - es (mirall): «Municipio de menos de 250 empadronados: una sola persona o casa mueve este
    número. Léelo como orden de magnitud.»
  - També pendents del mateix vot narratiu, com tot copy nou: el text es de la capçalera
    (mirall del ca aprovat), les etiquetes de les barres i la frase plana de l'envelliment.
- **Nota única del grup La gent** (una línia al peu del grup, no quatre repeticions):
  «Les particions (edats i lloc de naixement) sumen exactament el padró.» — i la guarda ara
  RE-VERIFICA que això és cert sobre el dataset servit (31/31 exacte; si un dia no suma, la
  nota es torna mentida i el verificador cau).

### 5 · Fora duplicats i «sense procés automàtic»
- **«Els números clau»: eliminada sencera.** La targeta gran del padró: absorbida per la
  capçalera. Claus i18n òrfenes retirades (`muni_nums_title`, `muni_num_nop`, `muni_num_renda`,
  `muni_hab_padro`, `muni_etca_srcline`) amb guarda d'higiene.
- **«sense procés automàtic» fora de les targetes** (vot de Bea): la línia de frescor queda
  «cadència · darrera càrrega DD-MM-YYYY» (format ja existent, no tocat). La informació del
  procés **NO s'esborra del sistema**: la fitxa de /metodologia pinta ara una fila
  «Actualització» amb cadència · darrera càrrega · **procés de refresc** (la ruta del workflow,
  o «sense procés automàtic (es carrega a mà)»). Comentari de la regla E5 actualitzat al codi.

### 6 · Guardes (adaptades SENSE afluixar, i ampliades)
- `verify-govern.mjs`: tot el que hi havia es conserva (font O fórmula per targeta, rang llegit
  del mart + paritat, cap fletxa sense període, «<5» com a interval, atur amb les DUES
  comparacions, naixement foto-no-sèrie, P-947 Barcelona) adaptat als kinds nous
  (`edats`/`naixement`) i a la capçalera. **Noves**: les 8 xifres de les barres presents a la
  dada i cablejades al component · particions = padró exacte a tot el dataset · 15-64 derivada
  i les altres 3 mesurades · naixement `directe` (V3-CONTRACTE) · HUT amb font i dada ·
  E13_KEYS/llindar = doctrina del contracte + Sant Jaume exercit · capçalera cablejada ·
  seccions duplicades mortes de veritat · `proces_refresc` fora de la fitxa de municipi.
- `verify-docs.mjs`: el reagrupament mou claus de bloc, 20/20 targetes vives amb fitxa
  segueixen (el padró de capçalera i les 8 de les barres inclosos). **Nova §4**: /metodologia
  ha de llegir `proces_refresc` i cablejar la fila d'actualització — si algú la treu, cau,
  perquè llavors sí que la informació hauria desaparegut del sistema.
- Les dues guardes provades **en negatiu** durant el desenvolupament: la de duplicats morts va
  caure a la primera per un comentari d'estil que citava el literal de la classe morta
  (arreglat el comentari, no la guarda).

### 7 · Recompte de targetes
- **Abans:** 20 targetes (A 12 · B 2 · C 3 · D 3) + 2 seccions duplicades (targeta gran del
  padró, «Els números clau»).
- **Després:** **12 targetes** (A 4 · B 2 · C 2 · D 4) + **1 capçalera de presència**. Mateixa
  informació, cap xifra perduda (les 8 de les barres al DOM; padró amb rang/motiu/frescor a la
  capçalera; % no principal i renda ja eren targetes).

## ⛔ Premissa del brief, falsa (una)
- «les fitxes [de /metodologia] **ja pinten frescor de contracte**» — **no era cert**: la fitxa
  metodològica pintava què/com/font/advertiment del contracte, però CAP camp del bloc
  `frescor`. No hi havia «línia del procés» a afegir sobre res existent: he afegit la fila
  sencera (cadència · darrera càrrega · procés). La resta de premisses, verificades certes:
  `rtc_total`/`rtc_hut` servits (Pobla 31/24, Barcelona 11.421/10.653), naixement ja `directe`
  al contracte servit, DD-MM-YYYY ja implantat, Sant Jaume 08216 amb padró 25 i valor a les 5
  mètriques E13.

## Verificació (LOCAL, Actions avall fins el dia 1)
- `npm run check` → 0 errors / 0 warnings (1.256 fitxers).
- `npm run build` → verd (prerender complet).
- `npm run verify:govern` + `npm run verify:docs` → OK (missatges de resum nous).
- DOM al navegador (HTML prerenderitzat servit pel preview del build): la Pobla (08166),
  Barcelona (08019, fora pilot) i Sant Jaume de Frontanyà (08216, micromunicipi) — capçalera
  amb padró+ETCA junts · barres amb les 8 xifres · HUT a turisme · «Els números clau»
  inexistent · «sense procés automàtic» absent de les targetes (present a /metodologia) ·
  nota E13 a Sant Jaume (residus/elèctric/vidre/turisme/envelliment) · cap error de consola.
  (Detall del que s'ha vist, al PR.)

## Handoffs
- Cap de nou. Els vius segueixen: rang de `pct_nascuda_estranger` al mart (Sondeig, E9) i
  motius de `sense_serie` en registre ciutadà + `motiu_l10n` (Sondeig, V3-DADES en paral·lel —
  el tauler els segueix pintant literals fins que arribin els shards nous).

## Pendent del vot de Bea
- El copy exacte d'E13 (ca + mirall es), les etiquetes noves de la capçalera i barres, i la
  frase plana de l'envelliment (§4 d'aquesta bitàcola).
