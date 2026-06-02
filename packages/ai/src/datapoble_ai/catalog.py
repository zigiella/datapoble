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
        # Absent status means it is live; the contract only tags `planned`.
        return self.raw.get("status", "public")

    def is_available(self) -> bool:
        """True when the metric is public and actually computed.

        ``status: planned`` => defined but not yet produced by the pipeline, so
        the router must not query it (it would hit a missing column).
        """
        return self.visibility == "public" and self.status != "planned"

    # --- localized accessors ---
    def label(self, locale: str = DEFAULT_LOCALE) -> str:
        return localized(self.raw.get("label"), locale) or self.key

    def definition(self, locale: str = DEFAULT_LOCALE) -> str | None:
        return localized(self.raw.get("definicio"), locale)

    def unit(self, locale: str = DEFAULT_LOCALE) -> str | None:
        return localized(self.raw.get("unit"), locale)

    def note(self, locale: str = DEFAULT_LOCALE) -> str | None:
        return localized(self.raw.get("nota"), locale)

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
        for lw in lead_words:
            if stripped.startswith(lw + " "):
                terms.add(stripped[len(lw) + 1:].strip())
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
        """Public + computed metrics (what the agent is allowed to query)."""
        return [m for m in self.metrics.values() if m.is_available()]

    def tables(self) -> set[str]:
        """The set of mart tables referenced by available metrics.

        These are the *only* tables the SQL layer may touch (guardrail).
        """
        return {m.table for m in self.available_metrics() if m.table}

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
