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
        "IETR": (89.4, 0.5),       # prototip: #1 de la comarca
        "IETR_rank": (1, 0),
    },
    "08022": {  # Berga
        "rtc_total": (45, 0),
        "rtc_hut": (36, 0),
        "rtc_per_1000hab": (2.6, 0.1),
        "IETR": (0.3, 0.5),        # prototip: #31 de la comarca
        "IETR_rank": (31, 0),
    },
}

N_MUNICIPIS = 31

# Validació externa de l'IETR: ha de predir la càrrega real (residus). Spearman
# entre IETR i kg_hab_any > llindar. En el prototip va sortir 0,87.
SPEARMAN_MIN = 0.8


def _spearman(a: "pd.Series", b: "pd.Series") -> float:
    """Correlació de Spearman = Pearson sobre els rangs (sense dependència de scipy)."""
    return float(a.rank().corr(b.rank()))


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

    # Validació externa IETR ↔ residus (l'índex prediu la càrrega real).
    if {"IETR", "kg_hab_any"}.issubset(df.columns) and df["IETR"].notna().any():
        rho = _spearman(df["IETR"], df["kg_hab_any"])
        if pd.isna(rho) or rho <= SPEARMAN_MIN:
            errors.append(f"Spearman(IETR, kg_hab_any)={rho:.3f} <= {SPEARMAN_MIN}")
        else:
            print(f"Spearman(IETR, kg_hab_any) = {rho:.3f} (> {SPEARMAN_MIN}) · l'IETR prediu la càrrega real")

    if errors:
        print("VERIFICACIÓ FALLIDA:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"VERIFICACIÓ OK · {len(df)} municipis · Castellar i Berga cuadren amb docs/data-sources.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
