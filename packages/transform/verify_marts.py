"""Verificació de la mart contra docs/data-sources.md (Experiment 0).

Comprova que Castellar (08052) i Berga (08022) cuadren amb els valors verificats
en viu, la cobertura (cap font clau buida) i els invariants del contracte
(IETR = 0,5·stock + 0,5·impact; carrega_funcional = max(padró, L1, L2)).
Surt amb codi != 0 si algun check falla → apte per a CI.

    python packages/transform/verify_marts.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MART = REPO / "data" / "marts" / "mart_municipi.parquet"

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

    # --- Cobertura: cap font clau buida (la bateria FALLA si en falta una) ---
    coverage_cols = ["poblacio", "kg_hab_any", "kwh_hab", "vidre_hab", "IETR"]
    for col in coverage_cols:
        if col not in df.columns:
            errors.append(f"cobertura: falta la columna {col}")
        elif int(df[col].isna().sum()):
            errors.append(f"cobertura: {col} té {int(df[col].isna().sum())} nuls (esperat 0 de {len(df)})")

    # --- Invariant: IETR = 0,5·IETR_stock + 0,5·IETR_impact (tolerància d'arrodoniment 0,02) ---
    if {"IETR", "IETR_stock", "IETR_impact"}.issubset(df.columns):
        diff = ((0.5 * df["IETR_stock"] + 0.5 * df["IETR_impact"]).round(2) - df["IETR"].round(2)).abs()
        if diff.max() > 0.02:
            errors.append(f"IETR != 0.5*stock+0.5*impact a {df.index[diff > 0.02].tolist()} (diff màx {diff.max():.3f})")
        else:
            print(f"Invariant IETR = 0,5·stock + 0,5·impact OK (diff màx {diff.max():.3f})")

    # --- Invariant: carrega_funcional_est = max(padró, pernocta L1, càrrega residus L2) ---
    if {"carrega_funcional_est", "poblacio", "poblacio_pernocta_est", "carrega_total_est"}.issubset(df.columns):
        expected = df[["poblacio", "poblacio_pernocta_est", "carrega_total_est"]].max(axis=1)
        mismatch = df.index[df["carrega_funcional_est"] != expected].tolist()
        if mismatch:
            errors.append(f"carrega_funcional_est != max(padró, L1, L2) a {mismatch}")
        else:
            print(f"Invariant carrega_funcional_est = max(padró, L1, L2) OK · cobertura sense nuls ({len(df)} munis)")

    if errors:
        print("VERIFICACIÓ FALLIDA:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"VERIFICACIÓ OK · {len(df)} municipis · Castellar i Berga cuadren amb docs/data-sources.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
