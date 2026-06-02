"""Connector RTC — Registre de Turisme de Catalunya (Socrata ``t2h3-cgys``).

Una fila per establiment d'allotjament. Filtra el Berguedà (codi comarca 14).
Carrega amb **dlt** (destination=filesystem, parquet) i escriu procedència.

Nota RGPD: el dataset porta dades del titular (nom, cognoms, CIF). Aquí NO les
descartem a la capa raw (fidelitat a la font), però la mart agregada (transform)
no n'arrossega cap; el producte només exposa recomptes per municipi.
"""
from __future__ import annotations

import dlt

from .config import COMARCA_CODI_PILOT, RAW_DIR, SOURCES
from .provenance import write_provenance
from .socrata import fetch_all

SOURCE = "rtc"
TABLE = "rtc_establiments"


@dlt.resource(name=TABLE, write_disposition="replace")
def rtc_resource(where: str):
    """Files crues de RTC per al filtre donat."""
    yield from fetch_all(SOURCES[SOURCE]["url"], where=where)


def run(comarca_codi: str = COMARCA_CODI_PILOT) -> dict:
    """Executa la ingesta RTC del Berguedà. Idempotent (replace)."""
    where = f"codi_comarca_idescat='{comarca_codi}'"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = RAW_DIR / SOURCE  # data/raw/rtc/ — el crea dlt

    # bucket=data/raw, dataset=rtc -> parquet a data/raw/rtc/rtc_establiments/
    pipeline = dlt.pipeline(
        pipeline_name="datapoble_rtc",
        destination=dlt.destinations.filesystem(bucket_url=RAW_DIR.as_uri()),
        dataset_name=SOURCE,
    )
    load_info = pipeline.run(
        rtc_resource(where),
        loader_file_format="parquet",
    )

    # Recompte real des de l'estat del pipeline.
    row_count = _row_count(pipeline, TABLE)
    files = _parquet_files(out_dir)
    write_provenance(
        SOURCE,
        out_dir,
        row_count=row_count,
        files=files,
        query={"$where": where},
        extra={"loader": "dlt", "dlt_load_id": str(load_info.loads_ids[0]) if load_info.loads_ids else None},
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
