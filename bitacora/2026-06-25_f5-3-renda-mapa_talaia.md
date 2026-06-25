# F5.3 · Renda neta per persona com a indicador del mapa a tot Catalunya

**Data:** 2026-06-25
**Autora:** Talaia (encarna Sondeig/Mirador).
**Latido (Bea):** «següent peça F5».
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F5 (2a onada).

## Què he fet
Afegida la **renda neta per persona** (INE ADRH 2023) com a mètrica del mart i **5è indicador
pintable a tot CAT** (gap · residus · densitat · renda). Indicador de benestar + covariable de la base
del model → transparència. Mateix patró que la densitat, però la renda viu en CSV territorial (no a
EMEX) → entra per un staging nou.

- **`stg_renda`** (nou): llegeix `data/territorial/renda_municipi_cat.csv` (via `territorial_root`).
- **`mart_municipi`**: CTE `renda` + left join + exposa `renda_neta_persona`.
- **`metrics.yml`**: font nova `ine_adrh` (procedència) + mètrica `renda_neta_persona` (demografia,
  €/persona, 2023, format integer, public).
- `types.ts` (MetricKey) · `export_web_municipis` (METRIC_KEYS/FORMAT/COL_MUNI) ·
  `export_indicadors_cat` (compacte del mapa) · `MAP_INDICATORS` + `map_ind_renda` (ca/es).

## Verificat
- Renda a tot arreu: Girona 16.857 €, Berga 15.449 €; compacte 927 munis. catalunya.json 54 mètriques.
- «Renda neta per persona» al selector del mapa (HTML prerenderitzat).
- `svelte-check` 0/0 · `build` ✔ · `verify_marts`/`derive_fase1`/`export --check`/`dbt parse` OK ·
  `pytest test_catalog` 7/7.
- ⚠️ Mapa canvas → cop d'ull de Bea (la renda té rang més estret que la densitat; el Jenks va bé).

## Resta de F5 (no bloquejant)
- Fracció de gas domèstic com a indicador (font ICAEN gas; mateix patró).
- OSM + subtipus de tipologia a tot CAT (el més pesat).
- Electoral a tot CAT (aparcat per publicació).

— Talaia 🌊
