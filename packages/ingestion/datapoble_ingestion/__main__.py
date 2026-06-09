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

RUNNERS = {
    "rtc": rtc.run,
    "residus": residus.run,
    "idescat_emex": idescat_emex.run,
    "electoral": electoral.run,
    "icaen_consum": icaen_consum.run,
    "restauracio_osm": restauracio_osm.run,
    "serveis_osm": serveis_osm.run,
    "demografia_origen": demografia_origen.run,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="datapoble_ingestion")
    parser.add_argument(
        "source",
        choices=["all", *RUNNERS.keys()],
        help="font a ingerir (o 'all')",
    )
    args = parser.parse_args(argv)

    sources = list(RUNNERS) if args.source == "all" else [args.source]
    results = []
    for name in sources:
        print(f"[ingestion] {name} …", file=sys.stderr)
        results.append(RUNNERS[name]())

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
