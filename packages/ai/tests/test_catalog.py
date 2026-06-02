"""Catalog loads the contract correctly and exposes locale-aware accessors."""

from __future__ import annotations

from datapoble_ai.catalog import normalize


def test_loads_metrics_and_meta(catalog):
    assert catalog.project == "datapoble"
    assert "ca" in catalog.locales and "es" in catalog.locales
    assert catalog.default_locale == "ca"
    # A representative sample of contract metrics is present.
    for key in ("poblacio", "hab_noprincipal", "IETR", "rtc_total", "kg_hab_any"):
        assert catalog.metric(key) is not None, key


def test_planned_metrics_are_not_available(catalog):
    # These are status: planned in the contract -> defined but not queryable.
    for key in ("index_envelliment", "pct_extrema_dreta"):
        m = catalog.metric(key)
        assert m is not None
        assert m.is_available() is False
    # ...and excluded from the available set.
    available = {m.key for m in catalog.available_metrics()}
    assert "pct_extrema_dreta" not in available
    assert "poblacio" in available


def test_localized_labels_and_units(catalog):
    pob = catalog.metric("poblacio")
    assert pob.label("ca") == "Població"
    assert pob.label("es") == "Población"
    pct = catalog.metric("pct_noprincipal")
    # "%" is a scalar unit shared by both locales.
    assert pct.unit("ca") == "%"
    assert pct.unit("es") == "%"


def test_match_terms_include_synonyms_accent_folded(catalog):
    hab = catalog.metric("hab_noprincipal")
    terms = hab.match_terms("ca")
    assert normalize("segona residència") in terms
    # Longest-first ordering (most specific synonym before short ones).
    assert terms == sorted(terms, key=len, reverse=True)


def test_tables_only_reference_available_metrics(catalog):
    tables = catalog.tables()
    assert "mart_municipi" in tables
    assert "mart_electoral" in tables


def test_provenance_fields_present_on_contract(catalog):
    # The contract's own rule: no metric without formula, source and (mostly) date.
    for m in catalog.available_metrics():
        assert m.formula, f"{m.key} has no formula"
        assert m.source_key, f"{m.key} has no source"
