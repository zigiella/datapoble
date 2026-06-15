#!/usr/bin/env python3
"""Genera la geometria de VEGUERIES (8 àmbits territorials) dissolent les 43 comarques.

El mapa de la home i el /mapa han de poder commutar la granularitat comarca · vegueria · municipi
(decisió Bea + handoff DA «Quota»). Tenim geometria de comarques (`catalunya-comarques.geojson`) i
de municipis (`catalunya-municipis.geojson`), però NO de vegueries. Aquí les derivem dissolent les
comarques pels 8 àmbits funcionals territorials (els «vegueries» del Pla territorial, amb Penedès).

Entrada: `packages/web/static/geo/catalunya-comarques.geojson` (props {id, nom, cap}).
Sortida: `packages/web/static/geo/catalunya-vegueries.geojson` (props {id, nom, comarques:[...]}).
També escriu el mapatge a `data/territorial/comarca_vegueria.csv` (intern, reutilitzable).

Ús:  python tools/build_vegueries_geojson.py
"""
from __future__ import annotations

import csv
import json
import sys
import unicodedata
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

REPO = Path(__file__).resolve().parents[1]
COM = REPO / "packages" / "web" / "static" / "geo" / "catalunya-comarques.geojson"
OUT = REPO / "packages" / "web" / "static" / "geo" / "catalunya-vegueries.geojson"
MAP_CSV = REPO / "data" / "territorial" / "comarca_vegueria.csv"

# 43 comarques → 8 àmbits funcionals territorials (Pla territorial, amb Penedès 2017).
# (Lluçanès i Moianès → Comarques Centrals; Anoia → Penedès, segons l'àmbit del Penedès.)
VEGUERIES: dict[str, list[str]] = {
    "Metropolità": ["Barcelonès", "Baix Llobregat", "Maresme", "Vallès Occidental", "Vallès Oriental"],
    "Comarques Gironines": ["Alt Empordà", "Baix Empordà", "Garrotxa", "Gironès", "Pla de l'Estany",
                            "Ripollès", "Selva"],
    "Camp de Tarragona": ["Alt Camp", "Baix Camp", "Conca de Barberà", "Priorat", "Tarragonès"],
    "Terres de l'Ebre": ["Baix Ebre", "Montsià", "Ribera d'Ebre", "Terra Alta"],
    "Ponent": ["Garrigues", "Noguera", "Pla d'Urgell", "Segarra", "Segrià", "Urgell"],
    "Comarques Centrals": ["Bages", "Berguedà", "Osona", "Solsonès", "Moianès", "Lluçanès"],
    "Alt Pirineu i Aran": ["Alta Ribagorça", "Alt Urgell", "Cerdanya", "Pallars Jussà",
                           "Pallars Sobirà", "Val d'Aran"],
    "Penedès": ["Alt Penedès", "Baix Penedès", "Garraf", "Anoia"],
}
VEG_ID = {  # slug estable per a la propietat id (join/estil)
    "Metropolità": "metropolita", "Comarques Gironines": "gironines",
    "Camp de Tarragona": "camp-tarragona", "Terres de l'Ebre": "terres-ebre",
    "Ponent": "ponent", "Comarques Centrals": "centrals",
    "Alt Pirineu i Aran": "pirineu-aran", "Penedès": "penedes",
}


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not COM.exists():
        print(f"FALLA: no existeix {COM}", file=sys.stderr)
        return 2
    fc = json.loads(COM.read_text(encoding="utf-8"))

    # nom_comarca normalitzat → àmbit
    com2veg: dict[str, str] = {}
    for veg, coms in VEGUERIES.items():
        for c in coms:
            com2veg[_norm(c)] = veg

    # Verificació: cada comarca del geojson ha de tenir àmbit; cap nom del mapatge ha de sobrar.
    geo_noms = {_norm(f["properties"]["nom"]): f["properties"]["nom"] for f in fc["features"]}
    falten = [n for n in geo_noms if n not in com2veg]
    sobren = [c for c in com2veg if c not in geo_noms]
    if falten:
        print(f"FALLA: comarques del geojson sense àmbit: {[geo_noms[n] for n in falten]}", file=sys.stderr)
        return 1
    if sobren:
        print(f"FALLA: noms al mapatge que no són al geojson: {sobren}", file=sys.stderr)
        return 1

    # Agrupa geometries per àmbit i dissol.
    groups: dict[str, list] = {}
    members: dict[str, list[str]] = {}
    for f in fc["features"]:
        nom = f["properties"]["nom"]
        veg = com2veg[_norm(nom)]
        groups.setdefault(veg, []).append(shape(f["geometry"]))
        members.setdefault(veg, []).append(nom)

    features = []
    for veg in VEGUERIES:  # ordre estable
        geom = unary_union(groups[veg])
        features.append({
            "type": "Feature",
            "properties": {"id": VEG_ID[veg], "nom": veg,
                           "comarques": sorted(members[veg])},
            "geometry": mapping(geom),
        })

    out_fc = {"type": "FeatureCollection", "features": features}
    OUT.write_text(json.dumps(out_fc, ensure_ascii=False), encoding="utf-8")
    kb = OUT.stat().st_size / 1024

    MAP_CSV.parent.mkdir(parents=True, exist_ok=True)
    with MAP_CSV.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh)
        w.writerow(["comarca", "vegueria", "vegueria_id"])
        for veg in VEGUERIES:
            for c in sorted(members[veg]):
                w.writerow([c, veg, VEG_ID[veg]])

    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {len(features)} vegueries · {kb:.0f} kB")
    for f in features:
        print(f"  {f['properties']['nom']:22} ({len(f['properties']['comarques'])} comarques)")
    print(f"Mapatge → {MAP_CSV.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
