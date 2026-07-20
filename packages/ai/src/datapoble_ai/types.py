"""Shared result and provenance types for the agent.

The contract with every consumer (Mirador's UI, the evals, the API) is: an
answer is *never* a bare number. It always carries provenance — source, date,
formula and the exact query — or it is an explicit, reasoned refusal. These
dataclasses encode that contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class AnswerKind(str, Enum):
    """Whether the agent answered or refused (refusal-as-a-feature)."""

    ANSWER = "answer"
    REFUSAL = "refusal"


class RefusalReason(str, Enum):
    """Why the agent declined — machine-readable so the UI/evals can branch."""

    OUT_OF_CATALOG = "out_of_catalog"        # no metric in the contract matches
    METRIC_PLANNED = "metric_planned"        # defined but not yet computed
    METRIC_DEPRECATED = "metric_deprecated"  # retired by editorial vote; never served
    UNKNOWN_MUNICIPALITY = "unknown_municipality"
    UNSUPPORTED_QUESTION = "unsupported_question"  # understood metric, can't map intent
    GUARDRAIL_VIOLATION = "guardrail_violation"    # write/raw/illegal SQL attempt
    BUDGET_EXCEEDED = "budget_exceeded"            # AI spend ceiling reached; LLM paused
    RATE_LIMITED = "rate_limited"                  # too many requests (per IP/user)
    POLITICAL_GATED = "political_gated"            # vote-orientation metric, gated off


@dataclass
class Provenance:
    """The traceability block attached to every successful answer."""

    metric: str                     # contract key, e.g. "IETR"
    metric_label: str               # localized label
    source: str | None              # localized source description
    source_key: str | None          # contract source key
    date: str | None                # reference date/period from the contract
    formula: str | None             # the metric's formula from the contract
    query: str                      # the exact SQL that produced the value
    params: dict[str, Any] = field(default_factory=dict)
    license: str | None = None
    note: str | None = None         # caveats (ecological reading, etc.)
    is_fixture: bool = False        # True when answered from seed fixtures, not real marts

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Answer:
    """A complete agent response (answer *or* refusal), locale-aware."""

    kind: AnswerKind
    locale: str
    question: str
    backend: str                    # which LLMBackend produced this ("offline"/"openrouter")
    text: str                       # the human-readable answer in `locale`
    data: list[dict[str, Any]] = field(default_factory=list)  # raw rows behind the text
    provenance: Provenance | None = None
    refusal_reason: RefusalReason | None = None
    metric_key: str | None = None   # convenience for evals/tests
    metric_b_key: str | None = None  # second metric (correlation); the political gate reads both
    generation: dict[str, Any] | None = None  # LLM model + token usage (transparency #64); None = deterministic, no LLM
    # What the generative layer did, if it ran at all (X1 / contract C5): the
    # cage's status, its interventions and both blind verdicts. `None` = never
    # narrated; a `fallback_*` status = the deterministic text is what you see.
    narration: dict[str, Any] | None = None

    @property
    def is_answer(self) -> bool:
        return self.kind == AnswerKind.ANSWER

    @property
    def is_refusal(self) -> bool:
        return self.kind == AnswerKind.REFUSAL

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        if self.refusal_reason is not None:
            d["refusal_reason"] = self.refusal_reason.value
        return d
