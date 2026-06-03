"""Taxonomia CPV + paraules clau → ``tipus_senyal`` (verificada per Talaia).

HONEST BOUNDARY (cal dir-ho clar): aquesta classificació és **heurística**. El
senyal fort és el **CPV** (Common Procurement Vocabulary, el codi oficial de
l'objecte del contracte); quan no n'hi ha —i al pilot ~48% dels contractes no
porten CPV— recorrem a **paraules clau** sobre l'objecte, que és sorollós. El
calaix ``altres`` és, per tant, **gran a propòsit**: preferim no inventar un tema
abans que classificar malament. El refinament fi és feina de l'LLM (PR posterior).

La confiança (``confianca``, 0..1) ho reflecteix:
  - 0.9  match per **CPV** (família de 2-3 dígits) — evidència forta.
  - 0.6  match només per **paraula clau** sobre l'objecte — evidència feble.
  - 0.3  ``altres`` (cap senyal) — recompte residual, no afirmació de tema.

``classify`` és pur (sense xarxa, sense estat) → fàcil de testejar i auditar.
"""
from __future__ import annotations

import re
import unicodedata

# Confiances per nivell d'evidència.
CONF_CPV = 0.9
CONF_KEYWORD = 0.6
CONF_ALTRES = 0.3

# --- Taxonomia CPV (prefix de família) -> tipus_senyal -----------------------
# CPV s'estructura per famílies: els primers dígits són el grup. Comprovem per
# prefix per capturar tota la família (p.ex. '90' = serveis de medi ambient).
# Ordre de prioritat: el primer prefix que casa guanya (els més específics
# —3-4 dígits— van abans dels genèrics de 2).
CPV_PREFIX: tuple[tuple[str, str], ...] = (
    # neteja / residus — serveis de clavegueram, escombraries, neteja, medi ambient
    ("90", "neteja_residus"),
    # aigua — distribució d'aigua, captació/depuració (650.. i 412..)
    ("6512", "aigua"),
    ("6513", "aigua"),
    ("4112", "aigua"),
    ("4521", "aigua"),   # obres de captació/conducció d'aigua
    # mobilitat / via — construcció de carreteres, vials, transport
    ("4523", "mobilitat_via"),  # obres de carreteres/vials
    ("4500", "mobilitat_via"),  # preparació d'obres (genèric d'obra civil viària)
    ("6010", "mobilitat_via"),  # transport per carretera
    ("6371", "mobilitat_via"),  # serveis auxiliars de transport (senyalització…)
    ("6010", "mobilitat_via"),
    ("3712", "mobilitat_via"),  # mobiliari/equipament urbà de via
    # turisme / cultura / events — serveis recreatius, culturals, espectacles
    ("7995", "turisme_cultura_events"),  # serveis d'organització d'events
    ("9231", "turisme_cultura_events"),  # serveis artístics/espectacles
    ("9232", "turisme_cultura_events"),  # gestió d'instal·lacions artístiques
    ("9234", "turisme_cultura_events"),  # serveis d'espectacles/festes
    ("9237", "turisme_cultura_events"),  # serveis recreatius
    ("9252", "turisme_cultura_events"),  # museus / patrimoni
    ("9261", "turisme_cultura_events"),  # serveis esportius (events)
    ("9262", "turisme_cultura_events"),
    ("92", "turisme_cultura_events"),    # genèric cultura/esbarjo (fallback família)
    # seguretat / socorrisme — vigilància, socorrisme, salvament
    ("7971", "seguretat_socorrisme"),  # serveis de seguretat/vigilància
    ("7561", "seguretat_socorrisme"),  # serveis de socors/protecció civil
    ("7525", "seguretat_socorrisme"),  # serveis de salvament/socorrisme
)

# --- Fallback per paraules clau sobre l'objecte (evidència feble) ------------
# Llistes ordenades per prioritat. Tot en minúscula i sense accents (vegeu
# ``_norm``). Verificades sobre l'objecte real dels contractes del Berguedà.
KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("neteja_residus", (
        "neteja", "residu", "escombrari", "brossa", "deixalleria", "recollida",
        "selectiva", "claveguer", "sanejament", "abocador", "fems",
    )),
    ("aigua", (
        "aigua", "aigues", "potable", "abastament", "depurador", "edar",
        "cloracio", "dipo­sit d'aigua", "captacio d'aigua", "xarxa d'aigua",
    )),
    ("mobilitat_via", (
        "carretera", "vial", "via publica", "pavimentaci", "asfaltat",
        "camins", "cami ", "vorera", "voreres", "aparcament", "transport",
        "senyalitzacio", "ferm", "calçada", "calcada", "pont ", "rotonda",
    )),
    ("turisme_cultura_events", (
        "turis", "patum", "festa", "festes", "cultural", "espectacle",
        "concert", "fira", "museu", "patrimoni", "exposicio", "esdeveniment",
        "activitats", "tren del ciment", "visitant", "promocio", "agenda",
    )),
    ("seguretat_socorrisme", (
        "seguretat", "vigilancia", "socorrisme", "salvament", "socors",
        "proteccio civil", "emergenci", "policia", "guardia", "extincio",
    )),
)


def _norm(text: str | None) -> str:
    """Minúscules, sense accents, espais col·lapsats. Per a matching robust."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


def _cpv_codes(cpv_raw: str | None) -> list[str]:
    """Separa un CPV cru en codis. La font els concatena amb ``||`` quan n'hi
    ha més d'un (p.ex. ``71318100-1||51313000-9``)."""
    if not cpv_raw:
        return []
    return [c.strip() for c in str(cpv_raw).split("||") if c.strip()]


def classify(cpv_raw: str | None, objecte: str | None) -> tuple[str, float, str]:
    """Classifica un contracte → ``(tipus_senyal, confianca, metode)``.

    Prioritat: CPV (fort) → paraula clau (feble) → ``altres`` (residual).
    ``metode`` ∈ {``cpv``, ``keyword``, ``cap``} documenta l'evidència usada.
    """
    # 1) CPV — evidència forta.
    for code in _cpv_codes(cpv_raw):
        digits = re.sub(r"[^0-9]", "", code)  # '90511000-2' -> '905110002'
        for prefix, tipus in CPV_PREFIX:
            if digits.startswith(prefix):
                return tipus, CONF_CPV, "cpv"

    # 2) Paraula clau sobre l'objecte — evidència feble.
    obj = _norm(objecte)
    if obj:
        for tipus, words in KEYWORDS:
            if any(w in obj for w in words):
                return tipus, CONF_KEYWORD, "keyword"

    # 3) Res: recompte residual, no afirmació de tema.
    return "altres", CONF_ALTRES, "cap"
