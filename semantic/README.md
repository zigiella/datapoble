# semantic - contracte unic

metrics.yml: definicio unica de cada metrica (etiquetes multilingues ca/es, formula, font, data, visibilitat). El consumeixen dades, IA i frontend.

Estat: migrant el cataleg del prototip (F0).

## Convenció `visibility` vs `visibilitat` (C1 §3, vinculant)

Són **dos camps, no dos noms del mateix**:

- **`visibility`** (en) = **estat de publicació**: `public` (visible) | `planned` (definida, encara no calculada).
- **`visibilitat`** (ca) = **capa de dades**, segons la Convención de visibilidad de `docs/data-sources.md` §0:
  - `verd` = pot sortir al producte.
  - `vermell` = capa interna: mai s'exporta, només agregada.
  - Regla del join heretada: **qualsevol creuament verd × vermell dona vermell**.

`visibilitat` és obligatori a totes les mètriques noves des del contracte C1
(2026-07-16, primera implementació: D1 `atur_registrat`). El backfill de les
mètriques anteriors és un chore separat (owner: Talaia).
