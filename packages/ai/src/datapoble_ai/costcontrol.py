"""Cost control for the LLM path — deterministic-first, cache, rate-limit, cap.

The only thing that costs money in Brúixola is a call to OpenRouter. Everything
in this module exists to make those calls **rare and bounded**, and all of it is
**key-independent and testable offline** (no network, no secret). The pieces:

1. :class:`QuestionCache` — normalize a question (lowercase, trim, collapse
   whitespace) keyed by locale, and reuse a previous answer. In-memory LRU.
   *Persistence note:* on Render the filesystem is ephemeral and the service may
   run multiple instances, so a cache that survives restarts would need an
   external store (Redis / KV). Here we keep an in-process LRU on purpose; it is
   the cheap 80% and it never lies (cached answers carry their full provenance).

2. :class:`RateLimiter` — a token-bucket per identity (IP / user). Refills at a
   steady rate; a request with no token is rejected. Used by the API to return a
   friendly ``429`` in Catalan.

3. :class:`SpendGuard` — a hard ceiling on estimated OpenRouter spend per day and
   per month. Before each LLM call we ask ``can_spend``; after a call we
   ``record`` the (estimated) cost. Once a ceiling is crossed the guard says no
   and the API degrades gracefully to "no more AI queries today" — the
   deterministic answers keep working, because they never touch this guard.

The :class:`CostControl` facade bundles the three and reads its configuration
from the environment (all optional, with safe defaults), so deployment tuning is
a matter of env vars on Render, never code.

None of these classes import the OpenRouter client or need a key. The wiring
that actually *uses* them lives in :mod:`datapoble_ai.llm` (the backend) and
:mod:`datapoble_ai.api` (the HTTP surface).
"""

from __future__ import annotations

import os
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field

from .types import Answer

# --- normalisation -----------------------------------------------------------

_WS = re.compile(r"\s+")


def normalize_question(question: str, locale: str) -> str:
    """Canonical cache key for a question in a locale.

    Lowercase, strip, and collapse internal whitespace so that
    ``"  Quina   població té Berga?  "`` and ``"quina població té berga?"`` hit
    the same cache entry. We deliberately keep accents and punctuation: they can
    change meaning, and the deterministic router already accent-folds for
    *matching* — caching is about identical questions, so we stay conservative.
    The locale is part of the key (the same text answers differently in ca/es).
    """
    collapsed = _WS.sub(" ", question.strip().lower())
    return f"{locale}\x1f{collapsed}"


# --- question cache ----------------------------------------------------------


class QuestionCache:
    """A small thread-safe LRU over normalized (question, locale) -> Answer.

    Only *answers worth reusing* should be put here (the API caches LLM-backed
    answers; deterministic answers are already free to recompute). ``maxsize<=0``
    disables the cache entirely.
    """

    def __init__(self, maxsize: int = 512):
        self.maxsize = maxsize
        self._store: OrderedDict[str, Answer] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, question: str, locale: str) -> Answer | None:
        if self.maxsize <= 0:
            return None
        key = normalize_question(question, locale)
        with self._lock:
            ans = self._store.get(key)
            if ans is None:
                self.misses += 1
                return None
            self._store.move_to_end(key)  # mark most-recently-used
            self.hits += 1
            return ans

    def put(self, question: str, locale: str, answer: Answer) -> None:
        if self.maxsize <= 0:
            return
        key = normalize_question(question, locale)
        with self._lock:
            self._store[key] = answer
            self._store.move_to_end(key)
            while len(self._store) > self.maxsize:
                self._store.popitem(last=False)  # evict least-recently-used

    def stats(self) -> dict:
        with self._lock:
            return {
                "size": len(self._store),
                "maxsize": self.maxsize,
                "hits": self.hits,
                "misses": self.misses,
            }

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self.hits = 0
            self.misses = 0


# --- rate limiter ------------------------------------------------------------


@dataclass
class _Bucket:
    tokens: float
    last: float


class RateLimiter:
    """Token-bucket rate limiter keyed by an identity string (IP / user).

    ``capacity`` tokens, refilled at ``refill_per_sec``. Each accepted request
    spends one token; a request with no token left is rejected (the API maps that
    to ``429``). ``capacity<=0`` disables limiting (always allowed). Buckets are
    created lazily and pruned opportunistically so memory stays bounded under a
    spray of distinct IPs.
    """

    def __init__(self, capacity: float = 30, refill_per_sec: float = 0.5,
                 max_identities: int = 10_000):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.max_identities = max_identities
        self._buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    def _now(self) -> float:
        return time.monotonic()

    def check(self, identity: str) -> tuple[bool, float]:
        """Return ``(allowed, retry_after_seconds)``.

        ``retry_after_seconds`` is 0 when allowed, else the wait until one token
        is available (so the API can put it in a ``Retry-After`` header).
        """
        if self.capacity <= 0:
            return True, 0.0
        now = self._now()
        with self._lock:
            bucket = self._buckets.get(identity)
            if bucket is None:
                if len(self._buckets) >= self.max_identities:
                    self._prune(now)
                bucket = _Bucket(tokens=self.capacity, last=now)
                self._buckets[identity] = bucket
            # Refill proportional to elapsed time, capped at capacity.
            elapsed = now - bucket.last
            bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.refill_per_sec)
            bucket.last = now
            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                return True, 0.0
            needed = 1.0 - bucket.tokens
            retry_after = needed / self.refill_per_sec if self.refill_per_sec > 0 else 60.0
            return False, retry_after

    def _prune(self, now: float) -> None:
        """Drop buckets that have fully refilled (i.e. idle) to bound memory."""
        full = [
            k for k, b in self._buckets.items()
            if min(self.capacity, b.tokens + (now - b.last) * self.refill_per_sec)
            >= self.capacity
        ]
        for k in full:
            del self._buckets[k]
        # If still over budget (everyone active), evict the oldest-seen.
        if len(self._buckets) >= self.max_identities:
            oldest = sorted(self._buckets.items(), key=lambda kv: kv[1].last)
            for k, _ in oldest[: len(self._buckets) // 10 + 1]:
                del self._buckets[k]


# --- spend guard -------------------------------------------------------------

# Rough default price per LLM call, in USD. OpenRouter bills per token and the
# exact figure depends on the model; this is a deliberately conservative
# *estimate* used only to enforce a ceiling, never to bill anyone. Override per
# deployment (and per model) via env / ctor. See `pricing.py` for per-model
# numbers used by the multi-model eval script.
DEFAULT_USD_PER_CALL = 0.01


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _month() -> str:
    return time.strftime("%Y-%m", time.gmtime())


@dataclass
class SpendGuard:
    """Hard ceiling on estimated OpenRouter spend, per UTC day and month.

    Tracks an *estimated* running cost. ``can_spend`` is consulted **before**
    each LLM call; ``record`` is called **after** with the (estimated or actual)
    cost. When a ceiling is hit, ``can_spend`` returns False and the caller must
    not call the LLM — the API then degrades to the deterministic path plus a
    polite "daily AI budget reached" message.

    Ceilings ``<=0`` mean "unbounded" for that period. Defaults are intentionally
    small so an unconfigured production deploy fails *safe* (cheap), not
    surprising.
    """

    daily_usd: float = 1.0
    monthly_usd: float = 20.0
    usd_per_call: float = DEFAULT_USD_PER_CALL
    _day: str = field(default_factory=_today)
    _month_key: str = field(default_factory=_month)
    _spent_day: float = 0.0
    _spent_month: float = 0.0
    _calls_day: int = 0

    def __post_init__(self) -> None:
        self._lock = threading.Lock()

    def _rollover(self) -> None:
        d, m = _today(), _month()
        if d != self._day:
            self._day = d
            self._spent_day = 0.0
            self._calls_day = 0
        if m != self._month_key:
            self._month_key = m
            self._spent_month = 0.0

    def can_spend(self, estimated: float | None = None) -> bool:
        """True if one more call (at ``estimated`` USD) stays under both ceilings."""
        cost = self.usd_per_call if estimated is None else estimated
        with self._lock:
            self._rollover()
            if self.daily_usd > 0 and self._spent_day + cost > self.daily_usd:
                return False
            if self.monthly_usd > 0 and self._spent_month + cost > self.monthly_usd:
                return False
            return True

    def record(self, cost: float | None = None) -> None:
        """Account for a call that happened (estimated cost if actual unknown)."""
        c = self.usd_per_call if cost is None else cost
        with self._lock:
            self._rollover()
            self._spent_day += c
            self._spent_month += c
            self._calls_day += 1

    def stats(self) -> dict:
        with self._lock:
            self._rollover()
            return {
                "day": self._day,
                "month": self._month_key,
                "spent_day_usd": round(self._spent_day, 4),
                "spent_month_usd": round(self._spent_month, 4),
                "calls_day": self._calls_day,
                "daily_cap_usd": self.daily_usd,
                "monthly_cap_usd": self.monthly_usd,
                "usd_per_call": self.usd_per_call,
            }


# --- facade ------------------------------------------------------------------


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class CostControl:
    """Bundle of cache + rate-limiter + spend guard, configured from env.

    Read once at API startup and shared across requests. Every knob has a safe
    default and an env override, so production tuning never needs a code change:

    - ``AI_CACHE_MAXSIZE``        (default 512; ``0`` disables the cache)
    - ``AI_RATE_CAPACITY``        (default 30 tokens; ``0`` disables limiting)
    - ``AI_RATE_REFILL_PER_SEC``  (default 0.5 tokens/s ≈ 30/min sustained)
    - ``AI_DAILY_USD``            (default 1.0; ``0`` = unbounded)
    - ``AI_MONTHLY_USD``          (default 20.0; ``0`` = unbounded)
    - ``AI_USD_PER_CALL``         (default 0.01; conservative per-call estimate)
    """

    cache: QuestionCache
    rate_limiter: RateLimiter
    spend_guard: SpendGuard

    @classmethod
    def from_env(cls) -> CostControl:
        return cls(
            cache=QuestionCache(maxsize=_env_int("AI_CACHE_MAXSIZE", 512)),
            rate_limiter=RateLimiter(
                capacity=_env_float("AI_RATE_CAPACITY", 30),
                refill_per_sec=_env_float("AI_RATE_REFILL_PER_SEC", 0.5),
            ),
            spend_guard=SpendGuard(
                daily_usd=_env_float("AI_DAILY_USD", 1.0),
                monthly_usd=_env_float("AI_MONTHLY_USD", 20.0),
                usd_per_call=_env_float("AI_USD_PER_CALL", DEFAULT_USD_PER_CALL),
            ),
        )

    def stats(self) -> dict:
        return {
            "cache": self.cache.stats(),
            "spend": self.spend_guard.stats(),
            "rate_limit": {
                "capacity": self.rate_limiter.capacity,
                "refill_per_sec": self.rate_limiter.refill_per_sec,
            },
        }
