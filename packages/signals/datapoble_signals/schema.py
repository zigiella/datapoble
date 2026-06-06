"""El contracte de la capa: l'esquema d'**event**.

Una fila = un senyal. Tota font del cabal (contractació ara; sequera, edictes,
etc. després) ha de normalitzar-se a aquest esquema. Així la convergència futura
pot operar sobre una taula única sense saber d'on ve cada senyal.

Disciplina (innegociable, exigència de Talaia):
  - **Traçabilitat sempre:** cap event sense ``font_url``.
  - **Dada vs inferència explícit:** ``categoria`` separa el *fet* (el contracte
    existeix) de la *inferència* (què implica el senyal, p.ex. el ``tipus_senyal``).
  - **Àmbit explícit:** ``ambit`` marca si el senyal és municipal o supra
    (comarcal/supramunicipal) perquè la convergència el pugui repartir.
"""
from __future__ import annotations

# Vocabularis controlats ------------------------------------------------------

# Àmbit territorial del senyal. Determina si ``ine5`` pot ser NULL.
AMBITS = ("municipal", "comarcal", "supramunicipal")

# Fase del cicle d'un fenomen respecte al senyal:
#   anticipacio  — el senyal precedeix el fet (un contracte és anticipació).
#   realitzacio  — el senyal és contemporani al fet (p.ex. un aforament).
#   reaccio      — el senyal segueix el fet (p.ex. una queixa, una sanció).
FASES = ("anticipacio", "realitzacio", "reaccio")

# Frontera dada/inferència. El cor de la disciplina.
#   fet        — registrat a la font primària (el contracte existeix, amb import i data).
#   inferencia — derivat per heurística (el tema/pressió que el senyal implica).
CATEGORIES = ("fet", "inferencia")

# Tema del senyal (taxonomia verificada per Talaia, vegeu taxonomy.py).
#   aigua_sequera — declaració/canvi d'estat de sequera de l'ACA per a un
#     municipi/unitat d'explotació (rastre administratiu net, vegeu sequera.py).
#     Distint d'``aigua`` (contractació de serveis d'aigua): aquí el senyal és la
#     restricció declarada, no un contracte.
TIPUS_SENYAL = (
    "neteja_residus",
    "aigua",
    "aigua_sequera",
    "mobilitat_via",
    "turisme_cultura_events",
    "seguretat_socorrisme",
    "altres",
)

# Tipus de la data (què representa el camp ``data``). Permet barrejar fonts amb
# semàntiques temporals diferents sense perdre el significat.
DATA_TIPUS = (
    "adjudicacio",      # contractació: data_adjudicacio_contracte
    "publicacio",       # data de publicació del contracte/adjudicació
    "anunci",           # data de publicació de l'anunci de licitació (intenció)
    "inici_vigencia",   # restriccions (sequera): data d'entrada en vigor
    "ocurrencia",       # el fet va passar aquell dia
)

# Ordre canònic de columnes de la taula ``events`` (el contracte) -------------
# Cada font produeix exactament aquestes columnes, en aquest ordre.
EVENT_COLUMNS: tuple[str, ...] = (
    "event_id",      # str  — id estable i únic del senyal (hash determinista)
    "ine5",          # str|None — codi INE de 5 dígits; NULL si ambit != municipal
    "nom_muni",      # str|None — nom del municipi (o de l'òrgan supra)
    "ambit",         # str  — un de AMBITS
    "comarca",       # str|None — comarca del senyal
    "data",          # date — data principal del senyal
    "data_tipus",    # str  — un de DATA_TIPUS (què és 'data')
    "font",          # str  — nom de la font/dataset llegible (p.ex. l'òrgan)
    "font_url",      # str  — URL traçable a la publicació (MAI NULL)
    "tipus_senyal",  # str  — un de TIPUS_SENYAL (el tema; INFERÈNCIA)
    "fase",          # str  — un de FASES
    "objecte",       # str  — descripció lliure del senyal (l'objecte del contracte)
    "import",        # float|None — import econòmic associat (€, sense IVA); >= 0
    "categoria",     # str  — un de CATEGORIES (marca dada vs inferència del senyal)
    "confianca",     # float — 0..1, confiança en el tipus_senyal inferit
    # --- traçabilitat addicional (no obligatòria al contracte mínim) ---
    "dataset_id",    # str  — id Socrata de la font
    "font_clau",     # str  — clau de SOURCES (p.ex. 'contractacio')
    "cpv",           # str|None — codi CPV cru (evidència de la inferència)
    "raw_id",        # str|None — id natural a la font (codi_expedient/dir3…)
)

# Subconjunt mínim que el brief exigeix explícitament (per a tests/doc).
MIN_REQUIRED = (
    "event_id", "ine5", "nom_muni", "ambit", "comarca", "data", "data_tipus",
    "font", "font_url", "tipus_senyal", "fase", "objecte", "import",
    "categoria", "confianca",
)
