"""Catalan natural-language descriptions per municipality — TORCH-FREE.

One approved description per muni, keyed by the `register` computed in build.py.
These strings are the *documents* that get embedded (Phase 0b). They invent nothing
beyond the fields already in the `municipi` table: nom, tipus, estimacio, rang_baix,
rang_alt, padro, etca_oficial, register.

The templates are fixed and reviewed. Numbers render as integers; `tipus` has its
underscores replaced by spaces for readability.
"""

from __future__ import annotations

import duckdb


def _i(x) -> int:
    """Round a numeric field to int for display (documents show integers)."""
    return int(round(float(x)))


def _tipus(t: str | None) -> str:
    """Render tipus with underscores as spaces (e.g. 'interior_rural' -> 'interior rural')."""
    return (t or "").replace("_", " ")


def _describe(row: dict) -> str:
    nom = row["nom"]
    tipus = _tipus(row["tipus"])
    est = _i(row["estimacio"])
    rb = _i(row["rang_baix"])
    ra = _i(row["rang_alt"])
    reg = row["register"]

    if reg == "oficial":
        etca = _i(row["etca_oficial"])
        return (
            f"{nom} (Berguedà) · {tipus}. Presència estimada {est} "
            f"(rang {rb}–{ra}). Registre oficial: ≥1.000 hab amb dada ETCA d'Idescat "
            f"({etca}) — el model es pot contrastar amb la font oficial."
        )

    padro = _i(row["padro"])

    if reg == "senyal_mes":
        return (
            f"{nom} (Berguedà) · {tipus}. Presència estimada {est} "
            f"(rang {rb}–{ra}), per sobre del padró ({padro}). Registre senyal: "
            f"<1.000 hab; l'interval exclou el padró, sense validació oficial."
        )

    if reg == "senyal_menys":
        return (
            f"{nom} (Berguedà) · {tipus}. Presència estimada {est} "
            f"(rang {rb}–{ra}), per sota del padró ({padro}). Registre senyal: "
            f"<1.000 hab; l'interval exclou el padró, sense validació oficial."
        )

    if reg == "soroll":
        return (
            f"{nom} (Berguedà) · {tipus}. Presència estimada {est} "
            f"(rang {rb}–{ra}). Registre soroll: el rang inclou el padró ({padro}) "
            f"— l'estimació no es distingeix del propi marge en aquest poble."
        )

    raise ValueError(f"unknown register {reg!r} for {nom} ({row['ine5']})")


def generate_descriptions(conn: duckdb.DuckDBPyConnection) -> dict[str, str]:
    """Return {ine5: catalan_description} for every muni in the substrate.

    Torch-free: reads only the `municipi` table.
    """
    cols = ["ine5", "nom", "tipus", "padro", "estimacio", "rang_baix", "rang_alt",
            "etca_oficial", "register"]
    rows = conn.execute(
        f"SELECT {', '.join(cols)} FROM municipi ORDER BY ine5"
    ).fetchall()
    out: dict[str, str] = {}
    for r in rows:
        row = dict(zip(cols, r, strict=True))
        out[row["ine5"]] = _describe(row)
    return out
