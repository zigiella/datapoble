# Cartografia · Paleta coroplètica + classificació

**Autora:** Llegenda (direcció d'art) · **Frontera dada↔disseny:** acordat amb Talaia
**Data:** 2026-06-02 · **Actualitzat:** 2026-06-06 (DA final ronda 2: divergent «gap» `--dp-div2`, aprovada per Bea)
**Estat:** classificació **acordada** · **pendent** validació CVD de les rampes (§7)

Aquest document és l'spec de **com es pinta el mapa** de l'observatori. Els hex viuen com a tokens
a `tokens/tokens.json` → `color.scale.*` i a `tokens/tokens.css` (`--dp-exposure-*`, `--dp-div2-*`,
`--dp-cat-*`). Aquí s'explica **quina paleta**, **per a quina mètrica**, i **amb quin mètode de
classificació**.

> **Canvi DA final ronda 2 (Bea):** la divergent del **gap** és ara **`--dp-div2-0…6`** (teal↔**porpra**),
> que substitueix l'ús de la BrBG `--dp-div-*` al render. La porpra lliga amb `--dp-prov-derived`
> (inferència). Vegeu §3 i la **taula indicador→paleta** (§5 bis). El **color de marca** passa a ocre
> (`--dp-brand`); les paletes de dada **no** són marca.

---

## 1. Principis

1. **El dada resalta, el mapa s'apaga.** Basemap desaturat (tokens `--dp-map-*`); el color viu només
   on hi ha valor. El mapa no és decoració, és la lectura.
2. **Perceptualment ordenat.** Més fosc/saturat = més valor, de forma monòtona. Cap salt de to que
   inverteixi la lectura. La rampa segueix una lluminositat estrictament decreixent.
3. **Segur per a daltonisme.** Cap codificació que depengui de **vermell↔verd**. Famílies terra
   (groc→marró) per a seqüencial; teal↔marró per a diverging (evita el parany vermell-verd).
4. **El color comunica el mètode.** La llegenda diu sempre **quin mètode de classificació** s'ha
   usat i amb **quants talls**; canviar de mètode canvia el missatge, així que es fa explícit.
5. **Honestedat amb el "sense dada".** Castellar i els micromunicipis tenen **secret estadístic** i
   ràtios inestables (denominador diminut). El "sense dada" no es pinta pla: va amb **tramat (hatch)**
   sobre `--dp-nodata` perquè no es confongui amb un valor baix.

---

## 2. Paleta SEQÜENCIAL — "exposició / pressió" (la principal)

**Per a:** `IETR` (0-100), `kg_hab_any`, `pct_noprincipal`, `rtc_per_1000hab`, `pct_icaen_EFG`,
`hab_per_hab` quan es llegeix com a magnitud (no com a desviació). Totes són **una direcció**:
més = més pressió/exposició.

**6 passos, clar→fosc = baix→alt.** Família terra càlida (tipus *YlOrBr* de ColorBrewer, ajustada
al mood de muntanya). To gairebé monòton, lluminositat decreixent → ordre llegible també en escala
de grisos i en visió daltònica.

| Pas | Hex | Token | Significat |
|---:|---|---|---|
| 0 | `#FBF3D9` | `--dp-exposure-0` | molt baix |
| 1 | `#F3D9A0` | `--dp-exposure-1` | baix |
| 2 | `#E8B567` | `--dp-exposure-2` | mitjà-baix |
| 3 | `#D98B3E` | `--dp-exposure-3` | mitjà-alt |
| 4 | `#B5612A` | `--dp-exposure-4` | alt |
| 5 | `#7E3A1E` | `--dp-exposure-5` | molt alt |

- **Per què groc→marró i no un viridis:** viridis (lila→groc) és impecable en CVD i és la reserva
  tècnica, però el seu lila no encaixa amb el registre "muntanya, teula, pedra" de la marca. El
  groc→marró manté la seguretat CVD (no toca el vermell-verd) i parla el llenguatge del territori.
  Si en la validació algun pas falla per a **tritanòpia** (els passos clars 0-1 són els de risc), la
  reserva és substituir la rampa per **viridis** de 6 passos sense tocar res més del sistema.
- **Fons:** dissenyada per llegir-se sobre el `land` apagat (`#F2F1EC`) i sobre blanc-os.

---

## 3. Paleta DIVERGING «gap» — desviació amb centre 0 (la del gap població)

**Per a:** mètriques amb **punt neutre** significatiu: **`gap_pct`** (població real estimada vs padró)
com a cas principal, i qualsevol saldo / "per sobre / per sota de la mitjana comarcal". El zero
(gap 0 ≈ mitjana) ha de ser visualment neutre.

**7 passos, neutre al centre (índex 3).** **Teal ↔ PORPRA** (DA final ronda 2, aprovada per Bea).
El centre és os/neutre, **mai verd brillant** (per no xocar amb vermell en CVD). Els dos pols tenen
**significat semàntic**:
- **Teal** (`--dp-div2-0..2`) = **menys gent que el registre** (el padró sobreestima).
- **Porpra** (`--dp-div2-4..6`) = **població que el padró no veu** → és **inferència**, i per això la
  porpra **lliga amb `--dp-prov-derived`** (#7A5BA6): el color recorda que aquest costat és estimació.

| Pas | Hex | Token | Significat |
|---:|---|---|---|
| 0 | `#0F6E66` | `--dp-div2-0` | molt per sota (teal fort · menys gent que el registre) |
| 1 | `#4FA8A0` | `--dp-div2-1` | |
| 2 | `#B9DED9` | `--dp-div2-2` | |
| 3 | `#EFEEE8` | `--dp-div2-3` | **neutre (≈ mitjana · gap 0)** |
| 4 | `#CDB3DD` | `--dp-div2-4` | |
| 5 | `#9466B6` | `--dp-div2-5` | |
| 6 | `#5E3A86` | `--dp-div2-6` | molt per sobre (porpra fort · població que el padró no veu) |

- Usar diverging **només** quan el punt mitjà tingui sentit. Per a magnituds pures (IETR, % no
  principal, est/1000, residus), **seqüencial** (§2).
- **Classificació:** **talls simètrics al voltant de 0** (no cuantils), perquè el neutre coincideixi
  amb el zero. Per defecte **5 classes** (vegeu §5). El render del gap mostra els talls reals (p. ex.
  −21 %…+176 % al pilot).

### 3 bis. Diverging BrBG — LLEGAT (`--dp-div-*`)
La divergent anterior teal↔marró (tipus *BrBG* de ColorBrewer) **es conserva al contracte** com a
llegat (`--dp-div-0..6`, neutre=3) per a mètriques amb neutre que encara la facin servir, però el
**render del gap usa `--dp-div2-*`**. Hex: `#01665E #5AB4AC #C7EAE5 #F5F5F0 #DFC27D #BF812D #8C510A`.

---

## 4. Estats d'honestedat: «sense dada» i «confiança baixa»

Dos estats diferents, **diferenciats per textura (no només color)** — CVD-safe — i sempre a la llegenda:

- **Sense dada / secret estadístic** → token `--dp-nodata` `#E3E3DE`, **renderitzat amb tramat diagonal
  (hatch)**, **mai farciment pla**. S'aplica a municipis amb secret estadístic (Castellar en
  encreuaments fins, Gisclareny) o sense valor per a la mètrica. La llegenda inclou sempre l'entrada
  "sense dada / no disponible".
- **Confiança baixa (estimació feble)** → **es manté el color de la rampa** (el valor existeix), però
  **velat amb un puntejat** (radial dots) i un contorn discontinu: el «**llit sec**» de la marca.
  S'aplica a municipis amb estimació inestable (N petit, denominador diminut): el color es llegeix,
  però la textura avisa que la xifra és tova. *Mai* s'amaga el valor; es **qualifica**.

> **Regla d'una línia (per a la llegenda i per a Mirador):**
> **sense dada = tramat gris (mai farciment pla); confiança baixa = color de la rampa velat amb puntejat.**

---

## 5 bis. Taula **indicador → paleta** (lliurable clau de la DA final)

Cada visualització fa servir **una** paleta; **mai es barreja magnitud amb desviació**. La paleta
comunica el mètode. Aquesta és la correspondència canònica (espill del selector de `/mapa`):

| Indicador | Tipus de dada | Paleta | Tokens | Classificació |
|---|---|---|---|---|
| **Gap població (%)** (`gap_pct`) | desviació · centre 0 | **Divergent «gap»** | `--dp-div2-0…6` (neutre=div2-3) | simètrica al voltant de 0 · 5 classes |
| Població real estimada | magnitud | Seqüencial «terra» | `--dp-exposure-0…5` | Jenks · 5 classes |
| IETR (0–100) | índex normalitzat | Seqüencial «terra» | `--dp-exposure-0…5` | cuantils · 5 classes |
| % habitatge no principal | magnitud | Seqüencial «terra» | `--dp-exposure-0…5` | Jenks · 5 classes |
| Establiments / 1000 hab | magnitud (ràtio) | Seqüencial «terra» | `--dp-exposure-0…5` | Jenks · 5 classes |
| Residus kg/hab/any | magnitud | Seqüencial «terra» | `--dp-exposure-0…5` | Jenks · 5 classes |
| *(categòric, p. ex. candidatura)* | categoria sense ordre | Qualitativa | `--dp-cat-1…8` (Okabe-Ito) | — *(no sense acord amb Bea)* |

- **Divergent** ⇒ només quan hi ha un **centre 0** amb sentit (gap, saldo, vs comarca). Porpra =
  inferència (lliga amb `--dp-prov-derived`).
- **Seqüencial** ⇒ magnitud ordenada (clar→fosc = baix→alt).
- **Qualitativa** ⇒ categories sense ordre; **mai** color polític partidista sense acord (tema sensible).

---

## 5. Classificació: **cuantils vs Jenks** — recomanació

Aquesta és la decisió que **acordo amb Talaia** (el color comunica el mètode). La meva recomanació,
basada en com són les dades reals del pilot (`docs/data-sources.md`):

### Context de les dades
- **N petit i comarcal:** ~31 municipis del Berguedà (escala correcta segons data-sources §1.6).
- **Distribucions molt esbiaixades amb outlier clar:** Castellar (166 hab) té **1,66 habitatges/hab**
  i **~181 establiments/1000 hab** (~69× Berga). `pct_noprincipal` 74,3% a Castellar vs molt menys
  a la resta. Són distribucions de cua llarga amb un o dos extrems.
- **L'IETR ja ve normalitzat 0-100** respecte a la distribució (min-max winsoritzat).

### Recomanació per mètrica

| Mètrica | Mètode acordat | Per què |
|---|---|---|
| **IETR (0-100)** i índexs normalitzats | **Cuantils, 5 classes** | Ja és relatiu a la distribució; cuantils dóna lectura de rànquing robusta i omple la rampa. Casa amb `IETR_rank`. |
| `kg_hab_any`, `pct_noprincipal`, `rtc_per_1000hab` i magnituds crues | **Jenks (natural breaks), 5 classes** | Hi ha *gaps* naturals reals (l'outlier Castellar). Jenks respecta els salts i evita que un extrem aixafi la resta en una sola classe. |
| Diverging (desviació) | **Talls simètrics al voltant de la mitjana** (no cuantils) | El neutre ha de coincidir amb el zero; cuantils desplaçaria el centre. |

### Regla general acordada (decisió de Talaia, 2026-06-04)
- **Per defecte: 5 classes**, sigui quin sigui el mètode. És l'estàndard del sistema (llegibilitat en
  municipi petit; la rampa de 5 trams és inequívoca a la pestanya i a la llegenda).
- **Mètode per mètrica:**
  - **Cuantils** per a **índexs normalitzats** (IETR i derivats): ja són relatius a la distribució i
    l'objectiu és **comparar rànquing**.
  - **Jenks (natural breaks)** per a **magnituds crues** (`kg_hab_any`, `pct_noprincipal`,
    `rtc_per_1000hab`…): els *natural breaks* són honestos amb un territori d'extrems reals (el patró
    "dos extrems" Castellar↔Berga del brief) i eviten que un *outlier* aixafi la resta.
- **La rampa seqüencial conserva 6 stops** (`--dp-exposure-0..5`) com a **recurs de color** (escala
  contínua, *swatches*, casos amb 6 trams si mai calen). El **render coroplètic per defecte usa 5
  classes**: es prenen 5 mostres de la rampa, no els 6 stops literals.
- **Mai** *equal interval* amb aquestes distribucions: l'outlier deixaria ~28 municipis al primer color.
- **Sempre** a la llegenda: **mètode + nº de classes + font·data** de la mètrica (contracte: cap número
  sense procedència). Indicar també que els talls poden canviar si entren més municipis (l'escala a
  Catalunya, ~947, recalcularà *breaks* → documentar-ho).
- **Coherència temporal:** si es comparen dos anys, **fixar els talls** del primer perquè el color
  sigui comparable entre mapes (si no, el mateix color voldria dir coses diferents).

### Decisió C de Bea (DA final ronda 2) — reconciliació
Bea va aprovar com a **per defecte**: **«Jenks 5 (gap) / seqüencial la resta»**. Es concreta així,
coherent amb §3 i la taula §5 bis:
- **Gap (`gap_pct`)** → paleta **divergent `--dp-div2`** amb **5 classes**. El càlcul de talls és
  **simètric al voltant de 0** (no Jenks pur ni cuantils): el neutre ha de coincidir amb el zero. La
  llegenda del prototip ho mostra com «divergent (centrat en 0) · 5 classes» amb els talls reals.
  *(L'etiqueta «Jenks 5» de Bea és la consigna de 5 classes; el mètode honest per a una divergent amb
  centre 0 és el tall simètric.)*
- **La resta** → **seqüencial `--dp-exposure`**, **5 classes**: **Jenks** per a magnituds crues,
  **cuantils** per a índexs normalitzats (IETR). Tot 5 classes per defecte.

---

## 6. Llegenda (requisits visuals)

- Orientació horitzontal a sota/lateral del mapa; cada tram amb el seu **rang numèric** (cifres
  tabulars, `--dp-font-feature-tnum`), no només el color.
- Capçalera amb **mètode i nº de classes** ("Jenks · 5 classes") i la **font·data** de la mètrica
  (contracte semàntic: cap número sense procedència).
- Entrada explícita de **"sense dada"** amb el tramat.
- Estats de mapa (detall a F2): *hover* (contorn `--dp-map-label`), selecció (`--dp-map-highlight`),
  i el patró **"dos extrems"** ressaltant Castellar i Berga alhora.

---

## 7. Pendent (honest)

- [ ] **Validació CVD real** (protan/deuteran/tritan) de la rampa seqüencial amb simulador — ara és
      proposta basada en principis i en famílies de referència (ColorBrewer/Okabe-Ito), **no verificada**
      pas a pas en aquest encàrrec.
- [x] ~~Confirmar amb Talaia **5 vs 6 classes** i el mètode per defecte~~ → **tancat (2026-06-04):**
      5 classes per defecte; cuantils per a índexs normalitzats, Jenks per a magnituds crues; la rampa
      manté 6 stops com a recurs de color (render per defecte 5 classes). Veure §5.
- [ ] Mockup del mapa del prototip re-acolorit amb aquesta paleta (DoD de la spec) — el munta Mirador
      amb aquests tokens; jo entrego l'spec i els hex.
- [ ] Estil MapLibre complet (basemap apagat, etiquetes en català, relleu de muntanya) → F2.
