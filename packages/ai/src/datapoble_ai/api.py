"""FastAPI surface — the endpoint Mirador calls (no UI here, that's Mirador's).

A thin HTTP wrapper over :class:`~datapoble_ai.agent.Agent`. The agent is built
once at startup (offline by default; OpenRouter automatically if the key is in
the environment) and reused across requests.

Run locally::

    uvicorn datapoble_ai.api:app --reload

Endpoints:
- ``GET  /health``        -> liveness + which backend is active.
- ``GET  /metrics``       -> the available metrics (catalog introspection).
- ``POST /ask``           -> {question, locale} -> answer + provenance.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .agent import Agent
from .catalog import SUPPORTED_LOCALES

app = FastAPI(
    title="datapoble · Brúixola",
    description="Traceable text-to-SQL over the semantic contract. Provenance always.",
    version="0.1.0",
)


@lru_cache(maxsize=1)
def get_agent() -> Agent:
    """Build the agent once. Backend = auto (offline unless a key is present)."""
    return Agent(mode="auto")


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
def ask(req: AskRequest) -> dict:
    agent = get_agent()
    answer = agent.ask(req.question, locale=req.locale)
    return answer.to_dict()
