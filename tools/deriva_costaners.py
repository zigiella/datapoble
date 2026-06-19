#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deriva (geomètricament) la llista de MUNICIPIS COSTANERS de Catalunya.

Per què: el classificador del Nivell C (`tools/nivellc_analisi.py`) distingeix els tipus litorals
amb una llista de costaners feta A MÀ i només per a 5 comarques. Per estendre el model a tot
Catalunya cal la llista de TOT el país. En comptes d'inventar-la o picar-la a ull (~70 munis),
la derivem de dades obertes i reproduïbles:

  municipi costaner  ⇔  el seu polígon toca (o és a < LLINDAR del) MAR.

Fonts (citables, domini públic):
  - Geometria municipal: `packages/web/static/geo/catalunya-municipis.geojson` (INE/IGN, {ine5,nom}).
  - Mar: Natural Earth 1:10m «ocean» (`ne_10m_ocean.geojson`, domini públic), baixat i cachejat.

Mètode honest: la costa de Natural Earth i la municipal NO casen perfectament (fonts i
generalitzacions diferents), per això NO fem servir intersecció estricta sinó DISTÀNCIA al mar amb
un llindar, i deixem a la vista els casos FRONTERA perquè es puguin encreuar amb la llista oficial
(que la Bea investiga en paral·lel). Distàncies en metres via projecció equirectangular local
(escalat graus→m a la latitud central de Catalunya; n'hi ha prou a aquesta escala).

Sortida: `data/territorial/municipis_costaners.csv` (ine5, nom, costaner, dist_m) + resum a consola
amb el tall i els casos frontera + encreuament amb la llista a mà de `nivellc_analisi.py` (sanity).

Ús:  python tools/deriva_costaners.py
"""
import csv
import json
import math
import sys
import unicodedata
import urllib.request
from pathlib import Path

from shapely.geometry import shape, box
from shapely.ops import unary_union
from shapely import transform as shp_transform
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
MUNIS_GEO = REPO / "packages" / "web" / "static" / "geo" / "catalunya-municipis.geojson"
CACHE = REPO / "data" / "eval" / "ne_10m_ocean.geojson"  # gitignored
OUT = REPO / "data" / "territorial" / "municipis_costaners.csv"
OCEAN_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_ocean.geojson"

# Llindar de costa (m). Absorbeix el desajust de fonts (NE 10m generalitza la costa ~1 km). Per sota
# = costaner; entre LLINDAR i FRONTERA = dubtós (es llista a part per a l'encreuament manual).
LLINDAR_M = 1500.0
FRONTERA_M = 4000.0

# Projecció equirectangular local: metres ≈ graus · (m/grau) a la latitud central de Catalunya.
LAT0 = 41.7
M_PER_DEG_LAT = 111_132.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT0))


def to_metric(geom):
    """Escala (lon,lat) en graus → metres aprox (equirectangular local)."""
    return shp_transform(geom, lambda c: np.column_stack([c[:, 0] * M_PER_DEG_LON, c[:, 1] * M_PER_DEG_LAT]))


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = s.replace("'", " ").replace("-", " ")
    parts = [p for p in s.split() if p not in {"el", "la", "els", "les", "l", "de", "del", "d"}]
    return " ".join(parts)


# Llista A MÀ de costaners de les 5 comarques cobertes (de nivellc_analisi.py), per a SANITY CHECK:
# tots haurien de sortir costaners a la derivació.
COSTANERS_MA = {_norm(x) for x in [
    "Barcelona", "Badalona", "Sant Adrià de Besòs", "Montgat",
    "el Prat de Llobregat", "Viladecans", "Gavà", "Castelldefels",
    "el Masnou", "Premià de Mar", "Vilassar de Mar", "Cabrera de Mar", "Mataró",
    "Sant Andreu de Llavaneres", "Caldes d'Estrac", "Arenys de Mar", "Canet de Mar",
    "Sant Pol de Mar", "Calella", "Pineda de Mar", "Santa Susanna", "Malgrat de Mar",
    "Tarragona", "Salou", "Cambrils", "Vila-seca", "Torredembarra", "Altafulla", "Creixell",
    "Roda de Berà", "la Pobla de Montornès", "Vespella de Gaià",
]}


def load_ocean_clipped(bbox_deg):
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        print(f"[costaners] baixant Natural Earth ocean 10m → {CACHE} …")
        urllib.request.urlretrieve(OCEAN_URL, CACHE)
    gj = json.loads(CACHE.read_text(encoding="utf-8"))
    clip = box(*bbox_deg)
    geoms = []
    for f in gj["features"]:
        g = shape(f["geometry"])
        if g.intersects(clip):
            geoms.append(g.intersection(clip))
    return unary_union(geoms)


def main():
    gj = json.loads(MUNIS_GEO.read_text(encoding="utf-8"))
    feats = gj["features"]
    # bbox de Catalunya + marge per agafar el mar adjacent.
    xs, ys = [], []
    for f in feats:
        minx, miny, maxx, maxy = shape(f["geometry"]).bounds
        xs += [minx, maxx]
        ys += [miny, maxy]
    bbox = (min(xs) - 0.3, min(ys) - 0.3, max(xs) + 0.3, max(ys) + 0.3)

    ocean_deg = load_ocean_clipped(bbox)
    ocean_m = to_metric(ocean_deg)

    rows = []
    for f in feats:
        ine5 = str(f["properties"]["ine5"])
        nom = str(f["properties"]["nom"])
        gm = to_metric(shape(f["geometry"]))
        d = gm.distance(ocean_m)  # metres aprox; 0 si toca/encavalca el mar
        rows.append((ine5, nom, d))

    rows.sort(key=lambda r: r[2])
    costaners = [r for r in rows if r[2] <= LLINDAR_M]
    frontera = [r for r in rows if LLINDAR_M < r[2] <= FRONTERA_M]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ine5", "nom", "costaner", "dist_m"])
        for ine5, nom, d in rows:
            w.writerow([ine5, nom, "1" if d <= LLINDAR_M else "0", round(d)])

    print(f"\n[costaners] {len(costaners)} municipis costaners (dist ≤ {LLINDAR_M:.0f} m). CSV → {OUT}")
    print("  (els 12 més propers, sanity:)")
    for ine5, nom, d in costaners[:12]:
        print(f"    {ine5}  {nom:<32} {d:6.0f} m")

    print(f"\n[costaners] CASOS FRONTERA ({LLINDAR_M:.0f}–{FRONTERA_M:.0f} m) — per encreuar amb l'oficial:")
    for ine5, nom, d in frontera:
        print(f"    {ine5}  {nom:<32} {d:6.0f} m")

    # SANITY: tots els de la llista a mà (5 comarques) han de sortir costaners.
    cost_norm = {_norm(n) for _, n, _ in costaners}
    falten = sorted(COSTANERS_MA - cost_norm)
    print(f"\n[costaners] SANITY vs llista a mà (5 comarques, n={len(COSTANERS_MA)}): "
          f"{'TOTS OK ✓' if not falten else 'FALTEN: ' + ', '.join(falten)}")


if __name__ == "__main__":
    main()
