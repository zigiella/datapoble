"""Connector de sequera → events (Socrata ``i5n8-43cw``, ACA).

Normalitza cada **declaració/canvi d'estat de sequera** de l'Agència Catalana de
l'Aigua a un *event* del cabal. La idea: quan l'ACA declara un canvi d'estat
hidrològic (normalitat → prealerta → alerta → excepcionalitat → emergència) per a
una unitat d'explotació, emet una Resolució amb mesures i restriccions per a tots
els municipis d'aquella unitat. **Aquesta declaració és un rastre administratiu
net** —existeix una data, un estat i un àmbit— i és senyal de *pressió hídrica*,
que convergeix amb el turisme/segona residència (més població real → més consum
d'aigua → més tensió quan l'embassament baixa).

Font: dataset «Estat de sequera per unitats d'explotació i municipis a les
Conques Internes de Catalunya» (``i5n8-43cw``). El Berguedà és conca del
Llobregat (conca interna) → cobertura **municipal completa** (31/31 municipis,
verificat). Cada fila de la font = un canvi d'estat per a un municipi en una data.

Decisions de normalització (acotades pel brief):
  - ``ine5``      = ``codi_municipi[:5]`` (el dataset baixa fins a municipi: el
    codi és INE6, els 5 primers són l'INE5 de join amb ``mart_municipi``).
  - ``ambit``     = ``municipal`` SEMPRE. **Diferència clau amb contractació:**
    aquí la font dona resolució municipal real, no cal el maneig supramunicipal.
    La *unitat d'explotació* (la zona ACA que es declara) es preserva com a
    traçabilitat (``raw_id`` = codi UE) i dins ``objecte`` — és el nivell on es
    pren la decisió, però el senyal ja arriba assignat al municipi.
  - ``data``      = ``data_canvi_estat_sequera`` (``data_tipus='inici_vigencia'``:
    la restricció entra en vigor amb la declaració).
  - ``font``      = "Agència Catalana de l'Aigua (ACA)".
  - ``font_url``  = URL del dataset (traçabilitat; mai NULL).
  - ``fase``      = ``realitzacio``. **Diferència amb contractació** (que és
    ``anticipacio``): una declaració de sequera no precedeix el fet, *és* l'estat
    vigent contemporani —descriu la pressió mentre passa.
  - ``tipus_senyal`` = ``aigua_sequera`` (sempre; no és heurística com el CPV).
  - ``objecte``   = estat hidrològic declarat + unitat d'explotació + estat
    pluviomètric (text llegible amb tot el context de la fila).
  - ``import``    = NULL (una declaració no té import econòmic).
  - ``categoria`` = ``fet`` (la declaració EXISTEIX). Però el que *implica* en
    termes de pressió/restricció és INFERÈNCIA, graduada per ``confianca`` segons
    la severitat de l'estat (vegeu ``CONF_PER_ESTAT``): a ``emergència`` la
    restricció és inequívoca; a ``normalitat`` no hi ha senyal de pressió.

HONEST BOUNDARY (disciplina de Talaia): el camp ``data`` és la data del canvi
d'estat, no la de fi de vigència —un estat val fins al canvi següent (la font és
un històric de transicions, no d'intervals tancats). El motor de convergència
(PR futur) reconstruirà els intervals ordenant per ``data`` dins de cada
municipi. Aquí no ho fem: cada fila = un event, fidelitat a la font.
"""
from __future__ import annotations

import hashlib

import requests

from .config import COMARCA_PILOT, RAW_DIR, SOURCES
from .municipis import BERGUEDA_INE5
from .provenance import write_provenance
from .schema import EVENT_COLUMNS
from .socrata import fetch_all

SOURCE = "sequera"
FONT_CLAU = SOURCE
FONT_NOM = "Agència Catalana de l'Aigua (ACA)"

# Filtre del pilot: tots els municipis del Berguedà, per prefix INE5 sobre el
# codi de municipi (INE6) de la font. El Berguedà és conca del Llobregat (conca
# interna) → tots 31 municipis hi són (verificat: 398 files, 31 municipis).
PILOT_WHERE = " OR ".join(
    f"starts_with(codi_municipi,'{ine5}')" for ine5 in sorted(BERGUEDA_INE5)
)

# Gradació de ``confianca`` per severitat de l'estat hidrològic declarat.
# NO és incertesa sobre la dada (la declaració és sempre un FET): és la força del
# senyal de *pressió hídrica* que l'estat implica (inferència). Ordinal, alineat
# amb l'escala del Pla de sequera de l'ACA (normalitat → emergència).
# Clau = estat normalitzat (majúscules, sense accents). Inclou els nivells
# intermedis introduïts en revisions del pla (preemergència, emergència I/II).
CONF_PER_ESTAT: dict[str, float] = {
    "NORMALITAT": 0.1,        # cap pressió: l'estat de base
    "PREALERTA": 0.4,         # primer senyal d'estrès hídric
    "ALERTA": 0.6,            # restriccions lleus actives
    "PREEMERGENCIA": 0.7,     # transició cap a l'excepcionalitat
    "EXCEPCIONALITAT": 0.8,   # restriccions fortes (pic de la crisi 2023-24)
    "EMERGENCIA I": 0.9,
    "EMERGENCIA": 0.95,
    "EMERGENCIA II": 1.0,     # restricció màxima
}
CONF_DEFAULT = 0.5  # estat no catalogat: senyal mig (no inventem severitat)


def _strip_accents(text: str) -> str:
    import unicodedata

    t = unicodedata.normalize("NFKD", text)
    return "".join(c for c in t if not unicodedata.combining(c))


def confianca_estat(estat_hidro: str | None) -> float:
    """Severitat del senyal de pressió segons l'estat hidrològic (0..1)."""
    if not estat_hidro:
        return CONF_DEFAULT
    key = _strip_accents(estat_hidro).strip().upper()
    return CONF_PER_ESTAT.get(key, CONF_DEFAULT)


def _event_id(row: dict) -> str:
    """Id estable i únic d'un event de sequera.

    Determinista: hash de (dataset, municipi, data del canvi, estat hidrològic,
    estat pluviomètric). Cada **canvi d'estat** d'un municipi en una data és un
    senyal distint. Inclou els dos eixos perquè una mateixa data pot registrar un
    canvi només pluviomètric mantenint l'hidrològic (verificat a l'històric de
    Berga) → són files distintes a la font, events distints aquí.
    """
    key = "|".join(
        str(row.get(k, ""))
        for k in (
            "codi_municipi",
            "data_canvi_estat_sequera",
            "codi_estat_sequera_hidrol",
            "codi_estat_sequera_pluviom",
        )
    )
    digest = hashlib.sha1(f"{SOURCE}|{key}".encode("utf-8")).hexdigest()[:16]
    return f"seq_{digest}"


def _to_date(raw: str | None) -> str | None:
    """'2023-05-11T00:00:00.000' -> '2023-05-11' (DuckDB ho parseja a DATE)."""
    if not raw:
        return None
    return str(raw)[:10]


def _objecte(row: dict) -> str:
    """Descripció llegible de l'estat declarat, amb tot el context de la fila.

    Inclou l'estat hidrològic (el senyal principal), la unitat d'explotació (el
    nivell de decisió de l'ACA) i l'estat pluviomètric (context meteorològic).
    """
    hidro = (row.get("estat_sequera_hidrol_gic") or "?").strip()
    ue = (row.get("unitat_explotaci") or "?").strip()
    pluvi = (row.get("estat_sequera_pluviom_tric") or "?").strip()
    return (
        f"Estat de sequera (hidrològic): {hidro} — unitat d'explotació «{ue}» "
        f"(estat pluviomètric: {pluvi})"
    )


def normalize(row: dict) -> dict:
    """Una fila crua de ``i5n8-43cw`` → un event (dict amb ``EVENT_COLUMNS``)."""
    codi_muni = row.get("codi_municipi") or ""
    ine5 = codi_muni[:5] if codi_muni else None

    # Nom canònic del registre (net, sense mojibake de la font). Si el municipi
    # no és del Berguedà (no hauria de passar amb el filtre), caiem al nom cru.
    nom_muni = BERGUEDA_INE5.get(ine5, row.get("municipi"))

    estat_hidro = row.get("estat_sequera_hidrol_gic")
    data = _to_date(row.get("data_canvi_estat_sequera"))

    event = {
        "event_id": _event_id(row),
        "ine5": ine5,
        "nom_muni": nom_muni,
        "ambit": "municipal",           # la font baixa a municipi (no cal supra)
        "comarca": COMARCA_PILOT,
        "data": data,
        "data_tipus": "inici_vigencia", # la restricció entra en vigor amb la declaració
        "font": FONT_NOM,
        "font_url": SOURCES[SOURCE]["url"],  # traçabilitat: mai NULL
        "tipus_senyal": "aigua_sequera",
        "fase": "realitzacio",          # l'estat declarat és contemporani al fet
        "objecte": _objecte(row),
        "import": None,                 # una declaració no té import
        "categoria": "fet",             # la declaració EXISTEIX (la pressió és inferència)
        "confianca": confianca_estat(estat_hidro),
        "dataset_id": SOURCES[SOURCE]["dataset_id"],
        "font_clau": FONT_CLAU,
        "cpv": None,                    # no aplica a sequera
        "raw_id": row.get("codi_unitat_explotaci"),  # la UE: nivell de decisió ACA
    }
    # Garanteix l'ordre i la presència de totes les columnes del contracte.
    return {col: event.get(col) for col in EVENT_COLUMNS}


def fetch_events(where: str = PILOT_WHERE, *, save_raw: bool = True) -> list[dict]:
    """Descarrega el pilot i retorna la llista d'events normalitzats.

    Si ``save_raw``, deixa les files crues i la procedència a
    ``data/raw/sequera/`` (gitignored).
    """
    session = requests.Session()
    raw_rows = list(fetch_all(SOURCES[SOURCE]["url"], where=where, session=session))
    events = [normalize(r) for r in raw_rows]

    if save_raw:
        _save_raw(raw_rows, where)

    return events


def _save_raw(raw_rows: list[dict], where: str) -> None:
    """Persisteix la raw (JSON) + procedència. Fidelitat a la font."""
    import json

    out_dir = RAW_DIR / SOURCE
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_file = out_dir / "sequera_raw.json"
    raw_file.write_text(
        json.dumps(raw_rows, ensure_ascii=False, indent=0), encoding="utf-8"
    )
    write_provenance(
        SOURCE,
        out_dir,
        row_count=len(raw_rows),
        files=[raw_file.name],
        query={"$where": where},
        extra={
            "loader": "requests",
            "note": "1 fila crua = 1 canvi d'estat de sequera (municipi × data)",
        },
    )


def run() -> dict:
    """CLI entrypoint: descarrega el pilot, escriu la taula d'events, retorna resum."""
    from .events import write_events_table

    events = fetch_events()
    result = write_events_table(events, parquet_name="events_sequera_bergueda.parquet")
    return {"source": SOURCE, **result}


if __name__ == "__main__":
    import json

    print(json.dumps(run(), ensure_ascii=False, indent=2))
