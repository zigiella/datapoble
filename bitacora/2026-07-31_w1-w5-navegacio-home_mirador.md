# W1 + W5 — la navegació surt del Berguedà i la porta de la home s'obre (Mirador, 2026-07-31)

**Tasca:** esmenes W1 i W5 de Bea (`bitacora/next.md`). Branca: `mirador/w1-w5-navegacio-home`.
**No fusiono jo.** Jurisdicció tocada: només `packages/web/`.

---

## 1 · W1 · El selector de municipi es quedava al Berguedà

> Bea: «Un cop seleccionat un municipi, des de dins només es poden seleccionar municipis del
> Berguedà.»

### La causa: CONFIRMADA, i el símptoma era pitjor del que deia el brief

Verificat al HTML **prerenderitzat** del build de referència (no a la font):
`src/routes/municipi/[slug]/+page.svelte` construïa `muniOptions` de
`Object.values(dataset.municipis)` — els **31** del pilot — dins d'una fitxa que se serveix per als
**947**. Comptat al DOM de tres pàgines del build anterior:

| fitxa | opcions del selector | hi és Barcelona? | hi és Girona? |
|---|---|---|---|
| `/municipi/la-pobla-de-lillet/` | 31 | no | no |
| `/municipi/barcelona/` | **31** | **no** | no |
| `/es/municipi/girona/` | **31** | no | **no** |

El que el brief no deia i el DOM sí: **el municipi que s'estava mirant no sortia a la seva pròpia
llista**. Les tres pàgines servien exactament les mateixes 31 opcions, començant per «Avià», i el
`<select value={ine5}>` no trobava cap opció que hi casés → a la fitxa de Barcelona el navegador
pintava **«Avià» com a seleccionat**. No era només que no es pogués sortir del Berguedà: el selector
afirmava una cosa falsa sobre on ets.

### Què s'ha fet

- **La font del selector passa a ser el CATÀLEG dels 947** (`municipis-cataleg.json`, cens de
  noms+codis derivat de la geometria oficial) — la mateixa columna vertebral que ja resolia els
  slugs, els veïns i els miralls. El loader ja el carregava; ara el **retorna**.
- **L'`ine5` segueix sent la clau interna** del selector (el `value` de cada opció, com abans); el
  slug es resol amb el mateix índex que ha construït la llista.
- **Ordre**: es mostra la forma corrent («la Pobla de Lillet») i s'ordena per la forma d'**índex**
  («Pobla de Lillet, la»). A 31 municipis això era un detall; a 947 hi ha **131 noms amb article**
  que, ordenats per la forma corrent, s'apilarien sota «L» i «E». Per fer-ho hi ha una funció nova,
  `nomIndex`, que és la inversa exacta de `nomCanonic`.
- **Degradació honesta**: si el catàleg no arriba, la llista cau als municipis del dataset en
  comptes de quedar-se buida. Mai una llista muda.

### El cost, mesurat (no estimat)

Dos builds sencers, abans i després:

| | abans | després | Δ |
|---|---|---|---|
| fitxers del build | 5.926 | 5.933 | +7 |
| mida del build | 2.287 MB | 2.396 MB | **+109 MB (+4,8 %)** |
| fitxa de Barcelona | 728.551 B | 768.446 B | **+39.895 B (+5,5 %)** |
| fitxa de la Pobla | 1.047.576 B | 1.087.459 B | +39.883 B (+3,8 %) |
| home | 1.816.451 B | 1.830.205 B | +13.754 B (+0,8 %) |

**Tot el creixement de la fitxa són les 947 `<option>`**: el bloc `<select>` de la pàgina de
Barcelona fa **40.972 B**, i el delta mesurat és 39.895 B (la diferència són les 31 opcions velles
que ja hi eren). O sigui que **retornar el catàleg al `data` ha costat 0 bytes mesurables**: en una
pàgina prerenderitzada SvelteKit ja incrustava la RESPOSTA d'aquell `fetch`
(`data-sveltekit-fetched`, **43.776 B**) a **cada** fitxa des d'abans d'avui, i el `load` universal
la reaprofita en hidratar. La factura del catàleg ja estava pagada; el que faltava era fer-lo servir.

Marge de Cloudflare Pages intacte: 5.933 fitxers (límit 20.000), fitxer més gros sense canvi
(1,8 MB, `municipis.catalunya.json`).

### Col·lisió de slugs — **premissa del brief a mitges**

El brief diu que «el codi actual té una guarda de col·lisió **per al pilot**». Només és mig cert:
n'hi havia **dues**. `buildSlugIndex` sobre els 31 (al `load`) **i** la mateixa guarda dins
d'`entries()` de `municipi/[slug]/+page.ts`, que ja passava sobre els **947** del catàleg en BUILD
i, per tant, ja trencava el build a CI. Cap de les dues s'ha tret; s'hi ha **afegit una tercera,
offline**, a `verify-govern.mjs`, i s'ha comprovat el número:

- **947 municipis → 947 slugs distints, cap col·lisió** (avui).
- **131 noms amb article**, i per a tots ells `toSlug(nomIndex(nom)) === toSlug(nom)`: la clau
  d'ordenació nova **no mou cap URL**. També s'exercita la volta sencera
  `nomIndex → nomCanonic → el nom original`.

Perquè la guarda pugui exercir el `toSlug` **real** i no una còpia, la regla d'article s'ha extret a
`src/lib/contract/slug-core.js` (JS pur) i `slug.ts` ha quedat com a façana tipada que la re-exporta:
**cap punt de crida canvia**. És el mateix patró —i el mateix motiu— que `src/lib/govern/kpis.js`,
que ja existia precisament perquè el verificador i el component no derivin.

### Els veïns — **premissa del brief FALSA**

El brief demanava mirar «la llista de veïns, si beu de la mateixa font». **No en bevia: ja estava
bé.** Els veïns es construeixen del catàleg + `municipis-territori.json` des de P-947. Comptat al
build nou: la Pobla → 30 veïns del Berguedà · **Barcelona → 4 del Barcelonès** (Badalona,
l'Hospitalet, Sant Adrià, Santa Coloma) · **Girona → 26 del Gironès**. No s'hi ha tocat res.

---

## 2 · W5 · La porta de la home

> Bea: «l'apartat de la home llegeix la comarca està desactualitzat.»

### La causa: CONFIRMADA, les dues meitats

Al DOM del build de referència, la secció «Llegeix la comarca» servia literalment:

```html
<div class="porta porta--soon" aria-disabled="true">
  <span class="porta__nom">Resta de Catalunya</span>
  <span class="porta__sub">947 municipis · cada poble té fitxa amb les seves dades oficials</span>
</div>
```

(a) **No és «properament»**: des de P-947 els 947 municipis tenen fitxa i les 43 comarques tenen
pàgina prerenderitzada. (b) **El 947 hi estava etiquetat com a «resta»** quan és el **TOTAL** de
Catalunya — la resta serien **916**. La porta prometia menys del que hi ha i alhora comptava
malament.

**Serrell trobat de passada:** `home_porta_soon` («sense dades encara») era una clau i18n **òrfena**
a ca+es des de feia temps: declarada i pintada enlloc. Retirada, i afegida a la llista d'higiene
(`I18N_GONE`) perquè no pugui tornar a quedar-s'hi.

### La decisió: la porta va a `/comarca`, un índex nou de les 43 comarques

El brief deixava triar («/mapa o un índex de comarques; tria i justifica»). **Índex de comarques**,
per tres raons:

1. **El rètol de la secció mana.** Si la secció es diu «Llegeix la comarca», les seves dues portes
   han de ser comarques: el Berguedà (el nucli que treballem a fons) i **totes**.
2. **/mapa ja hi és, dues línies més amunt** («Obre el mapa complet»). Posar-hi la porta hauria
   duplicat un enllaç i, a més, un mapa no és «llegir una comarca».
3. **No promet feina nova.** Les 43 pàgines de comarca ja existeixen i ja es prerenderitzen;
   l'índex només les fa trobables. Surt sencer de `comarques.json`, l'artefacte que el prebuild ja
   deriva. Zero dades noves, zero jurisdicció d'altri.

`/comarca` (+ `/es/comarca`): 43 comarques agrupades per les 8 vegueries, cadascuna amb el seu
recompte de municipis i enllaç. **L'agrupació es fa per la `vegueria` de CADA comarca**, no per la
llista paral·lela `vegueries`: si un dia una comarca es quedés sense vegueria sortiria igualment, en
un grup declarat, en comptes de desaparèixer en silenci — és el bug de la llista fixa que ja ens ha
mossegat al glossari (`DIM_ORDER`) i al mart (D10). Verificat al DOM: **la suma dels municipis
pintats per comarca fa exactament 947**.

### Les xifres, comptades i no escrites

Cap número del copy de les portes va escrit al text: el subtítol rep `{comarques}` i `{munis}` (i el
del Berguedà, `{munis}`), i el loader de la home els **compta** de `comarques.json`. El «947
municipis» que es va quedar estale ho va fer per estar escrit al copy; ara no es pot repetir, i hi ha
guarda que fa caure el CI si algú torna a posar un dígit en aquestes cadenes. Si l'artefacte no
arriba, la porta s'ensenya **sense subtítol** en comptes de pintar un 0.

### ⚠️ COPY NOU — PENDENT DEL VOT NARRATIU DE BEA

Concepte votat implícitament (obrir la porta i dir la veritat); **la frase exacta, no**. El que hi ha
ara al PR, ca + mirall es:

| clau | ca | es |
|---|---|---|
| `home_porta_cat` | Totes les comarques | Todas las comarcas |
| `home_porta_cat_sub` | {comarques} comarques · {munis} municipis, cada poble amb la seva fitxa de dades oficials | {comarques} comarcas · {munis} municipios, cada pueblo con su ficha de datos oficiales |
| `home_porta_cat_cta` | Veure totes les comarques | Ver todas las comarcas |
| `comarques_title` | Comarques de Catalunya | Comarcas de Cataluña |
| `comarques_eyebrow` | Tot el país | Todo el país |
| `comarques_sub` | {comarques} comarques en {vegueries} vegueries · {munis} municipis, i cada poble té la seva fitxa de dades oficials. | {comarques} comarcas en {vegueries} veguerías · {munis} municipios, y cada pueblo tiene su ficha de datos oficiales. |
| `comarques_sense_vegueria` | Sense vegueria declarada | Sin veguería declarada |

Renderitzat avui: «**Totes les comarques** · 43 comarques · 947 municipis, cada poble amb la seva
fitxa de dades oficials · Veure totes les comarques →».

---

## 3 · Guardes noves (i provades EN NEGATIU, 9/9)

Dues seccions noves a `scripts/verify-govern.mjs`, que ja corre al job `web` del CI:

**W1** — (a) el catàleg cobreix els 947 · (b) cap col·lisió de slug entre els 947, amb el `toSlug`
**importat** · (c) la clau d'ordenació no mou cap URL i la volta `nomIndex→nomCanonic` torna al nom
original · (d) cablatge: el loader retorna el catàleg, la guarda de col·lisió d'`entries()` segueix
al seu lloc, el selector es construeix del catàleg i **no** torna a derivar-se del dataset del pilot.

**W5** — cap porta morta (`porta--soon`/`aria-disabled`) a la home · la porta apunta a `/comarca` ·
l'índex existeix i llegeix l'agrupació · les cadenes de porta **no poden portar cap dígit** ·
l'agrupació cobreix els 947 i cap municipi es queda sense comarca.

Provades cadascuna en negatiu (mutar → ha de caure amb el seu missatge → restaurar): **9/9**. Un
detall de mètode: la guarda de la porta morta va caure primer amb el **meu propi comentari**, que
anomena les classes retirades; s'ha corregit perquè miri el que es PINTA (fora comentaris HTML) i no
el que s'explica — una guarda que castiga la seva pròpia documentació acaba fent esborrar
l'explicació.

---

## 4 · Verificació

**En local, tot verd:**
- `npm run check` → **0 errors, 0 warnings** (1.266 fitxers)
- `npm run build` → verd, 3 m 24 s
- `npm run verify:govern` → OK (amb les línies W1/W5 noves al resum)
- `npm run verify:docs` → OK
- prova en negatiu de les guardes noves → **9/9**

**Al DOM prerenderitzat** (ca i es): selector amb **947 opcions** i l'opció correcta marcada
`selected` a la Pobla (08166), Barcelona (08019), Girona (17079) i Sant Jaume de Frontanyà (08216);
**els 947 slugs del catàleg tenen pàgina prerenderitzada en ca i en es (0 absents)**; índex de
comarques amb 43 comarques / 8 vegueries / suma 947.

**Al navegador** (servidor estàtic d'aquest worktree, per DOM): home → clic a la porta →
`/ca/comarca/` (43 targetes) · fitxa de la Pobla → selector → **Barcelona** · Barcelona → selector →
**Girona** · Girona → selector → **Sant Jaume de Frontanyà** (E13 pintada, 30 veïns). **Cap error de
consola** en tot el recorregut, en ca i en es.

`noindex` **intacte** a les tres superfícies (`app.html`, `robots.txt`, `_headers`). P1/P2 segueixen
ocults. Vista única «Tauler de dades». Doctrina intacta: no s'ha tocat cap xifra, cap rang, cap
tendència ni `kpis.js` — i per tant **no calia córrer `verify_tendencia.py`** (la lliçó del dia val:
el diff no toca cap `kind` ni cap mètrica pintada).

---

## 5 · Handoffs i coses vistes que NO he tocat

- **➡️ A Bea (vot narratiu):** el copy de la taula del §2.
- **➡️ A Bea (editorial, no tocat):** el hero de la home encara porta el rètol decoratiu
  **«31 municipis»** (`heroLabels`). En una home que ara promet 43 comarques i 947 municipis, es
  llegeix com un abast, no com un adorn. És copy: no l'he canviat pel meu compte.
- **Neteja encuada (no d'aquesta tasca):** `svelte.config.js` segueix prerenderitzant `/index/` i
  `/day-tripper/` (dos 404 benignes al build).
- **W2 (pàgina de mètrica)** no s'ha tocat: va després de la dada de Sondeig, com diu el brief.
- **Risc de mètode, per a la propera:** obrir el preview amb la configuració `web` de
  `.claude/launch.json` em va servir el `build/` **d'un altre arbre** (la porta vella, i `/comarca`
  en 404) tot i estar jo al worktree. És el risc #5 (recursos compartits entre agents) amb una cara
  nova: no el venv, sinó el servidor de preview. Se n'ha sortit servint el build d'aquest worktree en
  un port propi. **Verificar sempre que el que mires ve del teu arbre** — aquí es va veure perquè la
  ruta nova donava 404.
