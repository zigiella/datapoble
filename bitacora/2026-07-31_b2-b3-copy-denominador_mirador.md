# B2 + B3 — el hero deixa de prometre el pilot i el denominador del rang es fa llegible (Mirador, 2026-07-31)

**Tasca:** esmenes B2 i B3 de Bea (`bitacora/next.md`). Branca: `mirador/b2-b3-copy-denominador`.
**No fusiono jo.** Jurisdicció tocada: només `packages/web/`.

---

## 0 · Resum en una pantalla

- **B2** · el hero de la home deia **«31 municipis»** en una portada que promet 43 comarques i 947
  municipis. Arreglat: les dues xifres es **compten** del loader (mai escrites) i el rètol és i18n
  ca+es. Mirant «la resta de la home» n'ha aparegut una altra que el brief no citava: **el peu de
  TOTES les pàgines portava un «31» pelat** entre les cotes.
- **B3** · la premissa del brief («qui no té dada és zero») ja arribava marcada com a FALSA per
  Talaia, i **ho és**: ho he tornat a verificar a la dada servida. El fix implementat és el que
  demanava l'esmena de fons: **el denominador s'explica**, amb el MOTIU, a qualsevol mètrica on
  `n_amb_dada` < els municipis de la comarca.
- **Una premissa MEVA que ha caigut a mitja feina** (la guarda me la va tombar): el primer copy que
  vaig escriure deia «El recompte sí que es publica». **És fals al nostre web** per a nacionalitat.
  Vegeu §4 — és la troballa més important d'aquesta passada i porta handoff a Sondeig.
- ⚠️ **TOT EL COPY NOU ÉS PENDENT DEL VOT NARRATIU DE BEA** (§5, amb el mirall en es).

---

## 1 · B2 · El hero de la home

> Bea: «Els 31 municipis: cal arreglar-ho.»

`routes/+page.svelte` declarava les cotes del full topogràfic així:

```js
const heroLabels = ['31 municipis', '42°17′N', '1.245 m', '2°01′E'];
```

Tres defectes en una línia, i només el primer era el que Bea va veure:

1. **«31 municipis» és el pilot.** Dues seccions més avall, la mateixa pàgina promet 43 comarques i
   947 municipis (les portes de W5, que ja compten de la dada).
2. **La xifra estava ESCRITA.** És la mateixa forma d'error que va matar la porta de W5: un número
   al copy es queda estale **en silenci** — ningú se n'assabenta fins que un humà el llegeix.
3. **Estava en català dur dins d'una pàgina que es tradueix**: a `/es` es llegia «31 municipis».

### Què s'ha fet

- `heroLabels` passa a `$derived` dels comptadors que el loader **ja servia** (`totalMunis`,
  `totalComarques`, comptats de `comarques.json` — la mateixa font de les portes). Si el comptador
  no arriba, la cota **no es pinta**: abans que ensenyar un número que no hem comptat.
- Rètols i18n nous: `home_hero_munis` / `home_hero_comarques` (ca+es), amb la xifra per paràmetre.
- **Es retira `'1.245 m'`**: una altitud sense font ni municipi darrere, que a escala Catalunya no
  vol dir res. El **parell de coordenades es queda** com a motiu de marca (és el mateix que el peu).

Al DOM prerenderitzat, les cotes del hero ara diuen:

| | cotes |
|---|---|
| `/` | `947 municipis` · `43 comarques` · `42°17′N` · `2°01′E` |
| `/es/` | `947 municipios` · `43 comarcas` · `42°17′N` · `2°01′E` |

### El que el brief no deia: el «31» del PEU

Comptant els `<text>` del DOM de la home van sortir **quatre cotes de més**: venien del
`ContourField` del **peu**, que es pinta a **totes** les pàgines. Deien:

```js
const footLabels = ['1.245 m', '42°16′N', '31', '1°53′E', '593'];
```

Un **«31» pelat** —el pilot, sense unitat, sota una portada que promet 947— i un **«593»** del qual
no he sabut reconstruir cap procedència. **No els he substituït per 947 i 43**: el layout no
carrega dades, així que escriure-hi una xifra nova seria repetir exactament el defecte de B2.
S'han **retirat els dos números sols**; queden les cotes que diuen de què són (altitud i
coordenades), que és el motiu de marca. `footLabels = ['1.245 m', '42°16′N', '1°53′E']`.

### La resta de la home, revisada — i la promesa del pilot que NO he tocat

Escombrada sencera: hero, cercador, mapa, portes, peu **i les metadades**. Les xifres estan bé
(`home_map_scope` —«Al Berguedà hi treballem a fons»— és cert i deliberat; les portes ja compten des
de W5). Però mirant el navegador va sortir la promesa del pilot **més visible de totes**, que no és
una xifra:

> **El `<title>` de la home diu «riusdegent · Observatori territorial del Berguedà».**

És la clau `app_tagline`, i no viu només a la pestanya: és també l'**`og:title` de TOTES les
pàgines** (`+layout.svelte`) — o sigui, el que es veu quan algú comparteix qualsevol enllaç nostre.
Una portada que promet 43 comarques i 947 municipis es presenta a si mateixa com a observatori
d'una comarca.

**No l'he canviada.** És el rètol de la MARCA i un posicionament, no un número estale: és vot
narratiu de Bea de cap a peus, i canviar-lo de la meva mà seria decidir què som. Proposta al §5.

Del mateix escombrat, però **fora de la home** (altres rutes, tot copy viu):
`map_title` = «Mapa coroplètic del Berguedà» a `/mapa`, que des de fa temps pinta **tot Catalunya**
· `muni_srcline` = «Dades del contracte semàntic de datapoble · **Berguedà** · cap xifra sense
origen» al peu de **les 947 fitxes**, també les de fora · `muni_lede`, `map_outside_*`,
`map_legend_*`. Van totes al mateix vot (§5).

I finalment, **claus i18n òrfenes** amb «31 municipis» a dins (`footer_data_note`, `resum_*`,
`map_data_caveat`, `constel_aria`): **no les pinta ningú** avui, però són el mateix tipus de mina.
Vegeu §6.

---

## 2 · B3 · La premissa del brief, re-verificada a la dada servida

> Bea: «El rang de nacionalitat estrangera al Berguedà no pot ser sobre 27. Ha de ser sobre 31. Qui
> no té dada, és que és zero, no?»

Talaia ja havia marcat la premissa com a falsa. **L'he tornat a exercir sobre `govern.catalunya.json`
i `municipis.catalunya.json` (els artefactes que el web serveix de veritat), no sobre la font**, i
es confirma. Els 9 municipis de Catalunya sense percentatge de nacionalitat tenen **tots** menys de
50 habitants, i **cap** municipi de 50 o més se'l queda: el NULL és exactament el nostre llindar
(`demografia_min_n = 50`), no un forat.

Al Berguedà són 4, i **dos no són zero**: Fígols (5 de 41 hab) i **la Quar (7 de 44 = 15,9 %,
la número 2 de la comarca)**. Posar-los a zero pintaria la Quar **l'última**: publicaríem el
contrari de la veritat sobre un poble concret. **No s'ha implementat com Bea ho demanava
literalment** — i això queda dit aquí, no amagat en un commit.

**Però la incomoditat de Bea era bona i el fix va a la seva arrel:** «6 de 27» al costat de «8 de
31» a la mateixa pantalla sembla arbitrari si ningú l'explica.

---

## 3 · Què s'ha fet: el denominador es fa llegible (general, no només nacionalitat)

Quan `n_amb_dada` < els municipis de la comarca, la targeta afegeix una línia sota el rang:

> **6 de 27** · rang comarcal · per valor a Berguedà
> *27 dels 31 municipis de la comarca tenen aquesta xifra. On no hi és, és perquè hi viuen menys de
> 50 persones: amb tan poca gent, el percentatge assenyalaria veïns concrets. No vol dir zero.*

Tres decisions que valen més que el text:

**(a) El MOTIU es declara per mètrica, i n'hi ha TRES, no un.** Escombrant les 9 claus rankejables
× 43 comarques, els forats surten a **tres** mètriques i **per causes diferents**:

| mètrica | munis sense xifra | per què | motiu declarat |
|---|---|---|---|
| `pct_nacionalitat_estrangera` | 9 (4 al Berguedà) | **llindar NOSTRE** (`demografia_min_n = 50`) | `gov_denom_minn` |
| `renda_neta_persona` | 20 en 14 comarques | **l'INE no la publica** (ADRH) | `gov_denom_font` |
| `index_envelliment` | 1 (la Febró, Baix Camp) | **`pob_0_14 = 0`**: la divisió no es pot fer | `gov_denom_ratio` |

Escriure el text de nacionalitat per a totes tres hauria estat **mentir amb bona intenció**: la
renda la calla la FONT, no la nostra prudència (hi ha municipis de 38 hab **amb** renda i de 110
**sense**), i a la Febró no hi ha secret, hi ha una divisió per zero. Una mètrica que no consti al
mapa pinta el motiu **neutre** («no en tenim la xifra»): quedar-nos curts abans que inventar-ne la
causa.

**(b) Els tres motius es CONTRASTEN amb els 947 al verificador.** No n'hi ha prou que el text
existeixi: `verify-govern.mjs` comprova, municipi a municipi, que cada causa declarada és certa
(cap muni sense % d'origen arriba al llindar i cap que hi arribi se'l queda · sense índex
d'envelliment **només** on `pob_0_14 = 0` · la renda no segueix el patró del llindar). I llegeix
`demografia_min_n` del **transform**: si Sondeig el mou allà, la guarda cau abans que la pantalla
expliqui un llindar que ja no és el nostre.

**(c) El rang es pinta ara des d'UN sol lloc.** Hi havia el mateix marcatge **copiat tres vegades**
(capçalera de presència, targeta de mètrica, % de la barra de naixement). Una explicació que només
arribés a dos terços hauria estat pitjor que cap → snippet `rangComarcal` compartit, amb guarda que
compta els tres usos i que cau si torna a aparèixer marcatge duplicat.

### D'on surt el total de municipis de la comarca (C6 §4)

El JSON de govern **no** el porta (té `valor`, `rang`, `n_amb_dada`, `data`, `empat` i les dues
medianes de W4). **No s'ha calculat res al front**: es **compta** de `municipis-territori.json`,
que el loader de la fitxa **ja carregava** per a l'espina i els veïns. Tres raons per les quals això
no toca la frontera dura:

1. C6 §4 prohibeix calcular **percentils i rangs** al front, i preveu explícitament el recompte al
   client sobre dades que ja viatgen (el cas de `distinguish.ts`). Això no compara ni ordena cap
   municipi: compta files d'una partició.
2. És el **MATEIX artefacte** que fa la partició al mart — `mart_govern.sql` ho diu al seu capçal:
   «COMARCA = AUTORITAT municipis-territori.json». Per construcció no pot divergir del denominador.
3. És el precedent ja fusionat de W5: les xifres de les portes de la home es compten d'aquesta
   mateixa agrupació.

**➡️ Handoff a: Sondeig** (no bloquejant, millora de lloc): el lloc **durador** d'aquest número és
el mart. Afegir `n_comarca` a la cel·la de `mart_govern` (surt del mateix `partition by` que
`n_amb_dada`, cost zero) faria que el denominador i el seu total vinguessin **de la mateixa
finestra**, i el front passaria de comptar a llegir. El dia que hi sigui, el recompte del loader se
substitueix per la lectura i la guarda es queda igual.

---

## 4 · ⚠️ La premissa que va caure a mitja feina: el RECOMPTE de nacionalitat NO es publica

El brief deia —i jo m'ho vaig creure prou per escriure-ho a la pantalla— que **«els recomptes sí que
es publiquen»**. Vaig posar-ho al copy. **La meva pròpia guarda el va tombar**, i té raó:

- `poblacio_nacionalitat_estrangera` (els 7 de la Quar) viu a **`mart_demografia`** i **no arriba al
  web**: no és a `semantic/metrics.yml`, no és al contracte servit, no és a cap dataset del web.
- Per tant, a la fitxa de la Quar **no hi ha CAP xifra de nacionalitat**: ni el percentatge (suprimit
  pel llindar, correctament) ni el recompte (que no existeix al web).
- El que la Quar **sí** que té publicat és l'altra partició: **lloc de naixement**, amb els seus
  recomptes (36 · 2 · 6, que sumen el padró). Però és **una altra cosa** —el mateix tauler insisteix
  que nacionalitat ≠ biografia—, així que no serveix per sostenir la frase.

El text final diu **«No vol dir zero.»** en comptes de prometre un recompte que no servim. I hi ha
guarda **pels dos costats**: mentre el web no el serveixi, el copy no el pot prometre; i **el dia
que Sondeig el serveixi, la guarda cau** per obligar a reescriure la frase (que llavors es quedarà
curta) — no per castigar la millora. És el patró de la nota «foto, no sèrie» (§9b del verificador).

**➡️ Handoff a: Sondeig** — `poblacio_nacionalitat_estrangera` cap al contracte i a l'export web.
És el que faria vera la frase que tots dos volíem escriure, i és exactament el que evita que la
supressió d'un percentatge es llegeixi com un zero. **Decisió de si es publica: de Bea** (és un
recompte petit; la doctrina que suprimeix el percentatge fi no l'afecta, però val la pena que ho
digui ella).

---

## 5 · ⚠️ COPY NOU — PENDENT DEL VOT NARRATIU DE BEA

### B2 · cotes del hero de la home

| clau | ca | es |
|---|---|---|
| `home_hero_munis` | `{n} municipis` | `{n} municipios` |
| `home_hero_comarques` | `{n} comarques` | `{n} comarcas` |

Cotes resultants: **`947 municipis` · `43 comarques` · `42°17′N` · `2°01′E`**.
*Alternativa si Bea vol el full net:* retirar també el parell de coordenades — però aleshores caldria
retirar-lo **també del peu** (hi surt dues vegades: a les cotes i a la barra inferior), o quedaria
descosit.

### B2b · ⚠️ EL RÈTOL DE LA MARCA — no tocat, decisió teva

`app_tagline` = **«Observatori territorial del Berguedà»** / «Observatorio territorial del
Berguedà». És el `<title>` de la home **i l'`og:title` de tot el web** (el que es veu en compartir
qualsevol enllaç). Tres camins, i cap és obvi:

1. **Canviar l'abast:** «Observatori territorial de Catalunya» / «…de Cataluña». Directe, però
   promet més del que fem: a la resta del país servim indicadors oficials, no el treball a fons.
2. **Dir les dues coses** (el que la home ja diu al mapa): «Observatori territorial · Catalunya,
   poble a poble» / «…Cataluña, pueblo a pueblo». Honest i no promet profunditat uniforme.
3. **Deixar-lo com està** i assumir que la marca va néixer al Berguedà i s'hi queda ancorada.

Si tries 1 o 2, el mateix vot hauria d'arrossegar `map_title` («Mapa coroplètic del Berguedà» en un
mapa que pinta els 947), `muni_srcline` («… · Berguedà · …» al peu de les 947 fitxes) i `muni_lede`.
Ho faig en una passada quan votis.

### B2 · cotes del peu (afecta TOTES les pàgines)

`['1.245 m', '42°16′N', '31', '1°53′E', '593']` → **`['1.245 m', '42°16′N', '1°53′E']`**.

### B3 · la línia del denominador

| clau | ca | es |
|---|---|---|
| `gov_denom_line` | `{n} dels {total} municipis de la comarca tenen aquesta xifra.` | `{n} de los {total} municipios de la comarca tienen esta cifra.` |
| `gov_denom_minn` | `On no hi és, és perquè hi viuen menys de {n} persones: amb tan poca gent, el percentatge assenyalaria veïns concrets. No vol dir zero.` | `Donde no está, es porque viven menos de {n} personas: con tan poca gente, el porcentaje señalaría a vecinos concretos. No quiere decir cero.` |
| `gov_denom_font` | `On no hi és, és perquè la font no la publica per a aquell municipi.` | `Donde no está, es porque la fuente no la publica para ese municipio.` |
| `gov_denom_ratio` | `On no hi és, és perquè no hi viu ningú de 0 a 14 anys: la divisió no es pot fer.` | `Donde no está, es porque no vive nadie de 0 a 14 años: la división no se puede hacer.` |
| `gov_denom_nd` | `On no hi és, no en tenim la xifra.` | `Donde no está, no tenemos la cifra.` |

*Notes per al vot:* (a) la proposta del brief era «de 27 municipis amb dada publicable; 4 són massa
petits…»; he preferit **no comptar el forat** («4») perquè la frase hauria de concordar en singular
i plural en dues llengües, i **no dir «publicable»**, que és jerga nostra. (b) La forma és **una
línia sota el rang**, no un tooltip: ha de ser llegible en paper, per lector de pantalla i sense
passar-hi el ratolí. (c) El «50» del text **no està escrit**: ve declarat de `kpis.js` i verificat
contra el transform.

---

## 6 · Handoffs i coses que deixo dites (no fetes en aquest PR)

- **➡️ Sondeig** — `n_comarca` a la cel·la de `mart_govern` (§3) i
  `poblacio_nacionalitat_estrangera` cap al contracte i l'export web (§4).
- **➡️ Bea (editorial)** — el vot del §5 (inclòs **B2b, el rètol de la marca**, que és el que més
  es veu), i la pregunta oberta de si les coordenades del full topogràfic es queden (hero + peu) o
  cauen a tot arreu alhora.
- **➡️ Talaia (doctrina) + Sondeig (dada)** — **una incoherència que he vist verificant la Quar i
  que no és meva de resoldre.** A la seva fitxa, el % de nacionalitat surt com a `n. d.` (suprimit
  pel llindar) i **just al costat s'hi pinta la seva evolució: «↑ +1,62 punts, 2021 → 2025»**. El
  delta ve del mart (`mart_tendencia`) i el front el pinta com per a qualsevol altra targeta. No
  filtra el nivell —no es pot reconstruir el percentatge des del delta— però **la doctrina queda
  coixa**: diem que no publiquem el percentatge perquè amb 44 habitants cada persona el mou 2-4
  punts, i tot seguit publiquem un moviment de 1,62 punts d'aquest mateix percentatge. O el delta
  també cau sota el llindar, o el motiu que expliquem s'ha de matisar. **No ho toco**: el llindar és
  del transform i la doctrina és de contracte, cap de les dues és jurisdicció meva.
- **➡️ Mirador (jo mateix, propera passada)** — dues coses de la **mateixa família** que B2, que no
  entren aquí per no convertir un PR de copy en un PR de tot el web:
  1. **El hero de la FITXA de municipi** porta `'947'` escrit a mà i rètols només en català
     (`['INE', 'padró', 'font', '947', 'mètriques', 'procedència', 'fitxa']`, i el mateix patró a
     `/glossari`, `/pregunta-li` i `/metodologia`). El 947 **avui és cert**, però és exactament la
     mena de xifra escrita que va deixar el «31» podrint-se; i els rètols no es tradueixen a `/es`.
  2. **Claus i18n òrfenes amb el pilot a dins**: `footer_data_note`, `map_data_caveat`,
     `constel_aria`, `resum_*` diuen «31 municipis» i **no les pinta ningú**. Retirar-les és higiene
     (el bloc `I18N_GONE` del verificador ja té el mecanisme).

---

## 7 · Verificació (en local, abans del PR)

| comprovació | resultat |
|---|---|
| `npm run check` | **0 errors, 0 warnings** (1.273 fitxers) |
| `npm run build` | **verd**, 947 fitxes × 2 llengües |
| `npm run verify:govern` | **OK**, amb les seccions B2 i B3 noves |
| `npm run verify:docs` | **OK** (35 indicadors, 38 fitxes) |
| `python packages/transform/verify_tendencia.py` | **OK** (20.802 files) — obligatori en tocar `kpis.js` |
| **guardes noves provades EN NEGATIU** | **12/12** cauen quan han de caure |
| `noindex` | **intacte** (home ca+es, fitxa) |

**Al DOM prerenderitzat** (no a la captura del preview, que es degrada):

- `/municipi/la-pobla-de-lillet/` → nacionalitat **«6 de 27»** + la línia («27 dels 31 municipis de
  la comarca…»); vidre **«17 de 31»** **sense** línia, perquè no li'n cal. Mirall `/es/` idèntic.
- `/` i `/es/` → les cotes del hero, comptades i traduïdes.
- Al navegador: home i fitxa de la Pobla en ca i es, **cap error de consola**.

Les 12 proves en negatiu cobreixen: tornar «31 municipis» al hero · deixar de comptar-lo · escriure
una xifra al copy i18n · tornar a posar una cota pelada al peu · que el loader deixi de servir el
total · despenjar un dels tres rangs del snippet · duplicar el marcatge del rang · moure el llindar
respecte del transform · tornar a prometre el recompte · esborrar la línia d'un catàleg · declarar
un motiu que no es pinta · declarar la condició i no cridar-la.
