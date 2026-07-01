"""Phase 1 — the spatial retriever with tie detection — TORCH-FREE.

The ranking path never imports torch. It reuses the Phase-0a/0b substrate (the
`municipi` table with native geometry + FTS, and `municipi_emb` from
`search.load_embeddings`) and takes a *ready* 384-dim query vector (produced out of
this path by `embeddings.embed_query`, torch). So the whole retrieve() call — filter,
three ranked lists, RRF fusion, tie detection — runs offline with no torch.

THE PRINCIPLE (contract 03-fase1-recuperador.md). Inability to distinguish appears at
three heights and the honest system makes the SAME gesture at each:

    data       -> soroll     : "no distingeixo aquest número del meu marge"
    municipi   -> col·lisió  : "no distingeixo aquest poble d'aquell"
    recuperació-> empat      : "no distingeixo quin document va primer"

Phase 1 is where the gesture reaches retrieval. The retriever does NOT break a tie the
data cannot break — it REPORTS it. An unbreakable tie is the abstention of ordering
(the same abstention-calibration KPI, one level up). A retriever that always returns a
clean winner over tied data lies with confidence.

Order of operations in retrieve():
  1. HARD SPATIAL FILTER FIRST — anchor + its neighbours, else all 31 (comarca). Narrows
     the candidate set BEFORE any scoring.
  2. Up to THREE ranked lists over the candidates: spatial distance (anchor only),
     semantic cosine, FTS name.
  3. RRF fusion of RANKS: score(d) = Σ_lists 1/(RRF_K + rank_l(d)).
  4. TIE DETECTION (the only addition): collision tie (data) and score tie (RRF).
"""

from __future__ import annotations

import duckdb

from .descriptions import _collision_groups, _denom
from .search import EMB_DIM, load_embeddings  # noqa: F401 (load_embeddings re-exported)

# RRF constant (Cormack et al. 2009). Ranks start at 1.
RRF_K = 60

# Score-tie epsilon: relative gap between the #1 and #2 fused scores. Below this the two
# top candidates are declared tied — we will NOT order them by phrasing noise.
EPS = 0.02

__all__ = ["RRF_K", "EPS", "load_embeddings", "detect_anchor", "retrieve"]


def _has(conn: duckdb.DuckDBPyConnection, key: str) -> bool:
    row = conn.execute("SELECT value FROM _substrate_meta WHERE key=?", [key]).fetchone()
    return bool(row and row[0] == "1")


def detect_anchor(conn: duckdb.DuckDBPyConnection, query_text: str) -> str | None:
    """Return the ine5 of a muni proper-name mentioned in the query, or None.

    Matches each muni's name (and its de-articled form, e.g. "la Pobla de Lillet")
    against the query text, longest name first so "Sant Julià de Cerdanyola" wins over a
    bare "Sant". Torch-free; used to trigger the hard spatial filter. If no proper name
    appears the query is comarca-wide (candidate set = all 31).
    """
    q = (query_text or "").lower()
    rows = conn.execute("SELECT ine5, nom FROM municipi").fetchall()
    # Longest surface form first so multi-word names beat their prefixes.
    forms: list[tuple[str, str]] = []
    for ine5, nom in rows:
        for surface in {nom, _denom(nom)}:
            forms.append((ine5, surface))
    forms.sort(key=lambda t: len(t[1]), reverse=True)
    for ine5, surface in forms:
        if surface.lower() in q:
            return ine5
    return None


def _candidate_set(
    conn: duckdb.DuckDBPyConnection, anchor_ine5: str | None
) -> list[str]:
    """Hard spatial filter: anchor + spatial neighbours if anchored, else all 31.

    Neighbours are the touching polygons within the 31 (ST_Intersects), reusing the
    same adjacency the substrate exposes via build.neighbors. Falls back to all 31 if
    spatial is unavailable (offline-safe) — an honest widening, never a silent pick.
    """
    all31 = [r[0] for r in conn.execute("SELECT ine5 FROM municipi ORDER BY ine5").fetchall()]
    if anchor_ine5 is None:
        return all31
    if not _has(conn, "spatial"):
        return all31
    rows = conn.execute(
        """
        SELECT b.ine5
        FROM municipi a
        JOIN municipi b ON ST_Intersects(a.geom, b.geom)
        WHERE a.ine5 = ?
        """,
        [anchor_ine5],
    ).fetchall()
    cand = {anchor_ine5} | {r[0] for r in rows}
    return sorted(cand)


def _rank_map(ordered_ine5: list[str]) -> dict[str, int]:
    """Map ine5 -> 1-based rank from an ordered list (best first)."""
    return {ine5: i + 1 for i, ine5 in enumerate(ordered_ine5)}


def _spatial_list(
    conn: duckdb.DuckDBPyConnection, candidates: list[str], anchor_ine5: str
) -> list[str]:
    """Candidates ranked by centroid distance to the anchor, nearest first (fs=1/(1+d))."""
    if not _has(conn, "spatial"):
        return []
    placeholders = ",".join("?" for _ in candidates)
    rows = conn.execute(
        f"""
        SELECT b.ine5,
               ST_Distance(ST_Centroid(b.geom), ST_Centroid(a.geom)) AS d
        FROM municipi a, municipi b
        WHERE a.ine5 = ?
          AND b.ine5 IN ({placeholders})
        ORDER BY d ASC, b.ine5
        """,
        [anchor_ine5, *candidates],
    ).fetchall()
    return [r[0] for r in rows]


def _semantic_list(
    conn: duckdb.DuckDBPyConnection, candidates: list[str], query_vec: list[float]
) -> list[str]:
    """Candidates ranked by cosine(query_vec, municipi_emb), desc. Empty if no embeddings."""
    if not _has(conn, "embeddings"):
        return []
    if len(query_vec) != EMB_DIM:
        raise ValueError(f"query_vec must be {EMB_DIM}-dim, got {len(query_vec)}")
    vec_literal = "[" + ", ".join(repr(float(x)) for x in query_vec) + "]"
    placeholders = ",".join("?" for _ in candidates)
    rows = conn.execute(
        f"""
        SELECT e.ine5,
               array_cosine_similarity(e.emb, {vec_literal}::FLOAT[{EMB_DIM}]) AS score
        FROM municipi_emb e
        WHERE e.ine5 IN ({placeholders})
        ORDER BY score DESC, e.ine5
        """,
        candidates,
    ).fetchall()
    return [r[0] for r in rows]


def _name_list(
    conn: duckdb.DuckDBPyConnection, candidates: list[str], query_text: str
) -> list[str]:
    """Candidates ranked by FTS match_bm25 over municipi(nom), desc. Empty if no FTS/hit."""
    if not _has(conn, "fts"):
        return []
    placeholders = ",".join("?" for _ in candidates)
    try:
        rows = conn.execute(
            f"""
            SELECT ine5, score FROM (
                SELECT ine5, fts_main_municipi.match_bm25(ine5, ?) AS score
                FROM municipi
                WHERE ine5 IN ({placeholders})
            ) t
            WHERE score IS NOT NULL
            ORDER BY score DESC, ine5
            """,
            [query_text, *candidates],
        ).fetchall()
    except Exception:
        return []
    return [r[0] for r in rows]


def _rrf_fuse(rank_lists: list[dict[str, int]], candidates: list[str]) -> dict[str, float]:
    """RRF over RANKS: score(d) = Σ_lists 1/(RRF_K + rank_l(d)). Fuse ranks, not scores.

    A candidate absent from a list contributes nothing from that list (no rank there).
    """
    scores: dict[str, float] = {c: 0.0 for c in candidates}
    for rm in rank_lists:
        for ine5, rank in rm.items():
            if ine5 in scores:
                scores[ine5] += 1.0 / (RRF_K + rank)
    return scores


def rrf_score(*ranks: int) -> float:
    """Unit helper: RRF contribution of a candidate appearing at the given 1-based ranks.

    rrf_score(r1, r2) == 1/(RRF_K+r1) + 1/(RRF_K+r2). Exposed for the unit test.
    """
    return sum(1.0 / (RRF_K + r) for r in ranks)


def retrieve(
    conn: duckdb.DuckDBPyConnection,
    query_text: str,
    query_vec: list[float],
    anchor_ine5: str | None = None,
    k: int = 5,
) -> dict:
    """Retrieve the top-k candidates with honest tie detection.

    Steps (in order): hard spatial filter -> up to three ranked lists -> RRF fusion of
    ranks -> tie detection. Returns:

        {
          "candidates": [ {ine5, nom, score, register, estimacio, in_collision}, ... ],
          "anchor": ine5 | None,
          "n_candidates": int,          # size of the hard-filtered set
          "tie": {is_tie, kind, group:[ine5], note}
        }

    Tie contract: a collision top candidate reports the WHOLE sharing group (never drops
    a member, never silently picks one); a score tie within EPS is reported, not ordered
    by phrasing noise. Never present a shared/collision figure as muni-specific.
    """
    if anchor_ine5 is None:
        anchor_ine5 = detect_anchor(conn, query_text)

    # 1) HARD SPATIAL FILTER FIRST.
    candidates = _candidate_set(conn, anchor_ine5)

    # 2) Up to three ranked lists over the candidates.
    rank_lists: list[dict[str, int]] = []
    if anchor_ine5 is not None:
        sp = _spatial_list(conn, candidates, anchor_ine5)
        if sp:
            rank_lists.append(_rank_map(sp))
    sem = _semantic_list(conn, candidates, query_vec)
    if sem:
        rank_lists.append(_rank_map(sem))
    nm = _name_list(conn, candidates, query_text)
    if nm:
        rank_lists.append(_rank_map(nm))

    # 3) RRF fusion of ranks.
    scores = _rrf_fuse(rank_lists, candidates)

    # Order candidates by fused score desc; stable tie-break by ine5 for determinism ONLY
    # (never presented as a meaningful order — the tie block below is the honest signal).
    ordered = sorted(candidates, key=lambda c: (-scores[c], c))

    # Attach fields.
    by_ine, allm = _collision_groups()
    the31 = set(candidates) if anchor_ine5 is None else {
        r[0] for r in conn.execute("SELECT ine5 FROM municipi").fetchall()
    }
    meta = {
        r[0]: r
        for r in conn.execute(
            "SELECT ine5, nom, register, estimacio FROM municipi"
        ).fetchall()
    }
    cand_out = []
    for ine5 in ordered[:k]:
        _, nom, register, estimacio = meta[ine5]
        cand_out.append(
            {
                "ine5": ine5,
                "nom": nom,
                "score": scores[ine5],
                "register": register,
                "estimacio": estimacio,
                "in_collision": ine5 in by_ine,
            }
        )

    tie = _detect_tie(conn, ordered, scores, by_ine, allm, the31, meta)

    return {
        "candidates": cand_out,
        "anchor": anchor_ine5,
        "n_candidates": len(candidates),
        "tie": tie,
    }


def _detect_tie(
    conn: duckdb.DuckDBPyConnection,
    ordered: list[str],
    scores: dict[str, float],
    by_ine: dict[str, list[str]],
    allm: dict,
    the31: set[str],
    meta: dict,
) -> dict:
    """Return the tie block. COLLISION (data) takes precedence over SCORE (RRF)."""
    if not ordered:
        return {"is_tie": False, "kind": None, "group": [], "note": ""}

    top = ordered[0]

    # --- COLLISION tie (data) ---
    # If the top candidate shares its estimate+range with other munis (a collision
    # group), the data cannot tell it apart from them. Report the WHOLE group; do NOT
    # drop the other members or silently pick one.
    group = by_ine.get(top)
    if group:
        est = meta[top][3]  # estimacio
        in31 = [m for m in group if m in the31]
        register = meta[top][2]
        peers_all = " i ".join(_denom(allm[m]["nom"]) for m in group)
        if register == "oficial":
            etcas = " vs ".join(
                str(int(round(float(allm[m]["etca_oficial"]))))
                for m in group
                if allm[m].get("etca_oficial") is not None
            )
            note = (
                f"Empat de col·lisió (dada): el model dona la mateixa estimació "
                f"({int(round(float(est)))}) a {peers_all}; no els distingeix. La xifra NO és "
                f"específica del municipi. Idescat SÍ els separa (ETCA {etcas}) — "
                f"l'etiqueta oficial promet contrastable i l'empat la desmenteix."
            )
        else:
            note = (
                f"Empat de col·lisió (dada): el model dona la mateixa estimació "
                f"({int(round(float(est)))}) a {len(group)} municipis ({peers_all}); no els "
                f"distingeix. La xifra NO és específica del municipi consultat."
            )
        return {
            "is_tie": True,
            "kind": "collision",
            "group": list(group),
            "group_in31": in31,
            "note": note,
        }

    # --- SCORE tie (RRF) ---
    # If #1 and #2 fused scores are within EPS (relative gap), the retrieval cannot
    # order them. Report them tied; do NOT impose an order from phrasing noise.
    if len(ordered) >= 2:
        s1, s2 = scores[ordered[0]], scores[ordered[1]]
        if s1 > 0:
            rel_gap = (s1 - s2) / s1
        else:
            rel_gap = 0.0  # both zero -> indistinguishable
        if rel_gap < EPS:
            tied = [c for c in ordered if s1 > 0 and (s1 - scores[c]) / s1 < EPS]
            if len(tied) < 2:  # both-zero case
                tied = [c for c in ordered if scores[c] == s1]
            noms = " i ".join(_denom(meta[c][1]) for c in tied)
            note = (
                f"Empat de score (recuperació): {len(tied)} candidats amb score RRF dins "
                f"d'ε={EPS} ({noms}); la recuperació no els pot ordenar. No s'imposa ordre."
            )
            return {
                "is_tie": True,
                "kind": "score",
                "group": tied,
                "note": note,
            }

    return {"is_tie": False, "kind": None, "group": [], "note": ""}
