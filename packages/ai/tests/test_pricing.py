"""Pricing estimator tests — pure arithmetic, offline, no key."""

from __future__ import annotations

from datapoble_ai.pricing import ModelPrice, estimate_call_usd


def test_model_price_cost_is_linear():
    p = ModelPrice(prompt_usd_per_mtok=3.0, completion_usd_per_mtok=15.0)
    # 1M prompt + 1M completion tokens = 3 + 15 = 18 USD.
    assert p.cost(1_000_000, 1_000_000) == 18.0
    # Half the tokens, half the cost.
    assert p.cost(500_000, 0) == 1.5


def test_estimate_known_model_is_positive():
    usd = estimate_call_usd("anthropic/claude-3-haiku")
    assert usd is not None and usd > 0


def test_estimate_unknown_model_returns_none():
    assert estimate_call_usd("nonexistent/model-x") is None


def test_estimate_respects_custom_table():
    table = {"x/y": ModelPrice(1_000_000.0, 0.0)}  # 1 USD per token, absurd on purpose
    usd = estimate_call_usd("x/y", prompt_tokens=1, completion_tokens=0, table=table)
    assert usd == 1.0


def test_cheaper_model_estimates_less():
    haiku = estimate_call_usd("anthropic/claude-3-haiku")
    sonnet = estimate_call_usd("anthropic/claude-3.5-sonnet")
    assert haiku is not None and sonnet is not None
    assert haiku < sonnet
