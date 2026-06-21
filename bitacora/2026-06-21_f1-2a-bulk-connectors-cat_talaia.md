# F1.2a · Des-acotar els connectors BULK a tot Catalunya (provat en viu)

**Data:** 2026-06-21
**Autora:** Talaia (encarna Sondeig)
**Latido (Bea):** «endavant» (la part segura de F1.2).
**Pla:** [docs/pla-catalunya-profund.md](../docs/pla-catalunya-profund.md) §F1.

## Què he fet
Des-acotat els **4 connectors bulk** (una sola query Socrata cadascun) perquè `comarca=None`
(o `municipis_ine5=None`) signifiqui **sense filtre = tot Catalunya**, mantenint el Berguedà com a
opció explícita:
- `residus.py`, `rtc.py`, `icaen_consum.py`: `where` condicional (None → tot CAT).
- `electoral.py`: `_where` sense el filtre `territori_codi` quan no es passen munis → tots els munis
  de Catalunya per a les convocatòries.
- `__main__.py`: nova bandera **`--scope {bergueda,catalunya}`** (default `bergueda`, per no canviar
  el comportament previ; CAT és opt-in). OSM sota `catalunya` encara no està llest (cal bbox CAT +
  geometria 947) → **es difereix honestament a F1.2b** (omès a `all`, error si es demana sol).

## Provat EN VIU a tot CAT (sortida a data/raw, gitignored — cap soroll al repo)
Entorn nou: venv `.venv` (gitignored) amb el paquet `datapoble-ingestion` (dlt 1.28.1, duckdb 1.5.4).

| Connector | files | munis distints | nota |
|---|---|---|---|
| residus | 23.687 | **949** | anys 2000–2024 |
| rtc | 112.964 | **922** | no tots tenen allotjament (turisme concentrat) — esperat |
| icaen_consum | 54.611 | **947** | cobertura plena (consum elèctric a tot arreu) |
| electoral | 31.314 | **951** | munis × 2 convocatòries × candidatures |

Camí del **pilot conservat** (verificat): `electoral._where(None)` = tot CAT; amb el Berguedà manté
el filtre `territori_codi` (Gósol inclòs). Cap test trencat (només hi ha tests d'OSM, intactes).

## Abast (honest)
Això són les baixades **ràpides**. Encara NO he tocat ni corregut les **pesades**: EMEX i
demografia/origen (per-muni, ~1.900 crides corteses) i OSM a escala (bbox CAT + geometria 947). Són
**F1.2b**, i avisaré abans de llançar-les. La sortida d'avui viu a `data/raw` (regenerable, no es
versiona); els marts segueixen a 31 fins que es re-materialitzin a F2 amb el model unificat.

## Següent
F1.2b: connectors per-muni (EMEX/origen → `CATALUNYA`, amb cau) + OSM a escala. Després F2: unificar
el model (base Nivell C + z-scores per tipus) i re-materialitzar els marts a 947.

— Talaia 🌊
