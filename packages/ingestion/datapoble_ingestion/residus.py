"""Connector Residus municipals — ARC (Socrata ``69zu-w48s``).

Una fila per municipi × any. Conté ``kg_hab_any`` (proxy de càrrega real /
població fantasma). Filtra el Berguedà per nom de comarca i carrega amb **dlt**.
La selecció de l'any vigent (2024) es fa a la capa transform, no aquí: la raw
guarda la sèrie completa per traçabilitat.
"""
from __future__ import annotations

import dlt

from .config import RAW_DIR, SOURCES
from .provenance import write_provenance
from .socrata import fetch_all

SOURCE = "residus"
TABLE = "residus_municipals"


@dlt.resource(name=TABLE, write_disposition="replace")
def residus_resource(where: str | None):
    yield from fetch_all(SOURCES[SOURCE]["url"], where=where)


def run(comarca: str | None = None) -> dict:
    """Ingesta de residus (sèrie completa). `comarca=None` → TOT CATALUNYA (sense filtre);
    passa un nom de comarca per acotar (p. ex. el pilot del Berguedà). Idempotent."""
    where = f"comarca='{comarca}'" if comarca else None
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = RAW_DIR / SOURCE

    pipeline = dlt.pipeline(
        pipeline_name="datapoble_residus",
        destination=dlt.destinations.filesystem(bucket_url=RAW_DIR.as_uri()),
        dataset_name=SOURCE,
    )
    load_info = pipeline.run(
        residus_resource(where),
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
        extra={"loader": "dlt", "dlt_load_id": str(load_info.loads_ids[0]) if load_info.loads_ids else None},
    )
    return {"source": SOURCE, "rows": row_count, "files": files}


def _row_count(pipeline, table: str) -> int:
    try:
        with pipeline.sql_client() as c:
            return c.execute_sql(f"SELECT count(*) FROM {table}")[0][0]
    except Exception:  # noqa: BLE001
        return -1


def _parquet_files(out_dir) -> list[str]:
    return sorted(p.relative_to(out_dir).as_posix() for p in out_dir.rglob("*.parquet"))


if __name__ == "__main__":
    print(run())
