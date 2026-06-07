"""Tests OFFLINE i deterministes del connector restauracio_osm.

No toquen la xarxa: es **mockeja la resposta d'Overpass** (la llista d'``elements``)
i es comprova (a) l'extracció de POIs i (b) l'assignació al municipi per
punt-en-polígon amb la geometria REAL del repo (DuckDB spatial, totalment local).

Coordenades deterministes (centroides verificats de la geometria del pilot):
  · Berga  (08022): lon 1.8476, lat 42.1006  → dins Berga
  · Gósol  (25100): lon 1.6688, lat 42.2086  → dins Gósol
  · Barcelona      : lon 2.17,   lat 41.39    → FORA dels 31 municipis (es descarta)
"""
from __future__ import annotations

import pandas as pd

from datapoble_ingestion import restauracio_osm as r


# Resposta d'Overpass simulada: nodes i un way-amb-center, dins i fora del pilot,
# més una amenity NO de restauració (s'ha de filtrar) i un POI sense coords.
FAKE_ELEMENTS = [
    {"type": "node", "id": 1, "lat": 42.1006, "lon": 1.8476, "tags": {"amenity": "restaurant"}},
    {"type": "node", "id": 2, "lat": 42.1006, "lon": 1.8476, "tags": {"amenity": "bar"}},
    {"type": "way", "id": 3, "center": {"lat": 42.2086, "lon": 1.6688}, "tags": {"amenity": "cafe"}},
    {"type": "node", "id": 4, "lat": 41.39, "lon": 2.17, "tags": {"amenity": "restaurant"}},  # Barcelona → fora
    {"type": "node", "id": 5, "lat": 42.1006, "lon": 1.8476, "tags": {"amenity": "pharmacy"}},  # no restauració
    {"type": "node", "id": 6, "tags": {"amenity": "bar"}},  # sense coords → es descarta
]


def test_poi_points_filters_amenities_and_coords():
    pts = r._poi_points(FAKE_ELEMENTS)
    # 4 POIs de restauració amb coords (id 1,2,3,4); pharmacy i el sense-coords fora.
    assert len(pts) == 4
    assert {p["osm_id"] for p in pts} == {1, 2, 3, 4}
    assert {p["amenity"] for p in pts} == {"restaurant", "bar", "cafe"}
    # El way pren el centroide.
    way = next(p for p in pts if p["osm_id"] == 3)
    assert way["lon"] == 1.6688 and way["lat"] == 42.2086


def test_assign_to_municipis_point_in_polygon():
    pts = r._poi_points(FAKE_ELEMENTS)
    df = r.assign_to_municipis(pts).set_index("ine5")

    # Sempre 31 files (tots els municipis, fins i tot amb compte 0).
    assert len(df) == 31

    # Berga: 1 restaurant + 1 bar = 2. Gósol: 1 cafe = 1. La resta: 0.
    assert int(df.loc["08022", "restauracio_estab"]) == 2
    assert int(df.loc["08022", "n_restaurant"]) == 1
    assert int(df.loc["08022", "n_bar"]) == 1
    assert int(df.loc["25100", "restauracio_estab"]) == 1
    assert int(df.loc["25100", "n_cafe"]) == 1

    # El POI de Barcelona (fora dels 31 polígons) NO s'assigna a cap municipi:
    # el total assignat (3) < POIs amb coords (4).
    assert int(df["restauracio_estab"].sum()) == 3


def test_assign_handles_empty_snapshot():
    # Un snapshot buit (cap POI) ha de retornar 31 municipis amb compte 0, sense petar.
    df = r.assign_to_municipis([])
    assert len(df) == 31
    assert int(df["restauracio_estab"].sum()) == 0


def test_build_query_contains_amenities_and_bbox():
    q = r.build_query()
    for amenity in r.AMENITIES:
        assert amenity in q
    # bbox (south,west,north,east) present a la query.
    assert "out center tags" in q
    assert isinstance(r.assign_to_municipis([]), pd.DataFrame)
