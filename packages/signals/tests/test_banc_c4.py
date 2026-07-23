"""Guardes del transcriptor del banc C4 (parser del full d'etiquetatge).

CONGELAT (2026-07-20): Bea ha etiquetat les 66 files (C4 §2 v2 — cap agent, cap model
posa cap golden) i el banc s'ha congelat a `banc_c4_congelat.json`. Aquests tests
validen el PARSER i el VALIDADOR amb files sintètiques, que el full REAL parseja net
(66 files, 0 errors), i —la guarda de CONGELACIÓ— que el JSON congelat coincideix byte
a byte, en dada, amb `to_banc_json(parse_full())` i que el recompte no ha derivat (mateix
patró de fidelitat que test_parafrasis): ni el full ni el JSON es poden editar en silenci.
"""

from datapoble_signals.banc_c4 import (
    BANC_CONGELAT_PATH,
    FULL_PATH,
    carrega_banc_congelat,
    construeix_banc_congelat,
    parse_full,
    recompte,
    to_banc_json,
    valida,
)


def _fila(num, bdns, golden="", semafor="", motiu=""):
    return (
        f"| {num} | [{bdns}](https://x/{bdns}) | CONV | OBJ | BEN | AMB | 2026-01-01 |"
        f" {golden} | {semafor} | {motiu} |"
    )


def _parse_sintetic(tmp_path, rows):
    p = tmp_path / "full.md"
    p.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return parse_full(p)


def test_parseja_el_full_real_sense_petar():
    files = parse_full()
    assert FULL_PATH.exists()
    assert len(files) == 66, f"esperava 66 files (26 A + 40 B), n'hi ha {len(files)}"
    assert sum(1 for f in files if f.capa == "A") == 26
    assert sum(1 for f in files if f.capa == "B") == 40


def test_valida_etiquetatge_correcte(tmp_path):
    files = _parse_sintetic(tmp_path, [
        _fila(1, "111", "descartable", "", "nominativa"),
        _fila(2, "222", "elegible", "verd", "encaixa fort"),
        _fila(27, "333", "elegible", "groc", "cofinançament alt"),
        _fila(28, "444", "frontera", "", "dubte de matèria"),
    ])
    errors, _ = valida(files)
    assert errors == []
    r = recompte(files)
    assert r["A"]["descartable"] == 1 and r["A"]["elegible"] == 1
    assert r["B"]["elegible"] == 1 and r["B"]["frontera"] == 1
    assert r["denominador_recall_B"] == 1


def test_valida_cata_els_errors(tmp_path):
    files = _parse_sintetic(tmp_path, [
        _fila(1, "111"),                                  # sense golden
        _fila(2, "222", "elegible", "", ""),              # elegible sense semafor
        _fila(3, "333", "descartable", "verd", "x"),      # semafor en no-elegible
        _fila(4, "444", "frontera", "", ""),              # frontera sense motiu
        _fila(5, "555", "brillant", "", "x"),             # vocabulari
    ])
    errors, _ = valida(files)
    assert len(errors) == 5
    assert any("sense etiqueta" in e for e in errors)
    assert any("sense semafor" in e for e in errors)
    assert any("en una no-elegible" in e for e in errors)
    assert any("exigeix motiu" in e for e in errors)
    assert any("fora del vocabulari" in e for e in errors)


def test_solapament_a_b_es_warning_no_error(tmp_path):
    files = _parse_sintetic(tmp_path, [
        _fila(3, "918352", "frontera", "", "OSIC, dubte"),
        _fila(30, "918352", "frontera", "", "OSIC, dubte"),
    ])
    errors, warnings = valida(files)
    assert errors == []
    assert any("solapament" in w for w in warnings)


# --- La guarda de CONGELACIÓ (substitueix l'anti-pre-etiquetatge, ja complerta) ---
# Fins que Bea va etiquetar, la guarda dura era que el full NO portés etiquetes
# (test_les_tres_columnes_de_la_direccio_son_buides_al_full, a test_capa_b.py). Un cop
# etiquetat i congelat, aquella guarda és falsa per disseny; la substitueix aquesta, que
# congela el sentit contrari: el JSON d'or ha de coincidir SEMPRE amb el full etiquetat i
# el recompte no pot moure's. És el patró del projecte: quan una guarda es retira, la que
# la substitueix neix al mateix PR.

def test_el_full_real_valida_net_zero_errors_zero_warnings():
    """La precondició de la congelació: el full etiquetat per Bea valida sense res pendent."""
    errors, warnings = valida(parse_full())
    assert errors == [], f"el full ja NO valida net (mai s'arregla un golden — atura't): {errors}"
    assert warnings == [], f"warnings inesperats (p. ex. una fila sense motiu): {warnings}"


def test_el_banc_congelat_coincideix_amb_el_full_i_no_deriva():
    """Fidelitat full↔JSON congelat: el banc no pot derivar ni editar-se en silenci."""
    assert BANC_CONGELAT_PATH.exists(), "falta el banc congelat — corre `--congela`"
    files = parse_full()
    banc_del_full = to_banc_json(files)
    assert carrega_banc_congelat() == banc_del_full, (
        "el JSON congelat NO coincideix amb el full etiquetat: o algú ha editat el full "
        "sense regenerar, o ha tocat el JSON a mà. Regenera amb "
        "`python -m datapoble_signals.banc_c4 --congela` (mai s'edita el JSON a mà)."
    )
    # tota l'estructura (procedència + recompte + banc) ha de reconstruir-se des del full
    import json

    congelat = json.loads(BANC_CONGELAT_PATH.read_text(encoding="utf-8"))
    assert congelat == construeix_banc_congelat(files)


def test_el_recompte_congelat_es_el_que_bea_va_etiquetar():
    """El recompte d'or, clavat: cap deriva silenciosa del nombre d'elegibles/fronteres."""
    r = recompte(parse_full())
    assert r["A"] == {
        "total": 26, "elegible": 0, "verd": 0, "groc": 0,
        "descartable": 25, "frontera": 1, "fora": 0,
    }
    assert r["B"] == {
        "total": 40, "elegible": 7, "verd": 4, "groc": 3,
        "descartable": 13, "frontera": 20, "fora": 0,
    }
    assert r["denominador_recall_B"] == 7
    # el banc congelat porta EXACTAMENT les 66 files etiquetades (cap «fora»)
    assert len(carrega_banc_congelat()) == 66
