"""Connector consum elèctric municipal — ICAEN (Socrata ``8idm-becu``).

Proxy de **presència humana real** per a l'indicador "població real vs padró"
(vegeu ``docs/poblacio-real-fonts.md``). Una fila per municipi × any × sector.

Estat: **actiu**. Cablejat a ``python -m datapoble_ingestion all`` (mateix patró
que ``residus.py``). La capa transform (``stg_icaen_consum`` → ``mart_consum_electric``)
selecciona el sector USOS DOMÈSTICS i materialitza la sèrie 2013–2024 per ``ine5``.

Fets verificats en viu (2026-06-04, reconfirmats 2026-06-05), motiu de la tria:
  · ``cdmun`` = INE5 (join directe amb ``mart_municipi.ine5``, sense crosswalk).
  · Cobertura 2013–2024, anual, latència ~1 any.
  · 6 sectors; el sector **7 = USOS DOMÈSTICS** és el rellevant per a presència i
    **sobreviu al secret estadístic fins i tot a Castellar (166 hab)** — on els
    sectors industrials surten NULL amb ``observacions='Dada subjecta a secret
    estadístic'``. Per això no filtrem el sector a la raw (fidelitat a la font);
    la selecció ``codi_sector='7'`` es farà a la capa transform.

La selecció de sector i d'any vigent es deixa a transform: la raw guarda la sèrie
completa de tots els sectors del Berguedà per traçabilitat.
"""
from __future__ import annotations

import dlt

from .config import RAW_DIR, SOURCES
from .provenance import write_provenance
from .socrata import fetch_all

SOURCE = "icaen_consum"
TABLE = "consum_electric_municipal"


@dlt.resource(name=TABLE, write_disposition="replace")
def icaen_consum_resource(where: str | None):
    """Files crues de consum elèctric per al filtre donat (tots els sectors; o totes si None)."""
    yield from fetch_all(SOURCES[SOURCE]["url"], where=where)


def run(comarca: str | None = None) -> dict:
    """Ingesta de consum elèctric. `comarca=None` → TOT CATALUNYA; passa un nom de comarca per
    acotar (p. ex. el Berguedà). Idempotent (replace).

    El camp ``comarca`` al dataset ``8idm-becu`` ve en MAJÚSCULES i sense accents
    (``BERGUEDA``), a diferència d'altres datasets — per això normalitzem aquí.
    """
    if comarca:
        comarca_norm = (
            comarca.upper()
            .replace("À", "A").replace("Á", "A").replace("È", "E").replace("É", "E")
            .replace("Í", "I").replace("Ò", "O").replace("Ó", "O").replace("Ú", "U")
        )
        where = f"comarca='{comarca_norm}'"
    else:
        where = None
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = RAW_DIR / SOURCE

    pipeline = dlt.pipeline(
        pipeline_name="datapoble_icaen_consum",
        destination=dlt.destinations.filesystem(bucket_url=RAW_DIR.as_uri()),
        dataset_name=SOURCE,
    )
    load_info = pipeline.run(
        icaen_consum_resource(where),
        loader_file_format="parquet",
    )

    row_count = _row_count(pipeline, TABLE)
    files = _parquet_files(out_dir)
    write_provenance(
        SOURCE,
        out_dir,
        row_count=row_count,
        files=files,
        query={"$where": where},
        extra={
            "loader": "dlt",
            "dlt_load_id": str(load_info.loads_ids[0]) if load_info.loads_ids else None,
            "note": "cablejat a `all`; raw = tots els sectors; sector USOS DOMÈSTICS (7) = proxy de presència (selecció a transform)",
        },
    )
    return {"source": SOURCE, "rows": row_count, "files": files}


def _row_count(pipeline, table: str) -> int:
    try:
        with pipeline.sql_client() as c:
            return c.execute_sql(f"SELECT count(*) FROM {table}")[0][0]
    except Exception:  # noqa: BLE001 — el filesystem destination pot no tenir sql_client
        return -1


def _parquet_files(out_dir) -> list[str]:
    return sorted(p.relative_to(out_dir).as_posix() for p in out_dir.rglob("*.parquet"))


if __name__ == "__main__":
    print(run())
