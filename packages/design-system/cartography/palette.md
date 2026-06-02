# Cartografia · Paleta coroplètica + classificació

**Autora:** Llegenda (direcció d'art) · **Frontera dada↔disseny:** acordat amb Talaia
**Data:** 2026-06-02 · **Estat:** proposta — pendent validació CVD i acord final de classificació amb Talaia

Aquest document és l'spec de **com es pinta el mapa** de l'observatori. Els hex viuen com a tokens
a `tokens/tokens.json` → `color.scale.*` i a `tokens/tokens.css` (`--dp-exposure-*`, `--dp-div-*`).
Aquí s'explica **quina paleta**, **per a quina mètrica**, i **amb quin mètode de classificació**.

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

## 3. Paleta DIVERGING — desviació respecte a la mitjana comarcal

**Per a:** mètriques amb **punt neutre** significatiu: `hab_per_hab` centrat a la mitjana comarcal,
residus centrats, o qualsevol "per sobre / per sota de la mitjana del Berguedà". El zero (mitjana)
ha de ser visualment neutre.

**7 passos, neutre al centre (índex 3).** Teal ↔ marró (tipus *BrBG* de ColorBrewer), **diverging
CVD-safe canònic**. El centre és gris-os, **mai verd brillant** (per no xocar amb vermell en CVD).

| Pas | Hex | Token | Significat |
|---:|---|---|---|
| 0 | `#01665E` | `--dp-div-0` | molt per sota de la mitjana |
| 1 | `#5AB4AC` | `--dp-div-1` | |
| 2 | `#C7EAE5` | `--dp-div-2` | |
| 3 | `#F5F5F0` | `--dp-div-3` | **neutre (≈ mitjana)** |
| 4 | `#DFC27D` | `--dp-div-4` | |
| 5 | `#BF812D` | `--dp-div-5` | |
| 6 | `#8C510A` | `--dp-div-6` | molt per sobre de la mitjana |

- Usar diverging **només** quan el punt mitjà tingui sentit. Per a magnituds pures (IETR), seqüencial.

---

## 4. Sense dada / secret estadístic

- Token `--dp-nodata` = `#E3E3DE`, **renderitzat amb tramat diagonal (hatch)**, no com a farciment pla.
- S'aplica a municipis amb secret estadístic (Castellar en encreuaments fins) o sense valor per a la
  mètrica. La llegenda inclou sempre l'entrada "sense dada / no disponible".

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

| Mètrica | Mètode recomanat | Per què |
|---|---|---|
| **IETR (0-100)** | **Cuantils (5-6 classes)** | Ja és relatiu a la distribució; cuantils dóna lectura de rànquing robusta i omple la rampa. Casa amb `IETR_rank`. |
| `kg_hab_any`, `pct_noprincipal`, `rtc_per_1000hab` | **Jenks (natural breaks), 5 classes** | Hi ha *gaps* naturals reals (l'outlier Castellar). Jenks respecta els salts i evita que un extrem aixafi la resta en una sola classe. |
| Diverging (desviació) | **Talls simètrics al voltant de la mitjana** (no cuantils) | El neutre ha de coincidir amb el zero; cuantils desplaçaria el centre. |

### Regla general acordada
- **Per defecte: Jenks de 5 classes** per a magnituds amb cua (la majoria d'aquest pilot), perquè
  els *natural breaks* són honestos amb un territori on hi ha extrems reals (el patró "dos extrems"
  Castellar↔Berga del brief).
- **Cuantils** per a índexs ja normalitzats (IETR) i quan l'objectiu és **comparar rànquing**.
- **Mai** *equal interval* amb aquestes distribucions: l'outlier deixaria 28 municipis al primer color.
- **Sempre** a la llegenda: nom del mètode + nº de classes + que els talls poden canviar si entren
  més municipis (l'escala a Catalunya, ~947, recalcularà breaks → documentar-ho).
- **Coherència temporal:** si es comparen dos anys, **fixar els talls** del primer perquè el color
  sigui comparable entre mapes (si no, el mateix color voldria dir coses diferents).

> Decisió oberta per a Talaia: confirmar **5 vs 6 classes** com a estàndard. Jo proposo **5** per a
> Jenks (llegibilitat en municipi petit) i **6** quan s'usi la rampa completa en IETR.

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
- [ ] Confirmar amb Talaia **5 vs 6 classes** i el mètode per defecte definitiu.
- [ ] Mockup del mapa del prototip re-acolorit amb aquesta paleta (DoD de la spec) — el munta Mirador
      amb aquests tokens; jo entrego l'spec i els hex.
- [ ] Estil MapLibre complet (basemap apagat, etiquetes en català, relleu de muntanya) → F2.
