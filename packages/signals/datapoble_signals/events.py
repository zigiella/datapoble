"""Escriptura de la taula ``events`` a parquet **via DuckDB**.

La taula ``events`` és el contracte de la capa (vegeu ``schema.py``). Aquí
materialitzem la llista d'events normalitzats a un parquet tipat: la columna
``data`` es força a ``DATE`` i ``import``/``confianca`` a tipus numèrics. Usem
DuckDB (no pandas-to-parquet directe) perquè el cast de tipus i el COPY a parquet
quedin explícits i reproduïbles, com a la capa transform de Sondeig.
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from .config import events_path
from .schema import EVENT_COLUMNS

DEFAULT_PARQUET = "events_bergueda.parquet"


def events_to_frame(events: list[dict]) -> pd.DataFrame:
    """Llista d'events → DataFrame amb les columnes del contracte en ordre."""
    df = pd.DataFrame(events, columns=list(EVENT_COLUMNS))
    return df


def write_events_table(
    events: list[dict], *, parquet_name: str = DEFAULT_PARQUET
) -> dict:
    """Materialitza els events a ``data/events/<parquet_name>`` via DuckDB.

    Retorna un resum: fitxer, recompte, i un breakdown per ``ambit`` i
    ``tipus_senyal`` (per a verificació ràpida de les àncores).
    """
    df = events_to_frame(events)
    out = events_path(parquet_name)

    con = duckdb.connect()
    try:
        con.register("ev", df)
        # Cast explícit: data -> DATE, import/confianca -> DOUBLE. La resta VARCHAR.
        con.execute(
            """
            CREATE TABLE events AS
            SELECT
                CAST(event_id     AS VARCHAR) AS event_id,
                CAST(ine5         AS VARCHAR) AS ine5,
                CAST(nom_muni     AS VARCHAR) AS nom_muni,
                CAST(ambit        AS VARCHAR) AS ambit,
                CAST(comarca      AS VARCHAR) AS comarca,
                TRY_CAST(data     AS DATE)    AS data,
                CAST(data_tipus   AS VARCHAR) AS data_tipus,
                CAST(font         AS VARCHAR) AS font,
                CAST(font_url     AS VARCHAR) AS font_url,
                CAST(tipus_senyal AS VARCHAR) AS tipus_senyal,
                CAST(fase         AS VARCHAR) AS fase,
                CAST(objecte      AS VARCHAR) AS objecte,
                TRY_CAST("import" AS DOUBLE)  AS "import",
                CAST(categoria    AS VARCHAR) AS categoria,
                TRY_CAST(confianca AS DOUBLE) AS confianca,
                CAST(dataset_id   AS VARCHAR) AS dataset_id,
                CAST(font_clau    AS VARCHAR) AS font_clau,
                CAST(cpv          AS VARCHAR) AS cpv,
                CAST(raw_id       AS VARCHAR) AS raw_id
            FROM ev
            """
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        con.execute(
            "COPY events TO ? (FORMAT PARQUET)", [str(out)]
        )
        n = con.execute("SELECT count(*) FROM events").fetchone()[0]
        by_ambit = dict(
            con.execute(
                "SELECT ambit, count(*) FROM events GROUP BY ambit ORDER BY 1"
            ).fetchall()
        )
        by_tipus = dict(
            con.execute(
                "SELECT tipus_senyal, count(*) FROM events GROUP BY tipus_senyal ORDER BY 2 DESC"
            ).fetchall()
        )
    finally:
        con.close()

    return {
        "parquet": str(Path(out).as_posix()),
        "rows": int(n),
        "by_ambit": {k: int(v) for k, v in by_ambit.items()},
        "by_tipus_senyal": {k: int(v) for k, v in by_tipus.items()},
    }


def read_events_table(parquet_name: str = DEFAULT_PARQUET) -> pd.DataFrame:
    """Llegeix la taula d'events des del parquet (per a tests/anàlisi)."""
    out = events_path(parquet_name)
    return duckdb.connect().execute(
        "SELECT * FROM read_parquet(?)", [str(out)]
    ).df()
