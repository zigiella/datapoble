"""Connector COMPOSICIÓ I ARRELAMENT (origen) — transformació demogràfica.

**Enquadrament (innegociable).** Aquesta capa és **TRANSFORMACIÓ DEMOGRÀFICA**, MAI
«extranjería». Separa tres lents que la gent confon:
  · **nacionalitat** (espanyola / estrangera) — passaport, no arrelament;
  · **lloc de naixement** (Catalunya / resta d'Espanya / estranger) — biografia;
  · **evolució temporal** — el vèrtigen (el delta), no la foto.
Lectura **ECOLÒGICA** (sobre el municipi, mai sobre individus) i **llindar mínim N**
als micromunicipis (el secret estadístic ve cuit de la font).

**Fonts (les dues municipals i obertes; verificades EN VIU 2026-06-08).** Cap d'INE:
les taules municipals d'INE (Tempus3) només donen població per sexe; el detall per
país/edat-per-origen és nacional/CCAA i topa amb el secret estadístic sota província.
**Idescat és l'única via municipal + sèrie.** Dues operacions complementàries:

  (A) **EMEX** (``api.idescat.cat/emex/v1/dades.json?id={codi6}``) — la FOTO del
      darrer any (2025, Cens anual de població de l'INE). Indicadors:
        · Per nacionalitat:    f183 espanyola · f184 estrangera · f263 total.
        · Per lloc de naixement: f69 Catalunya · f72 resta d'Espanya · f73 estranger
          · f74 total.
      El camp ``v`` ve com ``municipi,comarca,Catalunya`` → conservem els tres
      nivells (la comarca i Catalunya són el CONTRAST ecològic honest del municipi).

  (B) **Població estrangera** (``idescat.cat/poblacioestrangera/?b=6&geo=mun:{codi6}
      &f=ssv``) — la SÈRIE municipal **2021→** (% i variacions de població estrangera
      per nacionalitat). És l'ÚNICA via oberta amb sèrie temporal municipal → alimenta
      els DELTES. Format SSV (semicolon-separated, ISO-8859-1), decimal amb COMA, i el
      marcador ``(..)`` = «dada confidencial, amb baixa fiabilitat o no disponible»
      (= el llindar de secret estadístic dels micromunicipis, p. ex. Sant Jaume de
      Frontanyà, 25 hab → estrangers suprimits). El respectem com a NULL.

**Ruptura metodològica (honestedat).** La sèrie municipal de població estrangera ve
del **Padró** 2000–2020 i del **Cens anual** 2021→; el canvi de font el 2021 és una
RUPTURA. Per no barrejar peres amb pomes, INGERIM NOMÉS la sèrie 2021→ (Cens anual,
homogènia), que la font ja serveix. Els deltes es calculen dins d'aquesta finestra
(5 anys: 2021→2025). Documentat a docs/demografia-origen-fonts.md.

**Sortida** (``data/raw/demografia_origen/``):
  · ``origen_snapshot.parquet`` — 1 fila/municipi×nivell×indicador (EMEX, darrer any).
  · ``estrangera_serie.parquet`` — 1 fila/municipi×any (SSV, 2021→).
  · ``_provenance.json`` — traçabilitat de les dues vies.

**Per què ``requests`` (no dlt).** EMEX no és Socrata (JSON niat propi) i el SSV és un
text tabular ad hoc; tots dos demanen aplanat a mà, com el connector ``idescat_emex``.
"""
from __future__ import annotations

import csv
import io
import time

import pandas as pd
import requests

from .config import IDESCAT_EMEX_BASE, IDESCAT_POBESTR_BASE, raw_path
from .municipis import BERGUEDA
from .provenance import write_provenance

SOURCE = "demografia_origen"

# Indicadors EMEX d'origen (id -> nom intern). Verificat en viu (2026-06-08):
# Castellar 080522 → nascuda_estranger=13, nac_estrangera=10, total=166; Berga
# 080229 → nascuda_estranger=4092, nac_estrangera=3185, total=17539.
ORIGEN_INDICATORS: dict[str, str] = {
    # Per lloc de naixement (grup t68)
    "f69": "nascuda_catalunya",
    "f72": "nascuda_resta_espanya",
    "f73": "nascuda_estranger",
    "f74": "pob_lloc_naix_total",
    # Per nacionalitat (grup t75)
    "f183": "nac_espanyola",
    "f184": "nac_estrangera",
    "f263": "pob_nac_total",
}

# El camp v de l'EMEX ve com "municipi,comarca,Catalunya": conservem els 3 nivells
# perquè el municipi es llegeixi SEMPRE contra el seu context (lectura ecològica).
NIVELLS = ("municipi", "comarca", "catalunya")

# Confidencial / baixa fiabilitat / no disponible al SSV de població estrangera.
SSV_NULL = "(..)"
SSV_NULL_INLINE = ".."

TIMEOUT = 60
USER_AGENT = "datapoble-riusdegent/1.0 (observatori territorial; sondeig@datapoble.local)"


# --------------------------------------------------------------------------- #
# (A) EMEX — foto del darrer any per nacionalitat i lloc de naixement
# --------------------------------------------------------------------------- #
def _iter_leaves(node):
    """Recorre el JSON niat de l'EMEX i emet cada fulla (dict amb ``id`` i ``v``)."""
    if isinstance(node, dict):
        if "id" in node and "v" in node:
            yield node
        for value in node.values():
            yield from _iter_leaves(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_leaves(item)


def _split_levels(v: str) -> dict[str, float | None]:
    """Parteix el camp v (``municipi,comarca,Catalunya``) en els 3 nivells."""
    parts = [p.strip() for p in str(v).split(",")]
    out: dict[str, float | None] = {}
    for i, nivell in enumerate(NIVELLS):
        raw = parts[i] if i < len(parts) else ""
        if raw in ("", "_", "-", ".."):
            out[nivell] = None
        else:
            try:
                out[nivell] = float(raw)
            except ValueError:
                out[nivell] = None
    return out


def fetch_snapshot_municipi(codi6: str, session: requests.Session | None = None) -> list[dict]:
    """Descarrega els indicadors d'origen d'un municipi (foto del darrer any).

    Emet 1 fila per (indicador × nivell): municipi, comarca i Catalunya. L'``any``
    ve de l'atribut ``r`` del GRUP (t68/t75), no de la fulla; el resolem associant
    cada fulla al seu grup pare durant el recorregut.
    """
    sess = session or requests.Session()
    resp = sess.get(
        IDESCAT_EMEX_BASE,
        params={"id": codi6},
        timeout=TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    )
    resp.raise_for_status()
    payload = resp.json()

    # Resol l'any de referència per indicador recorrent l'arbre i recordant el
    # darrer 'r' de grup vist (els grups t68/t75 porten r="2025").
    year_by_indicator = _resolve_years(payload)

    rows: list[dict] = []
    seen: set[str] = set()
    for leaf in _iter_leaves(payload):
        fid = leaf.get("id")
        if fid in ORIGEN_INDICATORS and fid not in seen:
            seen.add(fid)
            levels = _split_levels(leaf.get("v"))
            for nivell in NIVELLS:
                rows.append(
                    {
                        "codi6": codi6,
                        "ine5": codi6[:5],
                        "nivell": nivell,
                        "indicator_id": fid,
                        "indicator": ORIGEN_INDICATORS[fid],
                        "label": leaf.get("calt") or leaf.get("c"),
                        "year": year_by_indicator.get(fid),
                        "value": levels[nivell],
                    }
                )
    return rows


def _resolve_years(payload) -> dict[str, str | None]:
    """Mapa indicador_id -> any de referència, propagant el 'r' del grup pare."""
    years: dict[str, str | None] = {}

    def walk(node, current_year):
        if isinstance(node, dict):
            yr = node.get("r", current_year) if "r" in node else current_year
            if node.get("id") in ORIGEN_INDICATORS and "v" in node:
                years.setdefault(node["id"], yr)
            for value in node.values():
                walk(value, yr)
        elif isinstance(node, list):
            for item in node:
                walk(item, current_year)

    walk(payload, None)
    return years


# --------------------------------------------------------------------------- #
# (B) Població estrangera — sèrie municipal anual (SSV)
# --------------------------------------------------------------------------- #
def _to_float(cell: str) -> float | None:
    """Cel·la SSV → float (decimal amb COMA) o None si confidencial/buida."""
    cell = (cell or "").strip()
    if cell in ("", SSV_NULL, SSV_NULL_INLINE) or cell.startswith("("):
        return None
    cell = cell.replace(".", "").replace(",", ".")  # 1.234,5 -> 1234.5
    try:
        return float(cell)
    except ValueError:
        return None


def fetch_estrangera_serie(codi6: str, session: requests.Session | None = None) -> list[dict]:
    """Descarrega la sèrie 2021→ de població estrangera d'un municipi (SSV).

    La capçalera de dades comença per ``Categoria;`` (la resta són notes/peu). Cada
    fila de dades és ``any;població;estrangers;%;var_abs;var_rel``. El secret
    estadístic dels micromunicipis arriba com a ``(..)``/``..`` → NULL (es respecta).
    """
    sess = session or requests.Session()
    resp = sess.get(
        IDESCAT_POBESTR_BASE,
        params={"b": "6", "geo": f"mun:{codi6}", "f": "ssv"},
        timeout=TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    )
    resp.raise_for_status()
    # SSV en ISO-8859-1 (els accents catalans del peu); les dades són numèriques.
    text = resp.content.decode("iso-8859-1", errors="replace")

    rows: list[dict] = []
    reader = csv.reader(io.StringIO(text), delimiter=";")
    in_data = False
    for parts in reader:
        if not parts:
            continue
        head = parts[0].strip()
        if head.lower().startswith("categoria"):
            in_data = True
            continue
        if not in_data:
            continue
        # Fila de dades: el primer camp ha de ser un any de 4 dígits.
        if not (head.isdigit() and len(head) == 4):
            continue
        any_ = int(head)
        poblacio = _to_float(parts[1]) if len(parts) > 1 else None
        estrangers = _to_float(parts[2]) if len(parts) > 2 else None
        pct = _to_float(parts[3]) if len(parts) > 3 else None
        var_abs = _to_float(parts[4]) if len(parts) > 4 else None
        var_rel = _to_float(parts[5]) if len(parts) > 5 else None
        rows.append(
            {
                "codi6": codi6,
                "ine5": codi6[:5],
                "year": any_,
                "poblacio_total": poblacio,
                "estrangers_total": estrangers,
                "pct_estrangera": pct,
                "estrangers_var_abs": var_abs,
                "estrangers_var_rel": var_rel,
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def run(municipis: dict[str, str] = BERGUEDA, pause: float = 0.2, accumulate: bool = False) -> dict:
    """Ingesta de composició i arrelament dels municipis donats. Idempotent.

    Dues vies Idescat: EMEX (foto) + Població estrangera (sèrie). Escriu dos parquets
    i un sidecar de procedència compartit.

    `accumulate=False` (per defecte): sobreescriu (pilot Berguedà). `accumulate=True`: baixa a
    TROSSOS — carrega els parquets existents, en treu els municipis d'aquest tros (els refresca) i
    hi concatena els nous, perquè trossos successius s'acumulin. Vegeu docs/pla-catalunya-profund.md F1.2b.
    """
    out_dir = raw_path(SOURCE)
    session = requests.Session()

    snapshot_rows: list[dict] = []
    serie_rows: list[dict] = []
    for codi6 in municipis:
        snapshot_rows.extend(fetch_snapshot_municipi(codi6, session=session))
        if pause:
            time.sleep(pause)  # cortesia amb l'API pública
        serie_rows.extend(fetch_estrangera_serie(codi6, session=session))
        if pause:
            time.sleep(pause)

    snap_df = pd.DataFrame(snapshot_rows)
    serie_df = pd.DataFrame(serie_rows)

    snap_file = out_dir / "origen_snapshot.parquet"
    serie_file = out_dir / "estrangera_serie.parquet"
    if accumulate:
        chunk = {str(c) for c in municipis}
        if snap_file.exists():
            prev = pd.read_parquet(snap_file)
            snap_df = pd.concat([prev[~prev["codi6"].astype(str).isin(chunk)], snap_df], ignore_index=True)
        if serie_file.exists():
            prev = pd.read_parquet(serie_file)
            serie_df = pd.concat([prev[~prev["codi6"].astype(str).isin(chunk)], serie_df], ignore_index=True)
    snap_df.to_parquet(snap_file, index=False)
    serie_df.to_parquet(serie_file, index=False)

    # Any de referència de la foto (per al sidecar): el més comú a la snapshot.
    snap_year = (
        str(snap_df["year"].dropna().mode().iloc[0])
        if not snap_df.empty and snap_df["year"].notna().any()
        else None
    )
    serie_years = (
        sorted(int(y) for y in serie_df["year"].dropna().unique())
        if not serie_df.empty
        else []
    )

    write_provenance(
        SOURCE,
        out_dir,
        row_count=len(snap_df) + len(serie_df),
        files=[snap_file.name, serie_file.name],
        query={
            "emex_indicators": ORIGEN_INDICATORS,
            "emex_url": f"{IDESCAT_EMEX_BASE}?id={{codi6}}",
            "poblacioestrangera_url": f"{IDESCAT_POBESTR_BASE}?b=6&geo=mun:{{codi6}}&f=ssv",
            "ids": list(municipis.keys()),
        },
        extra={
            "loader": "requests",
            "n_municipis": int(serie_df["codi6"].astype(str).nunique()) if not serie_df.empty else 0,
            "n_municipis_tros": len(municipis),
            "mode": "accumulate" if accumulate else "replace",
            "snapshot_rows": len(snap_df),
            "snapshot_year": snap_year,
            "snapshot_format": "long (municipi×nivell×indicador); nivells = municipi/comarca/catalunya",
            "serie_rows": len(serie_df),
            "serie_years": serie_years,
            "serie_format": "long (municipi×any); població estrangera (% + variacions)",
            "note": (
                "TRANSFORMACIÓ DEMOGRÀFICA (origen), MAI 'extranjería'. Lectura "
                "ECOLÒGICA (municipi, no individus). El secret estadístic dels "
                "micromunicipis ve de la font com a '(..)' → NULL (es respecta; cal "
                "llindar mínim N i agrupació en grans àrees a transform). La sèrie de "
                "població estrangera ve del Cens anual (INE) des de 2021; el Padró "
                "2000-2020 NO s'ingereix (RUPTURA metodològica el 2021). INE Tempus3 "
                "NO dóna municipal+sèrie per nacionalitat/naixement (només per sexe; "
                "el detall país/edat-per-origen és nacional/CCAA, secret estadístic)."
            ),
        },
    )
    return {
        "source": SOURCE,
        "rows": len(snap_df) + len(serie_df),
        "files": [snap_file.name, serie_file.name],
        "snapshot_rows": len(snap_df),
        "serie_rows": len(serie_df),
        "serie_years": serie_years,
    }


if __name__ == "__main__":
    print(run())
