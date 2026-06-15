#!/usr/bin/env python3
"""Extreu la renda municipal catalana de l'INE ADRH (taula 30824) com a covariable del Nivell C.

L'INE ADRH (Atlas de Distribución de Renta de los Hogares) es baixa com un CSV gegant (~335 MB,
tot Espanya × municipi/districte/secció × indicadors × anys). Aquí en treiem NOMÉS les files de
nivell MUNICIPI (Districte i Secció buits), indicador «Renta neta media por persona», any 2023,
de les 4 províncies catalanes (08/17/25/43). Streaming: no carrega el fitxer sencer a memòria.

El fitxer font viu FORA del repo (OneDrive, massa gros i és estatal); l'artefacte de sortida és
petit i committejable (carril dades intern). Join amb la resta per `ine5`.

Ús:  python tools/extract_renda.py [ruta_csv_30824]
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SRC = r"C:\Users\usuario\OneDrive\Desktop\CAJON\30824.csv"
OUT = REPO / "data" / "territorial" / "renda_municipi_cat.csv"

INDICADOR = "Renta neta media por persona"
ANY = "2023"
PROV_CAT = ("08", "17", "25", "43")  # Barcelona, Girona, Lleida, Tarragona


def _renda(v: str):
    """«16.429» (separador de milers «.», format espanyol) → 16429. «..»/buit → None."""
    v = (v or "").strip()
    if v in ("", "..", "(..)", "-", "."):
        return None
    try:
        return int(v.replace(".", ""))
    except ValueError:
        return None


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    src = Path(argv[0]) if argv else Path(DEFAULT_SRC)
    if not src.exists():
        print(f"FALLA: no existeix {src}", file=sys.stderr)
        return 2

    rows: dict[str, dict] = {}
    n_seen = 0
    with src.open("r", encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh, delimiter=";")
        header = next(r)  # Municipios;Distritos;Secciones;Indicadores de renta media;Periodo;Total
        for row in r:
            if len(row) < 6:
                continue
            muni, distr, secc, indic, periode, total = row[0], row[1], row[2], row[3], row[4], row[5]
            # Nivell MUNICIPI = districte i secció buits.
            if distr.strip() or secc.strip():
                continue
            if indic.strip() != INDICADOR or periode.strip() != ANY:
                continue
            code = muni.strip().split(" ", 1)[0]
            if code[:2] not in PROV_CAT or len(code) != 5:
                continue
            n_seen += 1
            nom = muni.strip().split(" ", 1)[1] if " " in muni.strip() else ""
            rows[code] = {"ine5": code, "municipi": nom, "renda_neta_persona_2023": _renda(total)}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=["ine5", "municipi", "renda_neta_persona_2023"])
        w.writeheader()
        for k in sorted(rows):
            w.writerow(rows[k])

    vals = [r["renda_neta_persona_2023"] for r in rows.values() if r["renda_neta_persona_2023"]]
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {len(rows)} municipis catalans (2023)")
    if vals:
        vals.sort()
        print(f"  renda/persona: min {min(vals):,} · mediana {vals[len(vals)//2]:,} · max {max(vals):,} €")
        print(f"  amb dada: {len(vals)}/{len(rows)} (buits/secret: {len(rows)-len(vals)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
