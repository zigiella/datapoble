#!/usr/bin/env python3
"""Paquet de consultoria: la base de dades plana + el diccionari d'indicadors.

Genera, de forma reproduïble, els dos artefactes de DADES del dossier de consultoria, a partir del
que ja és la veritat del web (`data/web/municipis.catalunya.json`, F3) + el mapatge territorial:

  · municipis-catalunya.csv  — UNA fila per municipi (947) amb ine5, codi6, nom, comarca, vegueria i
    TOTS els valors d'indicador. És la base de dades sencera, plana, per a anàlisi extern.
  · diccionari-indicadors.csv — UNA fila per indicador: clau, etiqueta (ca/es), dimensió, unitat,
    format, font (procedència), estat (public/planned) i definició canònica. És el diccionari.

Tot surt del contracte + els marts (cap número inventat). Sortida a docs/dossier-consultoria-2026-06/.
Ús:  python tools/export_dossier.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAT = REPO / "data" / "web" / "municipis.catalunya.json"
TERR = REPO / "data" / "web" / "municipis-territori.json"
OUT_DIR = REPO / "docs" / "dossier-consultoria-2026-06"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not CAT.exists():
        print(f"FALLA: no existeix {CAT} (executa export_web_municipis.py --scope catalunya)", file=sys.stderr)
        return 2

    data = json.loads(CAT.read_text(encoding="utf-8"))
    munis = data["municipis"]
    metrics = data["metrics"]
    terr = json.loads(TERR.read_text(encoding="utf-8")) if TERR.exists() else {}
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Ordre de columnes d'indicador = ordre del catàleg (estable, llegible).
    metric_keys = list(metrics.keys())

    # --- 1) Base de dades plana (1 fila/muni) ---
    db = OUT_DIR / "municipis-catalunya.csv"
    with db.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ine5", "codi6", "municipi", "comarca", "vegueria", *metric_keys])
        for ine5, m in sorted(munis.items()):
            t = terr.get(ine5, {})
            vals = m.get("values", {})
            w.writerow([
                ine5, m.get("idescat6", ""), m.get("nom", ""),
                t.get("comarca", ""), t.get("vegueria", ""),
                *[vals.get(k, "") if vals.get(k) is not None else "" for k in metric_keys],
            ])

    # --- 2) Diccionari d'indicadors (1 fila/indicador) ---
    dic = OUT_DIR / "diccionari-indicadors.csv"
    with dic.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["clau", "etiqueta_ca", "etiqueta_es", "dimensio", "unitat", "format",
                    "font", "estat", "definicio_ca"])
        for k in metric_keys:
            md = metrics[k]
            lab = md.get("label") or {}
            unit = md.get("unit") or {}
            defi = md.get("definicio") or md.get("note") or {}
            w.writerow([
                k, lab.get("ca", ""), lab.get("es", ""), md.get("dimension", ""),
                unit.get("ca", "") if isinstance(unit, dict) else unit,
                md.get("format", ""), md.get("source", ""), md.get("status", ""),
                defi.get("ca", "") if isinstance(defi, dict) else "",
            ])

    print(f"Escrit {db.relative_to(REPO).as_posix()} · {len(munis)} munis × {len(metric_keys)} indicadors")
    print(f"Escrit {dic.relative_to(REPO).as_posix()} · {len(metric_keys)} indicadors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
