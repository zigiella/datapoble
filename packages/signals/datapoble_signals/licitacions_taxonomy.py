"""Taxonomia territorial de licitacions (pas 1 de la capa d'intel·ligència).

> «Una licitació és una **confessió administrativa**.» — la consultora.

Aquest mòdul **NO** substitueix ``taxonomy.py`` (que segueix sent el contracte de
la taula ``events``: el ``tipus_senyal`` CPV+paraules). Hi afegeix, **per damunt**,
tres lectures pròpies del territori que el CPV sol no dona, perquè el CPV descriu
*què es compra* però no *què revela* d'un municipi:

  1. ``tema_administratiu`` — 12-15 temes de govern local (residus, aigua, turisme,
     mobilitat, habitatge, digitalitzacio, social, cultura, educacio, seguretat,
     manteniment, energia, urbanisme, administracio, salut, altres). Més fi i més
     **territorial** que les 6 famílies de ``tipus_senyal``.
  2. ``caracter_senyal`` — ``ordinari | reforç | emergencia | transformacio |
     promocio | diagnostic``. Separa el **metabolisme normal** d'un municipi (el
     que gasta cada any per existir) de la **tensió** (el que delata un problema o
     una aposta). Es deriva del **verb de l'objecte**, no del CPV.
  3. ``contract_signal_type`` — ``evidencia_directa | proxy_fort | proxy_feble |
     nomes_context``. La **força com a senyal territorial**: contractar socorrisme
     de platja fluvial és evidència directa d'ús recreatiu; contractar material
     d'oficina no diu res del territori (només context administratiu).

HONEST BOUNDARY (innegociable, disciplina de Talaia): tot això és **heurística**.
El senyal fort segueix sent el **CPV**; sense CPV caiem a **paraules clau** sobre
l'objecte (sorollós) i, si res casa, a ``altres`` (calaix gran **a propòsit**). Cada
classificació porta la seva ``confianca`` i el ``metode`` que la justifica. El
refinament fi (LLM sobre ``altres`` + validació manual de 300 contractes) és el
**PAS 2**, no aquí.

Les funcions són **pures** (sense xarxa ni estat) → fàcils de testejar i auditar.
"""
from __future__ import annotations

import re
import unicodedata

# --- Vocabularis controlats (la sortida de la capa) --------------------------

# Tema administratiu: l'àrea de govern local que el contracte revela.
TEMES_ADMINISTRATIUS = (
    "residus",          # neteja viària, recollida, deixalleria, clavegueram
    "aigua",            # abastament, potabilització, dipòsits, EDAR
    "turisme",          # promoció turística, fires, visitants, rutes, senyalització turística
    "cultura",          # Patum, festes, museus, patrimoni, espectacles, arxiu
    "mobilitat",        # carreteres, vials, transport (no escolar), aparcament, senyalització viària
    "habitatge",        # habitatge públic, rehabilitació residencial, lloguer social
    "urbanisme",        # planejament, obra pública d'espai urbà, enllumenat (obra), parcs
    "manteniment",      # reparacions, conservació d'edificis/instal·lacions, neteja d'edificis
    "energia",          # fotovoltaica, eficiència energètica, subministrament elèctric/gas
    "social",           # serveis socials, gent gran, infància, inclusió, mediació, dependència
    "educacio",         # transport escolar, menjador escolar, tallers educatius, escola bressol
    "salut",            # salut mental, sanitari, material mèdic, prevenció
    "seguretat",        # vigilància, socorrisme, protecció civil, emergències, policia
    "digitalitzacio",   # programari, web, IT, connectivitat, administració electrònica
    "administracio",    # serveis jurídics, auditoria, consultoria genèrica, subministraments d'oficina
    "altres",           # cap senyal clar (residual honest)
)

# Caràcter del senyal: metabolisme normal vs tensió/aposta.
CARACTERS_SENYAL = (
    "ordinari",        # servei recurrent que sosté el funcionament normal
    "reforç",          # ampliació/ref0rç d'un servei existent (més del mateix)
    "emergencia",      # urgència, dany, reparació no planificada (apaga incendis)
    "transformacio",   # inversió estructural nova (obra, redacció de projecte, pla)
    "promocio",        # màrqueting, captació, projecció exterior (aposta de visibilitat)
    "diagnostic",      # estudi, anàlisi, auditoria, redacció (entendre abans d'actuar)
)

# Tipus de senyal territorial: quanta intel·ligència de territori aporta.
CONTRACT_SIGNAL_TYPES = (
    "evidencia_directa",  # el contracte ÉS la prova del fenomen al territori
    "proxy_fort",         # indici robust del fenomen (CPV temàtic clar)
    "proxy_feble",        # indici sorollós (només paraula clau, o tema genèric)
    "nomes_context",      # administratiu pur: no diu res del territori
)


def _norm(text: str | None) -> str:
    """Minúscules, sense accents, **apòstrofs i puntuació com a separadors**, espais
    col·lapsats. Per a matching robust de paraules clau.

    Tractem apòstrofs (``'`` ``’``), guions i punts com a espais perquè
    «d'abastament d'aigua» casi amb la clau «abastament d aigua» (les claus
    s'escriuen amb espais, no amb apòstrofs). El mojibake de la font (``�``)
    sobreviu com a caràcter qualsevol; no trenca el matching perquè cerquem
    subcadenes de paraules netes que solen quedar intactes.
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    # Apòstrofs i separadors -> espai (per a matching de subcadenes amb espais).
    t = re.sub(r"[''`´·.\-_/]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _cpv_codes(cpv_raw: str | None) -> list[str]:
    """Separa un CPV cru en codis (la font concatena amb ``||``)."""
    if not cpv_raw:
        return []
    return [c.strip() for c in str(cpv_raw).split("||") if c.strip()]


def _cpv_digits(code: str) -> str:
    """'90511000-2' -> '905110002' (només dígits, per a matching per prefix)."""
    return re.sub(r"[^0-9]", "", code)


# =============================================================================
# 1) tema_administratiu
# =============================================================================
#
# Estratègia: **CPV primer** (prefix de família, evidència forta), i quan el CPV és
# ambigu o absent, **paraules clau** sobre l'objecte (evidència feble). Alguns CPV
# són intrínsecament ambigus al sector públic local —``60`` transport pot ser bus
# escolar (educacio) o transport públic (mobilitat); ``45`` obra pot ser vial,
# aigua o esport— → per a aquests, la paraula clau de l'objecte DESEMPATA abans que
# el CPV genèric. Verificat sobre l'objecte real dels 1.295 contractes del pilot.

# Prefixos CPV no ambigus -> tema (el primer que casa guanya; específics abans que
# genèrics). Confiança alta (és el codi oficial de l'objecte).
_CPV_TEMA: tuple[tuple[str, str], ...] = (
    # --- específics (3-5 dígits) primer ---
    ("9251", "cultura"),         # biblioteques/arxius/museus
    ("9252", "cultura"),         # museus i patrimoni
    ("9253", "cultura"),         # jardins botànics/zoo (patrimoni)
    ("7995", "turisme"),         # serveis d'organització d'events/fires
    ("6312", "turisme"),         # serveis d'informació turística
    ("7531", "social"),          # serveis socials amb allotjament
    ("8531", "social"),          # serveis socials/benestar
    ("8532", "social"),
    ("8511", "salut"),           # serveis de salut
    ("8512", "salut"),
    ("8514", "salut"),
    ("7971", "seguretat"),       # serveis de seguretat/vigilància
    ("7972", "seguretat"),
    ("7561", "seguretat"),       # protecció civil
    ("7525", "seguretat"),       # salvament/socorrisme
    ("4521", "aigua"),           # obres de captació/conducció d'aigua
    ("45232", "aigua"),          # obres auxiliars de canonades (clavegueram/aigua)
    ("45233", "mobilitat"),      # obres de carreteres/autopistes/vials (NO 45231=canonades)
    ("4524", "aigua"),           # obres hidràuliques (preses, ports fluvials)
    ("4531", "manteniment"),     # instal·lacions elèctriques d'edifici
    ("4533", "manteniment"),     # lampisteria/calefacció d'edifici
    ("4534", "manteniment"),     # tancaments/altres instal·lacions d'edifici
    ("4521", "aigua"),
    ("0913", "energia"),         # electricitat
    ("0931", "energia"),         # energia solar
    ("0932", "energia"),         # biomassa
    # --- famílies de 2 dígits (genèric) ---
    ("90", "residus"),           # medi ambient / neteja / residus / clavegueram
    ("65", "aigua"),             # distribució d'aigua i serveis públics
    ("41", "aigua"),             # aigua natural (captació, tractament)
    ("92", "cultura"),           # serveis recreatius/culturals/esportius (fallback)
    ("80", "educacio"),          # serveis d'ensenyament i formació
    ("85", "salut"),             # serveis sanitaris i socials (refinat per paraula sota)
    ("66", "administracio"),     # serveis financers i d'assegurances
    ("72", "digitalitzacio"),    # serveis de TI (programació, consultoria)
    ("48", "digitalitzacio"),    # paquets de programari
    ("64", "digitalitzacio"),    # telecomunicacions
    ("60", "mobilitat"),         # transport (refinat per paraula sota: escolar->educacio)
    ("63", "mobilitat"),         # serveis auxiliars de transport
    ("34", "mobilitat"),         # equipament de transport (vehicles)
    ("50", "manteniment"),       # serveis de reparació i manteniment
    ("71", "administracio"),     # arquitectura/enginyeria (refinat: redacció->diagnòstic via caràcter)
    ("79", "administracio"),     # serveis empresarials (refinat per paraula sota: promoció->turisme)
    ("75", "administracio"),     # administració pública i defensa
    ("98", "administracio"),     # altres serveis comunitaris/personals
    ("55", "educacio"),          # hostaleria (al sector local sol ser càtering escolar)
    ("15", "social"),            # productes alimentaris (lots solidaris, menjadors)
    ("33", "salut"),             # equipament mèdic
    ("44", "urbanisme"),         # materials de construcció (obra d'espai urbà)
    ("45", "urbanisme"),         # construcció (genèric; desempata la paraula)
    ("39", "manteniment"),       # mobiliari/equipament
    ("30", "digitalitzacio"),    # equipament informàtic i d'oficina
    ("31", "manteniment"),       # material elèctric
    ("32", "digitalitzacio"),    # equips de ràdio/TV/comunicació
)

# Paraules clau -> tema (desempat i fallback). Ordre = prioritat. Tot normalitzat.
# Les llistes són específiques del govern local del Berguedà (verificades sobre els
# objectes reals). Algunes paraules ESCALEN per damunt del CPV genèric (vegeu
# ``_TEMA_KEYWORD_OVERRIDE_CPV``).
_TEMA_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("educacio", (
        "transport escolar", "menjador escolar", "menjador amb", "escola bressol",
        "escolar", "instituts", "centres educatius", "educatiu", "educacio",
        "tallers", "aula", "monitoratge", "monitorat", "lleure", "casal",
    )),
    ("social", (
        "serveis socials", "gent gran", "dependencia", "inclusio social",
        "mediacio", "terapia familiar", "families", "infants", "adolescents",
        "violenci", "atencio a les persones", "acollida", "vulnerab",
        "camins escolars", "guarderia rural", "menjars a domicili",
    )),
    ("salut", (
        "salut mental", "sanitari", "ambulanc", "medic", "infermeria", "salut",
        "prevencio de", "psicolog", "rehabilitacio funcional",
    )),
    ("seguretat", (
        "vigilancia", "vigilant", "seguretat privada", "socorrisme", "salvament",
        "socors", "proteccio civil", "emergenci", "policia", "guardia",
        "control d acces", "extincio", "bomber",
    )),
    ("turisme", (
        "turis", "visitant", "promocio del bergueda", "grand depart",
        "ciclisme", "ruta del", "rutes ", "itinerari", "senyalitzacio turis",
        "fira ", "tren del ciment", "geoparc", "punt d informacio",
        "marqueting", "campanya promocio", "projeccio exterior", "agenda",
    )),
    ("cultura", (
        "patum", "festa", "festes", "cultural", "espectacle", "concert",
        "museu", "patrimoni", "exposicio", "arxiu", "biblioteca", "teatre",
        "arqueolog", "monument", "documental dels", "fons fotograf",
        "fons documental", "artistic",
    )),
    ("residus", (
        "residu", "escombrari", "brossa", "deixalleria", "recollida selectiva",
        "recollida de", "neteja viaria", "claveguer", "sanejament", "abocador",
        "fems", "porta a porta", "rebuig", "fraccio",
    )),
    ("aigua", (
        "aigua", "aigues", "potable", "abastament", "depurador", "edar",
        "cloracio", "diposit d aigua", "captacio d aigua", "xarxa d aigua",
        "potabilitzacio", "clavegueram d aigua", "colector", "collector",
    )),
    ("energia", (
        "fotovoltaic", "fotovolta", "energia solar", "eficiencia energetica",
        "subministrament electric", "subministrament d energia",
        "enllumenat public" + "", "biomassa", "calefaccio district",
        "auditoria energetica", "punt de recarrega", "plaques solars",
    )),
    ("digitalitzacio", (
        "aplicatiu", "programari", "software", "web ", "informatic", "digital",
        "tramits", "seu electronica", "administracio electronica", "wifi",
        "connectivitat", "codis qr", "ciberseguretat", "servidor",
        "emmagatzemament inform", "intelligencia artificial",
    )),
    ("habitatge", (
        "habitatge", "habitatges", "vivenda", "rehabilitacio d habitatge",
        "lloguer social", "borsa de lloguer", "parc public d habitatge",
    )),
    ("mobilitat", (
        "carretera", "vial", "via publica", "pavimentaci", "asfaltat",
        "aparcament", "parquimetre", "parquimetres", "senyalitzacio viaria",
        "transport public", "mobilitat", "rotonda", "calçada", "calcada",
        "retirada de vehicles", "grua", "ferm",
    )),
    ("manteniment", (
        "manteniment", "reparaci", "reparacio", "conservacio", "arranjament",
        "substitucio de", "consolidacio", "filtracions", "coberta",
        "pintura", "jardineria", "poda", "desbross",
    )),
    ("urbanisme", (
        "obres de", "execucio de les obres", "obra civil", "espai public",
        "urbanitzacio", "planejament", "pla urbanistic", "pla operatiu",
        "parc ", "plaça", "placa ", "enderroc", "pista poliesportiva",
        "pista d atletisme", "equipament esportiu", "cementiri",
    )),
    ("administracio", (
        "auditoria", "control financer", "juridic", "advocat", "assegurança",
        "asseguranca", "asegur", "consultoria", "redaccio dels plecs",
        "material d oficina", "lots nadal", "subministrament de material",
        "gestio", "assistencia tecnica administrativa", "financ",
    )),
)

# Paraules que ESCALEN per damunt del CPV genèric (família de 2 dígits). Si una
# d'aquestes apareix a l'objecte, el tema de la paraula guanya encara que el CPV de
# 2 dígits apunti a un altre tema. Resol els CPV intrínsecament ambigus del sector
# públic local (transport escolar amb CPV 60; obra d'aigua amb CPV 45; promoció amb
# CPV 79). NO escala per damunt d'un CPV específic (3+ dígits), que ja és precís.
_TEMA_OVERRIDE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "educacio": ("escolar", "menjador", "escola bressol", "instituts",
                 "centres educatius", "casal", "tallers"),
    "social": ("serveis socials", "inclusio social", "gent gran", "dependencia",
               "mediacio comunitaria", "guarderia rural"),
    "turisme": ("turis", "promocio del bergueda", "grand depart", "ciclisme",
                "tren del ciment", "geoparc", "marqueting"),
    "aigua": ("abastament d aigua", "xarxa d aigua", "potabilitzacio",
              "captacio d aigua", "collector", "colector"),
    "energia": ("fotovoltaic", "fotovolta", "energia solar", "biomassa"),
    "seguretat": ("socorrisme", "salvament", "vigilant", "seguretat privada"),
    "digitalitzacio": ("aplicatiu", "programari", "informatic", "seu electronica"),
}


def tema_administratiu(cpv_raw: str | None, objecte: str | None) -> tuple[str, float, str]:
    """Deriva ``(tema, confianca, metode)`` per a un contracte.

    Prioritat:
      1. CPV **específic** (prefix ≥ 3 dígits) → tema + conf 0.9, metode 'cpv'.
      2. Paraula clau d'**override** sobre CPV de 2 dígits ambigu → conf 0.7,
         metode 'cpv+kw' (el CPV donava família però la paraula precisa el tema).
      3. CPV de 2 dígits → tema + conf 0.8, metode 'cpv'.
      4. Paraula clau (sense CPV temàtic) → conf 0.55, metode 'keyword'.
      5. Res → 'altres', conf 0.3, metode 'cap'.
    """
    obj = _norm(objecte)
    codes = _cpv_codes(cpv_raw)

    # 1) CPV específic (3+ dígits del prefix) — el més precís, no l'escala res.
    for code in codes:
        digits = _cpv_digits(code)
        for prefix, tema in _CPV_TEMA:
            if len(prefix) >= 3 and digits.startswith(prefix):
                return tema, 0.9, "cpv"

    # 2/3) CPV de 2 dígits (família) — però una paraula d'override pot precisar-lo.
    cpv2_tema: str | None = None
    for code in codes:
        digits = _cpv_digits(code)
        for prefix, tema in _CPV_TEMA:
            if len(prefix) == 2 and digits.startswith(prefix):
                cpv2_tema = tema
                break
        if cpv2_tema:
            break

    if cpv2_tema is not None:
        # Override: si l'objecte porta una paraula forta d'un altre tema, guanya.
        for tema, words in _TEMA_OVERRIDE_KEYWORDS.items():
            if tema != cpv2_tema and obj and any(w in obj for w in words):
                return tema, 0.7, "cpv+kw"
        return cpv2_tema, 0.8, "cpv"

    # 4) Sense CPV temàtic: paraula clau sobre l'objecte (evidència feble).
    if obj:
        for tema, words in _TEMA_KEYWORDS:
            if any(w in obj for w in words):
                return tema, 0.55, "keyword"

    # 5) Res: residual honest.
    return "altres", 0.3, "cap"


# =============================================================================
# 2) caracter_senyal  (es deriva del VERB de l'objecte, no del CPV)
# =============================================================================
#
# El caràcter separa el metabolisme normal de la tensió. El senyal viu al verb:
# «manteniment de…» (ordinari) vs «obres d'urgència…» (emergencia) vs «redacció del
# projecte de…» (transformacio/diagnostic) vs «campanya de promoció…» (promocio).

_CARACTER_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # emergencia primer (és el més informatiu i el menys freqüent)
    ("emergencia", (
        "urgenci", "urgent", "emergenci", "dany", "danys", "afectacio",
        "esllavissad", "temporal ", "aiguat", "reparacio urgent", "risc ",
        "despres del", "arran de", "filtracions", "averia", "avaria",
    )),
    # diagnostic: entendre abans d'actuar
    ("diagnostic", (
        "estudi ", "estudi de", "diagnosi", "diagnostic", "analisi",
        "auditoria", "redaccio del projecte", "redaccio d un projecte",
        "redaccio de projecte", "redaccio dels plecs", "avaluacio",
        "inventari", "cens ", "pla director", "pla operatiu", "pla de",
        "memoria valorada", "assistencia tecnica per a la redaccio",
    )),
    # promocio: projecció exterior / captació
    ("promocio", (
        "promocio", "marqueting", "campanya", "publicitat", "difusio",
        "projeccio exterior", "comunicacio i", "grand depart", "fira ",
        "creacio de continguts", "audiovisual de promocio",
    )),
    # transformacio: inversió estructural nova (obra de creació, no de reparació)
    ("transformacio", (
        "construccio", "construir", "creacio d", "creacio de", "nova ",
        "nou ", "instal lacio d un", "instal lacio de", "implementacio d un",
        "urbanitzacio", "ampliacio ", "millora integral", "execucio de les obres",
        "execucio d obres", "obres de creacio", "obres consistents a la creacio",
        "subministrament i muntatge", "adquisicio d un", "compra d un",
    )),
    # reforç: més del mateix (ampliació d'un servei existent)
    ("reforç", (
        "reforç", "reforc", "ampliacio del servei", "increment del servei",
        "servei extraordinari", "suport extern", "reforçar", "reforcar",
        "ampliacio de places",
    )),
)

# Si el tema és inherentment recurrent i cap verb de tensió hi casa, és ordinari.
_TEMES_TIPICAMENT_ORDINARIS = frozenset({
    "residus", "aigua", "manteniment", "seguretat", "social", "educacio",
    "administracio", "salut", "energia",
})


def caracter_senyal(objecte: str | None, tema: str) -> tuple[str, float]:
    """Deriva ``(caracter, confianca)`` del verb de l'objecte + el tema.

    Prioritat de verbs: emergencia > diagnostic > promocio > transformacio >
    reforç. Si cap verb hi casa: ``ordinari`` (és el cas per defecte del
    metabolisme municipal). La confiança és modesta perquè és lectura de text
    lliure (0.6 si un verb casa; 0.45 per al ``ordinari`` per defecte).
    """
    obj = _norm(objecte)
    if obj:
        for caracter, words in _CARACTER_KEYWORDS:
            if any(w in obj for w in words):
                return caracter, 0.6
    # Per defecte: metabolisme normal.
    return "ordinari", 0.45


# =============================================================================
# 3) contract_signal_type  (força com a senyal TERRITORIAL)
# =============================================================================
#
# Quanta intel·ligència de territori aporta el contracte? No tots els contractes
# parlen del territori: comprar material d'oficina és context administratiu pur;
# contractar socorrisme fluvial és evidència directa d'ús recreatiu de l'aigua.

# Temes que, contractats per un municipi, són EVIDÈNCIA DIRECTA d'un fenomen
# territorial (algú HA D'usar el servei → el fenomen existeix físicament).
_SIGNAL_EVIDENCIA: dict[str, tuple[str, ...]] = {
    "turisme": ("visitant", "socorrisme", "informacio turis", "tren del ciment",
                "geoparc", "afluencia", "aforament"),
    "residus": ("recollida", "deixalleria", "porta a porta"),
    "aigua": ("abastament", "potabilitzacio", "captacio d aigua"),
    "seguretat": ("socorrisme", "salvament"),
}

# Temes que són PROXY FORT del metabolisme/pressió del territori (CPV temàtic clar).
_TEMES_PROXY_FORT = frozenset({
    "residus", "aigua", "turisme", "cultura", "mobilitat", "energia",
    "social", "educacio", "salut", "habitatge", "urbanisme",
})

# Temes administratius purs: el contracte no diu res del territori (nomes_context).
_TEMES_CONTEXT = frozenset({"administracio"})


def contract_signal_type(
    tema: str, metode_tema: str, objecte: str | None
) -> tuple[str, float]:
    """Deriva ``(signal_type, confianca)``: la força territorial del contracte.

    Lògica:
      - ``administracio`` → ``nomes_context`` (no parla del territori).
      - tema territorial + paraula d'evidència directa → ``evidencia_directa``.
      - tema territorial amb CPV temàtic (metode 'cpv'/'cpv+kw') → ``proxy_fort``.
      - tema territorial només per paraula (metode 'keyword') → ``proxy_feble``.
      - ``altres`` → ``nomes_context`` (no sabem què revela).
    """
    obj = _norm(objecte)

    if tema in _TEMES_CONTEXT:
        return "nomes_context", 0.6
    if tema == "altres":
        return "nomes_context", 0.5

    # Evidència directa: el contracte és la prova física del fenomen.
    ev_words = _SIGNAL_EVIDENCIA.get(tema)
    if ev_words and obj and any(w in obj for w in ev_words):
        return "evidencia_directa", 0.7

    if tema in _TEMES_PROXY_FORT:
        if metode_tema in ("cpv", "cpv+kw"):
            return "proxy_fort", 0.75
        return "proxy_feble", 0.55

    # Tema territorial menys clar (no hauria d'arribar aquí amb la taxonomia actual).
    return "proxy_feble", 0.5


# =============================================================================
# API agregada: classifica un contracte sencer
# =============================================================================

def classify_licitacio(cpv_raw: str | None, objecte: str | None) -> dict:
    """Classifica un contracte a les tres dimensions territorials.

    Retorna un dict amb: ``tema_administratiu``, ``tema_confianca``,
    ``tema_metode``, ``caracter_senyal``, ``caracter_confianca``,
    ``contract_signal_type``, ``signal_confianca``. Pur i determinista.
    """
    tema, tema_conf, tema_metode = tema_administratiu(cpv_raw, objecte)
    caracter, car_conf = caracter_senyal(objecte, tema)
    sig_type, sig_conf = contract_signal_type(tema, tema_metode, objecte)
    return {
        "tema_administratiu": tema,
        "tema_confianca": round(tema_conf, 3),
        "tema_metode": tema_metode,
        "caracter_senyal": caracter,
        "caracter_confianca": round(car_conf, 3),
        "contract_signal_type": sig_type,
        "signal_confianca": round(sig_conf, 3),
    }
