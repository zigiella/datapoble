"""Connector de contractació → events (Socrata ``ybgg-dgi6``).

Normalitza cada **contracte menor adjudicat** a un *event* del cabal. La idea:
un contracte és el rastre administratiu d'una pressió futura —algú ha hagut de
contractar el servei abans que el fet passi—, així que **un contracte és
anticipació**.

Decisions de normalització (acotades pel brief):
  - ``ine5``      = ``codi_ine10[:5]`` **si** l'òrgan és municipal; NULL altrament.
  - ``nom_muni``  = nom canònic del municipi (del registre INE5) o nom de l'òrgan.
  - ``font``      = ``nom_organ`` (qui contracta).
  - ``fase``      = ``anticipacio`` (sempre, per a contractació).
  - ``data``      = ``data_adjudicacio_contracte`` (``data_tipus='adjudicacio'``).
  - ``font_url``  = ``enllac_publicacio.url`` (traçabilitat; mai NULL → si falta, fallback a la URL del dataset).
  - ``import``    = ``import_adjudicacio_sense`` (sense IVA), float, >= 0.
  - ``tipus_senyal`` = heurística CPV + paraules clau (vegeu ``taxonomy``).
  - ``categoria`` = ``fet`` (el contracte EXISTEIX) — però el ``tipus_senyal`` que
    n'inferim és INFERÈNCIA; ``confianca`` (de la taxonomia) ho gradua.

LLIÇÓ SUPRAMUNICIPAL (crèdit a Talaia): els òrgans comarcals/supra NO són un
municipi → ``ambit='comarcal'``, ``ine5=NULL``, ``comarca='Berguedà'``. *Un
contracte comarcal és senyal per als micromunicipis de la comarca* (els pobles
petits no contracten els seus serveis: Castellar té 23 contractes i cap de
turisme; viu del Consell). Marquem ``ambit`` perquè la convergència (PR futur)
ho pugui repartir.
"""
from __future__ import annotations

import hashlib

import requests

from .config import COMARCA_PILOT, RAW_DIR, SOURCES
from .municipis import (
    BERGUEDA_INE5,
    classify_ambit,
    comarca_from_organ,
)
from .provenance import write_provenance
from .schema import EVENT_COLUMNS
from .socrata import fetch_all
from .taxonomy import classify

SOURCE = "contractacio"
FONT_CLAU = SOURCE

# Filtre del pilot: Berga (08022) + Castellar (08052) per codi_ine10, i el Consell
# Comarcal del Berguedà per nom (el seu codi_ine10 no és municipal → no filtrable
# per prefix INE5). "la resta + el Consell" del brief: el Consell és l'òrgan supra
# que dona servei als micromunicipis; les seves files són el senyal comarcal.
PILOT_WHERE = (
    "starts_with(codi_ine10,'08022') "
    "OR starts_with(codi_ine10,'08052') "
    "OR nom_organ like '%Comarcal del Bergued%'"
)


def _event_id(row: dict) -> str:
    """Id estable i únic d'un event de contractació.

    Determinista: hash de (dataset, expedient, dir3, organ, lot, objecte, data,
    import). Sobreviu a re-ingestes (idempotent) i no depèn de l'ordre de fila.

    Per què ``numero_lot``: una mateixa licitació es publica sovint partida en
    **lots** (mateix expedient/objecte/data, diferent ``descripcio_lot`` i
    pressupost). Cada lot és un sub-contracte distint → un senyal distint → ha de
    tenir el seu ``event_id``. Sense el lot, els lots col·lapsarien i perdríem
    senyals reals (verificat: 79 col·lisions al pilot, totes lots de transport
    escolar i obres de camins del Consell).
    """
    key = "|".join(
        str(row.get(k, ""))
        for k in (
            "codi_expedient",
            "codi_dir3",
            "codi_organ",
            "numero_lot",
            "objecte_contracte",
            "data_adjudicacio_contracte",
            "import_adjudicacio_sense",
        )
    )
    digest = hashlib.sha1(f"{SOURCE}|{key}".encode("utf-8")).hexdigest()[:16]
    return f"con_{digest}"


def _to_date(raw: str | None) -> str | None:
    """'2023-09-19T00:00:00.000' -> '2023-09-19' (DuckDB ho parseja a DATE)."""
    if not raw:
        return None
    return str(raw)[:10]


# Cadena de fallback de data (camp de la font -> data_tipus de l'esquema), en
# ordre de preferència semàntica. La primera que existeix guanya.
_DATE_CHAIN: tuple[tuple[str, str], ...] = (
    ("data_adjudicacio_contracte", "adjudicacio"),
    ("data_publicacio_contracte", "publicacio"),
    ("data_publicacio_adjudicacio", "publicacio"),
    ("data_publicacio_anunci", "anunci"),
    ("data_publicacio_futura", "anunci"),
    ("data_publicacio_previ", "anunci"),
)


def _pick_date(row: dict) -> tuple[str | None, str]:
    """Tria la millor data disponible i el seu ``data_tipus``.

    Per defecte ``adjudicacio`` encara que no n'hi hagi cap (data NULL): el
    senyal segueix sent un contracte adjudicat conceptualment.
    """
    for field, tipus in _DATE_CHAIN:
        d = _to_date(row.get(field))
        if d is not None:
            return d, tipus
    return None, "adjudicacio"


def _to_float(raw: str | None) -> float | None:
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _url(row: dict) -> str | None:
    enllac = row.get("enllac_publicacio")
    if isinstance(enllac, dict):
        return enllac.get("url")
    return None


def normalize(row: dict) -> dict:
    """Una fila crua de ``ybgg-dgi6`` → un event (dict amb ``EVENT_COLUMNS``)."""
    nom_organ = row.get("nom_organ")
    ambit = classify_ambit(nom_organ)

    ine10 = row.get("codi_ine10") or ""
    ine5 = ine10[:5] if ine10 else None

    if ambit == "municipal":
        # Municipi: ine5 vàlid i nom canònic del registre (net, sense mojibake).
        nom_muni = BERGUEDA_INE5.get(ine5, nom_organ)
        comarca = COMARCA_PILOT
    else:
        # Supra: NO és un municipi → ine5 = NULL (encara que el codi_ine10 dugui
        # un prefix: és un codi de comarca, no de municipi). La convergència
        # repartirà aquest senyal als micromunicipis (PR futur).
        ine5 = None
        nom_muni = nom_organ
        comarca = comarca_from_organ(nom_organ) or COMARCA_PILOT

    tipus_senyal, confianca, _metode = classify(
        row.get("codi_cpv"), row.get("objecte_contracte") or row.get("denominacio")
    )

    font_url = _url(row) or SOURCES[SOURCE]["url"]  # traçabilitat: mai NULL

    objecte = row.get("objecte_contracte") or row.get("denominacio") or ""

    # Data: preferim l'adjudicació (el contracte com a senyal d'anticipació ja
    # adjudicat). Si l'expedient encara no està adjudicat (fases obertes), caiem
    # —en ordre de preferència semàntica— a la publicació del contracte i després
    # a la de l'anunci de licitació (quan la intenció de contractar es fa
    # pública: també és anticipació). Ho marquem a ``data_tipus`` perquè el
    # significat temporal no es perdi. Així gairebé cap event queda sense data.
    data, data_tipus = _pick_date(row)

    event = {
        "event_id": _event_id(row),
        "ine5": ine5,
        "nom_muni": nom_muni,
        "ambit": ambit,
        "comarca": comarca,
        "data": data,
        "data_tipus": data_tipus,
        "font": nom_organ,
        "font_url": font_url,
        "tipus_senyal": tipus_senyal,
        "fase": "anticipacio",          # un contracte és anticipació
        "objecte": objecte,
        "import": _to_float(row.get("import_adjudicacio_sense")),
        "categoria": "fet",             # el contracte EXISTEIX (el tema és inferència)
        "confianca": confianca,
        "dataset_id": SOURCES[SOURCE]["dataset_id"],
        "font_clau": FONT_CLAU,
        "cpv": row.get("codi_cpv"),
        "raw_id": row.get("codi_expedient"),
    }
    # Garanteix l'ordre i la presència de totes les columnes del contracte.
    return {col: event.get(col) for col in EVENT_COLUMNS}


def fetch_events(where: str = PILOT_WHERE, *, save_raw: bool = True) -> list[dict]:
    """Descarrega el pilot i retorna la llista d'events normalitzats.

    Si ``save_raw``, deixa les files crues i la procedència a
    ``data/raw/contractacio/`` (gitignored).
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
    raw_file = out_dir / "contractacio_raw.json"
    raw_file.write_text(
        json.dumps(raw_rows, ensure_ascii=False, indent=0), encoding="utf-8"
    )
    write_provenance(
        SOURCE,
        out_dir,
        row_count=len(raw_rows),
        files=[raw_file.name],
        query={"$where": where},
        extra={"loader": "requests", "note": "1 fila crua = 1 contracte menor"},
    )


def run() -> dict:
    """CLI entrypoint: descarrega el pilot, escriu la taula d'events, retorna resum."""
    from .events import write_events_table

    events = fetch_events()
    result = write_events_table(events)
    return {"source": SOURCE, **result}


if __name__ == "__main__":
    import json

    print(json.dumps(run(), ensure_ascii=False, indent=2))
