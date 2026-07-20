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
    # (index_envelliment left this list on 2026-07-18: promoted to public after B3
    # found it planned with 946/947 real values in mart_municipi — KPI 1 of the
    # government dashboard. It now asserts AVAILABLE below.)
    for key in ("pct_extrema_dreta",):
        m = catalog.metric(key)
        assert m is not None
        assert m.is_available() is False
    # ...and excluded from the available set.
    available = {m.key for m in catalog.available_metrics()}
    assert "pct_extrema_dreta" not in available
    assert "poblacio" in available
    assert "index_envelliment" in available


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


def test_tables_only_reference_served_metrics(catalog):
    tables = catalog.tables()
    assert "mart_municipi" in tables
    # mart_electoral stays in the SQL allow-list even though `politica` is held
    # back: the dimension is KEYED, so the unlocked path has to be able to
    # execute. The allow-list bounds the blast radius; it is not the policy
    # gate. (This test used to assert the same line for the opposite reason —
    # back when the electoral metrics were simply available.)
    assert "mart_electoral" in tables
    # mart_demografia is where the `origen` metrics live. That dimension has no
    # key, so nothing can reach it and it drops out of the allow-list entirely.
    origen_tables = {
        m.table for m in catalog.metrics.values() if m.dimension == "origen"
    }
    assert origen_tables, "no origen metrics (test would be vacuous)"
    assert tables.isdisjoint(origen_tables), (
        f"unkeyed held-back tables in the SQL allow-list: {origen_tables & tables}"
    )


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


def test_politica_metrics_are_held_back_from_agent(catalog):
    # Bea's call, 2026-07-20: electoral goes behind the fence. A refusal already
    # existed at the ANSWER layer (politics.PoliticsGate), but it keys off a
    # *resolved* metric, so every surface that merely enumerates the catalog
    # walked around it and advertised what the agent would then refuse. This is
    # the gate at the catalog, where enumeration happens. Sibling of the origen
    # guard above; the difference is that politica is KEYED (see below).
    politica = [m for m in catalog.metrics.values() if m.dimension == "politica"]
    assert politica, "no politica-dimension metrics in the contract (test would be vacuous)"
    for m in politica:
        assert m.is_available() is False, f"{m.key} (politica) leaked: must not be agent-available"
    available = {m.key for m in catalog.available_metrics()}
    assert available.isdisjoint({m.key for m in politica}), "politica metrics leaked into the available set"
    # The four the contract declares, named so a fifth cannot be added silently.
    for key in ("pct_indep", "pct_esquerra", "pct_extrema_dreta", "guanya"):
        m = catalog.metric(key)
        assert m is not None and m.dimension == "politica", key
        assert m.is_available() is False, key


def test_politica_is_held_back_but_keyed_origen_is_not(catalog):
    # The two held-back dimensions are NOT the same door, and the difference is
    # load-bearing: `origen` is unconditional (no escape hatch until the origen
    # frontier of task #71 exists), `politica` is openable with the runtime
    # secret PoliticsGate reads. Collapsing them would have silently revoked a
    # key that is Bea's to revoke, not this layer's.
    keyed = {m.key for m in catalog.keyed_metrics()}
    # Computed politica metrics are keyed...
    assert "pct_indep" in keyed and "guanya" in keyed
    # ...but a planned one has no data to open, key or not.
    assert "pct_extrema_dreta" not in keyed
    # ...and origen is never keyed.
    for m in catalog.metrics.values():
        if m.dimension == "origen":
            assert m.key not in keyed, f"{m.key} (origen) must have no key"


def test_deprecated_metrics_are_not_available(catalog):
    # Handoff from Sondeig (#268): is_available() only excluded `planned`, so a
    # metric retired by editorial vote was still served. index_turisme is the
    # live case (Bea, 2026-07-18) — and its column still sits in mart_municipi,
    # so nothing failed: the agent just kept answering with a number the
    # project had decided not to stand behind. Silent, which is the bad kind.
    m = catalog.metric("index_turisme")
    assert m is not None and m.status == "deprecated"
    assert m.is_computed() is False
    assert m.is_available() is False
    available = {x.key for x in catalog.available_metrics()}
    assert "index_turisme" not in available
    # General form: no deprecated metric anywhere in the served set.
    deprecated = {k for k, x in catalog.metrics.items() if x.status == "deprecated"}
    assert deprecated, "no deprecated metric in the contract (test would be vacuous)"
    assert available.isdisjoint(deprecated)


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
