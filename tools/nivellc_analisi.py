#!/usr/bin/env python3
"""Nivell C · senyals per municipi a escala CATALUNYA (base de la regressió i l'export).

DIRIGIT PER COMARCA (totes 43 de `comarca_vegueria.csv`): baixa en viu els senyals
(elèctric ICAEN `8idm-becu` sector 7, gas ICAEN `qvqg-zag8` domèstic, residus ARC `69zu-w48s`),
les places RTC `t2h3-cgys` i l'ETCA oficial (Idescat EPE) — els municipis i els codis surten de
les DADES, no d'una llista a mà.

Covariables del model (totes NO depenen de la presència):
  · DENSITAT = població (ARC/EPE) / superfície (derivada del geojson oficial, offline). Equival a
    la densitat EMEX d'Idescat (r=0,9999 als munis validats) sense ~900 crides per-muni.
  · RENDA (INE ADRH 2023, via tools/extract_renda.py · l'afegeix la regressió).
  · GAS (fracció de gas del consum domèstic) — proxy de calefacció.

CLASSIFICACIÓ `tipus_territorial` (per a la banda per tipus):
  · litoral: municipi a la llista OFICIAL de costaners (`municipi_litoral.csv`, 70 munis derivats de
    Territori/PPOL, Llei 8/2020; match per ine5). litoral_metropolita si també AMB, si no
    litoral_vacacional.
  · metropolita_dens (densitat alta) · corona_metropolitana (AMB no densa) · interior_rural (resta).
    (L'altitud/pirineu queda fora en aquesta versió escalada: la validació held-out per tipus ja
    filtra els munis de muntanya amb estacionalitat que el model anual no capta.)

Sortida: `data/territorial/nivellc_analisi.csv` (un munis per fila, amb ETCA on n'hi ha) + resum.
Tot bulk/offline: cap fetch per-muni. Carril dades.

Ús:  python tools/nivellc_analisi.py
"""
from __future__ import annotations

import csv
import io
import json
import math
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from shapely import transform as shp_transform
from shapely.geometry import shape

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "territorial" / "nivellc_analisi.csv"
LITORAL_CSV = REPO / "data" / "territorial" / "municipi_litoral.csv"
MUNIS_GEO = REPO / "packages" / "web" / "static" / "geo" / "catalunya-municipis.geojson"

GO_RHO, GO_ERR = 0.7, 15.0
DENSITAT_METRO = 1500.0

ICAEN_URL = "https://analisi.transparenciacatalunya.cat/resource/8idm-becu.json"
GAS_URL = "https://analisi.transparenciacatalunya.cat/resource/qvqg-zag8.json"
ARC_URL = "https://analisi.transparenciacatalunya.cat/resource/69zu-w48s.json"
RTC_URL = "https://analisi.transparenciacatalunya.cat/resource/t2h3-cgys.json"

# Projecció equirectangular local (graus → m) per a l'àrea dels municipis.
_LAT0 = 41.7
_M_LAT = 111_132.0
_M_LON = 111_320.0 * math.cos(math.radians(_LAT0))


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = s.replace("'", " ").replace("-", " ")
    parts = [p for p in s.split() if p not in {"el", "la", "els", "les", "l", "de", "del", "d"}]
    return " ".join(parts)


# AMB = 36 municipis de l'Àrea Metropolitana de Barcelona (llista fixa oficial).
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


def load_costaners() -> set[str]:
    """ine5 dels 70 municipis costaners — llista OFICIAL (Territori/PPOL, Llei 8/2020) a
    `municipi_litoral.csv`. Match per ine5 (robust als canvis de topònim). La derivació geomètrica
    (`municipis_costaners.csv`, `tools/deriva_costaners.py`) queda com a cross-check."""
    if not LITORAL_CSV.exists():
        return set()
    with LITORAL_CSV.open(encoding="utf-8") as fh:
        return {r["ine5"] for r in csv.DictReader(fh, delimiter=";") if r.get("litoral") == "costaner"}


def build_areas() -> dict[str, float]:
    """Superfície km² per ine5 des de la geometria oficial (equirectangular local)."""
    gj = json.loads(MUNIS_GEO.read_text(encoding="utf-8"))
    out: dict[str, float] = {}
    for f in gj["features"]:
        gm = shp_transform(
            shape(f["geometry"]),
            lambda c: np.column_stack([c[:, 0] * _M_LON, c[:, 1] * _M_LAT]),
        )
        out[str(f["properties"]["ine5"])] = gm.area / 1e6
    return out


def _num(s):
    s = str(s if s is not None else "").replace(".", "").replace(",", ".").strip()
    return None if s in ("", "..", "(..)", "_", "-") else float(s)


def _socrata(url: str, where: str | None, select: str, limit: int = 300000) -> list[dict]:
    params = {"$select": select, "$limit": limit}
    if where:
        params["$where"] = where
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{q}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def fetch_electric() -> dict[str, float]:
    # Tot Catalunya (ICAEN és només de Catalunya); sense filtre de comarca (evita problemes de
    # noms amb apòstrof i la clàusula IN llarga). Sector 7 = domèstic.
    rows = _socrata(ICAEN_URL, "codi_sector='7'", "cdmun,any,consum_kwh")
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


def fetch_gas() -> dict[str, float]:
    rows = _socrata(GAS_URL, "sector='DOMÈSTIC'", "cdmun,any,consum_kwh_pcs")
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


def fetch_residus() -> dict[str, dict]:
    rows = _socrata(ARC_URL, None, "codi_municipi,municipi,any,kg_hab_any,poblaci")
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
    if not codi6s:
        return {}
    out: dict[str, int] = {}
    # En blocs (la clàusula IN amb ~950 codis és massa llarga per a una sola URL).
    for i in range(0, len(codi6s), 200):
        chunk = codi6s[i:i + 200]
        where = "codi_municipi_idescat in (" + ",".join(f"'{c}'" for c in chunk) + ")"
        for r in _socrata(RTC_URL, where, "codi_municipi_idescat,total_places"):
            ine5 = str(r.get("codi_municipi_idescat", "")).zfill(6)[:5]
            out[ine5] = out.get(ine5, 0) + int(_num(r.get("total_places")) or 0)
    return out


def fetch_etca(codi6s: set[str]) -> dict[str, dict]:
    """ETCA oficial (Idescat EPE, base 2021) per codi6. La SSV porta TOTS els munis; en filtrem els
    nostres. Munis sense valor d'ETCA (p. ex. <1.000 hab) queden fora del diccionari."""
    url = "https://www.idescat.cat/pub/?id=epe&n=17886&geo=mun&f=ssv"
    with urllib.request.urlopen(url, timeout=120) as r:
        text = r.read().decode("utf-8-sig")
    lines = text.splitlines()
    h = next(i for i, ln in enumerate(lines) if ln.startswith("Codi;"))
    out: dict[str, dict] = {}
    for row in csv.reader(io.StringIO("\n".join(lines[h:])), delimiter=";"):
        if len(row) >= 8 and row[0].strip() in codi6s:
            resident, etca = _num(row[5]), _num(row[6])
            if etca:
                out[row[0].strip()] = {"resident": resident, "etca": etca}
    return out


def classify(ine5: str, nom: str, densitat: float | None, costaners: set[str]) -> str:
    if ine5 in costaners:
        return "litoral_metropolita" if _norm(nom) in AMB_NOMS else "litoral_vacacional"
    if densitat is not None and densitat >= DENSITAT_METRO:
        return "metropolita_dens"
    if _norm(nom) in AMB_NOMS:  # AMB però no densa = corona residencial
        return "corona_metropolitana"
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


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    costaners = load_costaners()
    areas = build_areas()
    print(f"Costaners (provisional): {len(costaners)} · àrees: {len(areas)} · fetch: tot Catalunya")
    print("Baixant senyals (ICAEN elèctric+gas / ARC residus), RTC i ETCA…")
    electric = fetch_electric()
    gas = fetch_gas()
    residus = fetch_residus()
    # Conjunt = munis amb residus (nom+codi6) i elèctric (el senyal del model).
    ine5s = sorted(set(residus) & set(electric))
    codi6s = [residus[i]["codi6"] for i in ine5s]
    rtc = fetch_rtc(codi6s)
    etca = fetch_etca(set(codi6s))
    print(f"Munis amb senyals (residus∩elèctric): {len(ine5s)} · amb ETCA: {len(etca)}")

    rows = []
    sense_area = 0
    for ine5 in ine5s:
        codi6 = residus[ine5]["codi6"]
        nom = residus[ine5]["municipi"]
        e = etca.get(codi6, {})
        resident, etca_v = e.get("resident"), e.get("etca")
        kwh_dom = electric.get(ine5)
        gas_dom = gas.get(ine5, 0.0)
        places = rtc.get(ine5, 0)
        # Densitat = població / superfície (offline). Població: ARC (tots) o EPE resident (fallback).
        pop = residus[ine5].get("poblacio_arc") or resident
        area = areas.get(ine5)
        densitat = round(pop / area, 1) if (pop and area and area > 0) else None
        gas_fraction = (round(gas_dom / (gas_dom + kwh_dom), 3)
                        if (kwh_dom and (gas_dom + kwh_dom) > 0) else None)
        rows.append({
            "ine5": ine5, "municipi": nom,
            "tipus_territorial": classify(ine5, nom, densitat, costaners),
            "resident": int(resident) if resident else "",
            "poblacio": int(pop) if pop else "",
            "etca": int(etca_v) if etca_v else "",
            "kwh_dom": int(kwh_dom) if kwh_dom else "",
            "rtc_places": places,
            "rtc_places_per_resident": (round(places / resident, 3) if resident else ""),
            "gas_kwh_dom": int(gas_dom) if gas_dom else 0,
            "gas_fraction": gas_fraction if gas_fraction is not None else "",
            "altitud_m": "",  # fora en aquesta versió escalada (compat. de columna amb la regressió)
            "densitat_hab_km2": densitat if densitat is not None else "",
        })
        if densitat is None:
            sense_area += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nEscrit {OUT.relative_to(REPO).as_posix()} · {len(rows)} munis ({sense_area} sense densitat)")

    # Resum per tipus (munis amb ETCA, per veure cobertura del fit).
    from collections import Counter
    per_tipus = Counter(r["tipus_territorial"] for r in rows)
    amb_etca = Counter(r["tipus_territorial"] for r in rows if r["etca"])
    print("\nMunis per tipus (total · amb ETCA per al fit):")
    for t in sorted(per_tipus):
        print(f"  {t:22} {per_tipus[t]:4}  ·  {amb_etca.get(t, 0):4} amb ETCA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
