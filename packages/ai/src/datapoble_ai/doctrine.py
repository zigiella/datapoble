"""The doctrine: what may be said about a mart cell, and how.

Harvested from the geo-rag experiment (task X1, contract C5) and **adapted to the
marts**. ``packages/geo-rag`` stays frozen as the research annex; from here on this
module is the canonical house of the doctrine, and the UI latch
(``packages/web/src/lib/contract/distinguish.ts``) is propagated *from* it.

What was harvested (the doctrine)
---------------------------------
- **The registers**: a figure is not just a number; it carries a status that
  governs how you may speak about it.
- **The two different silences** — the distinction the experiment paid for:
  ``soroll`` = "I have the estimate and I disown it, with a reason" is NOT the
  same as out-of-catalog = "I don't have it". Collapsing them is the failure the
  doctrine exists to prevent.
- **The tie rule**: values that the data does not separate must not be ordered.
- **The precedence** learned across the three frozen prompt versions: first the
  *kind of question* and the comparison verdict, then the register.

What changed (the referent) — and why it had to
-----------------------------------------------
The experiment's register was a property of the **municipality** (Idescat's
≥1.000 inhabitants ETCA coverage), read off a purpose-built substrate carrying
``estimacio`` / ``rang_baix`` / ``rang_alt`` / ``padro`` / ``etca_oficial`` /
``collision_group``. **The marts carry none of those fields.** Copying the
experiment's code would have meant asking the model about columns that do not
exist. So the register is re-pointed at what the marts and the semantic contract
*actually* declare, and it becomes a property of the **cell** (metric ×
municipality):

===========  ==========================================================
``oficial``  a measured figure (contract: no ``categoria: derived``)
``senyal``   an inference (contract: ``categoria: derived``)
``soroll``   an inference the mart's own ``confianca`` flag calls ``baixa``
===========  ==========================================================

``confianca`` is not an invention of this module: it is a contract metric
("bandera de fiabilitat de les estimacions"), and its own declared caveat states
the soroll doctrine outright — *"un buit honest val més que un fals precís:
'baixa' marca micromunicipis … i casos on els senyals divergeixen"*. The harvest
just gives that flag teeth.

What did NOT survive the harvest (declared, not hidden)
------------------------------------------------------
- **Bands** ("el rang és la dada"). The marts store a point value per cell and no
  interval, so a band rule here would be fabricated. :func:`distinguishable`
  therefore degrades to the **exact-tie** case — the one thing the mart's own
  cells can prove — and nothing more.
- **Collision groups** ("la xifra no és específica del municipi"). That is a
  property of the *estimator* repeating a figure across municipalities; the marts
  do not record it. Not modelled, not guessed. See ``bitacora/`` for the handoff.

The exact-tie rule is not theoretical: on the real ``mart_municipi`` today, 47
municipalities share ``index_turisme = 100`` and 6 share ``IETR = 100`` (capped
indices), so a ``LIMIT 1`` ranking names one of them as *the* top by accident of
row order. That is the ``empat_trencat`` the doctrine forbids.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import Catalog, Metric

# --- registers ----------------------------------------------------------------

#: A measured figure: the contract does not mark it as derived.
OFICIAL = "oficial"
#: An inference: the contract marks it ``categoria: derived``.
SENYAL = "senyal"
#: An inference the mart's ``confianca`` flag calls ``baixa`` — the estimate
#: exists and is disowned *with a reason*. The loud silence, not the empty one.
SOROLL = "soroll"

#: Contract marker for a computed/inferred metric.
DERIVED = "derived"
#: The dimension whose estimates the ``confianca`` flag actually grades. The flag
#: is defined as the reliability of "les estimacions de les 3 capes" (pressure);
#: applying it to, say, an electoral count would be borrowing authority it does
#: not have.
CONFIDENCE_DIMENSION = "pressio"
#: The mart column holding the flag, and the value that means "disown it".
CONFIDENCE_COLUMN = "confianca"
LOW_CONFIDENCE = "baixa"

# Inside the package, not beside it: the wheel ships ``src/datapoble_ai``, so a
# sibling `prompts/` would be missing wherever the API is actually installed.
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
REDACTOR_PROMPT_PATH = PROMPTS_DIR / "redactor-v1.md"
#: The blind validator, harvested **byte-for-byte** from the frozen instrument
#: (``packages/geo-rag/prompts/validador-cec-v2-CONGELAT.md``). C5 §2 pins v2 (the
#: unequal-comparison flaw corrected). The system prompt is never edited: when the
#: mart context differs, the *user* message adapts (see :func:`build_context`).
VALIDATOR_PROMPT_PATH = PROMPTS_DIR / "validador-cec-v2.md"


def load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def is_inference(metric: Metric | None) -> bool:
    """True iff the contract marks ``metric`` as computed rather than measured."""
    return metric is not None and metric.raw.get("categoria") == DERIVED


def takes_confidence_flag(metric: Metric | None) -> bool:
    """True iff the mart's ``confianca`` flag actually grades this metric."""
    return is_inference(metric) and metric is not None and \
        metric.dimension == CONFIDENCE_DIMENSION


def register_for(metric: Metric | None, confidence: str | None) -> str:
    """The register of a cell: ``oficial`` / ``senyal`` / ``soroll``.

    ``confidence`` is the municipality's ``confianca`` cell (or None when the mart
    does not carry it / the flag does not apply to this metric).
    """
    if not is_inference(metric):
        return OFICIAL
    if (
        takes_confidence_flag(metric)
        and isinstance(confidence, str)
        and confidence.strip().lower() == LOW_CONFIDENCE
    ):
        return SOROLL
    return SENYAL


def obligated_caveat(metric: Metric | None, locale: str) -> str | None:
    """The caveat the *contract* declares for this metric — never invented here.

    See :meth:`Metric.note`, which reads both ``nota:`` and ``caveat:`` (the
    contract uses both keys; only the first was being read before this harvest, so
    every inference metric was served with its caveat silently dropped).
    """
    if metric is None:
        return None
    return metric.note(locale)


# --- the tie rule -------------------------------------------------------------


def distinguishable(values: list[Any]) -> bool:
    """Can these cells be ordered? Only if the top value is not shared.

    **Reduced on purpose.** The experiment's rule was band overlap; the marts have
    no bands, so the only separation the data can *prove* is that the leading
    value is strictly alone. Two cells holding the same number are not ordered by
    this observatory — whichever one ``LIMIT 1`` happened to surface.

    ``True`` when there are at least two values and the first is strictly ahead of
    the second (the list arrives already ordered by the SQL). A single value is
    trivially distinguishable; an empty list is not.
    """
    clean = [v for v in values if v is not None]
    if not clean:
        return False
    if len(clean) == 1:
        return True
    return clean[0] != clean[1]


def tied_names(rows: list[dict], value_key: str = "value",
               name_key: str = "municipi") -> list[str]:
    """Names of the rows sharing the leading value (empty when none do)."""
    if not rows:
        return []
    top = rows[0].get(value_key)
    if top is None:
        return []
    return [r[name_key] for r in rows
            if r.get(value_key) == top and r.get(name_key)]


# --- the context the generative layer is allowed to see -----------------------


def build_context(catalog: Catalog, metric: Metric | None, locale: str,
                  rows: list[dict], intent_kind: str,
                  confidence_by_muni: dict[str, str] | None = None,
                  distinguishable_verdict: bool | None = None,
                  winner: str | None = None) -> dict:
    """The CONTEXT block: mart cells only, plus the verdicts we computed.

    Mirrors the experiment's ``build_context`` in spirit — the deterministic
    prose is **discarded**; the model sees fields, never our own sentences — and
    carries the fields the frozen validator prompt keys off (``registre``,
    ``distinguishable``, ``winner``, ``caveat_obligat``), so that prompt needs no
    edit to judge mart data.
    """
    conf = confidence_by_muni or {}
    cells = []
    for r in rows:
        muni = r.get("municipi")
        cell: dict[str, Any] = {"municipi": muni}
        for k, v in r.items():
            if k != "municipi":
                cell[k] = v
        cell["registre"] = register_for(metric, conf.get(muni) if muni else None)
        cells.append(cell)

    ctx: dict[str, Any] = {"intent": intent_kind}
    if metric is not None:
        ctx["metrica"] = {
            "clau": metric.key,
            "etiqueta": metric.label(locale),
            "unitat": metric.unit(locale),
        }
        caveat = obligated_caveat(metric, locale)
        if caveat:
            ctx["caveat_obligat"] = caveat
    if not cells:
        ctx["not_found"] = True
        return ctx
    ctx["cel·les"] = cells
    if distinguishable_verdict is not None:
        ctx["distinguishable"] = distinguishable_verdict
        ctx["winner"] = winner
    return ctx
