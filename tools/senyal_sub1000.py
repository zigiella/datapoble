#!/usr/bin/env python3
"""Senyal vs soroll dels municipis <1.000 hab (sense ETCA) — el número que decideix l'arquitectura.

Decisió de direcció (Bea + Rapaz, 2026-06-29 · `docs/dossier-consultoria-2026-06/05-vot-tres-registres.md`):
la frontera del producte públic sota mil habitants NO és la població del municipi, sinó si la NOSTRA
estimació es distingeix del NOSTRE error. Aquesta eina fa recalculable per qualsevol el número que ho
decideix (els ~99), igual com `discrepancia_etca_pernocta.py` fa recalculables els 8 dels 151.

Univers: els municipis SENSE ETCA (`etca_oficial = null` a pernocta-catalunya.json), és a dir el
<1.000 hab on només existeix la nostra estimació (no hi ha font oficial per validar).

Criteri (única porta auditable sense ETCA — mateix MECANISME que la primera porta dels 151):
  · SENYAL: l'interval de pernocta per municipi [rang_baix, rang_alt] EXCLOU el padró → afirmem que
    la presència es distingeix del padró amb confiança. `senyal_mes` (tot l'interval per sobre → hi
    dorm més) o `senyal_menys` (tot per sota → hi dorm menys).
  · SOROLL: l'interval inclou el padró → no podem distingir el gap del nostre marge; es replega.

La MAGNITUD no és una segona porta. Als 151 la segona porta era |ETCA|≥5% (corroboració oficial
INDEPENDENT); aquest univers, per definició, no té ETCA. Exigir més magnitud no és corroboració: és
el mateix model parlant més fort, i un model pot estar molt segur i sistemàticament equivocat (el
règim dens). Per tant `marge_rel_pct` (com de lluny cau el padró de la vora que l'exclou) NO filtra
res: només GRADUA el to a la fitxa (veu més ferma com més l'exclou; rang i to més prudents com més
just sigui el marge).

Honestedat: passar aquest llindar és senyal INTERN («el model n'està segur»), no validació externa
(«ho hem comprovat»). La validació oficial d'aquest univers, si arriba, serà el test multianual
(persistència del gap 2013–2024), no aquesta porta.

Entrada (committejada → reproduïble, cap fetch):
  · data/web/pernocta-catalunya.json  (padro, estimacio, rang_baix/alt, etca_oficial, tipus)
Sortida: data/territorial/senyal_sub1000.csv (els <1.000 avaluables) + resum a stdout.

Ús:
    python tools/senyal_sub1000.py            # escriu la taula
    python tools/senyal_sub1000.py --check     # falla si la taula està desactualitzada
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PERN = REPO / "data" / "web" / "pernocta-catalunya.json"
OUT = REPO / "data" / "territorial" / "senyal_sub1000.csv"

FIELDS = ["ine5", "nom", "tipus", "padro", "estimacio", "rang_baix", "rang_alt",
          "registre", "marge_rel_pct"]


def build_rows() -> list[dict]:
    munis = json.loads(PERN.read_text(encoding="utf-8"))["munis"]
    rows: list[dict] = []
    for ine5, mu in munis.items():
        if mu.get("etca_oficial") is not None:
            continue  # univers = <1.000 hab sense ETCA (només la nostra estimació)
        padro = mu.get("padro")
        est = mu.get("estimacio")
        lo, hi = mu.get("rang_baix"), mu.get("rang_alt")
        if not (padro and padro > 0 and est is not None and lo is not None and hi is not None):
            continue  # sense banda → no avaluable aquí (els ~20 micromunis: base oficial i prou)
        if lo > padro:
            registre = "senyal_mes"            # tot l'interval per sobre del padró
            marge = (lo - padro) / padro * 100.0
        elif hi < padro:
            registre = "senyal_menys"          # tot l'interval per sota del padró
            marge = (padro - hi) / padro * 100.0
        else:
            registre = "soroll"                # el padró cau dins → inclou el zero
            marge = 0.0
        rows.append({
            "ine5": ine5,
            "nom": mu.get("nom"),
            "tipus": mu.get("tipus"),
            "padro": padro,
            "estimacio": est,
            "rang_baix": lo,
            "rang_alt": hi,
            "registre": registre,
            "marge_rel_pct": round(marge, 1),
        })
    rows.sort(key=lambda r: r["ine5"])
    return rows


def render(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="senyal_sub1000")
    ap.add_argument("--check", action="store_true", help="no escriu; falla si la taula està desactualitzada")
    args = ap.parse_args(argv)

    if not PERN.exists():
        print(f"FALLA: no existeix {PERN}", file=sys.stderr)
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
        print(f"OK (--check): {OUT} al dia ({len(rows)} municipis <1.000 avaluables).")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)

    n = len(rows)
    mes = [r for r in rows if r["registre"] == "senyal_mes"]
    menys = [r for r in rows if r["registre"] == "senyal_menys"]
    soroll = [r for r in rows if r["registre"] == "soroll"]
    senyal = len(mes) + len(menys)
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {n} municipis <1.000 avaluables")
    print(f"\nLa xifra que decideix l'arquitectura (interval exclou el padró):")
    print(f"  · SENYAL: {senyal}  ({senyal / n * 100:.0f}%)   → registre 2 (costura amb veu graduada)")
    print(f"      · hi dorm MÉS que el padró:   {len(mes)}")
    print(f"      · hi dorm MENYS que el padró: {len(menys)}")
    print(f"  · SOROLL: {len(soroll)}  ({len(soroll) / n * 100:.0f}%)   → registre 3 (base oficial i prou)")
    print("\nNota: SENYAL = el model n'està segur (porta interna), NO validació externa. La magnitud "
          "(marge_rel_pct) gradua el TO a la fitxa, no filtra: no hi ha ETCA per a una segona porta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
