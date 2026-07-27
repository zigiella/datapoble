"""Political gate at the resolution layer — vote questions are refused, discreetly.

Bea's rule: the public "Pregunta-li" must **not** answer questions about *how a
municipality voted*. Those are the metrics tagged ``dimension: politica`` in the
contract (``pct_indep``, ``pct_esquerra``, ``pct_extrema_dreta``, ``guanya``).
The agent refuses them with a **neutral, deliberately discreet** message that
gives no hint any bypass exists.

Why here (and not in a backend)
-------------------------------
The refusal keys off the **resolved metric's dimension**, so it must live where
the metric is already known — the :class:`~datapoble_ai.router.Router` executor
that *both* backends share (offline + OpenRouter). Applied there, it holds no
matter which backend produced the intent.

No runtime key — the key is revoked (Bea, 2026-07-27)
-----------------------------------------------------
This refusal used to carry a team-internal escape hatch: a secret word read at
runtime from ``AI_POLITICS_UNLOCK`` that opened the gate for a single question.
**Bea revoked that key outright on 2026-07-27** — *«revocar la clau; tot el vot
polític, fora»*. No env var, no secret word, no path of any kind may ever
re-serve a vote metric. The whole ``PoliticsGate`` machinery (unlock reading,
whole-word matching, secret stripping) is gone, and with it the ``KEYED_``
plumbing in :mod:`catalog` and the router.

The ``politica`` dimension is now held back **unconditionally**, exactly like
``origen`` (see :data:`~datapoble_ai.catalog.HELD_BACK_DIMENSIONS`). This module
keeps only the predicate that drives the discreet refusal — the gate itself
lives in the router, and it is no longer conditional on anything.
"""

from __future__ import annotations

from .catalog import Metric

#: Contract dimension that marks a metric as a vote-orientation metric.
POLITICS_DIMENSION = "politica"


def is_political_metric(metric: Metric | None) -> bool:
    """True iff ``metric`` is a vote-orientation metric (``dimension: politica``)."""
    return metric is not None and metric.dimension == POLITICS_DIMENSION
