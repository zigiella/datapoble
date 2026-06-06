"""CLI de la capa de senyals.

    python -m datapoble_signals contractacio   # descarrega + escriu events
    python -m datapoble_signals sequera         # descarrega + escriu events de sequera (ACA)
    python -m datapoble_signals all             # totes les fonts
"""
from __future__ import annotations

import argparse
import json
import sys

from . import contractacio, sequera

RUNNERS = {
    "contractacio": contractacio.run,
    "sequera": sequera.run,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="datapoble_signals")
    parser.add_argument(
        "source",
        choices=["all", *RUNNERS.keys()],
        help="font de senyal a normalitzar (o 'all')",
    )
    args = parser.parse_args(argv)

    sources = list(RUNNERS) if args.source == "all" else [args.source]
    results = []
    for name in sources:
        print(f"[signals] {name} …", file=sys.stderr)
        results.append(RUNNERS[name]())

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
