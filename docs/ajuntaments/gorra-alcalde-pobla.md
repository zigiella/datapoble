# La gorra de l'alcalde de la Pobla — selecció de KPIs del mode govern

**Annex operatiu del contracte C6** (que fixava «~12 KPIs» sense triar-los). Escrit per Talaia amb els
números reals del repo al davant, no d'intuïció abstracta. **Estat: proposta — vot narratiu de Bea.**
**Restricció nova (decisió de Bea, 2026-07-16):** v1 va **només amb dades públiques**. Les dades
internes de l'Ajuntament són **fase 2** — primer ensenyem valor, després demanem. C2 queda com a
contracte llest i dorment; D3 i D6 es difereixen.

---

## 1. La troballa incòmoda, primer (perquè condiciona tot el disseny)

**La Pobla és l'únic municipi oficial del Berguedà (1 de 9) on l'ETCA cau FORA de la nostra banda.**

| | valor |
|---|---|
| Padró | 1.106 |
| **La nostra estimació** | **852** · banda [726, 1.037] |
| **ETCA oficial (Idescat)** | **1.121** — **fora de la banda** |
| Desviació de la nostra estimació vs l'oficial | **−24%** |
| A més | 852 és el **número col·lidit** amb Guardiola de Berguedà |

*(Verificat: `pernocta-catalunya.json` → `dins_banda: false`; és l'únic dels 9 oficials del Berguedà.)*

**DECISIÓ DE BEA (2026-07-16, ratificada sobre aquesta troballa): EL MODEL S'APARCA per a aquest
track.** El mode govern treballa **només amb dades oficials i consolidades** (padró, ETCA on existeix,
atur SEPE, renda, cens d'habitatges, RTC, residus, energia…). La nostra estimació de pernocta **no
surt al mode govern** — ni com a titular ni com a secundària. On no hi ha dada oficial de presència
(pobles <1.000, sense ETCA), el tauler diu **«sense dada oficial»** — el gest honest de sempre, ara
sense model pel mig. El model i la seva doctrina queden vius a l'experiment (geo-rag, annex de
recerca) i a la resta del web fins que es decideixi el contrari; **aquí, aparcat**.

## 2. El poble, vist des de la gorra (no el que jo suposava)

Jo esperava la història del «poble que es buida entre setmana i s'omple el cap de setmana». **No és
la de la Pobla:** el padró (1.106) i l'ETCA oficial (1.121) **pràcticament coincideixen** (+1,4%).
La història real, amb els rangs comarcals contra els 31:

| Fet | Valor | Rang | Què vol dir |
|---|---|---|---|
| **Envelliment** | **407,1** | **6/31** | **4 persones grans per cada jove.** El número que mana. |
| **Habitatge no principal** | **52,07%** | 10/31 | **515 de 989 cases** sense ningú vivint-hi tot l'any |
| Padró | 1.106 | 8/31 | dels més grans entre els petits |
| Renda neta | 16.343 € | 19/31 | per sota del mig de la comarca |
| Població estrangera | 9,58% (+5,61 a la finestra) | 6/27 | **l'única entrada de gent nova** |
| Densitat | 21,5 hab/km² | 9/31 | |
| Serveis | 14,5 / 1.000 hab | 10/31 | |
| Residus | 458 kg/hab/any | 24/31 | dels que menys en generen |

**La frase que un alcalde entendria:** *la Pobla no és un poble que va i ve — és un poble que
envelleix amb la meitat de les cases tancades, i l'única gent nova que hi entra ve de fora d'Espanya.*
Aquestes dues coses (envelliment + estoc d'habitatge buit) **es toquen**: hi ha cases, però no
s'hi queda gent jove.

## 3. Els KPIs (12), triats per DECISIÓ que suporten

Cap KPI hi és perquè el tinguem. Cada un respon a una cosa que l'alcalde pot fer.

**A · Qui hi ha (i qui hi haurà)**
1. **Índex d'envelliment** (407,1 · 6/31) — *decisió: escola, serveis a la gent gran, ¿el poble té relleu?*
2. **Padró + tendència** (1.106 · 8/31) — *decisió: la base de finançament; ¿puja o baixa?*
3. **Nova població / origen divers** (9,58% · +5,61) — *decisió: acollida i arrelament; és l'única entrada de gent nova.* ⚠️ **Nota narrativa VINCULANT (Bea, 2026-07-16): aquest indicador es tracta amb cura.** El marc és **renovació demogràfica** (qui fa possible que el poble tingui futur), mai «pressió» ni cap marc problematitzant; l'etiqueta pública, el text de la fitxa i qualsevol frase del xat sobre aquest KPI passen pel **vot narratiu de Bea** abans de publicar-se.
4. **Presència oficial ETCA** (1.121) — *decisió: dimensionar serveis.* **Només la dada oficial** (§1: model aparcat). Als municipis <1.000 (sense ETCA): **«sense dada oficial»**, honest i sense substitut.

**B · Les cases (el nus)**
5. **% habitatge no principal** (52,07% · 10/31) — *decisió: política d'habitatge; 515 cases són estoc mort o segona residència.*
6. **Habitatges d'ús turístic (RTC)** (24 de 31 registres) — *decisió: quanta de l'ocupació no-principal és turisme reglat.*
7. **Índex de turisme** (66,4 · 17/31) — *decisió: pressió vs oportunitat.*

**C · El pols i l'economia**
8. **Atur registrat mensual** (D1, SEPE) — *decisió: l'únic número que es mou cada mes; el pols del poble.* ⚠️ Amb la **doctrina del «<5»** (interval [1,4], mai zero) — a la Pobla és probable que hi surti.
9. **Renda neta per persona** (16.343 € · 19/31) — *decisió: quines convocatòries per renda baixa l'apliquen.*
10. **Establiments de serveis i restauració** (16 + 7) — *decisió: ¿el poble té on comprar i on menjar?*

**D · Els diners i el que gastem**
11. **Radar de subvencions** (track R) — *decisió: l'acció. Diners que entren.*
12. **Licitacions** (ja existent) + **residus/energia per habitant** (458 kg · 1.375 kWh) — *decisió: contractes i despesa.*

## 4. El que NO hi posem (i per què)

- **La nostra estimació de presència com a titular** — §1. Hi és, amb avisos, mai al capdamunt.
- **IETR i família** — ja retirats del públic (`glossari` §HIDDEN); un índex compost no és una decisió.
- **`confianca_score`, `divergencia_senyals`, `*_base_ratio`, `bretxa_naturalitzacio`** — diagnòstics interns nostres, no del poble.
- **`poblacio_real_est` / `poblacio_real_rel`** — model d'una capa antic, ja ocult; duplicaria el gap.
- **`carrega_funcional_est`** — duplicat de `carrega_total_est` per a la Pobla (1.237 tots dos).
- **Res electoral** — capa 🔴, no es toca ni es creua.

## 5. RESOLT (Bea, 2026-07-16) + el pas a multi-municipi

**Camí triat: cap dels tres — el model s'aparca** (§1) i el tauler va només amb dades oficials.
**Els 12 KPIs: aprovats** (amb la nota narrativa del KPI 3).

**Multi-municipi des d'ara.** El disseny ja ho suporta (un perfil YAML per poble; el mode govern és
la mateixa fitxa per a tothom). Cobertura verificada dels 12 KPIs als primers candidats — completa
a tots; el que canvia per mida:

| | Pobla | Castellar de n'Hug | Guardiola | Gósol | Berga | Avià |
|---|---|---|---|---|---|---|
| Padró | 1.106 | 166 | 962 | 207 | 17.539 | 2.263 |
| ETCA oficial | 1.121 | **no existeix** | 1.005 | **no existeix** | 17.057 | 1.990 |
| Envelliment | 407 | 467 | 287 | 311 | 182 | 168 |
| % no principal | 52% | **74%** | 41% | **68%** | 24% | 26% |

- Als **<1.000** (Castellar, Gósol): presència = «sense dada oficial»; l'**atur SEPE sortirà sovint
  «<5»** (interval [1,4], doctrina C1) — el tauler petit és més silenci honest, i està bé que es vegi.
- ⚠️ **Gósol és província de LLEIDA (ine5 25100)** tot i ser Berguedà — el filtre «província=8» de la
  spec D1 **el perdia en silenci**; esmenat: el filtre és per `BERGUEDA_INE5` (els 31), i el test de
  la trampa de codis incorpora Gósol.
- **El radar segueix actiu NOMÉS a la Pobla** (porta C4 intacta): multi-municipi al dashboard ≠
  multi-perfil actiu al radar. Escalar el radar = activar perfils, després de la porta.
