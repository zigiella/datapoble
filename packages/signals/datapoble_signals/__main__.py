"""CLI de la capa de senyals.

    python -m datapoble_signals contractacio   # descarrega + escriu events
    python -m datapoble_signals sequera         # descarrega + escriu events de sequera (ACA)
    python -m datapoble_signals all             # totes les fonts (rastres)
    python -m datapoble_signals convergencia    # motor de convergència (turisme × sequera)
    python -m datapoble_signals licitacions     # capa d'intel·ligència institucional (taxonomia + repartiment + indicador)

``convergencia`` i ``licitacions`` NO descarreguen res: llegeixen els parquets ja
materialitzats (read-only) i escriuen sortides derivades a ``data/events/``. Per
això queden **fora** d'``all`` (que recull fonts); cal córrer-los després que els
rastres existeixin. ``licitacions`` enriqueix la contractació amb la taxonomia
territorial, reparteix els events comarcals als municipis i calcula l'indicador
``dependencia_supramunicipal``.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import contractacio, convergencia, licitacions, sequera

# Fonts (descàrrega de rastres). ``all`` les recull totes.
RUNNERS = {
    "contractacio": contractacio.run,
    "sequera": sequera.run,
}

# Derivats (operen sobre parquets ja materialitzats, sense xarxa). Fora d'``all``.
DERIVED = {
    "convergencia": convergencia.run,
    "licitacions": licitacions.run,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="datapoble_signals")
    parser.add_argument(
        "source",
        choices=["all", *RUNNERS.keys(), *DERIVED.keys()],
        help="font de senyal a normalitzar ('all' = tots els rastres), o un derivat ('convergencia')",
    )
    args = parser.parse_args(argv)

    all_runners = {**RUNNERS, **DERIVED}
    sources = list(RUNNERS) if args.source == "all" else [args.source]
    results = []
    for name in sources:
        print(f"[signals] {name} …", file=sys.stderr)
        results.append(all_runners[name]())

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
