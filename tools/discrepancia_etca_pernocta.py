#!/usr/bin/env python3
"""Partició honesta dels municipis on la nostra pernocta i l'ETCA discrepen de SIGNE.

Pregunta de Fase 1 (reconducció · nota Rapaz): el «31% de signe oposat» (151/486 munis amb ETCA)
és senyal o soroll? A prop de zero, el signe el decideix el NOSTRE marge d'error, no el territori:
celebrar els 151 crus seria divulgar el nostre soroll com a tesi. Els partim:

  · SENYAL: l'interval predictiu per municipi de la nostra estimació (rang_baix–rang_alt, = banda
    p10–p90 de la calibració) EXCLOU el padró → afirmem el signe de la nostra pernocta amb confiança;
    i, costat ETCA, |gap ETCA| ≥ ETCA_MIN_PCT (paràmetre declarat, no veritat: Idescat no en publica
    marge a aquesta desagregació).
  · SOROLL: l'interval inclou el padró (no podem ni afirmar el nostre propi signe) → el «signe
    oposat» és un artefacte del marge.

Segona dimensió: densitat. Hipòtesi (patró Barcelona): els casos forts són nuclis DENSOS amb pernocta
negativa i ETCA positiva (es buiden de nit, s'omplen de dia). El creuament la confirma o la tomba.

Aquest és l'insum del PRIMER scatter de /metodologia (x = la nostra pernocta, y = ETCA, diagonal
y=x, banda de soroll ombrejada). Entrades committejades (cap fetch → reproduïble):
  · data/web/pernocta-catalunya.json    (padro, estimacio, rang_baix/alt, etca_oficial)
  · data/territorial/nivellc_analisi.csv (densitat_hab_km2 per ine5)
Sortida: data/territorial/discrepancia_etca_pernocta.csv (486 munis, l'scatter) + resum a stdout.

Ús:
    python tools/discrepancia_etca_pernocta.py            # escriu la taula
    python tools/discrepancia_etca_pernocta.py --check     # falla si la taula està desactualitzada
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from statistics import median

REPO = Path(__file__).resolve().parents[1]
PERN = REPO / "data" / "web" / "pernocta-catalunya.json"
ANAL = REPO / "data" / "territorial" / "nivellc_analisi.csv"
OUT = REPO / "data" / "territorial" / "discrepancia_etca_pernocta.csv"

# Paràmetre declarat (NO veritat): Idescat no publica marge d'ETCA a escala municipal, així que
# exigim una magnitud mínima perquè el seu signe compti com a afirmat. 5% és prudent i revisable.
ETCA_MIN_PCT = 5.0


def _gap(value: float, padro: float) -> float:
    return (value - padro) / padro * 100.0


def build_rows() -> list[dict]:
    munis = json.loads(PERN.read_text(encoding="utf-8"))["munis"]
    dens: dict[str, float] = {}
    with ANAL.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                dens[r["ine5"]] = float(r["densitat_hab_km2"])
            except (KeyError, TypeError, ValueError):
                pass

    rows: list[dict] = []
    for ine5, mu in munis.items():
        padro = mu.get("padro")
        est = mu.get("estimacio")
        etca = mu.get("etca_oficial")
        lo, hi = mu.get("rang_baix"), mu.get("rang_alt")
        if not (padro and padro > 0 and est is not None and etca):
            continue  # només els municipis amb ETCA oficial (l'scatter)
        our = _gap(est, padro)
        eg = _gap(etca, padro)
        our_lo, our_hi = _gap(lo, padro), _gap(hi, padro)
        # L'interval per-muni exclou el padró (zero del gap)?
        exclou_zero = not (lo <= padro <= hi)
        oposat = (our < 0) != (eg < 0) and our != 0 and eg != 0
        if not oposat:
            classe = "coincident"
        elif exclou_zero and abs(eg) >= ETCA_MIN_PCT:
            classe = "senyal"
        else:
            classe = "soroll"
        rows.append({
            "ine5": ine5,
            "nom": mu.get("nom"),
            "densitat_hab_km2": round(dens[ine5], 1) if ine5 in dens else "",
            "our_gap_pct": round(our, 1),
            "etca_gap_pct": round(eg, 1),
            "our_lo_pct": round(our_lo, 1),
            "our_hi_pct": round(our_hi, 1),
            "signe_oposat": int(oposat),
            "classe": classe,
        })
    rows.sort(key=lambda r: r["ine5"])
    return rows


def render(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["ine5", "nom", "densitat_hab_km2", "our_gap_pct",
                                        "etca_gap_pct", "our_lo_pct", "our_hi_pct", "signe_oposat",
                                        "classe"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="discrepancia_etca_pernocta")
    ap.add_argument("--check", action="store_true", help="no escriu; falla si la taula està desactualitzada")
    args = ap.parse_args(argv)

    for p in (PERN, ANAL):
        if not p.exists():
            print(f"FALLA: no existeix {p}", file=sys.stderr)
            return 2

    rows = build_rows()
    payload = render(rows)

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

    n = len(rows)
    oposats = [r for r in rows if r["signe_oposat"]]
    senyal = [r for r in oposats if r["classe"] == "senyal"]
    soroll = [r for r in oposats if r["classe"] == "soroll"]
    # Patró Barcelona entre els senyals: dens, pernocta negativa, ETCA positiva.
    patro = [r for r in senyal if r["our_gap_pct"] < 0 < r["etca_gap_pct"]]
    dens_patro = [r["densitat_hab_km2"] for r in patro if r["densitat_hab_km2"] != ""]
    dens_altres = [r["densitat_hab_km2"] for r in senyal if r not in patro and r["densitat_hab_km2"] != ""]

    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {n} municipis amb ETCA")
    print(f"\nDe {len(oposats)} amb SIGNE OPOSAT (la xifra que es pot ensenyar sense por):")
    print(f"  · SENYAL (interval exclou el padró i |ETCA|≥{ETCA_MIN_PCT:.0f}%):  {len(senyal)}")
    print(f"  · SOROLL (a prop de zero, dins el nostre marge):           {len(soroll)}")
    print("\nCreuament amb densitat (hipòtesi patró Barcelona: dens · pernocta − · ETCA +):")
    print(f"  · senyals amb el patró (pernocta − / ETCA +): {len(patro)} de {len(senyal)}")
    if dens_patro and dens_altres:
        print(f"    densitat mediana — amb patró: {median(dens_patro):.0f} hab/km²  ·  "
              f"resta de senyals: {median(dens_altres):.0f} hab/km²")
    bcn = next((r for r in rows if r["ine5"] == "08019"), None)
    if bcn:
        print(f"\nBarcelona: nostra {bcn['our_gap_pct']:+.1f}%  ·  ETCA {bcn['etca_gap_pct']:+.1f}%  "
              f"·  interval nostre [{bcn['our_lo_pct']:+.0f},{bcn['our_hi_pct']:+.0f}]%  → {bcn['classe']}")
    print(f"\nNota: ETCA_MIN_PCT={ETCA_MIN_PCT:.0f}% és un PARÀMETRE declarat (Idescat no publica marge "
          "municipal), no una veritat. Amb error per tipus territorial, el llindar nostre serà per tipus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
