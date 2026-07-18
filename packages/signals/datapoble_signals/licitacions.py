"""Capa d'intel·ligència institucional de licitacions (PAS 1).

> «Una licitació és una **confessió administrativa**.» El cabal passa de *rastre
> lateral* a **capa de capacitat institucional**.

Aquest mòdul és **derivat i offline** (com ``convergencia.py``): NO descarrega res.
Llegeix la taula d'events de contractació ja materialitzada
(``data/events/events_bergueda.parquet``, 1.295 events, contracte intacte) i en
deriva, **per damunt**, tres sortides:

  1. **Events enriquits** — cada contracte amb la taxonomia territorial pròpia
     (``tema_administratiu``, ``caracter_senyal``, ``contract_signal_type`` +
     confiances), vegeu ``licitacions_taxonomy.py``. NO toca el parquet d'events
     original (que és el contracte de la capa): escriu un parquet nou.
     → ``data/events/licitacions_enriquit_bergueda.parquet``

  2. **Repartiment supramunicipal DECLARAT** — els 695 events del Consell Comarcal
     (``ambit='comarcal'``, ``ine5=NULL``) avui són **inútils a ``ine5=NULL``**.
     Aquí els repartim als 31 municipis del Berguedà amb un ``allocation_method``
     **explícit** + confiança. *Un contracte comarcal és senyal per als
     micromunicipis de la comarca* (la lliçó de Talaia).
     → ``data/events/licitacions_repartiment_bergueda.parquet``

  3. **Indicador ``dependencia_supramunicipal``** per municipi — quant del que es
     contracta «per a» un municipi ve de dalt (Consell) vs el que contracta ell
     mateix. Per als micromunicipis que **no contracten**, és el rastre de la seva
     dependència institucional (no contractar ≠ no necessitar).
     → ``data/events/licitacions_dependencia_bergueda.parquet``

HONEST BOUNDARY (innegociable): la classificació és **heurística** (cobertura
parcial; ``altres`` a propòsit). Els repartiments són **inferència declarada**: cap
és «la veritat», cada fila duu el seu mètode i la seva confiança. L'LLM sobre
``altres`` + la validació manual de 300 contractes + els altres 4 indicadors =
**PAS 2**.
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from .config import COMARCA_PILOT, events_path
from .licitacions_taxonomy import classify_licitacio
from .municipis import BERGUEDA_INE5, _strip_accents

# Parquet d'entrada (read-only): la taula d'events de contractació.
CONTRACTACIO_PARQUET = "events_bergueda.parquet"

# Parquets de sortida.
ENRIQUIT_PARQUET = "licitacions_enriquit_bergueda.parquet"
REPARTIMENT_PARQUET = "licitacions_repartiment_bergueda.parquet"
DEPENDENCIA_PARQUET = "licitacions_dependencia_bergueda.parquet"

# Mart de Sondeig (read-only) — només per a la població (denominador del
# repartiment ``per_poblacio`` i del càlcul de l'indicador). Si no hi és, caiem a
# repartiment igualitari (i ho marquem).
from .config import DATA_DIR  # noqa: E402

MART_MUNICIPI = DATA_DIR / "marts" / "mart_municipi.parquet"


# =============================================================================
# Vocabulari controlat del repartiment
# =============================================================================
#
# Com s'assigna un event supramunicipal als municipis. Cada mètode és una
# **hipòtesi de repartiment declarada**, no una mesura.
ALLOCATION_METHODS = (
    "directe_textual",  # l'objecte nomena un municipi concret → 100% a ell
    "per_poblacio",     # la càrrega escala amb la població → quota poblacional
    "per_carrega",      # repartit per una càrrega coneguda (PAS 2; no usat encara)
    "per_indicador",    # repartit per un indicador del mart (PAS 2; no usat encara)
    "igualitari",       # servei territorial compartit → parts iguals (1/31)
    "no_assignable",    # funcionament intern del Consell → no és senyal municipal
)

# Ordre canònic de columnes de la taula de repartiment (el contracte de sortida).
# 1 fila = (event supramunicipal × municipi receptor).
REPARTIMENT_COLUMNS: tuple[str, ...] = (
    "event_id",              # str — event original (del Consell)
    "ine5",                  # str — municipi RECEPTOR de la part
    "nom_muni",              # str — nom net del receptor
    "comarca",               # str
    "tema_administratiu",    # str — tema heurístic de l'event
    "caracter_senyal",       # str
    "contract_signal_type",  # str
    "allocation_method",     # str — un d'ALLOCATION_METHODS
    "allocation_share",      # float — fracció de l'event assignada a aquest muni (0..1)
    "import_total",          # float|None — import sencer de l'event (€, sense IVA)
    "import_assignat",       # float|None — import_total * allocation_share
    "allocation_confianca",  # float — confiança en el repartiment (0..1)
    "objecte",               # str — objecte de l'event (traçabilitat)
    "font_url",              # str — URL del contracte original (traçabilitat)
)

# Ordre canònic de columnes de l'indicador de dependència (1 fila/municipi).
DEPENDENCIA_COLUMNS: tuple[str, ...] = (
    "ine5",
    "nom_muni",
    "comarca",
    "poblacio",                         # int|None — padró (mart), denominador de context
    "import_municipal_directe",         # float — € que el municipi contracta ELL MATEIX
    "n_contractes_municipal",           # int   — nre de contractes propis
    "import_serveis_comarcals_assignables",  # float — € comarcals assignats (exclou no_assignable)
    "dependencia_supramunicipal",       # float — comarcal_assignable / municipal_directe
    "dependencia_lectura",              # str   — etiqueta honesta de la ràtio
    "confianca",                        # float — confiança composta (repartiment × cobertura)
)


# =============================================================================
# Repartiment supramunicipal: la lògica per tema
# =============================================================================
#
# Mapatge tema → mètode de repartiment per defecte. **Simple a propòsit** (el brief:
# «comença simple»): per_poblacio per als serveis a persones, igualitari per als
# territorials, no_assignable per al funcionament intern del Consell. La detecció
# textual d'un municipi concret (``directe_textual``) té prioritat sobre tot això.

# Serveis on la càrrega escala amb la població (qui té més gent, més en consumeix).
_TEMA_PER_POBLACIO = frozenset({
    "social", "educacio", "salut", "residus", "seguretat",
    "digitalitzacio", "habitatge",
})
# Serveis territorials compartits (la comarca sencera se'n beneficia per igual:
# promoció, planejament supramunicipal, xarxa viària comarcal, cultura de comarca).
_TEMA_IGUALITARI = frozenset({
    "turisme", "cultura", "mobilitat", "urbanisme", "aigua", "energia",
})
# Funcionament intern del Consell com a organisme (no és servei a cap municipi).
_TEMA_NO_ASSIGNABLE = frozenset({"administracio"})
# ``altres`` → igualitari amb confiança baixa (no sabem què és; el repartim pla i ho diem).


def _norm_match(text: str | None) -> str:
    """Sense accents, minúscules, apòstrofs/punts/guions com a espais. Igual que el
    ``_norm`` de la taxonomia, perquè la detecció textual de municipis sigui robusta
    a «Castellar de n'Hug» ↔ «castellar de n hug»."""
    import re

    if not text:
        return ""
    t = _strip_accents(text).lower()
    t = re.sub(r"[''`´·.\-_/]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# Noms de municipi → ine5, per a la detecció textual. Inclou variants sense article.
def _muni_name_index() -> list[tuple[str, str]]:
    """Llista (nom_normalitzat, ine5) ordenada per longitud desc (match avariciós:
    'castellar de n'hug' abans que 'castellar')."""
    pairs: list[tuple[str, str]] = []
    for ine5, nom in BERGUEDA_INE5.items():
        n = _norm_match(nom)
        pairs.append((n, ine5))
        # variant sense article inicial ("la pobla de lillet" -> "pobla de lillet")
        for art in ("l ", "la ", "el ", "els ", "les "):
            if n.startswith(art):
                pairs.append((n[len(art):], ine5))
        # variant amb apòstrof normalitzat ("castellar de n'hug" -> "castellar de n hug")
        if "'" in nom:
            pairs.append((_norm_match(nom.replace("'", " ")), ine5))
    # més llargs primer (eviten falsos positius de subcadenes curtes)
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


_MUNI_INDEX = _muni_name_index()

# Noms massa curts/ambigus per a match textual fiable (evita falsos positius).
_MUNI_MIN_LEN = 5


def _detect_municipi(objecte: str | None) -> str | None:
    """Si l'objecte nomena **un sol** municipi del Berguedà, retorna el seu ine5.

    Conservador: requereix que el nom tingui longitud >= ``_MUNI_MIN_LEN`` i que
    NO n'aparegui cap altre (si n'hi ha dos, no és repartiment directe net → None).
    """
    obj = _norm_match(objecte)
    if not obj:
        return None
    hits: set[str] = set()
    for nom, ine5 in _MUNI_INDEX:
        if len(nom) >= _MUNI_MIN_LEN and nom in obj:
            hits.add(ine5)
    if len(hits) == 1:
        return next(iter(hits))
    return None


def allocation_for_event(
    *, tema: str, objecte: str | None
) -> tuple[str, float]:
    """Decideix ``(allocation_method, confianca_base)`` per a un event supra.

    La detecció textual d'un municipi guanya sempre. Altrament, mètode per tema.
    La confiança és la del **mètode** (no de quant encerta el repartiment fi):
      - directe_textual 0.85 (l'objecte ho diu)
      - per_poblacio   0.6  (hipòtesi raonable de càrrega)
      - igualitari     0.45 (hipòtesi neutra)
      - no_assignable  0.7  (sabem que és intern del Consell)
    """
    muni = _detect_municipi(objecte)
    if muni is not None:
        return "directe_textual", 0.85
    if tema in _TEMA_NO_ASSIGNABLE:
        return "no_assignable", 0.7
    if tema in _TEMA_PER_POBLACIO:
        return "per_poblacio", 0.6
    if tema in _TEMA_IGUALITARI:
        return "igualitari", 0.45
    # altres / desconegut: repartiment pla, confiança baixa (i honest).
    return "igualitari", 0.3


# =============================================================================
# Pipeline
# =============================================================================

def _load_population() -> dict[str, int]:
    """ine5 -> població (del mart). {} si el mart no hi és (caurem a igualitari)."""
    if not MART_MUNICIPI.exists():
        return {}
    con = duckdb.connect()
    try:
        rows = con.execute(
            "SELECT ine5, poblacio FROM read_parquet(?)", [str(MART_MUNICIPI.as_posix())]
        ).fetchall()
    finally:
        con.close()
    return {str(i): int(p) for i, p in rows if i is not None and p is not None}


def enrich_events(df: pd.DataFrame) -> pd.DataFrame:
    """Afegeix les columnes de taxonomia territorial a la taula d'events.

    No modifica les columnes existents; n'afegeix de noves a la dreta. ``df`` ha de
    tenir almenys ``cpv`` i ``objecte``.
    """
    extra = df.apply(
        lambda r: classify_licitacio(r.get("cpv"), r.get("objecte")),
        axis=1, result_type="expand",
    )
    return pd.concat([df.reset_index(drop=True), extra.reset_index(drop=True)], axis=1)


def build_allocation(df_enriched: pd.DataFrame, pop: dict[str, int]) -> pd.DataFrame:
    """Reparteix els events comarcals als 31 municipis. 1 fila = (event × muni).

    ``df_enriched`` és la taula d'events enriquida (amb ``tema_administratiu`` etc.).
    Només es reparteixen els events amb ``ambit='comarcal'``. Els ``no_assignable``
    generen **una** fila amb ``ine5=NULL`` i share 0 (es preserven per a la
    traçabilitat i el recompte; no sumen a cap municipi).
    """
    # DENOMINADOR = la població dels municipis ON ES REPARTEIX (els 31), MAI la
    # de tot el diccionari: des de F2 el mart_municipi cobreix Catalunya sencera
    # (947 munis) i sum(pop.values()) és la població de tot el país. Amb el
    # denominador gros, les quotes per_poblacio sumaven pop(31)/pop(CAT) ≈ 0,5%
    # i es perdien ~7,67 M€ (86% del que reparteix el Consell) en silenci — el
    # vermell de test_real_parquet_cobertura_i_conservacio, destapat a R1.
    total_pop = sum(pop.get(i, 0) for i in BERGUEDA_INE5)
    rows: list[dict] = []
    comarcal = df_enriched[df_enriched["ambit"] == "comarcal"]

    for _, ev in comarcal.iterrows():
        tema = ev["tema_administratiu"]
        objecte = ev.get("objecte")
        method, conf = allocation_for_event(tema=tema, objecte=objecte)
        import_total = ev.get("import")
        import_total = float(import_total) if pd.notna(import_total) else None

        base = {
            "event_id": ev["event_id"],
            "comarca": ev.get("comarca") or COMARCA_PILOT,
            "tema_administratiu": tema,
            "caracter_senyal": ev["caracter_senyal"],
            "contract_signal_type": ev["contract_signal_type"],
            "allocation_method": method,
            "import_total": import_total,
            "allocation_confianca": round(conf, 3),
            "objecte": objecte,
            "font_url": ev.get("font_url"),
        }

        if method == "no_assignable":
            rows.append({
                **base, "ine5": None, "nom_muni": None,
                "allocation_share": 0.0, "import_assignat": 0.0,
            })
            continue

        if method == "directe_textual":
            ine5 = _detect_municipi(objecte)
            targets = {ine5: 1.0}
        elif method == "per_poblacio" and total_pop > 0:
            targets = {i: pop[i] / total_pop for i in BERGUEDA_INE5 if i in pop}
            # municipis sense població al mart: quota 0 (rara; el mart cobreix 31)
            for i in BERGUEDA_INE5:
                targets.setdefault(i, 0.0)
        else:
            # igualitari (o per_poblacio sense mart → cau a igualitari, marcat)
            if method == "per_poblacio" and total_pop == 0:
                method = "igualitari"
                base["allocation_method"] = "igualitari"
                base["allocation_confianca"] = round(min(conf, 0.3), 3)
            n = len(BERGUEDA_INE5)
            targets = {i: 1.0 / n for i in BERGUEDA_INE5}

        for ine5, share in targets.items():
            imp_assignat = (
                round(import_total * share, 2) if import_total is not None else None
            )
            rows.append({
                **base,
                "ine5": ine5,
                "nom_muni": BERGUEDA_INE5.get(ine5),
                "allocation_share": round(float(share), 6),
                "import_assignat": imp_assignat,
            })

    out = pd.DataFrame(rows, columns=list(REPARTIMENT_COLUMNS))
    return out


def _dependencia_lectura(ratio: float | None, n_propi: int) -> str:
    """Etiqueta honesta de la ràtio de dependència supramunicipal."""
    if n_propi == 0:
        return "no_contracta_propi"  # tot el seu rastre ve de dalt (micromunicipi)
    if ratio is None:
        return "sense_dada"
    if ratio >= 2.0:
        return "molt_dependent"      # rep >2x del que contracta ell mateix
    if ratio >= 0.5:
        return "dependencia_mitjana"
    return "autonom"                 # contracta molt més del que rep de dalt


def build_dependencia(
    df_enriched: pd.DataFrame, df_alloc: pd.DataFrame, pop: dict[str, int]
) -> pd.DataFrame:
    """Indicador ``dependencia_supramunicipal`` per municipi.

    = ``import_serveis_comarcals_assignables`` / ``import_municipal_directe``.

    - **numerador**: suma d'``import_assignat`` del repartiment (exclou
      ``no_assignable`` per construcció: tenen ine5=NULL).
    - **denominador**: € que el municipi contracta ell mateix (``ambit='municipal'``).

    Per als micromunicipis amb denominador 0 (no contracten res propi) la ràtio és
    indefinida → la marquem ``no_contracta_propi`` i deixem la ràtio NULL: **no
    contractar ≠ no necessitar**; el numerador (el que els arriba de dalt) ÉS,
    precisament, el rastre de la seva dependència.
    """
    # Denominador: contractació municipal directa.
    muni = df_enriched[df_enriched["ambit"] == "municipal"].copy()
    muni["import"] = pd.to_numeric(muni["import"], errors="coerce")
    direct = (
        muni.groupby("ine5")
        .agg(import_municipal_directe=("import", "sum"),
             n_contractes_municipal=("event_id", "count"))
        .reset_index()
    )

    # Numerador: import comarcal assignat (només files amb ine5 no nul).
    alloc = df_alloc[df_alloc["ine5"].notna()].copy()
    alloc["import_assignat"] = pd.to_numeric(alloc["import_assignat"], errors="coerce")
    assignat = (
        alloc.groupby("ine5")
        .agg(import_serveis_comarcals_assignables=("import_assignat", "sum"))
        .reset_index()
    )

    rows: list[dict] = []
    for ine5, nom in sorted(BERGUEDA_INE5.items()):
        d = direct[direct["ine5"] == ine5]
        a = assignat[assignat["ine5"] == ine5]
        imp_dir = float(d["import_municipal_directe"].iloc[0]) if len(d) else 0.0
        n_dir = int(d["n_contractes_municipal"].iloc[0]) if len(d) else 0
        imp_com = float(a["import_serveis_comarcals_assignables"].iloc[0]) if len(a) else 0.0

        ratio = (imp_com / imp_dir) if imp_dir > 0 else None
        lectura = _dependencia_lectura(ratio, n_dir)

        # Confiança composta: el repartiment és inferència (baixa-mitjana) i, si el
        # municipi no contracta res propi, el denominador és absent (menys fiable).
        conf = 0.5 if imp_dir > 0 else 0.35

        rows.append({
            "ine5": ine5,
            "nom_muni": nom,
            "comarca": COMARCA_PILOT,
            "poblacio": pop.get(ine5),
            "import_municipal_directe": round(imp_dir, 2),
            "n_contractes_municipal": n_dir,
            "import_serveis_comarcals_assignables": round(imp_com, 2),
            "dependencia_supramunicipal": round(ratio, 3) if ratio is not None else None,
            "dependencia_lectura": lectura,
            "confianca": conf,
        })

    return pd.DataFrame(rows, columns=list(DEPENDENCIA_COLUMNS))


# =============================================================================
# Materialització (parquet via DuckDB, mateix patró que events.py)
# =============================================================================

def _write_parquet(df: pd.DataFrame, name: str) -> str:
    out = events_path(name)
    out.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        con.register("t", df)
        con.execute("CREATE TABLE t2 AS SELECT * FROM t")
        con.execute("COPY t2 TO ? (FORMAT PARQUET)", [str(out)])
    finally:
        con.close()
    return str(Path(out).as_posix())


def compute(contractacio_parquet: str | None = None) -> dict[str, pd.DataFrame]:
    """Calcula les tres sortides (no escriu res). Retorna els tres DataFrames."""
    cp = contractacio_parquet or str(events_path(CONTRACTACIO_PARQUET).as_posix())
    con = duckdb.connect()
    try:
        df = con.execute("SELECT * FROM read_parquet(?)", [cp]).df()
    finally:
        con.close()

    pop = _load_population()
    enriched = enrich_events(df)
    alloc = build_allocation(enriched, pop)
    dep = build_dependencia(enriched, alloc, pop)
    return {"enriquit": enriched, "repartiment": alloc, "dependencia": dep}


def _coverage_summary(enriched: pd.DataFrame) -> dict:
    """Cobertura honesta de la classificació: % per tema + % altres."""
    n = len(enriched)
    by_tema = (
        enriched["tema_administratiu"].value_counts().to_dict()
    )
    by_caracter = enriched["caracter_senyal"].value_counts().to_dict()
    by_signal = enriched["contract_signal_type"].value_counts().to_dict()
    by_metode = enriched["tema_metode"].value_counts().to_dict()
    altres = int(by_tema.get("altres", 0))
    return {
        "n_events": int(n),
        "pct_altres": round(100 * altres / n, 1) if n else 0.0,
        "pct_classificats": round(100 * (n - altres) / n, 1) if n else 0.0,
        "per_tema": {k: int(v) for k, v in by_tema.items()},
        "per_caracter": {k: int(v) for k, v in by_caracter.items()},
        "per_signal_type": {k: int(v) for k, v in by_signal.items()},
        "per_metode_tema": {k: int(v) for k, v in by_metode.items()},
    }


def run(*, write: bool = True) -> dict:
    """CLI entrypoint: enriqueix, reparteix, calcula l'indicador, escriu, resumeix."""
    if not events_path(CONTRACTACIO_PARQUET).exists():
        raise FileNotFoundError(
            f"falta {CONTRACTACIO_PARQUET} (cal córrer `contractacio` primer)"
        )

    out = compute()
    enriched, alloc, dep = out["enriquit"], out["repartiment"], out["dependencia"]

    paths = {}
    if write:
        paths = {
            "enriquit": _write_parquet(enriched, ENRIQUIT_PARQUET),
            "repartiment": _write_parquet(alloc, REPARTIMENT_PARQUET),
            "dependencia": _write_parquet(dep, DEPENDENCIA_PARQUET),
        }

    # Resum del repartiment: events comarcals per mètode.
    alloc_events = alloc.drop_duplicates("event_id")
    by_method = alloc_events["allocation_method"].value_counts().to_dict()

    # Lectura de l'indicador (els micromunicipis que no contracten).
    dep_no_propi = dep[dep["dependencia_lectura"] == "no_contracta_propi"]

    return {
        "source": "licitacions",
        "parquets": paths,
        "cobertura_classificacio": _coverage_summary(enriched),
        "repartiment": {
            "events_comarcals": int(len(alloc_events)),
            "files_repartides": int(len(alloc)),
            "per_allocation_method": {k: int(v) for k, v in by_method.items()},
        },
        "dependencia": {
            "n_municipis": int(len(dep)),
            "municipis_sense_contractacio_propia": int(len(dep_no_propi)),
            "noms_sense_propia": sorted(dep_no_propi["nom_muni"].tolist()),
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run(), ensure_ascii=False, indent=2))
