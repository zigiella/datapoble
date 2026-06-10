"""Tests del contracte de la capa d'events i del connector de contractació.

Els tests del contracte (els 5 invariants que exigeix el brief) corren **offline**
sobre una mostra de files crues normalitzades (``fixtures.SAMPLE_RAW``), sense
xarxa → deterministes i aptes per a CI. A més, si el parquet del pilot ja existeix
(``data/events/events_bergueda.parquet``), s'hi reapliquen els mateixos invariants.
"""
from __future__ import annotations

import datetime as dt

import pytest

from datapoble_signals import contractacio
from datapoble_signals.config import events_path
from datapoble_signals.events import events_to_frame
from datapoble_signals.municipis import (
    VALID_INE5,
    classify_ambit,
    comarca_from_organ,
    is_supramunicipal,
)
from datapoble_signals.schema import (
    AMBITS,
    CATEGORIES,
    DATA_TIPUS,
    EVENT_COLUMNS,
    FASES,
    MIN_REQUIRED,
    TIPUS_SENYAL,
)
from datapoble_signals.taxonomy import CONF_ALTRES, CONF_CPV, CONF_KEYWORD, classify

from .fixtures import SAMPLE_RAW


@pytest.fixture(scope="module")
def events() -> list[dict]:
    """Events normalitzats des de la mostra crua (sense xarxa)."""
    return [contractacio.normalize(r) for r in SAMPLE_RAW]


# --- El contracte: estructura -------------------------------------------------

def test_event_te_totes_les_columnes_del_contracte(events):
    for ev in events:
        assert tuple(ev.keys()) == EVENT_COLUMNS  # ordre i presència exactes
        for col in MIN_REQUIRED:
            assert col in ev


# --- Els 5 invariants del brief ----------------------------------------------

def test_event_id_unic(events):
    ids = [ev["event_id"] for ev in events]
    assert len(ids) == len(set(ids)), "event_id ha de ser únic (lots inclosos)"


def test_lots_del_mateix_expedient_tenen_event_id_distint(events):
    # EXP-LOT-9 apareix dos cops (lot 1 i lot 3): han de ser events distints.
    lot_ids = [ev["event_id"] for ev in events if ev["raw_id"] == "EXP-LOT-9"]
    assert len(lot_ids) == 2
    assert len(set(lot_ids)) == 2


def test_dates_parsejables(events):
    for ev in events:
        d = ev["data"]
        if d is None:
            continue  # permès (algun expedient pre-mercat no té cap data)
        # Forma ISO 'YYYY-MM-DD', parsejable a date.
        parsed = dt.date.fromisoformat(d)
        assert isinstance(parsed, dt.date)
        assert ev["data_tipus"] in DATA_TIPUS


def test_cap_event_sense_font_url(events):
    for ev in events:
        assert ev["font_url"], "tot event ha de tenir font_url (traçabilitat)"
        assert ev["font_url"].startswith("http")


def test_ine5_valid_o_ambit_no_municipal(events):
    for ev in events:
        if ev["ambit"] == "municipal":
            assert ev["ine5"] in VALID_INE5, f"ine5 invàlid: {ev['ine5']}"
        else:
            assert ev["ine5"] is None, "supra no té ine5 (és codi de comarca, no municipi)"


def test_imports_no_negatius(events):
    for ev in events:
        if ev["import"] is not None:
            assert ev["import"] >= 0


# --- Vocabularis controlats ---------------------------------------------------

def test_valors_dins_dels_vocabularis(events):
    for ev in events:
        assert ev["ambit"] in AMBITS
        assert ev["fase"] in FASES
        assert ev["categoria"] in CATEGORIES
        assert ev["tipus_senyal"] in TIPUS_SENYAL


def test_contracte_sempre_es_fet_i_anticipacio(events):
    # Decisió del brief: el contracte EXISTEIX (fet) i és anticipació.
    for ev in events:
        assert ev["categoria"] == "fet"
        assert ev["fase"] == "anticipacio"


# --- La lliçó supramunicipal (micromunicipi → supra) -------------------------

def test_consell_comarcal_es_comarcal_sense_ine5(events):
    consell = [ev for ev in events if "Comarcal" in (ev["font"] or "")]
    assert consell, "la mostra ha d'incloure el Consell Comarcal"
    for ev in consell:
        assert ev["ambit"] == "comarcal"
        assert ev["ine5"] is None
        assert ev["comarca"] == "Berguedà"


def test_classify_ambit():
    assert classify_ambit("Ajuntament de Berga") == "municipal"
    assert classify_ambit("Consell Comarcal del Berguedà") == "comarcal"
    assert classify_ambit("Mancomunitat de Municipis") == "supramunicipal"
    assert classify_ambit("Consorci del Lluçanès") == "supramunicipal"


def test_is_supramunicipal():
    assert is_supramunicipal("Consell Comarcal del Berguedà")
    assert not is_supramunicipal("Ajuntament de Berga")


def test_comarca_from_organ():
    assert comarca_from_organ("Consell Comarcal del Berguedà") == "Berguedà"
    assert comarca_from_organ("Ajuntament de Berga") is None


# --- La taxonomia (heurística CPV + paraules clau) ---------------------------

def test_classify_cpv_fort():
    tipus, conf, metode = classify("92312130-1", "qualsevol cosa")
    assert tipus == "turisme_cultura_events"
    assert conf == CONF_CPV
    assert metode == "cpv"


def test_classify_cpv_neteja_residus():
    tipus, conf, _ = classify("90511000-2", None)
    assert tipus == "neteja_residus"
    assert conf == CONF_CPV


def test_classify_cpv_multivalor():
    # Format de la font: codis concatenats amb '||'. El primer que casa guanya.
    tipus, conf, _ = classify("71318100-1||90910000-9", None)
    assert tipus == "neteja_residus"
    assert conf == CONF_CPV


def test_classify_keyword_quan_no_cpv():
    tipus, conf, metode = classify(None, "Servei de neteja viària i recollida")
    assert tipus == "neteja_residus"
    assert conf == CONF_KEYWORD
    assert metode == "keyword"


def test_classify_altres_quan_res():
    tipus, conf, metode = classify(None, "Subministrament de material d'oficina")
    assert tipus == "altres"
    assert conf == CONF_ALTRES
    assert metode == "cap"


def test_confianca_marca_cpv_vs_keyword(events):
    # El senyal de CPV ha de tenir més confiança que el de paraula clau.
    berga_patum = next(ev for ev in events if ev["raw_id"] == "EXP-CULT-1")
    berga_neteja_kw = next(ev for ev in events if ev["raw_id"] == "EXP-NETEJA-1")
    assert berga_patum["confianca"] == CONF_CPV
    assert berga_neteja_kw["confianca"] == CONF_KEYWORD
    assert berga_patum["confianca"] > berga_neteja_kw["confianca"]


def test_font_url_fallback_quan_falta_enllac(events):
    # EXP-MISC-1 no porta enllaç → font_url cau a la URL del dataset (mai NULL).
    misc = next(ev for ev in events if ev["raw_id"] == "EXP-MISC-1")
    assert misc["font_url"]
    assert "ybgg-dgi6" in misc["font_url"]


def test_fallback_data_publicacio(events):
    # EXP-OBERT-1 no té data d'adjudicació → fallback a publicació, marcat.
    obert = next(ev for ev in events if ev["raw_id"] == "EXP-OBERT-1")
    assert obert["data"] is not None
    assert obert["data_tipus"] == "publicacio"


# --- El frame es construeix amb les columnes del contracte -------------------

def test_frame_te_columnes_del_contracte(events):
    df = events_to_frame(events)
    assert list(df.columns) == list(EVENT_COLUMNS)
    assert len(df) == len(events)


# --- Reaplica els invariants al parquet del pilot si existeix -----------------

@pytest.mark.skipif(
    not events_path("events_bergueda.parquet").exists(),
    reason="parquet del pilot no generat (cal córrer el connector amb xarxa)",
)
def test_parquet_pilot_compleix_invariants():
    import duckdb

    p = str(events_path("events_bergueda.parquet"))
    con = duckdb.connect()
    con.execute(f"CREATE VIEW e AS SELECT * FROM read_parquet('{p}')")
    def q(s):
        return con.execute(s).fetchone()[0]

    assert q("SELECT count(*) FROM e") > 0
    assert q("SELECT count(*) - count(DISTINCT event_id) FROM e") == 0  # únic
    assert q("SELECT count(*) FROM e WHERE font_url IS NULL") == 0      # traçable
    assert q("SELECT count(*) FROM e WHERE import < 0") == 0            # no negatiu
    # ine5 vàlid O ambit != municipal
    assert q("SELECT count(*) FROM e WHERE ambit='municipal' AND ine5 IS NULL") == 0
    assert q("SELECT count(*) FROM e WHERE ambit!='municipal' AND ine5 IS NOT NULL") == 0
    # totes les dates no nul·les són DATE vàlides (TRY_CAST ja ho garanteix al COPY)
    assert q("SELECT count(*) FROM e WHERE data IS NOT NULL AND TRY_CAST(data AS DATE) IS NULL") == 0
    # àncores de Talaia (municipal = Berga 577 + Castellar 23 = 600; comarcal 695)
    assert q("SELECT count(*) FROM e WHERE ambit='comarcal'") == 695
    assert q("SELECT count(*) FROM e WHERE ine5='08022'") == 577   # Berga
    assert q("SELECT count(*) FROM e WHERE ine5='08052'") == 23    # Castellar
