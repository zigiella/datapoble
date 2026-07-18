"""DEV SET del filtre R2 — sintètiques dirigides + 5 reals de FORA del banc.

**Disciplina C4 §4 («el banc mesura, no entrena — també el filtre»):** el filtre
dur es desenvolupa contra AQUEST conjunt, mai contra les 66 fixtures del banc
(capa A ``bdns_convocatories.json`` · capa B ``bdns_capa_b.json``). La
disjunció és mecànica: ``test_dev_set_disjunt_del_banc``. Cap entrada porta
etiqueta daurada (les daurades són NOMÉS de Bea); els «esperats» d'aquí són
expectatives de DEV del comportament del filtre, escrites per Sondeig.

Les SINTÈTIQUES són fitxes C3 construïdes a mà per exercir una regla concreta
cadascuna (la trampa de noms, el §2bis, la restricció de població…). Les REALS
(``fixtures/dev_r2_reals.json``) són 5 convocatòries BDNS del gener 2025
(finestra anterior a la composició de la capa B), arxivades crues
(busqueda+detall) i normalitzades amb el ``normalize`` real del connector.

DATA DE REFERÈNCIA FIXA del dev: 2026-07-01 per a les sintètiques (que porten
dates 2026 al voltant); les reals es jutgen a 2025-02-01 (la seva època), com
farà el banc amb la capa B (C4 §2: es jutja a data_publicacio, no avui).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

FIXTURE_REALS = Path(__file__).resolve().parent / "fixtures" / "dev_r2_reals.json"

# Dates fixes del dev (deterministes, rejugables).
DATA_REFERENCIA_SINTETIQUES = date(2026, 7, 1)
DATA_REFERENCIA_REALS = date(2025, 2, 1)
DATA_VISTA_SINTETIQUES = "2026-07-01"  # captura = referència → el flag de la font mana


def _fitxa(**kw: Any) -> dict[str, Any]:
    """Una fitxa C3 sintètica amb els 12 camps del contracte (defaults sans)."""
    base: dict[str, Any] = {
        "id_bdns": None,
        "fonts": [
            {
                "font_clau": "bdns",
                "font_url": "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias/dev",
                "data_vista": DATA_VISTA_SINTETIQUES,
            }
        ],
        "organisme": "",
        "objecte": "",
        "beneficiaris": "PERSONAS JURÍDICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA",
        "ambit_territorial": "CAT",
        "import": None,
        "cofinancament": None,
        "data_publicacio": "2026-06-25",
        "termini": None,
        "enllac": "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias/dev",
        "estat": "oberta",
    }
    base.update(kw)
    return base


# Cada sintètica: (id_dev, fitxa, expectativa_de_dev) — l'expectativa és el
# comportament del FILTRE que el cas exerceix (mai una daurada).
SINTETIQUES: list[dict[str, Any]] = [
    {
        "id_dev": "S01-elegible-clara-enllumenat",
        "espera": "viva VERDA: matèria enllumenat 0.8 + projecte en cartera + termini viu amb marge",
        "fitxa": _fitxa(
            id_bdns="700001",
            organisme="LOCAL · DIPUTACIÓN PROV. DE BARCELONA · DIPUTACIÓN PROVINCIAL DE BARCELONA",
            objecte=(
                "Subvenciones para la mejora del alumbrado público exterior de "
                "municipios de menos de 5.000 habitantes"
            ),
            beneficiaris="PERSONAS JURÍDICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA",
            ambit_territorial="provincia",
            **{"import": 40000.0},
            termini="2026-09-30",
        ),
    },
    {
        "id_dev": "S02-trampa-guardiola",
        "espera": (
            "DESCARTADA per convocant municipal aliè (Sant Salvador de Guardiola, Bages) — "
            "mai confosa amb Guardiola de Berguedà"
        ),
        "fitxa": _fitxa(
            id_bdns="700002",
            organisme="LOCAL · SANT SALVADOR DE GUARDIOLA · AYUNTAMIENTO DE SANT SALVADOR DE GUARDIOLA",
            objecte="Subvencions per a les entitats culturals del municipi, exercici 2026",
            ambit_territorial="provincia",
            termini="2026-09-15",
        ),
    },
    {
        "id_dev": "S03-consell-bergueda",
        "espera": "viva: el Consell Comarcal del BERGUEDÀ és el de la comarca del perfil",
        "fitxa": _fitxa(
            id_bdns="700003",
            organisme="LOCAL · CONSELL COMARCAL DEL BERGUEDÀ · CONSELL COMARCAL DEL BERGUEDÀ",
            objecte="Ajuts als municipis de la comarca per a camins municipals i espais públics",
            ambit_territorial="comarca",
            termini="2026-10-01",
        ),
    },
    {
        "id_dev": "S04-termini-null-oberta",
        "espera": "viva GROGA amb «termini per confirmar» — C3 §2bis: NULL mai descarta",
        "fitxa": _fitxa(
            id_bdns="700004",
            organisme="AUTONOMICA · CATALUÑA · DEPARTAMENT DE CULTURA",
            objecte="Subvencions per a la digitalització de patrimoni documental dels ens locals",
            termini=None,
            estat="oberta",
        ),
    },
    {
        "id_dev": "S05-poblacio-massa-gran",
        "espera": "DESCARTADA per restricció de població (>20.000) amb el padró citat",
        "fitxa": _fitxa(
            id_bdns="700005",
            organisme="ESTADO · MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA · IDAE",
            objecte=(
                "Ayudas a proyectos de movilidad sostenible para municipios de más de "
                "20.000 habitantes"
            ),
            ambit_territorial="estatal",
            termini="2026-12-31",
        ),
    },
    {
        "id_dev": "S06-nomes-empreses",
        "espera": "DESCARTADA per beneficiaris (només empreses/persones físiques amb activitat)",
        "fitxa": _fitxa(
            id_bdns="700006",
            organisme="AUTONOMICA · CATALUÑA · DEPARTAMENT D'EMPRESA I TREBALL",
            objecte="Ajuts a la competitivitat de les petites i mitjanes empreses turístiques",
            beneficiaris="PYME Y PERSONAS FÍSICAS QUE DESARROLLAN ACTIVIDAD ECONÓMICA",
            termini="2026-09-01",
        ),
    },
    {
        "id_dev": "S07-nominativa",
        "espera": "DESCARTADA per concessió nominativa (no és concurrència)",
        "fitxa": _fitxa(
            id_bdns="700007",
            organisme="LOCAL · DIPUTACIÓN PROV. DE BARCELONA · DIPUTACIÓN PROVINCIAL DE BARCELONA",
            objecte="Subvención nominativa al Consorcio del Ter para el ejercicio 2026",
            ambit_territorial="provincia",
            termini="2026-08-31",
        ),
    },
    {
        "id_dev": "S08-estatal-passa",
        "espera": "viva: l'àmbit estatal EXISTEIX i el perfil el porta (decisió R1 ratificada)",
        "fitxa": _fitxa(
            id_bdns="700008",
            organisme="ESTADO · MINISTERIO DE CULTURA · DIRECCIÓN GENERAL DE PATRIMONIO CULTURAL",
            objecte=(
                "Ayudas para la conservación del patrimonio cultural (1,5% cultural) "
                "destinadas a entidades locales"
            ),
            ambit_territorial="estatal",
            **{"import": 3000000.0},
            termini="2026-10-15",
        ),
    },
    {
        "id_dev": "S09-termini-vencut",
        "espera": "DESCARTADA per termini vençut a la data de referència",
        "fitxa": _fitxa(
            id_bdns="700009",
            organisme="AUTONOMICA · CATALUÑA · DEPARTAMENT DE TERRITORI",
            objecte="Subvencions per a la millora d'espais públics dels ens locals",
            termini="2026-06-15",
        ),
    },
    {
        "id_dev": "S10-score-zero-viva",
        "espera": "viva GROGA amb puntuació 0: la puntuació ordena, MAI filtra (R-FUNC §3)",
        "fitxa": _fitxa(
            id_bdns="700010",
            organisme="AUTONOMICA · CATALUÑA · DEPARTAMENT DE JUSTÍCIA",
            objecte="Subvencions per al foment de la mediació comunitària als ens locals",
            termini="2026-09-20",
        ),
    },
    {
        "id_dev": "S11-tancada-flag-vigent",
        "espera": "DESCARTADA: la font la marca tancada i el flag és vigent a la referència (run diari)",
        "fitxa": _fitxa(
            id_bdns="700011",
            organisme="AUTONOMICA · CATALUÑA · DEPARTAMENT D'ACCIÓ CLIMÀTICA",
            objecte="Ajuts per a instal·lacions d'autoconsum fotovoltaic en edificis municipals",
            estat="tancada",
            termini=None,
        ),
    },
    {
        "id_dev": "S12-projecte-cartera",
        "espera": "viva VERDA per projecte en cartera (guia turística QR) encara que la matèria sigui mitjana",
        "fitxa": _fitxa(
            id_bdns="700012",
            organisme="LOCAL · DIPUTACIÓN PROV. DE BARCELONA · DIPUTACIÓN PROVINCIAL DE BARCELONA",
            objecte="Subvenciones para guías turísticas digitales multilingües de municipios",
            ambit_territorial="provincia",
            termini="2026-11-30",
        ),
    },
]


def sintetiques() -> list[dict[str, Any]]:
    """Les fitxes C3 sintètiques del dev set (ordre estable)."""
    return [json.loads(json.dumps(s["fitxa"])) for s in SINTETIQUES]


def reals() -> list[dict[str, Any]]:
    """Les 5 reals de FORA del banc, normalitzades amb el connector real.

    ``_meta.data_vista`` (2026-07-18, dia de l'arxivat) fixa la captura →
    replay determinista: el flag «tancada» d'aquestes fitxes és POSTERIOR a la
    seva època (2025) i el filtre ho ha de saber (mode banc, C4 §2).
    """
    from datapoble_signals.subvencions_bdns import dedupe, normalize

    doc = json.loads(FIXTURE_REALS.read_text(encoding="utf-8"))
    vist_el = doc["_meta"]["data_vista"]
    fitxes = [
        normalize(c["detall"], c.get("busqueda"), vist_el=vist_el)
        for c in doc["convocatories"]
    ]
    return dedupe(fitxes)


def ids_reals() -> set[str]:
    doc = json.loads(FIXTURE_REALS.read_text(encoding="utf-8"))
    return {str(c["detall"]["codigoBDNS"]) for c in doc["convocatories"]}
