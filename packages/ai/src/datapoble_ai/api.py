"""FastAPI surface — the endpoint Mirador calls (no UI here, that's Mirador's).

A thin HTTP wrapper over :class:`~datapoble_ai.agent.Agent`, with the **cost
controls** that make the LLM path safe to publicise (see
:mod:`datapoble_ai.costcontrol`). The agent and the cost controls are built once
at startup and reused across requests.

Request flow for ``POST /ask``:

1. **Rate-limit** the caller (token bucket per IP/user). Over budget → ``429``
   with a friendly Catalan message.
2. **Cache**: a normalized (question, locale) that we have answered before is
   served from memory — no recompute, and crucially no LLM call.
3. Otherwise **ask the agent**. The agent is deterministic-first: it only calls
   OpenRouter for genuinely free text, and a shared :class:`SpendGuard` caps the
   daily/monthly spend (over budget → a graceful "AI limit reached" answer; the
   deterministic answers keep working).
4. Answers that actually used the LLM are **cached** so the next identical
   question is free.

Run locally::

    uvicorn datapoble_ai.api:app --reload     # http://127.0.0.1:8000/docs

Endpoints:
- ``GET  /health``   -> liveness + active backend + cost-control stats.
- ``GET  /metrics``  -> the available metrics (catalog introspection).
- ``POST /ask``      -> {question, locale} -> answer + provenance.
"""

from __future__ import annotations

import os
from functools import lru_cache

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, Field

from .agent import Agent
from .catalog import SUPPORTED_LOCALES
from .costcontrol import CostControl
from .router import Router
from .types import RefusalReason

app = FastAPI(
    title="datapoble · Brúixola",
    description="Traceable text-to-SQL over the semantic contract. Provenance always.",
    version="0.1.0",
)


@lru_cache(maxsize=1)
def get_cost_control() -> CostControl:
    """Build the cost controls once, from the environment (see CostControl)."""
    return CostControl.from_env()


@lru_cache(maxsize=1)
def get_agent() -> Agent:
    """Build the agent once.

    Backend = auto (offline unless a key is present). The shared spend guard is
    injected so the LLM path is capped; the offline path ignores it.
    """
    return Agent(mode="auto", spend_guard=get_cost_control().spend_guard)


@lru_cache(maxsize=1)
def _rate_limit_router(agent: Agent) -> Router:
    """A Router used only to render a localized 429 refusal (no LLM)."""
    return Router(agent.catalog, agent.warehouse)


def _client_identity(request: Request) -> str:
    """Best-effort caller identity for rate-limiting (no PII stored).

    Prefer an explicit user header if Mirador forwards one; else the upstream
    client IP. Behind Render/Cloudflare the real client is in
    ``X-Forwarded-For`` (first hop). We keep only what we need to bucket and
    never persist it — consistent with the project's "logs sense PII" rule.
    """
    user = request.headers.get("x-datapoble-user")
    if user:
        return f"user:{user}"
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return f"ip:{fwd.split(',')[0].strip()}"
    client = request.client
    return f"ip:{client.host}" if client else "ip:unknown"


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["Quin municipi té més IETR?"])
    locale: str | None = Field(
        default=None,
        description=f"Active locale. One of {list(SUPPORTED_LOCALES)}; "
                    "defaults to the contract default (ca).",
    )


@app.get("/health")
def health() -> dict:
    agent = get_agent()
    return {
        "status": "ok",
        "backend": agent.mode,
        "catalog_version": agent.catalog.version,
        "locales": agent.catalog.locales,
        "using_fixture": agent.warehouse.using_fixture,
        "cost_control": get_cost_control().stats(),
    }


@app.get("/metrics")
def metrics(locale: str = "ca") -> dict:
    agent = get_agent()
    loc = agent.catalog.resolve_locale(locale)
    return {
        "locale": loc,
        "metrics": [
            {
                "key": m.key,
                "label": m.label(loc),
                "definition": m.definition(loc),
                "unit": m.unit(loc),
                "source": m.source_key,
                "date": m.date,
                "formula": m.formula,
            }
            for m in agent.catalog.available_metrics()
        ],
    }


@app.post("/ask")
def ask(req: AskRequest, request: Request, response: Response) -> dict:
    agent = get_agent()
    cc = get_cost_control()
    loc = agent.catalog.resolve_locale(req.locale)

    # (1) rate-limit per identity → friendly 429 in the active locale.
    allowed, retry_after = cc.rate_limiter.check(_client_identity(request))
    if not allowed:
        response.status_code = 429
        response.headers["Retry-After"] = str(max(1, round(retry_after)))
        refusal = _rate_limit_router(agent)._refuse(
            req.question, loc, RefusalReason.RATE_LIMITED, agent.mode,
        )
        return refusal.to_dict()

    # (2) cache hit → free, with full provenance preserved.
    cached = cc.cache.get(req.question, loc)
    if cached is not None:
        response.headers["X-Cache"] = "hit"
        return cached.to_dict()

    # (3) ask the agent (deterministic-first; spend-capped on the LLM path).
    answer = agent.ask(req.question, locale=loc)
    response.headers["X-Cache"] = "miss"

    # (4) cache answers that actually cost an LLM call (deterministic ones are
    #     already free to recompute, so caching them just spends memory).
    used_llm = getattr(agent.backend, "last_call_used_llm", False)
    if used_llm and answer.is_answer:
        cc.cache.put(req.question, loc, answer)

    return answer.to_dict()


# Allow `python -m datapoble_ai.api` to serve in a container without a separate
# uvicorn invocation (handy for the Render start command / Dockerfile CMD).
def _serve() -> None:  # pragma: no cover - exercised by the container, not tests
    import uvicorn

    uvicorn.run(
        "datapoble_ai.api:app",
        host="0.0.0.0",  # noqa: S104 - container must bind all interfaces
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":  # pragma: no cover
    _serve()
