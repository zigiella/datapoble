"""Tests de la capa d'intel·ligència institucional de licitacions (PAS 1).

Tot **offline i determinista** (apte per CI): la taxonomia és pura, i el
repartiment + l'indicador es proven sobre un DataFrame **sintètic** d'events
(municipal + comarcal) on cada cas és conegut a mà. A més, si el parquet REAL de
contractació existeix, es reapliquen els invariants estructurals i les àncores
honestes (cobertura de classificació, conservació de l'import al repartiment).
"""
from __future__ import annotations

import pandas as pd
import pytest

from datapoble_signals import licitacions as lic
from datapoble_signals.config import events_path
from datapoble_signals.licitacions_taxonomy import (
    CARACTERS_SENYAL,
    CONTRACT_SIGNAL_TYPES,
    TEMES_ADMINISTRATIUS,
    caracter_senyal,
    classify_licitacio,
    contract_signal_type,
    tema_administratiu,
)
from datapoble_signals.municipis import BERGUEDA_INE5


# =============================================================================
# 1) Taxonomia territorial (pura)
# =============================================================================

def test_tema_cpv_especific_guanya():
    # CPV museu (9252) → cultura, confiança alta, mètode cpv.
    tema, conf, metode = tema_administratiu("92521000-9", "qualsevol cosa")
    assert tema == "cultura"
    assert conf == 0.9
    assert metode == "cpv"


def test_tema_cpv_familia_2_digits():
    # CPV 90 (medi ambient) sense paraula override → residus, conf 0.8.
    tema, conf, metode = tema_administratiu("90511000-2", None)
    assert tema == "residus"
    assert conf == 0.8
    assert metode == "cpv"


def test_tema_override_transport_escolar():
    # CPV 60 (transport) és ambigu; 'escolar' a l'objecte → educacio, no mobilitat.
    tema, conf, metode = tema_administratiu(
        "60130000-8", "Servei de transport escolar dels instituts de la comarca"
    )
    assert tema == "educacio"
    assert metode == "cpv+kw"
    assert conf == 0.7


def test_tema_override_obra_aigua():
    # CPV 45 (obra) ambigu; 'abastament d aigua' → aigua, no urbanisme.
    tema, _, metode = tema_administratiu(
        "45231300-8", "Obres de la xarxa d'abastament d'aigua potable"
    )
    assert tema == "aigua"
    assert metode == "cpv+kw"


def test_tema_keyword_sense_cpv():
    tema, conf, metode = tema_administratiu(None, "Servei de recollida selectiva de residus")
    assert tema == "residus"
    assert conf == 0.55
    assert metode == "keyword"


def test_tema_altres_quan_res():
    tema, conf, metode = tema_administratiu(None, "xyzzy quelcom inclassificable 123")
    assert tema == "altres"
    assert conf == 0.3
    assert metode == "cap"


def test_caracter_emergencia():
    car, conf = caracter_senyal("Obres d'urgència al col·lector per dany del temporal", "aigua")
    assert car == "emergencia"
    assert conf == 0.6


def test_caracter_diagnostic():
    car, _ = caracter_senyal("Redacció del projecte executiu de la nova escola", "educacio")
    assert car == "diagnostic"


def test_caracter_promocio():
    car, _ = caracter_senyal("Campanya de promoció turística del Berguedà", "turisme")
    assert car == "promocio"


def test_caracter_ordinari_per_defecte():
    car, conf = caracter_senyal("Servei de recollida de residus municipals", "residus")
    assert car == "ordinari"
    assert conf == 0.45


def test_signal_type_administracio_es_context():
    sig, _ = contract_signal_type("administracio", "cpv", "Auditoria de comptes")
    assert sig == "nomes_context"


def test_signal_type_evidencia_directa():
    sig, conf = contract_signal_type("turisme", "cpv", "Servei de socorrisme a la piscina i visitants")
    assert sig == "evidencia_directa"
    assert conf >= 0.7


def test_signal_type_proxy_fort_vs_feble():
    # 'mobilitat' no té paraules d'evidència directa → separa net proxy_fort/feble
    # segons el mètode del tema (CPV vs paraula).
    fort, _ = contract_signal_type("mobilitat", "cpv", "Obres de pavimentació del vial")
    feble, _ = contract_signal_type("mobilitat", "keyword", "asfaltat del camí")
    assert fort == "proxy_fort"
    assert feble == "proxy_feble"


def test_classify_licitacio_retorna_les_tres_dimensions():
    c = classify_licitacio("92312130-1", "Serveis tècnics per a La Patum")
    assert c["tema_administratiu"] in TEMES_ADMINISTRATIUS
    assert c["caracter_senyal"] in CARACTERS_SENYAL
    assert c["contract_signal_type"] in CONTRACT_SIGNAL_TYPES
    assert 0.0 <= c["tema_confianca"] <= 1.0
    assert 0.0 <= c["caracter_confianca"] <= 1.0
    assert 0.0 <= c["signal_confianca"] <= 1.0


def test_classify_es_determinista():
    a = classify_licitacio("60130000-8", "Transport escolar lot 2")
    b = classify_licitacio("60130000-8", "Transport escolar lot 2")
    assert a == b


# =============================================================================
# 2) Repartiment supramunicipal (sobre events sintètics)
# =============================================================================

# Un DataFrame mínim d'events enriquits: 1 municipal (Berga) + 4 comarcals que
# disparen cada mètode de repartiment.
def _synthetic_enriched() -> pd.DataFrame:
    base_cols = {
        "comarca": "Berguedà", "font_url": "https://x", "categoria": "fet",
        "fase": "anticipacio", "cpv": None, "data": None, "data_tipus": "adjudicacio",
        "font": None, "raw_id": None, "dataset_id": "ybgg-dgi6", "font_clau": "contractacio",
        "tipus_senyal": "altres", "confianca": 0.3,
    }
    rows = [
        # municipal — denominador de la dependència (Berga)
        {**base_cols, "event_id": "m1", "ine5": "08022", "nom_muni": "Berga",
         "ambit": "municipal", "objecte": "Servei de neteja viària", "import": 100000.0},
        # comarcal · per_poblacio (tema social)
        {**base_cols, "event_id": "c_pob", "ine5": None, "nom_muni": "Consell",
         "ambit": "comarcal", "objecte": "Servei d'inclusió social a la comarca", "import": 31000.0},
        # comarcal · igualitari (tema turisme, sense municipi nomenat)
        {**base_cols, "event_id": "c_igu", "ine5": None, "nom_muni": "Consell",
         "ambit": "comarcal", "objecte": "Promoció turística del territori", "import": 3100.0},
        # comarcal · directe_textual (nomena Puig-reig)
        {**base_cols, "event_id": "c_dir", "ine5": None, "nom_muni": "Consell",
         "ambit": "comarcal", "objecte": "Obres del col·lector de Puig-reig", "import": 50000.0},
        # comarcal · no_assignable (administracio interna)
        {**base_cols, "event_id": "c_noa", "ine5": None, "nom_muni": "Consell",
         "ambit": "comarcal", "objecte": "Auditoria de comptes del Consell", "import": 9000.0},
    ]
    df = pd.DataFrame(rows)
    return lic.enrich_events(df)


# Població sintètica (només per al per_poblacio); 3 municipis amb pesos clars.
_POP_SYN = {"08022": 8000, "08175": 1500, "08092": 500}  # Berga, Puig-reig, Gironella


def test_allocation_methods_assignats_correctament():
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    by_ev = alloc.drop_duplicates("event_id").set_index("event_id")["allocation_method"].to_dict()
    assert by_ev["c_pob"] == "per_poblacio"
    assert by_ev["c_igu"] == "igualitari"
    assert by_ev["c_dir"] == "directe_textual"
    assert by_ev["c_noa"] == "no_assignable"
    # el municipal NO es reparteix (no apareix a la taula d'allocation)
    assert "m1" not in by_ev


def test_allocation_directe_va_al_municipi_nomenat():
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    dirrows = alloc[alloc["event_id"] == "c_dir"]
    assert len(dirrows) == 1
    assert dirrows.iloc[0]["ine5"] == "08175"  # Puig-reig
    assert dirrows.iloc[0]["allocation_share"] == 1.0
    assert dirrows.iloc[0]["import_assignat"] == 50000.0


def test_allocation_no_assignable_no_va_a_cap_municipi():
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    noa = alloc[alloc["event_id"] == "c_noa"]
    assert len(noa) == 1
    assert pd.isna(noa.iloc[0]["ine5"])  # cap municipi receptor
    assert noa.iloc[0]["allocation_share"] == 0.0
    assert noa.iloc[0]["import_assignat"] == 0.0


def test_allocation_per_poblacio_pondera_per_poblacio():
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    pob = alloc[(alloc["event_id"] == "c_pob") & (alloc["ine5"].notna())]
    shares = pob.set_index("ine5")["allocation_share"].to_dict()
    # Berga (8000) > Puig-reig (1500) > Gironella (500); municipis sense pop → 0.
    assert shares["08022"] > shares["08175"] > shares["08092"] > 0
    # share total ~ 1.0 (els municipis amb població sumen 1; la resta 0).
    assert abs(pob["allocation_share"].sum() - 1.0) < 1e-6


def test_allocation_igualitari_reparteix_a_tots_31():
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    igu = alloc[alloc["event_id"] == "c_igu"]
    assert len(igu) == len(BERGUEDA_INE5)  # 31 parts
    assert abs(igu["allocation_share"].sum() - 1.0) < 1e-5


def test_allocation_conserva_import():
    # La suma d'import_assignat == import_total per a tot event assignable.
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    for ev in ("c_pob", "c_igu", "c_dir"):
        sub = alloc[alloc["event_id"] == ev]
        total = sub["import_total"].iloc[0]
        assignat = sub["import_assignat"].sum()
        assert abs(assignat - total) < 0.5, ev


def test_allocation_columnes_contracte():
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    assert list(alloc.columns) == list(lic.REPARTIMENT_COLUMNS)


def test_per_poblacio_sense_mart_cau_a_igualitari():
    # Sense població (mart absent) el per_poblacio degrada a igualitari, i ho marca.
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, {})  # pop buida
    pob = alloc[alloc["event_id"] == "c_pob"]
    assert (pob["allocation_method"] == "igualitari").all()
    assert len(pob) == len(BERGUEDA_INE5)


def test_per_poblacio_ignora_poblacio_de_fora_de_la_comarca():
    # REGRESSIÓ del vermell de main (destapat a R1, arreglat 2026-07-17): des de
    # F2 el mart_municipi cobreix Catalunya sencera (947 munis) i _load_population
    # retorna TOT el país. El denominador del per_poblacio ha de ser NOMÉS la
    # població dels municipis on es reparteix (els 31): amb sum(pop.values())
    # les quotes sumaven pop(31)/pop(CAT) ≈ 0,5% i es perdien ~7,67 M€ en silenci.
    enriched = _synthetic_enriched()
    pop_catalunya = {**_POP_SYN, "08019": 1_600_000, "17079": 100_000}  # BCN i Girona
    alloc = lic.build_allocation(enriched, pop_catalunya)
    pob = alloc[(alloc["event_id"] == "c_pob") & (alloc["ine5"].notna())]
    # Cap euro no marxa fora dels 31: les quotes sumen 1 i l'import es conserva.
    assert set(pob["ine5"]) <= set(BERGUEDA_INE5)
    assert abs(pob["allocation_share"].sum() - 1.0) < 1e-6
    assert abs(pob["import_assignat"].sum() - pob["import_total"].iloc[0]) < 0.5
    # I les quotes són les de la població COMARCAL (Berga 8000/10000 = 0.8),
    # no les diluïdes per Catalunya.
    berga = pob[pob["ine5"] == "08022"].iloc[0]
    assert abs(berga["allocation_share"] - 0.8) < 1e-6


# =============================================================================
# 3) Indicador dependencia_supramunicipal (sobre events sintètics)
# =============================================================================

def test_dependencia_columnes_i_31_municipis():
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    dep = lic.build_dependencia(enriched, alloc, _POP_SYN)
    assert list(dep.columns) == list(lic.DEPENDENCIA_COLUMNS)
    assert len(dep) == len(BERGUEDA_INE5)


def test_dependencia_berga_te_ratio():
    # Berga contracta 100000 propi i rep una part del per_poblacio (la majoritària).
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    dep = lic.build_dependencia(enriched, alloc, _POP_SYN)
    berga = dep[dep["ine5"] == "08022"].iloc[0]
    assert berga["import_municipal_directe"] == 100000.0
    assert berga["n_contractes_municipal"] == 1
    assert berga["import_serveis_comarcals_assignables"] > 0
    assert berga["dependencia_supramunicipal"] is not None
    assert berga["dependencia_lectura"] in (
        "autonom", "dependencia_mitjana", "molt_dependent"
    )


def test_dependencia_micromunicipi_sense_propi():
    # Un municipi que no contracta res propi → ratio NULL, lectura no_contracta_propi,
    # però amb numerador > 0 (rep de dalt): el rastre de la seva dependència.
    enriched = _synthetic_enriched()
    alloc = lic.build_allocation(enriched, _POP_SYN)
    dep = lic.build_dependencia(enriched, alloc, _POP_SYN)
    # Gisclareny (08093) no contracta i no és nomenat enlloc.
    g = dep[dep["ine5"] == "08093"].iloc[0]
    assert g["import_municipal_directe"] == 0.0
    assert g["n_contractes_municipal"] == 0
    assert pd.isna(g["dependencia_supramunicipal"])
    assert g["dependencia_lectura"] == "no_contracta_propi"
    # rep almenys la part igualitària del turisme → numerador > 0
    assert g["import_serveis_comarcals_assignables"] > 0


# =============================================================================
# 4) Reaplica invariants/àncores al parquet REAL si existeix
# =============================================================================

@pytest.mark.skipif(
    not events_path(lic.CONTRACTACIO_PARQUET).exists(),
    reason="parquet de contractació no generat (cal córrer el connector amb xarxa)",
)
def test_real_parquet_cobertura_i_conservacio():
    out = lic.compute()
    enriched, alloc, dep = out["enriquit"], out["repartiment"], out["dependencia"]

    # Cobertura: la classificació és heurística però NO majoritàriament 'altres'.
    n = len(enriched)
    altres = int((enriched["tema_administratiu"] == "altres").sum())
    assert n == 2770  # àncora dels 31 municipis del Berguedà
    assert altres / n < 0.20  # ~15% als 31 munis (taxonomia afinada al pilot de 3 òrgans); encara molt sota el 38% antic — re-afinar als 31 és feina de seguiment

    # Tots els temes/caràcters/signal_types dins del vocabulari.
    assert set(enriched["tema_administratiu"]).issubset(set(TEMES_ADMINISTRATIUS))
    assert set(enriched["caracter_senyal"]).issubset(set(CARACTERS_SENYAL))
    assert set(enriched["contract_signal_type"]).issubset(set(CONTRACT_SIGNAL_TYPES))

    # Repartiment: només es reparteixen els 713 comarcals.
    n_ev_repartits = alloc.drop_duplicates("event_id").shape[0]
    assert n_ev_repartits == 713

    # Conservació de l'import: sum(import_assignat) ≈ sum(import_total) dels
    # events assignables (exclou no_assignable, que té ine5 NULL).
    assignables = alloc[alloc["allocation_method"] != "no_assignable"]
    ev_imports = assignables.drop_duplicates("event_id")["import_total"].dropna().sum()
    assignat = alloc["import_assignat"].dropna().sum()
    assert abs(assignat - ev_imports) < 5.0  # tolerància d'arrodoniment

    # Indicador: 31 municipis, i ara TOTS contracten alguna cosa de propi. Abans el
    # pilot només ingeria 3 òrgans (Berga, Castellar, Consell) → 29 sortien «sense
    # contractació pròpia», que era un artefacte de cobertura; obrir el filtre als 31 ho corregeix.
    assert len(dep) == 31
    amb_propi = dep[dep["n_contractes_municipal"] > 0]["ine5"].tolist()
    assert len(amb_propi) == 31
