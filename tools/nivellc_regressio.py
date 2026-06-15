#!/usr/bin/env python3
"""Nivell C · regressió de la BASE elèctrica per càpita amb covariables contínues.

La troballa de `nivellc_analisi.py` (N~80): el `tipus_territorial` correlaciona amb el biaix de
la base única (1.224), però queda molta dispersió DINS del tipus → una base per tipus no n'hi ha
prou. Hipòtesi: el driver real és CONTINU (la densitat: pisos petits → menys kWh domèstic/persona).
Aquí ho provem: ajustem la base per persona PRESENT (calibrada a l'ETCA) com a funció de la
densitat (i l'altitud), i comparem la precisió contra la base única i la base per tipus.

Definició: per als munis amb ETCA, `base_implied = kWh_domèstic / ETCA` = elèctric per persona
realment present. Si el model és correcte, `base_implied` ha de ser PREDICTIBLE per densitat.
Ajust OLS (numpy). Error de POBLACIÓ sota el model: err% = (base_implied − base_pred)/base_pred×100
(equivalent a (pernocta_est_C − ETCA)/ETCA). Banda d'incertesa = p10–p90 del residual (substitueix
l'interim ±10% de la fitxa, Pas 0a). Go/no-go: cobertura |err|≤15% i amplada de banda.

Llegeix l'artefacte `data/territorial/nivellc_analisi.csv` (no re-baixa res). Carril dades en
silenci. Sortida: `data/territorial/nivellc_regressio.csv` + resum a stdout.

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
    """OLS per mínims quadrats. Torna (beta, prediccions, R²)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    return beta, pred, r2


def _band(errs: np.ndarray) -> dict:
    a = np.abs(errs)
    return {
        "p10": float(np.percentile(errs, 10)),
        "p50": float(np.percentile(errs, 50)),
        "p90": float(np.percentile(errs, 90)),
        "median_abs": float(np.median(a)),
        "coverage_15": float(np.mean(a <= GO_ERR) * 100),
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not SRC.exists():
        print(f"FALLA: no existeix {SRC} (executa abans tools/nivellc_analisi.py)", file=sys.stderr)
        return 2

    df = pd.read_csv(SRC, dtype={"ine5": str})
    # Covariable de renda (INE ADRH 2023, extreta per tools/extract_renda.py).
    renda_path = REPO / "data" / "territorial" / "renda_municipi_cat.csv"
    if renda_path.exists():
        renda = pd.read_csv(renda_path, dtype={"ine5": str})[["ine5", "renda_neta_persona_2023"]]
        df = df.merge(renda, on="ine5", how="left")
    else:
        df["renda_neta_persona_2023"] = pd.NA
    # Necessitem ETCA, pernocta_est, densitat>0 i RENDA per a una comparació justa entre models.
    df = df[df["etca"].notna() & df["pernocta_est"].notna() & df["densitat_hab_km2"].notna()].copy()
    df = df[df["densitat_hab_km2"] > 0]
    n_sense_renda = int(df["renda_neta_persona_2023"].isna().sum())
    df = df[df["renda_neta_persona_2023"].notna()].copy()
    df["kwh_dom"] = df["pernocta_est"] * BASE_UNICA
    df["base_implied"] = df["kwh_dom"] / df["etca"]
    df["log_dens"] = np.log10(df["densitat_hab_km2"].astype(float))
    df["alt"] = pd.to_numeric(df["altitud_m"], errors="coerce").fillna(0.0)
    df["renda_k"] = df["renda_neta_persona_2023"].astype(float) / 1000.0  # milers € (coef llegible)
    n = len(df)
    y = df["base_implied"].to_numpy()
    print(f"N (munis amb ETCA + densitat + renda) = {n}  (descartats sense renda: {n_sense_renda})\n")

    # --- Referència 1: base ÚNICA 1224 (l'error de població ja a la columna err_pernocta_pct) ---
    err_unica = df["err_pernocta_pct"].astype(float).to_numpy()
    b_unica = _band(err_unica)

    # --- Referència 2: base per TIPUS (factor = mediana base_implied per tipus) ---
    df["base_tipus"] = df.groupby("tipus_territorial")["base_implied"].transform("median")
    err_tipus = ((df["base_implied"] - df["base_tipus"]) / df["base_tipus"] * 100).to_numpy()
    b_tipus = _band(err_tipus)

    # --- Models de regressió contínua ---
    ones = np.ones(n)
    ld = df["log_dens"].to_numpy()
    rk = df["renda_k"].to_numpy()
    models = {
        "base ~ const (mitjana)": np.column_stack([ones]),
        "base ~ log10(densitat)": np.column_stack([ones, ld]),
        "base ~ renda": np.column_stack([ones, rk]),
        "base ~ log10(densitat) + renda": np.column_stack([ones, ld, rk]),
        "base ~ log10(densitat) + renda + altitud": np.column_stack([ones, ld, rk, df["alt"].to_numpy()]),
    }
    results = {}
    for name, X in models.items():
        beta, pred, r2 = _ols(X, y)
        err = (y - pred) / pred * 100  # err de població equivalent
        results[name] = {"beta": beta, "pred": pred, "r2": r2, "band": _band(err)}

    # Model triat: densitat + renda (les dues covariables disponibles que aporten).
    best_name = "base ~ log10(densitat) + renda"
    best = results[best_name]
    df["base_pred"] = best["pred"]
    df["err_regressio_pct"] = (df["base_implied"] - df["base_pred"]) / df["base_pred"] * 100

    # --- Informe ---
    def line(label, b, r2=None):
        r2s = "" if r2 is None else f"R²={r2:.2f}  "
        print(f"  {label:34} {r2s}|err| medià={b['median_abs']:5.1f}%  "
              f"cobertura±15%={b['coverage_15']:4.0f}%  banda p10/p90=[{b['p10']:+.0f},{b['p90']:+.0f}]%")

    print("Precisió de l'estimació de població (err vs ETCA) per estratègia de base:")
    line("Base única (1224)", b_unica)
    line("Base per tipus (mediana/tipus)", b_tipus)
    for name, res in results.items():
        line(name, res["band"], res["r2"])

    print(f"\nModel triat: {best_name}")
    bb = best["beta"]
    print(f"  base_pred = {bb[0]:.0f} {bb[1]:+.0f}·log10(dens) {bb[2]:+.0f}·renda_k€   (R²={best['r2']:.2f})")
    print(f"  → densitat ×10 ⇒ {bb[1]:+.0f} kWh/persona; +1.000 € renda ⇒ {bb[2]:+.0f} kWh/persona")

    print("\nResidual del model triat per tipus territorial:")
    for t, g in df.groupby("tipus_territorial"):
        e = g["err_regressio_pct"].to_numpy()
        cov = float(np.mean(np.abs(e) <= GO_ERR) * 100)
        print(f"  {t:22} n={len(g):3}  |err| medià={np.median(np.abs(e)):5.1f}%  "
              f"cobertura±15%={cov:4.0f}%  banda=[{np.percentile(e,10):+.0f},{np.percentile(e,90):+.0f}]%")

    # --- Validació HELD-OUT (leave-one-out) del model triat: que el 77% no sigui sobreajust ---
    Xb = np.column_stack([ones, ld, rk])  # densitat + renda
    loo = np.empty(n)
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        beta_i, *_ = np.linalg.lstsq(Xb[mask], y[mask], rcond=None)
        loo[i] = Xb[i] @ beta_i
    df["err_loo_pct"] = (y - loo) / loo * 100
    b_loo = _band(df["err_loo_pct"].to_numpy())
    ib = best["band"]
    print("\nValidació held-out (leave-one-out) — model densitat + renda:")
    print(f"  in-sample : |err| medià={ib['median_abs']:5.1f}%  cobertura±15%={ib['coverage_15']:4.0f}%  "
          f"banda=[{ib['p10']:+.0f},{ib['p90']:+.0f}]%")
    print(f"  held-out  : |err| medià={b_loo['median_abs']:5.1f}%  cobertura±15%={b_loo['coverage_15']:4.0f}%  "
          f"banda=[{b_loo['p10']:+.0f},{b_loo['p90']:+.0f}]%")
    gap = ib["coverage_15"] - b_loo["coverage_15"]
    print(f"  → caiguda de cobertura in-sample→held-out: {gap:.0f} pts "
          f"({'robust' if gap <= 8 else 'atenció: possible sobreajust'})")

    cols = ["ine5", "municipi", "tipus_territorial", "etca", "densitat_hab_km2", "altitud_m",
            "base_implied", "base_pred", "err_pernocta_pct", "err_regressio_pct", "err_loo_pct"]
    df_out = df[cols].copy()
    df_out["base_implied"] = df_out["base_implied"].round(0)
    df_out["base_pred"] = df_out["base_pred"].round(0)
    df_out["err_regressio_pct"] = df_out["err_regressio_pct"].round(1)
    df_out["err_loo_pct"] = df_out["err_loo_pct"].round(1)
    df_out.sort_values(["tipus_territorial", "ine5"]).to_csv(OUT, index=False, lineterminator="\n")
    print(f"\nEscrit {OUT.relative_to(REPO).as_posix()} · {n} munis (provisional, intern)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
