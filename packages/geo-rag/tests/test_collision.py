"""Collision-note tests (TORCH-FREE).

The Nivell C model gives identical estimate+range to different municipalities. Rendering
that number naked would propagate a source error in silence, so descriptions carry an
honest collision warning. These tests guard that the warning is present where it must be
(and absent where it must not). If the upstream collision count changes, the count guard
below fails on purpose — that is a signal to re-review, not a nuisance.
"""

from datapoble_geo_rag.build import build
from datapoble_geo_rag.descriptions import generate_descriptions

MARK = "Col·lisió del model"


def _descriptions():
    return generate_descriptions(build(None))


def _by_prefix(d: dict[str, str], prefix: str) -> str:
    return next(v for v in d.values() if v.startswith(prefix))


def test_collision_flagged_count():
    """12 of the 31 Berguedà munis share an estimate Catalunya-wide (see handoff 02)."""
    d = _descriptions()
    flagged = [v for v in d.values() if MARK in v]
    assert len(flagged) == 12, f"expected 12 collision-flagged munis, got {len(flagged)}"


def test_oficial_pair_cross_references_peer_and_etca():
    """Guardiola de Berguedà and la Pobla de Lillet: oficial collision — the label promises
    contrastable, the model collapses them (852=852), Idescat separates them (1005 vs 1121)."""
    d = _descriptions()
    guard = _by_prefix(d, "Guardiola de Berguedà")
    pobla = _by_prefix(d, "Pobla de Lillet, la")
    assert MARK in guard and "la Pobla de Lillet" in guard and "ETCA 1005 vs 1121" in guard
    assert MARK in pobla and "Guardiola de Berguedà" in pobla and "ETCA 1005 vs 1121" in pobla


def test_non_collision_muni_has_no_note():
    """A muni with a unique estimate carries no collision warning."""
    d = _descriptions()
    berga = _by_prefix(d, "Berga ")  # 16669, unique
    assert MARK not in berga
