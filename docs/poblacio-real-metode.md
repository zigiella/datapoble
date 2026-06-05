# Mètode — Població real estimada vs padró

*L'indicador estrella de riusdegent: fer visible la **població invisible** (qui omple el territori sense constar al padró). Mètode redactat per Talaia. Pilot: Berguedà (31 municipis). Tot el que diu aquí és **inferència**, no cens — i es comunica així.*

**Estat:** mètode validat sobre dades reals · materialització pendent (spec a §7) · 2026-06-05

---

## 1. Objectiu
Estimar la **presència humana real** d'un municipi (la gent que de debò l'habita i el carrega: residents registrats + no registrats + segones residències + estacionals) i comparar-la amb el **padró oficial**. La diferència és el **gap**: la població que el padró no veu.

## 2. El principi
La **generació de residus per habitant** és un termòmetre directe de presència: la gent genera escombraries de manera força uniforme pels dies que hi és. Si un municipi de 166 empadronats genera residus com si en tingués el doble, és que **n'hi ha el doble de presents**. Fórmula base:

```
presència_estimada = padró × (kg_residus_per_hab / BASE)
```

on `BASE` = generació per càpita d'un resident "normal". L'elecció de `BASE` és la decisió clau (§4).

## 3. Triangulació — la prova honesta (i una troballa)
Per no dependre d'un sol senyal, vam creuar **residus** amb **consum elèctric domèstic** (ICAEN, real, 2024, 31 munis). Resultat de correlació per càpita:

| Parell | Pearson |
|---|--:|
| residus/hab ↔ elèctric/hab | **0,43** |
| IETR ↔ elèctric/hab | 0,49 |
| % 2a residència ↔ elèctric/hab | 0,34 |

**Només coincideixen moderadament.** Un mètode ingenu que en fes la mitjana seria **erroni**. El perquè és real i interessant:
- **L'elèctric està confós per la calefacció:** a la muntanya es crema **llenya/gas** (no electricitat) → consum elèctric *baix* malgrat molta presència (p. ex. Castellar de n'Hug: residus altíssims, elèctric mitjà).
- **Soroll de denominador petit:** amb 44 empadronats (la Quar), un sol gran consumidor dispara el per càpita.

**Conclusió metodològica:**
- **Residus = senyal PRIMARI** (net, directe; ja validat r=0,87 amb l'IETR).
- **Elèctric = corroborador SECUNDARI**, amb *caveats*. El seu valor real: (a) **sobreviu al secret estadístic** fins i tot a Castellar (166 hab), i (b) quan **coincideix** amb els residus, apuja la **confiança**. No es pondera igual.

## 4. El càlcul i la base (dos talls)
Calculem `total_residus = 18.785.228 kg/any`, `padró_total = 41.523`.

**Tall A — relatiu (base comarcal, pop-ponderada = 452 kg/hab).** Mostra **qui acull més *dins* la comarca**. És robust però **suma zero** (el total es conserva = padró): redistribució espacial, no sub-recompte global.

**Tall B — absolut (base residencial).** Pren com a `BASE` la generació de les **viles de vall amb poc turisme** (IETR<5: Avià, Berga, Gironella, Puig-reig) = **410 kg/hab** (molt estable: amb IETR<12 surt 409). Això capta el **sub-recompte comarcal**:

| BASE (kg/hab) | Presència comarcal | vs padró |
|--:|--:|--:|
| 330 (residencial pur) | ~56.900 | **+37 %** |
| 360 | ~52.200 | +26 % |
| **410 (viles de vall, observat)** | ~45.800 | **~+10–13 %** |
| 452 (mitjana comarcal) | 41.560 | +0 % (degenerat) |

> **Lectura honesta:** la base 410 inclou Berga (capital comercial, els seus residus porten comerç) → és un **sostre de la base** i per tant un **terra del gap**. Conclusió defensable: el Berguedà sosté **com a mínim ~10 %, plausiblement ~15–25 %**, més gent de la que registra. La xifra exacta depèn de la base → es comunica com a **rang**, no com a decimal fals.

## 5. On viu el gap (pilot Berguedà)
No està repartit: es concentra a les **muntanyes turístiques**. Exemples (tall relatiu):

| Municipi | Padró | Presència est. | Gap |
|---|--:|--:|--:|
| Saldes | 301 | ~617 | +316 |
| Gósol | 207 | ~485 | +278 |
| Castellar de n'Hug | 166 | ~360 | +194 |
| Berga (vila) | 17.539 | ~17.500 | ~0 |

Exactament la tesi de *riusdegent*: el cabal humà s'acumula on el padró menys ho diu.

## 6. Honestedat (els guardrails, no negociables)
- És una **estimació/índex, no un cens**. Es marca com a **inferència** (procedència morada) i s'expressa com a **rang**.
- **Lectura ecològica:** mai sobre individus, sempre sobre el municipi.
- **Secret estadístic** als micro-munis; tot i així l'elèctric hi sobreviu i permet un senyal amb banda ampla.
- **Caveats explícits:** els residus inclouen part de comerç a les viles; un turista pot generar diferent que un resident; la base té incertesa. Tot va al peu de l'indicador.
- **Bandera de confiança:** alta quan residus + (elèctric o 2a residència) coincideixen; baixa quan divergeixen o el denominador és minúscul.

## 7. Materialització (spec per a Sondeig)
Afegir a `mart_municipi` (i declarar al `semantic/metrics.yml`, **visibilitat pública, categoria DERIVED**):

| Columna | Definició |
|---|---|
| `poblacio_real_est` | `round(poblacio * kg_hab_any / 410)` — tall absolut (base residencial) |
| `gap_abs` | `poblacio_real_est - poblacio` |
| `gap_pct` | `gap_abs / poblacio` |
| `poblacio_real_rel` | `round(poblacio * kg_hab_any / 452)` — tall relatiu comarcal (opcional, vista espacial) |
| `confianca` | `alta`/`mitjana`/`baixa` segons corroboració (regla a §6) |

Mètriques al contracte amb `label_ca/label_es`, `formula`, `font` (ARC residus + Idescat padró), `categoria: derived`, i un camp `caveat` amb el text d'incertesa. La `BASE=410` queda **documentada i parametritzable** (recalcular quan escalem a Catalunya, on cada comarca tindrà la seva base residencial).

## 8. Pendents
- **Calibratge** contra un senyal conegut (algun municipi amb estudi de població estacional real) per fixar la base amb evidència externa.
- A **escala Catalunya**: base residencial **per comarca** (no una de sola).
- Si apareix **elèctric mensual**, explotar l'estacionalitat (les 2es residències piquen a l'estiu) com a senyal de presència molt més net.

— Talaia 🌊
