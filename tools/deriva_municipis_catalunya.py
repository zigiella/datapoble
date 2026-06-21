#!/usr/bin/env python3
"""Registre de municipis de tot Catalunya (crosswalk codi6 ↔ ine5 ↔ nom).

És el FONAMENT de l'extensió a tota Catalunya (F1 de docs/pla-catalunya-profund.md): substitueix la
llista hardcoded dels 31 del Berguedà (packages/ingestion/.../municipis.py) per els 947 munis, amb el
`codi6` (codi Idescat de 6 dígits = ine5 + dígit de control) que necessiten els connectors per-muni
(EMEX, demografia/origen: l'endpoint és `?id={codi6}`).

Fonts (cap número sense procedència):
  · `ine5` + `nom` CANÒNICS  → geometria oficial ICGC (`catalunya-municipis.geojson`, 947 munis).
  · `codi6`                  → ARC residus (Socrata `69zu-w48s`, `codi_municipi`), que cobreix els
                               947 (verificat: 0 forats). Es creua per `ine5` i s'hi imposa el cens
                               canònic de la geometria (es descarten codis fora dels 947: junk/obsolets).

Verificació interna: 947 files, totes amb `codi6`; els 31 codi6 del Berguedà hardcodats han de quadrar
EXACTAMENT (inclòs Gósol 251001, prefix Lleida). Si no, surt amb error (no escriu res dolent).

Sortida: data/territorial/municipis-catalunya.csv  (codi6;ine5;nom)  · delimitador `;` (com municipi_litoral.csv).
Ús:  python tools/deriva_municipis_catalunya.py
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEO = REPO / "packages" / "web" / "static" / "geo" / "catalunya-municipis.geojson"
OUT = REPO / "data" / "territorial" / "municipis-catalunya.csv"
RESIDUS_URL = ("https://analisi.transparenciacatalunya.cat/resource/69zu-w48s.json"
               "?$select=distinct%20codi_municipi&$limit=5000")

# Els 31 codi6 del Berguedà (mirall de la llista hardcoded) per validar el crosswalk.
BERGUEDA_CODI6 = {
    "080116", "080168", "080229", "080240", "080459", "080497", "080500", "080522", "080575",
    "080787", "080804", "080924", "080930", "080996", "081304", "081326", "081424", "081445",
    "081666", "081751", "081770", "081884", "081901", "082166", "082554", "082687", "082938",
    "082994", "083089", "089030", "251001",
}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # 1) Cens canònic (ine5 -> nom) de la geometria oficial.
    geo = json.loads(GEO.read_text(encoding="utf-8"))
    nom_by_ine5 = {str(f["properties"]["ine5"]): str(f["properties"]["nom"]) for f in geo["features"]}
    print(f"geometria: {len(nom_by_ine5)} munis canònics")

    # 2) codi6 de l'ARC, creuat per ine5 (zfill a 6; ine5 = 5 primers dígits).
    rows = json.loads(urllib.request.urlopen(RESIDUS_URL, timeout=90).read())
    codi6_by_ine5: dict[str, str] = {}
    for r in rows:
        raw = r.get("codi_municipi")
        if not raw:
            continue
        codi6 = str(raw).zfill(6)
        codi6_by_ine5[codi6[:5]] = codi6
    print(f"ARC residus: {len(codi6_by_ine5)} codi6 distints")

    # 3) Assemblar els 947 (cens de la geometria mana; codi6 de l'ARC).
    registre = []
    sense_codi6 = []
    for ine5, nom in nom_by_ine5.items():
        codi6 = codi6_by_ine5.get(ine5)
        if not codi6:
            sense_codi6.append((ine5, nom))
            continue
        registre.append({"codi6": codi6, "ine5": ine5, "nom": nom})
    registre.sort(key=lambda r: r["nom"].lower())

    # 4) Verificacions (no escriure res dolent).
    if sense_codi6:
        print(f"ERROR: {len(sense_codi6)} munis de la geometria sense codi6 a l'ARC: {sense_codi6[:10]}",
              file=sys.stderr)
        return 1
    derivat_bergueda = {r["codi6"] for r in registre if r["codi6"] in BERGUEDA_CODI6}
    if derivat_bergueda != BERGUEDA_CODI6:
        falten = BERGUEDA_CODI6 - derivat_bergueda
        print(f"ERROR: el crosswalk no reprodueix els 31 codi6 del Berguedà. Falten: {sorted(falten)}",
              file=sys.stderr)
        return 1
    if len(registre) != len(nom_by_ine5):
        print(f"ERROR: {len(registre)} files (s'esperaven {len(nom_by_ine5)}).", file=sys.stderr)
        return 1

    # 5) Escriure.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codi6", "ine5", "nom"])
        for r in registre:
            w.writerow([r["codi6"], r["ine5"], r["nom"]])
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {len(registre)} munis "
          f"(Berguedà: {len(derivat_bergueda)}/31 ✓)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
