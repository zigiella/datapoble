#!/usr/bin/env python3
"""Indicadors COMPACTES a escala Catalunya per al MAPA (vista municipi).

El mapa és client-side: no pot carregar el dataset sencer (1,8 MB). Aquest artefacte compacte li dona,
per municipi, NOMÉS el que necessita per pintar i tramar tot Catalunya:
  · gap_pernocta_pct, kg_hab_any  → els indicadors que el mapa pinta a escala CAT (color del cobert).
  · conf                          → la CONFIANÇA (baixa/mitjana/alta) per a les TRAMES (confiança baixa
                                    velada) i el tooltip uniforme. (clau `conf`, no `confianca`, per no
                                    xocar amb la MetricKey homònima al contracte del frontend.)

Deriva de `data/web/municipis.catalunya.json` (F3) — MATEIXA font que la fitxa (DRY, coherent). Per als
munis del Berguedà el valor ric ja és al dataset del web; aquest artefacte cobreix tot CAT de forma
compacta. Honest: és inferència (rang) per al gap; mesura per als residus.

Sortida: data/web/indicadors-catalunya.json = { ine5: { gap_pernocta_pct?, kg_hab_any?, conf? } }.
Ús:  python tools/export_indicadors_cat.py   (després d'export_web_municipis.py --scope catalunya)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "web" / "municipis.catalunya.json"
OUT = REPO / "data" / "web" / "indicadors-catalunya.json"

# Indicadors numèrics que el mapa pinta a escala Catalunya (clau de mètrica → s'hi accedeix igual).
NUM_KEYS = ("gap_pernocta_pct", "kg_hab_any")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not SRC.exists():
        print(f"FALLA: no existeix {SRC} (executa abans export_web_municipis.py --scope catalunya)",
              file=sys.stderr)
        return 2

    data = json.loads(SRC.read_text(encoding="utf-8"))["municipis"]
    out: dict[str, dict] = {}
    for ine5, muni in data.items():
        v = muni.get("values", {})
        rec: dict = {}
        for k in NUM_KEYS:
            if isinstance(v.get(k), (int, float)):
                rec[k] = v[k]
        conf = v.get("confianca")
        if isinstance(conf, str):
            rec["conf"] = conf
        if rec:
            out[ine5] = rec

    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    ngap = sum(1 for r in out.values() if "gap_pernocta_pct" in r)
    nres = sum(1 for r in out.values() if "kg_hab_any" in r)
    ncf = sum(1 for r in out.values() if "conf" in r)
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {len(out)} munis · {kb:.0f} kB "
          f"(gap: {ngap}, residus: {nres}, conf: {ncf})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
