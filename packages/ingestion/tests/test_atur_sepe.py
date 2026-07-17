"""Tests OFFLINE i deterministes del connector atur_sepe (D1).

Cap crida de xarxa: es treballa sobre DUES fixtures arxivades, extretes BYTE A
BYTE dels CSV reals del SEPE (ISO-8859-1, ``;``, CRLF):

  · ``sepe_paro_202606.csv``  — el mes 2026-06 sencer per a Catalunya (els 947
    del catàleg) + 5 municipis de FORA de Catalunya (Abla 04001, Madrid 28079,
    Zaragoza 50297, Fraga 22155, Vinaròs 12138) per guardar el filtre.
  · ``sepe_paro_200601_sense_zeros.csv`` — mes 2006-01 amb els codis TAL COM els
    servia el SEPE el 2006, SENSE zero-pad (``8022`` per Berga): la trampa del
    zero-pad és real i té test.

Guardes del contracte (C1 §1.1 + esmenes 2026-07-16):
  · filtre pel CATÀLEG sencer, mai per província — Gósol (25100, Lleida) i
    Gombrèn (17080, Girona) HAN de ser a la sèrie;
  · doctrina del «<5» = interval [1, 4], mai zero ni NaN silenciós;
  · trampa de codis (C3 §5): Castellar 08052, la Pobla 08166, Idescat 6 dígits → [:5];
  · byte-match de 3 municipis contra el CSV font.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from datapoble_ingestion import atur_sepe
from datapoble_ingestion.municipis import CATALUNYA, CATALUNYA_INE5

FIXTURES = Path(__file__).parent / "fixtures"
N_CATALEG = 947


@pytest.fixture(scope="module")
def rows_202606() -> list[dict]:
    text = (FIXTURES / "sepe_paro_202606.csv").read_bytes().decode(atur_sepe.ENCODING)
    return atur_sepe.parse_any_csv(text)


@pytest.fixture(scope="module")
def per_ine5(rows_202606) -> dict[str, dict]:
    return {r["ine5"]: r for r in rows_202606}


# --- Filtre pel catàleg sencer (mai per província) ---------------------------------

def test_cataleg_es_el_dels_947():
    # El registre derivat (codi6 Idescat → ine5 = codi6[:5]) és la clau del filtre.
    assert len(CATALUNYA) == N_CATALEG
    assert len(CATALUNYA_INE5) == N_CATALEG


def test_cobertura_completa_del_cataleg(rows_202606):
    # El mes arxivat cobreix EXACTAMENT els 947 del catàleg: ni un de menys
    # (cap pèrdua pel join de codis), ni un de més (cap intrús de fora).
    assert {r["ine5"] for r in rows_202606} == set(CATALUNYA_INE5)
    assert len(rows_202606) == N_CATALEG  # 1 fila per municipi i mes


def test_gosol_i_gombren_presents(per_ine5):
    # LA guarda de l'esmena: Gósol és Lleida (25100) i Gombrèn és Girona
    # (17080, Ripollès). Si algú torna a filtrar per província o comarca de
    # Barcelona, aquest test peta.
    assert per_ine5["25100"]["municipio"] == "Gósol"
    assert per_ine5["25100"]["provincia"] == "Lleida"
    assert per_ine5["17080"]["municipio"] == "Gombrèn"  # bytes reals de la font (è)
    assert per_ine5["17080"]["provincia"] == "Girona"


def test_fora_de_cataleg_exclosos(per_ine5):
    # La fixture porta 5 municipis de fora de Catalunya: cap no pot passar.
    for intrus in ("04001", "28079", "50297", "22155", "12138"):
        assert intrus not in per_ine5


def test_cataleg_buit_peta_amb_soroll():
    text = (FIXTURES / "sepe_paro_202606.csv").read_bytes().decode(atur_sepe.ENCODING)
    with pytest.raises(atur_sepe.SepeFormatError, match="catàleg"):
        atur_sepe.parse_any_csv(text, catalog={})


# --- Trampa de codis (C3 §5) -------------------------------------------------------

def test_trampa_de_codis_castellar_i_la_pobla(per_ine5):
    # Castellar de n'Hug = 08052 i la Pobla de Lillet = 08166, zero-padejats a 5.
    assert "08052" in per_ine5 and "08166" in per_ine5
    assert per_ine5["08052"]["municipio"] == "Castellar de n'Hug"
    assert per_ine5["08166"]["municipio"] == "Pobla de Lillet, La"
    # Idescat usa 6 dígits (5 INE + control): el tall [:5] del catàleg hi encaixa.
    assert all(len(i) == 5 for i in per_ine5)


def test_zero_pad_codis_2006_sense_zeros(per_ine5):
    # El 2006 el SEPE servia '8022' (Berga) sense zero: el pad a 5 és obligatori.
    text = (FIXTURES / "sepe_paro_200601_sense_zeros.csv").read_bytes().decode(atur_sepe.ENCODING)
    rows = {r["ine5"]: r for r in atur_sepe.parse_any_csv(text)}
    assert set(rows) == {"08022", "08052", "08166", "25100", "17080"}  # Abla 4001 fora
    assert rows["08022"]["municipio"] == "Berga"
    assert rows["08022"]["codigo_municipio"] == "8022"  # fidelitat a la font
    assert rows["08022"]["date"] == "2006-01"
    # Pre-2022 no hi ha emmascarament: Gósol duia un 4 EXACTE (interval degenerat).
    assert rows["25100"]["atur_registrat"] == 4
    assert rows["25100"]["atur_registrat_min"] == 4
    assert rows["25100"]["atur_registrat_max"] == 4
    assert rows["25100"]["atur_emmascarat"] is False


# --- Doctrina del «<5» (C1 §1.1, vinculant) ----------------------------------------

def test_doctrina_interval_1_4(per_ine5):
    # Gósol, juny 2026: total '<5' real a la font → interval [1, 4].
    gosol = per_ine5["25100"]
    assert gosol["total_paro_registrado"] == "<5"     # fidelitat: el literal es conserva
    assert gosol["atur_registrat"] is None            # cap número inventat
    assert gosol["atur_registrat_min"] == 1
    assert gosol["atur_registrat_max"] == 4
    assert gosol["atur_emmascarat"] is True


def test_doctrina_mai_zero_ni_nan_silencios(rows_202606):
    for r in rows_202606:
        if r["atur_emmascarat"]:
            # mai zero, mai NaN silenciós: el buit va SEMPRE acompanyat de
            # l'interval [1,4] i del flag que el declara.
            assert r["atur_registrat"] is None
            assert (r["atur_registrat_min"], r["atur_registrat_max"]) == (1, 4)
        else:
            v = r["atur_registrat"]
            assert v is not None and v >= 0
            assert r["atur_registrat_min"] == v == r["atur_registrat_max"]


def test_parse_total_valor_brut_peta():
    # Un valor no numèric i no '<5' no passa mai en silenci.
    with pytest.raises(atur_sepe.SepeFormatError):
        atur_sepe.parse_total("n/d")
    with pytest.raises(atur_sepe.SepeFormatError):
        atur_sepe.parse_total("")


def test_capcalera_mutada_peta():
    text = (FIXTURES / "sepe_paro_202606.csv").read_bytes().decode(atur_sepe.ENCODING)
    mutat = text.replace("total Paro Registrado", "total paro")
    with pytest.raises(atur_sepe.SepeFormatError, match="capçalera"):
        atur_sepe.parse_any_csv(mutat)


# --- Byte-match contra el CSV font (llistó C1 §4.2) --------------------------------

def test_byte_match_3_municipis(per_ine5):
    # Valors copiats LITERALMENT dels bytes del CSV del SEPE (juny 2026):
    #   202606;…;08019;Barcelona;61175;…
    #   202606;…;08022;Berga;760;…
    #   202606;…;17079;Girona;3886;…
    assert per_ine5["08019"]["total_paro_registrado"] == "61175"
    assert per_ine5["08019"]["atur_registrat"] == 61175
    assert per_ine5["08022"]["total_paro_registrado"] == "760"
    assert per_ine5["08022"]["atur_registrat"] == 760
    assert per_ine5["17079"]["total_paro_registrado"] == "3886"
    assert per_ine5["17079"]["atur_registrat"] == 3886


def test_date_format_yyyy_mm(rows_202606):
    # C1 §1.1: primera mètrica mensual del catàleg — el format queda fixat aquí.
    assert {r["date"] for r in rows_202606} == {"2026-06"}
    assert all(r["codigo_mes"] == "202606" for r in rows_202606)


def test_dataframe_tipat(rows_202606):
    df = atur_sepe.rows_to_dataframe(rows_202606)
    assert str(df["atur_registrat"].dtype) == "Int64"        # enter NULLABLE, no float NaN
    assert str(df["atur_registrat_min"].dtype) == "Int64"
    assert str(df["atur_registrat_max"].dtype) == "Int64"
    assert str(df["atur_emmascarat"].dtype) == "bool"
    n_masked = int(df["atur_emmascarat"].sum())
    assert n_masked == 139  # juny 2026: 139 dels 947 emmascarats (comptat del CSV font)
    assert int(df["atur_registrat"].isna().sum()) == n_masked  # cap NaN fora dels declarats
