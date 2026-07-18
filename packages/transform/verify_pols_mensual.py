"""Verificació OFFLINE de mart_pols_mensual (D1) — apte per a CI.

Corre sobre l'artefacte VERSIONAT ``data/marts/mart_pols_mensual.parquet`` (cap
xarxa). Guarda el contracte C1 §1.1 i les esmenes de 2026-07-16:

  1. Àncores byte-match contra el CSV font del SEPE (valors copiats literalment
     dels bytes dels fitxers ``Paro_por_municipios_{2006,2026}_csv.csv``,
     verificats en viu el 2026-07-17).
  2. El filtre és pel CATÀLEG sencer, mai per província: Gósol (25100, Lleida)
     i Gombrèn (17080, Girona) HAN de ser a la sèrie, i la cobertura del darrer
     mes ha de ser exactament el catàleg dels 947.
  3. Doctrina del «<5»: emmascarat ⇒ punt NULL + interval [1,4]; no emmascarat ⇒
     punt = min = max ≥ 0. Mai zero inventat, mai NaN silenciós.
  4. La sèrie de mesos és EXACTAMENT l'esperada: contínua des de 2006-01, amb
     els DOS forats declarats de la font (2013-05…2013-12 i 2020-12 no existeixen
     al CSV del SEPE — verificat en viu 2026-07-17). Ni mesos de més, ni de menys.

    python packages/transform/verify_pols_mensual.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MART = REPO / "data" / "marts" / "mart_pols_mensual.parquet"
CATALEG = REPO / "data" / "territorial" / "municipis-catalunya.csv"

N_MUNICIPIS = 947
DATE_RE = re.compile(r"^\d{4}-\d{2}$")

# Àncores byte-match contra el CSV font (SEPE). Format: (ine5, date) -> valor
# exacte, o "MASK" si la font servia '<5' (⇒ interval [1,4]).
ANCHORS: dict[tuple[str, str], int | str] = {
    # bytes del fitxer 2026: 202606;…;08019;Barcelona;61175;… etc.
    ("08019", "2026-06"): 61175,   # Barcelona
    ("08022", "2026-06"): 760,     # Berga
    ("17079", "2026-06"): 3886,    # Girona
    ("08166", "2026-06"): 31,      # la Pobla de Lillet
    ("25100", "2026-06"): "MASK",  # Gósol — '<5' real a la font
    ("17080", "2026-06"): "MASK",  # Gombrèn — '<5' real a la font
    # bytes del fitxer 2006 (pre-emmascarament: valors 1–4 EXACTES existien)
    ("08022", "2006-01"): 637,     # Berga
    ("25100", "2006-01"): 4,       # Gósol — un 4 exacte, no un '<5'
    ("17080", "2006-01"): 4,       # Gombrèn
}


def main() -> int:
    fails: list[str] = []

    if not MART.exists():
        print(f"FALLA: no existeix {MART} (executa la ingesta + dbt build)", file=sys.stderr)
        return 2
    df = pd.read_parquet(MART)
    cataleg = pd.read_csv(CATALEG, sep=";", dtype=str)
    ine5_cataleg = set(cataleg["ine5"])

    def check(cond: bool, msg: str) -> None:
        if not cond:
            fails.append(msg)

    # --- Estructura ---
    check(not df.empty, "mart buit")
    check(df.duplicated(subset=["ine5", "date"]).sum() == 0, "(ine5, date) amb duplicats")
    check(df["ine5"].str.len().eq(5).all(), "hi ha ine5 que no fan 5 caràcters (zero-pad?)")
    check(df["date"].map(lambda d: bool(DATE_RE.match(str(d)))).all(),
          'hi ha date fora del format "YYYY-MM" (C1 §1.1)')
    check(set(df["ine5"]) <= ine5_cataleg, "hi ha ine5 de FORA del catàleg dels 947")

    # --- Filtre pel catàleg, mai per província (l'esmena de 2026-07-16) ---
    darrer = df["date"].max()
    del_mes = df[df["date"] == darrer]
    check(len(del_mes) == N_MUNICIPIS,
          f"cobertura del darrer mes ({darrer}) = {len(del_mes)} ≠ {N_MUNICIPIS}")
    check("25100" in set(del_mes["ine5"]), "Gósol (25100, Lleida) ABSENT del darrer mes")
    check("17080" in set(del_mes["ine5"]), "Gombrèn (17080, Girona) ABSENT del darrer mes")
    check(df["date"].min() == "2006-01", f"la sèrie no comença el 2006-01 ({df['date'].min()})")

    # --- Mesos: continus des de 2006-01, amb els forats DECLARATS de la font ---
    last_y, last_m = int(darrer[:4]), int(darrer[5:])
    expected_months: set[str] = set()
    for y in range(2006, last_y + 1):
        if y == 2013:
            n = 4                     # forat de la font: només 2013-01…04
        elif y == 2020:
            n = 11                    # forat de la font: falta el 2020-12
        elif y == last_y:
            n = last_m
        else:
            n = 12
        expected_months |= {f"{y}-{m:02d}" for m in range(1, n + 1)}
    actual_months = set(df["date"])
    check(actual_months == expected_months,
          f"mesos inesperats: sobren {sorted(actual_months - expected_months)[:4]}, "
          f"falten {sorted(expected_months - actual_months)[:4]}")

    # --- Doctrina del «<5» (C1 §1.1, vinculant) ---
    masked = df[df["atur_emmascarat"]]
    clar = df[~df["atur_emmascarat"]]
    check(masked["atur_registrat"].isna().all(), "emmascarat amb punt NO nul (número inventat)")
    check(masked["atur_registrat_min"].eq(1).all() and masked["atur_registrat_max"].eq(4).all(),
          "emmascarat sense interval [1,4]")
    check(clar["atur_registrat"].notna().all(),
          "NaN silenciós: files no emmascarades sense valor")
    check(clar["atur_registrat"].ge(0).all(), "valors negatius")
    check((clar["atur_registrat"] == clar["atur_registrat_min"]).all()
          and (clar["atur_registrat"] == clar["atur_registrat_max"]).all(),
          "no emmascarat amb interval ≠ punt")

    # --- Àncores byte-match contra el CSV font ---
    idx = df.set_index(["ine5", "date"])
    for (ine5, date), expected in ANCHORS.items():
        try:
            row = idx.loc[(ine5, date)]
        except KeyError:
            fails.append(f"àncora ({ine5}, {date}): fila absent")
            continue
        if expected == "MASK":
            ok = (bool(row["atur_emmascarat"]) and pd.isna(row["atur_registrat"])
                  and row["atur_registrat_min"] == 1 and row["atur_registrat_max"] == 4)
            if not ok:
                fails.append(f"àncora ({ine5}, {date}): esperava '<5' → interval [1,4], "
                             f"tinc {row.to_dict()}")
        elif not (row["atur_registrat"] == expected and not bool(row["atur_emmascarat"])):
            fails.append(f"àncora ({ine5}, {date}): esperava {expected}, "
                         f"tinc {row['atur_registrat']}")

    if fails:
        print("VERIFICACIÓ mart_pols_mensual: FALLA", file=sys.stderr)
        for f in fails:
            print(f"  [x] {f}", file=sys.stderr)
        return 1
    n_masked = int(df["atur_emmascarat"].sum())
    print(f"VERIFICACIÓ mart_pols_mensual: OK — {len(df)} files, "
          f"{df['ine5'].nunique()} municipis, {df['date'].nunique()} mesos "
          f"({df['date'].min()}..{darrer}), {n_masked} '<5' modelats com a interval, "
          f"{len(ANCHORS)} àncores byte-match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
