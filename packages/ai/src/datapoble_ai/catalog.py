"""Catalog loader for the semantic contract (``semantic/metrics.yml``).

The catalog is the single source of truth. Brúixola *consumes* it; it never
redefines metrics (that is Talaia's contract). Everything downstream — the
deterministic router, the guardrails, the LLM tool schema, the provenance
block — is derived from what this module exposes.

Design notes
------------
- Read-only view over the YAML. We do not mutate or persist anything here.
- Locale-aware accessors: ``label``/``definicio``/``unit`` can be a plain
  string (locale-independent, e.g. ``"%"``) or a ``{ca, es}`` mapping.
- ``status: planned`` metrics are *defined but not yet computed*. They stay in
  the catalog (so we can answer "that exists but isn't available yet") but the
  router must refuse to query them. See :meth:`Metric.is_available`.
- Some whole *dimensions* are held back from what the agent advertises, even
  though the contract keeps them public. See :data:`HELD_BACK_DIMENSIONS`.
"""

from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Locales the contract declares it supports. Kept in sync with metrics.yml meta.
SUPPORTED_LOCALES: tuple[str, ...] = ("ca", "es")
DEFAULT_LOCALE = "ca"

#: Contract ``status`` values that mean **never serve this metric**.
#:
#: - ``planned``: declared in the contract, not yet produced by the pipeline.
#:   Querying it would hit a missing column.
#: - ``deprecated``: produced once, then retired by an editorial vote
#:   (``index_turisme``, Bea 2026-07-18). The column may still physically exist
#:   in the mart, so nothing *fails* — the agent would just quietly keep serving
#:   a number the project has decided not to stand behind. That is the worse
#:   failure mode of the two, and the reason this is a set and not an ``!=``.
#:
#: Both stay in the contract on purpose: we want to be able to say "that metric
#: exists, and here is why you are not getting it".
NOT_SERVED_STATUSES: frozenset[str] = frozenset({"planned", "deprecated"})

#: Dimensions held back from the catalogue the agent **advertises and queries**.
#:
#: These are public on the web and in the glossary; what is withheld is the
#: agent's ability to enumerate and answer them. Holding back *here*, at the
#: catalog, is what keeps them out of every derived surface at once: the LLM
#: tool enum and system prompt (:mod:`llm`), the SQL table allow-list
#: (:meth:`Catalog.tables` -> ``Warehouse.allowed_tables``), the "metrics I can
#: answer" list in the out-of-catalog refusal, and the ``/metrics`` endpoint.
#:
#: - ``origen`` (nationality / birthplace / naturalisation) — **unconditional**.
#:   Held until the origen frontier exists: the guardrail that refuses
#:   individual-level, causal or ethnic-framing queries and enforces the
#:   ecological, non-«extranjería» reading (task #71).
#: - ``politica`` (vote orientation) — **conditional**, see
#:   :data:`KEYED_DIMENSIONS`. Bea's call, 2026-07-20: electoral goes behind the
#:   fence. A refusal already existed at the answer layer
#:   (:class:`~datapoble_ai.politics.PoliticsGate`), but it keys off a *resolved*
#:   metric, so every path that merely *enumerates* the catalog walked around it
#:   and advertised what the agent would then refuse.
HELD_BACK_DIMENSIONS: frozenset[str] = frozenset({"origen", "politica"})

#: The held-back dimensions a runtime key can still open.
#:
#: ``politica`` is gated, not removed: :class:`~datapoble_ai.politics.PoliticsGate`
#: opens it for a question carrying the secret read from ``AI_POLITICS_UNLOCK``.
#: Whether the team keeps that key is Bea's call, not this module's — so the
#: hold-back deliberately does **not** revoke it. The practical consequence is
#: that the tables of these dimensions must stay in the SQL allow-list (see
#: :meth:`Catalog.tables`), or the unlocked path would die at the guardrail.
#:
#: ``origen`` is *not* here: it has no key, so its tables leave the allow-list.
KEYED_DIMENSIONS: frozenset[str] = frozenset({"politica"})


def _repo_root() -> Path:
    """Locate the repository root by walking up until we find ``semantic/``.

    Works whether the package is installed editable, run from a worktree, or
    imported from tests. An explicit ``DATAPOBLE_ROOT`` env var wins (useful in
    CI / containers where the layout may differ).
    """
    override = os.environ.get("DATAPOBLE_ROOT")
    if override:
        return Path(override).resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "semantic" / "metrics.yml").is_file():
            return parent
    # Fallback: repo root is four levels up from this file
    # (src/datapoble_ai/catalog.py -> packages/ai/src/datapoble_ai).
    return here.parents[3]


def default_metrics_path() -> Path:
    """Absolute path to the canonical ``semantic/metrics.yml``."""
    return _repo_root() / "semantic" / "metrics.yml"


def normalize(text: str) -> str:
    """Lowercase + strip accents, for accent-insensitive matching.

    Catalan/Spanish toponyms and metric synonyms are full of accents and
    apostrophes (``Castellar de n'Hug``). We fold accents and lowercase so the
    deterministic router can match ``poblacio`` against ``Població`` etc.
    """
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def localized(value: Any, locale: str) -> Any:
    """Resolve a possibly-localized contract value for ``locale``.

    A value may be:
    - a plain scalar (``"%"``, ``"0-100"``) -> returned as-is,
    - a ``{ca: ..., es: ...}`` mapping -> the entry for ``locale`` (falling
      back to the default locale, then to any available value).
    """
    if not isinstance(value, dict):
        return value
    if locale in value:
        return value[locale]
    if DEFAULT_LOCALE in value:
        return value[DEFAULT_LOCALE]
    # Last resort: first available value, so we never crash on a partial entry.
    return next(iter(value.values()), None)


@dataclass(frozen=True)
class Source:
    """A declared data source (provenance lives here)."""

    key: str
    organisme: str | None = None
    producte: str | None = None
    acces: str | None = None
    llicencia: str | None = None
    dataset_id: str | None = None
    nota: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class Metric:
    """A single metric from the contract.

    Only fields the agent needs are promoted to attributes; the untouched YAML
    is kept in :attr:`raw` for anything we did not model explicitly.
    """

    key: str
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    # --- contract fields (kept as raw, resolved per-locale on access) ---
    @property
    def dimension(self) -> str | None:
        return self.raw.get("dimension")

    @property
    def formula(self) -> str | None:
        return self.raw.get("formula")

    @property
    def source_key(self) -> str | None:
        return self.raw.get("source")

    @property
    def origin_source_key(self) -> str | None:
        """Upstream primary source for derived (``datapoble``) metrics."""
        return self.raw.get("origin_source")

    @property
    def date(self) -> str | None:
        return self.raw.get("date")

    @property
    def table(self) -> str | None:
        return self.raw.get("table")

    @property
    def column(self) -> str | None:
        return self.raw.get("column")

    @property
    def visibility(self) -> str:
        return self.raw.get("visibility", "public")

    @property
    def status(self) -> str:
        # Absent status means it is live; the contract only tags the exceptions
        # (`planned`, `deprecated`).
        return self.raw.get("status", "public")

    @property
    def is_held_back(self) -> bool:
        """True when the metric's whole dimension is withheld from the agent.

        See :data:`HELD_BACK_DIMENSIONS`. Held back is orthogonal to computed:
        an ``origen`` metric is fully produced and live on the web; the agent
        just does not get to enumerate or query it.
        """
        return self.dimension in HELD_BACK_DIMENSIONS

    @property
    def is_keyed(self) -> bool:
        """True when a runtime key can still open this held-back metric.

        See :data:`KEYED_DIMENSIONS`. Only meaningful together with
        :attr:`is_held_back`.
        """
        return self.dimension in KEYED_DIMENSIONS

    def is_computed(self) -> bool:
        """True when the pipeline actually produces this metric.

        Ignores the hold-back gate on purpose: this is the question "is there a
        number behind this key?", not "may the agent show it?". The unlocked
        political path checks *this* — a held-back metric may be openable with a
        key, but a ``planned`` one has no data to open.
        """
        return self.visibility == "public" and self.status not in NOT_SERVED_STATUSES

    def is_available(self) -> bool:
        """True when the agent may advertise **and** query this metric.

        Two independent gates, both of which must be open:

        1. **Computed** — :meth:`is_computed`. ``planned`` was never produced;
           ``deprecated`` was retired by an editorial vote and must not be
           served even though its column may still sit in the mart.
        2. **Not held back** — :attr:`is_held_back`. Sensitive dimensions
           (``origen``, ``politica``) stay out of everything derived from this
           predicate, whatever their status.

        This is the single predicate every downstream surface reads, which is
        the point: a gate that has to be re-implemented per surface is a gate
        that will be missing from one of them.
        """
        if self.is_held_back:
            return False
        return self.is_computed()

    # --- localized accessors ---
    def label(self, locale: str = DEFAULT_LOCALE) -> str:
        return localized(self.raw.get("label"), locale) or self.key

    def definition(self, locale: str = DEFAULT_LOCALE) -> str | None:
        return localized(self.raw.get("definicio"), locale)

    def unit(self, locale: str = DEFAULT_LOCALE) -> str | None:
        return localized(self.raw.get("unit"), locale)

    def note(self, locale: str = DEFAULT_LOCALE) -> str | None:
        """The caveat the contract declares for this metric, if any.

        The contract writes it under **two** keys: ``nota:`` (5 metrics — IETR and
        friends) and ``caveat:`` (14 metrics — every inference of the pressure
        family: ``poblacio_pernocta_est``, ``gap_pernocta``, ``confianca`` …).
        Only ``nota`` was read here, so the caveats of exactly the metrics that
        most need one — the ones whose own text says *"INFERÈNCIA, no cens …
        Lectura ECOLÒGICA"* — were dropped on the floor and never reached the
        reader. Found during the X1 harvest (contract C5): the cage cannot enforce
        an obligated caveat that the catalog refuses to surface.

        Since the 2026-07-17 contract unification, ``caveat`` is the ONLY
        metric-level key (27 metrics carry it); ``nota`` remains as a legacy
        fallback so a stray key never silently drops a warning again.
        """
        value = self.raw.get("caveat")
        if value is None:
            value = self.raw.get("nota")
        return localized(value, locale)

    def synonyms(self, locale: str = DEFAULT_LOCALE) -> list[str]:
        syn = self.raw.get("synonyms")
        if not syn:
            return []
        return list(localized(syn, locale) or [])

    def match_terms(self, locale: str = DEFAULT_LOCALE) -> list[str]:
        """All normalized strings that should match this metric in NL.

        The key, the label, every synonym, and a few *label variants* with
        leading function tokens stripped (``%``, ``vot``/``voto``,
        ``establiments``/``establecimientos``…). The variants let a phrase like
        ``extrema dreta`` match the label ``% vot extrema dreta`` (the contract
        does not list a synonym for it). Returned longest-first so the router
        prefers the most specific phrase (``segona residencia`` before
        ``residencia``).

        A derived variant must still *name* the metric: if stripping the lead
        word leaves a bare qualifier phrase (``per habitant``, ``/ 1000 hab``),
        it is discarded. Found via the /pregunta-li chips (B3): «residus per
        habitant» matched ``hab_per_hab`` — «Habitatges per habitant» minus the
        lead word left ``per habitant``, which outscored the ``residus`` synonym
        on length and answered the wrong metric.
        """
        terms = {self.key, self.label(locale)}
        terms.update(self.synonyms(locale))
        # Derive label variants by dropping a small set of leading qualifiers.
        label_norm = normalize(self.label(locale))
        # Strip a leading "%" / "% " qualifier.
        stripped = label_norm.lstrip("% ").strip()
        if stripped:
            terms.add(stripped)
        # Drop a leading function word so "% vot extrema dreta" -> "extrema dreta".
        lead_words = ("vot", "voto", "establiments", "establecimientos",
                      "habitatges", "viviendas", "index d", "indice d")
        # Leads that reveal the remainder is a unit/qualifier, not a name.
        bare_qualifier = ("per ", "por ", "de ", "del ", "d'", "/", "x ")
        for lw in lead_words:
            if stripped.startswith(lw + " "):
                variant = stripped[len(lw) + 1:].strip()
                if variant and not variant.startswith(bare_qualifier):
                    terms.add(variant)
        normalized = {normalize(t) for t in terms if t and len(normalize(t)) >= 3}
        return sorted(normalized, key=len, reverse=True)


class Catalog:
    """In-memory, read-only view of the semantic contract."""

    def __init__(self, data: dict[str, Any], path: Path | None = None):
        self._data = data
        self.path = path
        meta = data.get("meta", {})
        self.project: str = meta.get("project", "datapoble")
        self.version: str = str(meta.get("version", "0"))
        self.locales: list[str] = list(meta.get("locales", SUPPORTED_LOCALES))
        self.default_locale: str = meta.get("default_locale", DEFAULT_LOCALE)
        self.join_key: str = meta.get("join_key", "ine5")

        self.sources: dict[str, Source] = {
            key: Source(key=key, raw=val, **{
                k: val.get(k)
                for k in ("organisme", "producte", "acces", "llicencia",
                          "dataset_id", "nota")
            })
            for key, val in data.get("sources", {}).items()
        }
        self.metrics: dict[str, Metric] = {
            key: Metric(key=key, raw=val)
            for key, val in data.get("metrics", {}).items()
        }
        self.entities: dict[str, Any] = data.get("entities", {})
        self.sample_questions: dict[str, list[str]] = data.get(
            "sample_questions", {}
        )

    # --- lookups ---
    def metric(self, key: str) -> Metric | None:
        return self.metrics.get(key)

    def source(self, key: str | None) -> Source | None:
        if key is None:
            return None
        return self.sources.get(key)

    def available_metrics(self) -> list[Metric]:
        """Public + computed + not held back — what the agent may advertise.

        Every derived surface reads this: the LLM tool enum and system prompt,
        the deterministic router's matcher, the ``/metrics`` endpoint and the
        "metrics I can answer" list in the out-of-catalog refusal.
        """
        return [m for m in self.metrics.values() if m.is_available()]

    def keyed_metrics(self) -> list[Metric]:
        """Computed metrics that are held back but a runtime key can open.

        See :data:`KEYED_DIMENSIONS`. Never advertised; reachable only once
        :class:`~datapoble_ai.politics.PoliticsGate` has opened.
        """
        return [
            m for m in self.metrics.values()
            if m.is_held_back and m.is_keyed and m.is_computed()
        ]

    def tables(self) -> set[str]:
        """The set of mart tables the SQL layer may touch (guardrail).

        Available metrics **plus** the keyed ones. The keyed tables have to be
        here or the unlocked political path would be built, then rejected by the
        allow-list — a confusing failure for a route that is meant to work.

        This allow-list is a *blast-radius* bound (no SQL outside contract
        tables), not the policy gate. Who may read a keyed table is decided
        above, at :meth:`Metric.is_available` and in the router. Note what this
        does exclude: ``origen`` has no key, so ``mart_demografia`` drops out of
        the allow-list entirely.
        """
        served = self.available_metrics() + self.keyed_metrics()
        return {m.table for m in served if m.table}

    def resolve_locale(self, locale: str | None) -> str:
        """Coerce a requested locale into a supported one."""
        if locale and locale in self.locales:
            return locale
        return self.default_locale

    @classmethod
    def load(cls, path: str | Path | None = None) -> Catalog:
        p = Path(path) if path else default_metrics_path()
        with open(p, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return cls(data, path=p)


@lru_cache(maxsize=4)
def load_catalog(path: str | None = None) -> Catalog:
    """Cached catalog loader. Pass an explicit path to bypass the default."""
    return Catalog.load(path)
