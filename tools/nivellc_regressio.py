#!/usr/bin/env python3
"""Nivell C · regressió de la BASE elèctrica per càpita (escala Catalunya) i predicció per a TOTS.

`base_implied = kWh_domèstic / ETCA` = elèctric per persona realment present (només calculable on hi
ha ETCA oficial). Ajustem OLS `base_implied ~ log10(densitat) + renda + gas_frac` sobre el conjunt
de CALIBRACIÓ (munis amb ETCA) i després PREDIM `base_pred` per a TOTS els municipis amb covariables
(inclosos els <1.000 hab sense ETCA). L'estimació de presència (a l'export) és `kWh / base_pred`.

Banda d'incertesa = p10–p90 del residual HELD-OUT (leave-one-out) PER TIPUS. Per als munis SENSE
ETCA (no validables) s'eixampla a l'export. Go/no-go honest: es publica en rang el que aguanta la
validació; el que no, queda fora o amb banda ampla.

Llegeix `data/territorial/nivellc_analisi.csv` (no re-baixa res). Sortida amb base_pred per a TOTS:
`data/territorial/nivellc_regressio.csv` + resum a stdout. Carril dades.

Ús:  python tools/nivellc_regressio.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "territorial" / "nivellc_analisi.csv"
OUT = REPO / "data" / "territorial" / "nivellc_regressio.csv"
BASE_UNICA = 1224.0
GO_ERR = 15.0


def _ols(X: np.ndarray, y: np.ndarray):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    return beta, pred, r2


def _band(errs: np.ndarray) -> dict:
    a = np.abs(errs)
    return {"p10": float(np.percentile(errs, 10)), "p50": float(np.percentile(errs, 50)),
            "p90": float(np.percentile(errs, 90)), "median_abs": float(np.median(a)),
            "coverage_15": float(np.mean(a <= GO_ERR) * 100)}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not SRC.exists():
        print(f"FALLA: no existeix {SRC} (executa abans tools/nivellc_analisi.py)", file=sys.stderr)
        return 2

    df = pd.read_csv(SRC, dtype={"ine5": str})
    renda_path = REPO / "data" / "territorial" / "renda_municipi_cat.csv"
    if renda_path.exists():
        renda = pd.read_csv(renda_path, dtype={"ine5": str})[["ine5", "renda_neta_persona_2023"]]
        df = df.merge(renda, on="ine5", how="left")
    else:
        df["renda_neta_persona_2023"] = pd.NA

    # Covariables (per a TOTS els munis amb densitat>0 i renda → predibles).
    df["densitat_hab_km2"] = pd.to_numeric(df["densitat_hab_km2"], errors="coerce")
    df["kwh_dom"] = pd.to_numeric(df["kwh_dom"], errors="coerce")
    df["etca"] = pd.to_numeric(df["etca"], errors="coerce")
    df["renda_k"] = pd.to_numeric(df["renda_neta_persona_2023"], errors="coerce") / 1000.0
    df["gas_frac"] = pd.to_numeric(df.get("gas_fraction"), errors="coerce").fillna(0.0)

    full = df[(df["densitat_hab_km2"] > 0) & df["renda_k"].notna() & df["kwh_dom"].notna()].copy()
    full["log_dens"] = np.log10(full["densitat_hab_km2"].astype(float))
    n_total = len(full)

    # Conjunt de CALIBRACIÓ: munis amb ETCA (base_implied calculable).
    fit = full[full["etca"].notna() & (full["etca"] > 0)].copy()
    fit["base_implied"] = fit["kwh_dom"] / fit["etca"]
    n = len(fit)
    print(f"Predicció per a {n_total} munis · calibració (amb ETCA) = {n}\n")

    yf = fit["base_implied"].to_numpy()
    Xf = np.column_stack([np.ones(n), fit["log_dens"].to_numpy(), fit["renda_k"].to_numpy(), fit["gas_frac"].to_numpy()])
    beta, pred_fit, r2 = _ols(Xf, yf)
    fit["base_pred"] = pred_fit
    fit["err_regressio_pct"] = (fit["base_implied"] - fit["base_pred"]) / fit["base_pred"] * 100

    print(f"Model: base_pred = {beta[0]:.0f} {beta[1]:+.0f}·log10(dens) {beta[2]:+.0f}·renda_k€ "
          f"{beta[3]:+.0f}·gas_frac   (R²={r2:.2f}, N={n})")
    b_in = _band(fit["err_regressio_pct"].to_numpy())
    print(f"  in-sample : |err| medià={b_in['median_abs']:.1f}%  cobertura±15%={b_in['coverage_15']:.0f}%  "
          f"banda=[{b_in['p10']:+.0f},{b_in['p90']:+.0f}]%")

    # Held-out (leave-one-out) sobre el conjunt de calibració.
    loo = np.empty(n)
    for i in range(n):
        m = np.ones(n, dtype=bool); m[i] = False
        bi, *_ = np.linalg.lstsq(Xf[m], yf[m], rcond=None)
        loo[i] = Xf[i] @ bi
    fit["err_loo_pct"] = (yf - loo) / loo * 100
    b_loo = _band(fit["err_loo_pct"].to_numpy())
    gap = b_in["coverage_15"] - b_loo["coverage_15"]
    print(f"  held-out  : |err| medià={b_loo['median_abs']:.1f}%  cobertura±15%={b_loo['coverage_15']:.0f}%  "
          f"banda=[{b_loo['p10']:+.0f},{b_loo['p90']:+.0f}]%  → caiguda {gap:.0f} pts "
          f"({'robust' if gap <= 8 else 'ATENCIÓ sobreajust'})")

    print("\nResidual held-out per tipus (la banda que es publica · munis amb ETCA):")
    for t, g in fit.groupby("tipus_territorial"):
        e = g["err_loo_pct"].to_numpy()
        cov = float(np.mean(np.abs(e) <= GO_ERR) * 100)
        print(f"  {t:22} n={len(g):4}  |err| medià={np.median(np.abs(e)):5.1f}%  "
              f"cobertura±15%={cov:4.0f}%  banda=[{np.percentile(e,10):+.0f},{np.percentile(e,90):+.0f}]%")

    # Predicció per a TOTS els munis (calibració + sense ETCA).
    Xall = np.column_stack([np.ones(n_total), full["log_dens"].to_numpy(),
                            full["renda_k"].to_numpy(), full["gas_frac"].to_numpy()])
    full["base_pred"] = Xall @ beta
    full = full.merge(fit[["ine5", "base_implied", "err_regressio_pct", "err_loo_pct"]], on="ine5", how="left")

    cols = ["ine5", "municipi", "tipus_territorial", "densitat_hab_km2", "etca", "kwh_dom",
            "base_implied", "base_pred", "err_regressio_pct", "err_loo_pct"]
    out = full[cols].copy()
    for c in ["base_implied", "base_pred"]:
        out[c] = out[c].round(0)
    for c in ["err_regressio_pct", "err_loo_pct"]:
        out[c] = out[c].round(1)
    out.sort_values(["tipus_territorial", "ine5"]).to_csv(OUT, index=False, lineterminator="\n")
    n_sense = int(out["etca"].isna().sum())
    print(f"\nEscrit {OUT.relative_to(REPO).as_posix()} · {n_total} munis "
          f"({n} calibrats amb ETCA, {n_sense} sense ETCA = predits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
