"""Connector BDNS → fitxa de subvenció normalitzada (contracte C3).

Font: **SNPSAP/BDNS** (Sistema Nacional de Publicidad de Subvenciones y Ayudas
Públicas). API pública, sense clau. Aquest mòdul **només ingesta i normalitza**:
el filtre fi per municipi és R2, el semàfor és R3 i qualsevol sortida (correu)
és R4 — vegeu `docs/ajuntaments/tasques-especificades.md`.

Contractes vinculants: `docs/ajuntaments/C3-subvencions-perfil.md` (la fitxa, la
clau d'identitat, la porta humana) i `C4-avaluacio-radar.md` §2 (les fixtures
arxivades són candidates al banc).

ÀNCORES VERIFICADES EN VIU (2026-07-16, crides reals contra l'API; els números
són reproduïbles amb `fechaDesde=01/01/2026&fechaHasta=30/06/2026`):

  - **Dos endpoints, dos esquemes distints** (trampa real):
      * `…/api/convocatorias/busqueda` → pàgina Spring. La fila és **plana** i
        porta `numeroConvocatoria` (NO `codigoBDNS`) i `nivel1/2/3` (NO
        `organo.*`). NO porta regions, pressupost, beneficiaris ni terminis.
      * `…/api/convocatorias?numConv=<codi>` → la **fitxa completa**, amb
        `codigoBDNS`, `organo.*`, `regiones[]`, `tiposBeneficiarios[]`,
        `presupuestoTotal`, `fechaInicioSolicitud`/`fechaFinSolicitud`, `abierto`.
    Per això la normalització necessita **les dues** (`busqueda` descobreix, la
    fitxa omple). `numeroConvocatoria == codigoBDNS` (verificat).

  - ⚠️ **LA TRAMPA DE LES REGIONS — el filtre NO cascada.** L'API declara l'arbre
    NUTS (`/api/regiones`: id 49 = «ES51 - CATALUÑA», fills 50/51/52/53 =
    Barcelona/Girona/Lleida/Tarragona) **però el filtre no l'aplica**: demanar
    `regiones=49` retorna NOMÉS les convocatòries etiquetades a l'arrel catalana.
    Mesurat (01/01–30/06/2026): `49` sol → **867**; `49,50,51,52,53` → **6.057**.
    És a dir, la regió pare sola es menja el **86%** del senyal. Vegeu el test
    `test_trampa_regions_no_cascada`.

  - ⚠️ **Els paràmetres desconeguts s'IGNOREN en silenci** (no hi ha error): p. ex.
    `abierto=true` a `busqueda` retorna exactament el mateix total que sense.
    Corol·lari: una errata en un filtre no falla — retorna dades sense filtrar.
    Per això `abierto` es filtra **a casa**, des de la fitxa, i per això la trampa
    de regions necessita un test que compti, no que miri codis HTTP.

  - **Dates:** la petició vol `dd/MM/yyyy` (`fechaDesde`/`fechaHasta`); la resposta
    dona `yyyy-MM-dd`. L'ISO a la petició → **HTTP 400** (verificat). No confondre.

  - **Paginació** Spring: `page` base 0, `pageSize` (fins a 1.000 acceptat),
    `order=fechaRecepcion`, `direccion=desc`; resposta `content[]`/`totalElements`.

  - **`vpd=GE`:** l'spec el marcava com a obligatori; **verificat que la `busqueda`
    respon 200 sense ell** (mateix `totalElements`). S'envia igualment (és la
    convenció del portal i la fitxa el porta a la seva URL pública), però el
    connector no hi confia com a garantia.

  - **4 miralls** servint dades idèntiques (verificat, mateix `totalElements`):
    infosubvenciones.es · pap.hacienda.gob.es · subvenciones.gob.es ·
    infosubvenciones.gob.es → fallback en cadena.

  - **Els 5 tipus de beneficiari són genèrics** (`/api/beneficiarios`: PYME…, GRAN
    EMPRESA, PERSONAS JURÍDICAS…, PERSONAS FÍSICAS…, SIN INFORMACION ESPECIFICA):
    **cap «ajuntament»/«entitat local»**. El filtre fi és de R2, no d'aquí.
    `tipoAdministracion` filtraria qui CONVOCA, no qui rep: no és el mateix.

FRONTERES HONESTES (el «no» és una resposta vàlida — no inventem el que la font
no dona):
  - `cofinancament` → **sempre NULL** des de BDNS: la fitxa no publica cap
    percentatge a càrrec del beneficiari.
  - `estat` → només `oberta`/`tancada`. La BDNS no té camp d'anul·lació (vegeu
    `schema.ESTATS_SUBVENCIO`).
  - `ambit_territorial` → només `estatal`/`CAT`/`provincia`: la BDNS no baixa de
    NUTS3. `comarca`/`municipi` els portarà CIDO (R5).
  - `enllac` → la **fitxa pública del portal**, no `urlBasesReguladoras`: aquest
    camp és **text lliure**, no una URL (verificat: «Convenio», «www.labisbal.cat»
    sense esquema… 3 de 26 a les fixtures no són URL). L'enllaç mai és NULL (C3).
    L'enllaç s'ha verificat **al navegador** (el portal és una SPA d'Angular: torna
    HTTP 200 amb el mateix esquelet per a QUALSEVOL ruta, fins i tot inventada →
    un 200 no prova res; el que prova que el patró és bo és que la pàgina renderitza
    la convocatòria correcta, comprovat amb la 919221).

  - ⚠️ `termini` → **NULL és AMBIGU, i R2/R4 ho han de saber.** Mesurat sobre les 26
    fixtures: només **8** porten `fechaFinSolicitud`; **11** no porten data però sí
    `textFin` en PROSA («Finaliza el 15 de septiembre de 2026», «15 Dies Hàbils»,
    «Vint dies a partir de l'endemà de la publicació al BOPB»); **7** no porten res.
    El contracte C3 només té `termini: date|NULL` i aquí **no s'inventa cap data a
    partir del text**: seria inferència servida com a fet, precisament al camp que
    diu si encara s'hi és a temps. Conseqüència honesta: `termini=NULL` vol dir «la
    font no en dona data», NO «no hi ha termini». Reportat a Talaia com a possible
    esmena de C3 (un camp per al termini en prosa) — no tapat amb un parser.

DECISIÓN QUE NECESSITA RATIFICACIÓ DE TALAIA (documentada, no silenciada):
  el llistó de R1 enumera només les 5 regions catalanes. Mesurat en viu, l'àmbit
  **estatal** (`regiones=1`, «ES - ESPAÑA») són **1.275 convocatòries més** en la
  mateixa finestra, i el conjunt és **disjunt** del català (6.057 + 1.275 = 7.332
  exactes). Excloure-les faria estructuralment invisibles les convocatòries
  ministerials/estatals a què un ajuntament SÍ que es pot presentar → un **FN de
  sistema**, que C4 §1 defineix com el pecat greu (i C3 §3 preveu `estatal` com a
  valor legítim de `territori` al perfil, cosa que no podria casar mai). L'asimetria
  mana: ingerir de més és recuperable (R2 filtra); ingerir de menys, no. Per això
  `REGIONS_DEFAULT` inclou l'estatal. Girar-ho és **una línia** (`REGIONS_R1_SPEC`).
"""
from __future__ import annotations

import hashlib
import json
import time
import unicodedata
from datetime import date, datetime, timezone
from typing import Any, Iterator

import requests

from .config import RAW_DIR, SOURCES
from .provenance import write_provenance
from .schema import AMBITS_SUBVENCIO, ESTATS_SUBVENCIO, SUBVENCIO_COLUMNS

SOURCE = "subvencions_bdns"
FONT_CLAU = "bdns"

# Miralls verificats (mateixes dades). L'ordre és l'ordre de fallback.
HOSTS: tuple[str, ...] = (
    "https://www.infosubvenciones.es/bdnstrans",
    "https://www.pap.hacienda.gob.es/bdnstrans",
    "https://www.subvenciones.gob.es/bdnstrans",
    "https://www.infosubvenciones.gob.es/bdnstrans",
)
PATH_BUSQUEDA = "/api/convocatorias/busqueda"
PATH_DETALL = "/api/convocatorias"
# Fitxa pública (l'`enllac` del contracte). `<codigoBDNS>` és el número de convocatòria.
PORTAL_FITXA = "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias/{codi}"

# Batch educat: l'avís legal de la font demana no abusar de l'accés.
USER_AGENT = "datapoble-radar/0.1 (+https://github.com/riusdegent/datapoble)"
TIMEOUT = 60
PAGE_SIZE = 200
PAUSA_ENTRE_CRIDES = 0.5   # s — ritme amable, no ràfega
BACKOFF_BASE = 2.0         # s — 2, 4, 8… davant 429/5xx
MAX_REINTENTS = 3

# Regions NUTS (ids verificats a `/api/regiones`). EL FILTRE NO CASCADA:
# enumerar la pare i els fills és OBLIGATORI (vegeu el docstring i el test).
REGIO_CATALUNYA = "49"                                    # ES51 - CATALUÑA
REGIONS_PROVINCIES_CAT = ("50", "51", "52", "53")         # BCN, GIR, LLE, TAR
REGIONS_R1_SPEC: tuple[str, ...] = (REGIO_CATALUNYA,) + REGIONS_PROVINCIES_CAT
REGIO_ESTATAL = "1"                                       # ES - ESPAÑA
# Default = spec + estatal (vegeu «DECISIÓN QUE NECESSITA RATIFICACIÓ» al docstring).
REGIONS_DEFAULT: tuple[str, ...] = (REGIO_ESTATAL,) + REGIONS_R1_SPEC

# Mapa NUTS → `ambit_territorial` (C3). Precedència: el més ample mana.
NUTS_ESTAT = "ES -"
NUTS_CAT = "ES51 -"
NUTS_PROVINCIES_CAT = ("ES511", "ES512", "ES513", "ES514")


# --- utilitats ---------------------------------------------------------------

def _strip_accents(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    return "".join(c for c in t if not unicodedata.combining(c))


def normalitza_text(text: str | None) -> str:
    """Normalització de C3 §2: minúscules, sense accents, espais col·lapsats."""
    if not text:
        return ""
    t = _strip_accents(str(text)).lower()
    return " ".join(t.split())


def data_peticio(d: date) -> str:
    """Data → `dd/MM/yyyy` (el format que EXIGEIX la petició; l'ISO dona 400)."""
    return d.strftime("%d/%m/%Y")


def _to_date(raw: str | None) -> str | None:
    """`'2026-06-30'` → `'2026-06-30'`; None/buit → None. La resposta ja és ISO."""
    if not raw:
        return None
    return str(raw)[:10]


# --- client HTTP (educat: backoff, UA identificat, fallback de miralls) -------

class BdnsClient:
    """Client mínim de la BDNS amb fallback entre miralls i backoff.

    No amaga els errors: si els 4 miralls fallen, propaga l'excepció (el «no» és
    una resposta vàlida — mai un silenci que sembli «cap convocatòria»).
    """

    def __init__(
        self,
        *,
        hosts: tuple[str, ...] = HOSTS,
        session: requests.Session | None = None,
        pausa: float = PAUSA_ENTRE_CRIDES,
        backoff: float = BACKOFF_BASE,
    ) -> None:
        self.hosts = hosts
        self.session = session or requests.Session()
        self.pausa = pausa
        # Injectable perquè els tests corrin sense esperes reals (a producció, el
        # backoff educat de debò: 2, 4, 8 s).
        self.backoff = backoff

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        ultim_error: Exception | None = None
        for host in self.hosts:
            url = f"{host}{path}"
            for intent in range(MAX_REINTENTS):
                try:
                    r = self.session.get(
                        url,
                        params={"vpd": "GE", **params},
                        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                        timeout=TIMEOUT,
                    )
                    if r.status_code in (429, 500, 502, 503, 504):
                        time.sleep(self.backoff * (2**intent))
                        continue
                    r.raise_for_status()
                    return r.json()
                except Exception as e:  # xarxa, JSON invàlid, HTTP dur…
                    ultim_error = e
                    time.sleep(self.backoff * (2**intent))
            # mirall esgotat → prova el següent
        raise RuntimeError(
            f"BDNS: els {len(self.hosts)} miralls han fallat per a {path}"
        ) from ultim_error

    def busca(
        self,
        *,
        desde: date,
        fins: date,
        regions: tuple[str, ...] = REGIONS_DEFAULT,
        page_size: int = PAGE_SIZE,
    ) -> Iterator[dict]:
        """Itera les files de `busqueda` (paginació Spring, base 0).

        `regions` s'envia com a llista explícita: la pare NO cascada (trampa).
        """
        page = 0
        while True:
            j = self._get(
                PATH_BUSQUEDA,
                {
                    "page": page,
                    "pageSize": page_size,
                    "order": "fechaRecepcion",
                    "direccion": "desc",
                    "fechaDesde": data_peticio(desde),
                    "fechaHasta": data_peticio(fins),
                    "regiones": ",".join(regions),
                },
            )
            content = j.get("content") or []
            if not content:
                break
            yield from content
            total_pages = j.get("totalPages")
            page += 1
            if total_pages is not None and page >= total_pages:
                break
            time.sleep(self.pausa)

    def fitxa(self, codi: str) -> dict:
        """La fitxa completa d'una convocatòria (`numConv=<codigoBDNS>`)."""
        j = self._get(PATH_DETALL, {"numConv": str(codi)})
        time.sleep(self.pausa)
        return j


# --- normalització a la fitxa C3 ---------------------------------------------

def ambit_territorial(detall: dict) -> str:
    """`regiones[]` → un valor de `AMBITS_SUBVENCIO`. El més ample mana.

    La BDNS dona `{"descripcion": "ES514 - Tarragona"}` (el codi NUTS va DINS del
    text, no hi ha camp d'id). Precedència estatal > CAT > província: una
    convocatòria d'àmbit estatal és estatal encara que llisti províncies.
    """
    descripcions = [
        (r.get("descripcion") or "").strip()
        for r in (detall.get("regiones") or [])
    ]
    if any(d.startswith(NUTS_ESTAT) and not d.startswith("ES5") for d in descripcions):
        return "estatal"
    if any(d.startswith(NUTS_CAT) for d in descripcions):
        return "CAT"
    if any(d.startswith(NUTS_PROVINCIES_CAT) for d in descripcions):
        return "provincia"
    # Fora de l'àmbit del radar (una altra CCAA) o sense regions declarades: la
    # font mana i no inventem. R2 ho descartarà pel territori del perfil.
    return "estatal" if not descripcions else "provincia"


def estat_convocatoria(detall: dict) -> str:
    """`abierto` (el flag de la FONT) mana sobre el termini.

    Verificat: 8 de 26 fixtures reals porten `abierto=false` amb un
    `fechaFinSolicitud` FUTUR (p. ex. un conveni de concessió directa amb data
    límit de justificació). Si deduíssim l'estat del termini diríem «oberta» a
    convocatòries a les quals **ningú es pot presentar** → soroll a la safata i,
    pitjor, una promesa falsa. La pregunta que respon el radar és «m'hi puc
    presentar?», i això és exactament el que declara `abierto`.
    """
    return "oberta" if detall.get("abierto") else "tancada"


def _organisme(detall: dict, busqueda: dict | None = None) -> str:
    """`organo.nivel1/2/3` → convocant llegible (la fitxa és niuada; la busca, plana)."""
    organo = detall.get("organo") or {}
    nivells = [organo.get(f"nivel{i}") for i in (1, 2, 3)]
    if not any(nivells) and busqueda:
        nivells = [busqueda.get(f"nivel{i}") for i in (1, 2, 3)]
    return " · ".join(str(n).strip() for n in nivells if n and str(n).strip())


def _objecte(detall: dict) -> str:
    """`descripcion` + `descripcionLeng` → objecte (sense perdre el català).

    `descripcion` (castellà) hi és sempre; `descripcionLeng` porta la versió en
    llengua cooficial quan existeix (16 de 26 fixtures). El contracte C3 té UN sol
    camp: els ajuntem en comptes de triar-ne un i llençar l'altre — el text català
    és el que llegirà una secretària de la Pobla, i el castellà és el text registral.
    """
    es = (detall.get("descripcion") or "").strip()
    ca = (detall.get("descripcionLeng") or "").strip()
    if ca and normalitza_text(ca) != normalitza_text(es):
        return f"{es} — [ca] {ca}" if es else ca
    return es


def _beneficiaris(detall: dict) -> str:
    """`tiposBeneficiarios[]` → text. Vocabulari genèric de la font (5 tipus)."""
    tipus = [
        (t.get("descripcion") or "").strip()
        for t in (detall.get("tiposBeneficiarios") or [])
    ]
    return " · ".join(t for t in tipus if t)


def _import(detall: dict) -> float | None:
    p = detall.get("presupuestoTotal")
    if p is None:
        return None
    try:
        return float(p)
    except (TypeError, ValueError):
        return None


def normalize(detall: dict, busqueda: dict | None = None, *, vist_el: str | None = None) -> dict:
    """Fitxa BDNS → la fila del contracte C3 (`SUBVENCIO_COLUMNS`, en ordre)."""
    codi = detall.get("codigoBDNS") or (busqueda or {}).get("numeroConvocatoria")
    codi = str(codi) if codi else None
    enllac = PORTAL_FITXA.format(codi=codi) if codi else SOURCES[SOURCE]["url"]
    fitxa = {
        "id_bdns": codi,
        "fonts": [
            {
                "font_clau": FONT_CLAU,
                "font_url": enllac,          # traçable a la publicació; MAI NULL
                "data_vista": vist_el or datetime.now(timezone.utc).date().isoformat(),
            }
        ],
        "organisme": _organisme(detall, busqueda),
        "objecte": _objecte(detall),
        "beneficiaris": _beneficiaris(detall),
        "ambit_territorial": ambit_territorial(detall),
        "import": _import(detall),
        "cofinancament": None,               # la BDNS no el publica (frontera honesta)
        "data_publicacio": _to_date(detall.get("fechaRecepcion")),
        "termini": _to_date(detall.get("fechaFinSolicitud")),
        "enllac": enllac,
        "estat": estat_convocatoria(detall),
    }
    return {col: fitxa.get(col) for col in SUBVENCIO_COLUMNS}


# --- clau d'identitat i dedupe (C3 §2) ---------------------------------------

def clau_identitat(fitxa: dict) -> str:
    """La clau de dedupe interfonts del contracte C3 §2.

    `bdns:<id_bdns>` si la fitxa porta id; si no, `h:<sha256[:16]>` sobre
    `organisme|objecte|termini` normalitzat (`sense-termini` si és NULL).
    """
    if fitxa.get("id_bdns"):
        return f"bdns:{fitxa['id_bdns']}"
    termini = fitxa.get("termini") or "sense-termini"
    cru = "|".join(
        (
            normalitza_text(fitxa.get("organisme")),
            normalitza_text(fitxa.get("objecte")),
            normalitza_text(str(termini)),
        )
    )
    return f"h:{hashlib.sha256(cru.encode('utf-8')).hexdigest()[:16]}"


def dedupe(fitxes: list[dict]) -> list[dict]:
    """Agrupa per clau C3: **una convocatòria = una fitxa amb N procedències**.

    Dedupe conservador (C3 §2): cap fusió per similitud tova. En conflicte de
    valors mana BDNS (font registral); aquí totes les fitxes són de BDNS, així que
    la primera vista mana i la resta només aporta `fonts` (re-sync: la BDNS
    corregeix i esborra a posteriori — cap assumpció d'immutabilitat).
    """
    per_clau: dict[str, dict] = {}
    for f in fitxes:
        k = clau_identitat(f)
        if k not in per_clau:
            per_clau[k] = {**f, "fonts": list(f.get("fonts") or [])}
            continue
        acumulada = per_clau[k]
        vistes = {
            (p.get("font_clau"), p.get("font_url")) for p in acumulada["fonts"]
        }
        for p in f.get("fonts") or []:
            if (p.get("font_clau"), p.get("font_url")) not in vistes:
                acumulada["fonts"].append(p)
    return list(per_clau.values())


# --- batch diari + materialització -------------------------------------------

def fetch_fitxes(
    *,
    desde: date,
    fins: date,
    regions: tuple[str, ...] = REGIONS_DEFAULT,
    client: BdnsClient | None = None,
    save_raw: bool = True,
) -> list[dict]:
    """Batch: `busqueda` (finestra + regions) → fitxa per novetat → normalitza.

    Poques crides: 1 per pàgina de cerca + 1 per convocatòria nova.
    """
    cli = client or BdnsClient()
    vist_el = datetime.now(timezone.utc).date().isoformat()
    files = list(cli.busca(desde=desde, fins=fins, regions=regions))

    detalls: list[dict] = []
    fitxes: list[dict] = []
    for fila in files:
        codi = fila.get("numeroConvocatoria")
        if not codi:
            continue
        detall = cli.fitxa(codi)
        detalls.append(detall)
        fitxes.append(normalize(detall, fila, vist_el=vist_el))

    fitxes = dedupe(fitxes)
    if save_raw:
        _save_raw(files, detalls, desde=desde, fins=fins, regions=regions)
    return fitxes


def _save_raw(
    files: list[dict],
    detalls: list[dict],
    *,
    desde: date,
    fins: date,
    regions: tuple[str, ...],
) -> None:
    out_dir = RAW_DIR / SOURCE
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_file = out_dir / "bdns_raw.json"
    raw_file.write_text(
        json.dumps({"busqueda": files, "detalls": detalls}, ensure_ascii=False, indent=0),
        encoding="utf-8",
    )
    write_provenance(
        SOURCE,
        out_dir,
        row_count=len(detalls),
        files=[raw_file.name],
        query={
            "fechaDesde": data_peticio(desde),
            "fechaHasta": data_peticio(fins),
            "regiones": ",".join(regions),
            "vpd": "GE",
        },
        extra={
            "loader": "requests (BdnsClient, fallback de 4 miralls)",
            # `write_provenance` posa per defecte l'scope del pilot de contractació
            # («Berguedà: Castellar, Berga, Consell Comarcal»), que aquí seria FALS:
            # la ingesta de subvencions és de Catalunya sencera + àmbit estatal (el
            # retall per municipi és de R2). El sobreescrivim: una procedència que
            # menteix sobre l'abast és pitjor que no tenir-ne.
            "scope": (
                "Catalunya (NUTS ES51 + les 4 províncies) + àmbit estatal "
                "(ES - ESPAÑA). El filtre per municipi/perfil és de R2."
            ),
            "note": (
                "1 fitxa = 1 convocatòria. Les regions s'enumeren explícitament: "
                "el filtre NUTS de la BDNS no cascada de la pare als fills."
            ),
        },
    )


def write_subvencions_table(
    fitxes: list[dict], *, parquet_name: str = "subvencions_bergueda.parquet"
) -> dict:
    """Materialitza les fitxes a `data/subvencions/<parquet_name>` via DuckDB.

    Casts explícits (mateix patró que `events.py`): dates a DATE, imports a
    DOUBLE, `fonts` a LIST(STRUCT(...)) — la procedència viu DINS la fila.
    """
    import duckdb
    import pandas as pd

    from .config import subvencions_path

    df = pd.DataFrame(fitxes, columns=list(SUBVENCIO_COLUMNS))
    out = subvencions_path(parquet_name)

    con = duckdb.connect()
    try:
        con.register("sub", df)
        con.execute(
            """
            CREATE TABLE subvencions AS
            SELECT
                CAST(id_bdns          AS VARCHAR) AS id_bdns,
                CAST(fonts AS STRUCT(font_clau VARCHAR, font_url VARCHAR, data_vista VARCHAR)[])
                                                  AS fonts,
                CAST(organisme        AS VARCHAR) AS organisme,
                CAST(objecte          AS VARCHAR) AS objecte,
                CAST(beneficiaris     AS VARCHAR) AS beneficiaris,
                CAST(ambit_territorial AS VARCHAR) AS ambit_territorial,
                TRY_CAST("import"     AS DOUBLE)  AS "import",
                TRY_CAST(cofinancament AS DOUBLE) AS cofinancament,
                TRY_CAST(data_publicacio AS DATE) AS data_publicacio,
                TRY_CAST(termini      AS DATE)    AS termini,
                CAST(enllac           AS VARCHAR) AS enllac,
                CAST(estat            AS VARCHAR) AS estat
            FROM sub
            """
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        con.execute("COPY subvencions TO ? (FORMAT PARQUET)", [str(out)])
        n = con.execute("SELECT count(*) FROM subvencions").fetchone()[0]
        by_estat = dict(
            con.execute(
                "SELECT estat, count(*) FROM subvencions GROUP BY estat ORDER BY 1"
            ).fetchall()
        )
        by_ambit = dict(
            con.execute(
                "SELECT ambit_territorial, count(*) FROM subvencions "
                "GROUP BY ambit_territorial ORDER BY 1"
            ).fetchall()
        )
    finally:
        con.close()

    return {
        "parquet": str(out.as_posix()),
        "rows": int(n),
        "by_estat": {k: int(v) for k, v in by_estat.items()},
        "by_ambit_territorial": {k: int(v) for k, v in by_ambit.items()},
    }


def run(*, dies_enrere: int = 1) -> dict:
    """CLI: batch diari educat (per defecte, la finestra d'ahir).

    NO produeix cap sortida cap enfora: C3 §6 (la porta humana) — el correu és R4
    i només per a perfils `actiu: true`.
    """
    from datetime import timedelta

    ahir = datetime.now(timezone.utc).date() - timedelta(days=dies_enrere)
    fitxes = fetch_fitxes(desde=ahir, fins=ahir)
    result = write_subvencions_table(fitxes)
    return {"source": SOURCE, "finestra": ahir.isoformat(), **result}


# Vocabularis re-exportats (comoditat per a R2/R3, que validen contra el contracte).
__all__ = [
    "AMBITS_SUBVENCIO",
    "ESTATS_SUBVENCIO",
    "SUBVENCIO_COLUMNS",
    "BdnsClient",
    "REGIONS_DEFAULT",
    "REGIONS_R1_SPEC",
    "clau_identitat",
    "dedupe",
    "normalize",
    "run",
]


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
