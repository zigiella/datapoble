#!/usr/bin/env python3
"""Exporta la presència estimada (qui dorm) EN RANG per a Catalunya — artefacte publicable.

Decisió Bea (2026-06-16): publicar el Nivell C com a RANG (no xifra absoluta), amb la metodologia
ben documentada. Aquest és el primer artefacte que treu el carril de dades del silenci: estimacions
de presència real més enllà del Berguedà, sempre com a interval honest.

Producte = la NOSTRA estimació del model (base elèctrica per persona ~ densitat + renda + gas,
calibrada amb l'ETCA), donada en RANG (banda = residual held-out per tipus territorial). On hi ha
ETCA oficial (municipis ≥1.000 hab) es mostra com a VALIDACIÓ, no la substituïm: el mètode és el
producte i l'ETCA en prova la fiabilitat.

Llegeix els artefactes interns ja calculats (sense re-baixar res):
  · data/territorial/nivellc_analisi.csv     (resident, etca, tipus per muni)
  · data/territorial/nivellc_regressio.csv   (base_implied, base_pred, err_loo_pct per muni)
Escriu: data/web/pernocta-catalunya.json  (publicable; el copia copy-data.mjs a static/).

Banda: per a cada muni, pop = kWh / base. El model prediu base_pred; el residual held-out
(err_loo = (base_implied − base_pred)/base_pred) per al seu TIPUS dona el rang del base real, i
per tant l'invers per a la població: pop ∈ pernocta / (1 + [p90, p10]/100).

NOTA: aquesta primera tanda cobreix els municipis amb ETCA (≥1.000 hab) de les comarques ja
ingerides. Els <1.000 (els petits turístics, el cas que més ho necessita) requereixen baixar-ne
les covariables a part — següent pas.

Ús:  python tools/export_pernocta_catalunya.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANAL = REPO / "data" / "territorial" / "nivellc_analisi.csv"
REGR = REPO / "data" / "territorial" / "nivellc_regressio.csv"
OUT = REPO / "data" / "web" / "pernocta-catalunya.json"
GO_ERR = 15.0


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _pct(xs: list[float], p: float) -> float:
    s = sorted(xs)
    if not s:
        return 0.0
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not ANAL.exists() or not REGR.exists():
        print("FALLA: cal nivellc_analisi.csv i nivellc_regressio.csv", file=sys.stderr)
        return 2

    anal = {r["ine5"]: r for r in csv.DictReader(ANAL.open(encoding="utf-8"))}
    regr = list(csv.DictReader(REGR.open(encoding="utf-8")))

    # Banda per tipus: percentils p10/p90 del residual held-out (err_loo_pct).
    by_tipus: dict[str, list[float]] = {}
    for r in regr:
        e = _f(r.get("err_loo_pct"))
        if e is not None:
            by_tipus.setdefault(r["tipus_territorial"], []).append(e)
    band = {t: (_pct(v, 10), _pct(v, 90)) for t, v in by_tipus.items()}

    munis = {}
    n_cov = 0
    for r in regr:
        ine5 = r["ine5"]
        tipus = r["tipus_territorial"]
        etca = _f(r.get("etca"))
        base_implied = _f(r.get("base_implied"))
        base_pred = _f(r.get("base_pred"))
        if not (etca and base_implied and base_pred):
            continue
        a = anal.get(ine5, {})
        padro = _f(a.get("resident"))
        # pernocta del model: kWh/base_pred = (base_implied·etca)/base_pred
        est = base_implied * etca / base_pred
        p10, p90 = band.get(tipus, (-GO_ERR, GO_ERR))
        low = est / (1 + p90 / 100)   # p90 (base més alt) → població més baixa
        high = est / (1 + p10 / 100)  # p10 (base més baix) → població més alta
        within = abs((est - etca) / etca * 100) <= GO_ERR  # el model cau a prop de l'ETCA?
        munis[ine5] = {
            "nom": r.get("municipi"),
            "tipus": tipus,
            "padro": int(padro) if padro else None,
            "estimacio": int(round(est)),
            "rang_baix": int(round(low)),
            "rang_alt": int(round(high)),
            "etca_oficial": int(etca),  # validació (Idescat EPE); munis ≥1.000 hab
            "dins_banda": within,
        }
        n_cov += 1

    payload = {
        "metode": "Nivell C · presència estimada (qui dorm) = consum elèctric domèstic / base, "
                  "amb base ~ log10(densitat) + renda + fracció de gas, calibrada amb l'ETCA. "
                  "Inferència, no cens: es publica EN RANG (banda p10–p90 del residual per tipus).",
        "model": {"r2": 0.65, "covariables": ["densitat", "renda", "gas"], "n_calibracio": len(regr),
                  "validacio": "ETCA oficial (Idescat EPE) als municipis ≥1.000 hab; held-out robust"},
        "nota_abast": "Primera tanda: municipis amb ETCA (≥1.000 hab) de Berguedà, Barcelonès, "
                      "Tarragonès, Baix Llobregat i Maresme. Els <1.000 (petits turístics) i la resta "
                      "de Catalunya s'incorporen poc a poc, verificant.",
        "munis": dict(sorted(munis.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {n_cov} municipis · {kb:.0f} kB")
    print("Banda per tipus (p10/p90 del residual held-out):")
    for t, (a, b) in sorted(band.items()):
        print(f"  {t:22} [{a:+.0f}, {b:+.0f}]%")
    print("\nMostra (estimació · rang · ETCA oficial):")
    for ine5 in list(munis)[:6]:
        m = munis[ine5]
        print(f"  {m['nom'][:22]:22} {m['estimacio']:>8}  [{m['rang_baix']}–{m['rang_alt']}]  "
              f"ETCA {m['etca_oficial']}  {'✓dins' if m['dins_banda'] else '·fora'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
