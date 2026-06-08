"""Connector OpenStreetMap (Overpass) — comerç i serveis essencials per municipi.

**Per què (la tasca de Bea).** La tipologia ``capital_serveis`` no ha de voler dir
«municipi gran» sinó **«centre de serveis real»**: un poble que TÉ comerç i serveis
essencials que serveixen els pobles del voltant. Per distingir-ho cal un **senyal de
CENTRALITAT funcional**: quants establiments de comerç i serveis bàsics hi ha mapejats
al municipi. És germà del connector de restauració (``restauracio_osm.py``) —mateixa
via Overpass + punt-en-polígon— però mira l'altra cara de la centralitat: no
l'hostaleria (que sovint és turisme), sinó el **comerç quotidià i els serveis** que fan
que un poble sigui capçalera (supermercat, farmàcia, banc, ferreteria, metge, ajuntament…).

**Font i mètode.** Overpass API (OpenStreetMap), sense autenticació. Es compten els
POIs amb ``shop`` ∈ {supermarket, convenience, bakery, butcher, greengrocer,
hardware, …} i ``amenity`` ∈ {bank, pharmacy, post_office, townhall, fuel, doctors,
clinic, …} dins el *bounding box* del Berguedà, i s'assigna **cada POI al seu municipi
per PUNT-EN-POLÍGON** amb la geometria administrativa REAL dels 31 munis
(``packages/web/static/geo/bergueda-municipis.geojson``, mateixa ``ine5`` del
contracte) via l'extensió ``spatial`` de DuckDB. El bbox rectangular sobre-captura
municipis veïns; el punt-en-polígon els **retalla** a les 31 fronteres reals.

**El senyal és el COMPTE ABSOLUT.** A diferència de la restauració (on la densitat per
càpita aïlla el turisme), el que mesura la CENTRALITAT és el **nombre absolut**
d'establiments: un poble amb supermercat + farmàcia + banc + ferreteria és capçalera
encara que tingui pocs habitants; un poble dormitori gran sense cap d'aquests serveis
no ho és. Per això la sortida primària és ``serveis_estab`` (absolut). La densitat
``serveis_per_1000hab`` es deriva a transform (és secundària, útil per a context).

**FRONTERA HONESTA (innegociable).** OSM **infra-mapeja** les zones rurals: la
completesa del mapejat varia entre municipis. El recompte és un **MÍNIM observat, NO un
cens** d'establiments (mateix caveat que la restauració). El contrast oficial Idescat
(CCAE-47 comerç al detall, CCAE-64/86 serveis) **no és accessible a nivell municipal
per API oberta** (l'EMEX només dóna el sector "serveis" agregat; el detall té secret
estadístic als micromunicipis). OSM és l'única via municipal viable per al pilot.

**A ESCALA CATALUNYA (nota de calibratge).** El compte absolut és comparable DINS d'una
comarca (mateix teixit territorial). Entre comarques NO ho és directament: la signatura
de serveis d'un poble del Vallès, del Pirineu o de la costa són molt diferents. A
escala Catalunya el senyal s'haurà de **z-scoritzar PER COMARCA / tipus territorial**,
igual que ja fan els z-scores comarcals de la tipologia (vegeu ``mart_municipi.sql`` i
``docs/tipologia-municipal.md``).

**Sortida:** ``data/raw/serveis_osm/serveis_osm.parquet`` — **una fila per municipi**
(``ine5, codi6, municipi, serveis_estab`` + desglossament per categoria) +
``_provenance.json``. La densitat per 1000 hab es deriva a transform.

**Robustesa:** reintents amb *backoff*, rotació de miralls Overpass i ``User-Agent``
explícit (el primari respon 406 sense capçalera). Determinista quant a query i
assignació espacial (l'snapshot d'OSM pot variar amb el temps).
"""
from __future__ import annotations

import time
from pathlib import Path

import duckdb
import pandas as pd
import requests

from .config import OVERPASS_ENDPOINTS, REPO_ROOT, raw_path
from .municipis import BERGUEDA
from .provenance import write_provenance

SOURCE = "serveis_osm"

# Geometria administrativa real dels 31 municipis (mateixa ine5 del contracte).
GEOJSON = REPO_ROOT / "packages" / "web" / "static" / "geo" / "bergueda-municipis.geojson"

# Comerç quotidià (shop) — alimentació + bàsics de capçalera. Aproxima CCAE-47
# (comerç al detall) amb les claus shop d'OSM més directes i fiables al rural.
SHOPS = (
    "supermarket",
    "convenience",
    "bakery",
    "butcher",
    "greengrocer",
    "hardware",
    "doityourself",
    "chemist",
    "kiosk",
    "general",
)

# Serveis essencials (amenity) — el que fa que un poble sigui capçalera funcional:
# banca, sanitat de proximitat, administració, combustible, correus.
AMENITY_SERVICES = (
    "bank",
    "pharmacy",
    "post_office",
    "townhall",
    "fuel",
    "doctors",
    "clinic",
    "hospital",
    "veterinary",
    "school",
)

# Bounding box del Berguedà (south, west, north, east), idèntic al de restauracio_osm
# (envolupant dels 31 polígons; el punt-en-polígon retalla els veïns capturats).
BBOX = (41.89, 1.60, 42.33, 2.08)

# Capçalera obligatòria: Overpass principal respon 406 sense User-Agent.
USER_AGENT = "datapoble-riusdegent/1.0 (observatori territorial; sondeig@datapoble.local)"
TIMEOUT = 190
RETRIES = 4


def build_query() -> str:
    """Query Overpass QL: tots els POIs de comerç/serveis dins el bbox (node/way/rel)."""
    south, west, north, east = BBOX
    shop_re = "|".join(SHOPS)
    amenity_re = "|".join(AMENITY_SERVICES)
    return (
        "[out:json][timeout:180];\n"
        "(\n"
        f"  nwr[shop~'^({shop_re})$']({south},{west},{north},{east});\n"
        f"  nwr[amenity~'^({amenity_re})$']({south},{west},{north},{east});\n"
        ");\n"
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


def _poi_points(elements: list[dict]) -> list[dict]:
    """Extreu lon/lat + categoria de cada POI de comerç/serveis.

    ``categoria`` = ``shop:<valor>`` o ``amenity:<valor>`` (per al desglossament). Un
    POI amb tots dos tags es classifica per ``shop`` (té prioritat); els POIs sense cap
    clau de la llista es descarten.
    """
    pts: list[dict] = []
    for el in elements:
        tags = el.get("tags", {})
        shop = tags.get("shop")
        amenity = tags.get("amenity")
        if shop in SHOPS:
            categoria = f"shop:{shop}"
        elif amenity in AMENITY_SERVICES:
            categoria = f"amenity:{amenity}"
        else:
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
                "categoria": categoria,
                "lon": float(lon),
                "lat": float(lat),
            }
        )
    return pts


# Categories de desglossament (ordre estable de columnes n_*): comerç primer, serveis
# després. Cada una és una columna `n_<clau>` a la sortida (traçabilitat / QA).
CATEGORIES = tuple(f"shop:{s}" for s in SHOPS) + tuple(
    f"amenity:{a}" for a in AMENITY_SERVICES
)


def _col_name(categoria: str) -> str:
    """`shop:supermarket` -> `n_shop_supermarket` (nom de columna SQL-segur)."""
    return "n_" + categoria.replace(":", "_")


def assign_to_municipis(points: list[dict]) -> pd.DataFrame:
    """Assigna cada POI al seu municipi per punt-en-polígon (DuckDB spatial).

    Retorna **una fila per municipi** (els 31, fins i tot amb compte 0) amb el total
    i el desglossament per categoria. Els POIs fora dels 31 polígons (municipis veïns
    capturats pel bbox) es **descarten** silenciosament — és el retall a la frontera.
    """
    con = duckdb.connect()
    con.execute("INSTALL spatial")
    con.execute("LOAD spatial")
    geo = GEOJSON.resolve().as_posix()

    poi_df = pd.DataFrame(
        points, columns=["osm_type", "osm_id", "categoria", "lon", "lat"]
    )
    con.register("poi_raw", poi_df)

    cat_cols = ",\n        ".join(
        f"count(*) filter (where poi.categoria = '{c}') as {_col_name(c)}"
        for c in CATEGORIES
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
            select mun.ine5, mun.nom, poi.categoria
            from mun
            left join poi on st_contains(mun.geom, poi.g)
        )
        select
            ine5,
            any_value(nom) as nom_geo,
            count(categoria) as serveis_estab,
            {cat_cols}
        from joined poi
        group by ine5
        order by ine5
        """
    ).df()
    con.close()
    return df


def run(municipis: dict[str, str] = BERGUEDA) -> dict:
    """Ingesta OSM de comerç i serveis essencials per als 31 municipis. Idempotent.

    Determinista quant a query i assignació; l'snapshot d'OSM pot variar amb el temps
    (és un mínim observat, no un cens).
    """
    out_dir = raw_path(SOURCE)

    elements = fetch_overpass(build_query())
    points = _poi_points(elements)
    counts = assign_to_municipis(points)

    # codi6 + nom oficial des del registre de municipis (no del nom d'OSM).
    ine5_to_codi6 = {codi6[:5]: codi6 for codi6 in municipis}
    ine5_to_nom = {codi6[:5]: nom for codi6, nom in municipis.items()}
    counts.insert(1, "codi6", counts["ine5"].map(ine5_to_codi6))
    counts.insert(2, "municipi", counts["ine5"].map(ine5_to_nom))
    counts = counts.drop(columns=["nom_geo"])

    out_file = out_dir / "serveis_osm.parquet"
    counts.to_parquet(out_file, index=False)

    total = int(counts["serveis_estab"].sum())
    fetched = len(points)
    write_provenance(
        SOURCE,
        out_dir,
        row_count=len(counts),
        files=[out_file.name],
        query={
            "overpass_ql": build_query(),
            "bbox_south_west_north_east": list(BBOX),
            "shops": list(SHOPS),
            "amenity_services": list(AMENITY_SERVICES),
            "endpoints": list(OVERPASS_ENDPOINTS),
        },
        extra={
            "loader": "requests+duckdb_spatial",
            "n_municipis": len(counts),
            "format": "wide (1 fila per municipi)",
            "pois_fetched_in_bbox": fetched,
            "pois_assigned_to_31_munis": total,
            "pois_dropped_outside": fetched - total,
            "geometry": str(GEOJSON.relative_to(REPO_ROOT).as_posix()),
            "note": (
                "Senyal de CENTRALITAT funcional (centre de serveis real), germà de "
                "restauracio_osm. El senyal primari és el COMPTE ABSOLUT serveis_estab "
                "(no la densitat): un poble és capçalera per TENIR supermercat/farmàcia/"
                "banc/ferreteria, independentment de la mida. OSM INFRA-MAPEJA el rural "
                "→ compte = MÍNIM observat, no cens. Assignació per punt-en-polígon amb "
                "geometria real (ine5); POIs fora dels 31 polígons descartats. Idescat "
                "(CCAE-47 comerç, serveis) NO és municipal per API oberta (secret "
                "estadístic; l'EMEX només dóna 'serveis' agregat). A escala Catalunya el "
                "senyal s'ha de z-scoritzar PER COMARCA (signatures molt diferents). "
                "Llicència ODbL (atribució + compartir-igual)."
            ),
        },
    )
    return {
        "source": SOURCE,
        "rows": len(counts),
        "files": [out_file.name],
        "pois_assigned": total,
        "pois_fetched": fetched,
    }


if __name__ == "__main__":
    print(run())
