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
PERN = REPO / "data" / "web" / "pernocta-catalunya.json"
OUT = REPO / "data" / "web" / "indicadors-catalunya.json"

# Indicadors numèrics que el mapa pinta a escala Catalunya (clau de mètrica → s'hi accedeix igual).
# Tots tenen valor calculat al mart per a tot CAT (deriven de senyals que ja cobreixen el país:
# residus, EMEX, RTC). Els únics indicadors del mapa que NO hi són són tipologia i restauració
# (depenen d'OSM, encara només-Berguedà → 2a onada).
# `index_turisme` DEPRECAT (#267): fora del publicador (satura a 100 · re-escala lossy de
# vidre_hab). El mapa ja no el pinta; per a la lectura d'hostaleria, vidre_hab (kg/hab).
NUM_KEYS = (
    "gap_pernocta_pct", "kg_hab_any", "densitat_hab_km2", "renda_neta_persona",
    "carrega_total_est", "IETR", "pct_noprincipal", "divergencia_senyals",
    "restauracio_per_1000hab",
)


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
    # Costura del gap al MAPA (regla del règim dens): on hi ha ETCA oficial (≥1.000 hab) MANA Idescat
    # —mai la nostra pernocta pintada de fort (Barcelona, el Prat, l'Hospitalet… serien artefacte)—.
    # Així el color del cobert ja es pinta amb el gap d'Idescat; la nostra estimació queda com a
    # CONTRAST anotat (`gap_nostra`) per al tooltip. Als <1.000 (sense ETCA) es manté la nostra,
    # tramada per confiança baixa. El waveform fa el contrari (la nostra mètrica és l'heroi): és una
    # decisió PER SUPERFÍCIE, no una còpia.
    pern = json.loads(PERN.read_text(encoding="utf-8"))["munis"] if PERN.exists() else {}

    out: dict[str, dict] = {}
    for ine5, muni in data.items():
        v = muni.get("values", {})
        rec: dict = {}
        for k in NUM_KEYS:
            if isinstance(v.get(k), (int, float)):
                rec[k] = v[k]
        # Override del gap per als munis amb ETCA: el color del mapa mostra Idescat, no la nostra.
        p = pern.get(ine5)
        if p and isinstance(p.get("etca_oficial"), (int, float)) and p.get("padro"):
            idescat_gap = round((p["etca_oficial"] - p["padro"]) / p["padro"] * 100, 1)
            if isinstance(rec.get("gap_pernocta_pct"), (int, float)):
                rec["gap_nostra"] = rec["gap_pernocta_pct"]  # la nostra estimació, ara com a contrast
            rec["gap_pernocta_pct"] = idescat_gap
        conf = v.get("confianca")
        if isinstance(conf, str):
            rec["conf"] = conf
        # tipologia (categòrica): clau `tip` per pintar els coberts al mapa (capa categòrica).
        tip = v.get("tipologia")
        if isinstance(tip, str) and tip != "pendent":
            rec["tip"] = tip
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
