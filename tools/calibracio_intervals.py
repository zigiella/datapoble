#!/usr/bin/env python3
"""Calibració dels intervals predictius del Nivell C — reliability diagram + cobertura empírica.

Pregunta de Fase 1 (reconducció §1.4, Rapaz): *l'interval que publiquem cobreix de debò el que
promet?* La banda publicada (export_pernocta_catalunya.py) és el p10–p90 del residual held-out
(leave-one-out) PER TIPUS territorial → un interval nominal del **80%**. Aquí en mesurem la
**cobertura empírica**: de tots els municipis amb ETCA oficial (l'única veritat de terra que tenim),
quina fracció cau realment dins el seu interval, a diversos nivells nominals.

Honestedat anti-trampa: la banda d'un municipi es calcula amb els residuals dels ALTRES municipis del
seu tipus (leave-one-out de la PRÒPIA banda), no amb tot el conjunt; si no, la cobertura seria ~nominal
per construcció. Es reporta també la variant in-sample per veure l'optimisme.

Límit declarat: només es pot validar on hi ha ETCA (municipis ≥1.000 hab). La banda dels <1.000 hab
(eixamplada ×1,5 a l'export) és una EXTRAPOLACIÓ no validada — i és justament on el model tremola més
(micromunicipis). Això NO ho pot mesurar aquest script; ho diem, no ho amaguem.

Entrada (committejada, cap fetch → reproduïble offline):
  · data/territorial/nivellc_regressio.csv  (err_loo_pct + tipus per muni amb ETCA)
Sortida:
  · data/territorial/calibracio_intervals.csv  (taula: scope × nivell nominal → cobertura empírica)
  · resum + reliability a stdout

Ús:
    python tools/calibracio_intervals.py            # escriu la taula
    python tools/calibracio_intervals.py --check     # falla si la taula al disc no coincideix
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "territorial" / "nivellc_regressio.csv"
OUT = REPO / "data" / "territorial" / "calibracio_intervals.csv"

# Nivells nominals d'interval a auditar (l'interval és simètric en percentils: nivell 80 = [p10, p90]).
NIVELLS = [50, 60, 70, 80, 90, 95]
# Mínim de veïns per formar una banda leave-one-out fiable per a un municipi.
MIN_VEINS = 5


def _pct(xs: list[float], p: float) -> float:
    """Percentil amb interpolació lineal (mateixa convenció que l'export)."""
    s = sorted(xs)
    if not s:
        return 0.0
    k = (len(s) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def _coverage(errs_by_tipus: dict[str, list[float]], scope_tipus: list[str] | None, level: float,
              loo: bool) -> tuple[int, int]:
    """Compta (dins, jutjats) a un nivell nominal. La banda d'un muni surt dels seus veïns de tipus
    (leave-one-out si loo=True). scope_tipus None = global (tots els tipus)."""
    lo_q, hi_q = (100 - level) / 2.0, 100 - (100 - level) / 2.0
    within = judged = 0
    for tipus, errs in errs_by_tipus.items():
        if scope_tipus is not None and tipus not in scope_tipus:
            continue
        for i, e in enumerate(errs):
            veins = errs[:i] + errs[i + 1:] if loo else errs
            if len(veins) < MIN_VEINS:
                continue
            lo, hi = _pct(veins, lo_q), _pct(veins, hi_q)
            judged += 1
            if lo <= e <= hi:
                within += 1
    return within, judged


def build_rows() -> tuple[list[dict], dict[str, list[float]]]:
    errs_by_tipus: dict[str, list[float]] = {}
    with SRC.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            raw = (r.get("err_loo_pct") or "").strip()
            if not raw:
                continue
            try:
                errs_by_tipus.setdefault(r["tipus_territorial"], []).append(float(raw))
            except ValueError:
                continue

    rows: list[dict] = []
    scopes: list[tuple[str, list[str] | None]] = [("GLOBAL", None)]
    scopes += [(t, [t]) for t in sorted(errs_by_tipus)]
    for scope_name, scope_tipus in scopes:
        for level in NIVELLS:
            w_loo, n = _coverage(errs_by_tipus, scope_tipus, level, loo=True)
            w_in, _ = _coverage(errs_by_tipus, scope_tipus, level, loo=False)
            rows.append({
                "scope": scope_name,
                "nivell_nominal": level,
                "cobertura_loo": round(w_loo / n * 100, 1) if n else "",
                "cobertura_insample": round(w_in / n * 100, 1) if n else "",
                "n": n,
            })
    return rows, errs_by_tipus


def render(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["scope", "nivell_nominal", "cobertura_loo",
                                        "cobertura_insample", "n"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="calibracio_intervals")
    ap.add_argument("--check", action="store_true", help="no escriu; falla si la taula està desactualitzada")
    args = ap.parse_args(argv)

    if not SRC.exists():
        print(f"FALLA: no existeix {SRC} (executa abans tools/nivellc_regressio.py)", file=sys.stderr)
        return 2

    rows, errs_by_tipus = build_rows()
    payload = render(rows)

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

    n_total = sum(len(v) for v in errs_by_tipus.values())
    g80 = next((r for r in rows if r["scope"] == "GLOBAL" and r["nivell_nominal"] == 80), None)
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · calibració sobre {n_total} municipis amb ETCA")
    print("\nReliability (GLOBAL · banda leave-one-out per tipus):")
    print(f"  {'nominal':>8}  {'empíric':>8}  {'in-sample':>9}")
    for r in rows:
        if r["scope"] != "GLOBAL":
            continue
        print(f"  {r['nivell_nominal']:>7}%  {r['cobertura_loo']:>7}%  {r['cobertura_insample']:>8}%")
    if g80:
        diag = "ben calibrat" if abs(float(g80["cobertura_loo"]) - 80) <= 5 else \
               ("OPTIMISTA (banda estreta)" if float(g80["cobertura_loo"]) < 75 else "CONSERVADOR (banda ampla)")
        print(f"\n  → L'interval nominal del 80% (p10–p90) cobreix el {g80['cobertura_loo']}% real "
              f"(held-out, n={g80['n']}): {diag}.")
    print("\nCobertura empírica per tipus a nivell 80% (LOO):")
    for r in rows:
        if r["scope"] != "GLOBAL" and r["nivell_nominal"] == 80:
            print(f"  {r['scope']:22} n={r['n']:>4}  cobertura={r['cobertura_loo']}%")
    print("\nLímit: només validable on hi ha ETCA (≥1.000 hab). La banda dels <1.000 hab és "
          "extrapolació no validada (eixamplada ×1,5 a l'export) — el punt més incert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
