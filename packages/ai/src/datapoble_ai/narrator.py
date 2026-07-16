"""The generative layer — an embellishment that must earn the right to be served.

Harvested in X1 (contract C5). It sits **behind** the existing pattern, and does
not loosen it: the LLM still never writes SQL. The deterministic router answers
first, with provenance; only then may a model re-write that answer's *prose*, and
only if the cage can certify the result. Otherwise the deterministic text stands.

    question -> Router (SQL + provenance)  ->  deterministic Answer   [always safe]
                                                     |
                                       narrate?  ----+
                                                     v
                              redactor -> Cage -> RE-VALIDATE -> serve
                                                     |
                                             fails / no budget / gated
                                                     v
                                            deterministic Answer

Three ways to *not* narrate, all of them silent to the reader (they simply get the
traceable answer):

- **The political gate wins over everything** (C5 §4). ``politics.py`` is
  untouched; no metric with ``dimension: politica`` is ever narrated — not even
  when the team's runtime unlock has opened the deterministic answer. The unlock
  opens data, never a model's prose about a vote.
- **No budget, no generative.** The whole narration (redactor + up to two
  validator calls) is priced *before* the first call. If the ceiling cannot cover
  the full cage, the narration never starts: serving a generative answer with a
  half-paid cage is exactly what C5 forbids.
- **The cage says no.** See :mod:`datapoble_ai.cage`.

The provenance line is **never generated**. The redactor writes prose about the
cells; the source/date/formula tail is appended deterministically, as always.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .cage import Cage, CageResult, parse_output
from .catalog import Catalog
from .costcontrol import SpendGuard
from .doctrine import (
    REDACTOR_PROMPT_PATH,
    VALIDATOR_PROMPT_PATH,
    build_context,
    load_prompt,
)
from .politics import is_political_metric
from .pricing import estimate_call_usd
from .types import Answer

MAX_TOKENS_REDACTOR = 700
#: A narration costs one redactor call plus **two** validator calls in the worst
#: case (judge the prose, then re-judge the caged text). We reserve for the worst
#: case so a narration is never started that the budget cannot see through.
VALIDATOR_CALLS_PER_NARRATION = 2

DEFAULT_REDACTOR_MODEL = "anthropic/claude-3.5-sonnet"
#: The blind validator is the cheap second reader (the experiment used Haiku).
#: Pinned to a model the price table actually carries, so the budget arithmetic
#: below is real rather than a guess (see :mod:`datapoble_ai.pricing`).
DEFAULT_VALIDATOR_MODEL = "anthropic/claude-3-haiku"


class ScriptedBackend:
    """A queued, offline stand-in for a model. No network, no key.

    The default backend for tests and the offline eval: it makes the *cage* the
    subject under test, not the weather.
    """

    name = "scripted"

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        self.calls.append({"system": system, "user": user,
                           "max_tokens": max_tokens})
        if not self._responses:
            raise AssertionError(
                "ScriptedBackend ran out of responses — the code under test made "
                "more calls than the script expected."
            )
        return self._responses.pop(0)


class OpenRouterNarratorBackend:
    """OpenAI-compatible client for the generative path. Inert without a key."""

    name = "openrouter"

    def __init__(self, model: str, api_key: str | None = None,
                 base_url: str = "https://openrouter.ai/api/v1"):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = base_url
        self._client = None

    def _ensure(self):  # pragma: no cover - needs a key
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "OPENROUTER_API_KEY is not set; the generative path is "
                    "scaffolded but requires the secret at runtime."
                )
            from openai import OpenAI  # lazy: optional dependency

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def complete(self, *, system: str, user: str,
                 max_tokens: int) -> str:  # pragma: no cover - needs a key
        resp = self._ensure().chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "")


@dataclass
class NarrationOutcome:
    """What happened, for the record. Attached to the served answer."""

    status: str
    interventions: list[str]
    cage: dict | None = None

    def to_dict(self) -> dict:
        return {"status": self.status,
                "interventions": list(self.interventions),
                "cage": self.cage}


class Narrator:
    """Turns a deterministic :class:`Answer` into a caged, certified narration."""

    def __init__(self, catalog: Catalog, redactor_backend, validator_backend,
                 spend_guard: SpendGuard | None = None,
                 redactor_model: str = DEFAULT_REDACTOR_MODEL,
                 validator_model: str = DEFAULT_VALIDATOR_MODEL):
        self.catalog = catalog
        self.redactor_backend = redactor_backend
        self.redactor_prompt = load_prompt(REDACTOR_PROMPT_PATH)
        self.cage = Cage(load_prompt(VALIDATOR_PROMPT_PATH), validator_backend)
        self.spend_guard = spend_guard
        self.redactor_model = redactor_model
        self.validator_model = validator_model

    # --- gates ---------------------------------------------------------------
    def _is_political(self, answer: Answer) -> bool:
        """True if any metric behind this answer is a vote-orientation metric."""
        for key in (answer.metric_key, answer.metric_b_key):
            if key and is_political_metric(self.catalog.metric(key)):
                return True
        return False

    def _narration_budget_usd(self) -> float | None:
        """Worst-case price of a full narration (redactor + both judgements)."""
        red = estimate_call_usd(self.redactor_model)
        val = estimate_call_usd(self.validator_model)
        if red is None and val is None:
            return None
        return (red or 0.0) + (val or 0.0) * VALIDATOR_CALLS_PER_NARRATION

    def can_narrate(self, answer: Answer) -> tuple[bool, str]:
        """Whether this answer may be narrated at all, and why not if not."""
        if not answer.is_answer:
            return False, "fallback_refusal"       # refusals are never dressed up
        if self._is_political(answer):
            return False, "fallback_political_gate"
        if self.spend_guard is not None and not self.spend_guard.can_spend(
            self._narration_budget_usd()
        ):
            return False, "fallback_budget_exceeded"
        return True, ""

    # --- the run -------------------------------------------------------------
    def narrate(self, answer: Answer, context: dict) -> Answer:
        """Return ``answer`` narrated, or ``answer`` untouched. Never raises.

        The deterministic answer is the floor: any failure — a gate, the budget,
        the cage, a backend blowing up — lands on it.
        """
        allowed, why = self.can_narrate(answer)
        if not allowed:
            answer.narration = NarrationOutcome(status=why, interventions=[]).to_dict()
            return answer

        try:
            raw = self._call_redactor(answer, context)
            accio, prose = parse_output(raw)
            if accio == "error_format" or not prose.strip():
                return self._fallback(answer, "fallback_format")
            result = self._run_cage(answer, context, prose)
        except Exception as exc:  # noqa: BLE001 - the floor must always hold
            return self._fallback(answer, "fallback_error", detail=str(exc)[:200])

        if not result.served or not result.text:
            answer.narration = NarrationOutcome(
                status=result.status, interventions=result.interventions,
                cage=result.to_dict()).to_dict()
            return answer

        # Served: the prose is the model's, the provenance tail is ours.
        answer.text = self._with_deterministic_tail(result.text, answer)
        answer.narration = NarrationOutcome(
            status=result.status, interventions=result.interventions,
            cage=result.to_dict()).to_dict()
        return answer

    def _call_redactor(self, answer: Answer, context: dict) -> str:
        import json as _json

        user = (f"PREGUNTA: {answer.question}\n"
                f"CONTEXT: {_json.dumps(context, ensure_ascii=False, separators=(',', ':'))}")
        raw = self.redactor_backend.complete(
            system=self.redactor_prompt, user=user, max_tokens=MAX_TOKENS_REDACTOR)
        self._record(self.redactor_model)
        return raw

    def _run_cage(self, answer: Answer, context: dict, prose: str) -> CageResult:
        calls_before = getattr(self.cage.backend, "calls", None)
        n_before = len(calls_before) if calls_before is not None else 0
        result = self.cage.run(answer.question, context, prose)
        n_after = len(calls_before) if calls_before is not None else 0
        # Account every judgement the cage actually made.
        for _ in range(max(1, n_after - n_before)):
            self._record(self.validator_model)
        return result

    def _record(self, model: str) -> None:
        if self.spend_guard is not None:
            self.spend_guard.record(estimate_call_usd(model))

    def _fallback(self, answer: Answer, status: str,
                  detail: str | None = None) -> Answer:
        out = NarrationOutcome(status=status, interventions=[]).to_dict()
        if detail:
            out["detail"] = detail
        answer.narration = out
        return answer

    def _with_deterministic_tail(self, prose: str, answer: Answer) -> str:
        """Re-attach the provenance line the deterministic answer already built.

        The redactor is told never to write the source/date/formula; we take the
        tail from the deterministic text so a narrated answer carries exactly the
        same provenance as the answer it re-words.
        """
        prov = answer.provenance
        if prov is None:
            return prose
        from .i18n import t

        tail = t(answer.locale, "provenance_line",
                 source=prov.source or "—", date=prov.date or "s.d.",
                 formula=prov.formula or "—")
        out = f"{prose} {tail}"
        if prov.note:
            out += " " + t(answer.locale, "note_prefix") + prov.note
        return out


def context_for(catalog: Catalog, warehouse, answer: Answer,
                locale: str) -> dict:
    """Build the doctrine context for an already-answered question.

    Reads the ``confianca`` flag for the municipalities in play (a read-only mart
    query, same guardrails) so the register of each cell is the mart's own verdict
    rather than a guess.
    """
    metric = catalog.metric(answer.metric_key) if answer.metric_key else None
    rows = answer.data or []
    intent_kind = "valor_municipi" if len(rows) == 1 else "ranquing"
    if answer.provenance and answer.provenance.formula and \
            answer.provenance.formula.startswith("spearman("):
        intent_kind = "correlacio"

    confidence = _confidence_for(catalog, warehouse, metric, rows)
    verdict = winner = None
    if intent_kind == "ranquing":
        from .doctrine import distinguishable

        values = [r.get("value") for r in rows]
        verdict = distinguishable(values)
        winner = rows[0].get("municipi") if verdict and rows else None
    return build_context(catalog, metric, locale, rows, intent_kind,
                         confidence_by_muni=confidence,
                         distinguishable_verdict=verdict, winner=winner)


def _confidence_for(catalog: Catalog, warehouse, metric, rows) -> dict[str, str]:
    """``{municipi: confianca}`` for the rows in play, or ``{}`` if unavailable."""
    from .doctrine import CONFIDENCE_COLUMN, takes_confidence_flag
    from .warehouse import WarehouseError

    if not takes_confidence_flag(metric) or not rows:
        return {}
    names = [r.get("municipi") for r in rows if r.get("municipi")]
    if not names:
        return {}
    conf_metric = catalog.metric(CONFIDENCE_COLUMN)
    table = conf_metric.table if conf_metric else (metric.table if metric else None)
    if not table:
        return {}
    try:
        got = warehouse.query(
            f'SELECT municipi, "{CONFIDENCE_COLUMN}" AS c FROM "{table}" '
            f"WHERE municipi IN ({','.join('?' * len(names))})", names)
    except WarehouseError:
        # The mart does not carry the flag: no register upgrade, no invention.
        return {}
    return {r["municipi"]: r["c"] for r in got if r.get("c") is not None}
