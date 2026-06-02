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

# Endpoint base Socrata (Dades Obertes de Catalunya).
SOCRATA_DOMAIN = "https://analisi.transparenciacatalunya.cat"

# Endpoint base Idescat EMEX.
IDESCAT_EMEX_BASE = "https://api.idescat.cat/emex/v1/dades.json"

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
    },
    "idescat_emex": {
        "organisme": "Idescat",
        "producte": "El municipi en xifres (EMEX) / Cens 2021",
        "dataset_id": None,
        "url": f"{IDESCAT_EMEX_BASE}?id={{codi6}}",
        "llicencia": "Idescat, reutilització amb atribució",
        "kind": "idescat_emex",
    },
}


def raw_path(source: str) -> Path:
    """Carpeta crua per a una font, creada si cal."""
    p = RAW_DIR / source
    p.mkdir(parents=True, exist_ok=True)
    return p
