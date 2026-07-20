"""Tests OFFLINE i deterministes del connector idescat_emex (D7 · E5/E11/E12).

Cap crida de xarxa: es treballa sobre una fixture arxivada BYTE A BYTE de la resposta
real de l'API (``idescat_emex_080522.json``, Castellar de n'Hug, baixada el 2026-07-20 de
``https://api.idescat.cat/emex/v1/dades.json?id=080522``).

El que guarden aquests tests:

  1. **L'any de referència hereta de l'avantpassat** (el forat que D7 va destapar). A
     l'EMEX l'``r`` viu al node de la TAULA, no a la fulla: el recorregut anterior només
     mirava ``leaf["r"]`` i per això la columna ``year`` de la raw sortia NULL a 12 dels
     13 indicadors. Amb l'herència, cada fila sap de quin període és.

  2. **Els vintages NO són tots el mateix**, i és el moll de l'os de la frescor (E5):
     població i franges d'edat són del Cens de població ANUAL (2025); els habitatges,
     del Cens d'habitatge (2021). Un tauler que ho pinti tot amb la mateixa data menteix.

  3. **Les franges d'edat quadren amb el total** (E12): 0-14 + 65-84 + 85+ ≤ població, i
     la resta (la franja intermèdia derivada) és positiva. És la precondició de la regla
     «deriva-la NOMÉS si quadra» que aplica ``mart_municipi``.

  4. **Byte-match dels valors** contra la fixture (166 habitants, 276 habitatges…), que
     són els mateixos que ``docs/data-sources.md`` cita per a Castellar.

NOTA sobre la SÈRIE (E11), verificat en viu el 2026-07-20 i documentat al contracte:
l'operació ``dades`` de l'API EMEX només admet els filtres ``id``, ``i`` i ``tipus``
(documentació oficial https://www.idescat.cat/dev/api/emex/). NO hi ha cap paràmetre
temporal: els que s'hi provin s'ignoren en silenci. EMEX és una FOTO, no una sèrie —
per això no hi ha cap test de sèrie aquí: no hi ha res a provar, hi ha un límit a declarar.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from datapoble_ingestion import idescat_emex

FIXTURES = Path(__file__).parent / "fixtures"
CODI6 = "080522"  # Castellar de n'Hug


@pytest.fixture(scope="module")
def payload() -> dict:
    return json.loads((FIXTURES / f"idescat_emex_{CODI6}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rows(payload) -> list[dict]:
    """Files aplanades tal com les produiria `fetch_municipi`, però sense xarxa:
    es replica el seu cos sobre la fixture (el `requests.get` és l'única part que
    aquest test no cobreix, i és a propòsit: el CI no toca la xarxa)."""
    out: list[dict] = []
    seen: set[str] = set()
    for leaf, year in idescat_emex._iter_leaves(payload):
        fid = leaf.get("id")
        if fid in idescat_emex.INDICATORS and fid not in seen:
            seen.add(fid)
            out.append({
                "codi6": CODI6,
                "ine5": CODI6[:5],
                "indicator_id": fid,
                "indicator": idescat_emex.INDICATORS[fid],
                "label": leaf.get("calt") or leaf.get("c"),
                "year": year,
                "value_municipi": idescat_emex._municipi_value(leaf.get("v")),
            })
    return out


@pytest.fixture(scope="module")
def per_indicator(rows) -> dict[str, dict]:
    return {r["indicator"]: r for r in rows}


def test_indicadors_trobats(per_indicator):
    """Els indicadors nuclears del tauler han de sortir de la fixture."""
    for nom in ("poblacio", "pob_0_14", "pob_65_84", "pob_85_mes",
                "hab_total", "hab_principal", "hab_noprincipal"):
        assert nom in per_indicator, f"indicador absent de la fixture: {nom}"


def test_any_hereta_de_lavantpassat(per_indicator):
    """CAP indicador es pot quedar sense any.

    És la regressió concreta del forat: abans d'heretar l'`r`, només `altitud_m` (que en
    porta un de propi a la fulla) tenia any; la resta sortia NULL. Si això torna a passar,
    la frescor del tauler es queda sense base i el contracte ha d'escriure els vintages a mà.
    """
    sense_any = [nom for nom, r in per_indicator.items() if r["year"] is None]
    assert not sense_any, f"indicadors sense any de referència: {sorted(sense_any)}"


def test_vintages_diferents_per_bloc(per_indicator):
    """Població i franges d'edat = Cens anual (2025); habitatges = Cens 2021.

    No és cosmètic: és la raó per la qual `hab_*` porta `actualitzacio: puntual` al
    contracte encara que la font (EMEX) es refresqui cada any.
    """
    for nom in ("poblacio", "pob_0_14", "pob_65_84", "pob_85_mes"):
        assert per_indicator[nom]["year"] == "2025", (
            f"{nom}: any {per_indicator[nom]['year']!r}, s'esperava 2025 (Cens de població anual)"
        )
    for nom in ("hab_total", "hab_principal", "hab_noprincipal"):
        assert per_indicator[nom]["year"] == "2021", (
            f"{nom}: any {per_indicator[nom]['year']!r}, s'esperava 2021 (Cens d'habitatge)"
        )
    anys = {per_indicator[n]["year"] for n in ("poblacio", "hab_total")}
    assert len(anys) == 2, "població i habitatges han de tenir vintages DIFERENTS"


def test_franges_edat_quadren(per_indicator):
    """Precondició de la regla «deriva la 15-64 només si quadra» (E12).

    La suma de les tres franges d'EMEX no pot passar de la població, i la resta (la
    franja intermèdia) ha de ser positiva. Si això falla, `mart_municipi` ha d'emetre
    NULL — i llavors aquest test és qui avisa que ha passat.
    """
    pob = int(per_indicator["poblacio"]["value_municipi"])
    b0 = int(per_indicator["pob_0_14"]["value_municipi"])
    b65 = int(per_indicator["pob_65_84"]["value_municipi"])
    b85 = int(per_indicator["pob_85_mes"]["value_municipi"])
    assert b0 + b65 + b85 <= pob, (
        f"les franges sumen {b0 + b65 + b85} > població {pob}: la partició no quadra"
    )
    intermedia = pob - b0 - b65 - b85
    assert intermedia >= 0
    # Byte-match: 166 − 9 − 36 − 6 = 115 (calculat a mà sobre la fixture).
    assert (pob, b0, b65, b85, intermedia) == (166, 9, 36, 6, 115)


def test_valors_byte_match(per_indicator):
    """Àncores de Castellar de n'Hug (les mateixes de docs/data-sources.md)."""
    esperat = {
        "poblacio": "166",
        "hab_total": "276",
        "hab_principal": "71",
        "hab_noprincipal": "205",
    }
    for nom, val in esperat.items():
        assert per_indicator[nom]["value_municipi"] == val, (
            f"{nom}: {per_indicator[nom]['value_municipi']!r} ≠ {val!r}"
        )


def test_valor_municipal_es_el_primer_camp():
    """`v` ve com a «municipi,comarca,Catalunya»: només el primer camp és del municipi.

    Confondre-ho publicaria la xifra de Catalunya com si fos la del poble.
    """
    assert idescat_emex._municipi_value("166,41523,8124126") == "166"
    # marcadors de dada absent → None (mai 0, mai la cadena literal)
    for buit in ("_", "-", ""):
        assert idescat_emex._municipi_value(f"{buit},1,2") is None


def test_sense_duplicats(rows):
    """Alguns ids surten repetits a fitxes diferents: només se n'agafa el primer."""
    ids = [r["indicator_id"] for r in rows]
    assert len(ids) == len(set(ids)), "hi ha indicadors duplicats a la sortida"
