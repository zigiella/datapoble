# Document d'analista — Escala a Catalunya · Nivell C

> Document VIU. L'analista (Talaia, carril dades / domini Sondeig) hi va acumulant **troballes** i
> **decisions** a mesura que avança la calibració de la presència real a escala de Catalunya.
> Carril dades EN SILENCI: res d'això es publica al web fins que un tipus passi el go/no-go.
> Última actualització: **2026-06-15**.

---

## 1. Objectiu i context

Escalar l'indicador de **presència real** (la «gent que el padró no veu») del pilot Berguedà a
tot Catalunya. El model de 3 capes estima presència a partir de senyals físics per càpita:

    presència_estimada = padró × (senyal/hab) / BASE

amb `BASE` = el consum/generació d'un resident «normal». Al Berguedà la base és endògena
(elèctric **1.224** kWh/hab, residus **410** kg/hab, de viles de vall poc turístiques). **El repte
de l'escala:** aquesta base única NO val per a tot Catalunya. Aquest document mesura QUANT falla i
construeix la correcció (**Nivell C**: esperats per covariables + bandes d'incertesa).

**Validació externa:** ETCA/EPE d'Idescat (població estacional equivalent, base 2021, munis ≥1.000
hab). **Go/no-go (decisió Bea 2026-06-11):** publicar presència ABSOLUTA només si el tipus valida
amb ρ≥0,7 i error≤15%; si no, índexs/rangs relatius + «encara no ho mesurem prou bé aquí».

**Arquitectura (disseny `bitacora/2026-06-11_pas4-bases-etca-disseny_talaia.md`):**
- **Nivell A** — bases oficials CAT com a alarma (no per estimar).
- **Nivell B** — classificador `tipus_territorial` (QUÈ és el municipi; estructura estable).
- **Nivell C** — esperats per regressió amb covariables NO de presència + indicador d'excés +
  banda p10–p90. ← **objecte d'aquest document.**

---

## 2. Registre de troballes (cronològic)

### T1 · La base única falla per tipus (2026-06-15, 9 munis Barcelonès+Tarragonès) — #130
Primera mesura amb senyals reals (elèctric ICAEN + residus ARC) i error vs ETCA:
- **metropolita_dens −25%**, **litoral_metropolita −15%** (la base infraestima: el resident urbà
  gasta menys llum domèstica, pisos petits).
- **litoral_vacacional MIXT** (−17% Salou … +18% Cambrils).
- Direcció consistent dins del tipus → el tipus és un pivot raonable; però N=2-4 massa petita.

### T2 · La base per tipus centra però NO estreny (2026-06-15, N~80 Baix Llobregat+Maresme) — #132
Ampliada la mostra (anàlisi dirigida per comarca) + covariable RTC + tipus `corona_metropolitana`:
- El tipus correlaciona amb el biaix (ρ 0,92–1,0) i una **base per tipus centra** cada grup (error
  medià baixa molt), PERÒ **queda molta dispersió DINS del tipus** (residual màx 20–48%) → una base
  sola per tipus no posa tothom sota el 15%.
- **RTC places/resident NO explica** net el residual del vacacional (l'elèctric domèstic no veu els
  hostes d'hotel; l'ETCA és mitjana anual) → l'estacionalitat vol dada de **pic**, no aquest proxy.
- `interior_rural` (n=39) surt **contaminat** amb exurbis metropolitans → el classificador necessita
  les llistes oficials senceres (AMB/costaners/corona).

### T3 · La densitat (contínua) bat les bases discretes (2026-06-15, N=91) — #133
Regressió de la base per persona present (calibrada a l'ETCA) sobre covariables contínues:

| estratègia de base | R² | \|err\| medià | cobertura ±15% | banda p10/p90 |
|---|--:|--:|--:|--:|
| única (1.224) | — | 19,1% | 45% | [−17, +42] |
| per tipus (mediana/tipus) | — | 12,2% | 55% | [−21, +22] |
| **~ log10(densitat)** | 0,29 | 11,9% | **69%** | [−23, +21] |
| ~ log10(densitat) + altitud | 0,30 | 11,0% | 68% | [−22, +21] |

- **La regressió contínua per densitat BAT les dues bases discretes** (cobertura 69% vs 55% vs 45%):
  el biaix «per tipus» és, en realitat, un **efecte continu de densitat** (`base = 2101 − 239·log10(dens)`;
  densitat ×10 ⇒ −239 kWh/persona). Físicament coherent: pisos densos = menys elèctric/persona.
- **Però R²=0,29:** la densitat sola explica un terç de la variació → la **banda p10–p90 (~±20%)** és
  ampla. Cal més covariables per estrènyer.
- Residual del model per tipus: **litoral_metropolita 100%** dins ±15% (publicable), metropolita_dens
  i corona 75%, litoral_vacacional 60%, interior_rural 67%.
- L'altitud quasi no aporta (R² 0,29→0,30) i té signe contraintuïtiu → model **densitat sola**.

**Conclusió de l'estat:** el camí del disseny (covariables contínues + banda) es confirma. Amb una
sola covariable (densitat) ja superem la base única i la base per tipus; per arribar a cobertura
publicable (≈≥85% dins ±15%) calen covariables addicionals (renda, mix de calefacció) i tractar
l'estacionalitat del litoral a part.

---

## 3. Registre de decisions

| # | Data | Decisió | Per qui |
|--:|---|---|---|
| D1 | 2026-06-11 | Carril dades EN SILENCI (offline, no publicat fins go/no-go) | Bea |
| D2 | 2026-06-11 | Go/no-go = ρ≥0,7 i error≤15% per a presència absoluta | Bea |
| D3 | 2026-06-15 | Recalibració ràpida de base per tipus (provisional) | Bea |
| D4 | 2026-06-15 | Ampliar mostra comarca a comarca **i** provar covariable d'estacionalitat | Bea |
| D5 | 2026-06-15 | Construir la regressió contínua + bandes p10–p90 ara | Bea |
| D6 | 2026-06-15 | Afegir tipus `corona_metropolitana` (AMB no densa ≠ dens urbà) | Talaia |
| D7 | 2026-06-15 | Model Nivell C = densitat sola (altitud no aporta; parsimònia) | Talaia |

---

## 4. Eines i artefactes (interns, no publicats)

- `tools/nivellc_analisi.py` — dirigit per comarca; baixa senyals (ICAEN/ARC) + RTC + ETCA + EMEX,
  estima amb la base única, mesura error per tipus i recalibra base per tipus.
  → `data/territorial/nivellc_analisi.csv`, `data/territorial/nivellc_bases_tipus.csv`.
- `tools/nivellc_regressio.py` — ajusta la base per persona ~ log10(densitat) (OLS numpy), compara
  amb base única i per tipus, dona bandes p10–p90 i residual per tipus.
  → `data/territorial/nivellc_regressio.csv`.
- Bitàcola de detall: `bitacora/2026-06-15_nivellc-analisi-error-tipus_talaia.md`.
- Comarques cobertes (N=91 amb ETCA): Berguedà, Barcelonès, Tarragonès, Baix Llobregat, Maresme.

---

## 5. Pendents / següents passos

1. **Més covariables** per estrènyer la banda (R² 0,29 → objectiu): renda (INE ADRH — necessita
   accés especial INE, ho gestiona Bea), mix de calefacció / gas natural (ICAEN), grandària de la
   llar. Validació **held-out** (no només in-sample) abans del go/no-go.
2. **Estacionalitat del litoral vacacional**: l'elèctric domèstic anual no veu el pic estival; cal
   dada de pic (consum trimestral, ocupació turística) o modelar el flux a part.
3. **Completar les llistes** del classificador (AMB 36 / costaners / corona oficials) perquè els
   grups no es contaminin (avui `interior_rural` agafa exurbis).
4. **Ampliar la mostra** a més comarques (litoral sencer, interior, Pirineu) per estabilitzar els
   coeficients i tenir N per tipus.
5. **Replicar per a residus** (base 410) el mateix exercici (L2 càrrega), i pensar el go/no-go
   conjunt L1+L2.

— Talaia 🌊
