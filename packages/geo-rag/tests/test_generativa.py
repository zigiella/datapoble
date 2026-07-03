"""Tests OFFLINE de l'arnès generatiu (cap crida d'API; TORCH-FREE).

Cobreixen les peces deterministes del contracte 08 / protocol 10:
extractor de xifres (milers catalans inclosos), parser del tag ACCIO, conjunt permès
des d'un context sintètic, marcatge de la gàbia + comptabilitat d'intervencions,
puntuació nu/gàbia, parsing del veredicte del validador, i les FORMES del context
(build_context sobre build(None)) — amb l'assert clau que la prosa determinista del
router MAI entra al context del generador.

REGLA DE LA CLAU: cap test viu per defecte. Si mai se n'afegeix un, ha d'anar guardat
per OPENROUTER_API_KEY **i** GENERATIVA_LIVE=1 alhora (vegeu _LIVE al final).
"""

import json
import os

import pytest

from datapoble_geo_rag.build import build
from datapoble_geo_rag.generativa import (
    REGISTER_THRESHOLD,
    allowed_numbers,
    apply_cage,
    build_context,
    content_check,
    extract_numbers,
    hard_validation,
    parse_output,
    parse_verdict,
    score_trial,
    user_message,
)
from datapoble_geo_rag.router import route

# Guard per a un eventual test viu: MAI corre per defecte (calen les DUES condicions).
_LIVE = bool(os.environ.get("OPENROUTER_API_KEY")) and os.environ.get("GENERATIVA_LIVE") == "1"

# --- 1. Extractor de xifres -------------------------------------------------------------


def test_extract_numbers_plain_integers():
    assert extract_numbers("Berga en té 76 i un rang 418–720.") == {76, 418, 720}


def test_extract_numbers_catalan_thousands():
    # 16.669 és UNA xifra (milers catalans), no {16, 669}.
    assert extract_numbers("La presència és 16.669 persones.") == {16669}


def test_extract_numbers_mixed_thousands_and_plain():
    got = extract_numbers("Estimació 2.126 (rang 1.986–2.316), padró 2214, llindar ≥1.000 hab.")
    assert got == {2126, 1986, 2316, 2214, 1000}


def test_extract_numbers_empty_and_no_digits():
    assert extract_numbers("") == set()
    assert extract_numbers("cap xifra aquí") == set()


# --- 2. Parser del tag ACCIO --------------------------------------------------------------


def test_parse_output_canonical():
    accio, prose = parse_output("ACCIO: RESPONDRE\nBerga té molta presència.")
    assert accio == "respondre"
    assert prose == "Berga té molta presència."


def test_parse_output_case_and_whitespace_variants():
    assert parse_output("accio:   abstenir\nprosa")[0] == "abstenir"
    assert parse_output("  ACCIO : RESPONDRE  \nprosa")[0] == "respondre"
    assert parse_output("Accio: Abstenir\nprosa")[0] == "abstenir"


def test_parse_output_accented_and_decorated_variants():
    assert parse_output("ACCIÓ: ABSTENIR\nprosa")[0] == "abstenir"
    assert parse_output("**ACCIO: RESPONDRE**\nprosa")[0] == "respondre"


def test_parse_output_leading_blank_lines_and_fences():
    accio, prose = parse_output("\n```\nACCIO: ABSTENIR\nNo ho afirmo.\n```")
    assert accio == "abstenir"
    assert prose == "No ho afirmo."


def test_parse_output_missing_or_malformed_tag_is_error_format():
    accio, prose = parse_output("Berga té 16.669 habitants.")
    assert accio == "error_format"
    assert "16.669" in prose
    assert parse_output("ACCIO: POTSER\nprosa")[0] == "error_format"
    assert parse_output("")[0] == "error_format"


# --- 3. Conjunt permès des d'un context sintètic -------------------------------------------

_SYNTH_CTX = {
    "intent": "valor_municipi",
    "municipi": {
        "nom": "Vilatest",
        "register": "soroll",
        "estimacio": 527.4,
        "rang_baix": 418.0,
        "rang_alt": 720.0,
        "padro": 663,
        "etca_oficial": None,
    },
    "collision_group": [
        {"nom": "Vilatest", "estimacio": 527.4, "etca_oficial": None},
        {"nom": "Salomtest", "estimacio": 527.4, "etca_oficial": 1121.0},
    ],
    "distinguishable": False,  # bool: NO ha d'entrar com a xifra
}


def test_allowed_numbers_fields_roundings_counts_and_threshold():
    allowed = allowed_numbers(_SYNTH_CTX)
    assert {527, 418, 720, 663, 1121} <= allowed  # camps + arrodoniments (527.4 → 527)
    assert REGISTER_THRESHOLD in allowed  # el 1000 doctrinal («≥1.000 hab»)
    assert 2 in allowed  # recompte de la llista collision_group
    assert 0 not in allowed and 1 not in allowed  # el bool False/True no és cap xifra


def test_hard_validation_flags_only_untraceable_numbers():
    prose = "Al voltant de 527 (rang 418–720), padró 663; jo diria 9.999 segur."
    assert hard_validation(prose, _SYNTH_CTX) == [9999]
    assert hard_validation("Entre 418 i 720, amb padró 663.", _SYNTH_CTX) == []


# --- 4. Gàbia: marcatge + comptabilitat d'intervencions -------------------------------------


def test_cage_cuts_invented_number_and_marks_it():
    prose = "La xifra és 9.999 amb tota seguretat, sobre un padró de 663."
    caged, interventions = apply_cage(prose, _SYNTH_CTX, [9999], [])
    assert "⟦9.999: xifra no verificada⟧" in caged
    assert "9.999 amb tota seguretat" not in caged
    assert "663" in caged  # la xifra traçable NO es toca
    assert interventions == ["xifra_tallada(9999)"]


def test_cage_appends_deterministic_guardrails_from_context_fields():
    prose = "Hi viuen 527 persones."
    caged, interventions = apply_cage(
        prose, _SYNTH_CTX, [], ["to_ferm_sobre_soroll", "collisio_amagada"]
    )
    # Postdata de soroll: rang + padró TRETS DEL CONTEXT, mai del generador.
    assert "418–720" in caged and "663" in caged
    assert "no es distingeix del marge" in caged
    # Postdata de col·lisió: nomena els ALTRES membres del grup.
    assert "Salomtest" in caged
    assert "no és específica" in caged
    assert interventions == ["postdata(to_ferm_sobre_soroll)", "postdata(collisio_amagada)"]


def test_cage_tie_guardrail_and_unknown_problem_adds_nothing():
    caged, interventions = apply_cage("Empat.", {"intent": "comparacio"}, [], ["empat_trencat"])
    assert "no es pot ordenar" in caged
    assert interventions == ["postdata(empat_trencat)"]
    caged2, interv2 = apply_cage("Text.", _SYNTH_CTX, [], ["validador_illegible"])
    assert caged2 == "Text." and interv2 == []


# --- 5. Puntuació nu/gàbia (dels MATEIXOS outputs) ------------------------------------------

_OK_VERDICT = {"compleix": True, "problemes": [], "motiu": "ok"}


def test_score_trial_clean_pass_is_ok_naked_and_caged():
    s = score_trial("respondre", "respondre", [], _OK_VERDICT, None)
    assert s["naked_ok"] and s["caged_ok"]
    assert s["taxonomy"] == []


def test_score_trial_invented_number_fails_naked_but_cage_fixes_it():
    verdict = {"compleix": False, "problemes": ["xifra_inventada"], "motiu": "num"}
    s = score_trial("respondre", "respondre", [9999], verdict, None)
    assert not s["naked_ok"]
    assert s["caged_ok"]  # la validació dura l'ha tallada: arreglat per (a)
    assert s["taxonomy"] == ["xifra_inventada"]


def test_score_trial_caveat_problem_fails_naked_but_cage_fixes_it():
    verdict = {"compleix": False, "problemes": ["to_ferm_sobre_soroll"], "motiu": "to"}
    s = score_trial("abstenir", "abstenir", [], verdict, None)
    assert not s["naked_ok"]
    assert s["caged_ok"]  # postdata (b)
    assert s["taxonomy"] == ["to_ferm_sobre_soroll"]


def test_score_trial_action_error_is_not_fixable_by_the_cage():
    s = score_trial("abstenir", "respondre", [], _OK_VERDICT, None)
    assert not s["naked_ok"] and not s["caged_ok"]


def test_score_trial_illegible_validator_blocks_caged():
    verdict = {"compleix": False, "problemes": ["validador_illegible"], "motiu": "?"}
    s = score_trial("respondre", "respondre", [], verdict, None)
    assert not s["naked_ok"] and not s["caged_ok"]
    assert s["unfixable"] == ["validador_illegible"]


def test_score_trial_wrong_content_fails_both():
    s = score_trial("respondre", "respondre", [], _OK_VERDICT, False)
    assert not s["naked_ok"] and not s["caged_ok"]


# --- 6. Veredicte del validador --------------------------------------------------------------


def test_parse_verdict_plain_and_fenced():
    v = parse_verdict('{"compleix": true, "problemes": [], "motiu": "net"}')
    assert v == {"compleix": True, "problemes": [], "motiu": "net"}
    v2 = parse_verdict('```json\n{"compleix": false, "problemes": ["empat_trencat"], '
                       '"motiu": "ordre"}\n```')
    assert v2["compleix"] is False and v2["problemes"] == ["empat_trencat"]


def test_parse_verdict_malformed_is_illegible_and_fails_closed():
    v = parse_verdict("no sé què dir-te")
    assert v["compleix"] is False
    assert v["problemes"] == ["validador_illegible"]
    assert v["motiu"] == "no sé què dir-te"


# --- 7. Formes del context (build(None); la prosa determinista MAI entra) --------------------


@pytest.fixture(scope="module")
def conn():
    c = build(None)
    yield c
    c.close()


def _ctx_and_text(conn, query):
    ctx = build_context(conn, query)
    det_text = route(conn, query)["text"]
    dump = json.dumps(ctx, ensure_ascii=False)
    return ctx, det_text, dump


def test_context_valor_oficial(conn):
    q = "Quina és la presència estimada a Cercs?"
    ctx, det_text, dump = _ctx_and_text(conn, q)
    assert ctx["intent"] == "valor_municipi"
    m = ctx["municipi"]
    assert m["nom"] == "Cercs" and m["register"] == "oficial"
    assert m["etca_oficial"] is not None
    for field in ("estimacio", "rang_baix", "rang_alt", "padro"):
        assert m[field] is not None
    assert "collision_group" not in ctx
    assert det_text not in dump  # la resposta determinista NO viatja al generador
    assert "presència estimada" not in dump  # ni cap tros de la seva prosa


def test_context_soroll_collisio_montmajor(conn):
    q = "Digue'm la població que dorm a Montmajor."
    ctx, det_text, dump = _ctx_and_text(conn, q)
    assert ctx["intent"] == "valor_municipi"
    assert ctx["municipi"]["register"] == "soroll"
    grp = ctx["collision_group"]
    assert len(grp) >= 2
    noms = {g["nom"] for g in grp}
    assert "Montmajor" in noms
    assert "Salomó" in noms  # membre FORA dels 31 (via descriptions._collision_groups)
    for g in grp:
        assert g["estimacio"] == ctx["municipi"]["estimacio"]  # la col·lisió és això
    assert det_text not in dump


def test_context_comparacio_dos_noms(conn):
    q = "Qui és més gran de nit, Berga o Puig-reig?"
    ctx, det_text, dump = _ctx_and_text(conn, q)
    assert ctx["intent"] == "comparacio"
    assert len(ctx["municipis"]) == 2
    assert ctx["distinguishable"] is True
    assert ctx["winner"] == "Berga"
    assert det_text not in dump


def test_context_not_found_municipi_desconegut(conn):
    q = "Quanta gent dorm a Ripoll?"
    ctx, det_text, dump = _ctx_and_text(conn, q)
    assert ctx["intent"] == "municipi_desconegut"
    assert ctx["not_found"] == "municipi_desconegut"
    assert "municipi" not in ctx and "municipis" not in ctx
    assert det_text not in dump


def test_user_message_carries_question_and_compact_json(conn):
    ctx = build_context(conn, "Quina és la presència estimada a Cercs?")
    msg = user_message("Quina és la presència estimada a Cercs?", ctx)
    assert msg.startswith("PREGUNTA: ")
    assert "\nCONTEXT: {" in msg
    assert '"intent":"valor_municipi"' in msg  # JSON compacte (sense espais)


# --- 8. Comprovació de contingut (aprox. doc 10, documentada a content_check) ----------------


def test_content_check_value_winner_list(conn):
    golden_v = {"action": "respondre", "expect": {"value": 16669}}
    assert content_check(conn, golden_v, "Berga té 16.669 persones (rang ampli).") is True
    assert content_check(conn, golden_v, "Berga té 17.000 persones.") is False

    golden_w = {"action": "respondre", "expect": {"winner": "08022"}}  # Berga
    assert content_check(conn, golden_w, "Berga en té més que Gironella.") is True
    assert content_check(conn, golden_w, "Gironella guanya.") is False

    golden_l = {"action": "respondre", "expect": {"list": ["08022", "08175"]}}
    assert content_check(conn, golden_l, "Són 2 municipis.") is True  # recompte declarat
    assert content_check(conn, golden_l, "Berga i Puig-reig.") is True  # tots els noms
    assert content_check(conn, golden_l, "Només Berga.") is False


def test_content_check_not_applicable_returns_none(conn):
    assert content_check(conn, {"action": "abstenir"}, "el que sigui") is None
    assert content_check(conn, {"action": "respondre"}, "sense expect") is None
