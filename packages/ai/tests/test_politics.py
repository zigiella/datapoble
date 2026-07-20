"""The political gate: vote-orientation metrics are refused, discreetly.

Bea's rule: the public "Pregunta-li" must not answer how a municipality voted
(metrics with ``dimension: politica``: ``pct_indep``, ``pct_esquerra``,
``pct_extrema_dreta``, ``guanya``). It refuses them with a neutral message that
never hints an unlock exists — **unless** the question carries a secret word read
at runtime from ``AI_POLITICS_UNLOCK``.

These tests are deterministic and key-free. They monkeypatch the env var (never a
hardcoded secret in the repo), force the seed fixtures, and exercise the gate on
both backends (the offline router and the OpenRouter backend's deterministic-first
path, which reaches the shared executor without any network/key).
"""

from __future__ import annotations

import pytest

from datapoble_ai import Agent, OpenRouterBackend, PoliticsGate
from datapoble_ai.catalog import load_catalog
from datapoble_ai.politics import UNLOCK_ENV_VAR, is_political_metric
from datapoble_ai.types import AnswerKind, RefusalReason
from datapoble_ai.warehouse import Warehouse

# A throwaway secret used only by these tests. The *real* value lives only in the
# runtime env on Render — never in the repo. Picked to be accent-free and unlike
# any catalog term so it cannot collide with routing.
SECRET = "obretesim"

# Representative vote questions (one per available politica metric) + an es one.
VOTE_QUESTIONS_CA = [
    "Quin municipi té més % vot independentista?",   # pct_indep (ranking)
    "Quin % de vot d'esquerra té Berga?",            # pct_esquerra (lookup)
    "Quina candidatura guanya a Berga?",             # guanya (lookup)
]


@pytest.fixture(autouse=True)
def _sealed_by_default(monkeypatch):
    """Every test starts with NO secret configured (the fail-safe baseline).

    Individual tests that want the gate open set ``AI_POLITICS_UNLOCK`` explicitly.
    This guarantees the suite never depends on a value leaking from the real env.
    """
    monkeypatch.delenv(UNLOCK_ENV_VAR, raising=False)


def _offline_agent() -> Agent:
    return Agent(mode="offline", use_fixtures=True)


# --- gate unit (the env-reading + matching primitive) -------------------------

def test_gate_fail_safe_when_unconfigured():
    # No word configured -> the gate can never open, for any text.
    gate = PoliticsGate(unlock_word=None)
    assert gate.has_unlock_configured is False
    assert gate.is_unlocked(f"{SECRET} quin vot?") is False
    gate_empty = PoliticsGate(unlock_word="   ")  # whitespace == unset
    assert gate_empty.has_unlock_configured is False
    assert gate_empty.is_unlocked(SECRET) is False


def test_gate_unlocks_case_and_accent_insensitively():
    gate = PoliticsGate(unlock_word="óbrE")
    assert gate.is_unlocked("digues OBRE el resultat")
    assert gate.is_unlocked("abans obré la consulta")
    # Whole-word: must not fire on an incidental substring.
    assert gate.is_unlocked("sobre el vot") is False


def test_gate_strips_secret_preserving_the_rest():
    gate = PoliticsGate(unlock_word=SECRET)
    out = gate.strip_unlock(f"{SECRET} Quina població té Berga?")
    assert SECRET not in out.lower()
    assert out == "Quina població té Berga?"


def test_gate_from_env(monkeypatch):
    monkeypatch.setenv(UNLOCK_ENV_VAR, SECRET)
    gate = PoliticsGate.from_env()
    assert gate.has_unlock_configured is True
    assert gate.is_unlocked(f"{SECRET} vot")


def test_is_political_metric_flags_only_politica():
    cat = load_catalog()
    assert is_political_metric(cat.metric("pct_indep")) is True
    assert is_political_metric(cat.metric("guanya")) is True
    assert is_political_metric(cat.metric("poblacio")) is False
    assert is_political_metric(None) is False


# --- (a) vote question WITHOUT the word -> POLITICAL_GATED ---------------------

@pytest.mark.parametrize("q", VOTE_QUESTIONS_CA)
def test_vote_question_is_gated_by_default(q):
    with _offline_agent() as a:
        ans = a.ask(q, locale="ca")
    assert ans.kind == AnswerKind.REFUSAL
    assert ans.refusal_reason == RefusalReason.POLITICAL_GATED


def test_gated_refusal_message_is_discreet_ca():
    with _offline_agent() as a:
        ans = a.ask("Quin municipi té més % vot independentista?", locale="ca")
    text = ans.text.lower()
    assert "orientació de vot" in text
    # Discreet: it must NOT reveal that a password/unlock/secret exists.
    for leak in ("paraula", "secret", "clau", "desbloque", "contrasenya", "password"):
        assert leak not in text


def test_gated_refusal_message_is_discreet_es():
    with _offline_agent() as a:
        ans = a.ask("¿Qué municipio tiene más voto independentista?", locale="es")
    assert ans.refusal_reason == RefusalReason.POLITICAL_GATED
    text = ans.text.lower()
    assert "orientación de voto" in text
    for leak in ("palabra", "secret", "clave", "desbloque", "contraseña", "password"):
        assert leak not in text


# --- (b) WITH the word -> normal answer; word never leaks ----------------------

def test_unlock_word_lets_vote_question_through(monkeypatch):
    monkeypatch.setenv(UNLOCK_ENV_VAR, SECRET)
    with _offline_agent() as a:
        ans = a.ask(f"{SECRET} Quin municipi té més % vot independentista?",
                    locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "pct_indep"
    # The secret word must not contaminate the routing, the displayed question,
    # the answer text, or the executed SQL.
    assert SECRET not in ans.question.lower()
    assert SECRET not in ans.text.lower()
    assert ans.provenance is not None
    assert SECRET not in ans.provenance.query.lower()


def test_unlock_word_mid_question_also_works(monkeypatch):
    monkeypatch.setenv(UNLOCK_ENV_VAR, SECRET)
    with _offline_agent() as a:
        ans = a.ask(f"Quin % de vot d'esquerra té Berga? {SECRET}", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "pct_esquerra"
    assert SECRET not in ans.question.lower()


# --- (c) non-political question is untouched by the gate ----------------------

def test_non_political_question_unaffected_when_sealed():
    with _offline_agent() as a:
        ans = a.ask("Quina població té Berga?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "poblacio"


def test_non_political_question_unaffected_when_unlocked(monkeypatch):
    # Configuring the secret must not change non-political behaviour at all.
    monkeypatch.setenv(UNLOCK_ENV_VAR, SECRET)
    with _offline_agent() as a:
        ans = a.ask("Quina població té Berga?", locale="ca")
    assert ans.kind == AnswerKind.ANSWER
    assert ans.metric_key == "poblacio"


# --- (d) fail-safe: unconfigured env -> always gated --------------------------

def test_fail_safe_blocks_even_if_question_contains_some_word():
    # No env var set (autouse fixture). Even a question that *mentions* a word
    # cannot unlock anything, because there is no configured secret.
    with _offline_agent() as a:
        ans = a.ask(f"{SECRET} Quin municipi té més % vot independentista?",
                    locale="ca")
    assert ans.kind == AnswerKind.REFUSAL
    assert ans.refusal_reason == RefusalReason.POLITICAL_GATED


def test_empty_env_var_is_treated_as_unconfigured(monkeypatch):
    monkeypatch.setenv(UNLOCK_ENV_VAR, "   ")  # whitespace-only == not configured
    with _offline_agent() as a:
        ans = a.ask(f"{SECRET} Quina candidatura guanya a Berga?", locale="ca")
    assert ans.refusal_reason == RefusalReason.POLITICAL_GATED


# --- both backends: the OpenRouter backend honours the same gate --------------
# Deterministic-first resolves vote metrics through the SHARED executor without
# any key/network, so the gate is exercised on that backend too.

def test_openrouter_backend_gates_vote_question(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    cat = load_catalog()
    wh = Warehouse(cat, use_fixtures=True)
    try:
        be = OpenRouterBackend(cat, wh)  # gate read from env (sealed here)
        ans = be.ask("Quin municipi té més % vot independentista?", locale="ca")
        assert ans.refusal_reason == RefusalReason.POLITICAL_GATED
        assert be.last_call_used_llm is False  # never touched the network
    finally:
        wh.close()


def test_openrouter_backend_unlocks_with_word(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv(UNLOCK_ENV_VAR, SECRET)
    cat = load_catalog()
    wh = Warehouse(cat, use_fixtures=True)
    try:
        be = OpenRouterBackend(cat, wh)
        ans = be.ask(f"{SECRET} Quin municipi té més % vot independentista?",
                     locale="ca")
        assert ans.kind == AnswerKind.ANSWER
        assert ans.metric_key == "pct_indep"
        assert be.last_call_used_llm is False
        assert SECRET not in ans.question.lower()
    finally:
        wh.close()


# --- /metrics endpoint: politica metrics are not advertised -------------------

# --- the fence must not be announced through --------------------------------
# Everything below was leaking *before* the electoral hold-back (2026-07-20).
# The PoliticsGate closed the ANSWER; these are the surfaces that merely
# ENUMERATE the catalog, which the gate structurally cannot reach because it
# keys off a resolved metric. Each assertion here is a hole that was open.

def test_vote_metrics_are_not_advertised_to_the_llm():
    # The model was told pct_indep/pct_esquerra/guanya existed, in both the tool
    # enum and the system prompt. It could pick one, and only then be refused —
    # and a prompt that lists an electoral table is a prompt that leaks it.
    from datapoble_ai.llm import _intent_tool_schema, _system_prompt

    cat = load_catalog()
    enum = _intent_tool_schema(cat, "ca")["function"]["parameters"]["properties"]["metric"]["enum"]
    prompt = _system_prompt(cat, "ca")
    for key in ("pct_indep", "pct_esquerra", "pct_extrema_dreta", "guanya"):
        assert key not in enum, f"{key} offered to the LLM in the tool enum"
        assert key not in prompt, f"{key} named in the LLM system prompt"
    assert "poblacio" in enum and "poblacio" in prompt  # not a vacuous test


def test_out_of_catalog_refusal_does_not_list_vote_metrics():
    # The out-of-catalog refusal ends with "Mètriques disponibles: {…}", built
    # from available_metrics(). It listed «% vot independentista», «% vot
    # esquerra» and «Candidatura guanyadora» as things the agent could answer —
    # directly contradicting the doctrine written down for /metrics, and then
    # refusing them if you asked.
    with _offline_agent() as a:
        ans = a.ask("Quin és el preu del peix a Berga?", locale="ca")
    assert ans.refusal_reason == RefusalReason.OUT_OF_CATALOG
    lowered = ans.text.lower()
    for leak in ("vot independentista", "vot esquerra", "candidatura guanyadora",
                 "vot extrema dreta"):
        assert leak not in lowered, f"refusal advertises «{leak}»"


def test_electoral_mart_is_not_reachable_while_sealed():
    # mart_electoral holds 31 of 947 municipalities (pilot-era artifact, kept on
    # purpose — rebuilding it would publish electoral aggregates for 947
    # municipalities in a public repo, which is an editorial decision). While
    # sealed, no question may reach it at all: an empty result from a stale
    # artifact is indistinguishable from an honest "we don't know".
    with _offline_agent() as a:
        for q in VOTE_QUESTIONS_CA:
            ans = a.ask(q, locale="ca")
            assert ans.kind == AnswerKind.REFUSAL
            assert ans.provenance is None, "a gated question produced a query"


@pytest.mark.parametrize("q,locale", [
    ("On creix més l'extrema dreta?", "ca"),
    ("¿Dónde crece más la extrema derecha?", "es"),
])
def test_planned_vote_metric_uses_the_discreet_door(q, locale):
    # pct_extrema_dreta is status: planned, so parse() refused it *before* the
    # gate — which only fires on a resolved metric — and answered «la mètrica
    # "% vot extrema dreta" ... encara no està calculada»: it named a vote
    # metric and promised it was coming. Both phrasings are seed questions in
    # the contract's own sample_questions, so this route was reachable.
    with _offline_agent() as a:
        ans = a.ask(q, locale=locale)
    assert ans.refusal_reason == RefusalReason.POLITICAL_GATED
    lowered = ans.text.lower()
    assert "extrema" not in lowered and "planned" not in lowered


def test_metrics_endpoint_hides_politica(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from fastapi.testclient import TestClient

    from datapoble_ai.api import app, get_agent
    get_agent.cache_clear()
    client = TestClient(app)
    keys = {m["key"] for m in client.get("/metrics", params={"locale": "ca"}).json()["metrics"]}
    assert "poblacio" in keys                      # non-political still listed
    for politica in ("pct_indep", "pct_esquerra", "guanya", "pct_extrema_dreta"):
        assert politica not in keys                # vote metrics never advertised
