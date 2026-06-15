#!/usr/bin/env python3
"""Nivell C · anàlisi exploratòria: error del model base (Berguedà) per tipus territorial.

Pas següent de l'stress-test (`stress_test_escala.py`): aquell només contrastava l'ETCA amb
el tipus territorial; aquí AFEGIM els SENYALS (elèctric ICAEN + residus ARC) i l'estimació del
model de 3 capes amb les BASES ENDÒGENES del Berguedà (elèctric 1.224 kWh/hab, residus 410
kg/hab), i mesurem QUANT s'equivoca per `tipus_territorial` contra l'ETCA oficial. És l'input
empíric per calibrar el Nivell C (esperats per tipus): si el litoral es dobla i el metro baixa,
ho veurem en xifres d'error per tipus.

Model (macro `estimacio_presencia`): presència = padró × (senyal/hab) / BASE.
  · L1 pernocta  = padró × kwh_hab / base_electric      = consum_kwh_domèstic / base_electric
  · L2 càrrega   = padró × kg_hab_any / base_residencial
Comparació: error_pernocta% = (pernocta_est − ETCA) / ETCA × 100, agregat per tipus (mediana +
Spearman ρ). Go/no-go per tipus: ρ≥0,7 i |error medià|≤15% (decisió Bea 2026-06-11).

Carril dades EN SILENCI: artefacte INTERN (no publicat). Baixa en viu (Socrata + Idescat).
Sortida: `data/territorial/nivellc_analisi.csv` + resum per tipus a stdout.

Ús:  python tools/nivellc_analisi.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tipus_territorial import classify  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "territorial" / "nivellc_analisi.csv"

# Bases endògenes del Berguedà (dbt vars base_electric / base_residencial). El Nivell C les
# substituirà per esperats per tipus; aquí les usem com a BASE ÚNICA per mesurar-ne el biaix.
BASE_ELECTRIC = 1224.0
BASE_RESIDENCIAL = 410.0
GO_RHO, GO_ERR = 0.7, 15.0  # go/no-go per tipus

ICAEN_URL = "https://analisi.transparenciacatalunya.cat/resource/8idm-becu.json"
ARC_URL = "https://analisi.transparenciacatalunya.cat/resource/69zu-w48s.json"

# Mateix lot que l'stress-test (Barcelonès metro + Tarragonès litoral): tipus i ETCA ja
# verificats. codi6 Idescat → nom.
MUNIS = {
    "080193": "Barcelona",
    "081017": "l'Hospitalet de Llobregat",
    "080155": "Badalona",
    "082457": "Santa Coloma de Gramenet",
    "081944": "Sant Adrià de Besòs",
    "439057": "Salou",
    "431482": "Tarragona",
    "430385": "Cambrils",
    "431711": "Vila-seca",
}


def _num(s):
    s = str(s if s is not None else "").replace(".", "").replace(",", ".").strip()
    return None if s in ("", "..", "(..)", "_", "-") else float(s)


def _socrata(url: str, where: str, select: str, limit: int = 50000) -> list[dict]:
    q = urllib.parse.urlencode({"$where": where, "$select": select, "$limit": limit})
    req = urllib.request.Request(f"{url}?{q}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def fetch_etca() -> dict[str, dict]:
    """ETCA/EPE Idescat (SSV, base 2021 n=17886): resident + població estacional ETCA."""
    url = "https://www.idescat.cat/pub/?id=epe&n=17886&geo=mun&f=ssv"
    with urllib.request.urlopen(url, timeout=60) as r:
        text = r.read().decode("utf-8-sig")
    lines = text.splitlines()
    h = next(i for i, ln in enumerate(lines) if ln.startswith("Codi;"))
    out: dict[str, dict] = {}
    for row in csv.reader(io.StringIO("\n".join(lines[h:])), delimiter=";"):
        if len(row) >= 8 and row[0].strip() in MUNIS:
            out[row[0].strip()] = {"resident": _num(row[5]), "etca": _num(row[6])}
    return out


def fetch_emex(codi6: str) -> dict:
    """Altitud (f258) + densitat (f262) d'Idescat EMEX (per classificar el tipus)."""
    url = f"https://api.idescat.cat/emex/v1/dades.json?id={codi6}"
    with urllib.request.urlopen(url, timeout=40) as r:
        d = json.load(r)

    def leaves(n):
        if isinstance(n, dict):
            if "id" in n and "v" in n:
                yield n
            for v in n.values():
                yield from leaves(v)
        elif isinstance(n, list):
            for x in n:
                yield from leaves(x)

    def emex_num(v):
        first = str(v).split(",")[0].strip()
        try:
            return float(first) if first not in ("", "_", "-") else None
        except ValueError:
            return None

    vals: dict[str, float | None] = {}
    for lf in leaves(d):
        if lf.get("id") in ("f258", "f262") and lf["id"] not in vals:
            vals[lf["id"]] = emex_num(lf.get("v"))
    return {"altitud": vals.get("f258"), "densitat": vals.get("f262")}


def fetch_electric() -> dict[str, float]:
    """Consum elèctric domèstic (sector 7) de l'any més recent, per ine5 (ICAEN 8idm-becu)."""
    ine5s = sorted({c[:5] for c in MUNIS})
    where = "codi_sector='7' and cdmun in (" + ",".join(f"'{i}'" for i in ine5s) + ")"
    rows = _socrata(ICAEN_URL, where, "cdmun,any,consum_kwh")
    latest: dict[str, tuple[int, float]] = {}
    for r in rows:
        ine5 = str(r.get("cdmun", "")).zfill(5)
        any_ = int(_num(r.get("any")) or 0)
        kwh = _num(r.get("consum_kwh"))
        if kwh is None:
            continue
        if ine5 not in latest or any_ > latest[ine5][0]:
            latest[ine5] = (any_, kwh)
    return {k: v[1] for k, v in latest.items()}


def fetch_residus() -> dict[str, dict]:
    """kg/hab/any + població de l'any més recent, per ine5 (ARC 69zu-w48s)."""
    codi6s = sorted(MUNIS)
    where = "codi_municipi in (" + ",".join(f"'{c}'" for c in codi6s) + ")"
    rows = _socrata(ARC_URL, where, "codi_municipi,any,kg_hab_any,poblaci")
    latest: dict[str, tuple[int, dict]] = {}
    for r in rows:
        ine5 = str(r.get("codi_municipi", "")).zfill(6)[:5]
        any_ = int(_num(r.get("any")) or 0)
        kg = _num(r.get("kg_hab_any"))
        if kg is None:
            continue
        if ine5 not in latest or any_ > latest[ine5][0]:
            latest[ine5] = (any_, {"kg_hab_any": kg, "poblacio_arc": _num(r.get("poblaci"))})
    return {k: v[1] for k, v in latest.items()}


def _spearman(pairs: list[tuple[float, float]]) -> float | None:
    """Spearman ρ sense numpy: correlació de Pearson sobre els rangs."""
    n = len(pairs)
    if n < 3:
        return None

    def ranks(vals):
        order = sorted(range(n), key=lambda i: vals[i])
        rk = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                rk[order[k]] = avg
            i = j + 1
        return rk

    xs = ranks([p[0] for p in pairs])
    ys = ranks([p[1] for p in pairs])
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    dx = sum((xs[i] - mx) ** 2 for i in range(n)) ** 0.5
    dy = sum((ys[i] - my) ** 2 for i in range(n)) ** 0.5
    return None if dx == 0 or dy == 0 else num / (dx * dy)


def _median(xs: list[float]) -> float | None:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def main() -> int:
    try:  # consola Windows (cp1252) → força UTF-8 per als rètols (ρ, →, accents)
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("Baixant ETCA + senyals (ICAEN/ARC) + EMEX…")
    etca = fetch_etca()
    electric = fetch_electric()
    residus = fetch_residus()

    rows = []
    for codi6, nom in MUNIS.items():
        ine5 = codi6[:5]
        em = fetch_emex(codi6)
        e = etca.get(codi6, {})
        resident = e.get("resident")
        etca_v = e.get("etca")
        kwh_dom = electric.get(ine5)
        res = residus.get(ine5, {})
        kg_hab = res.get("kg_hab_any")

        # Model base Berguedà. Pernocta: el padró es cancel·la (kwh/hab × padró = kwh_total).
        pernocta_est = round(kwh_dom / BASE_ELECTRIC) if kwh_dom else None
        carrega_est = (
            round((kg_hab * resident) / BASE_RESIDENCIAL) if (kg_hab and resident) else None
        )
        err_pernocta = (
            round((pernocta_est - etca_v) / etca_v * 100, 1)
            if (pernocta_est and etca_v) else None
        )
        rows.append({
            "ine5": ine5, "municipi": nom,
            "tipus_territorial": classify(ine5, em["altitud"], em["densitat"]),
            "resident": int(resident) if resident else None,
            "etca": int(etca_v) if etca_v else None,
            "kwh_dom_total": int(kwh_dom) if kwh_dom else None,
            "kg_hab_any": kg_hab,
            "pernocta_est": pernocta_est,
            "carrega_est": carrega_est,
            "err_pernocta_pct": err_pernocta,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nEscrit {OUT.relative_to(REPO).as_posix()} · {len(rows)} munis\n")

    # Per municipi
    print(f"{'municipi':28} {'tipus':22} {'ETCA':>7} {'pernocta':>9} {'err%':>7}")
    for r in rows:
        print(f"  {r['municipi']:26} {r['tipus_territorial']:22} {str(r['etca'] or '—'):>7} "
              f"{str(r['pernocta_est'] or '—'):>9} {str(r['err_pernocta_pct'] or '—'):>7}")

    # Per tipus territorial: go/no-go amb la base ÚNICA
    print("\nPer tipus territorial (base única Berguedà → error vs ETCA):")
    tipus: dict[str, list[dict]] = {}
    for r in rows:
        tipus.setdefault(r["tipus_territorial"], []).append(r)
    for t, rs in sorted(tipus.items()):
        errs = [r["err_pernocta_pct"] for r in rs if r["err_pernocta_pct"] is not None]
        pairs = [(float(r["pernocta_est"]), float(r["etca"])) for r in rs
                 if r["pernocta_est"] and r["etca"]]
        med = _median([abs(x) for x in errs]) if errs else None
        rho = _spearman(pairs)
        verdict = ("—" if med is None or rho is None
                   else "GO" if (abs(rho) >= GO_RHO and med <= GO_ERR) else "NO-GO")
        print(f"  {t:22} n={len(rs):2}  err_medià={_fmt(med)}%  ρ={_fmt(rho)}  → {verdict}")

    # RECALIBRACIÓ RÀPIDA (provisional, N petita): base per tipus = base_electric / factor,
    # on factor = mediana(ETCA / pernocta_est). Residual = error que queda DESPRÉS de centrar.
    # Criteri honest amb base per tipus: el residual MÀXIM ≤ 15% (que cap muni del tipus se'n
    # vagi), no només la mediana (que per construcció va a ~0).
    print("\nRecalibració ràpida — base per tipus (provisional, N petita):")
    base_rows = []
    for t, rs in sorted(tipus.items()):
        ratios = [r["etca"] / r["pernocta_est"] for r in rs if r["pernocta_est"] and r["etca"]]
        if not ratios:
            continue
        factor = _median(ratios)
        base_t = round(BASE_ELECTRIC / factor)
        resid = [abs((r["pernocta_est"] * factor - r["etca"]) / r["etca"] * 100)
                 for r in rs if r["pernocta_est"] and r["etca"]]
        med_res, max_res = _median(resid), max(resid)
        verdict = "GO" if max_res <= GO_ERR else "NO-GO"
        base_rows.append({"tipus_territorial": t, "n": len(ratios),
                          "base_electric_tipus": base_t, "factor": round(factor, 3),
                          "residual_medianpct": round(med_res, 1) if med_res is not None else "",
                          "residual_maxpct": round(max_res, 1), "go_nogo": verdict})
        print(f"  {t:22} base={base_t:5} (×{factor:.2f})  residual medià={_fmt(med_res)}% "
              f"màx={_fmt(max_res)}%  → {verdict}")

    base_out = OUT.parent / "nivellc_bases_tipus.csv"
    with base_out.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(base_rows[0].keys()))
        w.writeheader()
        w.writerows(base_rows)
    print(f"\nBases per tipus → {base_out.relative_to(REPO).as_posix()} (provisional, intern)")
    print("Nota: base ÚNICA Berguedà = 1224. Comparació de referència, no publicat.")
    return 0


def _fmt(x):
    return "—" if x is None else f"{x:.2f}"


if __name__ == "__main__":
    raise SystemExit(main())
