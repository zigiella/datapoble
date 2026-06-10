"""Tests del motor de convergència (turisme × sequera) → ``convergencia_bergueda``.

Corren **offline i deterministes** (aptes per CI): construeixen tres parquets
sintètics minúsculs (``fixtures_convergencia``) on cada quadrant i cada flag és
conegut a mà, i verifiquen la lògica del motor sobre ells via ``build_sql``. A
més, si el parquet real ja existeix al repo
(``data/events/convergencia_bergueda.parquet``), s'hi reapliquen invariants
estructurals i les **àncores honestes** del Berguedà.
"""
from __future__ import annotations

import duckdb
import pytest

from datapoble_signals import convergencia as cv
from datapoble_signals.config import events_path
from datapoble_signals.convergencia import (
    CONVERGENCIA_COLUMNS,
    LLINDAR_SEQUERA_ALTA,
    QUADRANTS,
)

from .fixtures_convergencia import (
    M_AS,
    M_AT,
    M_BB,
    M_BT,
    MUNI_FIXTURE,
    write_fixture_parquets,
)

REAL_PARQUET = "convergencia_bergueda.parquet"


# --- Resultat sobre les fixtures sintètiques ---------------------------------

@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    """Executa el motor sobre els parquets sintètics → DataFrame indexat per ine5."""
    tmp = tmp_path_factory.mktemp("conv_fx")
    paths = write_fixture_parquets(tmp)
    sql = cv.build_sql(
        contractacio_parquet=paths["contractacio"],
        sequera_parquet=paths["sequera"],
        mart_parquet=paths["mart"],
        muni_registry=MUNI_FIXTURE,
    )
    df = duckdb.connect().execute(sql).df()
    return df.set_index("ine5")


# --- El contracte de sortida --------------------------------------------------

def test_columnes_del_contracte_en_ordre(synth):
    # El motor projecta exactament CONVERGENCIA_COLUMNS, en ordre (ine5 és l'índex).
    cols = ("ine5", *tuple(c for c in synth.columns))
    assert cols == CONVERGENCIA_COLUMNS


def test_cobertura_de_tots_els_municipis(synth):
    # Una fila per municipi del registre injectat (cap perdut, cap duplicat).
    assert sorted(synth.index) == sorted(MUNI_FIXTURE)
    assert len(synth) == len(MUNI_FIXTURE)


# --- 2) Reconstrucció d'intervals de sequera ---------------------------------

def test_severitat_mitjana_ponderada_per_dies(synth):
    # UE A: 0.4 del 2021-01-01 al 2021-03-01 (59 dies), després 0.8 fins 2025-05-16.
    # La mitjana ponderada per dies ha de seure molt a prop de 0.8 (el tram llarg),
    # clarament per sobre del llindar de sequera alta.
    sev_at = synth.loc[M_AT, "sequera_severitat_mitjana"]
    assert sev_at > LLINDAR_SEQUERA_ALTA
    assert 0.78 < sev_at < 0.8  # dominada pel tram de 0.8, lleugerament rebaixada
    # Pic = 0.8 (excepcionalitat assolida).
    assert synth.loc[M_AT, "sequera_severitat_pic"] == pytest.approx(0.8)


def test_sequera_baixa_zona_normalitat(synth):
    # UE B: normalitat (0.1) tot el període → mitjana 0.1, sota el llindar.
    assert synth.loc[M_AS, "sequera_severitat_mitjana"] == pytest.approx(0.1)
    assert synth.loc[M_AS, "sequera_severitat_mitjana"] < LLINDAR_SEQUERA_ALTA
    # Cap mes en alerta (severitat mai >= 0.6).
    assert synth.loc[M_AS, "sequera_mesos_alerta"] == pytest.approx(0.0)


def test_mesos_alerta_compta_nomes_severitat_alta(synth):
    # UE A seu en 0.8 (>=0.6) des del 2021-03-01 fins 2025-05-16 → molts mesos.
    assert synth.loc[M_AT, "sequera_mesos_alerta"] > 40


# --- FRONTERA HONESTA: la sequera és de la zona (UE), no del municipi --------

def test_sequera_identica_dins_la_unitat_explotacio(synth):
    # M_AT i M_BT són la MATEIXA UE 'A' → severitat de sequera IDÈNTICA.
    # És el cor de la frontera: la sequera no discrimina dins la zona.
    assert (
        synth.loc[M_AT, "sequera_severitat_mitjana"]
        == synth.loc[M_BT, "sequera_severitat_mitjana"]
    )
    assert (
        synth.loc[M_AT, "sequera_unitat_explotacio"]
        == synth.loc[M_BT, "sequera_unitat_explotacio"]
        == "A"
    )


def test_flag_sequera_per_zona_sempre_cert(synth):
    # La sequera SEMPRE prové de la UE (és supramunicipal en origen).
    assert synth["flag_sequera_per_zona"].all()


# --- 4) Els quatre quadrants (la lectura creuada) ----------------------------

def test_quadrants_assignats_correctament(synth):
    assert synth.loc[M_AT, "quadrant"] == "alt_turisme_alta_sequera"   # la hipòtesi
    assert synth.loc[M_BT, "quadrant"] == "baix_turisme_alta_sequera"
    assert synth.loc[M_AS, "quadrant"] == "alt_turisme_baixa_sequera"
    assert synth.loc[M_BB, "quadrant"] == "baix_turisme_baixa_sequera"


def test_quadrant_dins_del_vocabulari(synth):
    assert set(synth["quadrant"]).issubset(set(QUADRANTS))


def test_convergencia_score_es_producte_normalitzat(synth):
    # convergencia_score = (index_turisme/100) * sequera_severitat_mitjana.
    for ine5, row in synth.iterrows():
        esperat = (row["turisme_index"] / 100.0) * row["sequera_severitat_mitjana"]
        assert row["convergencia_score"] == pytest.approx(esperat)
    # El candidat alt×alt té el score més alt de tots.
    assert synth["convergencia_score"].idxmax() == M_AT


# --- Flags honestos -----------------------------------------------------------

def test_flag_turisme_poc_fiable_micromunicipi(synth):
    # M_AT té poblacio 150 (< 300) → poc fiable, encara que el turisme sigui alt.
    assert bool(synth.loc[M_AT, "flag_turisme_poc_fiable"]) is True
    # M_AS (800 hab, confiança alta) → fiable.
    assert bool(synth.loc[M_AS, "flag_turisme_poc_fiable"]) is False


def test_flag_contractacio_feble_quan_no_contracta(synth):
    # Només M_AT contracta turisme propi → els altres tenen el senyal secundari mut.
    assert bool(synth.loc[M_AT, "flag_turisme_contractacio_feble"]) is False
    assert synth.loc[M_AT, "turisme_contractacio_n"] == 3
    assert synth.loc[M_AT, "turisme_contractacio_eur"] == pytest.approx(23000.0)
    for muni in (M_BT, M_AS, M_BB):
        assert bool(synth.loc[muni, "flag_turisme_contractacio_feble"]) is True
        assert synth.loc[muni, "turisme_contractacio_n"] == 0


def test_turisme_score_es_index_sobre_100(synth):
    for ine5, row in synth.iterrows():
        assert row["turisme_score"] == pytest.approx(row["turisme_index"] / 100.0)
        assert 0.0 <= row["turisme_score"] <= 1.0


# --- El resum honest derivat del DataFrame -----------------------------------

def test_resum_marca_convergents_no_fiables(synth):
    # En el cas sintètic l'únic convergent (M_AT) és micromunicipi → cap fiable.
    s = cv._summary_from_df(synth.reset_index())
    assert s["per_quadrant"]["alt_turisme_alta_sequera"] == 1
    assert s["convergents"] == [MUNI_FIXTURE[M_AT]]
    assert s["convergents_fiables"] == []  # el convergent és poc fiable
    assert set(s["unitats_explotacio"]) == {"A", "B"}


# --- Invariants i àncores sobre el parquet REAL (si existeix) -----------------

@pytest.mark.skipif(
    not events_path(REAL_PARQUET).exists(),
    reason="parquet de convergència no generat (cal córrer el motor)",
)
def test_parquet_real_invariants_i_ancores():
    p = str(events_path(REAL_PARQUET))
    con = duckdb.connect()
    con.execute(f"CREATE VIEW c AS SELECT * FROM read_parquet('{p}')")

    def q(s):
        return con.execute(s).fetchone()[0]

    # Estructura: 31 municipis del Berguedà, un per fila, sense nulls clau.
    assert q("SELECT count(*) FROM c") == 31
    assert q("SELECT count(DISTINCT ine5) FROM c") == 31
    assert q("SELECT count(*) FROM c WHERE quadrant IS NULL") == 0
    assert q("SELECT count(*) FROM c WHERE sequera_severitat_mitjana IS NULL") == 0
    assert q("SELECT count(*) FROM c WHERE turisme_index IS NULL") == 0
    # Quadrant dins del vocabulari.
    assert q(
        "SELECT count(*) FROM c WHERE quadrant NOT IN "
        f"({','.join(repr(x) for x in QUADRANTS)})"
    ) == 0
    # Scores dins de rang.
    assert q("SELECT count(*) FROM c WHERE turisme_score < 0 OR turisme_score > 1") == 0
    assert q(
        "SELECT count(*) FROM c WHERE convergencia_score < 0 OR convergencia_score > 1"
    ) == 0

    # ÀNCORA honesta 1: la sequera és per zona → exactament 3 UEs al Berguedà
    # (06 Capçalera, 10 Embassament, 16 Mig Llobregat) i dins cada UE la severitat
    # és idèntica (un sol valor distint de severitat per UE).
    assert q("SELECT count(DISTINCT sequera_unitat_explotacio) FROM c") == 3
    assert q(
        "SELECT max(n) FROM (SELECT count(DISTINCT sequera_severitat_mitjana) n "
        "FROM c GROUP BY sequera_unitat_explotacio)"
    ) == 1
    # flag_sequera_per_zona sempre cert.
    assert q("SELECT count(*) FROM c WHERE flag_sequera_per_zona = FALSE") == 0

    # ÀNCORA honesta 2: la hipòtesi NO es confirma — el quadrant alt×alt és petit i
    # els seus municipis són tots poc fiables (micromunicipis), i la correlació de
    # rang turisme↔sequera és negativa. (Un "no" honest, no forçat.)
    n_conv = q("SELECT count(*) FROM c WHERE quadrant = 'alt_turisme_alta_sequera'")
    assert n_conv <= 6  # minoria clara dels 31
    n_conv_fiable = q(
        "SELECT count(*) FROM c WHERE quadrant = 'alt_turisme_alta_sequera' "
        "AND flag_turisme_poc_fiable = FALSE"
    )
    assert n_conv_fiable == 0  # cap convergent robust

    # ÀNCORA honesta 3: Berga (08022, UE 16) — molta sequera, poc turisme, molta
    # població → el cas que il·lustra la inversió (la tensió hídrica del corredor
    # no l'explica el turisme).
    berga_quad = q("SELECT quadrant FROM c WHERE ine5 = '08022'")
    assert berga_quad == "baix_turisme_alta_sequera"
