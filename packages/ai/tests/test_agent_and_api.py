"""Agent facade, backend selection, OpenRouter inertness, and the API."""

from __future__ import annotations

import pytest

from datapoble_ai import Agent, OpenRouterBackend
from datapoble_ai.llm import OfflineBackend


def test_auto_mode_is_offline_without_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with Agent(mode="auto") as a:
        assert a.mode == "offline"
        assert isinstance(a.backend, OfflineBackend)


def test_auto_mode_selects_openrouter_when_key_present(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-real")
    with Agent(mode="auto") as a:
        assert a.mode == "openrouter"
        assert isinstance(a.backend, OpenRouterBackend)


def test_openrouter_is_inert_without_key(monkeypatch):
    # Scaffolded but must not pretend to work: asking without a key raises a
    # clear, actionable error (never a silent fake answer).
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with Agent(mode="openrouter") as a:
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            a.ask("Quina població té Berga?", locale="ca")


def test_answer_serializes_to_dict(agent):
    ans = agent.ask("Quina població té Berga?", locale="ca")
    d = ans.to_dict()
    assert d["kind"] == "answer"
    assert d["provenance"]["metric"] == "poblacio"
    assert "query" in d["provenance"]


# ---- API ---------------------------------------------------------------------

@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from fastapi.testclient import TestClient

    from datapoble_ai.api import app, get_agent
    get_agent.cache_clear()
    return TestClient(app)


def test_health_reports_backend(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["backend"] == "offline"
    assert "mart_municipi" in body["using_fixture"]


def test_metrics_endpoint_lists_available_only(client):
    r = client.get("/metrics", params={"locale": "ca"})
    assert r.status_code == 200
    keys = {m["key"] for m in r.json()["metrics"]}
    assert "poblacio" in keys
    assert "pct_extrema_dreta" not in keys      # planned -> excluded


def test_ask_endpoint_answer(client):
    r = client.post("/ask", json={"question": "Quina població té Berga?", "locale": "ca"})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "answer"
    assert body["provenance"]["source"]


def test_ask_endpoint_refusal(client):
    r = client.post("/ask", json={"question": "Quin és el PIB de Berga?", "locale": "ca"})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "refusal"
    assert body["refusal_reason"] == "out_of_catalog"
