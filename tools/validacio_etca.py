#!/usr/bin/env python3
"""Validació externa de la inferència de presència contra ETCA (Idescat).

Pas 4 · primer pas (spec consultora 2 §2.3). Compara les nostres estimacions del
mart (`poblacio_pernocta_est`, `carrega_funcional_est`) amb la **Població ETCA**
oficial d'Idescat (Estimacions de població estacional, base 2021) per als municipis
del Berguedà que en tenen (≥1.000 hab). És la PRIMERA validació externa DISCRIMINANT:
fins ara l'única «validació» era Spearman(IETR, residus), gairebé circular (L2 *són*
residus).

Entrades (totes committejades, cap fetch en viu → reproduïble offline):
  · `data/etca/etca_bergueda.csv`     — snapshot ETCA per municipi (font: Idescat EPE)
  · `data/marts/mart_municipi.parquet`— les nostres estimacions

Sortida: `data/web/etca-validacio.json` amb, per municipi, la nostra estimació vs ETCA
i l'error; i el resum comarcal (Spearman ρ + error medià + go/no-go ρ≥0,7 i error≤15%).

Ús:
    python tools/validacio_etca.py            # escriu el JSON
    python tools/validacio_etca.py --check     # falla si el JSON al disc no coincideix
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import median

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "data" / "etca" / "etca_bergueda.csv"
MART = REPO / "data" / "marts" / "mart_municipi.parquet"
PROV = REPO / "data" / "etca" / "_provenance.json"
OUT = REPO / "data" / "web" / "etca-validacio.json"

# Llindars go/no-go de l'spec §2.3 (confirmats per la Bea 2026-06-11).
RHO_MIN = 0.7
ERR_MAX = 15.0


def _spearman(xs: list[float], ys: list[float]) -> float:
    """Correlació de rangs (Pearson sobre els rangs). Sense scipy."""

    def rank(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for pos, i in enumerate(order):
            r[i] = pos + 1
        return r

    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num / den, 3) if den else float("nan")


def _err_pct(est: float, ref: float) -> float | None:
    if ref in (None, 0) or est is None or pd.isna(est) or pd.isna(ref):
        return None
    return round(100.0 * (est - ref) / ref, 1)


def build() -> dict:
    etca = pd.read_csv(SNAPSHOT, dtype={"ine5": str})
    mart = pd.read_parquet(MART)[
        ["ine5", "municipi", "poblacio", "poblacio_pernocta_est", "carrega_funcional_est"]
    ]
    mart["ine5"] = mart["ine5"].astype(str).str.zfill(5)
    df = mart.merge(etca[["ine5", "poblacio_etca", "etca_resident"]], on="ine5", how="left")

    per_muni: list[dict] = []
    pairs_per: list[tuple[float, float]] = []
    pairs_car: list[tuple[float, float]] = []
    errs_per: list[float] = []
    errs_car: list[float] = []
    for _, r in df.sort_values("poblacio", ascending=False).iterrows():
        etcav = None if pd.isna(r["poblacio_etca"]) else float(r["poblacio_etca"])
        per = None if pd.isna(r["poblacio_pernocta_est"]) else float(r["poblacio_pernocta_est"])
        car = None if pd.isna(r["carrega_funcional_est"]) else float(r["carrega_funcional_est"])
        covered = etcav is not None
        e_per = _err_pct(per, etcav)
        e_car = _err_pct(car, etcav)
        if covered and per is not None:
            pairs_per.append((per, etcav))
            errs_per.append(abs(e_per))
        if covered and car is not None:
            pairs_car.append((car, etcav))
            errs_car.append(abs(e_car))
        per_muni.append(
            {
                "ine5": r["ine5"],
                "municipi": r["municipi"],
                "padro": int(r["poblacio"]) if not pd.isna(r["poblacio"]) else None,
                "etca": int(etcav) if covered else None,
                "pernocta_est": int(per) if per is not None else None,
                "err_pernocta_pct": e_per,
                "carrega_funcional_est": int(car) if car is not None else None,
                "err_carrega_pct": e_car,
                "covered": covered,
            }
        )

    def summary(pairs, errs):
        if not pairs:
            return None
        rho = _spearman([a for a, _ in pairs], [b for _, b in pairs])
        err = round(median(errs), 1)
        return {
            "n": len(pairs),
            "spearman": rho,
            "error_median_pct": err,
            "passa": bool(rho >= RHO_MIN and err <= ERR_MAX),
        }

    prov = json.loads(PROV.read_text(encoding="utf-8")) if PROV.exists() else {}
    return {
        "font": prov.get("organisme", "Idescat — ETCA"),
        "base": prov.get("base"),
        "any": prov.get("any"),
        "go_no_go": {"rho_min": RHO_MIN, "error_max_pct": ERR_MAX},
        "pernocta_vs_etca": summary(pairs_per, errs_per),
        "carrega_vs_etca": summary(pairs_car, errs_car),
        "municipis": per_muni,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="validacio_etca")
    ap.add_argument("--check", action="store_true", help="no escriu; falla si el JSON està desactualitzat")
    args = ap.parse_args(argv)

    for p in (SNAPSHOT, MART):
        if not p.exists():
            print(f"FALLA: no existeix {p}", file=sys.stderr)
            return 2

    data = build()
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"FALLA (--check): no existeix {OUT}", file=sys.stderr)
            return 1
        with OUT.open("r", encoding="utf-8", newline="") as fh:
            if fh.read() != payload:
                print(f"FALLA (--check): {OUT} desactualitzat (re-executa sense --check)", file=sys.stderr)
                return 1
        print(f"OK (--check): {OUT} al dia.")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
    s = data["pernocta_vs_etca"]
    print(
        f"Escrit {OUT.relative_to(REPO).as_posix()} · pernocta vs ETCA: "
        f"rho={s['spearman']} error_media={s['error_median_pct']}% "
        f"({'PASSA' if s['passa'] else 'NO passa'} go/no-go, n={s['n']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
