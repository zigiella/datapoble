# Metodologia — presència real estimada a Catalunya (en rang)

> Com estimem **la gent que el padró no veu** (la presència real, «qui hi dorm») més enllà del
> Berguedà, i per què la donem **en rang** i no com a xifra tancada. Honestedat de marca: cap
> número sense procedència; estimació ≠ cens; el «no» i el rang per davant de la falsa precisió.
> Document tècnic; la versió pública condensada va a `/metodologia`. Detall intern: `docs/analisi-escala-nivellc.md`.

## 1. Què mesurem
El **padró** diu qui *consta* en un municipi. Però hi ha gent que hi dorm i no hi consta (segona
residència, estacional, no empadronada) i gent que hi consta però en surt (commuters). Mesurem la
**presència real estimada** — quanta gent *hi dorm de fet* — i la contrastem amb el padró. La
diferència és el cor del projecte.

## 2. El senyal
El **consum elèctric domèstic** per municipi (ICAEN) és un termòmetre de presència: si un municipi
consum com si tingués més habitants dels que el padró diu, és que n'hi ha (aprox.) més de presents.

    presència_estimada = consum_elèctric_domèstic / BASE

on `BASE` = el consum elèctric d'**un resident "normal"**. El repte: aquesta base **no és la mateixa
arreu** (un pis dens gasta menys per persona que una casa gran; una llar de renda alta, més; una llar
amb calefacció de gas, molt menys elèctric). Per això la modelem (Nivell C).

## 3. Per què en RANG (no una xifra)
És **inferència, no cens**. La base real de cada municipi té incertesa, i per tant la població
estimada també. Publicar una xifra exacta seria fingir una precisió que no tenim. Donem un **interval
honest** (p10–p90) i, on no validem prou bé, ho diem obertament. Quan un tipus de municipi validi
amb prou força (objectiu: ≥85% dins ±15% contra dada oficial), podrem donar-ne la xifra absoluta;
fins llavors, **rang**.

## 4. El model (Nivell C)
Estimem la **base elèctrica per persona** com a funció de covariables que **NO** depenen de la
presència (no podem predir la presència amb senyals de presència; seria circular):

    base = 855 − 154·log10(densitat) + 72·(renda en milers €) − 615·(fracció de gas domèstic)

- **Densitat** (Idescat): més densitat → pisos més petits → menys elèctric/persona.
- **Renda** neta per persona (INE ADRH 2023): més renda → més consum/persona.
- **Fracció de gas** del consum domèstic = gas/(gas+elèctric) (ICAEN): on es calefacta amb gas,
  l'elèctric per persona baixa molt (−615 kWh de 0% a 100% de gas). És un **ràtio**, independent de
  la presència.

El model s'**ajusta (calibra) contra l'ETCA oficial** (vegeu §5). `R² = 0,65`.

## 5. La banda i la validació
- **Banda** = els percentils **p10–p90 del residual** del model, calculats **per tipus territorial**
  (litoral, metropolità dens, corona, interior…). Cada municipi hereta la incertesa del seu tipus
  (p. ex. el litoral vacacional té banda més ampla: l'estacionalitat hi pesa més).
- **Validació externa = ETCA** (Idescat, *Estimacions de població ETCA/EPE*), la població estacional
  equivalent oficial, disponible per a municipis ≥1.000 hab. On hi ha ETCA, la mostrem **al costat
  de la nostra estimació** com a prova de fiabilitat (no la substituïm: el mètode és el producte).
- **Robustesa**: validació *held-out* (leave-one-out) — el model encerta igual en municipis que no
  ha vist (cobertura 77% dins ±15% in-sample = held-out). **No és sobreajust.**

## 6. Honestedat i abast (go/no-go)
- **Regla**: presència **absoluta** (xifra) només si el tipus valida amb **ρ≥0,7 i error≤15%**;
  si no, **rang** + «encara no ho mesurem prou bé aquí». Avui: **rang per a tothom**.
- **Primera tanda publicada**: municipis amb ETCA (**≥1.000 hab**) de **Berguedà, Barcelonès,
  Tarragonès, Baix Llobregat i Maresme** (artefacte `data/web/pernocta-catalunya.json`).
- **Pendent (s'incorpora poc a poc, verificant):** els municipis **<1.000 hab** (els petits
  turístics, el cas que més ho necessita), la resta de comarques, i l'**estacionalitat del litoral**
  — l'elèctric/gas **anual** no veu el **pic estival**; per a la costa cal dada de **pic** (consum
  trimestral / ocupació) abans de donar-ne xifra absoluta.

## 7. Fonts (cap número sense procedència)
| Dada | Font | Dataset |
|---|---|---|
| Consum elèctric domèstic | ICAEN (Transparència) | `8idm-becu` (sector 7) |
| Consum de gas natural domèstic | ICAEN (Transparència) | `qvqg-zag8` (sector domèstic) |
| Renda neta per persona 2023 | INE — Atlas de Distribució de Renda (ADRH) | taula 30824 |
| Població estacional (validació) | Idescat — ETCA/EPE | `epe` (base 2021) |
| Densitat / altitud | Idescat — EMEX | `f262` / `f258` |

## 8. Reproduïbilitat
`tools/nivellc_analisi.py` (baixa senyals + covariables per comarca) → `tools/nivellc_regressio.py`
(ajusta el model + held-out) → `tools/export_pernocta_catalunya.py` (genera l'artefacte publicable
en rang). Carril de dades fet en silenci fins ara; aquesta és la primera publicació, en rang.

— Talaia 🌊
