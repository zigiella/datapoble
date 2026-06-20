#!/usr/bin/env python3
"""Pobles MIRALL a escala Catalunya — el bessó FUNCIONAL de cada municipi (backlog #5/#6).

Idea (consultora «municipios espejo» + elaboració Talaia): més útil que el veí geogràfic és el
municipi que es COMPORTA igual. Fins ara només es feia dins el Berguedà (mirall.ts, 31 munis). Amb
el Nivell C estès (#152) ja tenim vectors de característiques per a ~927 munis de tota Catalunya →
el bessó pot ser a l'altra punta del país (un poble turístic del Berguedà ↔ un de la Costa Brava).

Vector de COMPORTAMENT (per càpita / relatiu, NO mida — no volem agrupar per gran/petit):
  · log10(densitat)         (densitat hab/km², de nivellc_analisi)
  · renda_k                 (renda neta/persona, INE ADRH 2023)
  · gas_fraction            (fracció de calefacció de gas)
  · gap                     (presència estimada / padró − 1, de pernocta-catalunya)
  · rtc_per_resident        (places turístiques reglades / resident)
z-normalitzat (cada senyal pesa igual) · distància euclidiana · top-K bessons.

Per a cada bessó, el «senyal que els agermana» = la característica on tots dos són més extrems en la
MATEIXA direcció (co-extremitat); si cap, la més propera. Honest: tota similitud és un mapa mental,
no una mesura (projecció lossy).

Sortida: data/web/municipis-mirall.json = { ine5: {nom, veins: [{ine5, nom, dist, agermana}]} }.
Bulk/offline, reproduïble. Ús:  python tools/deriva_miralls.py
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANAL = REPO / "data" / "territorial" / "nivellc_analisi.csv"
RENDA = REPO / "data" / "territorial" / "renda_municipi_cat.csv"
PERN = REPO / "data" / "web" / "pernocta-catalunya.json"
OUT = REPO / "data" / "web" / "municipis-mirall.json"
K = 6  # bessons per municipi

# Característica → CODI curt del «senyal que els agermana» (la UI el resol a etiqueta i18n).
# Artefacte compacte: no hi guardem ni noms ni etiquetes (es resolen al web des del catàleg + i18n).
FEAT_CODE = {"dens": "d", "renda": "r", "gas": "g", "gap": "p", "turisme": "t"}


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    renda = {}
    for r in csv.DictReader(RENDA.open(encoding="utf-8")):
        v = _f(r.get("renda_neta_persona_2023"))
        if v:
            renda[r["ine5"]] = v / 1000.0

    pern = json.loads(PERN.read_text(encoding="utf-8"))["munis"]

    # Munt el vector per muni (només els que tenen totes les peces).
    rows = {}
    for r in csv.DictReader(ANAL.open(encoding="utf-8")):
        ine5 = r["ine5"]
        dens = _f(r.get("densitat_hab_km2"))
        gas = _f(r.get("gas_fraction"))
        rtcpr = _f(r.get("rtc_places_per_resident"))
        p = pern.get(ine5)
        rk = renda.get(ine5)
        if not (dens and dens > 0 and rk is not None and p and p.get("padro")):
            continue
        gap = (p["estimacio"] - p["padro"]) / p["padro"]
        rows[ine5] = {
            "nom": p["nom"],
            "dens": math.log10(dens),
            "renda": rk,
            "gas": gas if gas is not None else 0.0,
            "gap": gap,
            "turisme": rtcpr if rtcpr is not None else 0.0,
        }

    feats = ["dens", "renda", "gas", "gap", "turisme"]
    ids = list(rows)
    # z-normalització per característica.
    stats = {}
    for f in feats:
        vals = [rows[i][f] for i in ids]
        mean = sum(vals) / len(vals)
        sd = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5 or 1.0
        stats[f] = (mean, sd)
    z = {i: {f: (rows[i][f] - stats[f][0]) / stats[f][1] for f in feats} for i in ids}

    def agermana(a: str, b: str) -> str:
        """Característica on a i b són més co-extrems (mateix signe, tots dos lluny de la mitjana)."""
        best, best_score = None, 0.0
        for f in feats:
            za, zb = z[a][f], z[b][f]
            if za * zb > 0:  # mateixa direcció
                score = min(abs(za), abs(zb))
                if score > best_score:
                    best, best_score = f, score
        if best and best_score >= 0.5:
            return FEAT_CODE[best]
        # cap co-extremitat clara → la característica més propera entre els dos
        closest = min(feats, key=lambda f: abs(z[a][f] - z[b][f]))
        return FEAT_CODE[closest]

    # Compacte: { ine5: [[twinIne5, dist, codiSenyal], …] }. Nom/slug i etiqueta es resolen al web.
    out = {}
    for a in ids:
        za = z[a]
        dists = []
        for b in ids:
            if b == a:
                continue
            d = math.sqrt(sum((za[f] - z[b][f]) ** 2 for f in feats))
            dists.append((d, b))
        dists.sort(key=lambda x: x[0])
        out[a] = [[b, round(d, 2), agermana(a, b)] for d, b in dists[:K]]

    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {len(out)} munis · {kb:.0f} kB")

    # Sanity: els bessons d'uns quants munis emblemàtics.
    by_nom = {rows[k]["nom"]: k for k in ids}
    code2lab = {c: lab for lab, c in zip(["densitat", "renda", "gas", "presència", "turisme"], "drgpt")}
    for nom in ["Salou", "Bolvir", "Barcelona", "Cadaqués", "Berga"]:
        i = by_nom.get(nom)
        if i:
            tw = " · ".join(f"{rows[b]['nom']} ({code2lab.get(c, c)})" for b, _d, c in out[i][:4])
            print(f"  {nom:12} → {tw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
