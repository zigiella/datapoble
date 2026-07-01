"""Smoke tests for the Berguedà geospatial substrate.

Every asserted number traces to a committed source file — no invented values.
"""

import json

import pytest

from datapoble_geo_rag.build import PERNOCTA_JSON, build, name_search, neighbors

VALID_REGISTERS = {"oficial", "senyal_mes", "senyal_menys", "soroll"}


@pytest.fixture(scope="module")
def conn():
    c = build(None)  # in-memory
    yield c
    c.close()


def test_exactly_31(conn):
    assert conn.execute("SELECT COUNT(*) FROM municipi").fetchone()[0] == 31


def test_no_indeterminat(conn):
    bad = conn.execute(
        "SELECT ine5, nom FROM municipi WHERE register = 'indeterminat'"
    ).fetchall()
    assert not bad, f"indeterminat munis present (should be zero): {bad}"


def test_every_register_valid(conn):
    regs = conn.execute("SELECT DISTINCT register FROM municipi").fetchall()
    got = {r[0] for r in regs}
    assert got <= VALID_REGISTERS, f"unexpected register values: {got - VALID_REGISTERS}"


def test_register_counts_sum_to_31(conn):
    split = dict(
        conn.execute("SELECT register, COUNT(*) FROM municipi GROUP BY register").fetchall()
    )
    assert sum(split.values()) == 31, split
    assert all(r in VALID_REGISTERS for r in split), split


def test_bands_and_sigma_and_estimacio(conn):
    rows = conn.execute(
        "SELECT ine5, rang_baix, rang_alt, sigma, estimacio FROM municipi"
    ).fetchall()
    assert len(rows) == 31
    for ine5, rb, ra, sigma, est in rows:
        assert rb < ra, f"{ine5}: rang_baix {rb} !< rang_alt {ra}"
        assert sigma > 0, f"{ine5}: sigma {sigma} !> 0"
        assert est > 0, f"{ine5}: estimacio {est} !> 0"


def test_geometry_present(conn):
    missing = conn.execute(
        "SELECT ine5 FROM municipi WHERE geom_geojson IS NULL"
    ).fetchall()
    assert not missing, f"munis missing geometry: {missing}"


def test_name_search_exact(conn):
    # Berga is the comarcal capital (08022), an exact proper name.
    res = name_search(conn, "Berga")
    assert res, "name_search('Berga') returned nothing"
    assert res[0][0] == "08022", f"top hit should be Berga/08022, got {res[0]}"


def test_neighbors_within_31(conn):
    spatial = conn.execute(
        "SELECT value FROM _substrate_meta WHERE key='spatial'"
    ).fetchone()[0]
    the_31 = {r[0] for r in conn.execute("SELECT ine5 FROM municipi").fetchall()}
    nb = neighbors(conn, "08022")  # Berga
    if spatial != "1":
        assert nb is None
        pytest.skip("spatial extension unavailable on this box")
    assert nb is not None
    assert len(nb) >= 1, "Berga should touch at least one Berguedà muni"
    for ine5, _nom in nb:
        assert ine5 in the_31, f"neighbour {ine5} outside the 31"


def test_estimacio_bands_byte_match_source(conn):
    """Built estimacio / rang_baix / rang_alt must byte-match pernocta-catalunya.json."""
    with open(PERNOCTA_JSON, encoding="utf-8") as f:
        munis = json.load(f)["munis"]

    for ine5 in ("08022", "08024", "08045"):  # Berga (oficial), Borredà, Capolat (<1000)
        src = munis[ine5]
        built = conn.execute(
            "SELECT estimacio, rang_baix, rang_alt FROM municipi WHERE ine5 = ?",
            [ine5],
        ).fetchone()
        assert built is not None, f"{ine5} not in substrate"
        assert built[0] == float(src["estimacio"]), f"{ine5} estimacio {built[0]} != {src['estimacio']}"
        assert built[1] == float(src["rang_baix"]), f"{ine5} rang_baix {built[1]} != {src['rang_baix']}"
        assert built[2] == float(src["rang_alt"]), f"{ine5} rang_alt {built[2]} != {src['rang_alt']}"
