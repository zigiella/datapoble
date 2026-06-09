# Mètode — Població, càrrega i turisme (model de 3 capes)

*L'indicador estrella de riusdegent: fer visible **com s'habita el territori** més enllà del padró. Redactat per Talaia. Pilot: Berguedà (31 municipis). **Tot el que diu aquí és inferència, no cens** — i es comunica així. Aquesta pàgina és la base de la **metodologia pública**.*

**Estat:** **v2 — model de 3 capes**, dissenyat, materialitzat a `mart_municipi` i validat sobre dades reals · 2026-06-06. Supera el v1 (una sola capa basada en residus).

---

## 1. El problema (i la volta de rosca que el resol)
El padró oficial **no veu** qui omple un municipi sense constar-hi. Però «qui l'omple» **no és una sola cosa**. En un poble molt turístic, l'augment de residus **no és població**: pot ser **excursionistes que vénen a passar el dia**. Anomenar-ho «població» seria fals.

Per això **no estimem un sol número, sinó tres capes** que separen fenòmens diferents: qui hi **dorm**, la **càrrega total**, i l'**activitat turística**.

## 2. Tres senyals físics independents
La idea de fons (el *cabal*): rastres administratius involuntaris revelen presència que cap cens captura. Triem tres que capten coses diferents:

| Senyal | Font | Què capta |
|---|---|---|
| **Residus** kg/hab/any | ARC | càrrega **TOTAL** (residents + 2a residència + qui pernocta + **excursionistes** + part de comerç) |
| **Elèctric domèstic** kWh/hab | ICAEN | qui hi **DORM** (l'excursionista de dia no fa servir l'electricitat de casa) |
| **Vidre** kg/hab/any | ARC (fracció) | activitat d'**hostaleria** (ampolles de bar/restaurant = visitants) |

## 3. Les tres capes
La **base** = generació/consum d'un resident "normal", calculada de les **viles de vall poc turístiques** (IETR < 5, ponderada per població):
`BASE_residus = 410 kg/hab` · `BASE_elèctric = 1.224 kWh/hab` · `BASE_vidre = 26,5 kg/hab`.

### L1 · Població real estimada (qui pernocta) — *la signatura «població invisible»*
```
poblacio_pernocta_est = round(padró × kWh_hab / 1224)
gap_pernocta = poblacio_pernocta_est − padró
```
El **gap** és la gent que **dorm** al territori sense constar al padró: residents no registrats, **segones residències**, turisme que pernocta. **Això sí que és «població».**

### L2 · Càrrega per residus  ·  i el denominador funcional
```
carrega_total_est     = round(padró × kg_residus_hab / 410)            # càrrega que suggereixen els residus
carrega_funcional_est = max(poblacio_pernocta_est, carrega_total_est)  # el sostre per governar
```
La pressió que **suggereixen els residus**, **inclosos els excursionistes de dia** i part del comerç. **NO en diem «població» — en diem «càrrega».** ⚠️ **No és un sostre:** la càrrega per residus pot quedar **PER SOTA de la pernocta (L1)** quan els residus/càpita són baixos, la recollida és atípica o la base està mal calibrada (passa a **16 dels 31** municipis del pilot; el nom «total» del passat era enganyós). Per **dimensionar serveis** (residus, aigua, neteja) s'usa la **càrrega funcional = max(L1, L2)**, i quan L1 > L2 es marca una **alerta de divergència**.

### L3 · Pressió turística (hostaleria)
```
index_turisme = z-score comarcal de (vidre_hab) → escala 0–100
```
Intensitat d'**activitat de visitants** (bars, restaurants, begudes). **No és població; és pressió turística.**

## 4. Validació — i un *catch* de rigor
Sobre dades reals 2024:

| Municipi | Padró | L1 pernocta | L2 càrrega | L3 turisme | Lectura |
|---|--:|--:|--:|--:|---|
| **Gósol** | 207 | **+87 %** | 535 | **100** | hi dorm molta gent (2a res.) **i** màxima hostaleria → poble turístic ple |
| **Castellar de n'Hug** | 166 | +31 % | 397 | 84 | vidre alt però menys pernocta → **el poble d'excursió de dia** |
| **Saldes** | 301 | +86 % | 681 | 71 | segona residència + hostaleria |
| **Berga** | 17.539 | ≈ 0 % | 19.626 | ~27 | capital: població de residents |

**El *catch*:** vam provar de fer la capa turística com a simple **resta** (càrrega − pernocta), però als extrems donava disbarats — a Berga sortia +2.454 (és **residu COMERCIAL** de botigues, no excursionistes) i a les viles de vall sortia negatiu (artefacte de bases). Per això la capa turística surt del **vidre** (senyal net d'hostaleria), **no de la resta**. *La rigor abans que la xifra bonica.*

## 5. Honestedat (innegociable)
- Tot és **inferència, no cens** → categoria `derived`, procedència **morada**, es comunica com a **rang**.
- **Lectura ecològica**: parla del municipi, mai de persones concretes.
- **Bandera de confiança** (`alta`/`mitjana`/`baixa`): **baixa** als micromunicipis (< 75 hab, soroll de denominador) i on els senyals **divergeixen**.
- *Caveats* per capa: l'**elèctric** està confós per la calefacció de llenya (muntanya); els **residus** de les viles porten comerç; el **vidre** és un *proxy* d'hostaleria.
- **Secret estadístic** als micromunicipis; tot i això, el vidre i l'elèctric hi sobreviuen.

## 6. Materialitzat (font de veritat)
A `mart_municipi`, declarat a `semantic/metrics.yml` i exposat al JSON web (PR #34):
`poblacio_pernocta_est`, `gap_pernocta`, `gap_pernocta_pct`, `carrega_total_est`, `index_turisme`, `vidre_hab`, `kwh_hab`, `confianca`. Bases parametritzables (vars dbt) → a escala Catalunya, **una base per comarca**.

## 7. Pendents honestos
- **Calibratge** amb un senyal extern conegut (algun estudi de població estacional real).
- **Restauració** (Idescat CCAE-56 oficial / OpenStreetMap *proxy*) com a 2n senyal d'hostaleria, encreuat amb el vidre.
- **Estacionalitat**: cap font ho dóna mensual × municipal ara (elèctric i residus són anuals) — pendent.
- **Escala Catalunya**: base residencial per comarca.

— Talaia 🌊
