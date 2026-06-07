"""CORS so the browser-side Mirador front can call the API cross-origin.

Mirador is an ``adapter-static`` build served from a different origin
(riusdegent.cat / *.pages.dev), so every API response it consumes must carry
``Access-Control-Allow-Origin``. These tests pin, **offline** and without any
key, that:

- an allowed origin (default config) gets the header echoed on both a GET and a
  CORS preflight (``OPTIONS``);
- a non-allowed origin gets **no** ``Access-Control-Allow-Origin`` (the browser
  would then block the response);
- the env knob ``AI_CORS_ORIGINS`` replaces the defaults;
- the default regex lets Cloudflare Pages preview origins through, and
  ``AI_CORS_ORIGIN_REGEX`` is configurable.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from datapoble_ai.api import (
    DEFAULT_CORS_ORIGIN_REGEX,
    DEFAULT_CORS_ORIGINS,
    app,
    cors_config_from_env,
)

ALLOWED = "https://riusdegent.cat"
ALLOWED_DEV = "http://localhost:5173"
DISALLOWED = "https://evil.example.com"


@pytest.fixture()
def client(monkeypatch):
    """The real app (module-level CORS = defaults), offline, no key."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from datapoble_ai.api import get_agent

    get_agent.cache_clear()
    return TestClient(app)


def _client_with_cors(**cors_kwargs) -> TestClient:
    """A throwaway app exercising a specific CORS config in isolation.

    Lets us assert non-default configs (custom origins / regex) without mutating
    the import-time middleware on the shared ``app``.
    """
    tmp = FastAPI()
    tmp.add_middleware(CORSMiddleware, **cors_kwargs)

    @tmp.get("/ping")
    def ping() -> dict:  # pragma: no cover - trivial
        return {"ok": True}

    return TestClient(tmp)


# ---- the real app, default config -------------------------------------------

def test_allowed_origin_gets_cors_header_on_get(client):
    r = client.get("/health", headers={"Origin": ALLOWED})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ALLOWED


def test_allowed_dev_origin_gets_cors_header(client):
    r = client.get("/health", headers={"Origin": ALLOWED_DEV})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ALLOWED_DEV


def test_preflight_options_is_allowed_for_post(client):
    # The browser preflights POST /ask before sending the JSON body.
    r = client.options(
        "/ask",
        headers={
            "Origin": ALLOWED,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ALLOWED
    allow_methods = r.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods


def test_disallowed_origin_gets_no_cors_header(client):
    r = client.get("/health", headers={"Origin": DISALLOWED})
    # The request itself still succeeds server-side; what matters is that the
    # browser sees NO allow-origin header and therefore blocks the response.
    assert "access-control-allow-origin" not in r.headers


def test_credentials_are_not_allowed(client):
    # No cookies: the allow-credentials header must never be sent (it is what
    # makes an explicit-origin allowlist safe).
    r = client.get("/health", headers={"Origin": ALLOWED})
    assert "access-control-allow-credentials" not in r.headers


def test_pages_preview_origin_allowed_by_default_regex(client):
    preview = "https://deadbeef.riusdegent.pages.dev"
    r = client.get("/health", headers={"Origin": preview})
    assert r.headers.get("access-control-allow-origin") == preview


# ---- config helper (env parsing) --------------------------------------------

def test_config_defaults_when_env_absent():
    cfg = cors_config_from_env(env={})
    assert cfg["allow_origins"] == list(DEFAULT_CORS_ORIGINS)
    assert cfg["allow_origin_regex"] == DEFAULT_CORS_ORIGIN_REGEX
    assert cfg["allow_credentials"] is False
    assert set(cfg["allow_methods"]) == {"GET", "POST", "OPTIONS"}


def test_config_origins_env_replaces_defaults():
    cfg = cors_config_from_env(
        env={"AI_CORS_ORIGINS": " https://a.example , https://b.example ,"}
    )
    assert cfg["allow_origins"] == ["https://a.example", "https://b.example"]


def test_config_blank_origins_env_falls_back_to_defaults():
    cfg = cors_config_from_env(env={"AI_CORS_ORIGINS": "   "})
    assert cfg["allow_origins"] == list(DEFAULT_CORS_ORIGINS)


def test_config_empty_regex_env_disables_regex():
    cfg = cors_config_from_env(env={"AI_CORS_ORIGIN_REGEX": ""})
    assert cfg["allow_origin_regex"] is None


# ---- a non-default config, end to end ---------------------------------------

def test_custom_env_origin_allowed_and_default_disallowed():
    cfg = cors_config_from_env(env={"AI_CORS_ORIGINS": "https://only-this.example"})
    c = _client_with_cors(**cfg)

    ok = c.get("/ping", headers={"Origin": "https://only-this.example"})
    assert ok.headers["access-control-allow-origin"] == "https://only-this.example"

    # A default origin must NOT be allowed once AI_CORS_ORIGINS overrides them.
    nope = c.get("/ping", headers={"Origin": ALLOWED})
    assert "access-control-allow-origin" not in nope.headers
