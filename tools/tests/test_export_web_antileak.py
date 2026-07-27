"""Guarda anti-fuita dels exports web de govern i tauler (P-947, Sondeig).

Per què existeix: obrir els exports del Berguedà (31) als 947 municipis podia, per un
descuit futur (una columna nova al mart, un canvi de contracte), destapar la capa de VOT
—`dimension: politica` / `source: electoral` / `mart_electoral`— al web públic. Els exports
ja tenen la guarda `assert_no_electoral` cablada a cada execució (write i `--check`); aquest
test li dona DENTS: comprova que la detecció de la capa prohibida FUNCIONA (no passa en buit)
i que la guarda REALMENT peta si algú hi cola una mètrica prohibida.

100% offline: llegeix el contracte i els marts versionats (data/marts/*.parquet).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import export_govern_web as G  # noqa: E402
import export_tauler_web as T  # noqa: E402

CONTRACT = yaml.safe_load((REPO / "semantic" / "metrics.yml").read_text(encoding="utf-8"))

# Les 4 mètriques de vot que HAN d'estar retingudes (sentinella de les dents: si la detecció
# es trenqués i tornés buit, aquest conjunt deixaria de trobar-se i el test cauria).
ELECTORAL_KNOWN = {"pct_indep", "pct_esquerra", "pct_extrema_dreta", "guanya"}


def test_forbidden_set_has_teeth():
    """La detecció de la capa prohibida troba les mètriques electorals del contracte real.
    Sense això, `assert_no_electoral` passaria en buit (guarda decorativa)."""
    forbidden_g = G.forbidden_metric_keys(CONTRACT)
    forbidden_t = T.forbidden_metric_keys(CONTRACT)
    assert forbidden_g == forbidden_t, "les dues guardes han de calcular el mateix conjunt"
    assert ELECTORAL_KNOWN <= forbidden_g, (
        f"la detecció no troba la capa de vot esperada: falten "
        f"{sorted(ELECTORAL_KNOWN - forbidden_g)}"
    )
    # Cap de les 4 pot ser una mètrica «segura» per accident.
    assert len(forbidden_g) >= len(ELECTORAL_KNOWN)


def test_govern_outputs_carry_no_electoral():
    """Cap dels dos abasts de govern (31 i 947) serveix una mètrica de la capa de vot."""
    forbidden = G.forbidden_metric_keys(CONTRACT)
    df = pd.read_parquet(G.MART)
    for scope in ("Berguedà", None):
        payload = G.build(df, scope)
        emitted = {m for muni in payload.values() for m in muni["metrics"]}
        assert not (emitted & forbidden), (
            f"govern ({scope or 'Catalunya'}) filtraria {sorted(emitted & forbidden)}"
        )


def test_tauler_outputs_carry_no_electoral():
    """Cap dels dos abasts del tauler (31 i 947) serveix una mètrica de la capa de vot."""
    forbidden = T.forbidden_metric_keys(CONTRACT)
    for scope in ("Berguedà", None):
        payload = T.build(scope)
        assert not (T.emitted_metrics(payload) & forbidden), (
            f"tauler ({scope or 'Catalunya'}) filtraria "
            f"{sorted(T.emitted_metrics(payload) & forbidden)}"
        )


def test_govern_guard_fires_on_injection():
    """Si un payload de govern portés una mètrica prohibida, la guarda ha de PETAR."""
    poison = {"08999": {"comarca": "X", "metrics": {"guanya": {"valor": 1, "rang": 1,
                                                               "n_amb_dada": 1, "data": "2024",
                                                               "empat": False}}}}
    with pytest.raises(SystemExit):
        G.assert_no_electoral(poison, {"guanya"}, "test.json")


def test_tauler_guard_fires_on_injection():
    """Si un payload del tauler portés una mètrica prohibida a tendència, la guarda peta."""
    poison = {"municipis": {"08999": {"tendencia": {"pct_indep": [{}]}, "atur": {}}}}
    with pytest.raises(SystemExit):
        T.assert_no_electoral(poison, {"pct_indep"}, "test/shard.json")
