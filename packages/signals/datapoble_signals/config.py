"""Configuració central de la capa de senyals.

La taula ``SOURCES`` és el mirall operatiu de les fonts del cabal. Mateix patró
que ``packages/ingestion/config.py`` (Sondeig): si canvia un ``dataset_id`` o una
llicència, s'actualitza aquí.
"""
from __future__ import annotations

from pathlib import Path

# Arrel del repo: .../packages/signals/datapoble_signals/config.py -> repo
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"           # gitignored (es regenera amb un comando)
EVENTS_DIR = DATA_DIR / "events"     # versionat (com data/marts/)

# Comarca del pilot. El Berguedà = comarca 14 (codi Idescat).
# Escala a Catalunya = fora d'aquest PR (es parametritza canviant el filtre).
COMARCA_PILOT = "Berguedà"
COMARCA_CODI_PILOT = "14"

# Endpoint base Socrata (Dades Obertes de Catalunya).
SOCRATA_DOMAIN = "https://analisi.transparenciacatalunya.cat"

# Registre de fonts (procedència). Cada event hereta source/url/llicència d'aquí.
SOURCES: dict[str, dict] = {
    "contractacio": {
        "organisme": "Generalitat — Plataforma de Serveis de Contractació Pública",
        "producte": "Contractes menors adjudicats (publicació agregada)",
        "dataset_id": "ybgg-dgi6",
        "url": f"{SOCRATA_DOMAIN}/resource/ybgg-dgi6.json",
        "llicencia": "Dades Obertes de Catalunya",
        "kind": "socrata",
        "tipus_senyal_default": "contractacio",
    },
    "sequera": {
        "organisme": "Agència Catalana de l'Aigua (ACA)",
        "producte": (
            "Estat de sequera per unitats d'explotació i municipis a les "
            "Conques Internes de Catalunya"
        ),
        "dataset_id": "i5n8-43cw",
        "url": f"{SOCRATA_DOMAIN}/resource/i5n8-43cw.json",
        "llicencia": "Dades Obertes de Catalunya",
        "kind": "socrata",
        "tipus_senyal_default": "aigua_sequera",
    },
    # Radar de subvencions (C3/C4). NO és Socrata: API pròpia del SNPSAP.
    # `dataset_id` = None a propòsit: la BDNS no té id de dataset (no inventem).
    "subvencions_bdns": {
        "organisme": (
            "Ministerio de Hacienda — Sistema Nacional de Publicidad de "
            "Subvenciones y Ayudas Públicas (SNPSAP/BDNS)"
        ),
        "producte": "Convocatòries de subvencions i ajuts públics (API de consulta)",
        "dataset_id": None,
        "url": "https://www.infosubvenciones.es/bdnstrans/api/convocatorias/busqueda",
        # Llicència: la BDNS no publica una llicència oberta tipus CC; publica un
        # AVÍS LEGAL amb restriccions de reutilització. Es cita literalment (i cada
        # fitxa porta el seu camp `advertencia`) en comptes d'inventar-ne una.
        "llicencia": (
            "Avís legal del SNPSAP "
            "(https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) — "
            "reutilització subjecta a restriccions; dades dinàmiques, subjectes a "
            "correccions i eliminacions posteriors a l'extracció"
        ),
        "kind": "bdns",
        "tipus_senyal_default": None,  # una convocatòria no és un event del cabal
    },
}

# Carpeta versionada de la taula de subvencions (C3 §1: materialització a
# `data/subvencions/…parquet` + `_provenance.json` per càrrega).
SUBVENCIONS_DIR = DATA_DIR / "subvencions"


def raw_path(source: str) -> Path:
    """Carpeta crua per a una font, creada si cal."""
    p = RAW_DIR / source
    p.mkdir(parents=True, exist_ok=True)
    return p


def events_path(name: str) -> Path:
    """Ruta d'un parquet d'events (carpeta creada si cal)."""
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    return EVENTS_DIR / name


def subvencions_path(name: str) -> Path:
    """Ruta d'un artefacte de la taula de subvencions (carpeta creada si cal)."""
    SUBVENCIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SUBVENCIONS_DIR / name
