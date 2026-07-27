#!/usr/bin/env python3
"""Export web del tauler v2 → l'ATUR i la TENDÈNCIA servibles (E4 + E6 + E5).

El forat que tapa: `mart_pols_mensual` porta la sèrie mensual d'atur dels 947 municipis
des de 2006 (224.439 files) i `mart_tendencia` porta la tendència amb el seu període, però
**cap dels dos era servible al web**: el tauler no pot llegir un parquet. És el mateix
forat que D4 va deixar amb `mart_govern` i que #272 va haver de tapar després — aquí
l'export neix amb `--check` i CABLAT AL CI el mateix dia, no en un PR posterior.

ABAST (P-947, 2026-07-27): s'emeten DUES formes, cadascuna amb el seu `--check`:
  · `tauler.bergueda.json` — MONÒLIT dels 31 del Berguedà (RETROCOMPATIBILITAT: el
    prebuild `copy-data.mjs` i el verificador `verify-govern.mjs` de Mirador encara hi
    depenen; no es toca fins que Mirador migri a l'abast 947).
  · `data/web/tauler/<ine5>.json` — UN FITXER PER MUNICIPI (947) + `data/web/tauler/_meta.json`.
    DECISIÓ D'ARQUITECTURA amb el número a la mà: el monòlit a 947 faria ~17 MB compacte
    (~24 MB indentat) que la fitxa carregaria SENCER per pintar UN municipi — inacceptable
    al navegador. Partit per municipi, cada fitxa només llegeix el SEU shard (~19 kB) + el
    `_meta` compartit (~1 kB). És el mateix patró que `copy-data.mjs` ja fa amb
    `municipis.catalunya.json` → `static/data/muni/<ine5>.json`, però resolt A L'ORIGEN
    (data/web) perquè el repo no carregui mai el monòlit. El `_meta` (frescor + doctrina del
    «<5» + darrer mes) és compartit i va al sidecar; els shards només porten el municipi.

Per què un fitxer separat del dataset (`municipis.*.json`):
  · CADÈNCIA DIFERENT. L'atur es refresca cada MES (refresh-atur.yml); la resta del
    tauler, un cop l'any o menys.
  · FORMA DIFERENT: una sèrie temporal no cap a `values: {clau: número}`.

Frontera honesta (aquí NO es calcula res que no vingui dels marts):
  · L'atur es re-serialitza de `mart_pols_mensual` tal com hi és.
  · La tendència ve SENCERA de `mart_tendencia` (deltes, períodes, estat, motiu EN ELS
    DOS IDIOMES): aquest fitxer no resta cap parell de números ni tradueix cap text.
  · QUINES mètriques hi ha d'haver es deriva de la composició del tauler
    (`tools/tauler_kpis.py` → `packages/web/src/lib/govern/kpis.js`), mai d'una llista
    escrita aquí: dues llistes a mà divergeixen, i divergeixen en silenci (D10).
  · La DOCTRINA DEL «<5» (C1 §1.1) es propaga literalment: un mes emmascarat surt amb
    `valor: null` + `min`/`max` (l'interval [1,4]) + `emmascarat: true`. MAI zero.

GUARDA ANTI-FUITA (P-947): cap mètrica `dimension: politica` / `source: electoral` (res de
`mart_electoral`) pot entrar en aquest export. mart_tendencia només porta mètriques segures
(atur, edat, origen, residus…); la guarda ho ASSERTA a cada execució llegint el contracte.

Ús:
    python tools/export_tauler_web.py            # (re)genera monòlit + shards (31 + 947)
    python tools/export_tauler_web.py --check    # falla si algun artefacte versionat és estale

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

from tauler_kpis import metriques_del_tauler

REPO = Path(__file__).resolve().parents[1]
MART_POLS = REPO / "data" / "marts" / "mart_pols_mensual.parquet"
MART_TEND = REPO / "data" / "marts" / "mart_tendencia.parquet"
TERRITORI = REPO / "data" / "web" / "municipis-territori.json"
METRICS_YML = REPO / "semantic" / "metrics.yml"
OUT_BERGUEDA = REPO / "data" / "web" / "tauler.bergueda.json"
# Abast 947: un fitxer per municipi + un sidecar de metadades compartides.
TAULER_DIR = REPO / "data" / "web" / "tauler"
META_NAME = "_meta.json"

# Mesos de sèrie que s'emeten (comptant el darrer). 25 = el darrer mes + 24 enrere:
# el mínim que permet al front pintar dos anys sencers I ensenyar el mateix mes de
# l'any anterior sense una segona petició. La sèrie completa (2006→) es queda al mart:
# servir 20 anys × 947 municipis al navegador seria pes sense lectura.
MESOS_SERIE = 25


def forbidden_metric_keys(contract: dict) -> set[str]:
    """Claus de mètrica de la capa de VOT que no poden sortir mai al web: qualsevol de
    ``dimension: politica`` o ``source: electoral`` o ``table: mart_electoral``. Derivat del
    contracte (no una llista a mà) perquè una mètrica nova d'aquestes la culli sola."""
    forbidden: set[str] = set()
    for key, spec in contract.get("metrics", {}).items():
        if (
            spec.get("dimension") == "politica"
            or spec.get("source") == "electoral"
            or spec.get("table") == "mart_electoral"
        ):
            forbidden.add(key)
    return forbidden


def emitted_metrics(payload: dict) -> set[str]:
    """Claus de mètrica que aquest payload serveix (les de tendència; l'atur és una sola
    mètrica segura, `atur_registrat`, i va a part)."""
    keys: set[str] = set()
    for muni in payload["municipis"].values():
        keys |= set(muni["tendencia"].keys())
    return keys


def assert_no_electoral(payload: dict, forbidden: set[str], label: str) -> None:
    """GUARDA ANTI-FUITA: peta l'export (write O --check) si el tauler servís cap mètrica
    de la capa de vot. Font: el contracte."""
    leak = emitted_metrics(payload) & forbidden
    if leak:
        raise SystemExit(
            f"FUITA ELECTORAL: {label} contindria mètriques de la capa de vot "
            f"{sorted(leak)} (dimension: politica / source: electoral). El tauler només "
            f"pot servir mètriques segures; revisa mart_tendencia i el contracte."
        )


def _num(v: Any) -> Any:
    """int/float net per a JSON, o None si NaN. Enters sense .0 (diff estable)."""
    if v is None or pd.isna(v):
        return None
    f = float(v)
    return int(f) if f.is_integer() else f


def _txt(v: Any) -> Any:
    return None if v is None or pd.isna(v) else str(v)


def scope_ine5(scope: str | None) -> dict[str, str]:
    """ine5 → comarca des de l'AUTORITAT territorial (data/web/municipis-territori.json),
    mai una llista fixa cablejada: el mateix criteri que fa servir mart_govern. ``scope`` =
    nom de comarca a filtrar, o None per a tots els municipis (947)."""
    terr = json.loads(TERRITORI.read_text(encoding="utf-8"))
    out = {k: v.get("comarca") for k, v in terr.items()}
    if scope is not None:
        out = {k: c for k, c in out.items() if c == scope}
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
        motiu_ca, motiu_es = _txt(r.motiu_ca), _txt(r.motiu_es)
        entry.setdefault(str(r.metric), []).append({
            "estat": str(r.estat),
            "comparacio": _txt(r.comparacio),
            # `motiu` (ca) es manté MENTRE Mirador llegeix `{e.motiu}` amb lang="ca" cablat:
            # canviar-lo a objecte avui pintaria «[object Object]» en producció, i el web és
            # viu. `motiu_l10n` és la forma bona —{ca,es}, com `label`/`definicio` al
            # contracte— i el mart ja les serveix totes dues.
            # ➡️ Handoff a Mirador: `pick(e.motiu_l10n, locale)` + fora el lang="ca". Quan
            # hi sigui, aquesta línia (i el camp pla) desapareixen.
            "motiu": motiu_ca,
            "motiu_l10n": {"ca": motiu_ca, "es": motiu_es} if motiu_ca or motiu_es else None,
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
                    # El motiu és l'ÚNICA cosa que la targeta pot dir quan no hi ha fletxa:
                    # si falta una llengua, el lector d'aquella llengua es queda sense res.
                    l10n = e["motiu_l10n"] or {}
                    for lang in ("ca", "es"):
                        if not l10n.get(lang):
                            errs.append(f"{ine5}/{metric}: 'sense_serie' sense motiu en [{lang}]")
                if e["delta_emmascarat"] and e["delta"] is not None:
                    errs.append(f"{ine5}/{metric}: delta exacte sobre un punt emmascarat")
    return errs


def build(scope: str | None) -> dict:
    """Payload complet del tauler per a un abast. ``scope`` = comarca o None (947)."""
    contract = yaml.safe_load(METRICS_YML.read_text(encoding="utf-8"))
    comarques = scope_ine5(scope)
    ine5s = set(comarques)

    pols = pd.read_parquet(MART_POLS)
    tend = pd.read_parquet(MART_TEND)

    falten = metriques_del_tauler(REPO) - set(tend["metric"].unique())
    if falten:
        raise SystemExit(
            f"FALLA: el tauler pinta {sorted(falten)} i mart_tendencia no en porta cap fila. "
            f"Una targeta sense fila calla, i callar es llegeix com «no ha canviat»: afegeix-les "
            f"al mart amb estat 'sense_serie' i el motiu escrit (mart_tendencia.sql, CTE `sense`)."
        )

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
        "abast": scope or "Catalunya",
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
                    "absència es llegeix com un zero i un 'sense_serie' no. Quines "
                    "mètriques hi han de ser es deriva de la composició del tauler, no "
                    "d'una llista a mà: si el tauler pinta una targeta sense fila aquí, "
                    "aquest export falla."
                ),
                "motiu": (
                    "El motiu és DADA i ve del mart en ca i es (`motiu_l10n`); el front el "
                    "pinta literal i traduir-lo allà seria inventar-se'l. El camp pla "
                    "`motiu` (català) és transitori i desapareixerà quan el web llegeixi "
                    "`motiu_l10n`."
                ),
                "fonts": ["mart_tendencia.parquet"],
            },
        },
        "municipis": municipis,
    }


def render_monolith(payload: dict) -> str:
    """Monòlit del Berguedà (retrocompatibilitat): mateixa forma indentada de sempre,
    per no moure ni un byte del que Mirador (`copy-data.mjs`, `verify-govern.mjs`) llegeix."""
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def shard_files(payload: dict) -> dict[str, str]:
    """Abast 947 partit: `{nom_de_fitxer: text}`. `_meta.json` = tot menys `municipis`
    (compartit, indentat i llegible); un fitxer COMPACTE per municipi amb el seu payload."""
    files: dict[str, str] = {}
    meta = {k: v for k, v in payload.items() if k != "municipis"}
    files[META_NAME] = json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    for ine5, row in payload["municipis"].items():
        # Compacte (com el split de `municipis.catalunya.json` a copy-data.mjs): els shards
        # els llegeix el navegador, no un humà. sort_keys → forma canònica i diff estable.
        files[f"{ine5}.json"] = (
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        )
    return files


def _read_lf(path: Path) -> str:
    """Llegeix sense traduir finals de línia (comparació byte-estable; eol=lf)."""
    with path.open("r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def check_shards(files: dict[str, str]) -> list[str]:
    """Compara el directori 947 amb el conjunt esperat: detecta shards estale, absents I
    ESTRANYS (un municipi retirat deixaria un fitxer orfe que es llegiria com a dada viva)."""
    errs: list[str] = []
    if not TAULER_DIR.exists():
        return [f"no existeix {TAULER_DIR}/ (executa'l sense --check)"]
    actual = {p.name for p in TAULER_DIR.glob("*.json")}
    expected = set(files)
    for name in sorted(expected - actual):
        errs.append(f"tauler/{name}: absent")
    for name in sorted(actual - expected):
        errs.append(f"tauler/{name}: estrany (no correspon a cap municipi de l'abast)")
    for name in sorted(expected & actual):
        if _read_lf(TAULER_DIR / name) != files[name]:
            errs.append(f"tauler/{name}: estale")
    return errs


def write_shards(files: dict[str, str]) -> None:
    """Escriu els 947 shards + `_meta.json` i ESBORRA els `*.json` orfes (municipi retirat)
    perquè el directori sigui exactament el conjunt esperat (i el --check hi casi)."""
    TAULER_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        _write_lf(TAULER_DIR / name, text)
    expected = set(files)
    for p in TAULER_DIR.glob("*.json"):
        if p.name not in expected:
            p.unlink()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="export_tauler_web")
    ap.add_argument("--check", action="store_true",
                    help="no escriu; falla (codi 1) si algun artefacte al disc no coincideix")
    args = ap.parse_args(argv)

    for p in (MART_POLS, MART_TEND, TERRITORI, METRICS_YML):
        if not p.exists():
            print(f"FALLA: no existeix {p} (executa abans el pipeline transform)", file=sys.stderr)
            return 2

    contract = yaml.safe_load(METRICS_YML.read_text(encoding="utf-8"))
    forbidden = forbidden_metric_keys(contract)

    # Berguedà (monòlit, retrocompatibilitat) + Catalunya (shards). Construïm i validem els
    # DOS abans de tocar el disc: invariants d'honestedat + guarda anti-fuita a cadascun.
    berg = build("Berguedà")
    if errs := invariants(berg):
        _report(errs, "tauler.bergueda")
        return 1
    assert_no_electoral(berg, forbidden, OUT_BERGUEDA.name)
    berg_text = render_monolith(berg)

    cat = build(None)
    if errs := invariants(cat):
        _report(errs, "tauler/ (947)")
        return 1
    assert_no_electoral(cat, forbidden, "tauler/<ine5>.json")
    files = shard_files(cat)

    if args.check:
        stale: list[str] = []
        if not OUT_BERGUEDA.exists():
            print(f"FALLA (--check): no existeix {OUT_BERGUEDA} (executa'l sense --check)", file=sys.stderr)
            return 1
        if _read_lf(OUT_BERGUEDA) != berg_text:
            stale.append(f"{OUT_BERGUEDA.name}: estale")
        stale.extend(check_shards(files))
        if stale:
            print(f"FALLA (--check): {len(stale)} artefactes del tauler estale/absents/estranys — "
                  f"regenera'l (python tools/export_tauler_web.py):", file=sys.stderr)
            for e in stale[:10]:
                print(f"  · {e}", file=sys.stderr)
            if len(stale) > 10:
                print(f"  · … i {len(stale) - 10} més", file=sys.stderr)
            return 1
        print(f"OK (--check): tauler al dia — {OUT_BERGUEDA.name} ({len(berg['municipis'])} munis) "
              f"+ tauler/ ({len(cat['municipis'])} munis + _meta), darrer mes d'atur "
              f"{cat['_meta']['atur']['darrer_mes']}.")
        return 0

    _write_lf(OUT_BERGUEDA, berg_text)
    write_shards(files)
    berg_kb = OUT_BERGUEDA.stat().st_size / 1024
    shard_total = sum((TAULER_DIR / n).stat().st_size for n in files) / 1048576
    print(f"Escrit {OUT_BERGUEDA.relative_to(REPO).as_posix()} ({len(berg['municipis'])} munis, "
          f"{berg_kb:.1f} kB) + data/web/tauler/ ({len(cat['municipis'])} shards + _meta, "
          f"{shard_total:.1f} MB) · atur fins {cat['_meta']['atur']['darrer_mes']} ({MESOS_SERIE} mesos).")
    return 0


def _report(errs: list[str], label: str) -> None:
    print(f"FALLA: {len(errs)} invariants d'honestedat trencades a {label}:", file=sys.stderr)
    for e in errs[:10]:
        print(f"  · {e}", file=sys.stderr)
    if len(errs) > 10:
        print(f"  · … i {len(errs) - 10} més", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
