"""Fixtures sintètiques i deterministes per al motor de convergència.

Construeixen tres parquets minúsculs (contractació, sequera, mart) en un directori
temporal, dissenyats perquè el resultat de cada quadrant i de cada flag sigui
**conegut a mà** —així els tests verifiquen la lògica del motor sense xarxa ni
dependència dels parquets reals del repo.

El cas sintètic (4 municipis, 2 unitats d'explotació) cobreix els 4 quadrants i la
frontera honesta clau: **dins d'una UE la sequera és idèntica** (mateixa zona,
mateixos canvis d'estat) → la sequera no discrimina dins la zona; la variació ve
del turisme.

  UE 'A' (sequera ALTA, seu en alerta/excepcionalitat ~tot el període):
    - M_AT (ALT turisme, ALTA sequera)   → quadrant alt_turisme_alta_sequera (la hipòtesi)
    - M_BT (BAIX turisme, ALTA sequera)  → quadrant baix_turisme_alta_sequera
  UE 'B' (sequera BAIXA, sempre normalitat/prealerta):
    - M_AS (ALT turisme, BAIXA sequera)  → quadrant alt_turisme_baixa_sequera
    - M_BB (BAIX turisme, BAIXA sequera) → quadrant baix_turisme_baixa_sequera

A més M_AT és micromunicipi (poblacio < 300) i M_BT en té molta → exercita
``flag_turisme_poc_fiable``. Només M_AT té contractació de turisme → exercita
``flag_turisme_contractacio_feble`` als altres.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from datapoble_signals.schema import EVENT_COLUMNS

PERIODE_FI_TEST = "2025-05-16"

# ine5 ficticis però amb forma vàlida (5 dígits). No cal que siguin del registre
# real: el motor ancora noms al registre, però per als tests de lògica fem servir
# un registre injectat (vegeu build_sql amb parquets de fixture).
M_AT = "09001"  # alt turisme, alta sequera (UE A) — micromunicipi
M_BT = "09002"  # baix turisme, alta sequera (UE A) — poble gran
M_AS = "09003"  # alt turisme, baixa sequera (UE B)
M_BB = "09004"  # baix turisme, baixa sequera (UE B)


def _seq_event(ine5: str, ue: str, data: str, conf: float) -> dict:
    """Una fila de sequera mínima amb les columnes del contracte EVENT_COLUMNS."""
    base = {c: None for c in EVENT_COLUMNS}
    base.update(
        event_id=f"seq_{ine5}_{data}_{int(conf*100)}",
        ine5=ine5,
        nom_muni=ine5,
        ambit="municipal",
        comarca="Berguedà",
        data=data,
        data_tipus="inici_vigencia",
        font="ACA (fixture)",
        font_url="https://example.test/i5n8-43cw.json",
        tipus_senyal="aigua_sequera",
        fase="realitzacio",
        objecte=f"estat fixture conf={conf}",
        categoria="fet",
        confianca=conf,
        raw_id=ue,
    )
    return base


def _con_event(ine5: str, data: str, eur: float) -> dict:
    """Una fila de contractació de turisme/cultura mínima."""
    base = {c: None for c in EVENT_COLUMNS}
    base.update(
        event_id=f"con_{ine5}_{data}",
        ine5=ine5,
        nom_muni=ine5,
        ambit="municipal",
        comarca="Berguedà",
        data=data,
        data_tipus="adjudicacio",
        font="Contractació (fixture)",
        font_url="https://example.test/ybgg-dgi6.json",
        tipus_senyal="turisme_cultura_events",
        fase="anticipacio",
        objecte="acte cultural fixture",
        categoria="fet",
        confianca=0.9,
        raw_id="x",
    )
    base["import"] = eur
    return base


# --- Sequera sintètica --------------------------------------------------------
# UE 'A': prealerta -> excepcionalitat (0.8) gairebé tot el període -> alta mitjana.
# Els DOS municipis de la UE A comparteixen EXACTAMENT els mateixos canvis (la
# sequera és de zona). UE 'B': normalitat tot el període -> baixa mitjana.
_SEQ_UE_A = [
    ("2021-01-01", 0.4),   # prealerta
    ("2021-03-01", 0.8),   # excepcionalitat (seu fins al final)
]
_SEQ_UE_B = [
    ("2021-01-01", 0.1),   # normalitat tot el període
]

SEQUERA_ROWS: list[dict] = (
    [_seq_event(M_AT, "A", d, c) for d, c in _SEQ_UE_A]
    + [_seq_event(M_BT, "A", d, c) for d, c in _SEQ_UE_A]
    + [_seq_event(M_AS, "B", d, c) for d, c in _SEQ_UE_B]
    + [_seq_event(M_BB, "B", d, c) for d, c in _SEQ_UE_B]
)

# --- Contractació sintètica ---------------------------------------------------
# Només M_AT contracta turisme (3 events). Els altres, res → flag feble.
CONTRACTACIO_ROWS: list[dict] = [
    _con_event(M_AT, "2023-05-10", 10000.0),
    _con_event(M_AT, "2023-05-20", 5000.0),
    _con_event(M_AT, "2024-05-15", 8000.0),
]

# --- Mart sintètic (subconjunt de columnes que el motor llegeix) --------------
# index_turisme: M_AT i M_AS alt (>=50); M_BT i M_BB baix (<50).
MART_ROWS: list[dict] = [
    {"ine5": M_AT, "poblacio": 150, "comarca": "Berguedà",
     "index_turisme": 90.0, "gap_pernocta_pct": 1.2, "confianca": "alta"},
    {"ine5": M_BT, "poblacio": 5000, "comarca": "Berguedà",
     "index_turisme": 25.0, "gap_pernocta_pct": 0.0, "confianca": "mitjana"},
    {"ine5": M_AS, "poblacio": 800, "comarca": "Berguedà",
     "index_turisme": 70.0, "gap_pernocta_pct": 0.8, "confianca": "alta"},
    {"ine5": M_BB, "poblacio": 1200, "comarca": "Berguedà",
     "index_turisme": 30.0, "gap_pernocta_pct": 0.1, "confianca": "mitjana"},
]

# Registre de municipis del cas sintètic (ine5 -> nom net), per injectar al motor.
MUNI_FIXTURE: dict[str, str] = {
    M_AT: "Muni Alt-Alt",
    M_BT: "Muni Baix-Alt",
    M_AS: "Muni Alt-Baix",
    M_BB: "Muni Baix-Baix",
}


def write_fixture_parquets(tmp_dir: Path) -> dict[str, str]:
    """Materialitza els tres parquets sintètics a ``tmp_dir``.

    Retorna les rutes (posix) de contractació, sequera i mart, llestes per a
    ``build_sql``.
    """
    import pandas as pd

    tmp_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    paths: dict[str, str] = {}
    try:
        specs = {
            "contractacio": (
                pd.DataFrame(CONTRACTACIO_ROWS, columns=list(EVENT_COLUMNS)),
                tmp_dir / "fx_contractacio.parquet",
            ),
            "sequera": (
                pd.DataFrame(SEQUERA_ROWS, columns=list(EVENT_COLUMNS)),
                tmp_dir / "fx_sequera.parquet",
            ),
            "mart": (pd.DataFrame(MART_ROWS), tmp_dir / "fx_mart.parquet"),
        }
        for key, (df, path) in specs.items():
            con.register("t", df)
            con.execute(
                "COPY (SELECT * FROM t) TO ? (FORMAT PARQUET)", [str(path)]
            )
            con.unregister("t")
            paths[key] = str(path.as_posix())
    finally:
        con.close()
    return paths
