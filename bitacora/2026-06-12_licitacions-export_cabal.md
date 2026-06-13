# Licitacions: pont dada→web (export standalone)

**Fecha:** 2026-06-12
**Autora:** Cabal (senyals) — executat per Talaia
**Para:** Talaia (review/merge) · Bea
**Tema:** primer pas de «Licitacions al web» (decisió Bea: secció + fitxa). El pont que faltava entre les sortides del Cabal (`data/events/licitacions_*.parquet`) i el frontend, sense passar pel mart (mateix patró que l'ETCA).
**Status:** fet, verificat (export + --check) / handoff. La secció `/licitacions` i el bloc de fitxa van a PRs següents (Mirador).

## Context
El PAS 1 de licitacions ja era complet a `packages/signals` (1.295 contractes classificats + repartiment supramunicipal + indicador de dependència), però NO arribava al web: l'exportador del web només llegeix marts. Aquest és el pont.

## Què he fet
- **`tools/export_licitacions.py`**: llegeix els 3 parquets del Cabal (enriquit/repartiment/dependencia) i emet `data/web/licitacions-bergueda.json`:
  - **resum comarcal**: 1.295 contractes (695 comarcals + 600 municipals), import total ~42,4 M€, taxonomia per tema (12), i el recompte de dependència.
  - **fila per municipi**: import municipal directe, nº de contractes propis, import de serveis comarcals assignables, ràtio de dependència supramunicipal (o null), lectura, confiança, i els **3 temes que més rep del Consell** (del repartiment).
  - `--check` (offline, reproduïble) → gate de CI.
- **`copy-data.mjs`**: copia també `licitacions-bergueda.json` a `static/data/`.
- **`ci.yml`**: `export_licitacions.py --check` al job de dades.

## Resultat (clau)
- **Dependència supramunicipal**: només **2 de 31** municipis contracten res propi (Berga ràtio 0,196 i Castellar = autònoms); **29 = no_contracta_propi**. Berga: 21,3 M€ directes, 577 contractes.
- Exemple fitxa: Gironella (no_contracta_propi) rep del Consell sobretot mobilitat (886 k€), aigua (600 k€), residus (545 k€).

## Frontera honesta (per a la copy del web)
«no_contracta_propi» = **centralització** (el Consell contracta pels municipis) **+ biaix de font** (els petits poden publicar en altre lloc o sota llindar), **MAI mala gestió**. La taxonomia és heurística i el repartiment és una hipòtesi declarada (mètode + confiança per fila). Aquest enquadrament és INNEGOCIABLE a la UI (risc difamatori si es publica el «29 de 31» sense context).

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] **PR següent (Mirador):** secció `/licitacions` (resum comarcal: taxonomia + dependència + enquadrament honest) + bloc a la fitxa de municipi (la seva dependència + què rep del Consell).
- [ ] Integrar al mart quan es reconstrueixi el pipeline complet (avui standalone, com l'ETCA, perquè no hi ha `data/raw/`).

## Enlaces
- `tools/export_licitacions.py` · `data/web/licitacions-bergueda.json` · `packages/web/scripts/copy-data.mjs` · `.github/workflows/ci.yml`
- dades: `data/events/licitacions_*.parquet` (Cabal) · mètode: `docs/licitacions-intel-metode.md` · pla: `bitacora/` plans de licitacions

— Cabal
