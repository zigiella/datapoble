#!/usr/bin/env python3
"""Classificador de TIPUS TERRITORIAL (Pas 4 · Nivell B, spec consultora 2 §2.2).

Assigna a cada municipi un `tipus_territorial` determinista: QUÈ ÉS el municipi
(estructura geogràfica estable), SEPARAT de la `tipologia` comportamental del mart
(COM s'habita). És el «pont» de l'escala: el nivell d'agregació amb què, a Catalunya,
els municipis hereten esperats calibrats per tipus.

Vuit tipus + un flag transversal `micromunicipi` (padró < 250). Regles per ORDRE
(primera que encaixa), amb «interior rural» com a residual. Criteris de fonts obertes:
costaner (llista Territori), AMB (llista 36), densitat (Idescat), capitalitat comarcal
(llista oficial), altitud (Idescat). L'`agroindustrial` (pes CCAE) queda pendent de dada
fina i de moment cau a «interior rural».

CARRIL DADES (decisió Bea 2026-06-11): artefacte INTERN, offline, NO publicat al web fins
que el seu tipus validi contra ETCA. Reproduïble: llegeix snapshot committejat + mart.

Entrades: `data/territorial/inputs_bergueda.csv` (altitud/densitat, font Idescat EMEX) +
`data/marts/mart_municipi.parquet` (padró). Sortida: `data/territorial/tipus_territorial_bergueda.csv`.

Ús:
    python tools/tipus_territorial.py            # escriu el CSV
    python tools/tipus_territorial.py --check     # falla si el CSV està desactualitzat
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
INPUTS = REPO / "data" / "territorial" / "inputs_bergueda.csv"
MART = REPO / "data" / "marts" / "mart_municipi.parquet"
OUT = REPO / "data" / "territorial" / "tipus_territorial_bergueda.csv"

# Llistes de Catalunya. PARCIALS: omplertes amb el pilot (Berguedà) + el primer lot
# d'escala (Barcelonès + Tarragonès turístic). A completar amb les llistes oficials
# senceres (AMB 36, costaners ~70, 41 capitals) quan s'escali a tot Catalunya.
COSTANERS: set[str] = {
    "08019", "08015", "08194",  # Barcelona, Badalona, Sant Adrià de Besòs (litoral metropolità)
    "43905", "43038", "43171", "43148",  # Salou, Cambrils, Vila-seca, Tarragona (litoral)
}
AMB: set[str] = {  # municipis de l'Àrea Metropolitana de Barcelona (parcial: Barcelonès)
    "08019", "08101", "08015", "08245", "08194",
}
CORONA: set[str] = set()  # corona metropolitana (contigüitat funcional, mobilitat obligada)
CAPITALS_COMARCALS: set[str] = {"08022", "43148"}  # Berga, Tarragona (extensible a les 41)

DENSITAT_METRO = 1500.0  # hab/km² (llindar metropolità dens)
ALTITUD_PIRINEU = 800.0  # m (llindar Pirineu / alta muntanya)
PADRO_MICRO = 250  # flag micromunicipi (modificador, no tipus)


def classify(ine5: str, altitud: float | None, densitat: float | None) -> str:
    """Tipus territorial per ORDRE (primera regla que encaixa; rural és el residual)."""
    if ine5 in COSTANERS:
        # Litoral metropolità (AMB) vs vacacional (la resta): la densitat sola no distingeix
        # un resort dens (Salou) d'una ciutat metro, per això partim per AMB.
        return "litoral_metropolita" if ine5 in AMB else "litoral_vacacional"
    if ine5 in AMB or (densitat is not None and densitat >= DENSITAT_METRO):
        return "metropolita_dens"
    if ine5 in CORONA:
        return "corona_metropolitana"
    if ine5 in CAPITALS_COMARCALS:
        return "capital_comarcal"
    if altitud is not None and altitud >= ALTITUD_PIRINEU:
        return "pirineu_alta_muntanya"
    return "interior_rural"


def build() -> pd.DataFrame:
    inp = pd.read_csv(INPUTS, dtype={"ine5": str})
    mart = pd.read_parquet(MART)[["ine5", "municipi", "poblacio"]]
    mart["ine5"] = mart["ine5"].astype(str).str.zfill(5)
    df = mart.merge(inp[["ine5", "altitud_m", "densitat_hab_km2"]], on="ine5", how="left")

    out_rows = []
    for _, r in df.sort_values("ine5").iterrows():
        alt = None if pd.isna(r["altitud_m"]) else float(r["altitud_m"])
        den = None if pd.isna(r["densitat_hab_km2"]) else float(r["densitat_hab_km2"])
        pad = None if pd.isna(r["poblacio"]) else int(r["poblacio"])
        out_rows.append(
            {
                "ine5": r["ine5"],
                "municipi": r["municipi"],
                "tipus_territorial": classify(r["ine5"], alt, den),
                "micromunicipi": bool(pad is not None and pad < PADRO_MICRO),
                "poblacio": pad,
                "altitud_m": int(alt) if alt is not None else "",
                "densitat_hab_km2": den if den is not None else "",
            }
        )
    return pd.DataFrame(out_rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tipus_territorial")
    ap.add_argument("--check", action="store_true", help="no escriu; falla si el CSV està desactualitzat")
    args = ap.parse_args(argv)

    for p in (INPUTS, MART):
        if not p.exists():
            print(f"FALLA: no existeix {p}", file=sys.stderr)
            return 2

    df = build()
    payload = df.to_csv(index=False, lineterminator="\n")

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
    counts = df["tipus_territorial"].value_counts().to_dict()
    micro = int(df["micromunicipi"].sum())
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {len(df)} munis · {counts} · micromunicipis={micro}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
