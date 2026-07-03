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
# taula municipi i la SEMÀNTICA de l'única magnitud servida (presència/pernocta = gent
# que hi és/hi dorm/hi viu de veritat). El que NO hi és no s'enumera enlloc: cau per
# defecte (el mecanisme honest és desconegut-per-defecte).
#
# ENDURIT (v2, 2026-07-03) després de la sonda de paràfrasis (fase3-parafrasis-resultat
# v1): la capa d'intenció fallava per (1) «gent» sola activant la ruta de valor («quant
# GUANYA la gent» responia pernocta — FN greu), (2) menció-nua massa golafre, (3)
# comparacions només per «té més», (4) famílies de vocabulari massa estretes. El fix és
# ESTRUCTURAL (precedència + famílies semàntiques), no una llista de frasejos del joc de
# proves: cap paràfrasi literal apareix aquí. Caveat de circularitat declarat: les
# famílies s'han ampliat a partir dels MODES DE FALL de la v1 (no dels seus strings);
# la prova de generalització real seran frasejos nous (tests + capa generativa).

# (a) Indicadors EXPLÍCITS del camp servit: basten sols.
EXPLICIT_VALUE_TOKENS = (
    "presènc", "presenc",  # presència (nocturna) estimada
    "pernoct",             # pernocta / hi pernocta
    "estimac",             # estimació
    "padró", "padro",      # camp padró
    "etca",                # camp etca_oficial
)

# (b) Paraules de GENT: ja NO basten soles (la pregunta pot ser sobre una altra magnitud
# de la gent: guanys, feina…). Necessiten un marc de presència.
_PEOPLE_RE = re.compile(
    r"\b(gent|gente|habitants?|poblaci\w*|población|residents?|ànim(?:a|es))\b"
)

# (c) MARC DE PRESÈNCIA fort (basta sol): dormir-hi / fer-hi nit / ser-hi quan és fosc.
_STRONG_FRAME_RE = re.compile(
    r"\b(dorm\w*|duerme\w*|nits?|noche|nocturn\w*|fosc|pernocta\w*)\b|\bhi\s+viu\w*\b"
)

# (d) MARC feble (necessita paraula de gent): viure-hi/ser-hi «de veritat/efectiu/real».
# v2.1: + «fa/fan/fer vida» i «moviment» (presència viscuda), destapats pel dev set de la
# capa generativa (D2) — famílies de presència, no strings del dev set.
_WEAK_FRAME_RE = re.compile(
    r"\b(viu(?:en)?|vive[ns]?|queda\w*|reals?|real|efectiu\w*|efectiva\w*|moviment)\b"
    r"|\bhi\s+ha\b|\bde\s+veritat\b|\bde\s+deb[oò]\b|\bde\s+verdad\b|\bde\s+fet\b"
    r"|\bf(?:a|an|er)\s+vida\b"
)

# Llistes de catàleg per registre (el registre és un camp computat del substrat).
# «contrast(ar)» és vocabulari propi del registre oficial (la seva definició al web).
OFICIAL_LIST_TOKENS = ("dada oficial", "etca", "idescat", "oficial", "contrast")
# Família de (des)confiança/credibilitat de l'estimació = la semàntica del soroll.
DISTRUST_LIST_TOKENS = (
    "refi", "fiabl", "fiabilitat", "soroll", "fluix", "creie", "creïbl", "credib",
    "confia", "confieu",
)

# Relació espacial que el substrat respon (build.neighbors).
NEIGHBOUR_TOKENS = (
    "toquen", "toca ", "veïn", "vein", "limiten", "limita", "fronter", "envolt",
    "colind",
)

# Forma de comparació EXPLÍCITA: «qui (en) té més», «té més … o …», «tenen més».
_COMPARE_RE = re.compile(r"\bqui\s+(en\s+)?té\s+més\b|\bté\s+més\b|\btenen\s+més\b")
# Pista comparativa ESTRUCTURAL: si es detecten DOS municipis, un comparatiu o la
# disjunció « o » entre candidats ja marca comparació («on dorm més gent, a X o a Y?»).
_COMPARE_HINT_RE = re.compile(r"\b(més|menys|más|menos|mayor|major)\b|\so\s")

# Forma de pregunta quantitativa (interrogatius de quantitat/identitat de valor).
_QUANT_RE = re.compile(
    r"\bquin(a|s|es)?\b|\bquant(a|s|es)?\b|\bqu[èé]\b|\bcu[aá]nt(a|o|as|os)?\b"
)

# Forma de llista («quins municipis…», «de quins pobles…», «a quins municipis…»).
_LIST_RE = re.compile(r"\bquin(s|es)\b.*\b(municipis|pobles)\b")

# Mots buits per a la prova de menció-nua (vegeu _is_bare_mention).
_STOPWORDS = {
    "i", "y", "o", "u", "la", "el", "els", "les", "l", "de", "del", "d", "a", "al",
    "en", "què", "que", "qué", "és", "es", "per", "hi",
}

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


def _is_bare_mention(conn: duckdb.DuckDBPyConnection, q: str, munis: list[str]) -> bool:
    """True si la consulta és essencialment NOMÉS el municipi («I Castellar del Riu?»).

    Endurit v2: abans QUALSEVOL frase amb un municipi i sense paraula quantitativa
    queia a la ruta de valor («què costa comprar un pis a Puig-reig?» responia la
    pernocta — FN greu de la sonda). Ara: es treuen les formes del nom del municipi i
    els mots buits; si queda cap paraula de contingut, NO és menció nua.
    """
    rest = q
    rows = dict(conn.execute("SELECT ine5, nom FROM municipi").fetchall())
    for ine5 in munis:
        nom = rows.get(ine5, "")
        for surface in {nom, _denom(nom)}:
            if surface:
                rest = rest.replace(surface.lower(), " ")
    tokens = re.findall(r"[a-zà-ÿ']+", rest)
    content = [t for t in tokens if t not in _STOPWORDS]
    return len(content) == 0


def route(conn: duckdb.DuckDBPyConnection, query_text: str) -> dict:
    """Encamina una consulta a les funcions existents. GENÈRIC: el desconegut cau sol.

    Retorna {intent, munis, answer_action ('respondre'|'abstenir'), text, meta}.

    Precedència (endurida v2 — vegeu el bloc de vocabulari):
      comparació (explícita O estructural amb 2 municipis) → veïns → llistes de catàleg
      → valor (indicador explícit O marc de presència; gent sola ja no basta; menció
      nua només si la consulta és NOMÉS el municipi) → indicador desconegut → per defecte.
    """
    q = (query_text or "").lower()
    munis = detect_anchors(conn, query_text, limit=2)

    # 1) Comparació: explícita («qui té més…») O estructural — DOS municipis detectats
    #    amb un comparatiu o la disjunció « o » («on dorm més gent, a X o a Y?»).
    #    v2.1: amb UN sol municipi, un «té més» NO és comparació entre municipis («la
    #    Quar té més moviment del que diu el padró?» és una pregunta de valor vs padró) —
    #    cau a la ruta de valor. Amb zero municipis, la comparació explícita es manté i
    #    respon honestament que li calen dos noms reconeguts.
    if (_COMPARE_RE.search(q) and len(munis) != 1) or (
        len(munis) == 2 and _COMPARE_HINT_RE.search(q)
    ):
        return _route_comparison(conn, query_text, munis)

    # 2) Veïns espacials («toquen», «veïns», «envolten», «fa frontera») amb un municipi.
    if any(t in q for t in NEIGHBOUR_TOKENS) and munis:
        return _route_neighbours(conn, munis[0])

    # 3) Llistes de catàleg per registre («quins municipis/pobles …»); el registre
    #    oficial també respon la seva pròpia definició («on podem contrastar…»).
    if _LIST_RE.search(q):
        if any(t in q for t in DISTRUST_LIST_TOKENS):
            return _route_register_list(conn, "soroll")
        if any(t in q for t in OFICIAL_LIST_TOKENS):
            return _route_register_list(conn, "oficial")
    if not munis and any(t in q for t in OFICIAL_LIST_TOKENS) and "contrast" in q:
        return _route_register_list(conn, "oficial")

    # Detecció de la magnitud servida (presència/pernocta). La paraula de gent SOLA ja
    # no activa la ruta de valor: cal un indicador explícit, un marc fort, o gent+marc.
    has_known = (
        any(t in q for t in EXPLICIT_VALUE_TOKENS)
        or bool(_STRONG_FRAME_RE.search(q))
        or (bool(_PEOPLE_RE.search(q)) and bool(_WEAK_FRAME_RE.search(q)))
    )
    has_quant = bool(_QUANT_RE.search(q))

    # 4) Indicador servit (o menció ESTRICTAMENT nua d'un municipi): la ruta de valor.
    if has_known or (munis and _is_bare_mention(conn, q, munis)):
        if munis:
            return _route_muni_value(conn, munis[0])
        # Indicador conegut però cap municipi entre els 31 → fora de catàleg.
        return _out(
            "municipi_desconegut", [], "abstenir",
            "No ho tinc: no reconec cap municipi dels 31 del substrat (Berguedà) en "
            "aquesta consulta.",
        )

    # 5) Pregunta quantitativa sense cap indicador servit → indicador fora de catàleg.
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
