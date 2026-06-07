"""Configuració central de la ingesta.

La taula ``SOURCES`` és el mirall operatiu de ``semantic/metrics.yml`` (secció
``sources``). Si allà canvia un dataset_id o una llicència, s'actualitza aquí.
"""
from __future__ import annotations

from pathlib import Path

# Arrel del repo: .../packages/ingestion/datapoble_ingestion/config.py -> repo
REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = REPO_ROOT / "data" / "raw"

# Comarca del pilot. El Berguedà és la comarca 14 (codi Idescat).
# Escala a Catalunya = fora d'aquest PR (es parametritza canviant aquest filtre).
COMARCA_PILOT = "Berguedà"
COMARCA_CODI_PILOT = "14"
N_MUNICIPIS_BERGUEDA = 31

# Convocatòries electorals del pilot (Parlament de Catalunya). id_eleccio = lletra
# (tipus) + any + sufix de repetició. A20241 = Parlament 2024; A20211 = 2021.
ELECCIONS_PILOT = ["A20241", "A20211"]

# Endpoint base Socrata (Dades Obertes de Catalunya).
SOCRATA_DOMAIN = "https://analisi.transparenciacatalunya.cat"

# Endpoint base Idescat EMEX.
IDESCAT_EMEX_BASE = "https://api.idescat.cat/emex/v1/dades.json"

# Overpass API (OpenStreetMap) — POIs d'amenity per a la densitat de restauració
# (2n proxy d'hostaleria, complement del vidre). Sense auth. Llista de miralls per
# robustesa (el primari respon 406 sense User-Agent → cal capçalera; vegeu connector).
OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)

# Registre de fonts (procedència). url_template documenta l'accés canònic.
SOURCES: dict[str, dict] = {
    "rtc": {
        "organisme": "Generalitat — Registre de Turisme de Catalunya",
        "producte": "Establiments d'allotjament turístic",
        "dataset_id": "t2h3-cgys",
        "url": f"{SOCRATA_DOMAIN}/resource/t2h3-cgys.json",
        "llicencia": "Dades Obertes de Catalunya",
        "kind": "socrata",
    },
    "residus": {
        "organisme": "Agència de Residus de Catalunya (ARC)",
        "producte": "Estadístiques de residus municipals",
        "dataset_id": "69zu-w48s",
        "url": f"{SOCRATA_DOMAIN}/resource/69zu-w48s.json",
        "llicencia": "Dades Obertes de Catalunya",
        "kind": "socrata",
        # NOTA (Sondeig, 2026-06-06): aquest MATEIX dataset conté totes les fraccions
        # de recollida selectiva per municipi (vidre, paper_i_cartr, envasos_lleugers,
        # mat_ria_org_nica…). El VIDRE és proxy d'hostaleria/turisme per a l'afinament
        # "pernocta vs excursionista de dia". L'stub `residus_fraccions.py` (no cablejat
        # a `all`) hi accedeix focalitzat; vegeu docs/poblacio-real-fonts.md §turisme.
    },
    # STUB (Sondeig, 2026-06-04): consum elèctric municipal per a l'indicador
    # "població real vs padró". Verificat en viu: cdmun=ine5, 2013-2024, sector
    # USOS DOMÈSTICS sobreviu al secret estadístic fins i tot a micromunicipis.
    # El connector existeix (icaen_consum.py) però NO està cablejat a l'`all`
    # fins que Talaia validi l'indicador. Vegeu docs/poblacio-real-fonts.md.
    "icaen_consum": {
        "organisme": "Institut Català d'Energia (ICAEN)",
        "producte": "Consum d'energia elèctrica per municipis i sectors de Catalunya",
        "dataset_id": "8idm-becu",
        "url": f"{SOCRATA_DOMAIN}/resource/8idm-becu.json",
        "llicencia": "Dades Obertes de Catalunya",
        "kind": "socrata",
    },
    "idescat_emex": {
        "organisme": "Idescat",
        "producte": "El municipi en xifres (EMEX) / Cens 2021",
        "dataset_id": None,
        "url": f"{IDESCAT_EMEX_BASE}?id={{codi6}}",
        "llicencia": "Idescat, reutilització amb atribució",
        "kind": "idescat_emex",
    },
    "electoral": {
        "organisme": "Generalitat — Departament competent en processos electorals",
        "producte": "Processos electorals - Vots (resultats per territori)",
        "dataset_id": "ntc4-rnwr",
        "url": f"{SOCRATA_DOMAIN}/resource/ntc4-rnwr.json",
        "llicencia": "Dades Obertes de Catalunya",
        "kind": "socrata",
    },
    # Restauració (CCAE-56: bars, restaurants, cafeteries, menjars ràpids) com a
    # 2n proxy d'hostaleria de la capa L3 (complement del vidre). PRIMARI = OSM via
    # Overpass (granular, obert, sense auth): es compten els POIs amb amenity in
    # (restaurant, cafe, bar, fast_food, pub, biergarten, ice_cream) i s'assignen al
    # municipi per punt-en-polígon amb la geometria REAL dels 31 munis
    # (packages/web/static/geo/bergueda-municipis.geojson).
    # FRONTERA HONESTA: OSM INFRA-MAPEJA les zones rurals → el compte és un MÍNIM, no
    # un cens. El contrast oficial Idescat (ee, CCAE-56) NO és municipal per API oberta
    # (l'EMEX només dóna "serveis" agregat; el detall municipal té secret estadístic).
    "restauracio_osm": {
        "organisme": "OpenStreetMap (col·laboradors) — via Overpass API",
        "producte": "Punts d'interès de restauració (amenity=restaurant/cafe/bar/…)",
        "dataset_id": None,
        "url": OVERPASS_ENDPOINTS[0],
        "llicencia": "ODbL (OpenStreetMap) — atribució + compartir-igual",
        "kind": "overpass",
    },
}


def raw_path(source: str) -> Path:
    """Carpeta crua per a una font, creada si cal."""
    p = RAW_DIR / source
    p.mkdir(parents=True, exist_ok=True)
    return p
