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
  4. **Aigües avall de l'atur** (D7): ``mart_tendencia`` (el Δ mensual i l'interanual
     canvien cada mes) + ``verify_tendencia.py`` + l'export web ``tauler.bergueda.json``.
     Sense aquest pas, el refresc mensual deixaria el JSON servit ENRERE respecte al
     parquet i el ``--check`` del CI cauria al PR següent — el forat de D4/D5, que aquí
     es tanca d'entrada.
  5. Actualitza ``semantic/metrics.yml``: el camp ``date:`` d'``atur_registrat`` amb el
     darrer mes carregat i el ``darrera_carrega:`` de la font ``sepe`` amb la data d'avui
     (E5 · frescor). Edició quirúrgica: els comentaris del fitxer són contracte i no es toquen.

NOTA sobre el pas 4 en un runner net: ``mart_tendencia`` depèn de ``mart_municipi`` i
``mart_demografia``, que aquest refresc NO reconstrueix (la seva raw —EMEX, origen— no
es baixa aquí: és anual i té el seu propi cicle). Es carreguen al magatzem des dels
PARQUETS VERSIONATS abans de construir la tendència. Així el model conserva els seus
``ref()`` de debò (lineage intacte) i el refresc mensual només toca el que canvia cada mes.

Ús:
    python tools/refresh_atur.py [--anys 2026 2025]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
METRICS = REPO / "semantic" / "metrics.yml"
TRANSFORM = REPO / "packages" / "transform"
MARTS = REPO / "data" / "marts"

# Marts VERSIONATS que mart_tendencia necessita però que aquest refresc NO reconstrueix
# (tenen el seu propi cicle, anual). Es carreguen al magatzem perquè els ref() del model
# resolguin en un runner net, sense haver de baixar la seva raw.
MARTS_UPSTREAM = ("mart_municipi", "mart_demografia")

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


def bump_darrera_carrega(avui: str) -> bool:
    """Posa ``darrera_carrega: "YYYY-MM-DD"`` a la font ``sepe`` (E5 · frescor).

    Acotada al bloc ``sepe:`` de ``sources`` fins al seu camp ``darrera_carrega``. És el
    que fa que el tauler pugui dir «mensual · darrera càrrega: …» amb una data que algú
    ha escrit de veritat, no una que es dedueix.
    """
    text = METRICS.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(\n  sepe:\n(?:    .*\n|    # .*\n)*?    darrera_carrega: ")\d{4}-\d{2}-\d{2}(")'
    )
    if not pattern.search(text):
        raise RuntimeError("no trobo darrera_carrega de la font sepe a metrics.yml")
    new_text = pattern.sub(rf"\g<1>{avui}\g<2>", text, count=1)
    if new_text == text:
        return False
    METRICS.write_text(new_text, encoding="utf-8")
    return True


def seed_marts_upstream() -> None:
    """Carrega al magatzem els marts versionats que la tendència necessita i que aquest
    refresc no reconstrueix. Només LECTURA dels parquets del repo: cap dada inventada,
    cap xarxa. Si un no hi és, es peta — val més que el refresc caigui que no pas que
    generi una tendència contra un mart absent."""
    import duckdb

    db = TRANSFORM / "datapoble.duckdb"
    con = duckdb.connect(str(db))
    try:
        for nom in MARTS_UPSTREAM:
            parquet = MARTS / f"{nom}.parquet"
            if not parquet.exists():
                raise RuntimeError(f"falta el mart versionat {parquet}")
            con.execute(
                f"create or replace table main.{nom} as "
                f"select * from read_parquet('{parquet.as_posix()}')"
            )
            print(f"[refresh_atur] magatzem ← {nom}.parquet (versionat)", file=sys.stderr)
    finally:
        con.close()


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

    # --- Aigües avall de l'atur (D7): la tendència i el JSON servit ---
    # Els dos Δ de l'atur (mes anterior i mateix mes de l'any anterior) canvien CADA MES:
    # si això no es refés aquí, el tauler ensenyaria la tendència del mes passat al
    # costat de la xifra d'aquest.
    seed_marts_upstream()
    _run([sys.executable, "-m", "dbt.cli.main", "run",
          "--project-dir", ".", "--profiles-dir", ".",
          "--select", "mart_tendencia"],
         cwd=TRANSFORM)
    _run([sys.executable, str(TRANSFORM / "verify_tendencia.py")])
    _run([sys.executable, str(REPO / "tools" / "export_tauler_web.py")])

    changed = bump_metrics_date(darrer)
    avui = date.today().isoformat()
    changed_carrega = bump_darrera_carrega(avui)
    print(json.dumps({
        "ingesta": res,
        "metrics_yml_date": darrer,
        "metrics_yml_canviat": changed,
        "darrera_carrega": avui,
        "darrera_carrega_canviada": changed_carrega,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
