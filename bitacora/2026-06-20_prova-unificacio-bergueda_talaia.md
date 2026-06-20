# F0 · Provar el model unificat al Berguedà (abans d'escalar a tot CAT)

**Data:** 2026-06-20
**Autora:** Talaia (encarna Sondeig)
**Latido (Bea):** «volem fer-ho bé» → vot d'abast: **«provar primer al Berguedà»** (re-córrer el model
unificat només al Berguedà i confirmar que reprodueix l'ETCA, abans d'escalar).
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) (fase «dataset profund a tot CAT»).

## Què he provat
El **guardó §3.1**: si substituïm la base de presència FIXA del Berguedà (Nivell B,
`base_electric=1224`, calibrada sobre 31 munis) per la base de COVARIABLES de tot CAT (Nivell C,
`base=f(densitat,renda,gas)`), el Berguedà segueix reproduint la seva validació ETCA?

Comparació **offline** (cap re-baixada) de dos artefactes existents: `poblacio_pernocta_est`
(Nivell B, de `municipis.bergueda.json`) vs `estimacio`+rang (Nivell C, de `pernocta-catalunya.json`,
que ja inclou el Berguedà), contra `etca_oficial` (Idescat) als 9 munis del Berguedà ≥1.000 hab.
Eina reproduïble: `tools/prova_unificacio_bergueda.py`.

## Resultat: ✅ PASSA (i MILLORA)
| Mètrica | Nivell B (base fixa) | Nivell C (covariables) |
|---|---|---|
| Error medià vs ETCA | 11,9% | **8,2%** |
| Dins ±15% | 5/9 | **7/9** |
| ETCA dins rang | — | 8/9 |
| Spearman(ETCA, NivC) | — | **0,979** |

Arregla els errors GROSSOS del Nivell B: **Cercs 46,2%→1,3%**, **Casserres 41,6%→3,4%**, **Avià
34,9%→6,8%**, Bagà 20,6%→8,2%. La base de covariables (densitat/renda/gas) captura millor el consum
per resident que la base fixa comarcal.

## El punt feble honest
Micromunis de **muntanya-turisme** s'**infraestimen** amb la base de covariables: **la Pobla de
Lillet 10,9%→24,0%** (ETCA cau FORA del rang), Guardiola 11,9%→15,2%. Causa coneguda: l'elèctric
domèstic ANUAL no veu el pic estacional turístic (mateix límit que el litoral vacacional). El **rang +
la bandera de confiança** són la xarxa; aquests munis necessitarien senyal de pic per a xifra absoluta.

## Abast del que s'ha provat (honestedat)
S'ha provat la **base de presència** — la part que l'ETCA pot validar. Els **z-scores per tipus
territorial** (tipologia, confiança) NO els valida l'ETCA (són categòrics/relatius) i necessiten els
senyals a escala CAT (vidre, %no-principal) → es validaran a **F2** per estabilitat (que la tipologia
del Berguedà no es desmunti en canviar el grup de referència de comarca→tipus), no per ETCA.

## Veredicte i següent pas
El guardó es compleix: **es pot escalar la base unificada**. Desbloqueja **F1** (des-acotar la
ingesta a tot CAT), ara de-risquejada pel que fa al cor del model. Pendent de F1: les baixades pesades
(EMEX/origen per-muni, OSM a escala) i, a F2, validar els z-scores per tipus.

— Talaia 🌊
