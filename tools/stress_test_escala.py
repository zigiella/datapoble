#!/usr/bin/env python3
"""Stress-test de l'escala: Barcelonès (metro) + Tarragonès turístic (litoral).

Pas 4 · prova del disseny §11.2. Incorpora els dos tipus territorials que TRENQUEN els
supòsits de la base endògena del Berguedà (metro dens / litoral vacacional) i els contrasta
amb l'ETCA oficial. Objectiu: veure SI el classificador `tipus_territorial` (Nivell B) els
tipa bé i CONFIRMAR que cap base única encaixa (litoral es dobla, metro residencial baixa) →
motiva el Nivell C (esperats per tipus).

Carril dades en silenci: artefacte INTERN (no publicat). Baixa en viu d'Idescat (ETCA SSV +
EMEX). Sortida: `data/territorial/stress_test_escala.csv`.

Ús:  python tools/stress_test_escala.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tipus_territorial import classify  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "territorial" / "stress_test_escala.csv"

# Primer lot d'escala (codi6 Idescat → nom). Barcelonès + Tarragonès turístic.
MUNIS = {
    "080193": "Barcelona",
    "081017": "l'Hospitalet de Llobregat",
    "080155": "Badalona",
    "082457": "Santa Coloma de Gramenet",
    "081944": "Sant Adrià de Besòs",
    "439057": "Salou",
    "431482": "Tarragona",
    "430385": "Cambrils",
    "431711": "Vila-seca",
}


def _num(s: str | None):
    s = (s or "").replace(".", "").replace(",", ".").strip()
    return None if s in ("", "..", "(..)", "_", "-") else float(s)


def fetch_etca() -> dict[str, dict]:
    url = "https://www.idescat.cat/pub/?id=epe&n=17886&geo=mun&f=ssv"
    with urllib.request.urlopen(url, timeout=60) as r:
        text = r.read().decode("utf-8-sig")
    lines = text.splitlines()
    h = next(i for i, ln in enumerate(lines) if ln.startswith("Codi;"))
    out = {}
    for row in csv.reader(io.StringIO("\n".join(lines[h:])), delimiter=";"):
        if len(row) >= 8 and row[0].strip() in MUNIS:
            out[row[0].strip()] = {"resident": _num(row[5]), "etca": _num(row[6]), "pct": row[7].strip()}
    return out


def fetch_emex(codi6: str) -> dict:
    url = f"https://api.idescat.cat/emex/v1/dades.json?id={codi6}"
    with urllib.request.urlopen(url, timeout=40) as r:
        d = json.load(r)

    def leaves(n):
        if isinstance(n, dict):
            if "id" in n and "v" in n:
                yield n
            for v in n.values():
                yield from leaves(v)
        elif isinstance(n, list):
            for x in n:
                yield from leaves(x)

    # EMEX dades.json: el valor municipal és el 1r camp (separat per comes); usa «.» decimal
    # i SENSE separador de milers → float() directe (NO el format català de l'SSV).
    def emex_num(v) -> float | None:
        first = str(v).split(",")[0].strip()
        if first in ("", "_", "-"):
            return None
        try:
            return float(first)
        except ValueError:
            return None

    vals = {}
    for lf in leaves(d):
        if lf.get("id") in ("f258", "f262") and lf["id"] not in vals:
            vals[lf["id"]] = emex_num(lf.get("v"))
    return {"altitud": vals.get("f258"), "densitat": vals.get("f262")}


def main() -> int:
    etca = fetch_etca()
    rows = []
    for codi6, nom in MUNIS.items():
        ine5 = codi6[:5]
        em = fetch_emex(codi6)
        e = etca.get(codi6, {})
        rows.append(
            {
                "ine5": ine5,
                "municipi": nom,
                "tipus_territorial": classify(ine5, em["altitud"], em["densitat"]),
                "resident": int(e["resident"]) if e.get("resident") else None,
                "etca": int(e["etca"]) if e.get("etca") else None,
                "etca_pct": e.get("pct"),
                "altitud_m": int(em["altitud"]) if em["altitud"] is not None else "",
                "densitat_hab_km2": em["densitat"] if em["densitat"] is not None else "",
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {len(rows)} munis")
    for r in rows:
        print(f"  {r['municipi']:30} {r['tipus_territorial']:22} ETCA% {r['etca_pct']:>7}  (alt {r['altitud_m']}m, dens {r['densitat_hab_km2']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
