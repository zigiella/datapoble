"""Tests de la CAPA B del banc C4 (tasca R1.5) — 100% offline.

Tres guardes, per aquest ordre d'importància:

1. **Anti-pre-etiquetatge de la COMPOSICIÓ (C4 §2 v2, vinculant):** cap
   `golden`/`semafor`/`motiu` a les fixtures, ordre mecànic. Qui etiqueta és NOMÉS la
   direcció humana, sobre A+B juntes. *(La guarda germana que exigia les columnes del full
   BUIDES es va retirar a la congelació —Bea ja ha etiquetat— i la substitueix la fidelitat
   full↔JSON congelat de test_banc_c4.py; vegeu el comentari on vivia.)*
2. **Transcripció mecànica fixtures↔taula** (patró `test_parafrasis`): les 7 columnes
   de dada (num…termini) de la segona taula de
   `docs/ajuntaments/banc-c4-etiquetatge.md` són exactament `render_fila_taula()` de cada
   entrada — si algú edita una fila a mà o toca la fixture sense regenerar, això cau. Les 3
   columnes d'etiqueta les posa Bea i es comparen a part (congelades).
3. **La trampa de noms:** «Sant Salvador de Guardiola» (Bages) ≠ «Guardiola de
   Berguedà». Les #9–10 de la capa A l'exerceixen; aquí queda l'àncora que un
   matching per substring confondria els dos municipis (avís per a R2).
"""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter
from pathlib import Path

from datapoble_signals import subvencions_bdns as bdns
from datapoble_signals.schema import SUBVENCIO_COLUMNS

from .fixtures_bdns import CONVOCATORIES as CONVOCATORIES_A
from .fixtures_bdns_capa_b import (
    CONVOCATORIES_B,
    DETALLS_B,
    META_B,
    PROGRAMES_B,
    per_codi_b,
    render_fila_taula,
    taula_capa_b,
)

DOC_ETIQUETATGE = (
    Path(__file__).resolve().parents[3] / "docs" / "ajuntaments" / "banc-c4-etiquetatge.md"
)

FINESTRA_DESDE = dt.date(2025, 7, 18)
FINESTRA_FINS = dt.date(2026, 7, 18)


def _files_b_del_doc() -> list[str]:
    """Les files 27+ de la taula del doc (la segona taula, la de la capa B)."""
    text = DOC_ETIQUETATGE.read_text(encoding="utf-8")
    seccio = text.split("## CAPA B")[1]
    return re.findall(r"^\| \d+ \| \[\d+\]\([^)]+\).*$", seccio, re.M)


# --- 1. La guarda anti-pre-etiquetatge (C4 §2 v2) -----------------------------

def test_cap_entrada_porta_golden_ni_cap_altre_camp_de_judici():
    """La fixture no pot contenir NI el camp: l'etiqueta és de la direcció.

    Aquesta guarda ES QUEDA després de la congelació: protegeix la COMPOSICIÓ (que
    Sondeig arxiva sense etiquetar), no l'estat del full. Les etiquetes viuen NOMÉS al
    full de Bea i al banc congelat, mai a les fixtures del repositori de la capa B.
    """
    prohibides = {"golden", "semafor", "semafor_esperat", "motiu", "motiu_daurat", "elegible"}
    for c in CONVOCATORIES_B:
        assert set(c.keys()) == {"programa", "busqueda", "detall"}
        assert not (prohibides & set(c.keys()))
        # ni colades dins de la captura literal de la font
        assert not (prohibides & set(c["detall"].keys()))
        assert not (prohibides & set(c["busqueda"].keys()))


# RETIRAT (2026-07-20, congelació del banc): test_les_tres_columnes_de_la_direccio_son_buides_al_full
# assertava que les columnes golden/semafor/motiu del full eren BUIDES — va complir la
# seva funció el dia que va néixer (impedir el pre-etiquetatge) i fins que Bea va etiquetar
# les 66 files (C4 §2 v2). Ara és FALSA PER DISSENY: el full JA porta etiquetes. La guarda
# que la substitueix viu a test_banc_c4.py (test_el_banc_congelat_coincideix_amb_el_full_i_no_deriva):
# congela el sentit contrari —el JSON d'or ha de coincidir amb el full etiquetat—, així ni
# el full ni el JSON deriven en silenci. NO es retira la guarda de composició de sobre
# (les FIXTURES segueixen sense etiquetes): només la que congelava el DOC sense etiquetar.


def test_ordre_mecanic_per_codi_cap_ordenacio_per_encaix():
    codis = [int(d["codigoBDNS"]) for d in DETALLS_B]
    assert codis == sorted(codis), "l'ordre és codigoBDNS ascendent (mecànic), res més"


def test_la_meta_declara_la_guarda_i_la_procedencia_de_cada_consulta():
    assert "golden" in META_B["guarda_anti_pre_etiquetatge"]
    assert "NOMES la direccio humana" in META_B["guarda_anti_pre_etiquetatge"]
    # cada programa de cada entrada és una consulta documentada amb paràmetres
    consultes = META_B["consultes_per_programa"]
    for programa in PROGRAMES_B:
        assert programa in consultes, f"programa sense consulta documentada: {programa}"
        assert "params" in consultes[programa]


def test_el_recompte_per_programa_coincideix_amb_les_consultes_declarades():
    reals = Counter(PROGRAMES_B)
    for programa, decl in META_B["consultes_per_programa"].items():
        assert reals[programa] == decl["resultats"], (
            f"{programa}: _meta declara {decl['resultats']} i la fixture en té {reals[programa]}"
        )


# --- 2. Transcripció mecànica fixtures ↔ taula (patró test_parafrasis) --------

def _sense_etiquetes(fila: str) -> str:
    """Treu les 3 columnes finals (golden/semafor/motiu) — de la direcció, no mecàniques.

    Post-congelació el full JA porta les etiquetes de Bea, així que la comparació de
    transcripció mecànica es fa sobre les 7 columnes de dada (num…termini): la resta és
    judici humà, congelat a part (test_banc_c4.py). Les etiquetes no porten mai `|` (si en
    portessin, el parser del transcriptor petaria i valida() ho cridaria)."""
    return re.sub(r"\|[^|]*\|[^|]*\|[^|]*\|\s*$", "|", fila)


def test_la_taula_del_doc_es_exactament_la_render_de_les_fixtures():
    """Cap fila editada a mà, cap fila de més, cap de menys, mateix ordre.

    La comparació és sobre les columnes MECÀNIQUES (num…termini): les 3 columnes
    d'etiqueta les posa Bea al full i divergeixen de la fixture PER DISSENY des de la
    congelació — la seva fidelitat la guarda test_banc_c4.py (full↔JSON congelat)."""
    del_doc = _files_b_del_doc()
    generades = taula_capa_b(primer_num=27)
    assert len(del_doc) == len(generades) == len(CONVOCATORIES_B) == 40
    for i, (fd, fg) in enumerate(zip(del_doc, generades)):
        fd_mec, fg_mec = _sense_etiquetes(fd), _sense_etiquetes(fg)
        assert fd_mec == fg_mec, (
            f"fila {27 + i} divergeix de la fixture (columnes mecàniques):\n"
            f"  doc: {fd_mec}\n  gen: {fg_mec}"
        )


def test_la_numeracio_continua_la_capa_a():
    # La capa A acaba a la #26: la B comença a la #27 (referència unívoca al banc).
    primera = _files_b_del_doc()[0]
    assert primera.startswith("| 27 | ")
    assert len(CONVOCATORIES_A) == 26


def test_render_termini_data_mana_sobre_text_i_multiregio_no_enganya():
    # data ISO quan la font la dona
    assert "| 2026-09-30 |" in render_fila_taula(1, per_codi_b("911751"))
    # textFin en prosa quan no hi ha data (cap parser: es mostra tal qual, truncat)
    assert "45 días hábiles a contar desde" in render_fila_taula(1, per_codi_b("873847"))
    # multiregió: la primera de 19 CCAA sola enganyaria (semblaria «només Galícia»)
    assert "ES11 - GALICIA (+18)" in render_fila_taula(1, per_codi_b("896067"))


# --- 3. La trampa de noms: Guardiola ------------------------------------------

def test_trampa_noms_sant_salvador_de_guardiola_no_es_guardiola_de_bergueda():
    """#9–10 de la capa A: Ajuntament de SANT SALVADOR DE GUARDIOLA (Bages).

    Un matching ingenu per substring «guardiola» diria que són del Berguedà.
    L'àncora que R2 hereta: els noms normalitzats NO són iguals — el municipi es
    casa pel nom COMPLET normalitzat (o per codi INE quan la font en doni, que
    la BDNS no en dona: verificat a R1), MAI per substring.
    """
    bages = bdns.normalitza_text("SANT SALVADOR DE GUARDIOLA")
    bergueda = bdns.normalitza_text("Guardiola de Berguedà")
    assert bages != bergueda
    # el perill és real: el substring hi és a TOTS DOS
    assert "guardiola" in bages and "guardiola" in bergueda
    # i cap dels dos noms complets conté l'altre (el matching per contenció també cau)
    assert bages not in bergueda and bergueda not in bages

    # les dues fixtures de la capa A que exerceixen la trampa hi són, intactes
    trampes = [
        c for c in CONVOCATORIES_A
        if "SANT SALVADOR DE GUARDIOLA" in (c["detall"]["organo"].get("nivel2") or "")
    ]
    assert {c["detall"]["codigoBDNS"] for c in trampes} == {"918981", "919009"}
    for c in trampes:
        regions = [r["descripcion"].strip() for r in c["detall"]["regiones"]]
        assert regions == ["ES511 - Barcelona"], "és el Bages (província BCN), no cal més"


def test_cap_convocant_de_la_capa_b_conte_guardiola():
    # Fet mecànic (cap judici): la trampa viu a la capa A (#9–10); a la B no hi
    # ha cap Guardiola — si un refresc de fixtures n'hi portés una, aquest test
    # obliga a re-mirar la trampa de noms en comptes de deixar-la passar callada.
    for d in DETALLS_B:
        organo = " ".join(str(d["organo"].get(f"nivel{i}") or "") for i in (1, 2, 3))
        assert "guardiola" not in bdns.normalitza_text(organo)


# --- Les fixtures són arxiu real, complet i dins de la finestra ---------------

def test_les_40_son_reals_uniques_i_normalitzables_al_contracte():
    assert len(CONVOCATORIES_B) == META_B["n_convocatories"] == 40
    codis = [d["codigoBDNS"] for d in DETALLS_B]
    assert len(set(codis)) == 40, "cap duplicat"
    for c in CONVOCATORIES_B:
        assert str(c["busqueda"]["numeroConvocatoria"]) == str(c["detall"]["codigoBDNS"])
        fitxa = bdns.normalize(c["detall"], c["busqueda"], vist_el="2026-07-18")
        assert tuple(fitxa.keys()) == SUBVENCIO_COLUMNS
        assert fitxa["enllac"].endswith(str(c["detall"]["codigoBDNS"]))


def test_totes_dins_de_la_finestra_declarada():
    for d in DETALLS_B:
        rec = dt.date.fromisoformat(d["fechaRecepcion"][:10])
        assert FINESTRA_DESDE <= rec <= FINESTRA_FINS


def test_cap_solapament_amb_la_capa_a_i_el_dedupe_documentat():
    codis_a = {c["detall"]["codigoBDNS"] for c in CONVOCATORIES_A}
    codis_b = {d["codigoBDNS"] for d in DETALLS_B}
    assert not (codis_a & codis_b), "una convocatòria no pot viure a les dues capes"
    # el solapament trobat per la cerca (918352) està DOCUMENTAT, no silenciat
    solapaments = META_B["solapaments_capa_a"]
    assert [s["codigoBDNS"] for s in solapaments] == ["918352"]
    assert "918352" in codis_a and "918352" not in codis_b


def test_el_conflicte_registral_abierto_false_amb_termini_futur_tambe_es_a_b():
    """El fet de R1 (abierto mana sobre el termini) té exemplars a la capa B.

    El Leader 2026 (911751, fi 30/09/2026) i camins (914337, fi 15/10/2026)
    porten `abierto=false` amb termini futur en la data d'arxiu: si R2 deduís
    l'estat del termini, prometria convocatòries a què ningú es pot presentar.
    """
    conflictes = {
        d["codigoBDNS"]
        for d in DETALLS_B
        if not d.get("abierto")
        and d.get("fechaFinSolicitud")
        and d["fechaFinSolicitud"][:10] > "2026-07-18"
    }
    assert {"911751", "914337"} <= conflictes
    for d in DETALLS_B:
        fitxa = bdns.normalize(d)
        assert fitxa["estat"] == ("oberta" if d.get("abierto") else "tancada")


def test_la_cerca_educada_esta_documentada_amb_el_recompte_de_crides():
    crides = META_B["crides_api"]
    assert crides["total"] == crides["exploracio_i_verificacio"] + crides["descarrega_final"]
    assert crides["total"] == 100
    assert "avisolegal" in META_B["avis_legal_font"]
    assert META_B["finestra"]["fechaDesde"] == "18/07/2025"
    assert META_B["finestra"]["fechaHasta"] == "18/07/2026"


def test_els_no_del_periode_queden_escrits():
    """El «no» és una resposta vàlida — i es versiona, no s'esfuma."""
    nos = META_B["programes_sense_resultat_al_periode"]
    for clau in (
        "cataleg_diba_com_a_convocatories",
        "idae_enllumenat",
        "caminos_naturales_estatal",
        "puosc",
        "consell_comarcal_bergueda",
    ):
        assert clau in nos, f"falta el «no» documentat: {clau}"
