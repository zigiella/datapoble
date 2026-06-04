# riusdegent · Guia de marca (1 pàgina)

**riusdegent · Dades per entendre com s'habita el territori**

**Autora:** Llegenda (direcció d'art) · **Vot final de marca:** Bea · **Review:** Talaia
**Data:** 2026-06-03 · **Estat:** **proposta de sortida per iterar** (segon encàrrec — primer PR d'identitat). El nom públic `riusdegent` **està tancat** (visió v3); el **dibuix** del logo, marca i favicon és proposta a refinar per un humà.

> Aquesta guia **aplica** el sistema de tokens (`tokens/tokens.json` · `tokens/tokens.css`); **no el redefineix**. Tot color/tipografia referencia un token existent.

---

## 1. El concepte — `riusdegent` = *rius de gent*

El cabal humà que travessa, omple o buida el territori. Metàfora **hidrogràfica**, coherent amb el món cartogràfic de l'equip (Talaia, Sondeig, Cabal, Brúixola, Mirador) i amb el gir de la visió v3: de *pressió* a *habitança* — presència **i** absència alhora.

La idea clau, i el que fa la marca única: **un riu creix i s'asseca**. La sobrepressió (segona residència, estacionals que omplen) i la despoblació (padró fantasma, els que marxen) són **el mateix fenomen vist als dos vessants d'una divisòria**. La marca ho dibuixa literalment.

---

## 2. La marca / símbol

Línies de **cabal** que travessen una **divisòria** vertical:
- **Vessant esquerre — el riu va ple:** traços continus i gruixuts (corrent, sobrepressió).
- **Vessant dret — el mateix riu s'asseca:** els traços s'aprimen i es trenquen en un **llit puntejat** (despoblació, padró buit).
- **La divisòria** (línia vertical terracota) és l'*aiguavés*: la línia que parteix les aigües i el patró "dos extrems" del territori (Castellar ↔ Berga).

Llegeix com aigua/corba de nivell a mida gran i com un glif net a mida favicon. **Fitxers:**
- `riusdegent-mark.svg` — marca sola, color, sobre clar.
- `favicon.svg` — marca simplificada dins contenidor slate (per a pestanya).

**Proposta a refinar (honestedat):** les corbes són Béziers a ull, no una retícula òptica tancada; els gruixos i l'espaiat de les línies demanen el polit d'un humà. La idea i el sistema de color són ferms; el traç és iterable.

---

## 3. El logotip (wordmark)

`riusdegent`, tot en minúscula, una sola paraula (és un domini i una veu de baix perfil, no un crit). Partició visual **`rius` | `degent`** per color, **sense espai**, perquè es llegeixi "rius de gent" sense trencar la paraula.

- **Tipografia:** **Inter** (token `--dp-font-sans`), pes **600**, *tracking* lleugerament negatiu (token `--dp-ls-tight`, −0,01em). Inter perquè és la veu de dada/UI del sistema, té cifres tabulars i diacrítiques catalanes completes.
- **Color clar:** `rius` en `--dp-neutral-900` (#1B212A) · `degent` en `--dp-teal-600` (#216262).
- **Color fosc:** `rius` en `--dp-neutral-50` · `degent` en teal clar (germà clar del teal de carena).
- **Tagline:** Inter 400, `--dp-neutral-600` (clar) / `--dp-neutral-300` (fosc).

**Versions entregades:**

| Fitxer | Ús |
|---|---|
| `riusdegent-logo.svg` | Principal, fons clar. |
| `riusdegent-logo-dark.svg` | Fons fosc (`--dp-neutral-950`). |
| `riusdegent-logo-mono.svg` | **Una sola tinta** (`currentColor`): premsa 1-tinta, segell, embossing, marca d'aigua. Hereta el color del context. |

**Àrea de respir:** mínim = l'alçada de la "x" del wordmark per tots quatre costats. **Mida mínima:** wordmark ≥ 110 px d'ample; per sota, usar només la marca/favicon.

---

## 4. Favicon

`favicon.svg` (64×64, contenidor arrodonit slate `--dp-neutral-900`, marca en teal clar + divisòria terracota clara per contrastar sobre fosc en qualsevol tema de pestanya). Verificat que rasteritza net.

**Per a ICO** (indicació, no generat aquí — cal una eina de raster):
```bash
# amb ImageMagick o rsvg-convert + png2ico; mides recomanades 16/32/48:
rsvg-convert -w 32 -h 32 favicon.svg -o favicon-32.png   # idem 16 i 48
magick favicon-16.png favicon-32.png favicon-48.png favicon.ico
```
Servir alhora: `<link rel="icon" type="image/svg+xml" href="favicon.svg">` + `favicon.ico` de *fallback*. **Pendent humà:** generar i versionar l'ICO.

---

## 5. Paleta (subconjunt de marca — referint tokens, **no redefinida**)

| Rol | Token | Hex |
|---|---|---|
| Tinta principal / text | `--dp-neutral-900` | #1B212A |
| Suport text/traç | `--dp-neutral-700` | #3C4756 |
| **Aigua / cabal (marca)** | `--dp-teal` / `--dp-teal-600` | #2A7B7B / #216262 |
| **Divisòria / detall humà** | `--dp-accent-500` | #C75D34 |
| Accent sobre fosc | `--dp-accent-300` | #E3A584 |
| Fons fosc (hero) | `--dp-neutral-950` | #10141A |

Les **paletes de dada** (seqüencial exposició, diverging, qualitativa) **no** són colors de marca: viuen a `cartography/palette.md` i només pinten mapes/charts. La marca no competeix amb el dada.

---

## 6. Tipografia (la del sistema)

- **`--dp-font-sans` Inter** — wordmark, UI, dada (cifres tabulars `--dp-font-feature-tnum`).
- **`--dp-font-serif` IBM Plex Serif** — lectura editorial llarga i **el paràgraf hero** (§8).
- **`--dp-font-mono` IBM Plex Mono** — codi, taula crua, captions tècnics.

Totes amb diacrítiques catalanes completes (à è é í ï ò ó ú ü ç l·l). Interlineat generós (`--dp-lh-relaxed` 1,6) perquè el català i el francès corren llargs.

---

## 7. To de veu

El del **geògraf honest** que t'ensenya on cau cada gota: **afirmatiu, sobri, territorial**. Diu el que sap i **marca el que no sap** (dada vs inferència vs resultat negatiu). Mai sensacionalista amb un tema sensible (segona residència, despoblació, política). Bilingüe natiu ca + es.

- **Sí:** "El cabal humà que travessa, omple o buida cada municipi." · "Font, data i fórmula visibles."
- **No:** alarmisme ("invasió turística"), *hype* de big data, promeses que l'observatori no compleix.

---

## 8. El paràgraf *hero* (tractament)

El paràgraf de Bea és el cor de la home:

> *Persones que arriben, marxen, tornen, pernocten, lloguen, compren, hereten, visiten, treballen, voten, ocupen places, omplen segones residències o desapareixen del padró real de la vida quotidiana.*

**Tractament proposat** (mockup: `hero-mockup.html`):
- **Serif editorial** (`--dp-font-serif`), cos gran (`--dp-fs-3xl`), interlineat `--dp-lh-snug`, sobre fons fosc `--dp-neutral-950`. És un paràgraf per **llegir**, no un titular cridat.
- **Ritme dels verbs:** els primers verbs de moviment — *arriben, marxen, tornen* — en **semibold terracota** (`--dp-accent-300`): són el pols del riu. La resta, en pes normal.
- **El gir final** — *"desapareixen del padró real de la vida quotidiana"* — en **itàlica teal clar**: l'absència, el riu que s'asseca. Tanca el paràgraf amb el concepte de marca.
- Subratllat per un *eyebrow* curt ("Observatori del territori") i una frase de suport que diu la tesi en una línia.

> El mockup és **referència visual**, no producte. **Mirador** l'implementa de veritat amb els tokens. El **vot sobre el tractament del hero és de Bea**.

---

## 9. Què és tancat vs proposta

- **Tancat:** el nom `riusdegent`, el tagline, el **concepte** hidrogràfic (riu que creix i s'asseca + divisòria), i que la marca **aplica** els tokens sense redefinir-los.
- **Proposta a refinar per un humà:** el **dibuix** fi del traç (corbes/gruixos a ull), el lockup exacte i l'espaiat, la generació de **l'ICO**, i el tractament del hero (subjecte al vot de Bea). Sóc una agent de codi: entrego SVG net i una identitat de sortida **creïble per iterar**, no un logo final polit d'estudi.

---

*Pendent: vot de marca de Bea · review de Talaia · polit humà del traç + ICO · (F2) integració a Mirador amb els tokens.*
