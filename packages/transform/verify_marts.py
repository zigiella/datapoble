"""Verificació de la mart contra docs/data-sources.md (Experiment 0).

Comprova que Castellar (08052) i Berga (08022) cuadren amb els valors verificats
en viu. Surt amb codi != 0 si algun ancoratge falla → apte per a CI.

    python packages/transform/verify_marts.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MART = REPO / "data" / "marts" / "mart_municipi_bergueda.parquet"

# Ancoratges de docs/data-sources.md (§8 "Hechos verificados clave").
# (valor_esperat, tolerància_absoluta)
ANCHORS: dict[str, dict[str, tuple[float, float]]] = {
    "08052": {  # Castellar de n'Hug
        "poblacio": (166, 0),
        "hab_total": (276, 0),
        "hab_principal": (71, 0),
        "hab_noprincipal": (205, 0),
        "pct_noprincipal": (74.3, 0.1),
        "hab_per_hab": (1.66, 0.01),
        "rtc_total": (30, 0),
        "rtc_per_1000hab": (181, 1),
    },
    "08022": {  # Berga
        "rtc_total": (45, 0),
        "rtc_hut": (36, 0),
        "rtc_per_1000hab": (2.6, 0.1),
    },
}

N_MUNICIPIS = 31


def main() -> int:
    if not MART.exists():
        print(f"FALLA: no existeix {MART} (executa primer dbt build)", file=sys.stderr)
        return 2

    df = pd.read_parquet(MART).set_index("ine5")
    errors: list[str] = []

    if len(df) != N_MUNICIPIS:
        errors.append(f"row count {len(df)} != {N_MUNICIPIS}")

    for ine5, checks in ANCHORS.items():
        if ine5 not in df.index:
            errors.append(f"falta municipi {ine5}")
            continue
        row = df.loc[ine5]
        for col, (expected, tol) in checks.items():
            got = row[col]
            if pd.isna(got) or abs(float(got) - expected) > tol:
                errors.append(f"{ine5}.{col}: got={got} expected={expected}±{tol}")

    if errors:
        print("VERIFICACIÓ FALLIDA:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"VERIFICACIÓ OK · {len(df)} municipis · Castellar i Berga cuadren amb docs/data-sources.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
