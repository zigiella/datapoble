# F5.5b · OSM a tot Catalunya → tipologia + restauració + serveis a cada fitxa

**Data:** 2026-06-27
**Autora:** Talaia (encarna Sondeig).
**Latido (Bea):** «arranquem» (OSM, l'última peça per pintar-ho TOT a CAT).
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F5.

## Què he fet
Des-acotat l'OSM (la 2a onada, el tros més pesat) i estès la tipologia a tot Catalunya.

**Connectors OSM (restauracio_osm, serveis_osm):** parametritzats per abast — `geojson`+`bbox`+`tiles`.
A escala CAT baixen per **MOSAIC** (4×4=16 tiles d'Overpass, deduplicant per id) sobre el bbox de
Catalunya, i el punt-en-polígon (DuckDB-spatial) assigna als 947. `__main__ --scope catalunya` els
corre amb geometria 947 + bbox CAT. Resultat: **restauració 22.782 estab. assignats** (807/947 amb
locals, 140 a 0 = infra-mapeig rural honest), **serveis 22.959**.
*(La baixada de serveis es va penjar per la suspensió nocturna de la màquina; re-executada en fresc
sense problema — no era cap bug, sinó la màquina dormint.)*

**Mart (tipologia a tot CAT):** `bstats`/`btipo` passen de «només Berguedà» a **z-scores per
tipus_territorial** (iguals amb iguals), com la confiança. La tipologia es calcula per als 927 munis
amb tipus; els ~20 sense covariables → `pendent`. Mirall `derive_fase1.py` actualitzat igual.

**GUARDÓ ✅:** els arquetips provats del Berguedà es mantenen — Berga=capital_serveis,
Castellar=excursió, Gósol=segona_residència. Distribució CAT plausible: indeterminat 495,
capital_serveis 150, segona_residència 125, excursió 80, buit 56, dormitori 21, pendent 20.

## Verificat
- mart 947 · arquetips preservats · `verify_marts`/`derive_fase1 --check` OK · `dbt` build OK.
- `export --check` (cat+berg) · `svelte-check` 0/0 · `npm build` ✔.
- **Fitxa de Girona** (no-Berguedà): ja mostra **Restauració (592), Serveis (486) i tipologia
  (segona residència)** — totes les fitxes de CAT són ara plenes.

## Honestedat
OSM **infra-mapa el rural** → els comptes de restauració/serveis són un **mínim observat, no un
cens**; el z-score per tipus ho atenua (rural amb rural) i la tipologia és una LECTURA amb caveat.
Els 140 munis amb 0 restauració es mostren «sense dada» al mapa (no classe baixa).

## Següent (F5.5c)
Pintar **tipologia** (categòric) i **restauració** (numèric) al MAPA per als coberts → els 2 últims
indicadors per tenir-los **TOTS** a tot CAT.

— Talaia 🌊
