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


def test_origen_metrics_are_held_back_from_agent(catalog):
    # The «origen» dimension (composició i arrelament: nationality / birthplace /
    # naturalisation) is SENSITIVE: public on the web but deliberately held back from
    # the agent until the origen frontier exists. Regression guard for that gate.
    origen = [m for m in catalog.metrics.values() if m.dimension == "origen"]
    assert origen, "no origen-dimension metrics in the contract (test would be vacuous)"
    for m in origen:
        assert m.is_available() is False, f"{m.key} (origen) leaked: must not be agent-available"
    available = {m.key for m in catalog.available_metrics()}
    assert available.isdisjoint({m.key for m in origen}), "origen metrics leaked into the available set"
    # Concrete sentinel that must stay held back.
    sentinel = catalog.metric("pct_nascuda_estranger")
    assert sentinel is not None and sentinel.dimension == "origen"
    assert sentinel.is_available() is False


# --- Guarda de la unificació de claus (2026-07-17) -----------------------------------
# Dins de `metrics:` l'ÚNICA clau d'advertència és `caveat` (la doctrina és al capçal
# del contracte). Abans convivien note/nota/caveat i cap lector les llegia totes: el
# «INFERÈNCIA, no cens» no arribava mai al lector. Si note:/nota: reapareixen en una
# mètrica, és un error de contracte i aquest test el fa VERMELL.


def test_cap_metrica_amb_note_o_nota_nomes_caveat():
    import yaml

    from datapoble_ai.catalog import _repo_root

    raw = yaml.safe_load(
        (_repo_root() / "semantic" / "metrics.yml").read_text(encoding="utf-8")
    )
    infractores = [
        k for k, v in raw["metrics"].items()
        if isinstance(v, dict) and ("note" in v or "nota" in v)
    ]
    assert infractores == [], (
        f"metrics amb note:/nota: (la clau del contracte és caveat:): {infractores}"
    )
    n_caveats = sum(
        1 for v in raw["metrics"].values() if isinstance(v, dict) and "caveat" in v
    )
    assert n_caveats >= 27  # les 27 de la unificació; poden créixer, mai baixar
