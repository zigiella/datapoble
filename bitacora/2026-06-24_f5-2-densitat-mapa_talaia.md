# F5.2 · Densitat de població com a indicador del mapa a tot Catalunya

**Data:** 2026-06-24
**Autora:** Talaia (encarna Sondeig/Mirador).
**Latido (Bea):** «seguim a F5».
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F5 (2a onada).

## Què he fet
Afegit **densitat de població (hab/km²)** com a indicador del mapa, pintable a **tot Catalunya**. Era
la covariable EMEX (f262) que el mart ja ingeria però no exposava; ara és **mètrica del mart** → flueix
neta a tot arreu (Berguedà pel dataset, resta pel compacte), sense trencar el pintat. És el **driver
principal** de la base del model de presència → transparència de l'estimació, i un 4t indicador CAT-wide
(abans només gap + residus; ara + densitat).

- `stg_idescat_emex`: pivota també `densitat_hab_km2`. `mart_municipi`: l'exposa.
- `metrics.yml` + `types.ts` (MetricKey) + `export_web_municipis` (METRIC_KEYS/FORMAT/COL_MUNI):
  nova mètrica `densitat_hab_km2` (demografia, EMEX 2025, format decimal).
- `export_indicadors_cat`: densitat al compacte del mapa. `MAP_INDICATORS` + etiqueta i18n
  `map_ind_densitat` (ca/es). Sense caveat: és mesura directa (no inferència).

## Verificat
- Densitat a tot arreu: Girona 2.770, Berga 777; compacte 947 munis. catalunya.json 53 mètriques.
- «Densitat de població» al selector del mapa (HTML prerenderitzat).
- `svelte-check` 0/0 · `build` ✔ · `verify_marts`/`derive_fase1`/`export --check`/`dbt parse` OK.
- ⚠️ Mapa canvas → **cop d'ull de Bea**: la densitat té rang molt ampli (metro ~20.000 vs rural ~5);
  el Jenks s'adapta, però si visualment domina l'àrea metropolitana, es podria valorar escala log
  més endavant.

## Resta de F5 (no bloquejant)
- Renda / fracció de gas com a indicadors (necessiten font nova al mart: renda CSV, gas ICAEN).
- OSM + subtipus de tipologia a tot CAT (el més pesat).
- Electoral a tot CAT (aparcat per publicació).

— Talaia 🌊
