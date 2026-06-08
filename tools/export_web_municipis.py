#!/usr/bin/env python3
"""Export marts → JSON per al web (Mirador). Pas de pipeline repetible.

Llegeix els marts reals que produeix `packages/transform`
(`data/marts/mart_municipi.parquet` + `mart_electoral.parquet`) i el contracte
semàntic (`semantic/metrics.yml`), i emet un únic artefacte JSON amb la forma
EXACTA que espera el frontend: `MunicipisDataset`
(`packages/web/src/lib/contract/types.ts`, implementada al mock
`packages/web/src/lib/mock/municipis.ts`).

Sortida: `data/web/municipis.bergueda.json` — els 31 municipis del Berguedà amb
dades REALS, llest perquè Mirador substitueixi el mock per un loader sense canviar
la forma.

Frontera honesta (cap valor inventat):
  · El catàleg `metrics` surt del contracte (`metrics.yml`): label/unit/nota/date/
    dimension/status NO es codifiquen aquí, vénen del contracte. Només el `format`
    de presentació i la cadena `source` llegible es resolen amb un mapa fix (mirall
    de com Mirador ja els pinta).
  · `pct_icaen_EFG` = null per a tots: requereix el connector de certificats ICAEN
    (`j6ii-t3w2`), fora d'aquest PR. És un buit honest marcat (status del contracte),
    no un placeholder.
  · Els indicadors polítics (`pct_indep`, `pct_esquerra`, `pct_extrema_dreta`,
    `guanya`) surten de `mart_electoral`, convocatòria Parlament 2024 (A20241).
    LECTURA ECOLÒGICA (agregat municipal, mai individual; volàtil en micromunicipis).
  · Qualsevol valor absent al mart s'emet com a `null` (n. d.), mai s'omple.

Ús:
    python tools/export_web_municipis.py            # des de l'arrel del repo
    python tools/export_web_municipis.py --check     # no escriu; falla si caldria

Requereix: pandas, pyarrow, pyyaml. Els marts han d'existir (executa abans
`packages/transform`: `dbt build`).
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
MART_MUNI = REPO / "data" / "marts" / "mart_municipi.parquet"
MART_ELEC = REPO / "data" / "marts" / "mart_electoral.parquet"
METRICS_YML = REPO / "semantic" / "metrics.yml"
OUT = REPO / "data" / "web" / "municipis.bergueda.json"

# Convocatòria electoral vigent per a les columnes polítiques del web.
ELEC = "A20241"

# Ordre i claus de mètrica del contracte (= MetricKey a types.ts). Determina
# l'ordre del catàleg `metrics` al JSON (estable → diffs nets).
METRIC_KEYS = [
    "poblacio", "hab_total", "hab_principal", "hab_noprincipal",
    "pct_noprincipal", "hab_per_hab", "index_envelliment",
    "rtc_total", "rtc_hut", "rtc_per_1000hab", "rtc_per_100hab_viv",
    "kg_hab_any",
    # Senyals físics per càpita (inputs de les 3 capes).
    "kwh_hab", "vidre_hab",
    # 2n proxy d'hostaleria de la capa L3 (restauració OSM, complement del vidre).
    "restauracio_estab", "restauracio_per_1000hab",
    # Indicador estrella: MODEL DE 3 CAPES (derived, inferència).
    # L1 població pernocta (la nova «població invisible»):
    "poblacio_pernocta_est", "gap_pernocta", "gap_pernocta_pct",
    # L2 càrrega humana total · L3 pressió turística:
    "carrega_total_est", "index_turisme", "confianca",
    # Compatibilitat (model anterior d'una capa), reenquadrades:
    "poblacio_real_est", "gap_abs", "gap_pct", "poblacio_real_rel",
    "pct_icaen_EFG", "IETR", "IETR_rank",
    "pct_indep", "pct_esquerra", "pct_extrema_dreta", "guanya",
]

# Format de presentació per clau (MetricFormat a types.ts). No és al contracte
# (és de presentació); mirall de com Mirador ja pinta cada mètrica al mock.
FORMAT_BY_KEY = {
    "poblacio": "integer", "hab_total": "integer", "hab_principal": "integer",
    "hab_noprincipal": "integer", "pct_noprincipal": "percent",
    "hab_per_hab": "ratio", "index_envelliment": "decimal",
    "rtc_total": "integer", "rtc_hut": "integer", "rtc_per_1000hab": "decimal",
    "rtc_per_100hab_viv": "decimal", "kg_hab_any": "decimal",
    # Senyals per càpita.
    "kwh_hab": "decimal", "vidre_hab": "decimal",
    # Restauració (2n proxy hostaleria L3): compte enter + densitat decimal.
    "restauracio_estab": "integer", "restauracio_per_1000hab": "decimal",
    # 3 capes: comptes d'habitants → integer; *_pct ja en 0-100 → percent (mateixa
    # convenció que pct_noprincipal); index_turisme és 0-100 → decimal; confianca → text.
    "poblacio_pernocta_est": "integer", "gap_pernocta": "integer",
    "gap_pernocta_pct": "percent", "carrega_total_est": "integer",
    "index_turisme": "decimal",
    # Compatibilitat (model anterior).
    "poblacio_real_est": "integer", "gap_abs": "integer", "gap_pct": "percent",
    "poblacio_real_rel": "integer", "confianca": "text",
    "pct_icaen_EFG": "percent", "IETR": "decimal", "IETR_rank": "rank",
    "pct_indep": "percent", "pct_esquerra": "percent",
    "pct_extrema_dreta": "percent", "guanya": "text",
}

# Mapa clau de mètrica → columna del mart corresponent.
COL_MUNI = {
    "poblacio": "poblacio", "hab_total": "hab_total",
    "hab_principal": "hab_principal", "hab_noprincipal": "hab_noprincipal",
    "pct_noprincipal": "pct_noprincipal", "hab_per_hab": "hab_per_hab",
    "index_envelliment": "index_envelliment", "rtc_total": "rtc_total",
    "rtc_hut": "rtc_hut", "rtc_per_1000hab": "rtc_per_1000hab",
    "rtc_per_100hab_viv": "rtc_per_100hab_viv", "kg_hab_any": "kg_hab_any",
    # Senyals per càpita.
    "kwh_hab": "kwh_hab", "vidre_hab": "vidre_hab",
    # Restauració (2n proxy hostaleria L3).
    "restauracio_estab": "restauracio_estab",
    "restauracio_per_1000hab": "restauracio_per_1000hab",
    # Indicador estrella: model de 3 capes.
    "poblacio_pernocta_est": "poblacio_pernocta_est", "gap_pernocta": "gap_pernocta",
    "gap_pernocta_pct": "gap_pernocta_pct", "carrega_total_est": "carrega_total_est",
    "index_turisme": "index_turisme",
    # Compatibilitat (model anterior d'una capa).
    "poblacio_real_est": "poblacio_real_est", "gap_abs": "gap_abs",
    "gap_pct": "gap_pct", "poblacio_real_rel": "poblacio_real_rel",
    "confianca": "confianca",
    "pct_icaen_EFG": "pct_icaen_EFG", "IETR": "IETR", "IETR_rank": "IETR_rank",
}

# Columnes de mart_municipi que són TEXT (no numèriques) → no passen per _num().
TEXT_COLS_MUNI = {"confianca"}
COL_ELEC = {
    "pct_indep": f"pct_indep_{ELEC}",
    "pct_esquerra": f"pct_esq_{ELEC}",
    "pct_extrema_dreta": f"pct_extrema_dreta_{ELEC}",
    "guanya": f"guanya_{ELEC}",
}

# Mètriques de recompte (suma comarcal) vs derivades (no se sumen).
COMARCA_SUM = ["poblacio", "hab_total", "rtc_total"]


def _localized(node: Any) -> dict[str, str] | None:
    """Normalitza un camp del contracte a {ca, es}. Accepta dict o escalar
    (p. ex. unit: "%" → mateix valor a tots dos locales)."""
    if node is None:
        return None
    if isinstance(node, dict):
        return {"ca": str(node.get("ca", "")), "es": str(node.get("es", ""))}
    s = str(node)
    return {"ca": s, "es": s}


def _source_label(spec: dict, sources: dict) -> str:
    """Cadena llegible de la font (mirall del mock): organisme — producte, amb
    `origin_source` afegit per a derivades de datapoble."""
    src = sources.get(spec.get("source", ""), {})
    org = src.get("organisme", spec.get("source", ""))
    prod = src.get("producte")
    label = f"{org} — {prod}" if prod else org
    origin = spec.get("origin_source")
    if origin and origin in sources:
        label += f" · {sources[origin].get('organisme', origin)}"
    return label


def build_metrics(contract: dict) -> dict[str, dict]:
    """Catàleg `metrics` (Record<MetricKey, MetricDef>) des del contracte."""
    raw = contract["metrics"]
    sources = contract.get("sources", {})
    out: dict[str, dict] = {}
    for key in METRIC_KEYS:
        spec = raw[key]
        m: dict[str, Any] = {
            "key": key,
            "label": _localized(spec.get("label")),
            "unit": _localized(spec.get("unit")),
            "dimension": spec.get("dimension"),
            "format": FORMAT_BY_KEY[key],
            "source": _source_label(spec, sources),
        }
        if spec.get("date"):
            m["date"] = str(spec["date"])
        # definicio: text canònic del «diccionari» que pinta el glossari
        # (definicio.ca/.es del contracte). S'emet només si hi és; si falta, el
        # web recau en `note` (MetricDef.definicio? és opcional).
        definicio = _localized(spec.get("definicio"))
        if definicio:
            m["definicio"] = definicio
        note = _localized(spec.get("nota"))
        if note:
            m["note"] = note
        # status: explícit al contracte (planned) o public per defecte (visibility).
        m["status"] = spec.get("status") or (
            "public" if spec.get("visibility") == "public" else "planned"
        )
        out[key] = m
    return out


def _num(v: Any) -> Any:
    """Cast a int/float net per a JSON, o None si NaN/None. Enters sense .0."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if pd.isna(v):
        return None
    f = float(v)
    return int(f) if f.is_integer() else f


def build_municipis(muni: pd.DataFrame, elec: pd.DataFrame) -> dict[str, dict]:
    """Files per municipi (Record<Ine5, MunicipiRow>), dades reals."""
    elec_by = elec.set_index("ine5")
    out: dict[str, dict] = {}
    for _, r in muni.iterrows():
        ine5 = str(r["ine5"])
        values: dict[str, Any] = {}
        for key, col in COL_MUNI.items():
            if col not in muni.columns:
                values[key] = None
            elif col in TEXT_COLS_MUNI:
                v = r[col]
                values[key] = None if pd.isna(v) else str(v)
            else:
                values[key] = _num(r[col])
        # Polítics des de mart_electoral (A20241). guanya és text (sigla) o None.
        if ine5 in elec_by.index:
            er = elec_by.loc[ine5]
            for key, col in COL_ELEC.items():
                if col not in elec.columns:
                    values[key] = None
                elif key == "guanya":
                    g = er[col]
                    values[key] = None if pd.isna(g) else str(g)
                else:
                    values[key] = _num(er[col])
        else:
            for key in COL_ELEC:
                values[key] = None
        out[ine5] = {
            "ine5": ine5,
            "nom": str(r["municipi"]),
            "idescat6": str(r["codi6"]),
            "values": values,
        }
    return out


def build_comarca(muni: pd.DataFrame, contract: dict) -> dict:
    """KPIs comarcals REALS: suma per a recomptes; mitjana ponderada per població
    per a ràtios per càpita; mitjana simple per a percentatges/índex."""
    pop = muni["poblacio"].astype(float)
    tot_pop = float(pop.sum())
    tot_viv = float(muni["hab_total"].astype(float).sum())

    def wmean_pc(col: str, denom: float, scale: float) -> float:
        # ràtio comarcal = suma(numerador) / denominador comarcal (coherent amb
        # la definició per càpita, no mitjana de ràtios municipals).
        # numerador = ràtio_muni * denom_muni / scale  → reconstrucció robusta.
        num = (muni[col].astype(float) * (pop if "1000" in col else muni["hab_total"].astype(float)) / scale).sum()
        return round(num / denom * scale, 2) if denom else None

    vals: dict[str, Any] = {
        "poblacio": int(tot_pop),
        "hab_total": int(tot_viv),
        "pct_noprincipal": round(
            float(muni["hab_noprincipal"].astype(float).sum()) / tot_viv * 100, 1
        ) if tot_viv else None,
        "rtc_total": int(muni["rtc_total"].astype(float).sum()),
        "rtc_per_1000hab": round(
            float(muni["rtc_total"].astype(float).sum()) / tot_pop * 1000, 2
        ) if tot_pop else None,
        # kg_hab_any comarcal: mitjana ponderada per població (càrrega mitjana real).
        "kg_hab_any": round(
            float((muni["kg_hab_any"].astype(float) * pop).sum()) / tot_pop, 1
        ) if tot_pop else None,
        # IETR comarcal: mediana de la distribució normalitzada (definició del contracte).
        "IETR": round(float(muni["IETR"].astype(float).median()), 1),
    }
    # Nom de la comarca: és el topònim del pilot (igual en ca/es), no una mètrica
    # del contracte. Coherent amb el mock (`comarca.label`).
    comarca_nom = str(muni["comarca"].iloc[0]) if "comarca" in muni.columns else "Berguedà"
    return {
        "label": {"ca": comarca_nom, "es": comarca_nom},
        "num_municipis": int(len(muni)),
        "values": vals,
    }


def build_dataset() -> dict:
    contract = yaml.safe_load(METRICS_YML.read_text(encoding="utf-8"))
    muni = pd.read_parquet(MART_MUNI)
    elec = pd.read_parquet(MART_ELEC)

    n = len(muni)
    if n != 31:
        print(f"AVÍS: mart_municipi té {n} files (s'esperaven 31).", file=sys.stderr)

    return {
        "contractVersion": str(contract["meta"]["version"]),
        "scope": str(contract["meta"]["scope"]),
        "metrics": build_metrics(contract),
        "municipis": build_municipis(muni, elec),
        "comarca": build_comarca(muni, contract),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="export_web_municipis")
    ap.add_argument(
        "--check", action="store_true",
        help="no escriu; falla (codi 1) si el JSON al disc no coincideix amb el generat",
    )
    args = ap.parse_args(argv)

    for p in (MART_MUNI, MART_ELEC, METRICS_YML):
        if not p.exists():
            print(f"FALLA: no existeix {p} (executa abans el pipeline transform)", file=sys.stderr)
            return 2

    dataset = build_dataset()
    payload = json.dumps(dataset, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"FALLA (--check): no existeix {OUT}", file=sys.stderr)
            return 1
        # Llegim SENSE traducció de finals de línia (newline="") perquè la
        # comparació sigui estable a Windows/Linux: el fitxer sempre s'escriu amb
        # LF (coherent amb `.gitattributes` eol=lf).
        with OUT.open("r", encoding="utf-8", newline="") as fh:
            on_disk = fh.read()
        if on_disk != payload:
            print(f"FALLA (--check): {OUT} està desactualitzat (re-executa sense --check)", file=sys.stderr)
            return 1
        print(f"OK (--check): {OUT} al dia ({len(dataset['municipis'])} municipis).")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n": LF explícit (no CRLF a Windows) → byte-estable amb eol=lf.
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
    n_muni = len(dataset["municipis"])
    n_metrics = len(dataset["metrics"])
    print(f"Escrit {OUT.relative_to(REPO).as_posix()} · {n_muni} municipis · {n_metrics} mètriques.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
