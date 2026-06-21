"""Connector electoral — Processos electorals · Vots (Socrata ``ntc4-rnwr``).

Una fila per (convocatòria × territori × candidatura). Filtra el **nivell
Municipi** (el dataset també porta Districte/Secció/Mesa) i els municipis del
**Berguedà**, per a les convocatòries del pilot (Parlament 2024 ``A20241`` i
2021 ``A20211``). Carrega amb **dlt** (parquet) i escriu procedència.

Capa 🔴 PRIVADA al registre de fonts, però el producte n'exposa només **agregats
ecològics** per municipi (vegeu mart_electoral): cap dada individual.

Nota de codis (verificat en viu 2026-06-02): ``territori_codi`` d'aquest dataset
NO és l'INE canònic — usa el mateix codi Idescat-derivat (5 dígits) que RTC /
residus / EMEX. Gósol = ``25100`` aquí i a mart_municipi (coincideixen). Per això
el filtre reusa ``BERGUEDA_INE5`` i el crosswalk Gósol és identitat.
"""
from __future__ import annotations

import dlt

from .config import ELECCIONS_PILOT, RAW_DIR, SOURCES
from .provenance import write_provenance
from .socrata import fetch_all

SOURCE = "electoral"
TABLE = "electoral_vots"

# Camps que ens interessen (la resta —logotips, colors, escons— no entra a la mart).
SELECT = (
    "id_eleccio,nom_eleccio,territori_codi,territori_nom,"
    "candidatura_codi,candidatura_denominacio,candidatura_sigles,vots"
)


def _where(eleccions: list[str], ine5: list[str] | None) -> str:
    elec = ",".join(f"'{e}'" for e in eleccions)
    base = f"id_eleccio in ({elec}) and nom_nivell_territorial='Municipi'"
    if not ine5:  # tot Catalunya: tots els municipis d'aquestes convocatòries
        return base
    codes = ",".join(f"'{c}'" for c in ine5)
    return f"{base} and territori_codi in ({codes})"


@dlt.resource(name=TABLE, write_disposition="replace")
def electoral_resource(where: str):
    """Files crues d'``ntc4-rnwr`` per al filtre donat (nivell Municipi)."""
    yield from fetch_all(SOURCES[SOURCE]["url"], where=where, select=SELECT)


def run(
    eleccions: list[str] = ELECCIONS_PILOT,
    municipis_ine5: dict[str, str] | None = None,
) -> dict:
    """Ingesta electoral (nivell Municipi). `municipis_ine5=None` → TOTS els munis de Catalunya
    per a aquestes convocatòries; passa un dict ine5→nom per acotar (p. ex. el Berguedà). Idempotent."""
    where = _where(eleccions, list(municipis_ine5.keys()) if municipis_ine5 else None)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = RAW_DIR / SOURCE

    pipeline = dlt.pipeline(
        pipeline_name="datapoble_electoral",
        destination=dlt.destinations.filesystem(bucket_url=RAW_DIR.as_uri()),
        dataset_name=SOURCE,
    )
    load_info = pipeline.run(
        electoral_resource(where),
        loader_file_format="parquet",
    )

    row_count = _row_count(pipeline, TABLE)
    files = _parquet_files(out_dir)
    write_provenance(
        SOURCE,
        out_dir,
        row_count=row_count,
        files=files,
        query={"$where": where, "$select": SELECT, "eleccions": eleccions},
        extra={
            "loader": "dlt",
            "dlt_load_id": str(load_info.loads_ids[0]) if load_info.loads_ids else None,
            "nivell": "Municipi",
            "lectura": "ecològica (no individual)",
        },
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
