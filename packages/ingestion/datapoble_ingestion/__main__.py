"""CLI de la ingesta.

    python -m datapoble_ingestion all          # totes les fonts
    python -m datapoble_ingestion rtc
    python -m datapoble_ingestion residus
    python -m datapoble_ingestion idescat_emex
    python -m datapoble_ingestion electoral
    python -m datapoble_ingestion icaen_consum
    python -m datapoble_ingestion restauracio_osm
    python -m datapoble_ingestion serveis_osm
    python -m datapoble_ingestion demografia_origen
"""
from __future__ import annotations

import argparse
import json
import sys

from . import (
    demografia_origen,
    electoral,
    icaen_consum,
    idescat_emex,
    residus,
    restauracio_osm,
    rtc,
    serveis_osm,
)
from .config import COMARCA_CODI_PILOT, COMARCA_PILOT
from .municipis import BERGUEDA, BERGUEDA_INE5, CATALUNYA

# Ordre canònic de fonts.
SOURCE_NAMES = [
    "rtc", "residus", "idescat_emex", "electoral", "icaen_consum",
    "restauracio_osm", "serveis_osm", "demografia_origen",
]

# OSM encara no està des-acotat a Catalunya (cal bbox CAT + geometria 947 → F1.2b).
OSM_PENDENT_CAT = {"restauracio_osm", "serveis_osm"}


def _invoke(name: str, scope: str):
    """Crida el connector amb l'abast triat. `bergueda` = pilot (comportament previ);
    `catalunya` = sense filtre / registre dels 947."""
    berg = scope == "bergueda"
    if name == "rtc":
        return rtc.run(COMARCA_CODI_PILOT if berg else None)
    if name == "residus":
        return residus.run(COMARCA_PILOT if berg else None)
    if name == "icaen_consum":
        return icaen_consum.run(COMARCA_PILOT if berg else None)
    if name == "electoral":
        return electoral.run(municipis_ine5=BERGUEDA_INE5 if berg else None)
    if name == "idescat_emex":
        return idescat_emex.run(municipis=BERGUEDA if berg else CATALUNYA)
    if name == "demografia_origen":
        return demografia_origen.run(municipis=BERGUEDA if berg else CATALUNYA)
    if name in OSM_PENDENT_CAT:
        if not berg:
            raise NotImplementedError(
                f"{name}: OSM a escala Catalunya encara no des-acotat "
                "(F1.2b: bbox CAT + geometria dels 947)."
            )
        mod = restauracio_osm if name == "restauracio_osm" else serveis_osm
        return mod.run(municipis=BERGUEDA)
    raise ValueError(name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="datapoble_ingestion")
    parser.add_argument("source", choices=["all", *SOURCE_NAMES], help="font a ingerir (o 'all')")
    parser.add_argument(
        "--scope", choices=["bergueda", "catalunya"], default="bergueda",
        help="abast territorial: 'bergueda' (pilot, per defecte) o 'catalunya' (947 munis)",
    )
    args = parser.parse_args(argv)

    sources = SOURCE_NAMES if args.source == "all" else [args.source]
    results = []
    for name in sources:
        if args.source == "all" and args.scope == "catalunya" and name in OSM_PENDENT_CAT:
            print(f"[ingestion] {name} … OMÈS (OSM a CAT pendent de F1.2b)", file=sys.stderr)
            continue
        print(f"[ingestion] {name} ({args.scope}) …", file=sys.stderr)
        results.append(_invoke(name, args.scope))

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
