#!/usr/bin/env python3
"""Indicadors a escala CATALUNYA per al mapa (vista municipi completa).

El mapa coroplètic té dades de TOTS els indicadors només al Berguedà (dataset profund). Per «completar»
la vista municipi, exposem aquí els indicadors que SÍ tenim a tot Catalunya, perquè el mapa pugui
pintar els ~927 munis coberts pel mateix indicador (no només el Berguedà):

  · gap_pernocta_pct   = (presència estimada − padró) / padró × 100   (Nivell C, pernocta)
  · kg_hab_any         = residus kg/hab/any                            (ARC, baixat aquí directament)

(Extensible: densitat, renda, gas, turisme RTC/resident es poden afegir com a indicadors nous.)

Claus IDÈNTIQUES a les del selector (MetricKey) perquè el mapa hi accedeixi uniformement. Per als
munis del Berguedà ja hi ha el valor ric al dataset; aquest artefacte cobreix la RESTA. Honest: són
inferència (rang) per al gap; mesura directa per als residus.

Sortida: data/web/indicadors-catalunya.json = { ine5: { gap_pernocta_pct, kg_hab_any } }.
Ús:  python tools/export_indicadors_cat.py
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PERN = REPO / "data" / "web" / "pernocta-catalunya.json"
OUT = REPO / "data" / "web" / "indicadors-catalunya.json"
ARC_URL = "https://analisi.transparenciacatalunya.cat/resource/69zu-w48s.json"  # residus municipals


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def fetch_residus_cat() -> dict[str, float]:
    """kg/hab/any de l'any més recent per ine5 (ARC, tot Catalunya). Bulk, sense filtre de comarca."""
    q = urllib.parse.urlencode({"$select": "codi_municipi,any,kg_hab_any", "$limit": 300000})
    req = urllib.request.Request(f"{ARC_URL}?{q}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        rows = json.load(r)
    latest: dict[str, tuple[int, float]] = {}
    for row in rows:
        ine5 = str(row.get("codi_municipi", "")).zfill(6)[:5]
        any_ = int(_f(row.get("any")) or 0)
        kg = _f(row.get("kg_hab_any"))
        if kg is None:
            continue
        if ine5 not in latest or any_ > latest[ine5][0]:
            latest[ine5] = (any_, kg)
    return {k: round(v[1], 1) for k, v in latest.items()}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    pern = json.loads(PERN.read_text(encoding="utf-8"))["munis"]
    residus = fetch_residus_cat()

    out = {}
    for ine5, p in pern.items():
        rec = {}
        if p.get("padro"):
            rec["gap_pernocta_pct"] = round((p["estimacio"] - p["padro"]) / p["padro"] * 100, 1)
        if ine5 in residus:
            rec["kg_hab_any"] = residus[ine5]
        if rec:
            out[ine5] = rec
    # munis amb residus però sense pernocta (rar): també hi entren amb el que tinguin.
    for ine5, kg in residus.items():
        out.setdefault(ine5, {}).setdefault("kg_hab_any", kg)

    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    ngap = sum(1 for v in out.values() if "gap_pernocta_pct" in v)
    nres = sum(1 for v in out.values() if "kg_hab_any" in v)
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {len(out)} munis · {kb:.0f} kB "
          f"(gap: {ngap}, residus: {nres})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
