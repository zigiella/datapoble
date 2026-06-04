"""Per-model OpenRouter price table + a token-based cost estimator.

Used by the multi-model eval script (`evals/compare_models.py`) to weigh
**quality vs cost**, and as the reference for the per-call spend estimate the
runtime :class:`~datapoble_ai.costcontrol.SpendGuard` enforces.

Prices are USD per **million tokens** (prompt / completion), as published by
OpenRouter. They drift, so they live in one table here and can be overridden:
the eval script accepts a ``--pricing`` JSON file. Nothing here makes a network
call or needs a key — it is plain arithmetic over a static table, so it is fully
testable offline.

The numbers below are order-of-magnitude reference values captured 2026-06; for
billing-grade figures pull the live ``/models`` endpoint (documented in the eval
script) when the key is available.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPrice:
    """USD per million prompt / completion tokens for one model."""

    prompt_usd_per_mtok: float
    completion_usd_per_mtok: float

    def cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """USD for a single call with the given token counts."""
        return (
            prompt_tokens / 1_000_000 * self.prompt_usd_per_mtok
            + completion_tokens / 1_000_000 * self.completion_usd_per_mtok
        )


# Reference table (USD / 1M tokens), captured 2026-06. Override via --pricing.
# Keys are OpenRouter model identifiers.
PRICES: dict[str, ModelPrice] = {
    "anthropic/claude-3.5-sonnet": ModelPrice(3.0, 15.0),
    "anthropic/claude-3-haiku": ModelPrice(0.25, 1.25),
    "openai/gpt-4o": ModelPrice(2.5, 10.0),
    "openai/gpt-4o-mini": ModelPrice(0.15, 0.6),
    "google/gemini-flash-1.5": ModelPrice(0.075, 0.30),
    "meta-llama/llama-3.1-70b-instruct": ModelPrice(0.30, 0.30),
    "mistralai/mistral-large": ModelPrice(2.0, 6.0),
}

# A tool-use intent selection is a small interaction: a compact system prompt
# (the catalog summary) + a short question + a tiny tool-call JSON. These are
# conservative averages used to turn a per-model price into a per-call estimate.
TYPICAL_PROMPT_TOKENS = 900
TYPICAL_COMPLETION_TOKENS = 60


def estimate_call_usd(
    model: str,
    prompt_tokens: int = TYPICAL_PROMPT_TOKENS,
    completion_tokens: int = TYPICAL_COMPLETION_TOKENS,
    table: dict[str, ModelPrice] | None = None,
) -> float | None:
    """Estimated USD for one intent-selection call on ``model``.

    Returns ``None`` if the model is unknown (caller can fall back to a flat
    per-call default). Never raises on unknown models.
    """
    prices = table or PRICES
    price = prices.get(model)
    if price is None:
        return None
    return price.cost(prompt_tokens, completion_tokens)
