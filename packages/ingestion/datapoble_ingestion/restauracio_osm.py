"""Connector OpenStreetMap (Overpass) — establiments de restauració per municipi.

**Per què:** 2n proxy d'hostaleria de la capa L3 (pressió turística), complement del
VIDRE. El vidre mesura *activitat* d'hostaleria (ampolles consumides); el recompte de
locals de restauració mesura la *capacitat* instal·lada (stock). Dos senyals
independents que apunten al mateix fenomen = validació més robusta (vegeu
``docs/poblacio-real-metode.md`` §L3 i ``docs/poblacio-real-fonts.md`` §T2).

**Font i mètode.** Overpass API (OpenStreetMap), sense autenticació. Es compten els
POIs amb ``amenity`` ∈ {restaurant, cafe, bar, fast_food, pub, biergarten,
ice_cream} dins el *bounding box* del Berguedà, i s'assigna **cada POI al seu
municipi per PUNT-EN-POLÍGON** amb la geometria administrativa REAL dels 31 munis
(``packages/web/static/geo/bergueda-municipis.geojson``, mateixa ``ine5`` del
contracte) via l'extensió ``spatial`` de DuckDB. El bbox rectangular sobre-captura
municipis veïns (Bages, Solsonès, Ripollès, Lluçanès…); el punt-en-polígon els
**retalla** amb precisió a les 31 fronteres reals.

**FRONTERA HONESTA (innegociable).** OSM **infra-mapeja** les zones rurals: la
completesa del mapejat varia entre municipis. Per tant el recompte és un **MÍNIM
observat, NO un cens** d'establiments. Es comunica així al contracte i a la bitàcola.
El *contrast oficial* Idescat (estadística ``ee``, CCAE-56) **no és accessible a
nivell municipal per API oberta**: l'EMEX només dóna el sector "serveis" agregat (no
aïlla hostaleria) i el detall municipal d'establiments té **secret estadístic** als
micromunicipis. OSM és, doncs, l'única via municipal viable per al pilot.

**Sortida:** ``data/raw/restauracio_osm/restauracio_osm.parquet`` — **una fila per
municipi** (``ine5, codi6, municipi, restauracio_estab`` + desglossament per
amenity) + ``_provenance.json``. La densitat per 1000 hab es deriva a transform
(numerador OSM / padró Idescat), no aquí (fidelitat a la font).

**Robustesa:** reintents amb *backoff*, rotació de miralls Overpass i ``User-Agent``
explícit (el primari respon 406 sense capçalera). Determinista: l'snapshot d'OSM pot
variar amb el temps, però la query i l'assignació espacial són reproduïbles.
"""
from __future__ import annotations

import sys
import time

import duckdb
import pandas as pd
import requests

from .config import OVERPASS_ENDPOINTS, REPO_ROOT, raw_path
from .municipis import BERGUEDA
from .provenance import write_provenance

SOURCE = "restauracio_osm"

# Geometria administrativa real dels 31 municipis (mateixa ine5 del contracte).
# La compta el web però és la font de veritat geogràfica del repo.
GEOJSON = REPO_ROOT / "packages" / "web" / "static" / "geo" / "bergueda-municipis.geojson"

# CCAE-56 (serveis de menjars i begudes) mapejat a les amenities d'OSM més directes:
# restaurants, cafeteries, bars, menjars ràpids, pubs, cerveseries, geladeries.
AMENITIES = ("restaurant", "cafe", "bar", "fast_food", "pub", "biergarten", "ice_cream")

# Bounding box del Berguedà (south, west, north, east), derivat de la geometria
# real (envolupant dels 31 polígons, amb marge nul: el punt-en-polígon ja retalla).
BBOX = (41.89, 1.60, 42.33, 2.08)

# Escala Catalunya (F5): envolupant segur de tot el país + geometria dels 947. Una query Overpass
# CAT sencera és massa gran → es baixa per MOSAIC (tiles×tiles sub-bboxes); el punt-en-polígon
# retalla als 947 polígons reals i descarta el que cau fora.
BBOX_CAT = (40.50, 0.15, 42.92, 3.35)
GEOJSON_CAT = REPO_ROOT / "packages" / "web" / "static" / "geo" / "catalunya-municipis.geojson"

# Capçalera obligatòria: Overpass principal respon 406 sense User-Agent.
USER_AGENT = "datapoble-riusdegent/1.0 (observatori territorial; sondeig@datapoble.local)"
TIMEOUT = 190
RETRIES = 4


def build_query(bbox: tuple = BBOX) -> str:
    """Query Overpass QL: tots els POIs de restauració dins el bbox (node/way/rel)."""
    south, west, north, east = bbox
    amenity_re = "|".join(AMENITIES)
    return (
        "[out:json][timeout:180];\n"
        f"(\n  nwr[amenity~'^({amenity_re})$']({south},{west},{north},{east});\n);\n"
        "out center tags;"
    )


def fetch_overpass(query: str, session: requests.Session | None = None) -> list[dict]:
    """Descarrega els elements d'Overpass amb reintents i rotació de miralls.

    Robust: prova cada mirall; en error transitori (timeout, 429, 5xx, 406) reintenta
    amb *backoff* exponencial abans de passar al següent. Llança si tots fallen.
    """
    sess = session or requests.Session()
    headers = {"User-Agent": USER_AGENT}
    last_err: Exception | None = None
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(RETRIES):
            try:
                resp = sess.post(
                    endpoint, data={"data": query}, headers=headers, timeout=TIMEOUT
                )
                if resp.status_code in (429, 504, 502, 503, 500, 406):
                    raise requests.HTTPError(f"{resp.status_code} de {endpoint}")
                resp.raise_for_status()
                return resp.json().get("elements", [])
            except (requests.RequestException, ValueError) as exc:  # ValueError = JSON
                last_err = exc
                time.sleep(2 ** attempt)  # 1, 2, 4, 8 s
    raise RuntimeError(f"Overpass ha fallat a tots els miralls: {last_err!r}")


def _tiles(bbox: tuple, n: int) -> list[tuple]:
    """Divideix un bbox en n×n sub-bboxes (mosaic), per no rebentar Overpass a escala Catalunya."""
    south, west, north, east = bbox
    dlat, dlon = (north - south) / n, (east - west) / n
    return [
        (south + i * dlat, west + j * dlon, south + (i + 1) * dlat, west + (j + 1) * dlon)
        for i in range(n)
        for j in range(n)
    ]


def fetch_pois(bbox: tuple = BBOX, tiles: int = 1, session: requests.Session | None = None) -> list[dict]:
    """Baixa els POIs de restauració del bbox. Si `tiles>1`, per MOSAIC (tiles×tiles), combinant i
    deduplicant per (type, id) — les fronteres de tile poden repetir un POI."""
    sess = session or requests.Session()
    boxes = _tiles(bbox, tiles) if tiles > 1 else [bbox]
    seen: set = set()
    elements: list[dict] = []
    for k, box in enumerate(boxes):
        els = fetch_overpass(build_query(box), session=sess)
        for el in els:
            key = (el.get("type"), el.get("id"))
            if key not in seen:
                seen.add(key)
                elements.append(el)
        if tiles > 1:
            print(f"  [restauracio] tile {k + 1}/{len(boxes)}: {len(els)} POIs (acum {len(elements)})",
                  file=sys.stderr)
    return elements


def _poi_points(elements: list[dict]) -> list[dict]:
    """Extreu lon/lat + amenity de cada element (node: lat/lon; way/rel: center)."""
    pts: list[dict] = []
    for el in elements:
        tags = el.get("tags", {})
        amenity = tags.get("amenity")
        if amenity not in AMENITIES:
            continue
        if el.get("type") == "node":
            lon, lat = el.get("lon"), el.get("lat")
        else:  # way / relation → centroide
            center = el.get("center") or {}
            lon, lat = center.get("lon"), center.get("lat")
        if lon is None or lat is None:
            continue
        pts.append(
            {
                "osm_type": el.get("type"),
                "osm_id": el.get("id"),
                "amenity": amenity,
                "lon": float(lon),
                "lat": float(lat),
            }
        )
    return pts


def assign_to_municipis(points: list[dict], geojson=GEOJSON) -> pd.DataFrame:
    """Assigna cada POI al seu municipi per punt-en-polígon (DuckDB spatial).

    Retorna **una fila per municipi** de `geojson` (fins i tot amb compte 0) amb el total i el
    desglossament per amenity. Els POIs fora dels polígons (veïns capturats pel bbox) es **descarten**
    silenciosament — és el retall a la frontera.
    """
    con = duckdb.connect()
    con.execute("INSTALL spatial")
    con.execute("LOAD spatial")
    geo = geojson.resolve().as_posix()

    # Registra els POIs com a taula (buida si no n'hi ha cap, p. ex. snapshot buit).
    poi_df = pd.DataFrame(points, columns=["osm_type", "osm_id", "amenity", "lon", "lat"])
    con.register("poi_raw", poi_df)

    amenity_cols = ",\n        ".join(
        f"count(*) filter (where poi.amenity = '{a}') as n_{a}" for a in AMENITIES
    )
    df = con.execute(
        f"""
        with mun as (
            select ine5, nom, geom from st_read('{geo}')
        ),
        poi as (
            select *, st_point(lon, lat) as g from poi_raw
        ),
        joined as (
            select mun.ine5, mun.nom, poi.amenity
            from mun
            left join poi on st_contains(mun.geom, poi.g)
        )
        select
            ine5,
            any_value(nom) as nom_geo,
            count(amenity) as restauracio_estab,
            {amenity_cols}
        from joined poi
        group by ine5
        order by ine5
        """
    ).df()
    con.close()
    return df


def run(municipis: dict[str, str] = BERGUEDA, geojson=GEOJSON, bbox: tuple = BBOX, tiles: int = 1) -> dict:
    """Ingesta OSM de restauració per municipi. Idempotent. `geojson`+`bbox`+`tiles` parametritzen
    l'abast: pilot Berguedà (defecte) o tot Catalunya (geometria 947 + bbox CAT + mosaic de tiles).

    Determinista quant a query i assignació; l'snapshot d'OSM pot variar amb el temps (és un mínim
    observat, no un cens).
    """
    out_dir = raw_path(SOURCE)

    elements = fetch_pois(bbox, tiles)
    points = _poi_points(elements)
    counts = assign_to_municipis(points, geojson)

    # codi6 + nom oficial des del registre de municipis (no del nom d'OSM).
    ine5_to_codi6 = {codi6[:5]: codi6 for codi6 in municipis}
    ine5_to_nom = {codi6[:5]: nom for codi6, nom in municipis.items()}
    counts.insert(1, "codi6", counts["ine5"].map(ine5_to_codi6))
    counts.insert(2, "municipi", counts["ine5"].map(ine5_to_nom))
    counts = counts.drop(columns=["nom_geo"])

    out_file = out_dir / "restauracio_osm.parquet"
    counts.to_parquet(out_file, index=False)

    total = int(counts["restauracio_estab"].sum())
    assigned = total
    fetched = len(points)
    write_provenance(
        SOURCE,
        out_dir,
        row_count=len(counts),
        files=[out_file.name],
        query={
            "overpass_ql": build_query(bbox),
            "bbox_south_west_north_east": list(bbox),
            "tiles": tiles,
            "amenities": list(AMENITIES),
            "endpoints": list(OVERPASS_ENDPOINTS),
        },
        extra={
            "loader": "requests+duckdb_spatial",
            "n_municipis": len(counts),
            "format": "wide (1 fila per municipi)",
            "pois_fetched_in_bbox": fetched,
            "pois_assigned_to_31_munis": assigned,
            "pois_dropped_outside": fetched - assigned,
            "geometry": str(geojson.relative_to(REPO_ROOT).as_posix()),
            "note": (
                "OSM INFRA-MAPEJA zones rurals → compte = MÍNIM observat, no cens. "
                "Assignació per punt-en-polígon amb geometria real (ine5). POIs fora "
                "dels 31 polígons (municipis veïns del bbox) descartats. Idescat "
                "CCAE-56 oficial NO és municipal per API oberta (secret estadístic; "
                "l'EMEX només dóna 'serveis' agregat). Llicència ODbL (atribució + SA)."
            ),
        },
    )
    return {
        "source": SOURCE,
        "rows": len(counts),
        "files": [out_file.name],
        "pois_assigned": assigned,
        "pois_fetched": fetched,
    }


if __name__ == "__main__":
    print(run())
