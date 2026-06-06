"""STUB — Fraccions de residus per municipi (ARC ``69zu-w48s``), èmfasi VIDRE.

Proxy de **turisme / hostaleria** per a l'afinament "pernocta vs excursionista de
dia" de l'indicador població real vs padró (vegeu la secció *Fonts per a turisme /
excursionisme* a ``docs/poblacio-real-fonts.md``).

⚠️ **Estat: STUB. NO cablejat a ``python -m datapoble_ingestion all``.** Existeix
documentat però inert fins que Talaia validi l'ús del vidre a l'indicador. Igual
que ``icaen_consum.py`` ho va estar abans de cablejar-se.

**Important — no cal descàrrega nova.** El dataset és **el mateix** ``69zu-w48s``
que ``residus.py`` ja ingereix, i la raw de ``residus`` **ja conté totes les
columnes de fracció** (``vidre``, ``paper_i_cartr``, ``envasos_lleugers``,
``mat_ria_org_nica`` = FORM, ``poda_i_jardineria``, ``total_recollida_selectiva``,
``suma_fracci_resta``, …). Per tant la via recomanada és **exposar aquestes
columnes a la capa transform** a partir de ``data/raw/residus`` — no re-baixar.

Aquest mòdul només ofereix un *fetch focalitzat* opcional (subconjunt de columnes
de fracció) per a exploració aïllada, amb el mateix client SODA i el mateix patró
dlt que ``residus.py``. La selecció d'any vigent i les derivades (vidre/càpita,
vidre/FORM, z-score comarcal) es fan a transform, no aquí (fidelitat a la font).

Fets verificats en viu (2026-06-06), motiu de la tria del VIDRE:
  · ``codi_municipi`` = INE5 → join directe amb ``mart_municipi.ine5``.
  · Cobertura **2000–2024**, anual; el pilot 2024 té ``vidre`` no-null a **31/31**
    municipis del Berguedà (sobreviu al secret estadístic fins a Castellar, 164 hab).
  · El **vidre per càpita** separa micromunicipis turístics (Gósol 149,4 kg/hab,
    Castellar de n'Hug 107,7) de la capital estable (Berga 27,6); mediana comarcal
    49,8. És el proxy d'hostaleria (ampolles de bar/restaurant) més directe i net.
  · Granularitat **anual** — NO capta estacionalitat (cap font municipal oberta ho fa).
"""
from __future__ import annotations

import dlt

from .config import COMARCA_PILOT, RAW_DIR, SOURCES
from .provenance import write_provenance
from .socrata import fetch_all

# Reutilitza l'entrada de configuració de ``residus`` (mateix dataset 69zu-w48s).
SOURCE = "residus"
TABLE = "residus_fraccions"

# Columnes de fracció rellevants com a proxy de presència/turisme. ``vidre`` és
# l'estrella (hostaleria); ``mat_ria_org_nica`` (FORM) escala amb residents que
# cuinen → el ràtio vidre/FORM separa hostaleria de dia de residència estable.
FRACCIONS = (
    "any",
    "codi_municipi",
    "municipi",
    "comarca",
    "poblaci",
    "vidre",
    "paper_i_cartr",
    "envasos_lleugers",
    "mat_ria_org_nica",
    "total_recollida_selectiva",
    "suma_fracci_resta",
    "generaci_residus_municipal",
)


@dlt.resource(name=TABLE, write_disposition="replace")
def residus_fraccions_resource(where: str):
    """Files crues amb només les columnes de fracció per al filtre donat."""
    select = ",".join(FRACCIONS)
    yield from fetch_all(SOURCES[SOURCE]["url"], where=where, select=select)


def run(comarca: str = COMARCA_PILOT) -> dict:
    """STUB. Ingesta focalitzada de fraccions de residus del Berguedà. Idempotent.

    No s'invoca des de l'``all``; és per a exploració manual mentre l'indicador no
    estigui validat. Materialitza a ``data/raw/residus_fraccions``.
    """
    where = f"comarca='{comarca}'"
    out_dir = RAW_DIR / TABLE
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="datapoble_residus_fraccions",
        destination=dlt.destinations.filesystem(bucket_url=RAW_DIR.as_uri()),
        dataset_name=TABLE,
    )
    load_info = pipeline.run(
        residus_fraccions_resource(where),
        loader_file_format="parquet",
    )

    row_count = _row_count(pipeline, TABLE)
    files = _parquet_files(out_dir)
    write_provenance(
        TABLE,
        out_dir,
        row_count=row_count,
        files=files,
        query={"$where": where, "$select": ",".join(FRACCIONS)},
        extra={
            "loader": "dlt",
            "dlt_load_id": str(load_info.loads_ids[0]) if load_info.loads_ids else None,
            "dataset_id": SOURCES[SOURCE]["dataset_id"],
            "note": (
                "STUB no cablejat a `all`; fraccions ja presents a la raw de `residus` "
                "(mateix dataset 69zu-w48s) — preferible exposar-les a transform. "
                "VIDRE = proxy hostaleria/turisme. Vegeu docs/poblacio-real-fonts.md."
            ),
        },
    )
    return {"source": TABLE, "rows": row_count, "files": files}


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
