"""LLM interface + backends (offline default, OpenRouter behind the interface).

The agent talks to an :class:`LLMBackend`, never to a provider SDK directly.
Two backends ship:

- :class:`OfflineBackend` — **the default**. Pure deterministic router (ports
  the prototype ``ask.py``). No network, no key, fully testable. This is what
  the evals run against today.
- :class:`OpenRouterBackend` — an OpenAI-compatible client for OpenRouter,
  used only when ``OPENROUTER_API_KEY`` is set. It does **not** loosen the
  guardrails: the model's job is narrow — read the question and pick a catalog
  metric + intent (lookup / ranking / correlation). The chosen intent is then
  executed by the same :class:`~datapoble_ai.router.Router` (parametrized,
  read-only, contract-only SQL + provenance). If the model picks something
  outside the catalog, we refuse exactly like the offline path.

This keeps a single source of truth for SQL generation and provenance, so the
LLM can never emit raw SQL or reach ``raw`` tables.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod

from .catalog import Catalog, normalize
from .router import Intent, Router
from .types import Answer, RefusalReason
from .warehouse import Warehouse

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# A model that is strong in ca/es by default; overridable via env/ctor.
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"


class LLMBackend(ABC):
    """Interface every backend implements."""

    name: str = "base"

    @abstractmethod
    def ask(self, question: str, locale: str | None = None) -> Answer:
        ...


class OfflineBackend(LLMBackend):
    """Deterministic baseline. Default, key-free, CI-friendly."""

    name = "offline"

    def __init__(self, catalog: Catalog, warehouse: Warehouse):
        self.router = Router(catalog, warehouse)

    def ask(self, question: str, locale: str | None = None) -> Answer:
        return self.router.ask(question, locale=locale, backend=self.name)


def _intent_tool_schema(catalog: Catalog, locale: str) -> dict:
    """JSON-schema tool the LLM must call to express its interpretation.

    The model is constrained to *enums of catalog metric keys* — it literally
    cannot name a metric that is not in the contract. That is the guardrail at
    the model boundary.
    """
    metric_keys = [m.key for m in catalog.available_metrics()]
    return {
        "type": "function",
        "function": {
            "name": "answer_from_catalog",
            "description": (
                "Express the question as a query over the datapoble semantic "
                "catalog. Only metrics in the enum are allowed. If the question "
                "cannot be answered with these metrics, call refuse instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["lookup", "ranking", "correlation"],
                    },
                    "metric": {"type": "string", "enum": metric_keys},
                    "metric_b": {
                        "type": "string", "enum": metric_keys,
                        "description": "Second metric, only for correlation.",
                    },
                    "municipality": {
                        "type": "string",
                        "description": "Municipality name for a lookup, if any.",
                    },
                    "descending": {
                        "type": "boolean",
                        "description": "Ranking direction: true = largest first.",
                    },
                    "want_list": {
                        "type": "boolean",
                        "description": "Ranking: return a list instead of the top one.",
                    },
                },
                "required": ["kind", "metric"],
            },
        },
    }


def _refuse_tool_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "refuse",
            "description": (
                "Decline when the question is outside the catalog. Provide a "
                "short reason in the user's language."
            ),
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"],
            },
        },
    }


def _system_prompt(catalog: Catalog, locale: str) -> str:
    lines = [
        "You are Brúixola, the traceable text-to-SQL agent for the datapoble "
        "territorial observatory.",
        "You MUST answer only from the semantic catalog below. Never invent "
        "data. If a question falls outside the catalog, call `refuse`.",
        f"Answer in locale '{locale}'. Available metrics (key: label):",
    ]
    for m in catalog.available_metrics():
        lines.append(f"- {m.key}: {m.label(locale)} — {m.definition(locale) or ''}")
    lines.append(
        "Pick exactly one interpretation via `answer_from_catalog`. The actual "
        "SQL and provenance are produced by the system, not by you."
    )
    return "\n".join(lines)


class OpenRouterBackend(LLMBackend):
    """OpenAI-compatible OpenRouter client behind the LLM interface.

    Scaffolded and wired, but **inert until a key is provided**. The model only
    selects a catalog intent; execution + guardrails stay in :class:`Router`.
    """

    name = "openrouter"

    def __init__(self, catalog: Catalog, warehouse: Warehouse,
                 api_key: str | None = None, model: str | None = None,
                 base_url: str = OPENROUTER_BASE_URL):
        self.catalog = catalog
        self.warehouse = warehouse
        self.router = Router(catalog, warehouse)
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model or os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
        self.base_url = base_url
        self._client = None  # lazily constructed on first call

    @classmethod
    def available(cls) -> bool:
        """True if a key is present in the environment (no key in repo, ever)."""
        return bool(os.environ.get("OPENROUTER_API_KEY"))

    def _ensure_client(self):
        if self._client is not None:
            return
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. The OpenRouter backend is "
                "scaffolded but requires the secret (passed at runtime, never "
                "committed). Use the offline backend for key-free runs."
            )
        try:
            from openai import OpenAI  # imported lazily; optional dependency
        except ImportError as exc:  # pragma: no cover - exercised only with key
            raise RuntimeError(
                "The 'openai' package is required for the OpenRouter backend. "
                "Install it (it is an optional dependency) to enable the LLM path."
            ) from exc
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def ask(self, question: str, locale: str | None = None) -> Answer:
        loc = self.catalog.resolve_locale(locale)
        self._ensure_client()
        tools = [
            _intent_tool_schema(self.catalog, loc),
            _refuse_tool_schema(),
        ]
        resp = self._client.chat.completions.create(  # pragma: no cover - needs key
            model=self.model,
            messages=[
                {"role": "system", "content": _system_prompt(self.catalog, loc)},
                {"role": "user", "content": question},
            ],
            tools=tools,
            tool_choice="required",
            temperature=0,
        )
        return self._dispatch(question, loc, resp)  # pragma: no cover - needs key

    def _dispatch(self, question: str, locale: str, resp) -> Answer:  # pragma: no cover - needs key
        """Turn the model's tool call into a guarded Router execution."""
        choice = resp.choices[0].message
        tool_calls = getattr(choice, "tool_calls", None) or []
        if not tool_calls:
            return self.router._refuse(
                question, locale, RefusalReason.UNSUPPORTED_QUESTION, self.name)
        call = tool_calls[0]
        args = json.loads(call.function.arguments or "{}")

        if call.function.name == "refuse":
            return self.router._refuse(
                question, locale, RefusalReason.OUT_OF_CATALOG, self.name)

        # Build a validated Intent from the (enum-constrained) model output, then
        # let the Router execute it under the same guardrails as offline.
        metric = self.catalog.metric(args.get("metric"))
        if metric is None or not metric.is_available():
            return self.router._refuse(
                question, locale,
                RefusalReason.METRIC_PLANNED if metric else RefusalReason.OUT_OF_CATALOG,
                self.name)
        metric_b = self.catalog.metric(args.get("metric_b"))
        muni_raw = args.get("municipality")
        muni = self.router.match_municipality(normalize(muni_raw)) if muni_raw else None
        intent = Intent(
            kind=args.get("kind", "lookup"),
            metric=metric,
            metric_b=metric_b,
            municipality=muni,
            descending=args.get("descending", True),
            want_list=args.get("want_list", False),
        )
        return self.router.execute_intent(question, locale, intent, self.name)
