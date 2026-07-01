"""Fase 2 tests — la regla de distingibilitat (TORCH-FREE, offline).

Guarda que UNA SOLA regla (distinguish.distinguishable) serveix els dos usos:
comparació entre municipis (ordena separats, s'absté en overlap) i modulació per σ (to
ferm per banda estreta, prudent per soroll). I que la col·lisió exacta de la Fase 1
(Guardiola / la Pobla de Lillet) es resol per la MATEIXA funció, com a cas límit a
distància zero — sense lògica d'overlap duplicada.
"""

from datapoble_geo_rag.build import build
from datapoble_geo_rag.compare import LAMBDA, answer, answer_comparison, compare
from datapoble_geo_rag.distinguish import distinguishable, overlaps

# ine5 reals del substrat (verificats contra pernocta-catalunya.json)
BERGA = "08022"          # oficial, banda estreta, [14206, 20289]
GIRONELLA = "08092"      # oficial, [4423, 6316] — disjunt de Berga
OLVAN = "08144"          # soroll,  [629, 1082]
POBLA = "08166"          # oficial, [726, 1037] — solapa amb Olvan; idèntic a Guardiola
GUARDIOLA = "08099"      # oficial, [726, 1037] — col·lisió exacta amb la Pobla
GOSOL = "25100"          # soroll,  banda ampla


# ---------------------------------------------------------------------------
# distinguishable() unitari — la funció pura
# ---------------------------------------------------------------------------


def test_distinguishable_disjoint_true():
    # [0,10] vs [20,30] — disjunts → distingibles
    assert distinguishable(0, 10, 20, 30) is True
    assert overlaps(0, 10, 20, 30) is False


def test_distinguishable_overlap_false():
    # [0,15] vs [10,30] — s'encavalquen → no distingibles
    assert distinguishable(0, 15, 10, 30) is False
    assert overlaps(0, 15, 10, 30) is True


def test_distinguishable_identical_false_phase1_limit():
    # Bandes idèntiques = la col·lisió exacta de la Fase 1 = distància zero → no distingibles.
    assert distinguishable(726, 1037, 726, 1037) is False
    assert overlaps(726, 1037, 726, 1037) is True


def test_distinguishable_touching_false():
    # Toquen just a l'extrem (max_low == min_high): gap = 0, no > 0 → no distingibles.
    assert distinguishable(0, 10, 10, 20) is False


def test_min_gap_is_declared_parameter():
    # Amb un gap real de 5, un min_gap=10 declarat els torna no distingibles.
    assert distinguishable(0, 10, 15, 25) is True          # gap 5 > 0 (per defecte)
    assert distinguishable(0, 10, 15, 25, min_gap=10) is False


# ---------------------------------------------------------------------------
# compare() — ordena separats, s'absté en overlap (mateixa regla)
# ---------------------------------------------------------------------------


def test_compare_orders_separated():
    conn = build(None)
    res = compare(conn, BERGA, GIRONELLA)
    assert res["distinguishable"] is True
    assert res["higher"] == BERGA and res["lower"] == GIRONELLA
    conn.close()


def test_compare_abstains_on_overlap():
    conn = build(None)
    res = compare(conn, OLVAN, POBLA)
    assert res["distinguishable"] is False
    assert res["higher"] is None and res["lower"] is None
    assert "s'encavalquen" in res["note"] and "no els puc ordenar" in res["note"]
    conn.close()


def test_exact_collision_via_shared_rule():
    # Guardiola / la Pobla: bandes idèntiques → compare() s'absté per la MATEIXA
    # distinguishable() (distància zero), no per un camí especial.
    conn = build(None)
    row = conn.execute(
        "SELECT rang_baix, rang_alt FROM municipi WHERE ine5 IN (?, ?)",
        [GUARDIOLA, POBLA],
    ).fetchall()
    # confirma que les bandes són realment idèntiques al substrat
    assert row[0] == row[1]
    res = compare(conn, GUARDIOLA, POBLA)
    assert res["distinguishable"] is False
    assert res["higher"] is None and res["lower"] is None
    # i que la funció pura, cridada directament amb aquestes bandes, coincideix
    (bl, bh) = row[0]
    assert distinguishable(bl, bh, bl, bh) is False
    conn.close()


def test_answer_comparison_detects_two_names():
    conn = build(None)
    out = answer_comparison(conn, "qui en té més, Berga o Gironella?")
    assert set(out["munis"]) == {BERGA, GIRONELLA}
    assert out["result"]["distinguishable"] is True
    assert out["result"]["higher"] == BERGA
    conn.close()


def test_answer_comparison_honest_when_one_muni():
    conn = build(None)
    out = answer_comparison(conn, "quanta gent hi ha a Berga?")
    assert len(out["munis"]) < 2
    assert "un municipi" in out["text"] or "cap municipi" in out["text"]
    conn.close()


# ---------------------------------------------------------------------------
# answer() — el to segueix σ (mateixa banda)
# ---------------------------------------------------------------------------


def test_answer_tone_ferm_for_narrow_band():
    conn = build(None)
    res = answer(conn, BERGA)
    assert res["tone"] == "ferm"
    assert res["band"] == [14206.0, 20289.0]
    conn.close()


def test_answer_tone_prudent_for_soroll():
    conn = build(None)
    res = answer(conn, GOSOL)
    assert res["tone"] == "prudent"
    assert res["register"] == "soroll"
    assert "prudència" in res["text"]
    conn.close()


def test_answer_s_score_is_mean_variance():
    # S = μ − λσ (Markowitz), amb la σ real (la banda).
    conn = build(None)
    res = answer(conn, BERGA)
    assert res["s_score"] == res["estimacio"] - LAMBDA * res["sigma"]
    conn.close()
