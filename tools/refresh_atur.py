#!/usr/bin/env python3
"""Refresh mensual de l'atur registrat SEPE (D1) — orquestrador del workflow.

L'invoca el workflow programat ``refresh-atur.yml`` (cron mensual; MAI el CI de
PR — el CI és 100% offline). No committeja res: deixa els artefactes regenerats
al working tree i el workflow els puja com a *artifacts*; Talaia els committeja
per la porta del PR (mateix patró que ``gen-fitxa``).

Passos:
  1. Ingesta SEPE — per defecte, TOTA la sèrie (2006 → avui): la raw és
     gitignored i el runner del workflow parteix de zero; refrescar-ho tot manté
     l'operació sense estat (~21 fitxers un cop al mes, ús educat).
  2. ``dbt build`` de ``stg_atur_sepe`` + ``mart_pols_mensual`` (amb els seus
     data tests) → regenera ``data/marts/mart_pols_mensual.parquet``.
  3. Verificació offline (``verify_pols_mensual.py``): àncores byte-match,
     doctrina del «<5», cobertura 947, forats declarats.
  4. Actualitza el camp ``date:`` d'``atur_registrat`` a ``semantic/metrics.yml``
     amb el darrer mes carregat (edició quirúrgica: els comentaris del fitxer
     són contracte i no es toquen).

Ús:
    python tools/refresh_atur.py [--anys 2026 2025]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
METRICS = REPO / "semantic" / "metrics.yml"
TRANSFORM = REPO / "packages" / "transform"

sys.path.insert(0, str(REPO / "packages" / "ingestion"))


def _run(cmd: list[str], cwd: Path = REPO) -> None:
    print(f"[refresh_atur] $ {' '.join(cmd)}", file=sys.stderr)
    subprocess.run(cmd, check=True, cwd=cwd)


def bump_metrics_date(darrer_mes: str) -> bool:
    """Posa ``date: "YYYY-MM"`` a l'entrada atur_registrat (edició quirúrgica).

    Regex acotada al bloc ``atur_registrat:`` fins al camp ``date:`` — no toca
    cap altra entrada ni cap comentari. Retorna True si ha canviat el fitxer.
    """
    text = METRICS.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(\n  atur_registrat:\n(?:    .*\n)*?    date: ")\d{4}-\d{2}(")'
    )
    if not pattern.search(text):
        raise RuntimeError("no trobo el camp date de atur_registrat a metrics.yml")
    new_text = pattern.sub(rf"\g<1>{darrer_mes}\g<2>", text, count=1)
    if new_text == text:
        return False
    METRICS.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anys", nargs="*", type=int, default=None,
                        help="anys a refrescar (per defecte: tota la sèrie 2006→avui)")
    args = parser.parse_args()

    from datapoble_ingestion import atur_sepe  # import tardà: sys.path ja apunta al paquet

    res = atur_sepe.run(years=args.anys)
    darrer = res["darrer_mes"]
    if not darrer:
        print("[refresh_atur] cap mes carregat — res a fer", file=sys.stderr)
        return 1

    # dbt s'invoca DES DE packages/transform: les vars raw_root/marts_root del
    # projecte són camins relatius a aquest directori (vegeu dbt_project.yml).
    _run([sys.executable, "-m", "dbt.cli.main", "build",
          "--project-dir", ".", "--profiles-dir", ".",
          "--select", "stg_atur_sepe", "mart_pols_mensual"],
         cwd=TRANSFORM)
    _run([sys.executable, str(TRANSFORM / "verify_pols_mensual.py")])

    changed = bump_metrics_date(darrer)
    print(json.dumps({
        "ingesta": res,
        "metrics_yml_date": darrer,
        "metrics_yml_canviat": changed,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
