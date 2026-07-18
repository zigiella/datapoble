"""Guardes del transcriptor del banc C4 (parser del full d'etiquetatge).

AVUI (pre-congelació): el full és a mig etiquetar per Bea — aquests tests validen el
PARSER i el VALIDADOR amb files sintètiques, i que el full REAL parseja (66 files, cap
etiqueta encara o les que hi hagi, sense petar). POST-CONGELACIÓ: s'hi afegirà el test de
fidelitat full↔JSON congelat (mateix patró que test_parafrasis).
"""

from datapoble_signals.banc_c4 import FULL_PATH, parse_full, recompte, valida


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
