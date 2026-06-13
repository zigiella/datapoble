#!/usr/bin/env python3
"""Export de Licitacions (el cabal) → JSON per al web (Mirador).

Pont dada→web del pilar 2 (contractació pública). Llegeix les sortides materialitzades
del Cabal (`data/events/licitacions_*.parquet`, de `packages/signals`) i emet un únic
artefacte que el web consumeix directament —sense passar pel mart, igual que la validació
ETCA—. Forma: resum COMARCAL (taxonomia + dependència) + fila per MUNICIPI (dependència
supramunicipal + què rep del Consell per tema).

Frontera honesta (la del mètode, docs/licitacions-intel-metode.md): la taxonomia és
HEURÍSTICA; el repartiment dels contractes del Consell als municipis és una HIPÒTESI
declarada (mètode + confiança per fila), no una mesura; «no_contracta_propi» vol dir que el
municipi no publica contractes propis en aquesta font (centralització al Consell + biaix de
font), MAI mala gestió. Cap xifra s'inventa: tot surt dels parquets.

Ús:
    python tools/export_licitacions.py            # escriu el JSON
    python tools/export_licitacions.py --check     # falla si el JSON està desactualitzat
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
ENRIQUIT = REPO / "data" / "events" / "licitacions_enriquit_bergueda.parquet"
REPARTIMENT = REPO / "data" / "events" / "licitacions_repartiment_bergueda.parquet"
DEPENDENCIA = REPO / "data" / "events" / "licitacions_dependencia_bergueda.parquet"
OUT = REPO / "data" / "web" / "licitacions-bergueda.json"

FONT = "Plataforma de Serveis de Contractació Pública (Generalitat) · Socrata ybgg-dgi6"


def _eur(v: Any) -> int | None:
    if v is None or pd.isna(v):
        return None
    return int(round(float(v)))


def build() -> dict:
    enr = pd.read_parquet(ENRIQUIT)
    rep = pd.read_parquet(REPARTIMENT)
    dep = pd.read_parquet(DEPENDENCIA)
    dep["ine5"] = dep["ine5"].astype(str).str.zfill(5)

    # --- Resum comarcal ---
    ambit = enr["ambit"].value_counts().to_dict()
    temes = (
        enr.groupby("tema_administratiu")
        .agg(n=("event_id", "count"), import_=("import", "sum"))
        .reset_index()
        .sort_values("n", ascending=False)
    )
    comarca = {
        "n_contractes": int(len(enr)),
        "n_comarcal": int(ambit.get("comarcal", 0)),
        "n_municipal": int(ambit.get("municipal", 0)),
        "import_total": _eur(enr["import"].sum()),
        "temes": [
            {"tema": r["tema_administratiu"], "n": int(r["n"]), "import": _eur(r["import_"])}
            for _, r in temes.iterrows()
        ],
        "dependencia": {k: int(v) for k, v in dep["dependencia_lectura"].value_counts().items()},
    }

    # --- Top temes que cada municipi REP del Consell (repartiment supramunicipal) ---
    rep_by_muni: dict[str, list[dict]] = {}
    if "import_assignat" in rep.columns:
        rep2 = rep.dropna(subset=["ine5"]).copy()
        rep2["ine5"] = rep2["ine5"].astype(str).str.zfill(5)
        g = (
            rep2.groupby(["ine5", "tema_administratiu"])["import_assignat"]
            .sum()
            .reset_index()
            .sort_values(["ine5", "import_assignat"], ascending=[True, False])
        )
        for ine5, sub in g.groupby("ine5"):
            rep_by_muni[ine5] = [
                {"tema": r["tema_administratiu"], "import": _eur(r["import_assignat"])}
                for _, r in sub.head(3).iterrows()
            ]

    # --- Fila per municipi ---
    municipis = []
    for _, r in dep.sort_values("ine5").iterrows():
        ratio = r["dependencia_supramunicipal"]
        municipis.append(
            {
                "ine5": r["ine5"],
                "nom": r["nom_muni"],
                "poblacio": _eur(r["poblacio"]),
                "import_municipal_directe": _eur(r["import_municipal_directe"]),
                "n_contractes_municipal": int(r["n_contractes_municipal"]),
                "import_serveis_comarcals": _eur(r["import_serveis_comarcals_assignables"]),
                "dependencia_ratio": None if pd.isna(ratio) else round(float(ratio), 3),
                "dependencia_lectura": r["dependencia_lectura"],
                "confianca": None if pd.isna(r.get("confianca")) else float(r["confianca"]),
                "temes_rebuts": rep_by_muni.get(r["ine5"], []),
            }
        )

    return {"scope": "Berguedà", "font": FONT, "comarca": comarca, "municipis": municipis}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="export_licitacions")
    ap.add_argument("--check", action="store_true", help="no escriu; falla si el JSON està desactualitzat")
    args = ap.parse_args(argv)

    for p in (ENRIQUIT, REPARTIMENT, DEPENDENCIA):
        if not p.exists():
            print(f"FALLA: no existeix {p} (executa abans packages/signals: licitacions)", file=sys.stderr)
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
    c = data["comarca"]
    print(
        f"Escrit {OUT.relative_to(REPO).as_posix()} · {c['n_contractes']} contractes "
        f"({c['n_comarcal']} comarcals + {c['n_municipal']} municipals) · "
        f"{len(data['municipis'])} municipis · dependencia={c['dependencia']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
