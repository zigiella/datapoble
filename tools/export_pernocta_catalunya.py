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

Ús:
    python tools/export_pernocta_catalunya.py            # escriu el JSON
    python tools/export_pernocta_catalunya.py --check     # no escriu; falla si està desactualitzat
"""
from __future__ import annotations

import argparse
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


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="export_pernocta_catalunya")
    ap.add_argument(
        "--check", action="store_true",
        help="no escriu; falla (codi 1) si el JSON al disc no coincideix amb el generat",
    )
    args = ap.parse_args(argv)
    if not ANAL.exists() or not REGR.exists():
        print("FALLA: cal nivellc_analisi.csv i nivellc_regressio.csv", file=sys.stderr)
        return 2

    anal = {r["ine5"]: r for r in csv.DictReader(ANAL.open(encoding="utf-8"))}
    regr = list(csv.DictReader(REGR.open(encoding="utf-8")))

    # Banda per tipus: percentils p10/p90 del residual held-out (err_loo_pct) — només munis amb ETCA.
    by_tipus: dict[str, list[float]] = {}
    for r in regr:
        e = _f(r.get("err_loo_pct"))
        if e is not None:
            by_tipus.setdefault(r["tipus_territorial"], []).append(e)
    band = {t: (_pct(v, 10), _pct(v, 90)) for t, v in by_tipus.items()}
    all_loo = [e for v in by_tipus.values() for e in v]
    band_global = (_pct(all_loo, 10), _pct(all_loo, 90)) if all_loo else (-GO_ERR, GO_ERR)
    # Munis SENSE ETCA (<1.000 hab, no validables): banda eixamplada (honestedat: més incertesa).
    WIDEN = 1.5

    munis = {}
    for r in regr:
        ine5 = r["ine5"]
        tipus = r["tipus_territorial"]
        base_pred = _f(r.get("base_pred"))
        kwh = _f(r.get("kwh_dom"))
        etca = _f(r.get("etca"))
        # Palanca 2: l'estimació és kWh/base_pred — l'ETCA NO hi cal (només valida). Així cobrim
        # també els <1.000 hab. Cal base_pred i consum vàlids: els micromunis sense covariables
        # (base_pred/kwh absents) s'exclouen aquí — són el forat 947→927 i a la fitxa surten com a
        # «sense estimació» (mai una xifra inventada). Sanejat coherent: a municipis.catalunya.json
        # aquests munis tenen la confiança anul·lada (export_web_municipis.py).
        if not (base_pred and base_pred > 0 and kwh and kwh > 0):
            continue
        est = kwh / base_pred
        p10, p90 = band.get(tipus, band_global)
        if not etca:
            p10, p90 = p10 * WIDEN, p90 * WIDEN  # sense validació oficial → banda més ampla
        low = est / (1 + p90 / 100)   # p90 (base més alt) → població més baixa
        high = est / (1 + p10 / 100)  # p10 (base més baix) → població més alta
        a = anal.get(ine5, {})
        padro = _f(a.get("poblacio")) or _f(a.get("resident"))
        within = (abs((est - etca) / etca * 100) <= GO_ERR) if etca else False
        munis[ine5] = {
            "nom": r.get("municipi"),
            "tipus": tipus,
            "padro": int(padro) if padro else None,
            "estimacio": int(round(est)),
            "rang_baix": int(round(low)),
            "rang_alt": int(round(high)),
            "etca_oficial": int(etca) if etca else None,  # validació (Idescat EPE); null si <1.000 hab
            "dins_banda": within,
        }
    n_cov = len(munis)
    n_etca = sum(1 for m in munis.values() if m["etca_oficial"] is not None)

    payload = {
        "metode": "Nivell C · presència estimada (qui dorm) = consum elèctric domèstic / base, "
                  "amb base ~ log10(densitat) + renda + fracció de gas, calibrada amb l'ETCA. "
                  "Inferència, no cens: es publica EN RANG (banda p10–p90 del residual held-out per "
                  "tipus territorial; eixamplada als municipis sense ETCA oficial).",
        "model": {"r2": 0.41, "covariables": ["densitat", "renda", "gas"], "n_calibracio": n_etca,
                  "validacio": "ETCA oficial (Idescat EPE) als municipis ≥1.000 hab; held-out robust "
                               "(cobertura ±15% ≈ 70%; el litoral vacacional, més feble per l'estacionalitat)"},
        "nota_abast": "Cobreix tota Catalunya amb senyal elèctric i covariables. Els municipis amb ETCA "
                      "(≥1.000 hab) es validen contra la dada oficial; els <1.000 hab es donen amb banda "
                      "més ampla i SENSE validació oficial. Classificació litoral = llista OFICIAL de 70 "
                      "municipis costaners (Territori/PPOL, Llei 8/2020).",
        "munis": dict(sorted(munis.items())),
    }
    out_str = json.dumps(payload, ensure_ascii=False, indent=1) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"FALLA (--check): no existeix {OUT}", file=sys.stderr)
            return 1
        # Lectura sense traducció de finals de línia (newline="") → comparació estable LF/CRLF.
        with OUT.open("r", encoding="utf-8", newline="") as fh:
            if fh.read() != out_str:
                print(f"FALLA (--check): {OUT} desactualitzat (re-executa sense --check)", file=sys.stderr)
                return 1
        print(f"OK (--check): {OUT} al dia ({n_cov} municipis).")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n": LF explícit (no CRLF a Windows) → byte-estable amb .gitattributes eol=lf.
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(out_str)
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
