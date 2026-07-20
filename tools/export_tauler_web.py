#!/usr/bin/env python3
"""Export web del tauler v2 → l'ATUR i la TENDÈNCIA servibles (E4 + E6 + E5).

El forat que tapa: `mart_pols_mensual` porta la sèrie mensual d'atur dels 947 municipis
des de 2006 (224.439 files) i `mart_tendencia` porta la tendència amb el seu període, però
**cap dels dos era servible al web**: el tauler no pot llegir un parquet. És el mateix
forat que D4 va deixar amb `mart_govern` i que #272 va haver de tapar després — aquí
l'export neix amb `--check` i CABLAT AL CI el mateix dia, no en un PR posterior.

Per què un fitxer separat i no dins `municipis.*.json`:
  · CADÈNCIA DIFERENT. L'atur es refresca cada MES (refresh-atur.yml); la resta del
    tauler, un cop l'any o menys. Ficar-ho al mateix JSON faria que el refresc mensual
    rebregués un artefacte de 947 municipis × 54 mètriques cada 30 dies, per una xifra.
  · FORMA DIFERENT: una sèrie temporal no cap a `values: {clau: número}`.

Frontera honesta (aquí NO es calcula res que no vingui dels marts):
  · L'atur es re-serialitza de `mart_pols_mensual` tal com hi és.
  · La tendència ve SENCERA de `mart_tendencia` (deltes, períodes, estat, motiu): aquest
    fitxer no resta cap parell de números. Si un dia un delta és dubtós, el lloc on
    mirar-lo és el mart, no aquest exportador.
  · La DOCTRINA DEL «<5» (C1 §1.1) es propaga literalment: un mes emmascarat surt amb
    `valor: null` + `min`/`max` (l'interval [1,4]) + `emmascarat: true`. MAI zero. Un
    delta que toqui un mes emmascarat surt amb `delta: null` + l'interval. El
    verificador `--check` ho comprova a cada CI.

Abast: els municipis del **Berguedà** (mateixa porta que la vista de govern, C6 §1.2).
Per ampliar: `SCOPE_COMARCA = None`.

Ús:
    python tools/export_tauler_web.py            # (re)genera data/web/tauler.bergueda.json
    python tools/export_tauler_web.py --check    # falla si el fitxer versionat és estale

Jurisdicció: Sondeig (exportadors `tools/export_*.py` + artefactes `data/web/*.json`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
MART_POLS = REPO / "data" / "marts" / "mart_pols_mensual.parquet"
MART_TEND = REPO / "data" / "marts" / "mart_tendencia.parquet"
TERRITORI = REPO / "data" / "web" / "municipis-territori.json"
METRICS_YML = REPO / "semantic" / "metrics.yml"
OUT = REPO / "data" / "web" / "tauler.bergueda.json"

# Comarca de l'abast (C6 §1.2). None = tota Catalunya.
SCOPE_COMARCA: str | None = "Berguedà"

# Mesos de sèrie que s'emeten (comptant el darrer). 25 = el darrer mes + 24 enrere:
# el mínim que permet al front pintar dos anys sencers I ensenyar el mateix mes de
# l'any anterior sense una segona petició. La sèrie completa (2006→) es queda al mart:
# servir 20 anys × 31 municipis al navegador seria pes sense lectura.
MESOS_SERIE = 25

# Mètriques que el mart de tendència ha de portar sí o sí (guarda del contracte del
# fitxer: si el mart deixa d'emetre'n una, l'export falla en comptes d'emetre un tauler
# amb una targeta muda).
TEND_METRICS_ESPERADES = {
    "atur_registrat", "pct_nacionalitat_estrangera", "poblacio_nacionalitat_estrangera",
    "poblacio", "pob_0_14", "pob_15_64", "pob_65_84", "pob_85_mes", "index_envelliment",
    "renda_neta_persona", "pct_noprincipal", "kg_hab_any", "kwh_hab", "vidre_hab",
    "rtc_per_1000hab",
}


def _num(v: Any) -> Any:
    """int/float net per a JSON, o None si NaN. Enters sense .0 (diff estable)."""
    if v is None or pd.isna(v):
        return None
    f = float(v)
    return int(f) if f.is_integer() else f


def _txt(v: Any) -> Any:
    return None if v is None or pd.isna(v) else str(v)


def scope_ine5() -> dict[str, str]:
    """ine5 → comarca des de l'AUTORITAT territorial (data/web/municipis-territori.json),
    mai una llista fixa cablejada: el mateix criteri que fa servir mart_govern."""
    terr = json.loads(TERRITORI.read_text(encoding="utf-8"))
    out = {k: v.get("comarca") for k, v in terr.items()}
    if SCOPE_COMARCA is not None:
        out = {k: c for k, c in out.items() if c == SCOPE_COMARCA}
    return out


def frescor_atur(contract: dict) -> dict[str, Any]:
    """Frescor de l'atur des del contracte (E5). No es dedueix del parquet: el contracte
    és la font de veritat de la cadència i del procés que la manté."""
    spec = contract["metrics"]["atur_registrat"]
    src = contract["sources"][spec["source"]]
    return {
        "actualitzacio": spec.get("actualitzacio") or src.get("actualitzacio"),
        "darrera_carrega": src.get("darrera_carrega"),
        "proces_refresc": src.get("proces_refresc"),
        "font_frescor": spec["source"],
        "date": str(spec.get("date")) if spec.get("date") else None,
    }


def build_atur(pols: pd.DataFrame, ine5s: set[str]) -> tuple[dict[str, dict], str]:
    """Darrer mes + sèrie recent per municipi, amb la doctrina del «<5» intacta."""
    pols = pols[pols["ine5"].isin(ine5s)]
    darrer_mes = str(pols["date"].max())
    mesos = sorted(pols["date"].unique())[-MESOS_SERIE:]
    pols = pols[pols["date"].isin(mesos)].sort_values(["ine5", "date"])

    out: dict[str, dict] = {}
    for ine5, g in pols.groupby("ine5", sort=True):
        punts = [
            {
                # valor null + interval + flag: MAI un zero on la font deia «<5».
                "date": str(r.date),
                "valor": _num(r.atur_registrat),
                "min": int(r.atur_registrat_min),
                "max": int(r.atur_registrat_max),
                "emmascarat": bool(r.atur_emmascarat),
            }
            for r in g.itertuples(index=False)
        ]
        ultim = next((p for p in reversed(punts) if p["date"] == darrer_mes), None)
        out[str(ine5)] = {"darrer": ultim, "serie": punts}
    return out, darrer_mes


def build_tendencia(tend: pd.DataFrame, ine5s: set[str]) -> dict[str, dict]:
    """`{ine5: {metric: [entrada, …]}}`. LLISTA per mètrica perquè l'atur en té DUES
    (mes anterior i mateix mes de l'any anterior) i el front les ha de poder pintar
    totes dues: ensenyar-ne només una seria triar la narrativa."""
    tend = tend[tend["ine5"].isin(ine5s)].sort_values(["ine5", "metric", "comparacio"])
    out: dict[str, dict[str, list]] = {}
    for r in tend.itertuples(index=False):
        entry = out.setdefault(str(r.ine5), {})
        entry.setdefault(str(r.metric), []).append({
            "estat": str(r.estat),
            "comparacio": _txt(r.comparacio),
            "motiu": _txt(r.motiu),
            "periode_actual": _txt(r.periode_actual),
            "periode_anterior": _txt(r.periode_anterior),
            "valor_actual": _num(r.valor_actual),
            "valor_anterior": _num(r.valor_anterior),
            "delta": _num(r.delta),
            "delta_min": _num(r.delta_min),
            "delta_max": _num(r.delta_max),
            "delta_emmascarat": bool(r.delta_emmascarat),
            "unitat_delta": _txt(r.unitat_delta),
            "direccio": _txt(r.direccio),
        })
    return {k: {m: out[k][m] for m in sorted(out[k])} for k in sorted(out)}


def invariants(payload: dict) -> list[str]:
    """Les regles d'honestedat del §2/§3 de les esmenes, comprovades sobre la sortida
    REAL abans d'escriure-la. Si alguna falla, no s'escriu res: val més un export que
    peta que un tauler que menteix."""
    errs: list[str] = []
    for ine5, muni in payload["municipis"].items():
        for punt in muni["atur"]["serie"]:
            if punt["emmascarat"] and punt["valor"] is not None:
                errs.append(f"{ine5} {punt['date']}: emmascarat amb valor exacte")
            if not punt["emmascarat"] and punt["valor"] is None:
                errs.append(f"{ine5} {punt['date']}: valor buit sense marca d'emmascarament")
            if punt["emmascarat"] and (punt["min"], punt["max"]) != (1, 4):
                errs.append(f"{ine5} {punt['date']}: emmascarat amb interval {punt['min']}-{punt['max']} (s'esperava 1-4)")
            if punt["valor"] == 0 and punt["emmascarat"]:
                errs.append(f"{ine5} {punt['date']}: zero on la font deia «<5»")
        for metric, entrades in muni["tendencia"].items():
            for e in entrades:
                # Regla de ferro de Bea: cap fletxa sense període.
                if e["direccio"] is not None and not e["periode_anterior"]:
                    errs.append(f"{ine5}/{metric}: direcció «{e['direccio']}» sense període de comparació")
                if e["delta"] is not None and not e["periode_anterior"]:
                    errs.append(f"{ine5}/{metric}: delta sense període de comparació")
                if e["estat"] == "sense_serie":
                    if e["delta"] is not None:
                        errs.append(f"{ine5}/{metric}: 'sense_serie' amb delta")
                    if not e["motiu"]:
                        errs.append(f"{ine5}/{metric}: 'sense_serie' sense motiu escrit")
                if e["delta_emmascarat"] and e["delta"] is not None:
                    errs.append(f"{ine5}/{metric}: delta exacte sobre un punt emmascarat")
    return errs


def build() -> dict:
    contract = yaml.safe_load(METRICS_YML.read_text(encoding="utf-8"))
    comarques = scope_ine5()
    ine5s = set(comarques)

    pols = pd.read_parquet(MART_POLS)
    tend = pd.read_parquet(MART_TEND)

    falten = TEND_METRICS_ESPERADES - set(tend["metric"].unique())
    if falten:
        raise SystemExit(f"FALLA: mart_tendencia no porta {sorted(falten)}")

    atur, darrer_mes = build_atur(pols, ine5s)
    tendencia = build_tendencia(tend, ine5s)

    noms = (
        pols[pols["ine5"].isin(ine5s)]
        .drop_duplicates("ine5")
        .set_index("ine5")[["municipi", "codi6"]]
    )

    municipis: dict[str, dict] = {}
    for ine5 in sorted(ine5s):
        if ine5 not in atur and ine5 not in tendencia:
            continue
        municipis[ine5] = {
            "ine5": ine5,
            "nom": str(noms.loc[ine5, "municipi"]) if ine5 in noms.index else None,
            "idescat6": str(noms.loc[ine5, "codi6"]) if ine5 in noms.index else None,
            "comarca": comarques[ine5],
            "atur": atur.get(ine5, {"darrer": None, "serie": []}),
            "tendencia": tendencia.get(ine5, {}),
        }

    return {
        "contractVersion": str(contract["meta"]["version"]),
        "abast": SCOPE_COMARCA or "Catalunya",
        "_meta": {
            "atur": {
                "darrer_mes": darrer_mes,
                "mesos_serie": MESOS_SERIE,
                "frescor": frescor_atur(contract),
                "doctrina_menys_de_5": (
                    "Des de gener de 2022 el SEPE emmascara els valors 1-4 com a «<5». "
                    "Aquests mesos surten amb valor null + min/max = [1,4] + emmascarat "
                    "true, MAI zero. Un delta que toqui un mes emmascarat és un interval "
                    "(delta null + delta_min/delta_max), no un número."
                ),
            },
            "tendencia": {
                "regla": (
                    "Cap fletxa sense període: tota entrada amb direcció diu contra quin "
                    "període compara. Les mètriques sense sèrie hi són EXPLÍCITES amb "
                    "estat 'sense_serie' i el motiu escrit — no s'ometen, perquè una "
                    "absència es llegeix com un zero i un 'sense_serie' no."
                ),
                "fonts": ["mart_tendencia.parquet"],
            },
        },
        "municipis": municipis,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="export_tauler_web")
    ap.add_argument("--check", action="store_true",
                    help="no escriu; falla (codi 1) si el JSON al disc no coincideix")
    args = ap.parse_args(argv)

    for p in (MART_POLS, MART_TEND, TERRITORI, METRICS_YML):
        if not p.exists():
            print(f"FALLA: no existeix {p} (executa abans el pipeline transform)", file=sys.stderr)
            return 2

    payload = build()
    errs = invariants(payload)
    if errs:
        print(f"FALLA: {len(errs)} invariants d'honestedat trencades:", file=sys.stderr)
        for e in errs[:10]:
            print(f"  · {e}", file=sys.stderr)
        return 1

    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"FALLA (--check): no existeix {OUT} (executa'l sense --check)", file=sys.stderr)
            return 1
        with OUT.open("r", encoding="utf-8", newline="") as fh:
            on_disk = fh.read()
        if on_disk != text:
            print(f"FALLA (--check): {OUT.name} està estale — regenera'l "
                  f"(python tools/export_tauler_web.py)", file=sys.stderr)
            return 1
        print(f"OK (--check): {OUT.name} al dia ({len(payload['municipis'])} municipis, "
              f"darrer mes d'atur {payload['_meta']['atur']['darrer_mes']}).")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    n_tend = sum(len(v) for m in payload["municipis"].values() for v in m["tendencia"].values())
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {len(payload['municipis'])} municipis "
          f"· atur fins {payload['_meta']['atur']['darrer_mes']} ({MESOS_SERIE} mesos) "
          f"· {n_tend} entrades de tendència · {OUT.stat().st_size / 1024:.1f} kB.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
