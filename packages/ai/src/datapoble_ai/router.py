"""Deterministic NL -> intent -> parametrized SQL router (offline baseline).

This is the industrialised descendant of the prototype's ``ask.py``: a
keyword/synonym router over the semantic catalog, with the prototype's core
principle preserved — **every answer carries provenance, and anything outside
the catalog is refused, not hallucinated**.

It is fully testable without any API key. The OpenRouter path (see
``llm.py``) reuses this same intent->SQL->provenance machinery; the LLM only
ever *chooses* a catalog metric and an intent, never writes raw SQL.

Pipeline
--------
1. Resolve the active locale.
2. Detect intent shape: correlation (two metrics) / ranking (superlative across
   municipalities) / lookup (one metric for one municipality).
3. Match metric(s) against the catalog via labels + synonyms (accent-folded).
4. Match a municipality name if the intent needs one.
5. Apply guardrails: refuse if no metric (out of catalog), if the metric is
   ``planned``, or if the municipality is unknown.
6. Build a **parametrized, read-only** SQL statement and execute it.
7. Render a localized answer + a :class:`Provenance` block.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass

from .catalog import Catalog, Metric, normalize
from .i18n import format_number, t
from .types import (
    Answer,
    AnswerKind,
    Provenance,
    RefusalReason,
)
from .warehouse import Warehouse, WarehouseError

# Cue words (accent-folded) that signal a *ranking* across municipalities.
_RANK_MAX_CUES = {
    "ca": ["mes", "major", "mes alt", "mes gran", "maxim", "lidera", "top", "ranquing", "rang"],
    "es": ["mas", "mayor", "mas alto", "maximo", "lidera", "top", "ranking", "rango"],
}
_RANK_MIN_CUES = {
    "ca": ["menys", "menor", "mes baix", "minim"],
    "es": ["menos", "menor", "mas bajo", "minimo"],
}
# Cue words that signal a *correlation / relationship* between two metrics.
_CORR_CUES = {
    "ca": ["relacio", "relacionat", "correlacio", "correlacionat", "te a veure", "vincle", "associacio"],
    "es": ["relacion", "relacionado", "correlacion", "correlacionado", "tiene que ver", "vinculo", "asociacion"],
}
# Cue words that ask explicitly for a list/ranking of several rows.
_LIST_CUES = {
    "ca": ["ranquing", "llista", "ordena", "classificacio", "top"],
    "es": ["ranking", "lista", "ordena", "clasificacion", "top"],
}


@dataclass
class Intent:
    """Structured interpretation of a question (the LLM emits this too)."""

    kind: str                       # "lookup" | "ranking" | "correlation"
    metric: Metric | None = None
    metric_b: Metric | None = None  # only for correlation
    municipality: str | None = None  # resolved canonical name
    descending: bool = True         # ranking direction (True = max first)
    want_list: bool = False         # ranking: full list vs single top


class Router:
    """The deterministic agent backend."""

    def __init__(self, catalog: Catalog, warehouse: Warehouse):
        self.catalog = catalog
        self.warehouse = warehouse
        # Precompute the municipality directory from the mart so we can resolve
        # toponyms. Falls back gracefully if a mart lacks `municipi`.
        self._muni_index = self._build_muni_index()

    # ------------------------------------------------------------------ setup
    def _build_muni_index(self) -> dict[str, str]:
        """Map normalized municipality name -> canonical name, from the marts."""
        index: dict[str, str] = {}
        for table in self.catalog.tables():
            try:
                rows = self.warehouse.query(
                    f'SELECT DISTINCT municipi FROM "{table}" '
                    "WHERE municipi IS NOT NULL"
                )
            except WarehouseError:
                continue
            for row in rows:
                name = row["municipi"]
                index[normalize(name)] = name
        return index

    # -------------------------------------------------------------- matching
    def match_metric(self, question_norm: str, locale: str,
                     exclude: Metric | None = None) -> Metric | None:
        """Best catalog metric whose label/synonym appears in the question.

        Longest match wins (most specific phrase). Only *available* metrics are
        eligible here; ``planned`` metrics are matched separately so we can give
        a precise "not yet computed" refusal.
        """
        best: tuple[int, Metric] | None = None
        for metric in self.catalog.metrics.values():
            if not metric.is_available():
                continue
            if exclude is not None and metric.key == exclude.key:
                continue
            for term in metric.match_terms(locale):
                if term and re.search(rf"\b{re.escape(term)}", question_norm):
                    score = len(term)
                    if best is None or score > best[0]:
                        best = (score, metric)
                    break
        return best[1] if best else None

    def _matched_metrics_by_position(
        self, question_norm: str, locale: str
    ) -> list[tuple[int, int, Metric]]:
        """Available metrics that match, as ``(position, -length, metric)``.

        Sorted by *earliest appearance* in the question (then longest match).
        Used for correlation, where word order disambiguates which metric is
        the primary one (``entre l'índex i els residus`` -> índex first).
        """
        found: list[tuple[int, int, Metric]] = []
        for metric in self.catalog.metrics.values():
            if not metric.is_available():
                continue
            earliest: tuple[int, int] | None = None
            for term in metric.match_terms(locale):
                m = re.search(rf"\b{re.escape(term)}", question_norm)
                if m:
                    cand = (m.start(), -len(term))
                    if earliest is None or cand < earliest:
                        earliest = cand
            if earliest is not None:
                found.append((earliest[0], earliest[1], metric))
        found.sort(key=lambda t: (t[0], t[1]))
        return found

    def _match_any_metric(self, question_norm: str, locale: str) -> Metric | None:
        """Match including planned/non-public, for precise refusals."""
        best: tuple[int, Metric] | None = None
        for metric in self.catalog.metrics.values():
            for term in metric.match_terms(locale):
                if term and re.search(rf"\b{re.escape(term)}", question_norm):
                    if best is None or len(term) > best[0]:
                        best = (len(term), metric)
                    break
        return best[1] if best else None

    def match_municipality(self, question_norm: str) -> str | None:
        """Resolve a municipality name mentioned in the question."""
        best: str | None = None
        best_len = 0
        for norm_name, canonical in self._muni_index.items():
            if norm_name and norm_name in question_norm and len(norm_name) > best_len:
                best = canonical
                best_len = len(norm_name)
        return best

    def _has_cue(self, question_norm: str, cues: list[str]) -> bool:
        return any(re.search(rf"\b{re.escape(c)}", question_norm) for c in cues)

    def _names_unknown_place(self, question: str) -> bool:
        """Heuristic: does the question name a proper place we don't know?

        Used to turn "habitatges no principals de Barcelona" into a precise
        ``unknown_municipality`` refusal instead of a silent ranking. We look
        for a capitalised token (mid-sentence) that is neither a known
        municipality nor a common word. Conservative on purpose: false negatives
        just fall through to a ranking, which is the sensible default.
        """
        # Tokens that are capitalised but are not toponyms (sentence starters,
        # locale words). Lowercased for comparison.
        stop = {
            "quants", "quantes", "quina", "quin", "quines", "on",
            "cuantos", "cuantas", "cuanto", "que", "donde", "cual", "cuales",
            "habitatges", "viviendas", "el", "la", "els", "les", "los", "las",
        }
        tokens = re.findall(r"[A-ZÀ-Ý][\wÀ-ÿ'·]+", question)
        for i, tok in enumerate(tokens):
            if i == 0:  # sentence-initial capital carries no signal
                continue
            if tok.lower() in stop:
                continue
            if normalize(tok) in self._muni_index:
                return False  # it's a known municipality -> not "unknown"
            # A multi-word toponym (e.g. "Castellar de n'Hug") is matched by
            # match_municipality already; here a lone unknown capital suffices.
            return True
        return False

    # ---------------------------------------------------------------- parse
    def parse(self, question: str, locale: str) -> Intent | RefusalReason:
        """Turn a question into an :class:`Intent`, or a refusal reason."""
        qn = normalize(question)

        corr_cues = _CORR_CUES.get(locale, _CORR_CUES["ca"])
        list_cues = _LIST_CUES.get(locale, _LIST_CUES["ca"])
        max_cues = _RANK_MAX_CUES.get(locale, _RANK_MAX_CUES["ca"])
        min_cues = _RANK_MIN_CUES.get(locale, _RANK_MIN_CUES["ca"])

        # --- correlation: two distinct metrics + a relationship cue ---
        if self._has_cue(qn, corr_cues):
            ordered = self._matched_metrics_by_position(qn, locale)
            if len(ordered) >= 2:
                # Primary = first to appear in the question; secondary = next.
                m1 = ordered[0][2]
                m2 = ordered[1][2]
                return Intent(kind="correlation", metric=m1, metric_b=m2)

        # --- otherwise we need one primary metric ---
        metric = self.match_metric(qn, locale)
        if metric is None:
            # Did it match a planned/non-public metric? Give a precise refusal.
            any_metric = self._match_any_metric(qn, locale)
            if any_metric is not None and not any_metric.is_available():
                return RefusalReason.METRIC_PLANNED
            return RefusalReason.OUT_OF_CATALOG

        # --- ranking vs lookup ---
        muni = self.match_municipality(qn)
        wants_min = self._has_cue(qn, min_cues)
        wants_max = self._has_cue(qn, max_cues)
        wants_list = self._has_cue(qn, list_cues)
        is_ranking = wants_min or wants_max or wants_list

        # A known municipality + no ranking cue -> lookup.
        if muni is not None and not is_ranking:
            return Intent(kind="lookup", metric=metric, municipality=muni)

        # Lookup-shaped question (no ranking cue) that names an *unknown* place
        # -> refuse precisely, never silently fall back to a ranking.
        if muni is None and not is_ranking and self._names_unknown_place(question):
            return RefusalReason.UNKNOWN_MUNICIPALITY

        # Superlative / list cue, or an open "which municipality" question.
        return Intent(
            kind="ranking",
            metric=metric,
            descending=not wants_min,
            want_list=wants_list,
        )

    def _availability_guard(self, metric: Metric) -> RefusalReason | None:
        """Refusal reason if a metric must not be queried, else None."""
        if not metric.is_available():
            return RefusalReason.METRIC_PLANNED
        return None

    # ----------------------------------------------------------------- ask
    def ask(self, question: str, locale: str | None = None,
            backend: str = "offline") -> Answer:
        """Answer a question (or refuse), with provenance, in ``locale``.

        This is the offline entrypoint: parse NL -> intent, then execute. The
        OpenRouter backend skips ``parse`` (the model produces the intent) and
        calls :meth:`execute_intent` directly, so both paths share one guarded
        executor.
        """
        loc = self.catalog.resolve_locale(locale)
        parsed = self.parse(question, loc)
        if isinstance(parsed, RefusalReason):
            return self._refuse(question, loc, parsed, backend)
        return self.execute_intent(question, loc, parsed, backend)

    def execute_intent(self, question: str, locale: str, intent: Intent,
                       backend: str) -> Answer:
        """Execute a (trusted, already-validated) intent under the guardrails.

        Shared by the offline router and the OpenRouter backend. Re-checks
        metric availability defensively, then runs the parametrized read-only
        SQL. Any guardrail violation surfaces as a reasoned refusal, never an
        exception to the caller.
        """
        loc = self.catalog.resolve_locale(locale)
        # Defensive availability re-check (the LLM path could pass anything).
        for m in (intent.metric, intent.metric_b):
            if m is not None and not m.is_available():
                return self._refuse(question, loc, RefusalReason.METRIC_PLANNED,
                                    backend, label=m.label(loc))
        try:
            if intent.kind == "lookup":
                return self._answer_lookup(question, loc, intent, backend)
            if intent.kind == "ranking":
                return self._answer_ranking(question, loc, intent, backend)
            if intent.kind == "correlation":
                if intent.metric_b is None:
                    return self._refuse(question, loc,
                                        RefusalReason.UNSUPPORTED_QUESTION, backend)
                return self._answer_correlation(question, loc, intent, backend)
        except WarehouseError as exc:
            return self._refuse(
                question, loc, RefusalReason.GUARDRAIL_VIOLATION, backend,
                detail=str(exc),
            )
        return self._refuse(question, loc, RefusalReason.UNSUPPORTED_QUESTION, backend)

    # ------------------------------------------------------------- builders
    def _provenance(self, metric: Metric, locale: str, query: str,
                    params: dict) -> Provenance:
        """Assemble the provenance block from the contract for ``metric``."""
        # Derived metrics cite their upstream origin source when present.
        src_key = metric.source_key
        source = self.catalog.source(src_key)
        origin = self.catalog.source(metric.origin_source_key)
        # Prefer a human description: organisme + producte.
        def describe(s):
            if s is None:
                return None
            parts = [p for p in (s.organisme, s.producte) if p]
            return " — ".join(parts) if parts else s.key
        source_desc = describe(source)
        if origin is not None:
            source_desc = f"{describe(origin)} (via {source_desc})"
        return Provenance(
            metric=metric.key,
            metric_label=metric.label(locale),
            source=source_desc,
            source_key=src_key,
            date=metric.date,
            formula=metric.formula,
            query=query,
            params=params,
            license=(origin or source).llicencia if (origin or source) else None,
            note=metric.note(locale),
            is_fixture=self.warehouse.using_fixture.get(metric.table, False),
        )

    def _unit_suffix(self, metric: Metric, locale: str) -> str:
        unit = metric.unit(locale)
        if not unit:
            return ""
        # "%" hugs the number; worded units get a space.
        return unit if unit == "%" else f" {unit}"

    def _answer_lookup(self, question: str, locale: str, intent: Intent,
                       backend: str) -> Answer:
        metric = intent.metric
        assert metric is not None
        col = metric.column
        sql = (
            f'SELECT municipi, "{col}" AS value '
            f'FROM "{metric.table}" WHERE municipi = $muni'
        )
        params = {"muni": intent.municipality}
        rows = self.warehouse.query(sql, params)
        if not rows or rows[0]["value"] is None:
            return self._refuse(
                question, locale, RefusalReason.UNKNOWN_MUNICIPALITY, backend,
                name=intent.municipality,
            )
        value = rows[0]["value"]
        prov = self._provenance(metric, locale, sql, params)
        text = t(
            locale, "value_for",
            label=metric.label(locale),
            municipi=rows[0]["municipi"],
            value=format_number(value, locale),
            unit=self._unit_suffix(metric, locale),
        )
        text = self._with_provenance_and_note(text, prov, locale)
        return Answer(
            kind=AnswerKind.ANSWER, locale=locale, question=question,
            backend=backend, text=text, data=rows, provenance=prov,
            metric_key=metric.key,
        )

    def _answer_ranking(self, question: str, locale: str, intent: Intent,
                        backend: str) -> Answer:
        metric = intent.metric
        assert metric is not None
        col = metric.column
        order = "DESC" if intent.descending else "ASC"
        limit = 5 if intent.want_list else 1
        sql = (
            f'SELECT municipi, "{col}" AS value '
            f'FROM "{metric.table}" WHERE "{col}" IS NOT NULL '
            f'ORDER BY "{col}" {order} LIMIT {limit}'
        )
        rows = self.warehouse.query(sql)
        if not rows:
            return self._refuse(question, locale,
                                RefusalReason.UNSUPPORTED_QUESTION, backend)
        prov = self._provenance(metric, locale, sql, {})
        unit = self._unit_suffix(metric, locale)
        if intent.want_list:
            lines = [t(locale, "ranking_list_intro", label=metric.label(locale))]
            for i, r in enumerate(rows, 1):
                lines.append(t(
                    locale, "ranking_row", rank=i, municipi=r["municipi"],
                    value=format_number(r["value"], locale), unit=unit,
                ))
            text = "\n".join(lines)
        else:
            sup = t(locale, "superlative_max" if intent.descending else "superlative_min")
            text = t(
                locale, "ranking_top", sup=sup, label=metric.label(locale),
                municipi=rows[0]["municipi"],
                value=format_number(rows[0]["value"], locale), unit=unit,
            )
        text = self._with_provenance_and_note(text, prov, locale)
        return Answer(
            kind=AnswerKind.ANSWER, locale=locale, question=question,
            backend=backend, text=text, data=rows, provenance=prov,
            metric_key=metric.key,
        )

    def _answer_correlation(self, question: str, locale: str, intent: Intent,
                            backend: str) -> Answer:
        a, b = intent.metric, intent.metric_b
        assert a is not None and b is not None
        # Both metrics must share a mart to be joined on ine5/municipi.
        if a.table != b.table:
            sql = (
                f'SELECT x.municipi AS municipi, x."{a.column}" AS a, '
                f'y."{b.column}" AS b '
                f'FROM "{a.table}" x JOIN "{b.table}" y USING (municipi) '
                f'WHERE x."{a.column}" IS NOT NULL AND y."{b.column}" IS NOT NULL'
            )
        else:
            sql = (
                f'SELECT municipi, "{a.column}" AS a, "{b.column}" AS b '
                f'FROM "{a.table}" '
                f'WHERE "{a.column}" IS NOT NULL AND "{b.column}" IS NOT NULL'
            )
        rows = self.warehouse.query(sql)
        xs = [r["a"] for r in rows]
        ys = [r["b"] for r in rows]
        rho = _spearman(xs, ys)
        # Provenance cites the primary metric; note explains it's a relationship.
        prov = self._provenance(a, locale, sql, {})
        prov.formula = f"spearman({a.key}, {b.key})"
        text = t(
            locale, "correlation",
            label_a=a.label(locale), label_b=b.label(locale),
            rho=(format_number(rho, locale) if rho is not None else "—"),
            n=len(rows),
        )
        text = self._with_provenance_and_note(text, prov, locale)
        return Answer(
            kind=AnswerKind.ANSWER, locale=locale, question=question,
            backend=backend, text=text, data=rows, provenance=prov,
            metric_key=a.key,
        )

    def _with_provenance_and_note(self, text: str, prov: Provenance,
                                  locale: str) -> str:
        """Append the provenance line (and any caveat note) to an answer."""
        prov_line = t(
            locale, "provenance_line",
            source=prov.source or "—",
            date=prov.date or "s.d.",
            formula=prov.formula or "—",
        )
        out = f"{text} {prov_line}"
        if prov.note:
            out += " " + t(locale, "note_prefix") + prov.note
        return out

    # --------------------------------------------------------------- refuse
    def _refuse(self, question: str, locale: str, reason: RefusalReason,
                backend: str, name: str | None = None, label: str | None = None,
                detail: str | None = None) -> Answer:
        if reason == RefusalReason.OUT_OF_CATALOG:
            metrics = ", ".join(
                m.label(locale) for m in self.catalog.available_metrics()
            )
            text = t(locale, "refusal_out_of_catalog", metrics=metrics)
        elif reason == RefusalReason.METRIC_PLANNED:
            any_m = self._match_any_metric(normalize(question), locale)
            text = t(locale, "refusal_planned",
                     label=any_m.label(locale) if any_m else (label or "?"))
        elif reason == RefusalReason.UNKNOWN_MUNICIPALITY:
            text = t(locale, "refusal_unknown_municipality", name=name or "?")
        elif reason == RefusalReason.GUARDRAIL_VIOLATION:
            text = t(locale, "refusal_guardrail", why=detail or "—")
        elif reason == RefusalReason.BUDGET_EXCEEDED:
            text = t(locale, "refusal_budget_exceeded")
        elif reason == RefusalReason.RATE_LIMITED:
            text = t(locale, "refusal_rate_limited")
        else:  # UNSUPPORTED_QUESTION
            m = self.match_metric(normalize(question), locale)
            text = t(locale, "refusal_unsupported",
                     label=m.label(locale) if m else (label or "?"))
        return Answer(
            kind=AnswerKind.REFUSAL, locale=locale, question=question,
            backend=backend, text=text, refusal_reason=reason,
        )


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    """Spearman rank correlation, dependency-free.

    We rank both series (average ranks for ties) and take the Pearson
    correlation of the ranks. Returns None if undefined (n<2 or zero variance).
    """
    n = len(xs)
    if n < 2 or len(ys) != n:
        return None
    rx = _rank(xs)
    ry = _rank(ys)
    try:
        return round(statistics.correlation(rx, ry), 3)
    except statistics.StatisticsError:
        return None


def _rank(values: list[float]) -> list[float]:
    """Average ranks (1-based) handling ties."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1  # average of tied positions, 1-based
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks
