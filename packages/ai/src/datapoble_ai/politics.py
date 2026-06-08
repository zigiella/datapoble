"""Political gate at the resolution layer — refuse vote questions, discreetly.

Bea's call: the public "Pregunta-li" must **not** answer questions about *how a
municipality voted*. Those are the metrics tagged ``dimension: politica`` in the
contract (``pct_indep``, ``pct_esquerra``, ``pct_extrema_dreta``, ``guanya``).
The agent refuses them with a **neutral, deliberately discreet** message that
gives no hint a bypass exists.

Why here (and not in a backend)
-------------------------------
The gate keys off the **resolved metric's dimension**, so it must live where the
metric is already known — the :class:`~datapoble_ai.router.Router` executor that
*both* backends share (offline + OpenRouter). Applied there, it holds no matter
which backend produced the intent.

The unlock (team-internal escape hatch)
---------------------------------------
A single **secret word**, read at runtime from the ``AI_POLITICS_UNLOCK`` env var
(never hardcoded, never committed — same discipline as
:meth:`CostControl.from_env`). If a question contains it, the gate opens *and the
word is stripped from the question* before routing, so it cannot leak into
keyword matching or echo back in the answer.

**Fail-safe.** If the env var is unset or empty, there is no word to match, so the
gate is **closed for everyone**: with no secret configured, no political metric is
ever answered. Locking is the default; unlocking is the deliberate exception.
"""

from __future__ import annotations

import os
import re

from .catalog import Metric, normalize

#: Contract dimension that marks a metric as a vote-orientation metric.
POLITICS_DIMENSION = "politica"

#: Name of the runtime secret. The *value* is never in the repo.
UNLOCK_ENV_VAR = "AI_POLITICS_UNLOCK"


def is_political_metric(metric: Metric | None) -> bool:
    """True iff ``metric`` is a vote-orientation metric (``dimension: politica``)."""
    return metric is not None and metric.dimension == POLITICS_DIMENSION


class PoliticsGate:
    """Decides whether a vote question may be answered, and hides the unlock.

    Construct it from the environment via :meth:`from_env` (the only supported
    way in production); the explicit constructor takes the word directly and is
    used by tests that want determinism without touching the process env.
    """

    def __init__(self, unlock_word: str | None = None):
        # Normalise once (accent/again-case-insensitive). Empty/whitespace or
        # unset collapses to ``None`` → the gate can never open (fail-safe).
        word = (unlock_word or "").strip()
        self._unlock_norm: str | None = normalize(word) if word else None

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> PoliticsGate:
        """Read the secret from ``AI_POLITICS_UNLOCK`` (mirrors CostControl)."""
        src = os.environ if env is None else env
        return cls(unlock_word=src.get(UNLOCK_ENV_VAR))

    @property
    def has_unlock_configured(self) -> bool:
        """Whether a non-empty secret is configured (else the gate is sealed)."""
        return self._unlock_norm is not None

    def is_unlocked(self, question: str) -> bool:
        """True iff the secret word is configured *and* present in ``question``.

        Match is accent- and case-insensitive (both sides are accent-folded and
        lowercased) and is bounded to whole words, so the secret does not fire on
        an incidental substring. With no secret configured this is always
        ``False`` — the fail-safe.
        """
        if self._unlock_norm is None:
            return False
        return self._contains_unlock(normalize(question))

    def strip_unlock(self, question: str) -> str:
        """Remove the secret word from ``question`` (whole-word, all occurrences).

        Done *before* routing so the word never pollutes keyword matching, and so
        it can never echo back in the displayed question/answer. Accent-insensitive
        on the *match*, but it edits the original (accented) text in place; leftover
        double spaces are collapsed. A no-op when nothing is configured/found.
        """
        if self._unlock_norm is None:
            return question
        # Walk the accent-folded text to locate matches, then cut the same spans
        # from the original so we preserve the user's casing/accents elsewhere.
        folded = normalize(question)
        pattern = self._unlock_pattern()
        # `normalize` is a per-character NFKD fold + lowercase that preserves
        # length for the scripts we handle (ca/es), so spans line up 1:1.
        if len(folded) != len(question):
            # Defensive: if folding changed length, fall back to a folded rebuild
            # (loses original accents in the rare exotic-input case, but stays
            # correct — the word is still removed).
            cleaned = pattern.sub(" ", folded)
            return re.sub(r"\s+", " ", cleaned).strip()
        out = list(question)
        for m in pattern.finditer(folded):
            for i in range(m.start(), m.end()):
                out[i] = " "
        return re.sub(r"\s+", " ", "".join(out)).strip()

    # -- internals -------------------------------------------------------------
    def _unlock_pattern(self) -> re.Pattern[str]:
        assert self._unlock_norm is not None
        return re.compile(rf"\b{re.escape(self._unlock_norm)}\b")

    def _contains_unlock(self, question_norm: str) -> bool:
        return self._unlock_pattern().search(question_norm) is not None
