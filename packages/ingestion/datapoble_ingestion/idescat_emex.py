"""Connector Idescat EMEX — "El municipi en xifres".

EMEX **no és Socrata**: és una API pròpia d'Idescat que torna un JSON niat
(``fitxes.gg.g[]…ff.f[]``) on cada fulla porta ``id`` (codi d'indicador, p. ex.
``f321`` = població), ``calt``/``c`` (etiqueta), ``r`` (any) i ``v`` (valor amb
format ``municipi,comarca,Catalunya``). Per això aquí fem servir ``requests``
(no dlt) i aplanem a format llarg.

Sortida: ``data/raw/idescat_emex/idescat_emex.parquet`` amb columnes
``codi6, ine5, indicator_id, label, year, value_municipi`` (una fila per
indicador rellevant i municipi), + ``_provenance.json``.

Els ``indicator_id`` rellevants per a ``mart_municipi`` estan verificats en viu
(2026-06-02) contra els valors de ``docs/data-sources.md``.
"""
from __future__ import annotations

import time

import pandas as pd
import requests

from .config import IDESCAT_EMEX_BASE, raw_path
from .municipis import BERGUEDA
from .provenance import write_provenance

SOURCE = "idescat_emex"

# Indicadors EMEX que alimenten mart_municipi (id -> nom intern).
# Verificat: Castellar (080522) dona poblacio=166, hab_total=276,
# hab_principal=71, hab_noprincipal=205 (= docs/data-sources.md).
INDICATORS: dict[str, str] = {
    "f321": "poblacio",          # Població
    "f122": "hab_total",         # Habitatges familiars (total)
    "f250": "hab_principal",     # Habitatges familiars principals
    "f398": "hab_noprincipal",   # Habitatges familiars no principals
    "f167": "pob_0_14",          # Població de 0 a 14 anys
    "f28": "pob_65_84",          # Població de 65 a 84 anys
    "f29": "pob_85_mes",         # Població de 85 anys i més
    # ETCA (Estimacions de població estacional, Idescat EPE base 2021) — àncora de
    # validació externa del Pas 4. Només present als munis ≥1.000 hab (els petits no en
    # tenen → no apareixeran a la resposta EMEX, queden NULL: cobertura honesta).
    "f342": "etca_estacional",   # Població estacional ETCA (total: no resident present − resident absent)
    "f343": "poblacio_etca",     # Població ETCA (resident + estacional; equivalent temps complet anual)
    "f344": "etca_pct",          # Població ETCA / població resident (%)
    # Covariables estructurals (Pas 4 · Nivell B classificador tipus_territorial): què ÉS el
    # municipi, no com s'habita. Estables, de fonts oficials.
    "f258": "altitud_m",         # Altitud (m) — llindar Pirineu / alta muntanya
    "f261": "superficie_km2",    # Superfície (km²)
    "f262": "densitat_hab_km2",  # Densitat de població (hab/km²) — llindar metropolità
}

TIMEOUT = 60


def _iter_leaves(node):
    """Recorre el JSON niat i emet cada fulla (dict amb ``id`` i ``v``)."""
    if isinstance(node, dict):
        if "id" in node and "v" in node:
            yield node
        for value in node.values():
            yield from _iter_leaves(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_leaves(item)


def _municipi_value(v: str):
    """El primer camp de ``v`` (separat per comes) és el valor municipal."""
    first = str(v).split(",")[0].strip()
    if first in ("", "_", "-"):
        return None
    return first


def fetch_municipi(codi6: str, session: requests.Session | None = None) -> list[dict]:
    """Descarrega i aplana els indicadors rellevants d'un municipi."""
    sess = session or requests.Session()
    resp = sess.get(IDESCAT_EMEX_BASE, params={"id": codi6}, timeout=TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()

    rows: list[dict] = []
    seen: set[str] = set()
    for leaf in _iter_leaves(payload):
        fid = leaf.get("id")
        if fid in INDICATORS and fid not in seen:
            seen.add(fid)  # alguns ids apareixen repetits a diferents fitxes
            rows.append(
                {
                    "codi6": codi6,
                    "ine5": codi6[:5],
                    "indicator_id": fid,
                    "indicator": INDICATORS[fid],
                    "label": leaf.get("calt") or leaf.get("c"),
                    "year": leaf.get("r"),
                    "value_municipi": _municipi_value(leaf.get("v")),
                }
            )
    return rows


def run(municipis: dict[str, str] = BERGUEDA, pause: float = 0.2, accumulate: bool = False) -> dict:
    """Ingesta EMEX dels municipis donats. Idempotent.

    `accumulate=False` (per defecte): sobreescriu el parquet sencer (pilot Berguedà).
    `accumulate=True`: baixa a TROSSOS — carrega el parquet existent, en treu els municipis
    d'aquest tros (els refresca) i hi concatena els nous. Així trossos successius (p. ex. per
    província) s'acumulen i re-córrer un tros és idempotent. Vegeu docs/pla-catalunya-profund.md F1.2b.
    """
    out_dir = raw_path(SOURCE)
    out_file = out_dir / "idescat_emex.parquet"
    session = requests.Session()
    all_rows: list[dict] = []
    for codi6 in municipis:
        all_rows.extend(fetch_municipi(codi6, session=session))
        if pause:
            time.sleep(pause)  # cortesia amb l'API pública

    df = pd.DataFrame(all_rows)
    if accumulate and out_file.exists():
        prev = pd.read_parquet(out_file)
        prev = prev[~prev["codi6"].astype(str).isin({str(c) for c in municipis})]
        df = pd.concat([prev, df], ignore_index=True)
    df.to_parquet(out_file, index=False)

    n_total = int(df["codi6"].astype(str).nunique()) if not df.empty else 0
    write_provenance(
        SOURCE,
        out_dir,
        row_count=len(df),
        files=[out_file.name],
        query={"ids": list(municipis.keys()), "indicators": INDICATORS},
        extra={
            "loader": "requests",
            "n_municipis": n_total,
            "n_municipis_tros": len(municipis),
            "mode": "accumulate" if accumulate else "replace",
            "format": "long (indicator x municipi)",
        },
    )
    return {"source": SOURCE, "rows": len(df), "files": [out_file.name]}


if __name__ == "__main__":
    print(run())
