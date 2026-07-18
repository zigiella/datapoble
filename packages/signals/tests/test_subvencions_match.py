"""Tests de R2 · filtre dur + puntuació + perfils (C3 §3/§2bis/§4/§6bis, C4 §1/§4).

100% OFFLINE: sintètiques + 5 reals arxivades (dev set PROPI — mai les 66 del
banc: la disjunció es verifica mecànicament aquí). Cap test llegeix ni cita cap
etiqueta daurada (no n'hi ha cap al repo: les etiquetes són de Bea).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from datapoble_signals import subvencions_match as match
from datapoble_signals.municipis import VALID_INE5
from datapoble_signals.perfils import (
    CONFIG_MUNICIPIS_DIR,
    PerfilError,
    carrega_perfil,
    carrega_perfil_per_ine5,
    carrega_perfils,
    valida_perfil,
)

from .fixtures_r2_dev import (
    DATA_REFERENCIA_REALS,
    DATA_REFERENCIA_SINTETIQUES,
    SINTETIQUES,
    ids_reals,
    reals,
    sintetiques,
)

GOLDEN_DIR = Path(__file__).resolve().parent / "fixtures" / "golden"


# ==============================================================================
# guarda anti-contaminació (C4 §4: el banc mesura, no entrena)
# ==============================================================================

def test_dev_set_disjunt_del_banc():
    """Cap fixture del dev set de R2 pot ser al banc C4 (capa A ni capa B)."""
    fixtures_dir = Path(__file__).resolve().parent / "fixtures"
    banc: set[str] = set()
    for name in ("bdns_convocatories.json", "bdns_capa_b.json"):
        doc = json.loads((fixtures_dir / name).read_text(encoding="utf-8"))
        banc |= {str(c["detall"]["codigoBDNS"]) for c in doc["convocatories"]}
    assert len(banc) >= 66, "el banc hauria de tenir les 26 (capa A) + 40 (capa B)"

    dev = ids_reals() | {s["fitxa"]["id_bdns"] for s in SINTETIQUES}
    solapament = dev & banc
    assert not solapament, (
        f"CONTAMINACIÓ: {solapament} són al banc C4 — el filtre no es pot "
        "desenvolupar contra el banc (C4 §4)"
    )


# ==============================================================================
# perfils (C3 §3 + §4 + §6bis) — validació fail-fast
# ==============================================================================

def _perfil_ok() -> dict:
    return {
        "tipus_beneficiari": "ajuntament",
        "poblacio": 1106,
        "poblacio_any": 2025,
        "territori": ["municipi:08166", "comarca:bergueda", "provincia:barcelona",
                       "catalunya", "estatal"],
        "materies": [{"nom": "turisme i patrimoni", "pes": 0.9}],
        "projectes_en_cartera": ["millora enllumenat públic"],
        "cofinancament_max": 20000,
        "destinataris": ["BEA"],
        "actiu": True,
    }


def test_perfil_valid_passa():
    assert valida_perfil(_perfil_ok(), origen="test") is not None


def test_perfil_camp_desconegut_falla():
    p = {**_perfil_ok(), "camp_inventat": 1}
    with pytest.raises(PerfilError, match="camps desconeguts"):
        valida_perfil(p, origen="test")


def test_perfil_pes_fora_de_rang_falla():
    p = _perfil_ok()
    p["materies"] = [{"nom": "turisme", "pes": 1.2}]
    with pytest.raises(PerfilError, match=r"fora de \[0,1\]"):
        valida_perfil(p, origen="test")


def test_perfil_sense_actiu_falla():
    p = _perfil_ok()
    del p["actiu"]
    with pytest.raises(PerfilError, match="absents"):
        valida_perfil(p, origen="test")


def test_perfil_correu_en_clar_falla():
    """§6bis: una «@» a destinataris → error (cap correu al repo públic)."""
    p = _perfil_ok()
    p["destinataris"] = ["algu@example.org"]
    with pytest.raises(PerfilError, match="6bis"):
        valida_perfil(p, origen="test")


def test_perfil_ine5_fora_del_bergueda_falla(tmp_path):
    """C3 §4: l'INE5 del nom de fitxer ha d'existir a BERGUEDA_INE5."""
    p = tmp_path / "08019-barcelona.yaml"  # Barcelona NO és al pilot
    p.write_text(yaml.safe_dump(_perfil_ok(), allow_unicode=True), encoding="utf-8")
    with pytest.raises(PerfilError, match="BERGUEDA_INE5"):
        carrega_perfil(p)


def test_perfils_reals_del_repo_carreguen():
    """Els perfils versionats a config/municipis/ passen la seva pròpia validació."""
    perfils = carrega_perfils()
    per_ine5 = {p["ine5"]: p for p in perfils}
    # v1 (C3 §3): actiu NOMÉS 08166; 08052 preparat i dorment.
    assert per_ine5["08166"]["actiu"] is True
    assert per_ine5["08052"]["actiu"] is False
    for p in perfils:
        assert p["ine5"] in VALID_INE5
        assert all("@" not in d for d in p["destinataris"])


def test_plantilla_default_valida_i_saltada():
    """_default.yaml: estructura vàlida (plantilla copiable) però MAI servida."""
    plantilla = CONFIG_MUNICIPIS_DIR / "_default.yaml"
    dades = yaml.safe_load(plantilla.read_text(encoding="utf-8"))
    assert valida_perfil(dades, origen="_default.yaml")["actiu"] is False
    assert all(p.get("ine5") != "_defa" for p in carrega_perfils())


def test_carrega_per_ine5():
    perfil = carrega_perfil_per_ine5("08166")
    assert perfil["ine5"] == "08166"
    assert perfil["poblacio"] == 1106 and perfil["poblacio_any"] == 2025


# ==============================================================================
# el filtre dur — sintètiques dirigides (una regla per cas)
# ==============================================================================

@pytest.fixture(scope="module")
def perfil_lillet() -> dict:
    return carrega_perfil_per_ine5("08166")


@pytest.fixture(scope="module")
def veredictes(perfil_lillet) -> dict[str, dict]:
    """id_dev → veredicte del filtre sobre les sintètiques (referència fixa)."""
    per_id = {}
    for s in SINTETIQUES:
        v = match.avalua(s["fitxa"], perfil_lillet, data_referencia=DATA_REFERENCIA_SINTETIQUES)
        per_id[s["id_dev"]] = v
    return per_id


def test_s01_elegible_clara_verda(veredictes):
    v = veredictes["S01-elegible-clara-enllumenat"]
    assert v["veredicte"] == "viva"
    assert v["semafor_determinista"] == "verd"
    assert v["marge_dies"] == 91  # 2026-07-01 → 2026-09-30
    assert any(m["nom"] == "eficiencia energetica i enllumenat" for m in v["materies"])
    assert "millora enllumenat públic" in v["projectes"]
    assert "enllumenat" in v["explicacio"]


def test_s02_trampa_sant_salvador_de_guardiola(veredictes):
    """«Sant Salvador de Guardiola» (Bages) ≠ «Guardiola de Berguedà».

    El descart és per convocant municipal ALIÈ, amb el nom complet del
    convocant al motiu — mai una confusió amb el municipi berguedà.
    """
    v = veredictes["S02-trampa-guardiola"]
    assert v["veredicte"] == "descartada"
    assert v["porta"] == "convocant"
    assert "sant salvador de guardiola" in v["motiu"].lower()
    assert "guardiola de bergueda" not in match.normalitza_text(v["motiu"])


def test_s03_consell_comarcal_bergueda_passa(veredictes):
    v = veredictes["S03-consell-bergueda"]
    assert v["veredicte"] == "viva"


def test_s04_termini_null_mai_descarta(veredictes):
    """C3 §2bis: NULL = «la font no en dona data», MAI «no hi ha termini»."""
    v = veredictes["S04-termini-null-oberta"]
    assert v["veredicte"] == "viva"
    assert v["termini_per_confirmar"] is True
    assert v["semafor_determinista"] == "groc"
    assert any("termini per confirmar" in n for n in v["notes"])


def test_s05_restriccio_poblacio_amb_padro_citat(veredictes):
    v = veredictes["S05-poblacio-massa-gran"]
    assert v["veredicte"] == "descartada"
    assert v["porta"] == "poblacio"
    assert ">20000 hab" in v["motiu"]
    assert "1106 hab (padró 2025)" in v["motiu"]  # el padró CITAT al perfil


def test_s06_beneficiaris_nomes_empreses(veredictes):
    v = veredictes["S06-nomes-empreses"]
    assert v["veredicte"] == "descartada"
    assert v["porta"] == "beneficiaris"


def test_s07_nominativa(veredictes):
    v = veredictes["S07-nominativa"]
    assert v["veredicte"] == "descartada"
    assert v["porta"] == "tipus"


def test_s08_ambit_estatal_passa(veredictes, perfil_lillet):
    """L'estatal EXISTEIX (decisió R1 ratificada): amb el perfil que el porta, passa."""
    v = veredictes["S08-estatal-passa"]
    assert v["veredicte"] == "viva"
    # I el contrari: un perfil SENSE estatal el descarta (mismatch positiu).
    perfil_sense = {**perfil_lillet, "territori": ["municipi:08166", "catalunya"]}
    fitxa = next(s["fitxa"] for s in SINTETIQUES if s["id_dev"] == "S08-estatal-passa")
    v2 = match.avalua(fitxa, perfil_sense, data_referencia=DATA_REFERENCIA_SINTETIQUES)
    assert v2["veredicte"] == "descartada" and v2["porta"] == "ambit"


def test_s09_termini_vencut(veredictes):
    v = veredictes["S09-termini-vencut"]
    assert v["veredicte"] == "descartada"
    assert "vençut" in v["motiu"] and "2026-06-15" in v["motiu"]


def test_s10_puntuacio_zero_no_filtra(veredictes):
    """R-FUNC §3: la puntuació ordena i gradua, MAI filtra."""
    v = veredictes["S10-score-zero-viva"]
    assert v["veredicte"] == "viva"
    assert v["puntuacio"] == 0.0
    assert v["semafor_determinista"] == "groc"


def test_s11_tancada_flag_vigent_descarta(veredictes):
    """Run diari (captura = referència): «abierto=false» respon «m'hi puc presentar?»."""
    v = veredictes["S11-tancada-flag-vigent"]
    assert v["veredicte"] == "descartada"
    assert "tancada" in v["motiu"]


def test_s12_projecte_en_cartera_dona_verd(veredictes):
    v = veredictes["S12-projecte-cartera"]
    assert v["veredicte"] == "viva"
    assert v["semafor_determinista"] == "verd"
    assert any("guia" in p for p in v["projectes"])


def test_cap_motiu_multilinia(veredictes):
    """C4 §7: cada descartada, UN motiu d'UNA línia (auditables una a una)."""
    for v in veredictes.values():
        if v["veredicte"] == "descartada":
            assert "\n" not in v["motiu"]
            assert len(v["motiu"]) < 200


# ==============================================================================
# matching lèxic — vores conegudes
# ==============================================================================

def test_cultura_no_matxeja_agricultura():
    """«cultura» és prefix de paraula: no dispara dins d'«agricultura»."""
    assert match._matxeja_materia("cultura i memoria", "ayudas a la agricultura ecologica") is False
    assert match._matxeja_materia("cultura i memoria", "actividades culturales del municipio") is True


def test_projecte_exigeix_dos_tokens():
    """Un sol token compartit no fa match de projecte (evita el soroll «guia»)."""
    assert match._matxeja_projecte("millora enllumenat públic", "mejora del alumbrado publico") is True
    assert match._matxeja_projecte("millora enllumenat públic", "guia de recursos locals") is False


# ==============================================================================
# reals de fora del banc (mode banc: es jutgen a la SEVA època, C4 §2)
# ==============================================================================

@pytest.fixture(scope="module")
def veredictes_reals(perfil_lillet) -> dict[str, dict]:
    per_id = {}
    for f in reals():
        v = match.avalua(f, perfil_lillet, data_referencia=DATA_REFERENCIA_REALS)
        per_id[f["id_bdns"]] = v
    return per_id


def test_real_diputacio_lleida_descartada(veredictes_reals):
    """809331 (Dip. Lleida, memòria democràtica): fora per província, tot i la matèria."""
    v = veredictes_reals["809331"]
    assert v["veredicte"] == "descartada"
    assert v["porta"] == "convocant"
    assert "lleida" in v["motiu"].lower() or "lerida" in v["motiu"].lower()


def test_real_ajuntament_oris_descartat(veredictes_reals):
    """810662 (Aj. d'Orís, eficiència energètica per als seus veïns): la trampa
    matèria-encaixa-però-convocant-aliè es resol pel convocant, mai per matèria."""
    v = veredictes_reals["810662"]
    assert v["veredicte"] == "descartada"
    assert v["porta"] == "convocant"
    assert "oris" in match.normalitza_text(v["motiu"])


def test_real_diba_viva_a_la_seva_epoca(veredictes_reals):
    """812061 (Diba BCN, termini 2025-03-06): VIVA jutjada a 2025-02-01 —
    el flag «tancada» és de la captura (2026-07-18), posterior al judici (C4 §2)."""
    v = veredictes_reals["812061"]
    assert v["veredicte"] == "viva"
    assert v["marge_dies"] == 33
    assert any("tancada en la captura" in n for n in v["notes"])


def test_reals_es_jutgen_a_avui_com_tancades(perfil_lillet):
    """Les mateixes reals jutjades AVUI (captura vigent) cauen per flag/termini:
    el mode diari i el mode banc són el mateix filtre amb data_referencia distinta."""
    for f in reals():
        v = match.avalua(f, perfil_lillet, data_referencia=date(2026, 7, 18))
        if v["veredicte"] == "descartada":
            assert v["porta"] in ("convocant", "vigencia", "beneficiaris", "tipus", "poblacio")


# ==============================================================================
# filtra() — ordre determinista i integritat del lot
# ==============================================================================

def test_filtra_conserva_totes_les_fitxes(perfil_lillet):
    """Cap fitxa desapareix en silenci: vives + descartades = totes (C4 §1)."""
    fitxes = sintetiques()
    r = match.filtra(fitxes, perfil_lillet, data_referencia=DATA_REFERENCIA_SINTETIQUES)
    assert len(r["vives"]) + len(r["descartades"]) == len(fitxes)


def test_filtra_ordena_verdes_primer(perfil_lillet):
    r = match.filtra(sintetiques(), perfil_lillet, data_referencia=DATA_REFERENCIA_SINTETIQUES)
    semafors = [v["semafor_determinista"] for v in r["vives"]]
    assert semafors == sorted(semafors, key=lambda s: 0 if s == "verd" else 1)


# ==============================================================================
# dry-run (R-FUNC §9.1) + snapshot (patró test_parafrasis)
# ==============================================================================

def test_dry_run_escriu_md_i_json(tmp_path, perfil_lillet):
    resum = match.dry_run(
        data_referencia=DATA_REFERENCIA_SINTETIQUES,
        ine5="08166",
        sortida=tmp_path,
        fitxes=sintetiques(),
    )
    md = (tmp_path / "radar-08166-2026-07-01.md").read_text(encoding="utf-8")
    payload = json.loads((tmp_path / "radar-08166-2026-07-01.json").read_text(encoding="utf-8"))
    assert resum["sortida_autoritzada"] is True  # lillet és l'actiu de la v1
    assert payload["n_verdes"] + payload["n_grogues"] + payload["n_descartades"] == len(SINTETIQUES)
    assert "Descartades" in md
    # C4 §7: totes les descartades apareixen al log amb el seu motiu.
    for d in payload["descartades"]:
        assert d["motiu"] in md


def test_dry_run_perfil_dorment_no_autoritza_sortida(tmp_path):
    """C3 §8.5: amb 08052 dorment, el log mostra el match i CAP sortida el conté."""
    resum = match.dry_run(
        data_referencia=DATA_REFERENCIA_SINTETIQUES,
        ine5="08052",
        sortida=tmp_path,
        fitxes=sintetiques(),
    )
    assert resum["actiu"] is False
    assert resum["sortida_autoritzada"] is False
    md = (tmp_path / "radar-08052-2026-07-01.md").read_text(encoding="utf-8")
    assert "NO autoritzada" in md
    assert resum["n_verdes"] + resum["n_grogues"] > 0  # el filtre SÍ que corre (C3 §3)


def test_dry_run_cli_amb_fixtures_reals(tmp_path):
    """La «ordre única» del R-FUNC §9.1 corre offline amb el JSON rejugable."""
    fixture = Path(__file__).resolve().parent / "fixtures" / "dev_r2_reals.json"
    rc = match.main([
        "--data", DATA_REFERENCIA_REALS.isoformat(),
        "--perfil", "08166",
        "--sortida", str(tmp_path),
        "--font", str(fixture),
    ])
    assert rc == 0
    assert (tmp_path / f"radar-08166-{DATA_REFERENCIA_REALS.isoformat()}.md").exists()


def test_snapshot_estructura_correu(tmp_path, perfil_lillet):
    """Snapshot GOLDEN de l'estructura (fixtures congelades → mateixos bytes).

    El format s'itera llegint el diff (patró test_parafrasis): si canvies el
    compositor a consciència, regenera el golden i revisa'l al PR.
    """
    match.dry_run(
        data_referencia=DATA_REFERENCIA_SINTETIQUES,
        ine5="08166",
        sortida=tmp_path,
        fitxes=sintetiques(),
    )
    produit = (tmp_path / "radar-08166-2026-07-01.md").read_text(encoding="utf-8")
    golden = (GOLDEN_DIR / "radar-08166-2026-07-01.md").read_text(encoding="utf-8")
    assert produit == golden, (
        "l'estructura del dry-run ha canviat — si és a consciència, regenera el "
        "golden (tests/fixtures/golden/) i explica-ho al PR"
    )
