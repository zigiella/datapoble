# Nivell C estès a TOTA Catalunya — de 91 a 927 municipis en rang

**Data:** 2026-06-18
**Autora:** Talaia (encarna Sondeig/dades)
**Latido (Bea):** «tira amb la llista provisional i jo configuro la bona». Tanca P0 #1 de `next.md`.
**Status:** a la porta del PR (branca `data/nivellc-tota-catalunya`).

## Què he fet
Estès el model Nivell C de 5 comarques (91 munis) a **tota Catalunya (927 munis en rang)**. Tres
canvis al pipeline, tots **bulk/offline** (cap crida per-muni → ràpid):

1. **`nivellc_analisi.py`** — fetch de tot Catalunya (trec el filtre de comarca: ICAEN/ARC/RTC ja
   són només de CAT; a més el filtre petava amb 400 pels apòstrofs tipus «Pla d'Urgell»). **Densitat
   = població/superfície** (àrea del geojson + població ARC/EPE) en lloc de l'EMEX per-muni —
   **validat r=0,9999 vs EMEX**, estalvia ~900 crides Idescat. **Costaners** de la derivació
   provisional (`municipis_costaners.csv`). Altitud fora (munis de muntanya → interior_rural).
2. **`nivellc_regressio.py`** — ajusta sobre els **486 munis amb ETCA** (abans 91) i **prediu
   base_pred per a tots els 927**. Held-out (LOO) + banda per tipus.
3. **`export_pernocta_catalunya.py`** — **Palanca 2**: `est = kWh/base_pred` (l'ETCA s'anul·la,
   només valida) → cobreix també els **<1.000 hab**, amb banda ×1,5 i marcats «sense validació
   oficial» (etca_oficial=null).

## Resultat (honest)
- Fit N=486 ETCA. **R²=0,41**, cobertura ±15% **70%**, **held-out=in-sample (caiguda 0 → robust)**.
- R² baixa (0,65→0,41) perquè el conjunt complet és molt més divers (353 interior_rural). És la
  realitat de tota Catalunya → **rang, no xifra** (la regla es manté).
- Banda per tipus: corona [−10,+9] · litoral_metro [−16,−3] · metro_dens [−19,+4] · interior
  [−18,+17] · **litoral_vacacional [−20,+26]** (l'estacionalitat de platja, el límit conegut).
- **927 munis publicats** (486 validats ETCA + 441 sub-1000 sense validació). 20 munis sense senyal
  elèctric/renda → «sense dades». El web ja consumeix l'artefacte → cobertura estesa sola.

## Verificat
- Pipeline complet corre net; `build` OK. Agullana (sub-1000) mostra rang [579–995] a la fitxa;
  munis ETCA amb validació ✓dins/·fora; els 20 sense senyal queden «sense dades».
- Metodologia pública (`metodologia-presencia-catalunya.md`) i doc d'analista (T6/D11) actualitzats
  amb els números reals.

## Pendents (flag honest)
- **La vista de cobertura per COMARCA/VEGUERIA del mapa quedà OBSOLETA**: deia «només Berguedà /
  Comarques Centrals»; ara cobrim ~tot CAT en rang. A granularitat municipi el mapa és correcte (927
  coberts), però la vista comarca/vegueria (default de la home) contradiu el missatge d'abast → cal
  actualitzar-la (següent increment).
- Llista costanera **OFICIAL** (Bea) → reemplaçar la provisional i recórrer (re-run barat).
- Dada de pic per al litoral (xifra absoluta) · residus L2.

— Talaia 🌊
