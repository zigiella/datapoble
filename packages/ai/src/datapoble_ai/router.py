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
from .politics import PoliticsGate, is_political_metric
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

# INE/Idescat registers write the article as a suffix: «Pobla de Lillet, la»,
# «Espunyola, l'». People ask with the natural form («la Pobla de Lillet»), so
# the municipality index carries both spellings (see :func:`_muni_name_variants`).
_INE_ARTICLE = re.compile(
    r"^(?P<base>.+?),\s*(?P<art>els|les|los|las|el|la|l'|es|sa|na)\s*$",
    re.IGNORECASE,
)


def natural_muni_name(name: str) -> str:
    """The name a person would say: register style -> natural article.

    «Pobla de Lillet, la» → «la Pobla de Lillet»; «Espunyola, l'» →
    «l'Espunyola» (an apostrophe article hugs the noun). Names without a
    suffixed article pass through untouched. Used for *prose only* — the data
    rows keep the mart's exact spelling, so the trace stays byte-faithful.
    """
    m = _INE_ARTICLE.match(name.strip())
    if not m:
        return name
    art, base = m.group("art"), m.group("base")
    return art + base if art.endswith("'") else f"{art} {base}"


def _muni_name_variants(name: str) -> set[str]:
    """Normalized search variants for a municipality name.

    Always the name as spelled; plus, for the register style with the article
    as a suffix, the natural form a question would use (see
    :func:`natural_muni_name`). Found via the /pregunta-li chips (B3): the real
    ``mart_municipi`` spells toponyms register-style, so every lookup for a
    municipality with an article refused («la Pobla de Lillet» — the demo
    municipality — was unrecognisable).
    """
    return {normalize(name), normalize(natural_muni_name(name))}


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

    def __init__(self, catalog: Catalog, warehouse: Warehouse,
                 politics_gate: PoliticsGate | None = None):
        self.catalog = catalog
        self.warehouse = warehouse
        # The political gate (see politics.py). Read from the env by default so
        # the secret is runtime-only; a gate with no word configured stays sealed
        # for every vote question (fail-safe). Injectable for deterministic tests.
        self.politics_gate = politics_gate or PoliticsGate.from_env()
        # Precompute the municipality directory from the marts so we can resolve
        # toponyms. Falls back gracefully if a mart lacks `municipi`.
        self._muni_index = self._build_muni_index()
        # Whether a mart carries a `date` column (monthly series), lazily probed.
        self._table_has_date: dict[str, bool] = {}

    # ------------------------------------------------------------------ setup
    def _build_muni_index(self) -> dict[str, dict[str, str]]:
        """Per-table map of normalized name variant -> canonical name.

        Keyed by table because the marts do not agree on spelling: the real
        ``mart_municipi``/``mart_electoral`` use the register style («Pobla de
        Lillet, la») while ``mart_pols_mensual`` uses the natural form («la
        Pobla de Lillet»). A lookup must bind ``$muni`` to the name *as spelled
        in the table it queries*, so each table resolves its own canonical.
        """
        index: dict[str, dict[str, str]] = {}
        for table in self.catalog.tables():
            try:
                rows = self.warehouse.query(
                    f'SELECT DISTINCT municipi FROM "{table}" '
                    "WHERE municipi IS NOT NULL"
                )
            except WarehouseError:
                continue
            per_table = index.setdefault(table, {})
            for row in rows:
                name = row["municipi"]
                for variant in _muni_name_variants(name):
                    per_table[variant] = name
        return index

    def _muni_variants_for(self, table: str | None) -> dict[str, str]:
        """The variant->canonical view to match against.

        For a known table, its own directory; otherwise the union of every
        table (ranking/correlation and the unknown-place heuristic do not care
        which spelling wins, only whether the toponym is known).
        """
        if table is not None and table in self._muni_index:
            return self._muni_index[table]
        merged: dict[str, str] = {}
        for per_table in self._muni_index.values():
            merged.update(per_table)
        return merged

    # -------------------------------------------------------------- matching
    @staticmethod
    def _is_eligible(metric: Metric, include_keyed: bool) -> bool:
        """Whether ``metric`` may be resolved by the matcher on this call.

        Normally: only what the agent advertises (:meth:`Metric.is_available`).
        With ``include_keyed`` — set when the political gate has been opened by
        the runtime secret — a held-back-but-keyed metric becomes resolvable
        too, provided it is actually computed. Without this, unlocking would
        stop working the moment ``politica`` became a held-back dimension: the
        matcher would never surface the metric for the gate to let through.
        """
        if metric.is_available():
            return True
        return (
            include_keyed
            and metric.is_held_back
            and metric.is_keyed
            and metric.is_computed()
        )

    def match_metric(self, question_norm: str, locale: str,
                     exclude: Metric | None = None,
                     include_keyed: bool = False) -> Metric | None:
        """Best catalog metric whose label/synonym appears in the question.

        Longest match wins (most specific phrase). Only *available* metrics are
        eligible here (plus keyed ones when ``include_keyed``); ``planned`` and
        held-back metrics are matched separately so we can give a precise
        refusal instead of a bare "out of catalog".
        """
        best: tuple[int, Metric] | None = None
        for metric in self.catalog.metrics.values():
            if not self._is_eligible(metric, include_keyed):
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
        self, question_norm: str, locale: str, include_keyed: bool = False
    ) -> list[tuple[int, int, Metric]]:
        """Available metrics that match, as ``(position, -length, metric)``.

        Sorted by *earliest appearance* in the question (then longest match).
        Used for correlation, where word order disambiguates which metric is
        the primary one (``entre l'índex i els residus`` -> índex first).
        """
        found: list[tuple[int, int, Metric]] = []
        for metric in self.catalog.metrics.values():
            if not self._is_eligible(metric, include_keyed):
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

    def match_municipality(self, question_norm: str,
                           table: str | None = None) -> str | None:
        """Resolve a municipality name mentioned in the question.

        ``table`` scopes the resolution to the mart the intent will query, so
        the canonical returned is spelled the way *that* table spells it (the
        marts disagree on article placement; see :meth:`_build_muni_index`).
        """
        best: str | None = None
        best_len = 0
        for norm_name, canonical in self._muni_variants_for(table).items():
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
        known = self._muni_variants_for(None)
        tokens = re.findall(r"[A-ZÀ-Ý][\wÀ-ÿ'·]+", question)
        for i, tok in enumerate(tokens):
            if i == 0:  # sentence-initial capital carries no signal
                continue
            if tok.lower() in stop:
                continue
            if normalize(tok) in known:
                return False  # it's a known municipality -> not "unknown"
            # A multi-word toponym (e.g. "Castellar de n'Hug") is matched by
            # match_municipality already; here a lone unknown capital suffices.
            return True
        return False

    # ---------------------------------------------------------------- parse
    def parse(self, question: str, locale: str,
              unlocked: bool = False) -> Intent | RefusalReason:
        """Turn a question into an :class:`Intent`, or a refusal reason.

        ``unlocked`` carries the political gate's decision (see
        :meth:`ask`). It widens the matcher to keyed metrics so an unlocked vote
        question can still resolve; it changes nothing else.
        """
        qn = normalize(question)

        corr_cues = _CORR_CUES.get(locale, _CORR_CUES["ca"])
        list_cues = _LIST_CUES.get(locale, _LIST_CUES["ca"])
        max_cues = _RANK_MAX_CUES.get(locale, _RANK_MAX_CUES["ca"])
        min_cues = _RANK_MIN_CUES.get(locale, _RANK_MIN_CUES["ca"])

        # --- correlation: two distinct metrics + a relationship cue ---
        if self._has_cue(qn, corr_cues):
            ordered = self._matched_metrics_by_position(qn, locale, unlocked)
            if len(ordered) >= 2:
                # Primary = first to appear in the question; secondary = next.
                m1 = ordered[0][2]
                m2 = ordered[1][2]
                return Intent(kind="correlation", metric=m1, metric_b=m2)

        # --- otherwise we need one primary metric ---
        metric = self.match_metric(qn, locale, include_keyed=unlocked)
        if metric is None:
            # Did it match a planned/held-back metric? Give a precise refusal.
            any_metric = self._match_any_metric(qn, locale)
            if any_metric is not None and not any_metric.is_available():
                # A vote metric must get the DISCREET political refusal, never
                # the "planned" one, which would name it. This path is how the
                # gate used to be walked around: `pct_extrema_dreta` is
                # `status: planned`, so it never reached the gate in
                # `execute_intent` (that only fires on a *resolved* metric) and
                # the refusal answered «la mètrica "% vot extrema dreta" ...
                # encara no està calculada» — naming the metric *and* promising
                # it was coming. Reachable from the contract's own seed question
                # («On creix més l'extrema dreta?»). Same path now covers the
                # other three, which are held back rather than planned.
                if is_political_metric(any_metric):
                    return RefusalReason.POLITICAL_GATED
                return self._unserved_reason(any_metric)
            return RefusalReason.OUT_OF_CATALOG

        # --- ranking vs lookup ---
        # Resolve the toponym against the mart this metric lives in, so the
        # canonical name is spelled the way that table spells it.
        muni = self.match_municipality(qn, metric.table)
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

    @staticmethod
    def _unserved_reason(metric: Metric) -> RefusalReason:
        """Why an unavailable metric is not served — accurately.

        ``deprecated`` is not ``planned``. Telling a reader that a retired
        metric is "not yet calculated" promises it is on its way, when the
        decision was precisely that it is not (``index_turisme``, Bea's vote of
        2026-07-18).
        """
        if metric.status == "deprecated":
            return RefusalReason.METRIC_DEPRECATED
        return RefusalReason.METRIC_PLANNED

    def _availability_guard(self, metric: Metric) -> RefusalReason | None:
        """Refusal reason if a metric must not be queried, else None."""
        if not metric.is_available():
            return self._unserved_reason(metric)
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
        # Political gate (resolution layer): if the secret word is present we
        # open the gate AND strip the word *before* routing, so it can never
        # pollute keyword matching nor echo back. The cleaned question is what we
        # parse, display and pass downstream.
        unlocked = self.politics_gate.is_unlocked(question)
        if unlocked:
            question = self.politics_gate.strip_unlock(question)
        parsed = self.parse(question, loc, unlocked=unlocked)
        if isinstance(parsed, RefusalReason):
            return self._refuse(question, loc, parsed, backend)
        return self.execute_intent(question, loc, parsed, backend, unlocked=unlocked)

    def execute_intent(self, question: str, locale: str, intent: Intent,
                       backend: str, unlocked: bool | None = None) -> Answer:
        """Execute a (trusted, already-validated) intent under the guardrails.

        Shared by the offline router and the OpenRouter backend. Re-checks
        metric availability defensively, applies the political gate, then runs
        the parametrized read-only SQL. Any guardrail violation surfaces as a
        reasoned refusal, never an exception to the caller.

        ``unlocked`` carries the political-gate decision from the entrypoint
        (which saw the raw question before the secret word was stripped). When
        ``None`` (a direct caller that did not pre-compute it) we evaluate it
        from ``question`` here, so the gate holds for every path into the
        executor — including the OpenRouter backend.
        """
        loc = self.catalog.resolve_locale(locale)
        if unlocked is None:
            unlocked = self.politics_gate.is_unlocked(question)
        # Political gate: a resolved vote-orientation metric (dimension: politica)
        # is refused, neutrally and discreetly, unless the gate was unlocked.
        if not unlocked:
            for m in (intent.metric, intent.metric_b):
                if is_political_metric(m):
                    return self._refuse(
                        question, loc, RefusalReason.POLITICAL_GATED, backend)
        # Defensive availability re-check (the LLM path could pass anything).
        for m in (intent.metric, intent.metric_b):
            if m is None:
                continue
            if unlocked and is_political_metric(m):
                # The gate above already let this through. Hold-back does not
                # apply to an unlocked call, but "computed" still does: an
                # unlocked `pct_extrema_dreta` has no data to serve, and must
                # refuse discreetly rather than name itself.
                if not m.is_computed():
                    return self._refuse(question, loc,
                                        RefusalReason.POLITICAL_GATED, backend)
                continue
            if not m.is_available():
                return self._refuse(question, loc, self._unserved_reason(m),
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
    def _has_date_column(self, table: str) -> bool:
        """True when ``table`` is a dated (monthly) mart. Probed once, cached."""
        cached = self._table_has_date.get(table)
        if cached is None:
            try:
                cached = "date" in self.warehouse.columns(table)
            except WarehouseError:
                cached = False
            self._table_has_date[table] = cached
        return cached

    def _latest_filter(self, table: str, alias: str = "") -> str:
        """``AND``-predicate pinning a monthly mart to its latest month, or ``""``.

        ``mart_pols_mensual`` is a long series (one row per municipality and
        month, 2006→today). A naive lookup used to grab whichever row came
        first, silently serving a 2006 unemployment figure as current — found
        while proving the /pregunta-li example chips resolve (B3). Any mart
        with a ``date`` column is pinned to ``MAX(date)``: the latest loaded
        month, which is what the contract's ``date:`` field documents.
        """
        if not self._has_date_column(table):
            return ""
        col = f'{alias}."date"' if alias else '"date"'
        return f' AND {col} = (SELECT MAX("date") FROM "{table}")'

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
            f"{self._latest_filter(metric.table)}"
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
            municipi=natural_muni_name(rows[0]["municipi"]),
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
        # Fetch one row past what we render: naming a single winner is only
        # honest if we have looked at the runner-up (see the tie guard below).
        sql = (
            f'SELECT municipi, "{col}" AS value '
            f'FROM "{metric.table}" WHERE "{col}" IS NOT NULL'
            f"{self._latest_filter(metric.table)} "
            f'ORDER BY "{col}" {order} LIMIT {limit}'
        )
        rows = self.warehouse.query(sql)
        if not rows:
            return self._refuse(question, locale,
                                RefusalReason.UNSUPPORTED_QUESTION, backend)
        prov = self._provenance(metric, locale, sql, {})
        unit = self._unit_suffix(metric, locale)
        if not intent.want_list:
            tie = self._tie_at_top(metric, col, order)
            if len(tie) > 1:
                # The doctrine's `empat`, at the deterministic layer (X1 / C5).
                # `LIMIT 1` picks one row out of a shared top by accident of row
                # order; the data does not single it out, so we do not either.
                # Live on the real mart: 47 municipalities share
                # `index_turisme = 100`, 6 share `IETR = 100` (capped indices).
                text = t(
                    locale, "ranking_tie",
                    sup=t(locale, "superlative_max" if intent.descending
                          else "superlative_min"),
                    label=metric.label(locale),
                    n=len(tie),
                    value=format_number(rows[0]["value"], locale),
                    unit=unit,
                    municipis=", ".join(natural_muni_name(m) for m in tie[:5])
                    + ("…" if len(tie) > 5 else ""),
                )
                text = self._with_provenance_and_note(text, prov, locale)
                return Answer(
                    kind=AnswerKind.ANSWER, locale=locale, question=question,
                    backend=backend, text=text, data=rows, provenance=prov,
                    metric_key=metric.key,
                )
        if intent.want_list:
            lines = [t(locale, "ranking_list_intro", label=metric.label(locale))]
            for i, r in enumerate(rows, 1):
                lines.append(t(
                    locale, "ranking_row", rank=i,
                    municipi=natural_muni_name(r["municipi"]),
                    value=format_number(r["value"], locale), unit=unit,
                ))
            text = "\n".join(lines)
        else:
            sup = t(locale, "superlative_max" if intent.descending else "superlative_min")
            text = t(
                locale, "ranking_top", sup=sup, label=metric.label(locale),
                municipi=natural_muni_name(rows[0]["municipi"]),
                value=format_number(rows[0]["value"], locale), unit=unit,
            )
        text = self._with_provenance_and_note(text, prov, locale)
        return Answer(
            kind=AnswerKind.ANSWER, locale=locale, question=question,
            backend=backend, text=text, data=rows, provenance=prov,
            metric_key=metric.key,
        )

    def _tie_at_top(self, metric: Metric, col: str, order: str) -> list[str]:
        """Municipalities sharing the leading value (>1 name means: do not order).

        The marts store a point value per cell and no interval, so the only
        separation their own cells can *prove* is that the leader is strictly
        alone. This is the harvested band rule, honestly reduced — see
        :func:`datapoble_ai.doctrine.distinguishable`.
        """
        anchor = self._latest_filter(metric.table)
        top_sql = (
            f'SELECT municipi FROM "{metric.table}" '
            f'WHERE "{col}" = (SELECT {"MAX" if order == "DESC" else "MIN"}("{col}") '
            f'FROM "{metric.table}" WHERE "{col}" IS NOT NULL{anchor})'
            f"{anchor} "
            f'ORDER BY municipi'
        )
        try:
            return [r["municipi"] for r in self.warehouse.query(top_sql)
                    if r.get("municipi")]
        except WarehouseError:
            return []

    def _answer_correlation(self, question: str, locale: str, intent: Intent,
                            backend: str) -> Answer:
        a, b = intent.metric, intent.metric_b
        assert a is not None and b is not None
        # Both metrics must share a mart to be joined on ine5/municipi.
        # Dated (monthly) marts are pinned to their latest month on either side,
        # so a long series never fans out the join nor skews the correlation.
        if a.table != b.table:
            sql = (
                f'SELECT x.municipi AS municipi, x."{a.column}" AS a, '
                f'y."{b.column}" AS b '
                f'FROM "{a.table}" x JOIN "{b.table}" y USING (municipi) '
                f'WHERE x."{a.column}" IS NOT NULL AND y."{b.column}" IS NOT NULL'
                f"{self._latest_filter(a.table, 'x')}"
                f"{self._latest_filter(b.table, 'y')}"
            )
        else:
            sql = (
                f'SELECT municipi, "{a.column}" AS a, "{b.column}" AS b '
                f'FROM "{a.table}" '
                f'WHERE "{a.column}" IS NOT NULL AND "{b.column}" IS NOT NULL'
                f"{self._latest_filter(a.table)}"
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
            metric_key=a.key, metric_b_key=b.key,
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
            # Belt to the parse-level braces: whatever route reached here, a vote
            # metric is never named back to the reader. Downgrading to the
            # discreet copy is the safe direction — the reverse would leak.
            if is_political_metric(any_m):
                text = t(locale, "refusal_political_gated")
                reason = RefusalReason.POLITICAL_GATED
            else:
                text = t(locale, "refusal_planned",
                         label=any_m.label(locale) if any_m else (label or "?"))
        elif reason == RefusalReason.METRIC_DEPRECATED:
            any_m = self._match_any_metric(normalize(question), locale)
            text = t(locale, "refusal_deprecated",
                     label=any_m.label(locale) if any_m else (label or "?"))
        elif reason == RefusalReason.UNKNOWN_MUNICIPALITY:
            text = t(locale, "refusal_unknown_municipality", name=name or "?")
        elif reason == RefusalReason.GUARDRAIL_VIOLATION:
            text = t(locale, "refusal_guardrail", why=detail or "—")
        elif reason == RefusalReason.BUDGET_EXCEEDED:
            text = t(locale, "refusal_budget_exceeded")
        elif reason == RefusalReason.RATE_LIMITED:
            text = t(locale, "refusal_rate_limited")
        elif reason == RefusalReason.POLITICAL_GATED:
            # Deliberately neutral and discreet — no hint that an unlock exists.
            text = t(locale, "refusal_political_gated")
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
