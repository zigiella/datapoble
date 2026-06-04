"""Cost-control unit tests — all OFFLINE, deterministic, no key, no network.

Covers the four levers that keep the LLM bill bounded:
- deterministic-first escalation (only free text reaches the LLM),
- the question cache (normalize + LRU),
- the rate limiter (token bucket),
- the hard spend guard (daily/monthly ceiling),
plus the API wiring (429, cache headers, graceful budget message).
"""

from __future__ import annotations

import pytest

from datapoble_ai import Agent
from datapoble_ai.costcontrol import (
    QuestionCache,
    RateLimiter,
    SpendGuard,
    normalize_question,
)
from datapoble_ai.llm import _ESCALATABLE_REFUSALS
from datapoble_ai.types import AnswerKind, RefusalReason

# ---- normalization -----------------------------------------------------------


def test_normalize_collapses_case_trim_and_whitespace():
    a = normalize_question("  Quina   població té Berga?  ", "ca")
    b = normalize_question("quina població té berga?", "ca")
    assert a == b


def test_normalize_is_locale_scoped():
    assert normalize_question("hola", "ca") != normalize_question("hola", "es")


# ---- question cache ----------------------------------------------------------


def test_cache_roundtrip_and_normalization(agent):
    cache = QuestionCache(maxsize=4)
    ans = agent.ask("Quina població té Berga?", locale="ca")
    cache.put("Quina població té Berga?", "ca", ans)
    # A differently-spaced/cased variant hits the same entry.
    hit = cache.get("  quina  població  té berga? ", "ca")
    assert hit is ans
    assert cache.stats()["hits"] == 1


def test_cache_lru_eviction(agent):
    cache = QuestionCache(maxsize=2)
    a = agent.ask("Quina població té Berga?", locale="ca")
    for q in ("q1", "q2", "q3"):
        cache.put(q, "ca", a)
    # q1 evicted (least recently used), q2/q3 retained.
    assert cache.get("q1", "ca") is None
    assert cache.get("q2", "ca") is a
    assert cache.get("q3", "ca") is a


def test_cache_disabled_when_maxsize_zero(agent):
    cache = QuestionCache(maxsize=0)
    a = agent.ask("Quina població té Berga?", locale="ca")
    cache.put("q", "ca", a)
    assert cache.get("q", "ca") is None


# ---- rate limiter ------------------------------------------------------------


def test_rate_limiter_allows_up_to_capacity_then_blocks():
    rl = RateLimiter(capacity=3, refill_per_sec=0)  # no refill during the test
    ip = "ip:1.2.3.4"
    assert all(rl.check(ip)[0] for _ in range(3))   # 3 tokens
    allowed, retry_after = rl.check(ip)             # 4th denied
    assert allowed is False
    assert retry_after > 0


def test_rate_limiter_is_per_identity():
    rl = RateLimiter(capacity=1, refill_per_sec=0)
    assert rl.check("ip:a")[0] is True
    assert rl.check("ip:a")[0] is False     # a exhausted
    assert rl.check("ip:b")[0] is True      # b independent


def test_rate_limiter_refills_over_time(monkeypatch):
    rl = RateLimiter(capacity=1, refill_per_sec=10)
    clock = {"t": 1000.0}
    monkeypatch.setattr(rl, "_now", lambda: clock["t"])
    assert rl.check("ip:x")[0] is True
    assert rl.check("ip:x")[0] is False
    clock["t"] += 0.2                       # 0.2s * 10/s = 2 tokens refilled
    assert rl.check("ip:x")[0] is True


def test_rate_limiter_disabled_when_capacity_zero():
    rl = RateLimiter(capacity=0)
    assert all(rl.check("ip:x")[0] for _ in range(1000))


# ---- spend guard -------------------------------------------------------------


def test_spend_guard_blocks_over_daily_ceiling():
    g = SpendGuard(daily_usd=0.05, monthly_usd=100, usd_per_call=0.02)
    assert g.can_spend() is True
    g.record()                              # 0.02
    g.record()                              # 0.04
    assert g.can_spend() is False           # 0.04 + 0.02 = 0.06 > 0.05


def test_spend_guard_blocks_over_monthly_ceiling():
    g = SpendGuard(daily_usd=100, monthly_usd=0.05, usd_per_call=0.04)
    g.record()
    assert g.can_spend() is False


def test_spend_guard_unbounded_when_zero():
    g = SpendGuard(daily_usd=0, monthly_usd=0, usd_per_call=999)
    for _ in range(10):
        assert g.can_spend() is True
        g.record()


def test_spend_guard_uses_estimate_argument():
    g = SpendGuard(daily_usd=0.10, monthly_usd=100, usd_per_call=0.01)
    assert g.can_spend(estimated=0.20) is False   # one big call already over
    assert g.can_spend(estimated=0.05) is True


def test_spend_guard_rollover_resets_day(monkeypatch):
    import datapoble_ai.costcontrol as cc
    days = iter(["2026-06-04", "2026-06-04", "2026-06-05"])
    cur = {"d": "2026-06-04"}
    monkeypatch.setattr(cc, "_today", lambda: cur["d"])
    g = SpendGuard(daily_usd=0.05, monthly_usd=100, usd_per_call=0.04)
    g.record()
    assert g.can_spend() is False
    cur["d"] = "2026-06-05"                  # new day -> daily budget resets
    assert g.can_spend() is True
    _ = days  # silence linter on the unused generator


# ---- deterministic-first escalation -----------------------------------------


def test_only_unmatched_refusals_escalate():
    # The contract of which refusals may cost an LLM call.
    assert RefusalReason.OUT_OF_CATALOG in _ESCALATABLE_REFUSALS
    assert RefusalReason.UNSUPPORTED_QUESTION in _ESCALATABLE_REFUSALS
    assert RefusalReason.METRIC_PLANNED not in _ESCALATABLE_REFUSALS
    assert RefusalReason.UNKNOWN_MUNICIPALITY not in _ESCALATABLE_REFUSALS


def test_planned_metric_does_not_escalate_to_llm(monkeypatch):
    # A planned-metric question is a *precise* refusal: it must be answered
    # deterministically (no key needed), never sent to the LLM.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with Agent(mode="openrouter") as a:
        ans = a.ask("On creix més l'extrema dreta?", locale="ca")
        assert ans.kind == AnswerKind.REFUSAL
        assert ans.refusal_reason == RefusalReason.METRIC_PLANNED
        assert a.backend.last_call_used_llm is False


def test_budget_exceeded_pauses_llm_but_keeps_deterministic(monkeypatch):
    # With the budget exhausted, free text that *would* hit the LLM returns a
    # graceful budget refusal — while deterministic questions still answer.
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-real")
    guard = SpendGuard(daily_usd=0.0001, monthly_usd=100, usd_per_call=1.0)
    with Agent(mode="openrouter", spend_guard=guard) as a:
        # Free text -> would escalate -> blocked by the cap (no network call).
        ans = a.ask("parla'm del paisatge i la vida al poble", locale="ca")
        assert ans.kind == AnswerKind.REFUSAL
        assert ans.refusal_reason == RefusalReason.BUDGET_EXCEEDED
        assert a.backend.last_call_used_llm is False
        # Deterministic question still works, untouched by the cap.
        ok = a.ask("Quina població té Berga?", locale="ca")
        assert ok.is_answer


def test_budget_message_is_localized(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-real")
    guard = SpendGuard(daily_usd=0.0001, monthly_usd=100, usd_per_call=1.0)
    with Agent(mode="openrouter", spend_guard=guard) as a:
        ca = a.ask("parla'm del paisatge", locale="ca")
        es = a.ask("háblame del paisaje", locale="es")
        assert "límit de consultes" in ca.text
        assert "límite de consultas" in es.text


# ---- API wiring --------------------------------------------------------------


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from fastapi.testclient import TestClient

    from datapoble_ai.api import app, get_agent, get_cost_control
    get_agent.cache_clear()
    get_cost_control.cache_clear()
    return TestClient(app)


def test_health_exposes_cost_control(client):
    body = client.get("/health").json()
    assert "cost_control" in body
    assert "cache" in body["cost_control"]
    assert "spend" in body["cost_control"]


def test_ask_sets_cache_headers(client):
    q = {"question": "Quina població té Berga?", "locale": "ca"}
    r1 = client.post("/ask", json=q)
    assert r1.headers.get("X-Cache") == "miss"
    # Deterministic answers are not cached (free to recompute) -> still a miss.
    r2 = client.post("/ask", json=q)
    assert r2.headers.get("X-Cache") == "miss"
    assert r1.json()["provenance"]["source"]


def test_rate_limit_returns_429_with_retry_after(monkeypatch):
    # Tight limiter so the test trips it deterministically.
    monkeypatch.setenv("AI_RATE_CAPACITY", "2")
    monkeypatch.setenv("AI_RATE_REFILL_PER_SEC", "0")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from fastapi.testclient import TestClient

    from datapoble_ai.api import app, get_agent, get_cost_control
    get_agent.cache_clear()
    get_cost_control.cache_clear()
    c = TestClient(app)
    q = {"question": "Quina població té Berga?", "locale": "ca"}
    assert c.post("/ask", json=q).status_code == 200
    assert c.post("/ask", json=q).status_code == 200
    blocked = c.post("/ask", json=q)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert blocked.json()["refusal_reason"] == "rate_limited"
