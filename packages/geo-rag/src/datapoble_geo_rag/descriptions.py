"""Catalan natural-language descriptions per municipality — TORCH-FREE.

One approved description per muni, keyed by the `register` computed in build.py.
These strings are the *documents* that get embedded (Phase 0b). They invent nothing
beyond the fields already in the `municipi` table: nom, tipus, estimacio, rang_baix,
rang_alt, padro, etca_oficial, register.

The templates are fixed and reviewed. Numbers render as integers; `tipus` has its
underscores replaced by spaces for readability.

COL·LISIÓ D'ESTIMACIONS (nota de la Rapaz, 30-06-2026). El model Nivell C dona, de
forma sistemàtica, estimacions+rang IDÈNTIQUES a municipis diferents (54 grups a tota
Catalunya). Renderitzar el número nu propagaria un error de la font en silenci: quan la
descripció el toca, hi afegim una advertència honesta. Cas greu: Guardiola de Berguedà
i la Pobla de Lillet són del registre OFICIAL (l'etiqueta promet «contrastable amb la
font»), reben la mateixa estimació (852), i Idescat SÍ els separa (ETCA 1005 vs 1121) —
l'etiqueta promet més del que la dada fa, dins el nucli validat. La causa estructural i
l'abast a l'oficial són el handoff a Sondeig (docs/experiment-rag-geo/02-*).
"""

from __future__ import annotations

from collections import defaultdict

import duckdb

from .build import PERNOCTA_JSON, _load_json

# Article final que la font posa al final del nom ("Pobla de Lillet, la"); el movem
# davant per a la prosa de la nota ("la Pobla de Lillet").
_ARTICLES = (", la", ", el", ", l'", ", els", ", les")


def _i(x) -> int:
    """Round a numeric field to int for display (documents show integers)."""
    return int(round(float(x)))


def _tipus(t: str | None) -> str:
    """Render tipus with underscores as spaces (e.g. 'interior_rural' -> 'interior rural')."""
    return (t or "").replace("_", " ")


def _denom(nom: str) -> str:
    """Move a trailing article to the front: 'Pobla de Lillet, la' -> 'la Pobla de Lillet'."""
    for suf in _ARTICLES:
        if nom.endswith(suf):
            art = suf[2:]  # 'la', 'el', "l'", ...
            base = nom[: -len(suf)]
            sep = "" if art.endswith("'") else " "
            return f"{art}{sep}{base}"
    return nom


def _collision_groups() -> tuple[dict[str, list[str]], dict]:
    """Groups of munis (Catalunya-wide) with identical (estimacio, rang_baix, rang_alt).

    Returns (by_ine5, all_munis): by_ine5 maps an ine5 to the FULL list of ine5 that
    share its estimate+range (including itself), ONLY for groups of size > 1; all_munis
    is the raw pernocta dict (for names + etca). Torch-free; reads the committed source.
    """
    allm = _load_json(PERNOCTA_JSON)["munis"]
    groups: dict[tuple, list[str]] = defaultdict(list)
    for ine5, v in allm.items():
        groups[(v["estimacio"], v["rang_baix"], v["rang_alt"])].append(ine5)
    by_ine: dict[str, list[str]] = {}
    for members in groups.values():
        if len(members) > 1:
            for ine5 in members:
                by_ine[ine5] = members
    return by_ine, allm


def _collision_note(row: dict, by_ine: dict[str, list[str]], allm: dict, berg: set[str]) -> str:
    """Honest collision warning appended to a muni's description, or '' if none.

    Register-aware: for OFICIAL the collision contradicts the label (Idescat separates
    what the model collapses) so we name the peers + their ETCA; otherwise we state the
    number is shared and not muni-specific.
    """
    ine5 = row["ine5"]
    members = by_ine.get(ine5)
    if not members:
        return ""
    others = [m for m in members if m != ine5]
    est = _i(allm[ine5]["estimacio"])

    if row["register"] == "oficial":
        peers = " i ".join(_denom(allm[m]["nom"]) for m in others)
        etcas = " vs ".join(
            str(_i(allm[m]["etca_oficial"])) for m in members if allm[m].get("etca_oficial") is not None
        )
        return (
            f" ⚠️ Col·lisió del model: no separa aquest municipi de {peers} — tots reben la mateixa "
            f"estimació ({est}). La dada oficial d'Idescat sí els distingeix (ETCA {etcas}). Fins que "
            f"no es resolgui a la font, aquesta xifra no s'ha de llegir com a específica del municipi."
        )

    berg_co = [_denom(allm[m]["nom"]) for m in others if m in berg]
    co = f" (al Berguedà, també {' i '.join(berg_co)})" if berg_co else ""
    return (
        f" ⚠️ Col·lisió del model: dona aquesta mateixa estimació ({est}) a {len(members)} municipis "
        f"de Catalunya{co}; no els distingeix. Fins que no es resolgui a la font, aquesta xifra no "
        f"s'ha de llegir com a específica del municipi."
    )


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

    Torch-free: reads the `municipi` table plus the committed pernocta source (to detect
    the model's identical-estimate collisions Catalunya-wide) and appends an honest
    collision warning where it applies.
    """
    cols = ["ine5", "nom", "tipus", "padro", "estimacio", "rang_baix", "rang_alt",
            "etca_oficial", "register"]
    rows = conn.execute(
        f"SELECT {', '.join(cols)} FROM municipi ORDER BY ine5"
    ).fetchall()
    by_ine, allm = _collision_groups()
    berg = {r[0] for r in rows}
    out: dict[str, str] = {}
    for r in rows:
        row = dict(zip(cols, r, strict=True))
        out[row["ine5"]] = _describe(row) + _collision_note(row, by_ine, allm, berg)
    return out
