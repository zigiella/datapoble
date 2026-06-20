#!/usr/bin/env python3
"""Prova del model UNIFICAT al Berguedà abans d'escalar a tot Catalunya (decisió de Bea: «provar
primer al Berguedà»).

Pregunta: si substituïm la base de presència FIXA del Berguedà (Nivell B: `base_electric=1224`,
calibrada sobre els 31 munis) per la base de COVARIABLES de tot Catalunya (Nivell C:
`base=f(densitat, renda, gas)`, ajustada contra l'ETCA sobre 486 munis), el Berguedà segueix
reproduint la seva validació ETCA? És el GUARDÓ de la unificació (docs/pla-catalunya-profund.md §3.1):
no podem trencar la joia validada.

Mètode: comparació offline de dos artefactes que JA existeixen (cap re-baixada):
  · Nivell B = `poblacio_pernocta_est` de data/web/municipis.bergueda.json (base fixa).
  · Nivell C = `estimacio` (+ rang) de data/web/pernocta-catalunya.json (base covariables; ja inclou
    el Berguedà perquè cobreix els 927 munis).
  · Oficial = `etca_oficial` (Idescat ETCA), per als munis del Berguedà ≥1.000 hab.

Sortida: taula per muni + veredicte (error medià, dins ±15%, ETCA dins rang, Spearman) contra el
llindar oficial go/no-go (ρ≥0,7, error≤15%). NO escriu res: és una prova, no un artefacte.

Ús:  python tools/prova_unificacio_bergueda.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BERG = REPO / "data" / "web" / "municipis.bergueda.json"
PERN = REPO / "data" / "web" / "pernocta-catalunya.json"

RHO_MIN = 0.7      # llindar oficial go/no-go (etca-validacio.json)
ERR_MAX = 15.0     # % error medià màxim


def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _spearman(a: list[float], b: list[float]) -> float:
    """Correlació de rang (Spearman) sense dependències externes. n petit."""
    def ranks(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        r = [0.0] * len(xs)
        i = 0
        while i < len(xs):
            j = i
            while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1  # rang mitjà per empats (1-based)
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = sum((ra[i] - ma) ** 2 for i in range(n)) ** 0.5
    db = sum((rb[i] - mb) ** 2 for i in range(n)) ** 0.5
    return num / (da * db) if da and db else 0.0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    berg = json.loads(BERG.read_text(encoding="utf-8"))["municipis"]
    pern = json.loads(PERN.read_text(encoding="utf-8"))["munis"]

    rows = []
    for ine5, m in berg.items():
        p = pern.get(ine5)
        if not p or p.get("etca_oficial") is None:
            continue
        etca = p["etca_oficial"]
        niv_b = m["values"].get("poblacio_pernocta_est")
        niv_c = p["estimacio"]
        if niv_b is None or niv_c is None:
            continue
        rows.append({
            "ine5": ine5, "nom": p.get("nom", ""), "etca": etca,
            "nivB": niv_b, "nivC": niv_c,
            "errB": abs(niv_b - etca) / etca * 100,
            "errC": abs(niv_c - etca) / etca * 100,
            "in_rang": p["rang_baix"] <= etca <= p["rang_alt"],
        })
    rows.sort(key=lambda r: r["etca"])

    print(f"Prova del model unificat al Berguedà · {len(rows)} munis amb ETCA\n")
    print(f"{'ine5':<6}{'municipi':<16}{'ETCA':>7}{'NivB':>7}{'errB%':>7}{'NivC':>7}{'errC%':>7}  rang")
    for r in rows:
        print(f"{r['ine5']:<6}{r['nom'][:15]:<16}{r['etca']:>7}{round(r['nivB']):>7}"
              f"{r['errB']:>7.1f}{round(r['nivC']):>7}{r['errC']:>7.1f}   {'✓' if r['in_rang'] else '✗'}")

    med_b = _median([r["errB"] for r in rows])
    med_c = _median([r["errC"] for r in rows])
    in15_b = sum(1 for r in rows if r["errB"] <= 15)
    in15_c = sum(1 for r in rows if r["errC"] <= 15)
    in_rang = sum(1 for r in rows if r["in_rang"])
    rho = _spearman([r["etca"] for r in rows], [r["nivC"] for r in rows])

    print("\n--- veredicte ---")
    print(f"error medià   · Nivell B (base fixa 1224): {med_b:.1f}%   →   "
          f"Nivell C (covariables): {med_c:.1f}%")
    print(f"dins ±15%     · Nivell B: {in15_b}/{len(rows)}   →   Nivell C: {in15_c}/{len(rows)}")
    print(f"ETCA dins rang (Nivell C): {in_rang}/{len(rows)}")
    print(f"Spearman(ETCA, Nivell C): {rho:.3f}   (llindar ρ≥{RHO_MIN})")

    passa = med_c <= ERR_MAX and rho >= RHO_MIN and med_c <= med_b
    print(f"\nGUARDÓ (no regressar el Berguedà; ρ≥{RHO_MIN}, error≤{ERR_MAX}%, no pitjor que Nivell B): "
          f"{'✅ PASSA' if passa else '❌ NO PASSA'}")
    if passa:
        print("→ La base unificada reprodueix (millora) la validació del Berguedà. Es pot escalar.")
    else:
        print("→ La base unificada regressa el Berguedà: cal mantenir-hi calibratge propi o revisar.")
    return 0 if passa else 1


if __name__ == "__main__":
    raise SystemExit(main())
