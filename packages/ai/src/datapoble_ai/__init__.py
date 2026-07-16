"""datapoble · Brúixola — traceable text-to-SQL agent.

Public surface (what Mirador / the API import):

    from datapoble_ai import Agent
    with Agent() as agent:                 # offline by default (no key needed)
        ans = agent.ask("Quin municipi té més IETR?", locale="ca")
        print(ans.text)                    # answer + provenance, in Catalan
        print(ans.provenance.to_dict())    # source · date · formula · query
"""

from __future__ import annotations

from .agent import Agent
from .cage import Cage, CageResult, apply_cage, hard_validation
from .catalog import Catalog, Metric, Source, load_catalog
from .costcontrol import (
    CostControl,
    QuestionCache,
    RateLimiter,
    SpendGuard,
    normalize_question,
)
from .doctrine import OFICIAL, SENYAL, SOROLL, distinguishable, register_for
from .llm import LLMBackend, OfflineBackend, OpenRouterBackend
from .narrator import Narrator, OpenRouterNarratorBackend, ScriptedBackend
from .politics import PoliticsGate, is_political_metric
from .types import Answer, AnswerKind, Provenance, RefusalReason
from .warehouse import Warehouse, WarehouseError

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "Catalog",
    "Metric",
    "Source",
    "load_catalog",
    "LLMBackend",
    "OfflineBackend",
    "OpenRouterBackend",
    "Warehouse",
    "WarehouseError",
    "Answer",
    "AnswerKind",
    "Provenance",
    "RefusalReason",
    "CostControl",
    "QuestionCache",
    "RateLimiter",
    "SpendGuard",
    "normalize_question",
    "PoliticsGate",
    "is_political_metric",
    # The doctrine and the cage (X1 / contract C5).
    "Cage",
    "CageResult",
    "hard_validation",
    "apply_cage",
    "distinguishable",
    "register_for",
    "OFICIAL",
    "SENYAL",
    "SOROLL",
    "Narrator",
    "ScriptedBackend",
    "OpenRouterNarratorBackend",
]
