# D11 · el lloc de naixement, que sí que hi era — Mirador (2026-07-20)

Capa de WEB de l'esmena **E11** de `docs/ajuntaments/tauler-v2-esmenes-bea.md`, reoberta per
Talaia després de verificar que **D9 la va tancar amb una premissa falsa**. La dada ja hi era des
de D7 (#276); aquí només es LLEGEIX.

**Resum en una línia:** el tauler ja ensenya **de què està feta la població per lloc de
naixement** —846 nascuts a Catalunya, 126 a la resta d'Espanya, 134 a l'estranger, 12,1% a la
Pobla—, i diu a la mateixa targeta que d'això en tenim **la foto i no la sèrie**, perquè l'única
evolució del bloc (+5,61 punts, 2021→2025) és de **nacionalitat**, que és una altra gent.

---

## 1. El meu error de D9, sencer

A D9 vaig escriure que «el mart només té nacionalitat» i vaig donar l'E11 per complerta a
mitges. **Era fals, i era comprovable amb una línia.** Les quatre mètriques de la dimensió
`origen` són `status: public` al contracte i arriben a `data/web/municipis.*.json` des de D7.
No em va faltar la dada: em va faltar mirar-la. El tauler va estar sis commits ensenyant el
passaport i amagant la biografia perquè jo vaig deduir una absència en comptes de verificar-la.

Ho deixo escrit sense adornar perquè la lliçó és de mètode, no d'aquesta targeta: **una
absència no es dedueix, es comprova**. El test nou (§4) existeix perquè aquesta forma concreta
d'equivocar-me no depengui que jo me'n recordi.

## 2. Què s'ha pintat

Quatre targetes noves al bloc A «Qui hi ha (i qui hi haurà)», just darrere de les franges d'edat
i **davant** de la nacionalitat:

| Targeta | La Pobla | Procedència a la targeta |
|---|---|---|
| Nascuts a Catalunya | **846** hab. | EMEX f69 · Idescat EMEX / Cens 2021 · 2025 |
| Nascuts a la resta d'Espanya | **126** hab. | EMEX f72 · Idescat EMEX / Cens 2021 · 2025 |
| Nascuts a l'estranger | **134** hab. | EMEX f73 · Idescat EMEX / Cens 2021 · 2025 |
| % nascuts a l'estranger | **12,1 %** | fórmula del contracte + font de les entrades |

Van **darrere de les franges d'edat i davant de la nacionalitat** per una raó que no és estètica:
són l'altra **partició** de la mateixa població. Nascuts a Catalunya + resta d'Espanya +
estranger = `poblacio`, **exacte als 947 municipis** (verificat, no suposat: 947/947 quadren al
byte, 0 desquadrats, 0 sense dada). I van davant de la nacionalitat perquè la nota de la
nacionalitat ha de poder referir-se a elles.

### El límit honest, escrit a la targeta

Mecanisme nou i petit: el descriptor de KPI accepta una `note`, que és una **clau i18n** d'un
límit de lectura que **no es dedueix de la dada** i que per tant s'ha de dir. Dues notes:

- A les quatre targetes de lloc de naixement: *«Foto, no sèrie: del lloc de naixement no en
  tenim evolució ingerida. L'única evolució d'aquest bloc és la de nacionalitat, que mesura una
  altra cosa.»*
- A la de nacionalitat, que és **l'única del bloc amb sèrie**: *«Aquesta evolució és de
  NACIONALITAT (passaport), no de lloc de naixement: qui es naturalitza deixa de comptar-hi
  sense marxar del poble.»*

La segona és la que de veritat tanca el forat. Un lector que baixa per quatre targetes de
nascuts-a i es troba un **↑ +5,61 punts · finestra · 2021 → 2025** llegeix, si ningú l'atura,
«han crescut els nascuts a l'estranger». No és el que diu aquella xifra. A la Pobla són **134
nascuts a l'estranger** contra **~106 amb passaport estranger**: qui es naturalitza surt d'un
conjunt i es queda a l'altre, sense moure's de casa.

Les quatre regles de pintura de D9 segueixen vigents i s'apliquen soles a les targetes noves:
com que `mart_tendencia` **no porta cap fila** de lloc de naixement, cauen al camí ja existent
«Sense tendència declarada: aquesta mètrica encara no és al mart de tendències» — i la `note`
hi afegeix la raó editorial a continuació.

## 3. Què s'ha decidit NO pintar (i per què)

- **«Nascuts fora de Catalunya» com a xifra única.** És literalment el que demana l'E11 de Bea,
  i **no existeix com a mètrica servida**. Serien 126 + 134 = 260, i sumar-ho al front seria
  fabricar una xifra sense procedència (C6 §8.1) — precisament la regla de ferro que aquest
  tauler defensa. Es pinten els tres components, que la donen a qui la vulgui. **Handoff a
  Sondeig** si Bea la vol com a targeta pròpia: ha de néixer al contracte, amb la seva fórmula.
- **`bretxa_naturalitzacio`.** És el concepte que fa llegible la distinció, però es deriva de
  dues xifres que ja són a la mateixa pantalla, i una cinquena targeta al bloc A hauria comprat
  claredat conceptual a canvi de densitat. La feina la fa la `note`, amb paraules. Segueix al
  catàleg i al bloc «Transformació demogràfica» de la fitxa.
- **Rang comarcal als tres recomptes.** Rankejar un component d'una partició és rankejar la mida
  del poble una altra vegada (mateix criteri que les franges d'edat de D9). El **%** sí que en
  demana i porta `pendingRank`, com la nacionalitat: el mart no el serveix i **aquí no es
  calcula** (C6 §4).

## 4. La guarda perquè això no torni

`verify-govern.mjs` (job `web` del CI, ja hi corria des de D9) creix amb una secció que ataca el
problema **des del costat contrari**: un test que només miri el que el tauler pinta no hauria
vist mai aquest forat, perquè el forat era el que **no** pintava. Va de la **dada** al descriptor:

| Guarda | Cau quan |
|---|---|
| **9a** | una mètrica de lloc de naixement té dada a la Pobla i el tauler **no la pinta** |
| **9b** | una targeta de lloc de naixement es queda **sense nota de límit**, o pren la tendència d'una sèrie de nacionalitat |
| **9b bis** | el mart comença a servir **sèrie** de lloc de naixement → la nota «foto, no sèrie» ha quedat obsoleta i s'ha de reescriure |
| **9c** | el tauler pinta l'evolució de nacionalitat i **no declara** que és de nacionalitat |
| **9d** | una `note` declarada al descriptor no existeix a ca+es **o no està cablejada** al component (seria un límit declarat en un fitxer i invisible a la pantalla) |

Les cinc s'han provat **fent-les caure una per una** sobre el codi bo i restaurant-lo després;
totes cauen amb el missatge correcte i totes passen en verd amb el codi final. La 9b bis és la
que m'importa més a llarg termini: és l'única que cau **quan la dada millora**, i ho fa a posta,
perquè una millora silenciosa deixaria una nota mentint a la pantalla.

## 5. Premisses del brief verificades (i una que no s'aguanta)

- ✅ Les quatre mètriques hi són, vives i servides. Xifres de la Pobla exactes al brief.
- ✅ El tauler no en pintava cap (`kpis.js`).
- ⚠️ **Matís:** no eren invisibles a tot el web. El bloc «Transformació demogràfica» de la fitxa
  ja les mostrava totes vuit — dins un `<details>` **plegat per defecte** (mode dades, P3). El
  forat era de **jerarquia**, no d'absència: la dada estava publicada, però al calaix de la
  maquinària i no al tauler que Bea llegeix. La feina i la conclusió no canvien.
- ❌ **Premissa falsa, i no és del brief sinó del contracte.** La `note` de
  `pct_nacionalitat_estrangera` afirma: *«Sempre ≤ % nascuts a l'estranger: la diferència són
  els qui s'han naturalitzat»*. **No és sempre.** A **37 dels 938** municipis amb dada, la
  nacionalitat estrangera **supera** el lloc de naixement i `bretxa_naturalitzacio` surt
  **negativa** (pitjors: Tornabous −2,66, el Cogul −2,47, Maials −2,44). El mecanisme és real i
  conegut: una criatura nascuda aquí de pares estrangers té passaport estranger i lloc de
  naixement català. No és un error de dada; és una **invariant mal enunciada** al contracte.
  Cap dels 37 és al Berguedà, així que el tauler d'avui no en mostra cap — però la fitxa serveix
  els 947 i **allà sí que es pot llegir aquella frase al costat d'una bretxa negativa**.
  No he tocat el copy: viu a `semantic/metrics.yml`, que no és meu. **Handoff a Sondeig.**
- ⚠️ El brief demana deixar `pendingRank` a `vidre_hab`. **No ho he fet**, i ho deixo dit:
  `vidre_hab` no en porta avui per una decisió editorial explícita de D9 («el vidre no el rankeja
  el mart: surt sense rang, que és la lectura honesta»), i canviar-la seria reobrir una decisió
  d'un altre lliurament des d'una tasca de lloc de naixement. Si Talaia vol el canvi, és una
  línia i una tasca pròpia.

## 6. Handoffs

**➡️ Handoff a: Sondeig** (dada · `semantic/metrics.yml`, `packages/transform/`):

1. **La invariant falsa de dalt.** «Sempre ≤» s'ha de reescriure a la `note` de
   `pct_nacionalitat_estrangera` (i revisar la de `bretxa_naturalitzacio`, que descriu la
   bretxa com si només pogués ser positiva). Amb 37 casos reals, el text actual és una promesa
   que la dada no compleix.
2. **Lloc de naixement absent de `mart_tendencia`.** Les quatre mètriques no hi tenen fila **ni
   com a `sense_serie` amb motiu** — exactament el mateix forat que D10(c) va obrir per a
   `serveis_estab`/`restauracio_estab`. Avui el front ho diu amb el text genèric «encara no és
   al mart de tendències»; amb una fila `sense_serie` diria el **motiu real de la font**, que és
   millor. Una fila que falta és invisible; un motiu es pot llegir.
3. **`formula` que no és una fórmula.** Els tres recomptes porten `formula: "EMEX f69 (darrer
   any)"`, que és un **localitzador de camp**, no un càlcul. `provenanceLine` (C6 §8.1) el
   classifica com a inferit i la targeta pinta un «ƒ» damunt d'una xifra **mesurada directament**.
   No és fals —la font també hi surt, a sota— però marca com a derivada una dada que no ho és.
   El fix natural és `formula: "directe"` + el localitzador al seu propi camp. **No ho he
   arreglat al front**: un cas especial a la UI seria amagar el que diu el contracte.
4. **Si Bea vol «nascuts fora de Catalunya»** com a xifra única, ha de ser mètrica del contracte
   amb la seva fórmula (§3).

## 7. Verificació

- `npm run check` (svelte-check): **1245 fitxers, 0 errors, 0 avisos**.
- `npm run verify:govern`: **OK — 20 KPIs**, tots amb font o fórmula i amb frescor; 7 amb rang
  llegit del mart; **4/4 mètriques de lloc de naixement pintades amb el seu límit declarat** i
  l'evolució de nacionalitat etiquetada com a tal.
- Guardes noves provades **en negatiu** (§4): 5/5 cauen quan toca, amb el missatge correcte.
- `npm run build`: verd.
- Verificat **al HTML prerenderitzat** de `la-pobla-de-lillet` (no a una captura del preview,
  que es degrada), en **ca i es**: hi surten les tres xifres (846 · 126 · 134), el 12,1 %, les
  dues notes de límit i la tendència de nacionalitat amb els seus dos períodes.

**Copy nou pendent del vot narratiu de Bea.** Les dues notes (`gov_naix_foto`,
`gov_nac_serie_es_nacionalitat`) són text nou i **encara no tenen el seu vot**; el copy de D9,
que sí que el té («el copy nou està guai»), no s'ha tocat.
