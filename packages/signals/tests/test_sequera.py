"""Tests del connector de sequera (ACA, ``i5n8-43cw``) → events.

Corren **offline** sobre una mostra de files crues reals (``fixtures_sequera``),
sense xarxa → deterministes i aptes per a CI. Reapliquen els mateixos invariants
del contracte d'events que la contractació, més els específics de la sequera. Si
el parquet de sequera ja existeix (``data/events/events_sequera_bergueda.parquet``),
s'hi reapliquen els invariants sobre dades reals.
"""
from __future__ import annotations

import datetime as dt

import pytest

from datapoble_signals import sequera
from datapoble_signals.config import events_path
from datapoble_signals.events import events_to_frame
from datapoble_signals.municipis import VALID_INE5
from datapoble_signals.schema import (
    AMBITS,
    CATEGORIES,
    DATA_TIPUS,
    EVENT_COLUMNS,
    FASES,
    MIN_REQUIRED,
    TIPUS_SENYAL,
)
from datapoble_signals.sequera import CONF_PER_ESTAT, confianca_estat

from .fixtures_sequera import SAMPLE_RAW

SEQUERA_PARQUET = "events_sequera_bergueda.parquet"


@pytest.fixture(scope="module")
def events() -> list[dict]:
    """Events de sequera normalitzats des de la mostra crua (sense xarxa)."""
    return [sequera.normalize(r) for r in SAMPLE_RAW]


# --- El contracte: estructura -------------------------------------------------

def test_event_te_totes_les_columnes_del_contracte(events):
    for ev in events:
        assert tuple(ev.keys()) == EVENT_COLUMNS  # ordre i presència exactes
        for col in MIN_REQUIRED:
            assert col in ev


# --- Invariants del contracte (els mateixos que la contractació) -------------

def test_event_id_unic(events):
    ids = [ev["event_id"] for ev in events]
    assert len(ids) == len(set(ids)), "event_id ha de ser únic"


def test_event_id_te_prefix_propi(events):
    # Namespace propi del rastre → no col·lisiona amb els 'con_' de contractació.
    for ev in events:
        assert ev["event_id"].startswith("seq_")


def test_canvi_nomes_pluviometric_es_event_distint(events):
    # Castellar de n'Hug, mateixa data i hidrològic (PREALERTA), pluviomètric
    # distint → dues files a la font → dos events distints.
    castellar = [ev for ev in events if ev["ine5"] == "08052"]
    assert len(castellar) == 2
    assert len({ev["event_id"] for ev in castellar}) == 2


def test_dates_parsejables_i_tipus_correcte(events):
    for ev in events:
        d = ev["data"]
        assert d is not None, "tota declaració de sequera porta data de canvi"
        parsed = dt.date.fromisoformat(d)
        assert isinstance(parsed, dt.date)
        assert ev["data_tipus"] == "inici_vigencia"
        assert ev["data_tipus"] in DATA_TIPUS


def test_cap_event_sense_font_url(events):
    for ev in events:
        assert ev["font_url"], "tot event ha de tenir font_url (traçabilitat)"
        assert ev["font_url"].startswith("http")
        assert "i5n8-43cw" in ev["font_url"]


def test_ine5_valid_i_municipal(events):
    # La sequera baixa a municipi → ambit municipal i ine5 sempre vàlid.
    for ev in events:
        assert ev["ambit"] == "municipal"
        assert ev["ine5"] in VALID_INE5, f"ine5 invàlid: {ev['ine5']}"


def test_ine5_derivat_de_ine6():
    # Gósol: INE6 '251001' → ine5 '25100' (el cas límit del registre).
    gosol = sequera.normalize(
        {"codi_municipi": "251001", "municipi": "Gósol",
         "data_canvi_estat_sequera": "2023-05-11T00:00:00.000",
         "estat_sequera_hidrol_gic": "EXCEPCIONALITAT"}
    )
    assert gosol["ine5"] == "25100"
    assert gosol["nom_muni"] == "Gósol"  # nom canònic del registre


def test_import_es_null(events):
    # Una declaració de sequera no té import econòmic.
    for ev in events:
        assert ev["import"] is None


# --- Vocabularis controlats ---------------------------------------------------

def test_valors_dins_dels_vocabularis(events):
    for ev in events:
        assert ev["ambit"] in AMBITS
        assert ev["fase"] in FASES
        assert ev["categoria"] in CATEGORIES
        assert ev["tipus_senyal"] in TIPUS_SENYAL


def test_sempre_aigua_sequera_fet_realitzacio(events):
    # Decisió del brief: la declaració EXISTEIX (fet) i és contemporània
    # (realitzacio, no anticipacio com un contracte).
    for ev in events:
        assert ev["tipus_senyal"] == "aigua_sequera"
        assert ev["categoria"] == "fet"
        assert ev["fase"] == "realitzacio"


# --- Confiança ordinal per severitat (la frontera dada/inferència) -----------

def test_confianca_creix_amb_severitat():
    # El senyal de pressió creix amb l'estat: normalitat < prealerta < alerta <
    # excepcionalitat < emergència. (No és certesa de la dada: és força del senyal.)
    assert (
        confianca_estat("NORMALITAT")
        < confianca_estat("PREALERTA")
        < confianca_estat("ALERTA")
        < confianca_estat("EXCEPCIONALITAT")
        < confianca_estat("EMERGÈNCIA")
    )


def test_confianca_robusta_a_accents_i_majuscules():
    # La font pot dur mojibake/variants: normalitzem accents i caixa.
    assert confianca_estat("excepcionalitat") == confianca_estat("EXCEPCIONALITAT")
    assert confianca_estat("Emergència II") == CONF_PER_ESTAT["EMERGENCIA II"]


def test_confianca_dins_rang(events):
    for ev in events:
        assert 0.0 <= ev["confianca"] <= 1.0


def test_confianca_estat_desconegut_es_mig():
    # Un estat no catalogat NO inventa severitat: senyal mig.
    assert confianca_estat("ESTAT_INEXISTENT") == sequera.CONF_DEFAULT
    assert confianca_estat(None) == sequera.CONF_DEFAULT


def test_excepcionalitat_te_confianca_alta(events):
    berga_exc = next(
        ev for ev in events
        if ev["ine5"] == "08022" and "EXCEPCIONALITAT" in ev["objecte"]
    )
    assert berga_exc["confianca"] == CONF_PER_ESTAT["EXCEPCIONALITAT"]


# --- L'objecte conserva el context de la fila --------------------------------

def test_objecte_inclou_estat_i_unitat(events):
    berga_exc = next(
        ev for ev in events
        if ev["ine5"] == "08022" and "EXCEPCIONALITAT" in ev["objecte"]
    )
    assert "EXCEPCIONALITAT" in berga_exc["objecte"]
    assert "Mig Llobregat" in berga_exc["objecte"]       # unitat d'explotació
    assert "SEQUERA EXTREMA" in berga_exc["objecte"]     # estat pluviomètric


def test_raw_id_es_unitat_explotacio(events):
    # Traçabilitat: la UE és el nivell de decisió de l'ACA.
    berga = next(ev for ev in events if ev["ine5"] == "08022")
    assert berga["raw_id"] == "16"  # codi UE Mig Llobregat


# --- El frame es construeix amb les columnes del contracte -------------------

def test_frame_te_columnes_del_contracte(events):
    df = events_to_frame(events)
    assert list(df.columns) == list(EVENT_COLUMNS)
    assert len(df) == len(events)


# --- Reaplica els invariants al parquet de sequera si existeix ----------------

@pytest.mark.skipif(
    not events_path(SEQUERA_PARQUET).exists(),
    reason="parquet de sequera no generat (cal córrer el connector amb xarxa)",
)
def test_parquet_sequera_compleix_invariants():
    import duckdb

    p = str(events_path(SEQUERA_PARQUET))
    con = duckdb.connect()
    con.execute(f"CREATE VIEW e AS SELECT * FROM read_parquet('{p}')")

    def q(s):
        return con.execute(s).fetchone()[0]

    assert q("SELECT count(*) FROM e") > 0
    assert q("SELECT count(*) - count(DISTINCT event_id) FROM e") == 0   # únic
    assert q("SELECT count(*) FROM e WHERE font_url IS NULL") == 0       # traçable
    # tot municipal amb ine5 vàlid (la sequera baixa a municipi)
    assert q("SELECT count(*) FROM e WHERE ambit != 'municipal'") == 0
    assert q("SELECT count(*) FROM e WHERE ine5 IS NULL") == 0
    # tot el rastre és aigua_sequera / fet / realitzacio
    assert q("SELECT count(*) FROM e WHERE tipus_senyal != 'aigua_sequera'") == 0
    assert q("SELECT count(*) FROM e WHERE categoria != 'fet'") == 0
    assert q("SELECT count(*) FROM e WHERE fase != 'realitzacio'") == 0
    # dates totes presents i vàlides
    assert q("SELECT count(*) FROM e WHERE data IS NULL") == 0
    assert q("SELECT count(*) FROM e WHERE TRY_CAST(data AS DATE) IS NULL") == 0
    # confiança dins rang
    assert q("SELECT count(*) FROM e WHERE confianca < 0 OR confianca > 1") == 0
    # àncores: 31 municipis del Berguedà, tots coberts
    assert q("SELECT count(DISTINCT ine5) FROM e") == 31
