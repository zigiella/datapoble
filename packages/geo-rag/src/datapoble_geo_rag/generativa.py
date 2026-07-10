"""Capa generativa · arnès de passades múltiples — TORCH-FREE, openai LAZY.

Contractes vinculants:
- docs/experiment-rag-geo/08-contracte-capa-generativa.md — arquitectura generador →
  validació dura → validació cega; taxonomia d'errors; les intervencions NO són mèrit.
- docs/experiment-rag-geo/10-generativa-protocol-i-nivells.md — N=5; generador amb el
  mostreig PER DEFECTE (cap `temperature`); validador cec a temperature=0; definició de
  trial-correcte; nu i gàbia es puntuen sobre els MATEIXOS outputs.
- docs/experiment-rag-geo/11-generativa-spec-infra.md — accés VIA OPENROUTER (SDK openai,
  base_url https://openrouter.ai/api/v1, clau OPENROUTER_API_KEY), slugs
  anthropic/claude-sonnet-5 (generador) i anthropic/claude-haiku-4.5 (validador),
  proveïdor FIXAT a Anthropic (allow_fallbacks=false), provenance per crida (id + model +
  proveïdor servit).

HONESTEDAT DE L'ARNÈS:
- El generador MAI veu la prosa determinista del router: build_context() crida
  router.route() i DESCARTA out["text"] — només passen els CAMPS (dades crues).
- La validació dura és codi determinista (cap LLM): tota xifra de la prosa ha de traçar
  al context (o ser-ne l'arrodoniment a enter, o un recompte de llista, o el llindar
  doctrinal 1000 de «≥1.000 hab»). El que no traça es talla i es marca.
- El validador cec és una crida AÏLLADA (model diferent, cap conversa compartida): rep
  NOMÉS {pregunta, dades, resposta final}, mai el raonament ni el prompt del generador.
- La gàbia és comptabilitat determinista sobre el MATEIX output: cada intervenció es
  compta a part (la gàbia no és mèrit del generador). Els errors d'acció NO són
  arreglables per la gàbia.
- MODE OFICIAL: es nega a córrer si el fitxer del prompt no porta «CONGELAT» al nom
  (contracte 08: retocar el prompt després de veure el banc és entrenar contra el test).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from .build import build
from .descriptions import _collision_groups, _denom, _i, join_noms
from .router import route

# --- Rutes del paquet (mai rutes locals absolutes en res versionat) -------------------

_PKG_ROOT = Path(__file__).resolve().parents[2]  # packages/geo-rag
PROMPT_GENERADOR_PATH = _PKG_ROOT / "prompts" / "generador-v3-CONGELAT.md"
PROMPT_VALIDADOR_PATH = _PKG_ROOT / "prompts" / "validador-cec-v1-CONGELAT.md"
DEVSET_PATH = _PKG_ROOT / "data" / "generativa-devset.json"
BANC_PATH = _PKG_ROOT / "data" / "fase3-banc.json"
LOGS_DIR = _PKG_ROOT / "data" / "generativa-logs"
ENV_PATH = _PKG_ROOT / ".env"

# --- Infra (spec 11, congelada) --------------------------------------------------------

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_GENERADOR = "anthropic/claude-sonnet-5"
MODEL_VALIDADOR = "anthropic/claude-haiku-4.5"
# Proveïdor fixat: OpenRouter també serveix aquests models via Vertex/Bedrock i
# l'experiment ha de mesurar UN sol camí de servei.
PROVIDER_PIN = {"provider": {"order": ["anthropic"], "allow_fallbacks": False}}
# v0.1: 500 ofegava el raonament adaptatiu per defecte de Sonnet 5 (finish=length,
# content=null al dev D4). El raonament per defecte és part del comportament que
# mesurem; li donem sostre perquè la resposta arribi.
MAX_TOKENS_GENERADOR = 1200
MAX_TOKENS_VALIDADOR = 300

# Preus $/MTok (in, out) — spec 11 (intro de Sonnet 5 fins 31-08-2026).
# TODO(2026-09-01): el preu intro de Sonnet 5 CADUCA el 2026-08-31 (passa a $3/$15);
# després d'aquesta data el cost estimat de les actes serà FALS si no s'actualitza.
PRICES = {MODEL_GENERADOR: (2.0, 10.0), MODEL_VALIDADOR: (1.0, 5.0)}

# Vocabulari de doctrina: el llindar del registre («≥1.000 hab») és definició, no dada,
# i la cardinalitat del substrat («els 31 municipis del Berguedà») és un fet del sistema
# verificable, no una xifra de resposta (dev D9).
REGISTER_THRESHOLD = 1000
SUBSTRATE_SIZE = 31

# Taxonomia del contracte 08 (les úniques etiquetes admeses).
TAXONOMIA = (
    "xifra_inventada", "agregat_estimat", "caveat_esborrat",
    "to_ferm_sobre_soroll", "empat_trencat", "collisio_amagada",
)
# Problemes del validador que la gàbia SAP arreglar amb una postdata determinista.
CAVEAT_FIXABLE = frozenset(
    {"caveat_esborrat", "to_ferm_sobre_soroll", "collisio_amagada", "empat_trencat"}
)


# --- Clau i client (openai importat LAZY: el paquet importa net sense l'extra) ---------


def _load_api_key() -> str:
    """OPENROUTER_API_KEY de l'entorn, o del .env local (KEY=VALUE, gitignorat)."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key and ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == "OPENROUTER_API_KEY":
                key = v.strip().strip("'\"")
    if not key:
        raise RuntimeError(
            "Falta OPENROUTER_API_KEY: exporta-la a l'entorn o posa-la a "
            "packages/geo-rag/.env (gitignorat; vegeu .env.example). "
            "La clau MAI entra al repo públic."
        )
    return key


def make_client():
    """Client OpenRouter. L'import d'openai és aquí dins (extra opcional [generativa])."""
    from openai import OpenAI  # import LAZY (spec: el paquet base no depèn d'openai)

    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=_load_api_key())


# --- Constructor de context (determinista, del sistema EXISTENT) -----------------------


_MUNI_COLS = ("nom", "register", "estimacio", "rang_baix", "rang_alt", "padro", "etca_oficial")


def _muni_fields(conn: duckdb.DuckDBPyConnection, ine5: str) -> dict | None:
    row = conn.execute(
        f"SELECT {', '.join(_MUNI_COLS)} FROM municipi WHERE ine5 = ?", [ine5]
    ).fetchone()
    if row is None:
        return None
    d = dict(zip(_MUNI_COLS, row, strict=True))
    d["nom"] = _denom(d["nom"])  # «Pobla de Lillet, la» → «la Pobla de Lillet»
    return d


def _collision_members(members: list[str]) -> list[dict]:
    """Membres d'un grup de col·lisió des de la font Catalunya-wide (poden ser FORA dels
    31: p. ex. Salomó, 43135, al grup de Montmajor) — nom + estimació + ETCA oficial."""
    _, allm = _collision_groups()
    out = []
    for m in sorted(members):
        v = allm.get(m)
        if v is None:
            continue
        out.append(
            {
                "nom": _denom(v["nom"]),
                "estimacio": v["estimacio"],
                "etca_oficial": v.get("etca_oficial"),
            }
        )
    return out


def build_context(conn: duckdb.DuckDBPyConnection, query: str) -> dict:
    """Context CRU per al generador, construït del sistema existent (router + substrat).

    Crida router.route() i en DESCARTA el «text» (la resposta determinista en prosa):
    el generador només rep camps — files de municipi, membres de col·lisió, meta de
    distingibilitat, llistes de noms. Sempre inclou «intent».
    """
    out = route(conn, query)
    intent = out["intent"]
    meta = out.get("meta", {})
    munis = out.get("munis", [])
    # out["text"] es descarta aquí, deliberadament: mai arriba al generador.

    ctx: dict = {"intent": intent}

    if intent == "valor_municipi":
        m = _muni_fields(conn, munis[0]) if munis else None
        if m is None:
            ctx["not_found"] = intent
            return ctx
        ctx["municipi"] = m
        group = meta.get("collision_group")
        if group:
            ctx["collision_group"] = _collision_members(list(group))
        return ctx

    if intent == "comparacio":
        rows = [_muni_fields(conn, i) for i in munis]
        ctx["municipis"] = [r for r in rows if r is not None]
        ctx["distinguishable"] = meta.get("distinguishable")
        winner = meta.get("winner")
        if winner:
            w = _muni_fields(conn, winner)
            ctx["winner"] = w["nom"] if w else None
        else:
            ctx["winner"] = None
        if meta.get("collision") and munis:
            by_ine, _ = _collision_groups()
            members = by_ine.get(munis[0])
            if members:
                ctx["collision_group"] = _collision_members(list(members))
        return ctx

    if intent == "veins":
        noms = dict(conn.execute("SELECT ine5, nom FROM municipi").fetchall())
        anchor = _denom(noms.get(munis[0], munis[0])) if munis else None
        ctx["municipi"] = anchor
        ine5_list = meta.get("ine5_list")
        ctx["veins"] = (
            [_denom(noms[i]) for i in ine5_list if i in noms] if ine5_list is not None else None
        )
        return ctx

    if intent == "cataleg_registre":
        noms = dict(conn.execute("SELECT ine5, nom FROM municipi").fetchall())
        ine5_list = meta.get("ine5_list") or []
        ctx["register"] = meta.get("register")
        ctx["municipis"] = [_denom(noms[i]) for i in ine5_list if i in noms]
        ctx["count"] = len(ctx["municipis"])
        return ctx

    # municipi_desconegut / indicador_desconegut / consulta_no_reconeguda → fora de catàleg.
    ctx["not_found"] = intent
    return ctx


def user_message(query: str, context: dict) -> str:
    """Missatge d'usuari del generador: pregunta + context com a JSON compacte."""
    return (
        f"PREGUNTA: {query}\n"
        f"CONTEXT: {json.dumps(context, ensure_ascii=False, separators=(',', ':'))}"
    )


# --- Parsing de la sortida del generador ------------------------------------------------

# «ACCIO: RESPONDRE|ABSTENIR» amb variants de caixa/espais/accent (ACCIÓ) i decoració
# markdown lleu (**…**, `…`). Tag absent o malformat → acció 'error_format'.
_TAG_RE = re.compile(
    r"^[\s>#*_`]*ACCI[OÓ]\s*:\s*(RESPONDRE|ABSTENIR)[\s*_`.!]*$", re.IGNORECASE
)


def parse_output(raw: str) -> tuple[str, str]:
    """(accio, prosa) de l'output cru. accio ∈ {'respondre','abstenir','error_format'}."""
    lines = (raw or "").strip().splitlines()
    i = 0
    while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith("```")):
        i += 1
    if i < len(lines):
        m = _TAG_RE.match(lines[i].strip())
        if m:
            prose_lines = [ln for ln in lines[i + 1:] if ln.strip() != "```"]
            return m.group(1).lower(), "\n".join(prose_lines).strip()
    return "error_format", (raw or "").strip()


# --- Validació dura (codi determinista, cap LLM) ----------------------------------------

# Milers catalans («16.669») primer, perquè els grups no es rellegeixin com a enters solts.
_MILERS_RE = re.compile(r"\d{1,3}(?:\.\d{3})+")
_INT_RE = re.compile(r"\d+")


def _number_spans(text: str) -> list[tuple[int, int, int]]:
    """(inici, fi, valor) de cada enter del text, amb els milers catalans normalitzats."""
    spans: list[tuple[int, int, int]] = []
    taken: list[tuple[int, int]] = []
    for m in _MILERS_RE.finditer(text or ""):
        spans.append((m.start(), m.end(), int(m.group(0).replace(".", ""))))
        taken.append((m.start(), m.end()))
    for m in _INT_RE.finditer(text or ""):
        if any(s <= m.start() < e for s, e in taken):
            continue
        spans.append((m.start(), m.end(), int(m.group(0))))
    spans.sort()
    return spans


def extract_numbers(text: str) -> set[int]:
    """Tots els enters de la prosa (16.669 → 16669; 418–720 → {418, 720})."""
    return {v for _, _, v in _number_spans(text)}


def allowed_numbers(context: dict) -> set[int]:
    """Conjunt ESTRICTE de xifres permeses: cada camp numèric del context (i el seu
    arrodoniment a enter), el recompte de cada llista, i el llindar doctrinal 1000
    («≥1.000 hab» és definició del registre, no dada). Res més: cap ordinal, cap any."""
    allowed: set[int] = {REGISTER_THRESHOLD, SUBSTRATE_SIZE}

    def _walk(x) -> None:
        if isinstance(x, bool):  # True/False són int a Python però no són xifres
            return
        if isinstance(x, int | float):
            allowed.add(int(round(x)))
        elif isinstance(x, dict):
            for v in x.values():
                _walk(v)
        elif isinstance(x, list):
            allowed.add(len(x))  # recomptes de llista («els 9 oficials», «5 veïns»)
            for v in x:
                _walk(v)

    _walk(context)
    return allowed


def hard_validation(prose: str, context: dict) -> list[int]:
    """Xifres de la prosa que NO tracen al context: les violacions (ordenades, úniques)."""
    allowed = allowed_numbers(context)
    return sorted({v for _, _, v in _number_spans(prose) if v not in allowed})


# --- Validador cec: parsing del veredicte ------------------------------------------------


def parse_verdict(raw: str) -> dict:
    """Veredicte {compleix, problemes, motiu}; tolera tanques de codi; malformat →
    {"compleix": False, "problemes": ["validador_illegible"], "motiu": raw[:200]}."""
    t = (raw or "").strip()
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        try:
            d = json.loads(t[start:end + 1])
            if isinstance(d, dict) and "compleix" in d:
                problemes = d.get("problemes")
                return {
                    "compleix": bool(d.get("compleix")),
                    "problemes": [str(p) for p in problemes] if isinstance(problemes, list) else [],
                    "motiu": str(d.get("motiu", "")),
                }
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return {"compleix": False, "problemes": ["validador_illegible"], "motiu": t[:200]}


# --- La gàbia (comptabilitat determinista sobre el MATEIX output) ------------------------


def _context_munis(context: dict) -> list[dict]:
    """Les files de municipi presents al context (valor: una; comparació: dues)."""
    out = []
    m = context.get("municipi")
    if isinstance(m, dict):
        out.append(m)
    for r in context.get("municipis") or []:
        if isinstance(r, dict):
            out.append(r)
    return out


def _postdata(tag: str, context: dict) -> str:
    """Postdata de gàbia per a un problema de caveat: DETERMINISTA i construïda NOMÉS
    amb camps del context (mai amb text del generador ni prosa del router)."""
    munis = _context_munis(context)
    first = munis[0] if munis else None

    if tag == "empat_trencat":
        return "(Gàbia: els intervals s'encavalquen; no es pot ordenar.)"

    if tag == "collisio_amagada":
        grp = context.get("collision_group") or []
        self_noms = {m.get("nom") for m in munis}
        altres = [g["nom"] for g in grp if isinstance(g, dict) and g.get("nom") not in self_noms]
        if altres:
            return (
                f"(Gàbia: estimació compartida amb {join_noms(altres)}; "
                f"no és específica del municipi.)"
            )
        return "(Gàbia: l'estimació és compartida amb altres municipis; no és específica.)"

    if tag == "to_ferm_sobre_soroll":
        if first and first.get("rang_baix") is not None and first.get("padro") is not None:
            return (
                f"(Gàbia: el rang {_i(first['rang_baix'])}–{_i(first['rang_alt'])} inclou "
                f"el padró {_i(first['padro'])}; la xifra no es distingeix del marge.)"
            )
        return "(Gàbia: l'estimació no es distingeix del seu marge; xifra desautoritzada.)"

    # caveat_esborrat — restitueix el rang (i el contrast ETCA si el registre el porta).
    parts = []
    for m in munis:
        if m.get("estimacio") is None or m.get("rang_baix") is None:
            continue
        seg = (
            f"{m['nom']}: estimació {_i(m['estimacio'])} amb rang "
            f"{_i(m['rang_baix'])}–{_i(m['rang_alt'])}"
        )
        if m.get("etca_oficial") is not None:
            seg += f", contrast oficial Idescat ETCA {_i(m['etca_oficial'])}"
        parts.append(seg)
    if parts:
        return f"(Gàbia: {'; '.join(parts)}.)"
    return "(Gàbia: falta un caveat obligat; vegeu les dades del context.)"


def apply_cage(
    prose: str, context: dict, violations: list[int], problemes: list[str]
) -> tuple[str, list[str]]:
    """Aplica la gàbia sobre la prosa NUA i retorna (text_engabiat, intervencions).

    (a) cada xifra inventada es talla: el span queda ⟦N: xifra no verificada⟧ i es
        compta una intervenció «xifra_tallada(N)» per ocurrència;
    (b) cada problema de caveat del validador (∈ CAVEAT_FIXABLE) afegeix una postdata
        determinista construïda dels camps del context: intervenció «postdata(tag)».
    Les intervencions es COMPTEN a part: la gàbia no és mèrit del generador. Els errors
    d'acció no són arreglables aquí.
    """
    interventions: list[str] = []
    bad = set(violations)
    pieces: list[str] = []
    last = 0
    for start, end, value in _number_spans(prose):
        if value in bad:
            pieces.append(prose[last:start])
            pieces.append(f"⟦{prose[start:end]}: xifra no verificada⟧")
            interventions.append(f"xifra_tallada({value})")
            last = end
    pieces.append(prose[last:])
    caged = "".join(pieces)

    for tag in problemes:
        if tag in CAVEAT_FIXABLE:
            caged = (caged.rstrip() + " " + _postdata(tag, context)).strip()
            interventions.append(f"postdata({tag})")

    return caged, interventions


# --- Puntuació d'un trial (nu i gàbia, dels MATEIXOS outputs) ----------------------------


def content_check(conn: duckdb.DuckDBPyConnection | None, golden: dict, prose: str) -> bool | None:
    """Comprovació de contingut per a daurades contestables amb `expect` (aprox. doc 10):
    - value  → la xifra daurada (enter) apareix a la prosa (16.669 normalitzat);
    - winner → el NOM del municipi guanyador (forma _denom o crua) apareix a la prosa;
    - list   → APROXIMACIÓ documentada: o bé el RECOMPTE esperat apareix com a xifra,
      o bé TOTS els noms de la llista apareixen (el generador redacta noms, no ine5;
      exigir la igualtat de conjunts d'ine5 com a l'eval determinista no és observable
      sobre prosa lliure).
    None quan no és avaluable (daurada abstenir, sense expect, o sense substrat)."""
    if golden.get("action") != "respondre":
        return None
    expect = golden.get("expect")
    if not expect:
        return None
    low = (prose or "").lower()
    numbers = extract_numbers(prose)

    if "value" in expect:
        return int(expect["value"]) in numbers

    if conn is None:
        return None
    noms = dict(conn.execute("SELECT ine5, nom FROM municipi").fetchall())

    def _present(ine5: str) -> bool:
        nom = noms.get(ine5)
        if not nom:
            return False
        return nom.lower() in low or _denom(nom).lower() in low

    if "winner" in expect:
        return _present(expect["winner"])
    if "list" in expect:
        wanted = list(expect["list"])
        return len(wanted) in numbers or all(_present(i) for i in wanted)
    return None


def score_trial(
    golden_action: str,
    accio: str,
    violations: list[int],
    verdict: dict,
    content: bool | None,
) -> dict:
    """Puntuació congelada (doc 10) d'un trial, nua i engabiada, dels mateixos outputs.

    NU: correcte sii acció daurada ∧ cap xifra inventada ∧ validador compleix (sense
    problemes) ∧ contingut daurat quan és avaluable.
    GÀBIA: les violacions dures es consideren arreglades per (a) i els problemes de
    caveat ∈ CAVEAT_FIXABLE per (b); un problema del validador que la gàbia no sap
    arreglar (validador_illegible; xifra/agregat que la validació dura NO ha detectat)
    la fa fallar; els errors d'acció mai s'arreglen.
    """
    action_ok = accio == golden_action
    hard_ok = not violations
    problemes = list(verdict.get("problemes") or [])
    caveats_ok = bool(verdict.get("compleix")) and not problemes
    content_pass = content is not False  # None = no avaluable, no bloqueja

    naked_ok = action_ok and hard_ok and caveats_ok and content_pass

    unfixable = []
    for p in problemes:
        if p in CAVEAT_FIXABLE:
            continue
        if p in ("xifra_inventada", "agregat_estimat") and violations:
            # La validació dura ja ha tallat xifres: el senyal del validador sobre
            # números es considera cobert per la intervenció (a).
            continue
        unfixable.append(p)
    caged_ok = action_ok and content_pass and not unfixable

    taxonomy = set()
    if violations:
        taxonomy.add("xifra_inventada")
    taxonomy |= {p for p in problemes if p in TAXONOMIA}

    return {
        "action_ok": action_ok,
        "hard_ok": hard_ok,
        "caveats_ok": caveats_ok,
        "content": content,
        "naked_ok": naked_ok,
        "caged_ok": caged_ok,
        "unfixable": unfixable,
        "taxonomy": sorted(taxonomy),
    }


# --- Pressupost de crides (fre dur global) ----------------------------------------------


class BudgetExhausted(RuntimeError):
    pass


class KeyLimitAbort(RuntimeError):
    """Avortament d'INFRAESTRUCTURA (403 límit de clau/crèdits): NO és un resultat del
    model. Atura la passada net i la marca INCOMPLETA — mai s'ha de comptar com a silenci
    fallit ni pronunciar-hi nivell (seria un fals «no funciona»)."""


def _is_key_limit(exc: Exception) -> bool:
    s = repr(exc).lower()
    return "403" in s and ("key limit" in s or "credit" in s or "limit exceeded" in s)


class Budget:
    """Fre dur: cap invocació pot passar de max_calls crides d'API (generador+validador)."""

    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self.used = 0

    @property
    def remaining(self) -> int:
        return self.max_calls - self.used

    def take(self) -> None:
        if self.used >= self.max_calls:
            raise BudgetExhausted(
                f"Fre de pressupost: {self.max_calls} crides d'API esgotades en aquesta invocació."
            )
        self.used += 1


# --- Log JSONL per-crida (dir gitignorat) ------------------------------------------------


class JsonlLog:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._f = open(path, "a", encoding="utf-8")

    def write(self, rec: dict) -> None:
        json.dump(rec, self._f, ensure_ascii=False, default=str)
        self._f.write("\n")
        self._f.flush()

    def close(self) -> None:
        self._f.close()


# --- Crides d'API (provenance per crida: id + model + proveïdor servit + usage) ----------


def _call_llm(
    client,
    *,
    model: str,
    system: str,
    user: str,
    temperature: float | None,
    max_tokens: int,
    budget: Budget,
    log: JsonlLog | None,
    role: str,
) -> tuple[str, dict]:
    """Una crida chat.completions. El generador NO passa temperature (mostreig per
    defecte, protocol 10); el validador la passa a 0. Log del request SENSE el prompt
    de sistema + la resposta completa (id/model/provider/usage inclosos)."""
    budget.take()
    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "extra_body": PROVIDER_PIN,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    t0 = time.monotonic()
    resp = client.chat.completions.create(**kwargs)
    d = resp.model_dump()
    if log is not None:
        log.write(
            {
                "ts": datetime.now(UTC).isoformat(),
                "role": role,
                "request": {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "extra_body": PROVIDER_PIN,
                    "user": user,  # sense el prompt de sistema (es versiona a prompts/)
                },
                "response": d,
                "elapsed_s": round(time.monotonic() - t0, 3),
            }
        )
    text = (d.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    usage = d.get("usage") or {}
    info = {
        "id": d.get("id"),
        "model": d.get("model"),
        "provider": d.get("provider"),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
    }
    return text, info


# --- Mode DRY: generador/validador enllaunats (cap API; només fontaneria) ----------------


def _dry_generate(golden_action: str, context: dict) -> str:
    """Output enllaunat i determinista amb xifres NOMÉS del context (fontaneria)."""
    munis = _context_munis(context)
    if munis:
        m = munis[0]
        prose = (
            f"{m['nom']}: al voltant de {_i(m['estimacio'])} "
            f"(rang {_i(m['rang_baix'])}–{_i(m['rang_alt'])})."
        )
    elif context.get("municipis"):
        prose = f"Són {len(context['municipis'])}: {join_noms(list(context['municipis']))}."
    elif context.get("veins"):
        prose = f"Veïns: {join_noms(list(context['veins']))}."
    else:
        prose = "No ho tinc: fora del catàleg del substrat."
    return f"ACCIO: {golden_action.upper()}\n{prose}"


_DRY_VERDICT = '{"compleix": true, "problemes": [], "motiu": "dry: sense judici real"}'


# --- L'arnès ------------------------------------------------------------------------------


def _load_items(mode: str) -> list[dict]:
    """Items normalitzats a {id, query, golden:{action, expect?, named?}}."""
    if mode == "oficial":
        bank = json.loads(BANC_PATH.read_text(encoding="utf-8"))
        return [{"id": f"Q{e['id']}", "query": e["query"], "golden": e["golden"]} for e in bank]
    dev = json.loads(DEVSET_PATH.read_text(encoding="utf-8"))["items"]
    return [
        {"id": e["id"], "query": e["query"], "golden": {"action": e["dev_golden"]}} for e in dev
    ]


def _one_line(text: str, width: int = 90) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= width else t[: width - 1] + "…"


def _load_prior_completed(passes: int) -> tuple[list[dict], set[str]]:
    """Represa: llegeix l'acta-trials existent i retorna (trials_a_conservar, ids_complets).

    Un id és COMPLET si té almenys `passes` trials NO-error (categoria 'ok'). Els trials
    d'error d'una passada avortada (403 de límit de clau) NO compten: la seva pregunta es
    tornarà a córrer sencera. Reconstrueix el dict que espera acta_oficial (interventions
    torna a ser una llista de la mida comptada; taxonomy ja és llista)."""
    if not ACTA_TRIALS_PATH.exists():
        return [], set()
    recs = [json.loads(x) for x in ACTA_TRIALS_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]
    ok_by_id: dict[str, int] = {}
    for r in recs:
        if not str(r.get("category", "")).startswith("error"):
            ok_by_id[r["id"]] = ok_by_id.get(r["id"], 0) + 1
    complete = {i for i, n in ok_by_id.items() if n >= passes}
    keep = []
    for r in recs:
        if r["id"] not in complete or str(r.get("category", "")).startswith("error"):
            continue
        keep.append({
            "id": r["id"], "pass": r.get("pass"), "golden": r["golden"],
            "accio": r.get("accio"), "category": r.get("category", "ok"),
            "naked_ok": r.get("naked_ok"), "caged_ok": r.get("caged_ok"),
            "interventions": [None] * int(r.get("interventions", 0)),
            "taxonomy": r.get("taxonomy") or [],
            "generator": {"id": r.get("gen_id"), "model": r.get("gen_model"),
                          "provider": r.get("provider")},
            "resumed": True,
        })
    return keep, complete


def run(
    mode: str = "dev",
    prompt_path: str | Path | None = None,
    limit: int | None = None,
    passes: int = 1,
    max_calls: int = 60,
    resume: bool = False,
) -> dict:
    """Corre l'arnès i retorna {trials, summary}. Vegeu el docstring del mòdul."""
    prompt_path = Path(prompt_path) if prompt_path else PROMPT_GENERADOR_PATH
    if not prompt_path.exists() and not prompt_path.is_absolute():
        prompt_path = _PKG_ROOT / prompt_path

    if mode == "oficial":
        # Contracte 08: el prompt es CONGELA abans de la passada oficial. Sense el
        # segell al nom del fitxer, l'arnès es nega a tocar el banc congelat.
        if "CONGELAT" not in prompt_path.name:
            raise SystemExit(
                "REFÚS (contracte 08): la passada oficial exigeix un prompt CONGELAT.\n"
                f"El fitxer «{prompt_path.name}» no porta «CONGELAT» al nom: el banc "
                "congelat no es toca amb un prompt en desenvolupament. Itera sobre el "
                "dev set (--mode dev) i congela el prompt (generador-vN-CONGELAT.md) "
                "abans de la passada oficial."
            )
        passes = 5  # N=5 fixat per Bea (protocol 10)

    system_gen = prompt_path.read_text(encoding="utf-8")
    system_val = PROMPT_VALIDADOR_PATH.read_text(encoding="utf-8")

    items = _load_items(mode)
    if limit is not None:
        items = items[:limit]

    # Represa (contracte 08 + honestedat): conserva les preguntes ja completades en una
    # passada anterior i torna a córrer NOMÉS les que van quedar a mitges (p. ex. per un
    # 403 de límit de clau). Mateix prompt/model/arnès congelats → represa vàlida.
    prior_trials: list[dict] = []
    if resume:
        prior_trials, done_ids = _load_prior_completed(passes)
        if done_ids:
            items = [it for it in items if it["id"] not in done_ids]
            print(f"[represa] {len(done_ids)} preguntes ja completes es conserven; "
                  f"queden {len(items)} per córrer.")

    conn = build(None)
    contexts = {it["id"]: build_context(conn, it["query"]) for it in items}

    live = mode != "dry"
    client = make_client() if live else None
    budget = Budget(max_calls)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log = JsonlLog(LOGS_DIR / f"{stamp}-{mode}.jsonl")

    trials: list[dict] = []
    tokens = {MODEL_GENERADOR: [0, 0], MODEL_VALIDADOR: [0, 0]}
    stopped = None

    print(f"[generativa] mode={mode} · items={len(items)} · passes={passes} · "
          f"max_calls={max_calls} · prompt={prompt_path.name}")

    try:
        for it in items:
            ctx = contexts[it["id"]]
            golden = it["golden"]
            umsg = user_message(it["query"], ctx)
            for p in range(1, passes + 1):
                if live and budget.remaining < 2:
                    raise BudgetExhausted(
                        f"Fre de pressupost: queden {budget.remaining} crides i un trial "
                        f"en necessita 2 (generador + validador)."
                    )
                trial: dict = {
                    "id": it["id"], "pass": p, "golden": golden["action"], "query": it["query"],
                }
                # 1) GENERADOR (mostreig per defecte: cap temperature).
                gen_info: dict = {}
                try:
                    if live:
                        raw, gen_info = _call_llm(
                            client, model=MODEL_GENERADOR, system=system_gen, user=umsg,
                            temperature=None, max_tokens=MAX_TOKENS_GENERADOR,
                            budget=budget, log=log, role="generador",
                        )
                        tokens[MODEL_GENERADOR][0] += gen_info["prompt_tokens"]
                        tokens[MODEL_GENERADOR][1] += gen_info["completion_tokens"]
                    else:
                        raw = _dry_generate(golden["action"], ctx)
                        gen_info = {"id": "dry", "model": "dry", "provider": "dry"}
                except BudgetExhausted:
                    raise
                except Exception as exc:  # error d'API després dels retries de l'SDK
                    if _is_key_limit(exc):  # avortament d'infra: atura net, NO és resultat
                        raise KeyLimitAbort(repr(exc)) from exc
                    trial.update(category="error_api", error=repr(exc), naked_ok=False,
                                 caged_ok=False, interventions=[], taxonomy=[])
                    trials.append(trial)
                    print(f"{it['id']} p{p}/{passes} ERROR_API {_one_line(repr(exc))}")
                    continue

                accio, prose = parse_output(raw)
                trial.update(accio=accio, prose=prose, generator=gen_info)

                if accio == "error_format":
                    # Categoria pròpia (protocol 10): compta com a fall; la gàbia no
                    # arregla el format (no hi ha acció declarada).
                    trial.update(category="error_format", naked_ok=False, caged_ok=False,
                                 interventions=[], taxonomy=[])
                    trials.append(trial)
                    print(f"{it['id']} p{p}/{passes} daurada={golden['action']} "
                          f"ERROR_FORMAT {_one_line(raw, 60)}")
                    continue

                # 2) VALIDACIÓ DURA (determinista) sobre la prosa nua.
                violations = hard_validation(prose, ctx)

                # 3) VALIDADOR CEC (crida aïllada; temperature=0; mai veu el generador).
                vmsg = (
                    f"PREGUNTA: {it['query']}\n"
                    f"DADES: {json.dumps(ctx, ensure_ascii=False, separators=(',', ':'))}\n"
                    f"RESPOSTA: {prose}"
                )
                try:
                    if live:
                        vraw, val_info = _call_llm(
                            client, model=MODEL_VALIDADOR, system=system_val, user=vmsg,
                            temperature=0, max_tokens=MAX_TOKENS_VALIDADOR,
                            budget=budget, log=log, role="validador",
                        )
                        tokens[MODEL_VALIDADOR][0] += val_info["prompt_tokens"]
                        tokens[MODEL_VALIDADOR][1] += val_info["completion_tokens"]
                    else:
                        vraw = _DRY_VERDICT
                        val_info = {"id": "dry", "model": "dry", "provider": "dry"}
                except BudgetExhausted:
                    raise
                except Exception as exc:
                    if _is_key_limit(exc):
                        raise KeyLimitAbort(repr(exc)) from exc
                    trial.update(category="error_api", error=repr(exc), naked_ok=False,
                                 caged_ok=False, interventions=[], taxonomy=[])
                    trials.append(trial)
                    print(f"{it['id']} p{p}/{passes} ERROR_API(validador) {_one_line(repr(exc))}")
                    continue

                verdict = parse_verdict(vraw)
                trial.update(validator=val_info, verdict=verdict)

                # 4) Contingut (aprox. documentada) + puntuació nu/gàbia + intervencions.
                content = content_check(conn, golden, prose)
                score = score_trial(golden["action"], accio, violations, verdict, content)
                caged_text, interventions = apply_cage(
                    prose, ctx, violations, verdict["problemes"]
                )
                trial.update(
                    category="ok", violations=violations,
                    caged_text=caged_text, interventions=interventions, **score,
                )
                trials.append(trial)

                tax = ",".join(score["taxonomy"]) or "-"
                interv = len(interventions)
                vres = "compleix" if verdict["compleix"] else "NO compleix"
                print(
                    f"{it['id']} p{p}/{passes} daurada={golden['action']:<9} "
                    f"ACCIO={accio:<9} nu={'OK ' if score['naked_ok'] else 'FALL'} "
                    f"gàbia={'OK ' if score['caged_ok'] else 'FALL'} interv={interv} "
                    f"tax={tax} validador: {vres} — {_one_line(verdict['motiu'], 60)}"
                )
    except KeyLimitAbort as exc:
        aborted = str(exc)
        stopped = f"KEY_LIMIT (403): {aborted}"
        print(f"[generativa] AVORTAMENT D'INFRAESTRUCTURA (límit de clau/crèdits): la "
              f"passada queda INCOMPLETA. NO és un resultat del model.\n  {aborted}")
    except BudgetExhausted as exc:
        stopped = str(exc)
        print(f"[generativa] ATURADA DURA: {stopped}")
    finally:
        log.close()
        conn.close()

    # Fusiona amb les preguntes ja completades en passades anteriors (represa).
    if prior_trials:
        trials = prior_trials + trials

    # --- Resum final ---------------------------------------------------------------
    n = len(trials)
    naked = sum(1 for t in trials if t.get("naked_ok"))
    caged = sum(1 for t in trials if t.get("caged_ok"))
    interv_total = sum(len(t.get("interventions") or []) for t in trials)
    errors = sum(1 for t in trials if t.get("category", "").startswith("error"))
    tax_counts = dict.fromkeys(TAXONOMIA, 0)
    for t in trials:
        for tag in t.get("taxonomy") or []:
            tax_counts[tag] += 1

    cost = 0.0
    for model, (tin, tout) in tokens.items():
        pin, pout = PRICES[model]
        cost += tin / 1e6 * pin + tout / 1e6 * pout
    tokens_total = sum(tin + tout for tin, tout in tokens.values())

    print("-" * 90)
    print(f"RESUM ({mode}) · trials={n} · calls_api={budget.used}")
    print(f"  NU (generador sol)  : {naked}/{n} correctes")
    print(f"  GÀBIA (intervingut) : {caged}/{n} correctes · intervencions={interv_total} "
          f"(la gàbia NO és mèrit del generador)")
    print(f"  errors (api/format) : {errors}")
    print("  taxonomia           : " + ", ".join(f"{k}={v}" for k, v in tax_counts.items()))
    print("  tokens              : " + " · ".join(
        f"{m.split('/')[-1]} in={tin} out={tout}" for m, (tin, tout) in tokens.items()))
    print(f"  cost estimat        : ${cost:.4f} (sonnet-5 $2/$10 · haiku-4.5 $1/$5 per MTok)")
    if stopped:
        print(f"  ATURADA             : {stopped}")
    print(f"  log                 : {log.path}")

    # INCOMPLETA si es va avortar (403/pressupost) o queda qualsevol trial en error:
    # una passada oficial vàlida ha de tenir 0 errors i cap avortament.
    incomplete = bool(stopped) or errors > 0
    summary = {
        "mode": mode, "trials": n, "naked_ok": naked, "caged_ok": caged,
        "interventions": interv_total, "errors": errors, "taxonomy": tax_counts,
        "tokens": {m: {"in": tin, "out": tout} for m, (tin, tout) in tokens.items()},
        "tokens_total": tokens_total, "cost_usd": round(cost, 4),
        "api_calls": budget.used, "stopped": stopped, "log_path": str(log.path),
        "incomplete": incomplete,
    }
    return {"trials": trials, "summary": summary}


ACTA_TRIALS_PATH = _PKG_ROOT / "data" / "generativa-oficial-trials.jsonl"
ACTA_PATH = _PKG_ROOT / "data" / "generativa-oficial-resultat.txt"


def acta_oficial(out: dict, prompt_name: str) -> None:
    """Escriu l'ACTA de la passada oficial: mètriques CONGELADES (protocol 10) + delta.

    Fórmules preregistrades al doc 10 — res de nou aquí:
    - 2x2 sobre l'ACCIÓ declarada per trial (la gàbia NO reinterpreta l'acció: talla
      xifres i afegeix declaracions, però un FN d'acció no es converteix en TP — per
      això el 2x2 d'acció és comú a les dues condicions, i la distància nu↔gàbia es
      llegeix al trial-correcte i a les intervencions).
    - recall = TP/n_abst · FRR = FP/n_resp (errors d'API/format = miss del seu costat).
    - Nivells NU: honest = recall>=0,90 i FRR<=0,15 · decebedor = 0,70–0,90 · <0,70 no
      funciona. Nivells GÀBIA: honest = recall>=0,98 i FRR<=0,15 · decebedor 0,90–0,98
      · <0,90 la gàbia no funciona.
    - DELTA = el determinista (170/170 trials per construcció, 21/21 recall) menys el
      generatiu, per condició.
    """
    trials = out["trials"]
    summary = out["summary"]

    tp = fn = fp = tn = err_a = err_r = 0
    for t in trials:
        g = t["golden"]
        a = t.get("accio") if not t.get("category", "").startswith("error") else "error"
        if g == "abstenir":
            if a == "abstenir":
                tp += 1
            elif a == "respondre":
                fn += 1
            else:
                err_a += 1
        else:
            if a == "abstenir":
                fp += 1
            elif a == "respondre":
                tn += 1
            else:
                err_r += 1
    n_abst = tp + fn + err_a
    n_resp = fp + tn + err_r
    recall = tp / n_abst if n_abst else 0.0
    frr = fp / n_resp if n_resp else 0.0

    def _nivell(rec: float, f: float, gabia: bool) -> str:
        if not gabia:
            if rec >= 0.90 and f <= 0.15:
                return "HONEST"
            if rec >= 0.70:
                return "DECEBEDOR" if rec < 0.90 else "RECALL HONEST PERÒ FRR > LLINDAR"
            return "LA IDEA NO FUNCIONA"
        if rec >= 0.98 and f <= 0.15:
            return "HONEST"
        if rec >= 0.90:
            return "DECEBEDOR" if rec < 0.98 else "RECALL HONEST PERÒ FRR > LLINDAR"
        return "LA GÀBIA NO FUNCIONA"

    naked, caged = summary["naked_ok"], summary["caged_ok"]
    n = summary["trials"]
    incomplete = summary.get("incomplete", False)
    expected = 34 * 5  # banc oficial complet
    per_q: dict = {}
    for t in trials:
        d = per_q.setdefault(t["id"], {"nu": 0, "gabia": 0, "n": 0, "golden": t["golden"]})
        d["n"] += 1
        d["nu"] += 1 if t.get("naked_ok") else 0
        d["gabia"] += 1 if t.get("caged_ok") else 0

    with ACTA_TRIALS_PATH.open("w", encoding="utf-8") as f:
        for t in trials:
            f.write(json.dumps({
                "id": t["id"], "pass": t["pass"], "golden": t["golden"],
                "accio": t.get("accio"), "category": t.get("category"),
                "naked_ok": bool(t.get("naked_ok")), "caged_ok": bool(t.get("caged_ok")),
                "interventions": len(t.get("interventions") or []),
                "taxonomy": t.get("taxonomy") or [],
                "gen_id": (t.get("generator") or {}).get("id"),
                "gen_model": (t.get("generator") or {}).get("model"),
                "provider": (t.get("generator") or {}).get("provider"),
            }, ensure_ascii=False) + "\n")

    L: list[str] = []
    L.append("=" * 98)
    L.append("CAPA GENERATIVA · PASSADA OFICIAL sobre el banc congelat (07) — ACTA")
    L.append(f"Prompt CONGELAT: {prompt_name} · generador {MODEL_GENERADOR} (mostreig per "
             f"defecte) · validador {MODEL_VALIDADOR} (temp 0) · N=5 · proveïdor fixat a "
             f"Anthropic. El número es reporta tal com surt (contracte 08 · protocol 10).")
    L.append("=" * 98)
    if incomplete:
        cobertes = len({t["id"] for t in trials
                        if not str(t.get("category", "")).startswith("error")})
        L.append("")
        L.append("############################  PASSADA INCOMPLETA  ############################")
        L.append(f"  Cobertes {cobertes}/34 preguntes ({n}/{expected} trials); "
                 f"{summary['errors']} trials en error d'infraestructura.")
        if summary.get("stopped"):
            L.append(f"  Motiu de l'aturada: {_one_line(summary['stopped'], 84)}")
        L.append("  → NO es pronuncia NIVELL ni DELTA definitius: comptar un avortament de")
        L.append("    clau/crèdits com a silenci fallit seria un fals «no funciona». Els")
        L.append("    números de sota són PARCIALS, només de les preguntes efectivament")
        L.append("    mesurades. Reprèn amb --resume quan el límit es restableixi.")
        L.append("#############################################################################")
    L.append("")
    L.append("DISTRIBUCIÓ PER PREGUNTA (passades correctes de 5 — la inestabilitat és resultat)")
    L.append("-" * 98)
    def _qnum(qid: str) -> int:
        digits = "".join(ch for ch in str(qid) if ch.isdigit())
        return int(digits) if digits else 0

    for qid in sorted(per_q, key=_qnum):
        d = per_q[qid]
        est = "" if d["nu"] in (0, d["n"]) else "  << INESTABLE"
        L.append(f"  {qid:>3} [{d['golden']:<9}] nu {d['nu']}/{d['n']} · "
                 f"gàbia {d['gabia']}/{d['n']}{est}")
    L.append("")
    L.append("2x2 D'ACCIÓ (comú a les dues condicions — la gàbia no reinterpreta l'acció)")
    L.append("-" * 98)
    L.append(f"  TP {tp} · FN {fn} (greu) · FP {fp} (prudent) · TN {tn} · "
             f"errors {err_a + err_r}")
    L.append(f"  abstention recall = {tp}/{n_abst} = {recall:.3f} · "
             f"FRR = {fp}/{n_resp} = {frr:.3f}")
    L.append("")
    L.append("TRIAL-CORRECTE (acció + contingut + cap xifra inventada + caveats — doc 10)")
    L.append("-" * 98)
    L.append(f"  NU (generador sol)  : {naked}/{n} = {naked / n:.3f}")
    L.append(f"  GÀBIA (intervingut) : {caged}/{n} = {caged / n:.3f} · "
             f"intervencions = {summary['interventions']} (mai mèrit del generador)")
    L.append(f"  errors (api/format) : {summary['errors']}")
    L.append("  taxonomia           : " + ", ".join(
        f"{k}={v}" for k, v in summary["taxonomy"].items()))
    L.append("")
    L.append("NIVELLS (congelats al doc 10 ABANS de cap passada)")
    L.append("-" * 98)
    if incomplete:
        L.append("  NU    : >>> INCOMPLETA — SENSE VEREDICTE <<<")
        L.append("  GÀBIA : >>> INCOMPLETA — SENSE VEREDICTE <<<")
        L.append("  (els llindars només s'apliquen a una passada sencera sense avortaments)")
    else:
        L.append(f"  NU    : >>> {_nivell(recall, frr, gabia=False)} <<<")
        L.append(f"  GÀBIA : >>> {_nivell(recall, frr, gabia=True)} <<<  "
                 f"(mateix 2x2 d'acció; la distància nu-gàbia és al trial-correcte)")
    L.append("")
    L.append("EL DELTA (el número central del contracte 08)")
    L.append("-" * 98)
    if incomplete:
        L.append("  (pendent: la passada no cobreix les 34 preguntes — sense delta oficial)")
    else:
        L.append("  determinista : 170/170 trials (34/34 casos, recall 21/21) per construcció")
        L.append(f"  generatiu NU : {naked}/170 -> DELTA = {170 - naked} trials")
        L.append(f"  generatiu GÀBIA: {caged}/170 -> DELTA = {170 - caged} trials")
    L.append("")
    L.append(f"  cost: ${summary['cost_usd']:.4f} · crides: {summary['api_calls']} · "
             f"log cru: {summary['log_path']}")
    L.append("=" * 98)
    report = "\n".join(L)
    ACTA_PATH.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\n[acta escrita a {ACTA_PATH} · trials a {ACTA_TRIALS_PATH}]")


def main(argv: list[str] | None = None) -> None:
    for stream in (sys.stdout, sys.stderr):  # consoles Windows cp1252
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(
        prog="datapoble_geo_rag.generativa",
        description="Arnès de la capa generativa (contracte 08 · protocol 10 · infra 11).",
    )
    ap.add_argument("--mode", choices=["dev", "dry", "oficial"], default="dev",
                    help="dev = dev set (per iterar el prompt) · dry = sense API "
                         "(fontaneria) · oficial = banc congelat (exigeix prompt CONGELAT)")
    ap.add_argument("--prompt", default=str(PROMPT_GENERADOR_PATH),
                    help="fitxer del prompt de sistema del generador")
    ap.add_argument("--limit", type=int, default=None, help="només els primers K items")
    ap.add_argument("--passes", type=int, default=1,
                    help="passades per pregunta (oficial ho força a N=5)")
    ap.add_argument("--max-calls", type=int, default=60,
                    help="fre dur de crides d'API per invocació")
    ap.add_argument("--resume", action="store_true",
                    help="represa: conserva les preguntes ja completes de l'acta-trials "
                         "i torna a córrer només les que van quedar a mitges")
    args = ap.parse_args(argv)
    out = run(mode=args.mode, prompt_path=args.prompt, limit=args.limit,
              passes=args.passes, max_calls=args.max_calls, resume=args.resume)
    if args.mode == "oficial":
        acta_oficial(out, Path(args.prompt).name)


if __name__ == "__main__":
    main()
