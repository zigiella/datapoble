"""Fase 3 · encaminador genèric de consultes — TORCH-FREE. Afegeix routing, MAI política.

Mapa una consulta en llenguatge natural a les funcions QUE JA EXISTEIXEN (Fases 0–2):
detecció de municipi (retrieval.detect_anchors), comparació (compare.answer_comparison),
resposta modulada per σ (compare.answer), veïns espacials (build.neighbors), llistes de
catàleg (taula municipi per `register`) i l'avís de col·lisió (descriptions).

REGLES D'HONESTEDAT DE L'ARNÈS (contracte 06-fase3-kpi-abstencio.md):
- Cap judici de distingibilitat/to/col·lisió es pren aquí: tots vénen dels mòduls de
  doctrina existents (distinguish → compare; _collision_groups → descriptions). El router
  només ENCAMINA i COMPON.
- GENÈRIC per construcció: el desconegut cau per defecte, mai per llista. Un municipi el
  nom del qual no és entre els 31 del substrat → «no ho tinc». Un indicador quantitatiu
  que no és al vocabulari del que el substrat TÉ (presència/pernocta/padró/ETCA…) →
  «no tinc aquest indicador». Cap literal de cap banc de proves apareix en aquest codi.
- La classificació respondre/abstenir es deriva dels CAMPS ESTRUCTURATS del sistema
  (register, col·lisió, distinguishable), mai d'un regex sobre la nostra pròpia prosa.

route(conn, query_text) -> {intent, munis, answer_action, text, meta}.
"""

from __future__ import annotations

import re

import duckdb

from .build import neighbors
from .compare import answer, answer_comparison, compare  # noqa: F401 (compare re-exported)
from .descriptions import _collision_groups, _collision_note, _denom, _i, join_noms
from .retrieval import detect_anchors

# --- Vocabulari del que el substrat TÉ (mai del que no té) ---------------------------
# Aquests termes poden ser literals perquè anomenen els camps/registres reals de la
# taula municipi. El que NO hi és no s'enumera enlloc: cau per defecte (el mecanisme
# honest és desconegut-per-defecte).

# Indicador de valor que el substrat serveix: la presència/pernocta estimada (i el seu
# vocabulari poblacional) + els camps padró i ETCA.
KNOWN_VALUE_INDICATORS = (
    "presènc", "presenc",       # presència (nocturna) estimada
    "pernoct",                   # pernocta / hi pernocta
    "estimac",                   # estimació
    "gent", "habitant", "poblac",  # vocabulari poblacional del mateix indicador
    "padró", "padro",            # camp padró
    "etca",                      # camp etca_oficial
)

# Llistes de catàleg per registre (el registre és un camp computat del substrat).
OFICIAL_LIST_TOKENS = ("dada oficial", "etca", "idescat", "oficial")
DISTRUST_LIST_TOKENS = ("refi", "fiabl", "fiabilitat", "soroll")

# Relació espacial que el substrat respon (build.neighbors).
NEIGHBOUR_TOKENS = ("toquen", "toca ", "veïn", "vein", "limiten", "limita", "frontere")

# Forma de comparació: «qui (en) té més», «té més … o …», «tenen més».
_COMPARE_RE = re.compile(r"\bqui\s+(en\s+)?té\s+més\b|\bté\s+més\b|\btenen\s+més\b")

# Forma de pregunta quantitativa (interrogatius de quantitat/identitat de valor).
_QUANT_RE = re.compile(r"\bquin(a|s|es)?\b|\bquant(a|s|es)?\b")

# Forma de llista («quins municipis…», «de quins pobles…»).
_LIST_RE = re.compile(r"\b(de\s+)?quin(s|es)\b.*\b(municipis|pobles)\b")

__all__ = ["route"]


def _out(intent: str, munis: list[str], action: str, text: str, **meta) -> dict:
    return {
        "intent": intent,
        "munis": munis,
        "answer_action": action,
        "text": text,
        "meta": meta,
    }


def _noms(conn: duckdb.DuckDBPyConnection, ine5s: list[str]) -> list[str]:
    rows = dict(conn.execute("SELECT ine5, nom FROM municipi").fetchall())
    return [_denom(rows[i]) for i in ine5s if i in rows]


def _route_comparison(conn, query_text: str, munis: list[str]) -> dict:
    """Comparació → compare.answer_comparison (la distingibilitat la diu distinguish)."""
    res = answer_comparison(conn, query_text)
    munis = res["munis"]
    result = res["result"]
    text = res["text"]
    if result is None:
        # Menys de dos municipis reconeguts: el sistema ho declara honestament.
        return _out("comparacio", munis, "abstenir", text, result=None)
    if result["distinguishable"]:
        return _out(
            "comparacio", munis, "respondre", text,
            winner=result["higher"], distinguishable=True,
        )
    # Bandes solapades → abstenció d'ordenar. Si a més els dos munis comparteixen grup
    # de col·lisió (mateixa estimació+banda), la col·lisió es reporta — el judici ve de
    # descriptions._collision_groups, no d'aquí.
    by_ine, allm = _collision_groups()
    group_a = by_ine.get(munis[0])
    collision = bool(group_a and munis[1] in group_a)
    if collision:
        berg = {r[0] for r in conn.execute("SELECT ine5 FROM municipi").fetchall()}
        reg = conn.execute(
            "SELECT register FROM municipi WHERE ine5=?", [munis[0]]
        ).fetchone()[0]
        text += _collision_note({"ine5": munis[0], "register": reg}, by_ine, allm, berg)
    return _out(
        "comparacio", munis, "abstenir", text,
        winner=None, distinguishable=False, collision=collision,
    )


def _route_neighbours(conn, ine5: str) -> dict:
    rows = neighbors(conn, ine5)
    nom = _noms(conn, [ine5])[0]
    if rows is None:
        return _out(
            "veins", [ine5], "abstenir",
            f"No puc calcular els veïns de {nom}: l'extensió espacial no està disponible.",
            ine5_list=None,
        )
    ine5_list = [r[0] for r in rows]
    noms = join_noms([_denom(r[1]) for r in rows])
    return _out(
        "veins", [ine5], "respondre",
        f"Municipis que toquen {nom}: {noms}.",
        ine5_list=ine5_list,
    )


def _route_register_list(conn, register: str) -> dict:
    rows = conn.execute(
        "SELECT ine5, nom FROM municipi WHERE register = ? ORDER BY nom", [register]
    ).fetchall()
    ine5_list = [r[0] for r in rows]
    noms = join_noms([_denom(r[1]) for r in rows])
    if register == "oficial":
        text = (
            f"{len(rows)} municipis amb registre oficial (≥1.000 hab, amb dada ETCA "
            f"d'Idescat, contrastable): {noms}."
        )
    else:
        text = (
            f"{len(rows)} municipis amb registre {register} (l'interval inclou el propi "
            f"padró: l'estimació no es distingeix del marge): {noms}."
        )
    return _out("cataleg_registre", [], "respondre", text, register=register,
                ine5_list=ine5_list)


def _route_muni_value(conn, ine5: str) -> dict:
    """Valor d'UN municipi: compare.answer (to per σ) + comprovació de col·lisió.

    Classificació per camps estructurats, exactament la doctrina existent:
    - col·lisió (el número no és específic del municipi) → ABSTENIR (amb l'informe del
      grup, i el contrast ETCA si el registre és oficial — text de descriptions).
    - register 'soroll' (el rang inclou el padró) → ABSTENIR (answer() ja porta la
      declaració de marge).
    - altrament → RESPONDRE (to ferm/prudent segons σ; a l'oficial s'hi afegeix el
      contrast amb la dada ETCA del substrat).
    """
    res = answer(conn, ine5)
    if res.get("register") is None:
        return _out("valor_municipi", [ine5], "abstenir", res["text"], found=False)

    by_ine, allm = _collision_groups()
    members = by_ine.get(ine5)
    text = res["text"]

    if members:
        berg = {r[0] for r in conn.execute("SELECT ine5 FROM municipi").fetchall()}
        note = _collision_note(
            {"ine5": ine5, "register": res["register"]}, by_ine, allm, berg
        )
        return _out(
            "valor_municipi", [ine5], "abstenir", text + note,
            register=res["register"], tone=res["tone"], collision=True,
            collision_group=list(members), estimacio=res["estimacio"], band=res["band"],
        )

    if res["register"] == "soroll":
        # El text d'answer() ja declara «no es distingeix del propi marge».
        return _out(
            "valor_municipi", [ine5], "abstenir", text,
            register=res["register"], tone=res["tone"], collision=False,
            estimacio=res["estimacio"], band=res["band"],
        )

    if res["register"] == "oficial":
        etca = conn.execute(
            "SELECT etca_oficial FROM municipi WHERE ine5=?", [ine5]
        ).fetchone()[0]
        if etca is not None:
            text += f" Contrast amb la dada oficial d'Idescat (ETCA): {_i(etca)}."

    return _out(
        "valor_municipi", [ine5], "respondre", text,
        register=res["register"], tone=res["tone"], collision=False,
        estimacio=res["estimacio"], band=res["band"],
    )


def route(conn: duckdb.DuckDBPyConnection, query_text: str) -> dict:
    """Encamina una consulta a les funcions existents. GENÈRIC: el desconegut cau sol.

    Retorna {intent, munis, answer_action ('respondre'|'abstenir'), text, meta}.
    """
    q = (query_text or "").lower()
    munis = detect_anchors(conn, query_text, limit=2)

    # 1) Comparació («qui té més…», «té més … o …»).
    if _COMPARE_RE.search(q):
        return _route_comparison(conn, query_text, munis)

    # 2) Veïns espacials («toquen», «veïns», «limiten») amb un municipi reconegut.
    if any(t in q for t in NEIGHBOUR_TOKENS) and munis:
        return _route_neighbours(conn, munis[0])

    # 3) Llistes de catàleg per registre («quins municipis/pobles …»).
    if _LIST_RE.search(q):
        if any(t in q for t in DISTRUST_LIST_TOKENS):
            return _route_register_list(conn, "soroll")
        if any(t in q for t in OFICIAL_LIST_TOKENS):
            return _route_register_list(conn, "oficial")

    has_known = any(t in q for t in KNOWN_VALUE_INDICATORS)
    has_quant = bool(_QUANT_RE.search(q))

    # 4) Indicador conegut (o menció nua d'un municipi): la ruta de valor.
    if has_known or (munis and not has_quant):
        if munis:
            return _route_muni_value(conn, munis[0])
        # Indicador conegut però cap municipi entre els 31 → fora de catàleg.
        return _out(
            "municipi_desconegut", [], "abstenir",
            "No ho tinc: no reconec cap municipi dels 31 del substrat (Berguedà) en "
            "aquesta consulta.",
        )

    # 5) Pregunta quantitativa sense cap indicador conegut → indicador fora de catàleg.
    if has_quant:
        if munis:
            nom = _noms(conn, [munis[0]])[0]
            return _out(
                "indicador_desconegut", munis, "abstenir",
                f"No tinc aquest indicador per a {nom}: el substrat només cobreix la "
                f"presència/pernocta estimada (amb banda), el padró i la dada oficial "
                f"ETCA.",
            )
        return _out(
            "indicador_desconegut", [], "abstenir",
            "No ho tinc: ni reconec cap municipi dels 31 del substrat ni l'indicador "
            "demanat és entre els que el substrat cobreix.",
        )

    # 6) Res reconegut → abstenció per defecte (mai inventar una ruta).
    return _out(
        "consulta_no_reconeguda", munis, "abstenir",
        "No reconec la consulta: no hi detecto cap intent que el substrat pugui servir.",
    )
