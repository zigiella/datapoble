"""Codis dels 31 municipis del Berguedà (pilot) + detecció d'òrgans supra.

``ine5`` = codi INE de 5 dígits = clau de join del contracte amb
``mart_municipi`` (Sondeig). Es deriva de ``codi_ine10[:5]`` del contracte.

Aquest mòdul reprodueix el conjunt INE5 que viu a
``packages/ingestion/datapoble_ingestion/municipis.py`` (Sondeig). Es manté aquí
local perquè la capa de senyals (i els seus tests) no depengui del paquet
d'ingestion. Si Sondeig hi afegeix municipis, sincronitzar.

LLIÇÓ CLAU (micromunicipi → supramunicipal, crèdit a Talaia): un òrgan comarcal
o supramunicipal (p.ex. el Consell Comarcal del Berguedà) **no és un municipi**.
El seu ``codi_ine10`` NO és un INE5 vàlid (el Consell porta ``8101410007`` →
``81014``, que és un codi de comarca, no de municipi). Per tant la detecció de
l'àmbit es fa pel **nom de l'òrgan**, no pel codi.
"""
from __future__ import annotations

import re

# ine5 -> nom oficial (català). Els 31 del Berguedà.
BERGUEDA_INE5: dict[str, str] = {
    "08011": "Avià",
    "08016": "Bagà",
    "08022": "Berga",
    "08024": "Borredà",
    "08045": "Capolat",
    "08049": "Casserres",
    "08050": "Castellar del Riu",
    "08052": "Castellar de n'Hug",
    "08057": "Castell de l'Areny",
    "08078": "l'Espunyola",
    "08080": "Fígols",
    "08092": "Gironella",
    "08093": "Gisclareny",
    "08099": "Guardiola de Berguedà",
    "08130": "Montclar",
    "08132": "Montmajor",
    "08142": "la Nou de Berguedà",
    "08144": "Olvan",
    "08166": "la Pobla de Lillet",
    "08175": "Puig-reig",
    "08177": "la Quar",
    "08188": "Sagàs",
    "08190": "Saldes",
    "08216": "Sant Jaume de Frontanyà",
    "08255": "Santa Maria de Merlès",
    "08268": "Cercs",
    "08293": "Vallcebre",
    "08299": "Vilada",
    "08308": "Viver i Serrateix",
    "08903": "Sant Julià de Cerdanyola",
    "25100": "Gósol",
}

assert len(BERGUEDA_INE5) == 31, "El Berguedà té 31 municipis"

VALID_INE5: frozenset[str] = frozenset(BERGUEDA_INE5)

# Patrons d'òrgans supramunicipals (no municipi). Tot sense accents i en
# minúscula a ``_is_supra`` perquè el matching sigui robust al mojibake de la font.
_SUPRA_PATTERNS = (
    "consell comarcal",
    "comarcal",
    "mancomunitat",
    "consorci",
    "diputacio",
    "area metropolitana",
    "agencia",
    "generalitat",
)


def _strip_accents(text: str) -> str:
    import unicodedata

    t = unicodedata.normalize("NFKD", text)
    return "".join(c for c in t if not unicodedata.combining(c))


def is_supramunicipal(nom_organ: str | None) -> bool:
    """Heurística: l'òrgan és supramunicipal (no un ajuntament concret)?"""
    if not nom_organ:
        return False
    n = _strip_accents(nom_organ).lower()
    return any(p in n for p in _SUPRA_PATTERNS)


def classify_ambit(nom_organ: str | None) -> str:
    """``comarcal`` si l'òrgan és un Consell Comarcal; ``supramunicipal`` per a
    la resta d'òrgans no-municipals; ``municipal`` altrament."""
    if not nom_organ:
        return "municipal"
    n = _strip_accents(nom_organ).lower()
    if "comarcal" in n:
        return "comarcal"
    if is_supramunicipal(nom_organ):
        return "supramunicipal"
    return "municipal"


def comarca_from_organ(nom_organ: str | None) -> str | None:
    """Extreu el nom de la comarca d'un òrgan comarcal.
    'Consell Comarcal del Berguedà' -> 'Berguedà'. None si no es pot."""
    if not nom_organ:
        return None
    m = re.search(r"[Cc]omarcal\s+(?:de\s+l['’]|del\s+|de\s+la\s+|de\s+|d['’])\s*(.+)$", nom_organ)
    if m:
        return m.group(1).strip(" .")
    return None
