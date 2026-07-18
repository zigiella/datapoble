"""R2 · Filtre dur DETERMINISTA + puntuació de perfil del radar de subvencions.

Contractes vinculants: ``docs/ajuntaments/C3-subvencions-perfil.md`` (fitxa,
perfil, §2bis termini NULL, §6 porta humana, §6bis seguretat) i
``docs/ajuntaments/C4-avaluacio-radar.md`` §1 (**el FN és el pecat greu**:
deixar passar una elegible és pitjor que ensenyar soroll). Input funcional:
``docs/ajuntaments/R-FUNC-radar.md`` §3 (el perfil ordena, no filtra) i §7
(casos límit).

DOCTRINA DEL FILTRE (l'asimetria mana):
  - Es descarta NOMÉS amb **evidència positiva d'exclusió** (un convocant que
    no pot ser per a nosaltres, un vocabulari de beneficiaris que exclou els
    ens públics, una restricció de població que el padró citat viola, un
    termini datat i vençut). En el dubte → PASSA (viva, sovint groga): el
    soroll és el pecat prudent; el silenci, el greu.
  - ``termini: NULL`` **MAI descarta** (C3 §2bis): vol dir «la font no en dona
    data», no «no hi ha termini» → la fitxa segueix viva marcada
    «termini per confirmar — mira l'enllaç» (mirada humana, no descart).
  - La **puntuació** (matèries×pesos + projectes en cartera) ORDENA i GRADUA;
    **no filtra mai** (R-FUNC §3): una viva amb puntuació 0 surt igualment,
    més avall i en groc.
  - Cada descartada porta el seu **motiu d'una línia** (C4 §7: auditables una
    a una, revisables en 2 minuts).

El semàfor d'aquí és el **DETERMINISTA** (stub offline-first de R-FUNC §9.1):
R3 (Haiku) el refinarà; aquest mòdul no fa cap crida de xarxa ni d'IA.

PORTA HUMANA (C3 §6): aquest mòdul NO envia res enlloc. La seva única sortida
és el dry-run local a un directori **gitignorat** (R-FUNC §9.1) amb
l'ESTRUCTURA del correu (verdes/grogues/descartades amb motius); el correu real
és R4 i només per a perfils ``actiu: true``.

Ús (dry-run local, la «ordre única» del R-FUNC §9.1):

    python -m datapoble_signals.subvencions_match \
        --data 2026-07-01 --perfil 08166 --sortida out/ \
        [--font data/subvencions/subvencions_bergueda.parquet | fixtures.json]

TRAMPES CONEGUDES QUE AQUEST MÒDUL EXERCEIX (tests):
  - «Sant Salvador de Guardiola» (Bages) ≠ «Guardiola de Berguedà»: el match de
    noms de convocants municipals és per nom COMPLET normalitzat, mai per
    subcadena d'un tros del nom.
  - L'àmbit ``estatal`` EXISTEIX i passa el filtre territorial si el perfil el
    porta (decisió de R1 ratificada: excloure'l seria un FN de sistema).
  - El filtre ``organos`` de la BDNS **no cascada** (germà de la trampa de
    regions, àncora de R1.5): per això aquí el convocant es llegeix del TEXT
    COMPLET d'``organisme`` (tots els nivells « · »), mai d'un sol nivell.
  - Les restriccions per població s'apliquen amb el **padró citat al perfil**
    (``poblacio`` + ``poblacio_any``), i el motiu del descart el cita.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from .municipis import BERGUEDA_INE5, comarca_from_organ
from .subvencions_bdns import clau_identitat, normalitza_text

# --- vocabulari BDNS de beneficiaris (tancat, 5 tipus; vegeu R1) --------------
# Un ajuntament és una persona jurídica PÚBLICA sense activitat econòmica: només
# hi pot concórrer on la font declara aquest tipus (o no declara res / «sin
# información» → prudència: passa). Els altres tipus són empresa/persones
# físiques → evidència positiva d'exclusió.
_BENEFICIARIS_COMPATIBLES = (
    "juridicas que no desarrollan actividad economica",
    "sin informacion",
)

# --- patrons de concessió no concurrent (R-FUNC §7: «el filtre dur les mata») --
_PATRONS_NOMINATIVA = (
    "nominativ",            # nominativa/nominatives/nominativo/nominativas
    "concesion directa",
    "concessio directa",
)

# --- restriccions de població al text de l'objecte ----------------------------
# Determinista i conservador: només dispara amb el patró complet
# «<subjecte local> de más/menos de N habitantes» (ca/es). La resta, ni cas.
_RE_POBLACIO = re.compile(
    r"(?:municipios|municipis|ayuntamientos|ajuntaments|entidades locales|"
    r"entitats locals|poblaciones|localidades|localitats)\s+"
    r"(?:de\s+)?(?:poblacion\s+)?"
    r"(mas de|menos de|mes de|menys de|superiores? a|inferiors? a|inferiores? a)\s+"
    r"([\d][\d.,]*)\s*(?:habitantes|habitants|hab\b)",
)

# Províncies conegudes per a la regla de diputacions (normalitzades).
_RE_DIPUTACIO = re.compile(
    r"diputaci\w*\s+(?:prov\w*\.?\s+|foral\s+)?(?:de\s+|d')?([a-z' -]+?)(?:\s*·|$)"
)

# Paraules buides per a la tokenització de matèries/projectes.
_STOPWORDS = frozenset(
    "de la el els les i y per para en dels las los amb con que a o u d l del al "
    "un una uns unes lo als se es sus seus seves su".split()
)

# --- lèxic ca↔es per token (v1, curt i transparent) ---------------------------
# El matching és LÈXIC i declarat com a tal: cada token significatiu d'una
# matèria o d'un projecte s'expandeix amb aquest lèxic (si hi és) i es busca
# com a PREFIX DE PARAULA (\b + prefix) al text normalitzat de l'objecte.
# «cultura» NO matxeja «agricultura» (no hi ha límit de paraula); «cultural»
# sí (prefix). El judici semàntic fi és de R3 (Haiku), no d'aquí.
_TOKEN_LEXICON: dict[str, tuple[str, ...]] = {
    "turisme": ("turis",),                       # turisme/turismo/turístic/turista
    "patrimoni": ("patrimoni",),                 # patrimoni/patrimonio/patrimonial
    "envelliment": ("envelliment", "envejecimiento", "gent gran", "gente mayor",
                     "persones grans", "personas mayores", "tercera edat",
                     "tercera edad", "dependencia"),
    "socials": ("serveis socials", "servicios sociales", "accio social",
                 "accion social", "benestar social", "bienestar social",
                 "inclusio social", "inclusion social"),
    "eficiencia": ("eficiencia",),
    "energetica": ("energetic", "energia renovable", "autoconsum", "autoconsumo",
                    "fotovoltaic",),
    "enllumenat": ("enllumenat", "alumbrado", "iluminacion", "il luminacio"),
    "digitalitzacio": ("digital",),              # digitalització/digitalización/digital
    "administracio": ("administracio electronica", "administracion electronica",
                       "govern obert", "gobierno abierto", "ciberseguretat",
                       "ciberseguridad", "dades obertes", "datos abiertos"),
    "cultura": ("cultura",),                     # cultura/cultural (prefix, no *agri*cultura)
    "memoria": ("memoria",),
    "camins": ("camin", "sender", "vies verdes", "vias verdes"),
    "natura": ("natura", "medi natural", "medio natural", "forestal",
                "biodiversitat", "biodiversidad"),
    "publics": ("espais publics", "espacios publicos", "espai public",
                 "espacio publico"),
    "habitatge": ("habitatge", "vivienda", "rehabilitacio", "rehabilitacion",
                   "lloguer", "alquiler"),
    "ocupacio": ("ocupacio", "empleo", "insercio laboral", "insercion laboral"),
    "promocio": ("promocio economica", "promocion economica", "emprenedoria",
                  "emprendimiento", "comerc local", "comercio local"),
    # tokens freqüents de projectes en cartera
    "millora": ("millora", "mejora"),
    "public": ("public",),                       # públic/pública/público/pública
    "arxiu": ("arxiu", "archivo"),
    "guia": ("guia",),                           # guia/guía/guias/guies
    "multilingue": ("multilingu",),
    "videoactes": ("videoact",),
    "transparencia": ("transparencia",),
}

_MIN_TOKEN = 4  # tokens més curts no discriminen (sorolls tipus «pla», «ple»)


# ==============================================================================
# utilitats de matching
# ==============================================================================

def _tokens_significatius(text: str) -> list[str]:
    return [
        t for t in normalitza_text(text).replace(",", " ").split()
        if len(t) >= _MIN_TOKEN and t not in _STOPWORDS
    ]


def _expansions(token: str) -> tuple[str, ...]:
    """Les formes que compten com a presència del token (lèxic v1 o ell mateix)."""
    return _TOKEN_LEXICON.get(token, (token,))


def _hi_es(expansio: str, text_norm: str) -> bool:
    """Prefix de paraula: «cultura» ∈ «actividades culturales», ∉ «agricultura»."""
    return re.search(r"\b" + re.escape(expansio), text_norm) is not None


def _matxeja_materia(nom_materia: str, text_norm: str) -> bool:
    """Una matèria matxeja si QUALSEVOL expansió de QUALSEVOL token hi és."""
    return any(
        _hi_es(exp, text_norm)
        for tok in _tokens_significatius(nom_materia)
        for exp in _expansions(tok)
    )


def _matxeja_projecte(projecte: str, text_norm: str) -> bool:
    """Un projecte matxeja si ≥2 dels seus tokens hi són (o l'únic que té).

    Més estricte que la matèria: els projectes són frases concretes i UN sol
    token compartit (p. ex. «guia») seria soroll d'ordenació.
    """
    tokens = _tokens_significatius(projecte)
    if not tokens:
        return False
    hits = sum(
        1 for tok in tokens if any(_hi_es(exp, text_norm) for exp in _expansions(tok))
    )
    return hits >= min(2, len(tokens))


# ==============================================================================
# les portes del filtre dur (cada una: motiu d'una línia o None = passa)
# ==============================================================================

def _nom_municipi_normalitzat(nom: str) -> str:
    """«BISBAL D'EMPORDÀ, LA» → «la bisbal d'emporda» normalitzat BDNS↔local.

    La BDNS posposa l'article («X, LA»); el desfem per comparar noms COMPLETS.
    """
    n = normalitza_text(nom)
    m = re.match(r"^(.*),\s*(la|el|les|els|l'|los|las)$", n)
    if m:
        n = f"{m.group(2)} {m.group(1)}"
    return " ".join(n.replace("’", "'").split())


def _gate_convocant(fitxa: dict, perfil: dict) -> str | None:
    """Descarta per CONVOCANT amb àmbit propi aliè (evidència positiva).

    Es llegeix el text COMPLET d'``organisme`` (tots els nivells « · »): el
    filtre ``organos`` de la BDNS no cascada i cap nivell per si sol és fiable.
    """
    org = normalitza_text(fitxa.get("organisme"))
    if not org:
        return None
    nom_perfil = _nom_municipi_normalitzat(BERGUEDA_INE5.get(perfil.get("ine5", ""), ""))

    # 1 · Ajuntaments: les seves convocatòries són per al SEU àmbit local (veïns,
    # entitats i empreses del municipi) — un altre ajuntament no hi concorre.
    m = re.search(r"\b(?:ayuntamiento|ajuntament)\s+(?:de\s+|d')\s*([^·]+)", org)
    if m:
        nom_conv = _nom_municipi_normalitzat(m.group(1).strip())
        if nom_perfil and nom_conv == nom_perfil:
            return "convocant: el mateix ajuntament (no és una oportunitat externa)"
        return f"convocant municipal aliè ({nom_conv}): ajuts de l'àmbit local propi"

    # 2 · Consells comarcals: es queda NOMÉS el de la comarca del perfil.
    if "consell comarcal" in org or "consejo comarcal" in org:
        comarca = comarca_from_organ(fitxa.get("organisme"))
        comarques_perfil = {
            t.split(":", 1)[1] for t in perfil.get("territori", []) if t.startswith("comarca:")
        }
        if comarca and normalitza_text(comarca) not in comarques_perfil:
            return f"convocant: consell comarcal d'una altra comarca ({comarca})"
        return None  # el del Berguedà (o indeterminable) passa

    # 3 · Diputacions: es queda NOMÉS la de la província del perfil.
    if "diputaci" in org:
        provincies_perfil = {
            t.split(":", 1)[1] for t in perfil.get("territori", []) if t.startswith("provincia:")
        }
        m = _RE_DIPUTACIO.search(org)
        if m:
            prov = m.group(1).strip()
            if prov and not any(p in prov or prov in p for p in provincies_perfil):
                return f"convocant: diputació d'una altra província ({prov})"
        return None  # la del perfil (o inextraïble) passa — prudència

    # 4 · Àrea Metropolitana de Barcelona: cap muni del Berguedà n'és membre (v1).
    if "area metropolitana" in org:
        return "convocant: Àrea Metropolitana de Barcelona (el municipi no n'és membre)"

    # 5 · Governs d'altres comunitats autònomes (format «AUTONOMICA · <CCAA> · …»).
    parts = [p.strip() for p in org.split("·")]
    if len(parts) >= 2 and parts[0] == "autonomica":
        if parts[1] not in ("cataluna", "catalunya", "catalua"):
            return f"convocant autonòmic d'una altra comunitat ({parts[1]})"

    return None


def _gate_beneficiaris(fitxa: dict) -> str | None:
    """Descarta si el vocabulari (tancat) de la BDNS EXCLOU els ens públics."""
    ben = normalitza_text(fitxa.get("beneficiaris"))
    if not ben:
        return None  # la font no ho declara → prudència: passa (R3/humà decideix)
    if any(pat in ben for pat in _BENEFICIARIS_COMPATIBLES):
        return None
    return (
        "beneficiaris: cap tipus compatible amb un ajuntament "
        f"(la font declara: {fitxa.get('beneficiaris')})"
    )


def _gate_nominativa(fitxa: dict) -> str | None:
    """Concessions nominatives/directes: no hi ha concurrència (R-FUNC §7)."""
    obj = normalitza_text(fitxa.get("objecte"))
    for pat in _PATRONS_NOMINATIVA:
        if pat in obj:
            return "concessió nominativa/directa: no és de concurrència (R-FUNC §7)"
    return None


def _gate_ambit(fitxa: dict, perfil: dict) -> tuple[str | None, list[str]]:
    """L'àmbit territorial declarat ha d'encaixar amb el ``territori`` del perfil.

    Només descarta per MISMATCH POSITIU (l'etiqueta requerida no és al perfil).
    La BDNS no baixa de NUTS3: «provincia» no diu QUINA → passa amb prudència
    (la regla de diputacions ja ha caçat les alienes identificables); «comarca»
    i «municipi» (futur CIDO) passen amb nota si no es poden verificar.
    """
    ambit = (fitxa.get("ambit_territorial") or "").strip()
    territori = perfil.get("territori", [])
    notes: list[str] = []

    if ambit == "estatal":
        if "estatal" not in territori:
            return "àmbit estatal fora del territori del perfil", notes
    elif ambit == "CAT":
        if "catalunya" not in territori:
            return "àmbit Catalunya fora del territori del perfil", notes
    elif ambit == "provincia":
        provincies = [t.split(":", 1)[1] for t in territori if t.startswith("provincia:")]
        if not provincies:
            return "àmbit provincial fora del territori del perfil", notes
        # La BDNS no baixa de NUTS3 i la fitxa no diu QUINA província; si el
        # CONVOCANT la resol (p. ex. «DIPUTACIÓN PROV. DE BARCELONA» amb el
        # perfil provincia:barcelona), no hi ha dubte. Si no, nota de prudència.
        org = normalitza_text(fitxa.get("organisme"))
        if not any(p in org for p in provincies):
            notes.append("la font no concreta la província (BDNS no baixa de NUTS3)")
    elif ambit == "comarca":
        if not any(t.startswith("comarca:") for t in territori):
            return "àmbit comarcal fora del territori del perfil", notes
        notes.append("àmbit comarcal: verifica a l'enllaç que és la comarca del perfil")
    elif ambit == "municipi":
        if not any(t.startswith("municipi:") for t in territori):
            return "àmbit municipal fora del territori del perfil", notes
        notes.append("àmbit municipal: verifica a l'enllaç que és el municipi del perfil")

    return None, notes


def _gate_poblacio(fitxa: dict, perfil: dict) -> str | None:
    """Restriccions de població al text, aplicades amb el PADRÓ CITAT al perfil."""
    obj = normalitza_text(fitxa.get("objecte"))
    m = _RE_POBLACIO.search(obj)
    if not m:
        return None
    direccio, llindar_txt = m.group(1), m.group(2)
    llindar = int(re.sub(r"[.,]", "", llindar_txt))
    poblacio = perfil["poblacio"]
    cita = f"{BERGUEDA_INE5.get(perfil.get('ine5', ''), 'el municipi')}: {poblacio} hab (padró {perfil['poblacio_any']})"
    if direccio in ("mas de", "mes de") or direccio.startswith("superior"):
        if poblacio <= llindar:
            return f"restricció de població: reservada a >{llindar} hab — {cita}"
    else:  # menos de / menys de / inferior a
        if poblacio >= llindar:
            return f"restricció de població: reservada a <{llindar} hab — {cita}"
    return None


def _data_vista_min(fitxa: dict) -> date | None:
    """La primera data en què alguna font va veure la fitxa (per datar el flag)."""
    vistes = []
    for f in fitxa.get("fonts") or []:
        dv = f.get("data_vista")
        if dv:
            try:
                vistes.append(date.fromisoformat(str(dv)[:10]))
            except ValueError:
                continue
    return min(vistes) if vistes else None


def _gate_vigencia(fitxa: dict, data_referencia: date) -> tuple[str | None, list[str], int | None, bool]:
    """Vigència a la DATA DE REFERÈNCIA (C4 §2: el banc jutja a data_publicacio).

    Retorna (motiu_descart | None, notes, marge_dies | None, termini_per_confirmar).

    Regles:
      - ``anul·lada`` → descartada (la font l'ha retirat).
      - termini DATAT i < referència → descartada (vençuda ALESHORES).
      - termini DATAT i ≥ referència → viva (marge en dies naturals).
      - termini NULL → **MAI descarta per si sol** (C3 §2bis): viva amb
        «termini per confirmar — mira l'enllaç».
      - ``estat: tancada`` (el flag ``abierto=false`` de la font) només mana si
        era VIGENT a la referència (data_vista ≤ referència): en el run diari
        (referència = avui = captura) descarta — «m'hi puc presentar?» és
        exactament el que declara la font (R1); en mode banc (referència =
        data_publicacio, anterior a la captura) el flag és posterior al judici
        → nota, no descart (si no, tota la capa B tancada-per-edat seria FN).
    """
    notes: list[str] = []
    estat = (fitxa.get("estat") or "").strip()
    if estat == "anul·lada":
        return "anul·lada per la font", notes, None, False

    termini_raw = fitxa.get("termini")
    termini: date | None = None
    if termini_raw:
        termini = date.fromisoformat(str(termini_raw)[:10])

    if termini is not None and termini < data_referencia:
        return f"termini vençut el {termini.isoformat()} (a la data de referència)", notes, None, False

    flag_vigent = True
    dv = _data_vista_min(fitxa)
    if dv is not None and data_referencia < dv:
        flag_vigent = False  # el flag es va capturar DESPRÉS del dia que jutgem

    if estat == "tancada":
        if flag_vigent:
            extra = f" (tot i termini {termini.isoformat()})" if termini else ""
            return f"la font la marca tancada (abierto=false){extra}", notes, None, False
        notes.append("la font la marcava tancada en la captura (posterior a la data de referència)")

    marge = (termini - data_referencia).days if termini is not None else None
    per_confirmar = termini is None
    if per_confirmar:
        notes.append("termini per confirmar — mira l'enllaç (la font no en dona data; C3 §2bis)")
    return None, notes, marge, per_confirmar


# ==============================================================================
# puntuació (ordena i gradua; MAI filtra — R-FUNC §3)
# ==============================================================================

def puntua(fitxa: dict, perfil: dict) -> dict[str, Any]:
    """Puntuació DETERMINISTA de perfil: matèries×pesos + projectes en cartera.

    ``puntuacio`` = màxim pes de les matèries amb match (+0,3 si algun projecte
    en cartera matxeja). Només serveix per ORDENAR el correu i graduar el
    semàfor determinista; el filtre no la mira mai.
    """
    text = normalitza_text(f"{fitxa.get('objecte') or ''} {fitxa.get('organisme') or ''}")
    materies_hit = [
        m for m in perfil.get("materies", []) if _matxeja_materia(m["nom"], text)
    ]
    projectes_hit = [
        p for p in perfil.get("projectes_en_cartera", []) if _matxeja_projecte(p, text)
    ]
    base = max((float(m["pes"]) for m in materies_hit), default=0.0)
    puntuacio = round(base + (0.3 if projectes_hit else 0.0), 2)

    trossos = []
    if materies_hit:
        millors = sorted(materies_hit, key=lambda m: -float(m["pes"]))
        trossos.append(
            " + ".join(f"matèria «{m['nom']}» (pes {float(m['pes']):.1f})" for m in millors[:2])
        )
    if projectes_hit:
        trossos.append("projecte en cartera: " + " · ".join(f"«{p}»" for p in projectes_hit[:2]))
    explicacio = " + ".join(trossos) if trossos else \
        "cap matèria del perfil hi encaixa (puntuació 0) — surt igualment: la puntuació no filtra"

    return {
        "puntuacio": puntuacio,
        "materies": [{"nom": m["nom"], "pes": float(m["pes"])} for m in materies_hit],
        "projectes": projectes_hit,
        "explicacio": explicacio,
    }


# ==============================================================================
# avaluació d'una fitxa + filtre del lot
# ==============================================================================

def avalua(fitxa: dict, perfil: dict, *, data_referencia: date) -> dict[str, Any]:
    """Passa UNA fitxa C3 pel filtre dur i, si viu, la puntua i gradua.

    Retorna el veredicte auditable: descartada (amb motiu d'una línia) o viva
    (amb semàfor determinista, puntuació, marge i explicació).
    """
    base = {
        "clau": clau_identitat(fitxa),
        "organisme": fitxa.get("organisme"),
        "objecte": fitxa.get("objecte"),
        "enllac": fitxa.get("enllac"),
    }

    for gate, nom in (
        (lambda: _gate_convocant(fitxa, perfil), "convocant"),
        (lambda: _gate_beneficiaris(fitxa), "beneficiaris"),
        (lambda: _gate_nominativa(fitxa), "tipus"),
        (lambda: _gate_poblacio(fitxa, perfil), "poblacio"),
    ):
        motiu = gate()
        if motiu:
            return {**base, "veredicte": "descartada", "porta": nom, "motiu": motiu}

    motiu, notes_ambit = _gate_ambit(fitxa, perfil)
    if motiu:
        return {**base, "veredicte": "descartada", "porta": "ambit", "motiu": motiu}

    motiu, notes_vig, marge, per_confirmar = _gate_vigencia(fitxa, data_referencia)
    if motiu:
        return {**base, "veredicte": "descartada", "porta": "vigencia", "motiu": motiu}

    notes = notes_ambit + notes_vig
    score = puntua(fitxa, perfil)

    # Semàfor DETERMINISTA (stub de R3, R-FUNC Annex A): verd només amb lligam
    # fort (matèria pes ≥ 0,7 o projecte en cartera) I termini datat viu I cap
    # nota de dubte. La resta, groc: es mira si hi ha temps — mai silenci.
    lligam_fort = bool(score["projectes"]) or any(m["pes"] >= 0.7 for m in score["materies"])
    semafor = "verd" if (lligam_fort and marge is not None and not notes) else "groc"

    return {
        **base,
        "veredicte": "viva",
        "semafor_determinista": semafor,
        "puntuacio": score["puntuacio"],
        "materies": score["materies"],
        "projectes": score["projectes"],
        "explicacio": score["explicacio"],
        "import": fitxa.get("import"),
        "termini": fitxa.get("termini"),
        "marge_dies": marge,
        "termini_per_confirmar": per_confirmar,
        "notes": notes,
        "estat": fitxa.get("estat"),
    }


def filtra(
    fitxes: list[dict], perfil: dict, *, data_referencia: date
) -> dict[str, list[dict]]:
    """Aplica el filtre a un lot i ordena les vives per utilitat.

    Ordenació (R-FUNC §4): verdes primer; dins de cada semàfor, puntuació alta
    primer i, a igual puntuació, MENYS marge primer (l'urgent amunt); les de
    termini per confirmar, al final del seu bloc. Ordre total i determinista
    (desempat per clau).
    """
    vives: list[dict] = []
    descartades: list[dict] = []
    for f in fitxes:
        v = avalua(f, perfil, data_referencia=data_referencia)
        (vives if v["veredicte"] == "viva" else descartades).append(v)

    def _ordre(v: dict) -> tuple:
        return (
            0 if v["semafor_determinista"] == "verd" else 1,
            -v["puntuacio"],
            v["marge_dies"] if v["marge_dies"] is not None else 10_000,
            v["clau"],
        )

    vives.sort(key=_ordre)
    descartades.sort(key=lambda d: d["clau"])
    return {"vives": vives, "descartades": descartades}


# ==============================================================================
# dry-run local (R-FUNC §9.1: en dev, el radar no envia — ESCRIU)
# ==============================================================================

def _trunca(text: str | None, n: int = 120) -> str:
    t = (text or "").strip().replace("\n", " ")
    return t if len(t) <= n else t[: n - 1] + "…"


def _md_dry_run(resultat: dict, perfil: dict, data_referencia: date) -> str:
    """L'ESTRUCTURA del correu (R-FUNC §4) en Markdown auditable.

    NO és el correu de R4: és el dry-run que permet llegir en 2 minuts què
    hauria sortit i per què — verdes amb el seu perquè, grogues amb el dubte,
    descartades amb el motiu d'una línia (C4 §7).
    """
    ine5 = perfil.get("ine5", "?????")
    nom = BERGUEDA_INE5.get(ine5, ine5)
    vives = resultat["vives"]
    verdes = [v for v in vives if v["semafor_determinista"] == "verd"]
    grogues = [v for v in vives if v["semafor_determinista"] == "groc"]
    desc = resultat["descartades"]

    linies: list[str] = []
    linies.append(
        f"# Radar subvencions · {data_referencia.isoformat()} · {nom} ({ine5}) · "
        f"{len(verdes)} verdes, {len(grogues)} grogues, {len(desc)} descartades"
    )
    linies.append("")
    linies.append(
        f"_Dry-run local (R-FUNC §9.1) · semàfor DETERMINISTA (stub de R3) · "
        f"perfil `actiu: {str(perfil['actiu']).lower()}` → sortida real "
        f"{'autoritzada NOMÉS via R4' if perfil['actiu'] else 'NO autoritzada (perfil dorment, C3 §3)'}_"
    )

    def _bloc(titol: str, items: list[dict]) -> None:
        linies.append("")
        linies.append(f"## {titol}")
        if not items:
            linies.append("_(cap)_")
        for v in items:
            marge = (
                f"{v['marge_dies']} dies de marge" if v["marge_dies"] is not None
                else "termini per confirmar — mira l'enllaç"
            )
            imp = f"{v['import']:,.0f} €".replace(",", ".") if v.get("import") else "import n.d."
            linies.append(f"- **{_trunca(v['objecte'], 110)}**")
            linies.append(f"  {v['organisme']}")
            linies.append(
                f"  {imp} · termini: {v['termini'] or 'n.d.'} ({marge}) · puntuació {v['puntuacio']:.2f}"
            )
            linies.append(f"  Per què: {v['explicacio']}")
            for n_ in v["notes"]:
                linies.append(f"  ⚠ {n_}")
            linies.append(f"  → {v['enllac']}")

    _bloc("🟢 Verdes", verdes)
    _bloc("🟡 Grogues (mirar si hi ha temps)", grogues)

    linies.append("")
    linies.append(f"## ⚪ Descartades ({len(desc)}) — un motiu per línia, revisable en 2 minuts")
    if not desc:
        linies.append("_(cap)_")
    for d in desc:
        linies.append(f"- {_trunca(d['organisme'], 60)} — {_trunca(d['objecte'], 80)} → **{d['motiu']}**")
    linies.append("")
    return "\n".join(linies)


def _carrega_fitxes(font: Path) -> list[dict]:
    """Fitxes C3 des d'un parquet (producció R1) o d'un JSON de fixtures (dev).

    El JSON pot ser: (a) una llista de fitxes C3 ja normalitzades, o (b) el
    format d'arxiu cru de R1 ``{"convocatories": [{"busqueda", "detall"}]}``,
    que es normalitza aquí amb el MATEIX ``normalize`` del connector
    (``_meta.data_vista`` fixa la data de captura → replay determinista).
    """
    if not font.exists():
        raise SystemExit(
            f"FALLA: no existeix {font}. Genera el parquet amb la ingesta R1 "
            "(python -m datapoble_signals.subvencions_bdns) o passa --font amb "
            "un JSON de fixtures rejugables."
        )
    if font.suffix == ".parquet":
        import duckdb

        con = duckdb.connect()
        try:
            df = con.execute("SELECT * FROM read_parquet(?)", [str(font)]).fetchdf()
        finally:
            con.close()
        fitxes = df.to_dict("records")
        for f in fitxes:
            for camp in ("data_publicacio", "termini"):
                if f.get(camp) is not None and not isinstance(f[camp], str):
                    f[camp] = None if str(f[camp]) in ("NaT", "None") else str(f[camp])[:10]
            fonts_val = f.get("fonts")
            if fonts_val is not None and not isinstance(fonts_val, list):
                f["fonts"] = list(fonts_val)
        return fitxes

    doc = json.loads(font.read_text(encoding="utf-8"))
    if isinstance(doc, list):
        return doc
    from .subvencions_bdns import dedupe, normalize

    vist_el = (doc.get("_meta") or {}).get("data_vista")
    fitxes = [
        normalize(c["detall"], c.get("busqueda"), vist_el=vist_el)
        for c in doc.get("convocatories", [])
    ]
    return dedupe(fitxes)


def dry_run(
    *,
    data_referencia: date,
    ine5: str,
    sortida: Path,
    fitxes: list[dict] | None = None,
    font: Path | None = None,
    config_dir: Path | None = None,
) -> dict[str, Any]:
    """El dry-run del R-FUNC §9.1: filtra, puntua i ESCRIU (mai envia).

    Escriu ``radar-<ine5>-<data>.md`` (estructura del correu) i ``.json``
    (veredictes complets, auditables) al directori ``sortida`` — que ha de ser
    local i gitignorat (``out/``). Cap timestamp de rellotge: mateixos inputs,
    mateixos bytes (fixtures rejugables → snapshot test).
    """
    from .perfils import CONFIG_MUNICIPIS_DIR, carrega_perfil_per_ine5

    perfil = carrega_perfil_per_ine5(ine5, config_dir=config_dir or CONFIG_MUNICIPIS_DIR)
    if fitxes is None:
        if font is None:
            from .config import subvencions_path

            font = subvencions_path("subvencions_bergueda.parquet")
        fitxes = _carrega_fitxes(Path(font))

    resultat = filtra(fitxes, perfil, data_referencia=data_referencia)
    vives = resultat["vives"]
    verdes = [v for v in vives if v["semafor_determinista"] == "verd"]

    sortida.mkdir(parents=True, exist_ok=True)
    base = f"radar-{ine5}-{data_referencia.isoformat()}"
    md = _md_dry_run(resultat, perfil, data_referencia)
    # newline="\n": bytes idèntics a qualsevol plataforma (el snapshot compara
    # contra el golden; sense això, Windows escriuria CRLF i el CI LF).
    (sortida / f"{base}.md").write_text(md, encoding="utf-8", newline="\n")

    payload = {
        "perfil": ine5,
        "data_referencia": data_referencia.isoformat(),
        "actiu": perfil["actiu"],
        # PORTA HUMANA (C3 §3/§6): la sortida real (correu R4) només existeix
        # per a perfils actius — i mai des d'aquest mòdul.
        "sortida_autoritzada": bool(perfil["actiu"]),
        "n_fitxes": len(fitxes),
        "n_verdes": len(verdes),
        "n_grogues": len(vives) - len(verdes),
        "n_descartades": len(resultat["descartades"]),
        "vives": vives,
        "descartades": resultat["descartades"],
    }
    (sortida / f"{base}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="datapoble_signals.subvencions_match",
        description="R2 · dry-run local del radar (filtra+puntua+escriu; MAI envia — C3 §6)",
    )
    ap.add_argument("--data", required=True, help="data de referència (ISO, p. ex. 2026-07-01)")
    ap.add_argument("--perfil", required=True, help="INE5 del perfil (p. ex. 08166)")
    ap.add_argument("--sortida", default="out/", help="directori LOCAL gitignorat (default: out/)")
    ap.add_argument(
        "--font",
        default=None,
        help="parquet C3 o JSON de fixtures rejugables (default: data/subvencions/subvencions_bergueda.parquet)",
    )
    args = ap.parse_args(argv)

    resum = dry_run(
        data_referencia=date.fromisoformat(args.data),
        ine5=args.perfil,
        sortida=Path(args.sortida),
        font=Path(args.font) if args.font else None,
    )
    resum_curt = {k: v for k, v in resum.items() if not isinstance(v, list)}
    print(json.dumps(resum_curt, ensure_ascii=False, indent=2))
    if not resum["sortida_autoritzada"]:
        print(
            f"[R2] perfil {args.perfil} dorment (actiu: false): dry-run escrit; "
            "CAP sortida real autoritzada (C3 §3).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
