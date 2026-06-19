#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deriva l'ESPINA TERRITORIAL: per a cada municipi de Catalunya, la seva comarca i vegueria.

Per què: l'espina/breadcrumb de la fitxa (Catalunya › vegueria › comarca › municipi) i la navegació
«altres municipis de la comarca» necessiten el mapatge muni→comarca→vegueria per als ~947 munis. La
geometria municipal (INE/IGN) NO porta la comarca, però les comarques SÓN unions de municipis
sencers: el punt representatiu d'un municipi cau dins exactament una comarca → assignació EXACTA
(no aproximada). Fallback per màxima intersecció si les dues capes (munis/comarques) no casen
perfectament per simplificació.

Fonts (al repo, no depèn de marts ni IA):
  - `packages/web/static/geo/catalunya-municipis.geojson`  (947, {ine5, nom})
  - `packages/web/static/geo/catalunya-comarques.geojson`  (43, {id, nom, cap})
  - `data/territorial/comarca_vegueria.csv`                 (comarca → vegueria, vegueria_id)

Sortida: `data/web/municipis-territori.json` = { ine5: {comarca, vegueria} }, servit a la web pel
prebuild (copy-data). Artefacte estable (la geometria no canvia); es versiona.

Ús:  python tools/deriva_territori.py
"""
import csv
import json
import sys
from pathlib import Path

from shapely.geometry import shape
from shapely.strtree import STRtree

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
GEO = REPO / "packages" / "web" / "static" / "geo"
MUNIS = GEO / "catalunya-municipis.geojson"
COMARQUES = GEO / "catalunya-comarques.geojson"
COM_VEG = REPO / "data" / "territorial" / "comarca_vegueria.csv"
OUT = REPO / "data" / "web" / "municipis-territori.json"


def main():
    com_veg = {}
    with COM_VEG.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            com_veg[r["comarca"]] = r["vegueria"]

    coms = json.loads(COMARQUES.read_text(encoding="utf-8"))["features"]
    com_geoms = [shape(c["geometry"]) for c in coms]
    com_noms = [c["properties"]["nom"] for c in coms]
    tree = STRtree(com_geoms)

    munis = json.loads(MUNIS.read_text(encoding="utf-8"))["features"]
    out = {}
    n_fallback = 0
    sense = []
    for f in munis:
        ine5 = str(f["properties"]["ine5"])
        nom = str(f["properties"]["nom"])
        g = shape(f["geometry"])
        pt = g.representative_point()  # garantit dins el polígon del municipi
        # Candidates per bbox (STRtree) → comarca que conté el punt.
        idx = None
        for i in tree.query(pt):
            if com_geoms[i].contains(pt):
                idx = i
                break
        if idx is None:
            # Fallback: comarca amb màxima àrea d'intersecció amb el municipi.
            best, best_a = None, 0.0
            for i in tree.query(g):
                a = g.intersection(com_geoms[i]).area
                if a > best_a:
                    best, best_a = i, a
            idx = best
            n_fallback += 1
        if idx is None:
            sense.append(f"{ine5} {nom}")
            continue
        comarca = com_noms[idx]
        out[ine5] = {"comarca": comarca, "vegueria": com_veg.get(comarca, "")}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # Resum + sanity.
    from collections import Counter
    per_com = Counter(v["comarca"] for v in out.values())
    sense_veg = sorted({v["comarca"] for v in out.values() if not v["vegueria"]})
    print(f"[territori] {len(out)} munis assignats ({n_fallback} per fallback d'intersecció). → {OUT}")
    print(f"[territori] comarques cobertes: {len(per_com)}/43")
    if sense:
        print(f"[territori] SENSE comarca ({len(sense)}): {', '.join(sense)}")
    if sense_veg:
        print(f"[territori] comarques sense vegueria al CSV: {', '.join(sense_veg)}")
    # Sanity puntual: Berga→Berguedà, Salou→Tarragonès, Roses→Alt Empordà.
    for ine5, esperat in [("08022", "Berguedà"), ("43137", "Tarragonès"), ("17152", "Alt Empordà")]:
        got = out.get(ine5, {}).get("comarca", "(cap)")
        print(f"[territori] sanity {ine5}: {got} {'OK' if got == esperat else '?? esperava ' + esperat}")


if __name__ == "__main__":
    main()
