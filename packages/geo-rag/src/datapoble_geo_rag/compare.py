"""Fase 2 · els dos usos de la regla de distingibilitat — TORCH-FREE.

Contracte: docs/experiment-rag-geo/04-fase2-distingibilitat.md. Una sola regla
(`distinguish.distinguishable`) governa TOTS DOS usos:

  1. compare() / answer_comparison() — ORDENACIÓ entre municipis. Dos munis només
     s'ordenen si les seves bandes p10–p90 NO s'encavalquen. Si s'encavalquen, s'absté
     d'ordenar (el mateix gest que l'empat de col·lisió de la Fase 1, ara per solapament
     de bandes contínues en comptes de per identitat exacta).
  2. answer() — MODULACIÓ per σ sobre UN municipi. El mateix σ (la banda) gradua el to:
     veu ferma on la banda relativa és estreta, prudent i rang ample on és àmplia. El
     `soroll` és sempre prudent (el rang inclou el propi padró).

No hi ha lògica de solapament reimplementada aquí: overlap/orderabilitat vénen NOMÉS de
distinguish. Així la comparació entre munis i la modulació per σ parlen amb una sola veu.
"""

from __future__ import annotations

import duckdb

from .descriptions import _denom, _i, join_noms
from .distinguish import distinguishable
from .retrieval import detect_anchors

# --- Modulació per σ ---------------------------------------------------------------

# S = μ − λ·σ (penalització mitjana-variància). λ tria la mà: λ=1.0 penalitza la meitat de
# l'amplada p10–p90 (perquè σ = (rang_alt − rang_baix)/2). És una tria conservadora i
# transparent, no ajustada a cap resultat.
#
# HONESTEDAT (contracte §1): S = μ − λ·σ és la penalització de risc mitjana-variància de
# Markowitz, NO una fórmula nostra. El que és nostre és que la σ és una BANDA DE FIABILITAT
# real (mig ample de la p10–p90 calibrada), no la variància introspectiva del model.
LAMBDA = 1.0

# Llindar de to sobre la banda RELATIVA (rang_rel = amplada/estimació). Al substrat, el
# registre oficial té rang_rel ≈ 0,365 i el soroll/senyal ≈ 0,57; 0,45 els separa net.
# És un llindar de PRESENTACIÓ declarat (com quedes el to), mai la veritat de la dada.
TONE_REL_THRESHOLD = 0.45


def _muni_row(conn: duckdb.DuckDBPyConnection, ine5: str) -> dict | None:
    row = conn.execute(
        "SELECT ine5, nom, register, estimacio, rang_baix, rang_alt, sigma, rang_rel "
        "FROM municipi WHERE ine5 = ?",
        [ine5],
    ).fetchone()
    if row is None:
        return None
    cols = ["ine5", "nom", "register", "estimacio", "rang_baix", "rang_alt", "sigma", "rang_rel"]
    return dict(zip(cols, row, strict=True))


# --- Ús 1: comparació entre municipis ----------------------------------------------


def compare(conn: duckdb.DuckDBPyConnection, ine5_a: str, ine5_b: str) -> dict:
    """Comparar dos municipis per la regla de distingibilitat (una, compartida).

    Retorna {distinguishable, higher, lower, note}. Si les bandes NO s'encavalquen →
    distingibles → s'ordena per `estimacio`. Si s'encavalquen → distinguishable=False,
    higher/lower=None i una nota d'abstenció d'ordenar (el mateix gest que l'empat de
    col·lisió; la col·lisió exacta n'és el cas límit a distància zero).
    """
    a = _muni_row(conn, ine5_a)
    b = _muni_row(conn, ine5_b)
    if a is None or b is None:
        missing = [x for x, r in ((ine5_a, a), (ine5_b, b)) if r is None]
        return {
            "distinguishable": False,
            "higher": None,
            "lower": None,
            "note": f"No trobo el/s municipi/s {join_noms(missing)} al substrat.",
        }

    can_order = distinguishable(a["rang_baix"], a["rang_alt"], b["rang_baix"], b["rang_alt"])

    if not can_order:
        note = (
            f"els seus intervals p10-p90 s'encavalquen "
            f"([{_i(a['rang_baix'])},{_i(a['rang_alt'])}] vs "
            f"[{_i(b['rang_baix'])},{_i(b['rang_alt'])}]); "
            f"no els puc ordenar amb confiança"
        )
        return {"distinguishable": False, "higher": None, "lower": None, "note": note}

    hi, lo = (a, b) if a["estimacio"] >= b["estimacio"] else (b, a)
    hi_nom, lo_nom = _denom(hi["nom"]), _denom(lo["nom"])
    note = (
        f"les bandes no s'encavalquen "
        f"([{_i(a['rang_baix'])},{_i(a['rang_alt'])}] vs "
        f"[{_i(b['rang_baix'])},{_i(b['rang_alt'])}]); "
        f"{hi_nom} ({_i(hi['estimacio'])}) supera {lo_nom} ({_i(lo['estimacio'])}) amb confiança"
    )
    return {
        "distinguishable": True,
        "higher": hi["ine5"],
        "lower": lo["ine5"],
        "note": note,
    }


def answer_comparison(conn: duckdb.DuckDBPyConnection, query_text: str) -> dict:
    """Respondre una consulta comparativa detectant els DOS municipis pel nom i encaminant a compare().

    Retorna {munis:[ine5...], result:{...}|None, text:str}. Si es detecten dos munis →
    compare(). Si només s'en detecta un o cap, ho diu honestament (no inventa un
    contrincant).
    """
    munis = detect_anchors(conn, query_text, limit=2)
    if len(munis) < 2:
        if len(munis) == 1:
            nom = _denom(_muni_row(conn, munis[0])["nom"])
            text = (
                f"La consulta sembla comparativa però només hi reconec un municipi ({nom}); "
                f"per comparar em calen dos noms."
            )
        else:
            text = (
                "La consulta sembla comparativa però no hi reconec cap municipi del Berguedà; "
                "per comparar em calen dos noms."
            )
        return {"munis": munis, "result": None, "text": text}

    ine5_a, ine5_b = munis[0], munis[1]
    result = compare(conn, ine5_a, ine5_b)
    nom_a = _denom(_muni_row(conn, ine5_a)["nom"])
    nom_b = _denom(_muni_row(conn, ine5_b)["nom"])
    if result["distinguishable"]:
        hi_nom = _denom(_muni_row(conn, result["higher"])["nom"])
        text = f"{hi_nom} en té més: {result['note']}."
    else:
        text = f"Entre {nom_a} i {nom_b} no puc dir qui en té més: {result['note']}."
    return {"munis": munis, "result": result, "text": text}


# --- Ús 2: modulació per σ sobre un municipi ---------------------------------------


def answer(conn: duckdb.DuckDBPyConnection, ine5: str) -> dict:
    """Resposta modulada per σ sobre UN municipi.

    Retorna {ine5, nom, register, estimacio, band:[baix,alt], sigma, rang_rel, tone,
    s_score, text}. El `tone` surt de σ (via la banda relativa): 'ferm' quan la banda és
    estreta, 'prudent' quan és àmplia; el `soroll` és sempre prudent (el rang inclou el
    padró). s_score = estimacio − LAMBDA·sigma (S = μ − λσ). El `text` és una resposta
    curta en català el to i l'amplada de la qual reflecteixen σ.
    """
    m = _muni_row(conn, ine5)
    if m is None:
        return {
            "ine5": ine5,
            "nom": None,
            "text": f"No trobo el municipi {ine5} al substrat.",
        }

    nom = _denom(m["nom"])
    est = m["estimacio"]
    baix, alt = m["rang_baix"], m["rang_alt"]
    sigma = m["sigma"]
    rang_rel = m["rang_rel"]
    register = m["register"]

    # To des de σ: soroll SEMPRE prudent; altrament ferm si la banda relativa és estreta.
    if register == "soroll" or (rang_rel is not None and rang_rel >= TONE_REL_THRESHOLD):
        tone = "prudent"
    else:
        tone = "ferm"

    s_score = est - LAMBDA * sigma

    if tone == "ferm":
        text = (
            f"{nom}: presència estimada {_i(est)} (rang {_i(baix)}–{_i(alt)}, banda estreta). "
            f"El senyal és ferm dins d'aquest marge."
        )
    else:
        noise = " — el rang inclou el propi padró, el número no es distingeix del marge" \
            if register == "soroll" else ""
        text = (
            f"{nom}: al voltant de {_i(est)}, però amb un rang ample ({_i(baix)}–{_i(alt)})"
            f"{noise}. Ho dic amb prudència: la banda és gran."
        )

    return {
        "ine5": ine5,
        "nom": nom,
        "register": register,
        "estimacio": est,
        "band": [baix, alt],
        "sigma": sigma,
        "rang_rel": rang_rel,
        "tone": tone,
        "s_score": s_score,
        "text": text,
    }
