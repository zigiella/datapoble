"""Build the DuckDB geospatial substrate for the 31 Berguedà municipalities.

Every value traces to a committed source file (see DATA_CARD.md). No invented numbers.

Sources (repo-relative):
- data/web/pernocta-catalunya.json        — pernocta bands + etca_oficial per ine5.
- data/territorial/senyal_sub1000.csv      — register (senyal_mes|senyal_menys|soroll) for <1000.
- data/web/municipis-mirall.json           — twins (ine5 -> [[mirror, distance, marker], ...]).
- packages/web/static/geo/bergueda-municipis.geojson — geometry + the canonical 31 ine5 set.
- data/marts/mart_consum_electric.parquet  — ICAEN domestic-electricity multi-year series.

Design notes:
- The set of "the 31 Berguedà munis" is defined by the tracked bergueda-municipis.geojson.
- REGISTER RULE (computed, never hardcoded):
    etca_oficial not null           -> 'oficial'
    else lookup in senyal_sub1000   -> its 'registre'
    else                            -> 'indeterminat' (counted, never dropped)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import duckdb

# Repo root resolved portably: this file lives at
# <repo>/packages/geo-rag/src/datapoble_geo_rag/build.py -> parents[3] is <repo>/packages/geo-rag
# so we need parents[4] for the repo root... but we keep sources package-relative below.
_PKG_ROOT = Path(__file__).resolve().parents[2]        # packages/geo-rag
_REPO_ROOT = Path(__file__).resolve().parents[4]        # repo root

PERNOCTA_JSON = _REPO_ROOT / "data" / "web" / "pernocta-catalunya.json"
SENYAL_CSV = _REPO_ROOT / "data" / "territorial" / "senyal_sub1000.csv"
TWINS_JSON = _REPO_ROOT / "data" / "web" / "municipis-mirall.json"
GEOJSON = _REPO_ROOT / "packages" / "web" / "static" / "geo" / "bergueda-municipis.geojson"
ICAEN_PARQUET = _REPO_ROOT / "data" / "marts" / "mart_consum_electric.parquet"

DEFAULT_DB_PATH = _PKG_ROOT / "data" / "bergueda.duckdb"

# Comarca is a constant here: the geojson is the Berguedà municipal file by construction.
COMARCA = "Berguedà"

# ICAEN parquet stores the domestic sector as this string (verified against the committed file).
DOMESTIC_SECTOR = "USOS DOMESTICS"


def _load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _try_extension(conn: duckdb.DuckDBPyConnection, name: str) -> bool:
    """Install+load a DuckDB extension; return True on success (offline-safe)."""
    try:
        conn.execute(f"INSTALL {name};")
        conn.execute(f"LOAD {name};")
        return True
    except Exception:
        return False


def build(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Build the substrate and return an open DuckDB connection.

    If db_path is None, builds an in-memory database.
    """
    conn = duckdb.connect(db_path if db_path is not None else ":memory:")

    spatial_ok = _try_extension(conn, "spatial")
    fts_ok = _try_extension(conn, "fts")

    # ---- Load committed sources into Python ----
    pernocta = _load_json(PERNOCTA_JSON)["munis"]

    senyal = {}
    with open(SENYAL_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            senyal[row["ine5"]] = row["registre"]

    geo = _load_json(GEOJSON)
    features = geo["features"]
    the_31 = [f["properties"]["ine5"] for f in features]
    geom_by_ine = {
        f["properties"]["ine5"]: json.dumps(f["geometry"], ensure_ascii=False) for f in features
    }

    # ---- Compute the municipi rows (register rule applied here) ----
    rows = []
    indeterminat = []
    for ine5 in the_31:
        p = pernocta.get(ine5)
        if p is None:
            # A muni in the geometry but absent from pernocta: cannot fabricate bands.
            indeterminat.append(ine5)
            continue
        etca = p.get("etca_oficial")
        if etca is not None:
            register = "oficial"
        elif ine5 in senyal:
            register = senyal[ine5]
        else:
            register = "indeterminat"
            indeterminat.append(ine5)

        estimacio = float(p["estimacio"])
        rang_baix = float(p["rang_baix"])
        rang_alt = float(p["rang_alt"])
        sigma = (rang_alt - rang_baix) / 2.0
        rang_rel = (rang_alt - rang_baix) / estimacio if estimacio else None
        rows.append(
            {
                "ine5": ine5,
                "nom": p["nom"],
                "comarca": COMARCA,
                "tipus": p.get("tipus"),
                "padro": p.get("padro"),
                "estimacio": estimacio,
                "rang_baix": rang_baix,
                "rang_alt": rang_alt,
                "sigma": sigma,
                "rang_rel": rang_rel,
                "etca_oficial": float(etca) if etca is not None else None,
                "register": register,
                "geom_geojson": geom_by_ine.get(ine5),
            }
        )

    # ---- Create the municipi table ----
    geom_col_ddl = "geom GEOMETRY," if spatial_ok else ""
    conn.execute(
        f"""
        CREATE OR REPLACE TABLE municipi (
            ine5 VARCHAR PRIMARY KEY,
            nom VARCHAR,
            comarca VARCHAR,
            tipus VARCHAR,
            padro INTEGER,
            estimacio DOUBLE,
            rang_baix DOUBLE,
            rang_alt DOUBLE,
            sigma DOUBLE,
            rang_rel DOUBLE,
            etca_oficial DOUBLE,
            register VARCHAR,
            {geom_col_ddl}
            geom_geojson VARCHAR
        );
        """
    )

    insert_cols = (
        "ine5, nom, comarca, tipus, padro, estimacio, rang_baix, rang_alt, sigma, "
        "rang_rel, etca_oficial, register, geom_geojson"
    )
    conn.executemany(
        f"INSERT INTO municipi ({insert_cols}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                r["ine5"], r["nom"], r["comarca"], r["tipus"], r["padro"], r["estimacio"],
                r["rang_baix"], r["rang_alt"], r["sigma"], r["rang_rel"], r["etca_oficial"],
                r["register"], r["geom_geojson"],
            )
            for r in rows
        ],
    )

    # Populate the native geometry column from the GeoJSON text (spatial only).
    if spatial_ok:
        conn.execute(
            "UPDATE municipi SET geom = ST_GeomFromGeoJSON(geom_geojson) WHERE geom_geojson IS NOT NULL"
        )

    # ---- Full-text index on proper names ----
    if fts_ok:
        try:
            conn.execute("PRAGMA create_fts_index('municipi', 'ine5', 'nom', overwrite=1)")
        except Exception:
            fts_ok = False

    # ---- twin table ----
    twins = _load_json(TWINS_JSON)
    twin_rows = []
    for ine5 in the_31:
        for rank, entry in enumerate(twins.get(ine5, [])):
            mirror, distance = entry[0], entry[1]
            twin_rows.append((ine5, rank, mirror, float(distance)))
    conn.execute(
        """
        CREATE OR REPLACE TABLE twin (
            ine5 VARCHAR,
            rank INTEGER,
            ine5_mirror VARCHAR,
            distance DOUBLE
        );
        """
    )
    if twin_rows:
        conn.executemany(
            "INSERT INTO twin (ine5, rank, ine5_mirror, distance) VALUES (?,?,?,?)", twin_rows
        )

    # ---- icaen_serie table (domestic sector) ----
    conn.execute(
        """
        CREATE OR REPLACE TABLE icaen_serie (
            ine5 VARCHAR,
            "any" INTEGER,
            kwh_domestic DOUBLE
        );
        """
    )
    try:
        conn.execute(
            """
            INSERT INTO icaen_serie (ine5, "any", kwh_domestic)
            SELECT ine5, any_consum, consum_kwh_domestic
            FROM read_parquet(?)
            WHERE sector = ? AND ine5 IN (SELECT ine5 FROM municipi)
            """,
            [str(ICAEN_PARQUET), DOMESTIC_SECTOR],
        )
    except Exception:
        pass  # optional for 0a; do not fail the build

    # ---- Availability + split metadata table (traceable, queryable) ----
    conn.execute(
        """
        CREATE OR REPLACE TABLE _substrate_meta (key VARCHAR, value VARCHAR);
        """
    )
    # ---- Semantic embeddings (Phase 0b) ----
    # Load the COMMITTED base-embeddings artifact into municipi_emb IF it exists.
    # Torch-free: read_parquet only. Absent artifact -> skip silently (0a still works).
    from .search import load_embeddings

    emb_ok = load_embeddings(conn)

    conn.executemany(
        "INSERT INTO _substrate_meta VALUES (?,?)",
        [
            ("spatial", "1" if spatial_ok else "0"),
            ("fts", "1" if fts_ok else "0"),
            ("embeddings", "1" if emb_ok else "0"),
            ("indeterminat_count", str(len(indeterminat))),
            ("indeterminat_ine5", ",".join(indeterminat)),
        ],
    )

    return conn


def name_search(conn: duckdb.DuckDBPyConnection, q: str):
    """Search municipi by proper name. Uses FTS if available, else LIKE.

    Returns a list of (ine5, nom) tuples ordered by relevance.
    """
    fts = conn.execute("SELECT value FROM _substrate_meta WHERE key='fts'").fetchone()
    if fts and fts[0] == "1":
        try:
            return conn.execute(
                """
                SELECT ine5, nom
                FROM (
                    SELECT ine5, nom, fts_main_municipi.match_bm25(ine5, ?) AS score
                    FROM municipi
                ) t
                WHERE score IS NOT NULL
                ORDER BY score DESC
                """,
                [q],
            ).fetchall()
        except Exception:
            pass
    # Fallback: case-insensitive LIKE.
    return conn.execute(
        "SELECT ine5, nom FROM municipi WHERE lower(nom) LIKE '%' || lower(?) || '%' ORDER BY nom",
        [q],
    ).fetchall()


def neighbors(conn: duckdb.DuckDBPyConnection, ine5: str):
    """Spatial neighbours (touching polygons) of a muni within the 31.

    Returns a list of (ine5, nom) if spatial is available, else None.
    """
    spatial = conn.execute("SELECT value FROM _substrate_meta WHERE key='spatial'").fetchone()
    if not (spatial and spatial[0] == "1"):
        return None
    return conn.execute(
        """
        SELECT b.ine5, b.nom
        FROM municipi a
        JOIN municipi b ON b.ine5 <> a.ine5
        WHERE a.ine5 = ?
          AND ST_Intersects(a.geom, b.geom)
        ORDER BY b.nom
        """,
        [ine5],
    ).fetchall()


def main() -> None:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DEFAULT_DB_PATH.exists():
        DEFAULT_DB_PATH.unlink()
    conn = build(str(DEFAULT_DB_PATH))

    total = conn.execute("SELECT COUNT(*) FROM municipi").fetchone()[0]
    split = conn.execute(
        "SELECT register, COUNT(*) FROM municipi GROUP BY register ORDER BY register"
    ).fetchall()
    with_geom = conn.execute(
        "SELECT COUNT(*) FROM municipi WHERE geom_geojson IS NOT NULL"
    ).fetchone()[0]
    with_sigma = conn.execute("SELECT COUNT(*) FROM municipi WHERE sigma > 0").fetchone()[0]
    meta = dict(conn.execute("SELECT key, value FROM _substrate_meta").fetchall())
    n_twin = conn.execute("SELECT COUNT(*) FROM twin").fetchone()[0]
    n_icaen = conn.execute("SELECT COUNT(*) FROM icaen_serie").fetchone()[0]

    print(f"Substrate built -> {DEFAULT_DB_PATH}")
    print(f"  total munis:      {total}")
    print("  register split:")
    for reg, n in split:
        print(f"    {reg:14s} {n}")
    print(f"  with geometry:    {with_geom}")
    print(f"  with sigma>0:     {with_sigma}")
    print(f"  indeterminat:     {meta.get('indeterminat_count')} "
          f"[{meta.get('indeterminat_ine5') or '-'}]")
    print(f"  twin rows:        {n_twin}")
    print(f"  icaen_serie rows: {n_icaen}")
    print(f"  spatial ext:      {'yes' if meta.get('spatial') == '1' else 'no'}")
    print(f"  fts ext:          {'yes' if meta.get('fts') == '1' else 'no'}")
    conn.close()


if __name__ == "__main__":
    main()
