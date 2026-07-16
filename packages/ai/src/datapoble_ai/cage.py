"""The cage: nothing generative is served unless it has been *checked*.

Harvested from the geo-rag experiment (task X1, contract C5). Two layers, in order:

1. **Hard validation** (deterministic, no LLM): every number in the prose must
   trace to a cell of the context. Untraceable figures are cut, visibly.
2. **The blind validator** (a second model, isolated call): sees only the
   question, the data and the final text — *never* the generator's reasoning — and
   judges the text against the doctrine.

The law of this module (C5 §2)
------------------------------
The re-validation annex of the experiment (#238) proved that **counting
interventions overstates the fix**: the cage scored 170/170 by accounting, but
only 163/170 when the *actual caged text* was fed back to the blind validator. So
here an intervention is never *considered* fixed — it is **re-checked**:

    deterministic answer -> generative prose -> cage -> RE-VALIDATE the caged text
                                                            |
                                              fails? -> deterministic fallback

The generative layer is a conditional embellishment, never a risk. If the cage
cannot certify the final text — or the budget is out, or the validator is
unreachable — the traceable deterministic answer is what gets served.

Adaptation to the marts (the honest part)
-----------------------------------------
The experiment's substrate held integers (people). The marts hold **floats**
(percentages, ratios, indices) rendered in ca/es convention (``1.234,56``). Ported
naively, ``74,28`` would read as the two integers 74 and 28 and the cage would cut
its own correct figure. So the number grammar here parses ca/es decimals, and a
figure is allowed when it matches a cell value at the precision it is written to.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

# --- number grammar (ca/es: 1.234,56) ----------------------------------------

# Order matters: the fullest shape first, so a thousands group is never re-read
# as a bare integer. Anchored on digit boundaries to avoid eating parts of words.
_NUM_RE = re.compile(
    r"(?<![\w,.])"
    r"\d{1,3}(?:\.\d{3})+(?:,\d+)?"   # 1.234  /  1.234,56
    r"|\d+,\d+"                        # 74,28
    r"|\d+"                            # 852
    r"(?![\w])"
)


def _parse(token: str) -> float:
    """``'1.234,56'`` -> ``1234.56``; ``'74,28'`` -> ``74.28``; ``'852'`` -> ``852.0``."""
    return float(token.replace(".", "").replace(",", "."))


def _decimals(token: str) -> int:
    """How many decimal places the figure is *written* to."""
    _, _, frac = token.partition(",")
    return len(frac)


def number_spans(text: str) -> list[tuple[int, int, float, str]]:
    """``(start, end, value, token)`` for every figure in ``text``."""
    return [(m.start(), m.end(), _parse(m.group(0)), m.group(0))
            for m in _NUM_RE.finditer(text or "")]


def cell_values(context: dict) -> list[float]:
    """Every numeric value reachable in the context, plus list counts.

    Mirrors the experiment's ``allowed_numbers`` walk: numeric fields *and* the
    length of each list (so "els 3 municipis" traces to the rows we handed over).
    Booleans are skipped — ``True`` is an ``int`` in Python but is not a figure.
    """
    out: list[float] = []

    def walk(x: Any) -> None:
        if isinstance(x, bool):
            return
        if isinstance(x, int | float):
            out.append(float(x))
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            out.append(float(len(x)))
            for v in x:
                walk(v)

    walk(context)
    return out


def _traces(value: float, token: str, allowed: list[float]) -> bool:
    """Does ``value`` trace to a cell, at the precision it is written to?

    A cell of ``74.28`` justifies ``74,28``, ``74,3`` and ``74`` — the same figure
    rounded — but not ``75``. Integer cells match exactly.
    """
    places = _decimals(token)
    for cell in allowed:
        if round(cell, places) == value or float(round(cell)) == value:
            return True
    return False


def hard_validation(prose: str, context: dict) -> list[str]:
    """The tokens in ``prose`` that trace to no cell (ordered, unique)."""
    allowed = cell_values(context)
    bad: list[str] = []
    for _, _, value, token in number_spans(prose):
        if not _traces(value, token, allowed) and token not in bad:
            bad.append(token)
    return bad


# --- the blind validator's verdict -------------------------------------------

#: The only labels the frozen v2 prompt may return.
TAXONOMY = (
    "xifra_inventada", "agregat_estimat", "caveat_esborrat",
    "to_ferm_sobre_soroll", "empat_trencat", "collisio_amagada",
)

#: Problems the cage knows how to repair with a deterministic postscript built
#: only from context fields. ``collisio_amagada`` is deliberately absent: the
#: marts carry no collision groups (see :mod:`datapoble_ai.doctrine`), so there is
#: nothing truthful to append — if it ever fires, the text is not repairable and
#: the fallback takes over. ``xifra_inventada`` is handled by cutting, above.
CAVEAT_FIXABLE = frozenset({"caveat_esborrat", "to_ferm_sobre_soroll", "empat_trencat"})


def parse_verdict(raw: str) -> dict:
    """``{compleix, problemes, motiu}``; unreadable output fails closed."""
    t = (raw or "").strip()
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        try:
            d = json.loads(t[start:end + 1])
            if isinstance(d, dict) and "compleix" in d:
                problemes = d.get("problemes")
                return {
                    "compleix": bool(d.get("compleix")),
                    "problemes": [str(p) for p in problemes]
                    if isinstance(problemes, list) else [],
                    "motiu": str(d.get("motiu", "")),
                }
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return {"compleix": False, "problemes": ["validador_illegible"],
            "motiu": t[:200]}


def parse_output(raw: str) -> tuple[str, str]:
    """``(accio, prose)`` from the redactor's output; ``accio`` may be
    ``respondre`` / ``abstenir`` / ``error_format``."""
    lines = (raw or "").strip().splitlines()
    i = 0
    while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith("```")):
        i += 1
    if i < len(lines):
        m = re.match(r"^[\s>#*_`]*ACCI[OÓ]\s*:\s*(RESPONDRE|ABSTENIR)[\s*_`.!]*$",
                     lines[i].strip(), re.IGNORECASE)
        if m:
            prose = "\n".join(ln for ln in lines[i + 1:] if ln.strip() != "```")
            return m.group(1).lower(), prose.strip()
    return "error_format", (raw or "").strip()


# --- the cage ----------------------------------------------------------------


def _postscript(tag: str, context: dict) -> str | None:
    """A deterministic repair, built **only** from context fields.

    Never from the generator's words: a caged text must not launder the model's
    prose into an apparent caveat.
    """
    if tag == "empat_trencat":
        cells = context.get("cel·les") or []
        top = [c.get("municipi") for c in cells if c.get("municipi")]
        if len(top) > 1:
            return (f"(Gàbia: {len(top)} municipis comparteixen aquest valor; "
                    f"no es poden ordenar.)")
        return "(Gàbia: els valors són iguals; no es poden ordenar.)"

    if tag == "to_ferm_sobre_soroll":
        return ("(Gàbia: el mart marca aquesta estimació amb confiança baixa "
                "(municipi molt petit o senyals divergents); la xifra no s'afirma "
                "com a fet.)")

    if tag == "caveat_esborrat":
        caveat = context.get("caveat_obligat")
        if caveat:
            return f"(Gàbia: {caveat})"
        return None
    return None


def apply_cage(prose: str, context: dict, violations: list[str],
               problemes: list[str]) -> tuple[str, list[str]]:
    """Cut untraceable figures, append deterministic caveats.

    Returns ``(caged_text, interventions)``. Interventions are counted separately:
    the cage is never the generator's merit.
    """
    interventions: list[str] = []
    bad = set(violations)
    pieces: list[str] = []
    last = 0
    for start, end, _value, token in number_spans(prose):
        if token in bad:
            pieces.append(prose[last:start])
            pieces.append(f"⟦{token}: xifra no verificada⟧")
            interventions.append(f"xifra_tallada({token})")
            last = end
    pieces.append(prose[last:])
    caged = "".join(pieces)

    for tag in problemes:
        if tag in CAVEAT_FIXABLE:
            post = _postscript(tag, context)
            if post:
                caged = (caged.rstrip() + " " + post).strip()
                interventions.append(f"postdata({tag})")
    return caged, interventions


# --- the validator's transport ------------------------------------------------


class ValidatorBackend(Protocol):
    """One isolated completion call. The cage never talks to an SDK directly."""

    def complete(self, *, system: str, user: str, max_tokens: int) -> str: ...


def validator_message(question: str, context: dict, text: str) -> str:
    """The user message for the blind validator.

    The frozen v2 system prompt is **never edited** (C5 §2); when the mart context
    differs from the experiment's substrate, *this* is what adapts. The prompt is
    written to obey the data ("el veredicte de comparació és de les DADES, no
    teu"), so supplying ``registre`` / ``distinguishable`` / ``caveat_obligat``
    here is enough to make it judge mart cells correctly.
    """
    return (
        f"PREGUNTA: {question}\n"
        f"DADES: {json.dumps(context, ensure_ascii=False, separators=(',', ':'))}\n"
        f"RESPOSTA: {text}"
    )


@dataclass
class CageResult:
    """What the cage did, and whether the text may be served."""

    served: bool
    text: str | None = None
    status: str = ""
    interventions: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    verdict: dict | None = None
    revalidated: dict | None = None

    def to_dict(self) -> dict:
        return {
            "served": self.served,
            "status": self.status,
            "interventions": list(self.interventions),
            "violations": list(self.violations),
            "verdict": self.verdict,
            "revalidated": self.revalidated,
        }


MAX_TOKENS_VALIDATOR = 300


class Cage:
    """Hard validation + blind validator + **re-validation of the final text**."""

    def __init__(self, validator_prompt: str, backend: ValidatorBackend):
        self.validator_prompt = validator_prompt
        self.backend = backend

    def _judge(self, question: str, context: dict, text: str) -> dict:
        raw = self.backend.complete(
            system=self.validator_prompt,
            user=validator_message(question, context, text),
            max_tokens=MAX_TOKENS_VALIDATOR,
        )
        return parse_verdict(raw)

    def run(self, question: str, context: dict, prose: str) -> CageResult:
        """Cage ``prose`` and certify the result, or refuse to serve it.

        The C5 §2 sequence, with no shortcut: hard-validate, judge, cage, then
        **judge the caged text again**. Only a text that passes *that* second,
        blind reading is served.
        """
        violations = hard_validation(prose, context)
        verdict = self._judge(question, context, prose)
        caged, interventions = apply_cage(
            prose, context, violations, verdict["problemes"])

        if not interventions and verdict["compleix"]:
            # Nothing was touched and the blind reading passed: the text the
            # validator approved is the text we serve. No second call needed.
            return CageResult(served=True, text=caged, status="clean",
                              interventions=interventions, violations=violations,
                              verdict=verdict, revalidated=verdict)

        # The annex's lesson: an intervention is not a fix until it is checked.
        revalidated = self._judge(question, context, caged)
        if revalidated["compleix"]:
            return CageResult(served=True, text=caged, status="caged_revalidated",
                              interventions=interventions, violations=violations,
                              verdict=verdict, revalidated=revalidated)
        return CageResult(served=False, text=None,
                          status="fallback_revalidation_failed",
                          interventions=interventions, violations=violations,
                          verdict=verdict, revalidated=revalidated)
