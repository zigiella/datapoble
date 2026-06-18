#!/usr/bin/env python3
"""Nivell C · anàlisi exploratòria de l'error del model base per tipus territorial (escala).

DIRIGIT PER COMARCA: baixa en viu els senyals (elèctric ICAEN `8idm-becu` sector 7 + residus
ARC `69zu-w48s`) de les comarques configurades — els municipis i els codis surten de les DADES,
no d'una llista a mà. Per a cada muni hi afegeix l'estimació del model de 3 capes amb les bases
endògenes del Berguedà i mesura l'error vs l'ETCA oficial, agregat per `tipus_territorial`.

Model (macro `estimacio_presencia`): presència = padró × (senyal/hab) / BASE.
  · L1 pernocta = padró × kwh_hab / base_electric = consum_kwh_domèstic / base_electric
Recalibració ràpida: base/tipus = base_electric / mediana(ETCA/pernocta_est); residual = error
després de centrar (criteri honest: màx ≤15%). Covariable d'estacionalitat: RTC places/resident
(`t2h3-cgys`) — per veure si explica el residual del litoral vacacional.

Carril dades EN SILENCI: artefactes INTERNS (no publicats). Sortida:
`data/territorial/nivellc_analisi.csv` + `nivellc_bases_tipus.csv` + resum a stdout.

Ús:  python tools/nivellc_analisi.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "territorial" / "nivellc_analisi.csv"

BASE_ELECTRIC = 1224.0
GO_RHO, GO_ERR = 0.7, 15.0
DENSITAT_METRO = 1500.0
ALTITUD_PIRINEU = 800.0

ICAEN_URL = "https://analisi.transparenciacatalunya.cat/resource/8idm-becu.json"
GAS_URL = "https://analisi.transparenciacatalunya.cat/resource/qvqg-zag8.json"  # gas natural municipal
ARC_URL = "https://analisi.transparenciacatalunya.cat/resource/69zu-w48s.json"
RTC_URL = "https://analisi.transparenciacatalunya.cat/resource/t2h3-cgys.json"

# Comarques a analitzar (nom de visualització). Berguedà = baseline (base endògena → factor ~1,0,
# sanity check). Barcelonès+Tarragonès = lot inicial. Baix Llobregat (metro + costa AMB) i Maresme
# (costa vacacional) = ampliació per créixer N. «Poc a poc»: afegir-ne més en increments.
COMARQUES = ["Berguedà", "Barcelonès", "Tarragonès", "Baix Llobregat", "Maresme"]


def _norm(s: str) -> str:
    """Normalitza un nom de municipi per casar (sense accents, articles, minúscules)."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = s.replace("'", " ").replace("-", " ")
    parts = [p for p in s.split() if p not in {"el", "la", "els", "les", "l", "de", "del", "d"}]
    return " ".join(parts)


# Conjunts per NOM (verificables a ull). AMB = 36 municipis de l'Àrea Metropolitana de Barcelona.
AMB_NOMS = {_norm(x) for x in [
    "Badalona", "Badia del Vallès", "Barberà del Vallès", "Barcelona", "Begues", "Castellbisbal",
    "Castelldefels", "Cerdanyola del Vallès", "Cervelló", "Corbera de Llobregat",
    "Cornellà de Llobregat", "Esplugues de Llobregat", "Gavà", "l'Hospitalet de Llobregat",
    "Molins de Rei", "Montcada i Reixac", "Montgat", "Pallejà", "la Palma de Cervelló", "el Papiol",
    "el Prat de Llobregat", "Ripollet", "Sant Adrià de Besòs", "Sant Andreu de la Barca",
    "Sant Boi de Llobregat", "Sant Climent de Llobregat", "Sant Cugat del Vallès",
    "Sant Feliu de Llobregat", "Sant Joan Despí", "Sant Just Desvern", "Sant Vicenç dels Horts",
    "Santa Coloma de Cervelló", "Santa Coloma de Gramenet", "Tiana", "Torrelles de Llobregat",
    "Viladecans",
]}

# Costaners (toquen mar) de les comarques cobertes. Litoral_metropolita si també AMB, si no
# litoral_vacacional. Llista per nom: revisar amb la sortida per-muni (es marca el tipus).
COSTANERS_NOMS = {_norm(x) for x in [
    # Barcelonès + Baix Llobregat (AMB litoral)
    "Barcelona", "Badalona", "Sant Adrià de Besòs", "Montgat",
    "el Prat de Llobregat", "Viladecans", "Gavà", "Castelldefels",
    # Maresme (litoral, no AMB excepte Montgat)
    "el Masnou", "Premià de Mar", "Vilassar de Mar", "Cabrera de Mar", "Mataró",
    "Sant Andreu de Llavaneres", "Caldes d'Estrac", "Arenys de Mar", "Canet de Mar",
    "Sant Pol de Mar", "Calella", "Pineda de Mar", "Santa Susanna", "Malgrat de Mar",
    # Tarragonès litoral
    "Tarragona", "Salou", "Cambrils", "Vila-seca", "Torredembarra", "Altafulla", "Creixell",
    "Roda de Berà", "la Pobla de Montornès", "Vespella de Gaià",
]}

# ICAEN usa comarca en MAJÚSCULES sense accents; ARC, amb accents.
def _icaen_comarca(nom: str) -> str:
    return _norm(nom).upper().replace(" ", " ")  # _norm ja treu accents; recompon sense article


def _num(s):
    s = str(s if s is not None else "").replace(".", "").replace(",", ".").strip()
    return None if s in ("", "..", "(..)", "_", "-") else float(s)


def _socrata(url: str, where: str, select: str, limit: int = 100000) -> list[dict]:
    q = urllib.parse.urlencode({"$where": where, "$select": select, "$limit": limit})
    req = urllib.request.Request(f"{url}?{q}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def _icaen_norm(nom: str) -> str:
    """Comarca tal com la guarda ICAEN: majúscules, sense accents, amb article si en té."""
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode().upper()
    return s


def fetch_electric(comarques: list[str]) -> dict[str, float]:
    noms = [_icaen_norm(c) for c in comarques]
    where = "codi_sector='7' and comarca in (" + ",".join(f"'{n}'" for n in noms) + ")"
    rows = _socrata(ICAEN_URL, where, "cdmun,any,consum_kwh,comarca")
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


def fetch_gas(comarques: list[str]) -> dict[str, float]:
    """Consum de gas natural DOMÈSTIC (kWh PCS) de l'any més recent, per ine5 (ICAEN qvqg-zag8).
    Munis sense gas canalitzat no hi surten → 0 (no és buit: és que no hi ha xarxa)."""
    noms = [_icaen_norm(c) for c in comarques]
    where = "sector='DOMÈSTIC' and comarca in (" + ",".join(f"'{n}'" for n in noms) + ")"
    rows = _socrata(GAS_URL, where, "cdmun,any,consum_kwh_pcs,comarca")
    latest: dict[str, tuple[int, float]] = {}
    for r in rows:
        ine5 = str(r.get("cdmun", "")).zfill(5)
        any_ = int(_num(r.get("any")) or 0)
        kwh = _num(r.get("consum_kwh_pcs"))
        if kwh is None:
            continue
        if ine5 not in latest or any_ > latest[ine5][0]:
            latest[ine5] = (any_, kwh)
    return {k: v[1] for k, v in latest.items()}


def fetch_residus(comarques: list[str]) -> dict[str, dict]:
    where = "comarca in (" + ",".join(f"'{c}'" for c in comarques) + ")"
    rows = _socrata(ARC_URL, where, "codi_municipi,municipi,any,kg_hab_any,poblaci,comarca")
    latest: dict[str, tuple[int, dict]] = {}
    for r in rows:
        codi6 = str(r.get("codi_municipi", "")).zfill(6)
        ine5 = codi6[:5]
        any_ = int(_num(r.get("any")) or 0)
        kg = _num(r.get("kg_hab_any"))
        if kg is None:
            continue
        if ine5 not in latest or any_ > latest[ine5][0]:
            latest[ine5] = (any_, {"codi6": codi6, "municipi": r.get("municipi"),
                                   "kg_hab_any": kg, "poblacio_arc": _num(r.get("poblaci"))})
    return {k: v[1] for k, v in latest.items()}


def fetch_rtc(codi6s: list[str]) -> dict[str, int]:
    """Places turístiques totals (tots els tipus d'allotjament) per ine5 (RTC t2h3-cgys)."""
    if not codi6s:
        return {}
    where = "codi_municipi_idescat in (" + ",".join(f"'{c}'" for c in codi6s) + ")"
    rows = _socrata(RTC_URL, where, "codi_municipi_idescat,total_places")
    out: dict[str, int] = {}
    for r in rows:
        ine5 = str(r.get("codi_municipi_idescat", "")).zfill(6)[:5]
        out[ine5] = out.get(ine5, 0) + int(_num(r.get("total_places")) or 0)
    return out


def fetch_etca(codi6s: set[str]) -> dict[str, dict]:
    url = "https://www.idescat.cat/pub/?id=epe&n=17886&geo=mun&f=ssv"
    with urllib.request.urlopen(url, timeout=60) as r:
        text = r.read().decode("utf-8-sig")
    lines = text.splitlines()
    h = next(i for i, ln in enumerate(lines) if ln.startswith("Codi;"))
    out: dict[str, dict] = {}
    for row in csv.reader(io.StringIO("\n".join(lines[h:])), delimiter=";"):
        if len(row) >= 8 and row[0].strip() in codi6s:
            out[row[0].strip()] = {"resident": _num(row[5]), "etca": _num(row[6])}
    return out


def fetch_emex(codi6: str) -> dict:
    url = f"https://api.idescat.cat/emex/v1/dades.json?id={codi6}"
    d = None
    for attempt in range(3):  # Idescat fa 502/timeout transitoris; reintenta abans de rendir-se
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                d = json.load(r)
            break
        except Exception:
            if attempt == 2:
                return {"altitud": None, "densitat": None}
    if d is None:
        return {"altitud": None, "densitat": None}

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


def classify(nom: str, altitud: float | None, densitat: float | None) -> str:
    n = _norm(nom)
    if n in COSTANERS_NOMS:
        return "litoral_metropolita" if n in AMB_NOMS else "litoral_vacacional"
    # Densitat (no pertinença AMB) decideix el dens urbà: l'AMB barreja pisos petits (poc
    # elèctric) amb residencial de cases grans (molt elèctric) → no és bon predictor sol.
    if densitat is not None and densitat >= DENSITAT_METRO:
        return "metropolita_dens"
    if n in AMB_NOMS:  # AMB però NO densa = corona residencial (perifèria de mobilitat obligada)
        return "corona_metropolitana"
    if altitud is not None and altitud >= ALTITUD_PIRINEU:
        return "pirineu_alta_muntanya"
    return "interior_rural"


def _spearman(pairs):
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

    xs, ys = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    dx = sum((xs[i] - mx) ** 2 for i in range(n)) ** 0.5
    dy = sum((ys[i] - my) ** 2 for i in range(n)) ** 0.5
    return None if dx == 0 or dy == 0 else num / (dx * dy)


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return None if n == 0 else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)


def _fmt(x):
    return "—" if x is None else f"{x:.2f}"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(f"Comarques: {', '.join(COMARQUES)}")
    print("Baixant senyals (ICAEN elèctric+gas / ARC), RTC, ETCA i EMEX…")
    electric = fetch_electric(COMARQUES)
    gas = fetch_gas(COMARQUES)
    residus = fetch_residus(COMARQUES)
    # Conjunt de munis = els que tenen residus (porten nom + codi6) i elèctric.
    ine5s = sorted(set(residus) & set(electric))
    codi6s = [residus[i]["codi6"] for i in ine5s]
    rtc = fetch_rtc(codi6s)
    etca = fetch_etca(set(codi6s))
    print(f"Munis amb senyals: {len(ine5s)}")

    rows = []
    for ine5 in ine5s:
        codi6 = residus[ine5]["codi6"]
        nom = residus[ine5]["municipi"]
        e = etca.get(codi6, {})
        # EMEX (altitud/densitat) només per als munis amb ETCA (els que entren a l'anàlisi);
        # la resta (<1.000 hab, sense ETCA) es classifiquen per nom/residual.
        em = fetch_emex(codi6) if e else {"altitud": None, "densitat": None}
        resident, etca_v = e.get("resident"), e.get("etca")
        kwh_dom = electric.get(ine5)
        gas_dom = gas.get(ine5, 0.0)  # sense gas canalitzat → 0 (no buit)
        kg_hab = residus[ine5]["kg_hab_any"]
        places = rtc.get(ine5, 0)
        pernocta_est = round(kwh_dom / BASE_ELECTRIC) if kwh_dom else None
        err = (round((pernocta_est - etca_v) / etca_v * 100, 1)
               if (pernocta_est and etca_v) else None)
        # Fracció de gas del consum domèstic = gas/(gas+elèctric): proxy de calefacció de gas
        # (ràtio → independent de la presència). Alta → menys elèctric/persona esperat.
        gas_fraction = (round(gas_dom / (gas_dom + kwh_dom), 3)
                        if (kwh_dom and (gas_dom + kwh_dom) > 0) else None)
        rows.append({
            "ine5": ine5, "municipi": nom,
            "tipus_territorial": classify(nom, em["altitud"], em["densitat"]),
            "resident": int(resident) if resident else None,
            "etca": int(etca_v) if etca_v else None,
            "pernocta_est": pernocta_est,
            "err_pernocta_pct": err,
            "rtc_places": places,
            "rtc_places_per_resident": (round(places / resident, 3) if resident else None),
            "gas_kwh_dom": int(gas_dom) if gas_dom else 0,
            "gas_fraction": gas_fraction,
            "altitud_m": int(em["altitud"]) if em["altitud"] is not None else "",
            "densitat_hab_km2": em["densitat"] if em["densitat"] is not None else "",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nEscrit {OUT.relative_to(REPO).as_posix()} · {len(rows)} munis")

    # Per-muni (per VERIFICAR la classificació a ull) — només els que tenen ETCA.
    print("\nPer municipi (amb ETCA):")
    print(f"  {'municipi':26} {'tipus':22} {'ETCA':>8} {'pernoc':>8} {'err%':>6} {'RTC/res':>8}")
    for r in sorted((x for x in rows if x["etca"]), key=lambda x: (x["tipus_territorial"], x["ine5"])):
        print(f"  {r['municipi'][:25]:26} {r['tipus_territorial']:22} {r['etca']:>8} "
              f"{str(r['pernocta_est'] or '—'):>8} {str(r['err_pernocta_pct'] or '—'):>6} "
              f"{str(r['rtc_places_per_resident'] or '—'):>8}")

    # Per tipus: base única + recalibració + RTC vs residual
    tipus: dict[str, list[dict]] = {}
    for r in rows:
        if r["etca"] and r["pernocta_est"]:
            tipus.setdefault(r["tipus_territorial"], []).append(r)

    print("\nBase única Berguedà (1224) → error vs ETCA per tipus:")
    for t, rs in sorted(tipus.items()):
        med = _median([abs(r["err_pernocta_pct"]) for r in rs])
        rho = _spearman([(r["pernocta_est"], r["etca"]) for r in rs])
        v = "—" if med is None or rho is None else ("GO" if abs(rho) >= GO_RHO and med <= GO_ERR else "NO-GO")
        print(f"  {t:22} n={len(rs):3}  err_medià={_fmt(med)}%  ρ={_fmt(rho)}  → {v}")

    print("\nRecalibració ràpida — base per tipus (provisional):")
    base_rows = []
    for t, rs in sorted(tipus.items()):
        ratios = [r["etca"] / r["pernocta_est"] for r in rs]
        factor = _median(ratios)
        base_t = round(BASE_ELECTRIC / factor)
        resid = [abs((r["pernocta_est"] * factor - r["etca"]) / r["etca"] * 100) for r in rs]
        med_res, max_res = _median(resid), max(resid)
        # RTC vs residual signat (per veure si l'estacionalitat explica la dispersió del vacacional)
        signed = [((r["pernocta_est"] * factor - r["etca"]) / r["etca"] * 100, r["rtc_places_per_resident"])
                  for r in rs if r["rtc_places_per_resident"] is not None]
        rho_rtc = _spearman([(s, p) for s, p in signed]) if len(signed) >= 3 else None
        v = "GO" if max_res <= GO_ERR else "NO-GO"
        base_rows.append({"tipus_territorial": t, "n": len(rs), "base_electric_tipus": base_t,
                          "factor": round(factor, 3),
                          "residual_medianpct": round(med_res, 1) if med_res is not None else "",
                          "residual_maxpct": round(max_res, 1),
                          "rho_residual_rtc": round(rho_rtc, 2) if rho_rtc is not None else "",
                          "go_nogo": v})
        print(f"  {t:22} n={len(rs):3} base={base_t:5} (×{factor:.2f})  resid medià={_fmt(med_res)}% "
              f"màx={_fmt(max_res)}%  ρ(resid,RTC)={_fmt(rho_rtc)}  → {v}")

    base_out = OUT.parent / "nivellc_bases_tipus.csv"
    with base_out.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(base_rows[0].keys()))
        w.writeheader()
        w.writerows(base_rows)
    print(f"\nBases per tipus → {base_out.relative_to(REPO).as_posix()} (provisional, intern)")
    print("Nota: base ÚNICA Berguedà = 1224. ρ(resid,RTC) alt al vacacional = l'estacionalitat "
          "(places/resident) explica el residual → covariable candidata.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
