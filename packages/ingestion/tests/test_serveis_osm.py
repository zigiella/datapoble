"""Tests OFFLINE i deterministes del connector serveis_osm.

No toquen la xarxa: es **mockeja la resposta d'Overpass** (la llista d'``elements``)
i es comprova (a) l'extracció/classificació de POIs de comerç i serveis i (b)
l'assignació al municipi per punt-en-polígon amb la geometria REAL del repo (DuckDB
spatial, totalment local). Mateix patró que test_restauracio_osm.

Coordenades deterministes (centroides verificats de la geometria del pilot):
  · Berga  (08022): lon 1.8476, lat 42.1006  → dins Berga
  · Gósol  (25100): lon 1.6688, lat 42.2086  → dins Gósol
  · Barcelona      : lon 2.17,   lat 41.39    → FORA dels 31 municipis (es descarta)
"""
from __future__ import annotations

import pandas as pd

from datapoble_ingestion import serveis_osm as s


# Resposta d'Overpass simulada: comerç (shop) i serveis (amenity), dins i fora del
# pilot, més un POI amb tag NO de la llista (s'ha de filtrar), un POI shop+amenity
# alhora (ha de comptar com a shop, té prioritat) i un POI sense coords.
FAKE_ELEMENTS = [
    {"type": "node", "id": 1, "lat": 42.1006, "lon": 1.8476, "tags": {"shop": "supermarket"}},
    {"type": "node", "id": 2, "lat": 42.1006, "lon": 1.8476, "tags": {"amenity": "pharmacy"}},
    {"type": "way", "id": 3, "center": {"lat": 42.2086, "lon": 1.6688}, "tags": {"amenity": "bank"}},
    {"type": "node", "id": 4, "lat": 41.39, "lon": 2.17, "tags": {"shop": "bakery"}},  # Barcelona → fora
    {"type": "node", "id": 5, "lat": 42.1006, "lon": 1.8476, "tags": {"amenity": "restaurant"}},  # no serveis
    {"type": "node", "id": 6, "lat": 42.1006, "lon": 1.8476, "tags": {"shop": "butcher", "amenity": "bank"}},  # shop guanya
    {"type": "node", "id": 7, "tags": {"shop": "convenience"}},  # sense coords → es descarta
]


def test_poi_points_classifies_shop_amenity_and_filters():
    pts = s._poi_points(FAKE_ELEMENTS)
    # 5 POIs vàlids amb coords (id 1,2,3,4,6); el restaurant i el sense-coords fora.
    assert len(pts) == 5
    assert {p["osm_id"] for p in pts} == {1, 2, 3, 4, 6}
    cats = {p["osm_id"]: p["categoria"] for p in pts}
    assert cats[1] == "shop:supermarket"
    assert cats[2] == "amenity:pharmacy"
    assert cats[3] == "amenity:bank"
    # POI amb shop + amenity alhora → es classifica per shop (prioritat).
    assert cats[6] == "shop:butcher"
    # El way pren el centroide.
    way = next(p for p in pts if p["osm_id"] == 3)
    assert way["lon"] == 1.6688 and way["lat"] == 42.2086


def test_assign_to_municipis_point_in_polygon():
    pts = s._poi_points(FAKE_ELEMENTS)
    df = s.assign_to_municipis(pts).set_index("ine5")

    # Sempre 31 files (tots els municipis, fins i tot amb compte 0).
    assert len(df) == 31

    # Berga: supermarket + pharmacy + butcher = 3. Gósol: bank = 1. La resta: 0.
    assert int(df.loc["08022", "serveis_estab"]) == 3
    assert int(df.loc["08022", "n_shop_supermarket"]) == 1
    assert int(df.loc["08022", "n_amenity_pharmacy"]) == 1
    assert int(df.loc["08022", "n_shop_butcher"]) == 1
    assert int(df.loc["25100", "serveis_estab"]) == 1
    assert int(df.loc["25100", "n_amenity_bank"]) == 1

    # El POI de Barcelona (fora dels 31 polígons) NO s'assigna a cap municipi:
    # el total assignat (4) < POIs amb coords (5).
    assert int(df["serveis_estab"].sum()) == 4


def test_assign_handles_empty_snapshot():
    # Un snapshot buit (cap POI) ha de retornar 31 municipis amb compte 0, sense petar.
    df = s.assign_to_municipis([])
    assert len(df) == 31
    assert int(df["serveis_estab"].sum()) == 0


def test_build_query_contains_shops_amenities_and_bbox():
    q = s.build_query()
    for shop in s.SHOPS:
        assert shop in q
    for amenity in s.AMENITY_SERVICES:
        assert amenity in q
    assert "out center tags" in q
    assert isinstance(s.assign_to_municipis([]), pd.DataFrame)
