"""Public facade: the ``Agent`` Mirador (and the API) call.

One entrypoint that wires the catalog, the warehouse and a backend together and
answers questions with provenance. Backend selection is automatic and honest:

- ``mode="offline"`` (default) -> deterministic router, no network, no key.
- ``mode="openrouter"`` -> the LLM path (requires ``OPENROUTER_API_KEY``).
- ``mode="auto"`` -> OpenRouter *iff* a key is present, else offline.

Today, with no key, ``auto`` resolves to offline — so the system is fully
functional and testable now, and gains the LLM transparently once Bea provides
the secret.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .catalog import Catalog, load_catalog
from .costcontrol import SpendGuard
from .llm import LLMBackend, OfflineBackend, OpenRouterBackend
from .types import Answer
from .warehouse import Warehouse

if TYPE_CHECKING:  # avoid importing the generative layer on the default path
    from .narrator import Narrator


class Agent:
    """The datapoble traceable text-to-SQL agent."""

    def __init__(self, catalog: Catalog | None = None,
                 warehouse: Warehouse | None = None,
                 backend: LLMBackend | None = None,
                 mode: str = "auto",
                 metrics_path: str | Path | None = None,
                 marts_dir: Path | None = None,
                 use_fixtures: bool = False,
                 spend_guard: SpendGuard | None = None,
                 narrator: Narrator | None = None):
        self.catalog = catalog or load_catalog(
            str(metrics_path) if metrics_path else None
        )
        # `use_fixtures=True` pins the seed warehouse — used by the deterministic
        # offline gate so it tests the logic, not whichever marts are on disk.
        self.warehouse = warehouse or Warehouse(
            self.catalog, marts_dir=marts_dir, use_fixtures=use_fixtures
        )
        # The hard spend cap is only meaningful on the LLM path; the offline
        # backend never spends, so it ignores it.
        self.spend_guard = spend_guard
        self.backend = backend or self._select_backend(mode)
        # The generative layer (X1 / contract C5). Off unless injected: with no
        # narrator the agent behaves exactly as before — a traceable
        # deterministic answer. A narration can only ever *replace the prose* of
        # an answer the router already produced, and only if the cage certifies
        # it; otherwise the deterministic text stands.
        self.narrator = narrator

    def _select_backend(self, mode: str) -> LLMBackend:
        if mode == "offline":
            return OfflineBackend(self.catalog, self.warehouse)
        if mode == "openrouter":
            return OpenRouterBackend(self.catalog, self.warehouse,
                                     spend_guard=self.spend_guard)
        # auto: prefer the LLM only if the secret is actually present.
        if mode == "auto" and OpenRouterBackend.available():
            return OpenRouterBackend(self.catalog, self.warehouse,
                                     spend_guard=self.spend_guard)
        return OfflineBackend(self.catalog, self.warehouse)

    @property
    def mode(self) -> str:
        """The backend actually in use (``offline`` / ``openrouter``)."""
        return self.backend.name

    def ask(self, question: str, locale: str | None = None) -> Answer:
        """Answer ``question`` in ``locale`` (or the contract default).

        With a narrator wired, the traceable answer is produced first and only
        then handed to the generative layer, which may re-word its prose *if* the
        cage certifies the result (contract C5). The deterministic answer is the
        floor and is never bypassed.
        """
        answer = self.backend.ask(question, locale=locale)
        if self.narrator is None:
            return answer
        from .narrator import context_for

        loc = self.catalog.resolve_locale(locale)
        allowed, why = self.narrator.can_narrate(answer)
        if not allowed:
            return self.narrator.narrate(answer, {})  # records why, changes nothing
        context = context_for(self.catalog, self.warehouse, answer, loc)
        return self.narrator.narrate(answer, context)

    def close(self) -> None:
        self.warehouse.close()

    def __enter__(self) -> Agent:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
