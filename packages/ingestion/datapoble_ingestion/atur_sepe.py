"""Connector atur registrat mensual — SEPE «Paro registrado por municipios» (D1).

Primera família MENSUAL del catàleg (contracte C1 §1.1, ESMENAT: la font Socrata
de l'spec original NO existeix — verificat en viu 2026-07-16 per Talaia). Font
real: CSV anual-amb-mesos del SEPE, un fitxer per any des de 2006, sense clau:

    https://sede.sepe.gob.es/es/portaltrabaja/resources/sede/datos_abiertos/datos/
    Paro_por_municipios_<ANY>_csv.csv

Fets verificats en viu (Sondeig, 2026-07-17):
  · Format: ISO-8859-1, separador ``;``, CRLF; línia 1 = títol, línia 2 = capçalera,
    20 columnes (mes, CA, província, municipi, total + sexe×edat + sectors).
  · ⚠️ TRAMPA DEL ZERO-PAD: el 2026 serveix ``08022`` (Berga) però el 2006 serveix
    ``8022`` — el zero-pad a 5 és OBLIGATORI sempre (C1 §1.1).
  · ⚠️ El servidor pot tornar **206 Partial Content** i tallar el cos (verificat:
    una descàrrega de 9,7 MB va arribar tallada a 256 KiB) → descàrrega amb
    verificació de longitud i represa per ``Range``.
  · Gósol surt com a **25100** (= ine5 Idescat-derivat del nostre catàleg, NO
    l'INE canònic 25101) i Gombrèn com a **17080**: el filtre pel catàleg de
    Catalunya sencer (947 ine5) hi encaixa IDENTITAT — cobertura 947/947 tots els
    mesos de 2026, sense crosswalk. Si la font canviés de codis, la cobertura
    cauria i el verificador ho faria petar (soroll, no silenci).
  · Doctrina del «<5» (C1 §1.1, VINCULANT): des de gener 2022 el SEPE emmascara
    els valors 1–4 com a ``<5``. Un ``<5`` és un **interval [1, 4]** — MAI un
    zero, MAI un NaN silenciós. Es modela amb ``atur_registrat`` NULL +
    ``atur_registrat_min/max`` = [1, 4] + ``atur_emmascarat`` = true; la UI el
    mostra com a «<5». (El juny de 2026, 139 dels 947 municipis venien emmascarats.)
  · Llicència (verificada literalment 2026-07-17 a l'avís legal de la seu del
    SEPE): reutilització comercial i no comercial segons l'art. 7 del RD 1495/2011
    (desplega la Llei 37/2007), amb cita obligada de la font.

FILTRE: pel CATÀLEG DE CATALUNYA sencer (els 947 ine5 de
``data/territorial/municipis-catalunya.csv``), MAI per província ni per comarca —
Gósol és Lleida (25100) i Gombrèn és Girona (17080, el Ripollès): qualsevol llista
provincial o comarcal tornaria a quedar curta. El volum és trivial (~947×12
files/any). El rang comarcal (D4) es calcula aigües avall contra la comarca del
municipi, mai contra una llista fixa aquí.

Sortida: ``data/raw/atur_sepe/paro_municipis_<ANY>.parquet`` (un per any; re-córrer
un any el substitueix → refresh incremental idempotent) + ``_provenance.json``.
Aigües avall: ``stg_atur_sepe`` → ``mart_pols_mensual`` (camp ``date`` "YYYY-MM").

El refresh és cosa del workflow programat ``refresh-atur.yml`` (cron mensual),
MAI del CI de PR: el CI corre 100% offline sobre la fixture arxivada a
``tests/fixtures/`` (vegeu ``tests/test_atur_sepe.py``).
"""
from __future__ import annotations

import csv
import io
import sys
import time
from datetime import date as _date
from typing import Iterable, Mapping

import pandas as pd
import requests

from .config import SEPE_ATUR_URL_TEMPLATE, raw_path
from .municipis import CATALUNYA_INE5
from .provenance import write_provenance

SOURCE = "atur_sepe"
FIRST_YEAR = 2006          # primer any publicat (verificat en viu: el fitxer 2006 existeix)
ENCODING = "latin-1"       # ISO-8859-1 verificat 2026-07-17
MASK = "<5"                # secret estadístic SEPE (des de 2022-01): interval [1, 4]
MASK_MIN, MASK_MAX = 1, 4
TIMEOUT = 120
MAX_ATTEMPTS = 6
USER_AGENT = "datapoble/0.1 (observatori de dades territorials; +https://github.com/zigiella/datapoble)"

# Capçalera EXACTA del CSV (cel·les .strip()). Si el SEPE la canvia, petem amb
# soroll — mai un mapeig posicional silenciós sobre un fitxer que ha mutat.
EXPECTED_HEADER = [
    "Código mes", "mes", "Código de CA", "Comunidad Autónoma",
    "Codigo Provincia", "Provincia", "Codigo Municipio", "Municipio",
    "total Paro Registrado",
    "Paro hombre edad < 25", "Paro hombre edad 25 -45", "Paro hombre edad >=45",
    "Paro mujer edad < 25", "Paro mujer edad 25 -45", "Paro mujer edad >=45",
    "Paro Agricultura", "Paro Industria", "Paro Construcción", "Paro Servicios",
    "Paro Sin empleo Anterior",
]

# Noms canònics de columna (mateix ordre que EXPECTED_HEADER). Els valors
# desagregats es guarden com a TEXT tal com vénen (fidelitat a la font: hi viuen
# els "<5"); la doctrina de l'interval s'aplica al total, que és la mètrica C1.
CANONICAL_COLUMNS = [
    "codigo_mes", "mes", "codigo_ca", "comunidad_autonoma",
    "codigo_provincia", "provincia", "codigo_municipio", "municipio",
    "total_paro_registrado",
    "paro_h_lt25", "paro_h_25_45", "paro_h_ge45",
    "paro_d_lt25", "paro_d_25_45", "paro_d_ge45",
    "paro_agricultura", "paro_industria", "paro_construccio", "paro_serveis",
    "paro_sense_ocupacio_anterior",
]

class SepeFormatError(RuntimeError):
    """El CSV del SEPE no té el format verificat (capçalera o valors) — fallo sorollós."""


def parse_total(raw: str) -> tuple[int | None, int, int, bool]:
    """Doctrina del «<5» (C1 §1.1): retorna (valor, min, max, emmascarat).

    · valor exacte  → (n, n, n, False)
    · ``<5``        → (None, 1, 4, True)  — interval, MAI zero ni NaN silenciós
    · qualsevol altra cosa → excepció (cap valor no numèric passa en silenci)
    """
    v = raw.strip()
    if v == MASK:
        return None, MASK_MIN, MASK_MAX, True
    if not v.isdigit():
        raise SepeFormatError(f"total Paro Registrado no numèric ni {MASK!r}: {raw!r}")
    n = int(v)
    return n, n, n, False


def parse_any_csv(text: str, catalog: Mapping[str, str] | None = None) -> list[dict]:
    """Aplana el CSV anual del SEPE i FILTRA pel catàleg de Catalunya (947 ine5).

    ``catalog`` = ``ine5 -> nom`` (per defecte, el registre dels 947). El codi de
    municipi es zero-padeja a 5 ABANS de mirar el catàleg (trampa 2006: ``8022``).
    El filtre és per PERTINENÇA AL CATÀLEG, mai per província ni CA.
    """
    if catalog is None:
        catalog = CATALUNYA_INE5
    if not catalog:
        raise SepeFormatError(
            "catàleg de Catalunya buit (data/territorial/municipis-catalunya.csv "
            "absent?) — sense catàleg no hi ha filtre honest, no s'ingereix res"
        )

    reader = csv.reader(io.StringIO(text), delimiter=";")
    try:
        title = next(reader)
        header = next(reader)
    except StopIteration as exc:
        raise SepeFormatError("CSV massa curt: falta títol o capçalera") from exc
    if "PARO REGISTRADO POR MUNICIPIOS" not in ";".join(title):
        raise SepeFormatError(f"línia de títol inesperada: {title!r}")
    stripped = [cell.strip() for cell in header]
    if stripped != EXPECTED_HEADER:
        raise SepeFormatError(f"capçalera del SEPE ha canviat: {stripped!r}")

    rows: list[dict] = []
    for raw_row in reader:
        if not raw_row or not any(cell.strip() for cell in raw_row):
            continue  # línia buida final
        if len(raw_row) != len(CANONICAL_COLUMNS):
            raise SepeFormatError(f"fila amb {len(raw_row)} columnes (esperades "
                                  f"{len(CANONICAL_COLUMNS)}): {raw_row[:8]!r}…")
        ine5 = raw_row[6].strip().zfill(5)  # zero-pad OBLIGATORI (2006: '8022')
        if ine5 not in catalog:
            continue  # fora del catàleg de Catalunya (no per província: pel catàleg)
        codigo_mes = raw_row[0].strip()
        if not (len(codigo_mes) == 6 and codigo_mes.isdigit()):
            raise SepeFormatError(f"Código mes no és AAAAMM: {codigo_mes!r}")
        total, t_min, t_max, masked = parse_total(raw_row[8])
        row = dict(zip(CANONICAL_COLUMNS, (cell.strip() for cell in raw_row)))
        row.update(
            ine5=ine5,
            date=f"{codigo_mes[:4]}-{codigo_mes[4:6]}",  # "YYYY-MM" (C1 §1.1)
            atur_registrat=total,
            atur_registrat_min=t_min,
            atur_registrat_max=t_max,
            atur_emmascarat=masked,
        )
        rows.append(row)
    return rows


def rows_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    """DataFrame tipat: interval en enters nullables, la resta text fidel a la font."""
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["atur_registrat"] = df["atur_registrat"].astype("Int64")
    df["atur_registrat_min"] = df["atur_registrat_min"].astype("Int64")
    df["atur_registrat_max"] = df["atur_registrat_max"].astype("Int64")
    df["atur_emmascarat"] = df["atur_emmascarat"].astype(bool)
    return df


def _body_ok(resp: "requests.Response") -> tuple[bool, str]:
    """El cos d'una resposta és un CSV SENCER? (longitud + darrera línia completa).

    No es refia del Content-Range: el servidor n'arriba a servir DOS de contradictoris
    a la mateixa resposta (verificat en viu), un d'ells un sentinella de 2 GiB.
    """
    if resp.status_code not in (200, 206):
        return False, f"HTTP {resp.status_code}"
    body = resp.content
    if not body:
        return False, "cos buit"
    cl = resp.headers.get("Content-Length")
    if cl and cl.isdigit() and len(body) != int(cl):
        return False, f"{len(body)} bytes != Content-Length {cl}"
    if not body.endswith(b"\n"):
        return False, "cos tallat: no acaba en salt de línia"
    last_line = body.rstrip(b"\r\n").rsplit(b"\n", 1)[-1]
    if last_line.count(b";") != len(CANONICAL_COLUMNS) - 1:
        return False, "cos tallat: darrera línia incompleta"
    return True, ""


# FORATS DE LA FONT, verificats en viu (2026-07-17, fitxers sencers re-descarregats
# i recomptats): el CSV anual del SEPE de 2013 només porta gener–abril (la resta
# del 2013 només existeix en XLS semestrals, fora d'abast de D1), i el de 2020
# perd el desembre. Es DECLAREN aquí — el forat és de la font, no nostre — i la
# guarda els exigeix EXACTES: si el SEPE mai repara aquests fitxers, això peta
# amb soroll i llavors ampliem la sèrie (mai un canvi de font en silenci).
KNOWN_SOURCE_GAPS: dict[int, int] = {
    2013: 4,   # només 2013-01 … 2013-04
    2020: 11,  # només 2020-01 … 2020-11 (falta el desembre)
}


def _check_year_months(year: int, rows: list[dict], *, is_current: bool) -> None:
    """Defensa en profunditat contra fitxers a mitges: un any passat ha de dur els
    12 mesos (tret dels forats DECLARATS de la font), i l'any en curs una seqüència
    contigua des del gener. Si un intermediari colés un prefix del fitxer que
    passés les guardes de descàrrega, aquí petaria igualment — mai un any coix en
    silenci."""
    months = sorted({r["date"] for r in rows})
    if not months:
        raise SepeFormatError(f"{year}: cap fila del catàleg de Catalunya al CSV")
    if year in KNOWN_SOURCE_GAPS:
        n_expected = KNOWN_SOURCE_GAPS[year]
    elif is_current:
        n_expected = len(months)
    else:
        n_expected = 12
    expected = [f"{year}-{m:02d}" for m in range(1, n_expected + 1)]
    if months != expected:
        raise SepeFormatError(f"{year}: mesos {months} ≠ esperats {expected}")


def download_year(year: int, session: requests.Session | None = None) -> str:
    """Descarrega el CSV d'un any amb ``Range: bytes=0-`` i verificació del cos.

    El servidor de la seu del SEPE és voluble (verificat en viu 2026-07-17): a un
    GET pla li pot respondre 206 amb una FINESTRA de 256 KiB del fitxer, i un
    intermediari arriba a CACHEJAR la finestra com si fos l'objecte sencer (des
    d'aleshores serveix ``Content-Range: bytes 0-262143/262144`` i rebutja la
    represa amb 416). Antídots verificats: ``Range: bytes=0-`` (demana el rang
    complet) + ``Cache-Control/Pragma: no-cache`` (travessa la còpia enverinada).
    Estratègia: demanar sempre així i NO acceptar cap cos que no passi
    ``_body_ok`` (longitud declarada + darrera línia completa); reintents amb
    backoff, fallo sorollós al final.
    404 → FileNotFoundError (el tracta ``run``: només és esperable per a l'any en
    curs abans de la primera publicació).
    """
    url = SEPE_ATUR_URL_TEMPLATE.format(any=year)
    headers = {
        "User-Agent": USER_AGENT,
        "Range": "bytes=0-",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    reason = "cap intent"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        # Reintents: connexió NOVA (el keep-alive et pot deixar clavat al node
        # enverinat) + query de trenca-caché (canvia la clau de caché; el servidor
        # d'estàtics la ignora — verificat en viu sobre una còpia enverinada).
        sess = (session or requests.Session()) if attempt == 1 else requests.Session()
        url_try = url if attempt <= 2 else f"{url}?nc={int(time.time())}"
        try:
            resp = sess.get(url_try, headers=headers, timeout=TIMEOUT)
        except requests.RequestException as exc:
            if attempt == MAX_ATTEMPTS:
                raise
            print(f"[atur_sepe] {year} intent {attempt}: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            time.sleep(attempt)
            continue
        if resp.status_code == 404:
            raise FileNotFoundError(url)
        ok, reason = _body_ok(resp)
        if ok:
            return resp.content.decode(ENCODING)
        print(f"[atur_sepe] {year} intent {attempt}: descarto la resposta ({reason}; "
              f"CR={resp.headers.get('Content-Range')})", file=sys.stderr)
        time.sleep(attempt)  # backoff educat abans del següent intent
    raise SepeFormatError(
        f"descàrrega no fiable de {url} després de {MAX_ATTEMPTS} intents ({reason})"
    )


def run(years: Iterable[int] | None = None, pause: float = 1.0) -> dict:
    """Ingesta de l'atur registrat SEPE, filtrada pel catàleg dels 947.

    ``years=None`` → tota la sèrie (2006 → any en curs). Un parquet per any
    (re-córrer un any el substitueix). El fitxer de l'any en curs pot no existir
    encara al gener (la primera publicació de l'any arriba al febrer): s'omet amb
    soroll a stderr, mai en silenci.
    """
    today = _date.today()
    ys = sorted(years) if years else list(range(FIRST_YEAR, today.year + 1))
    out_dir = raw_path(SOURCE)
    session = requests.Session()

    files: list[str] = []
    skipped: list[int] = []
    n_rows = 0
    last_month: str | None = None
    coverage_last_month = 0
    for year in ys:
        try:
            text = download_year(year, session=session)
        except FileNotFoundError:
            if year >= today.year:
                print(f"[atur_sepe] {year}: encara no publicat (404) — s'omet", file=sys.stderr)
                skipped.append(year)
                continue
            raise  # un any passat que falta és un problema de veritat: soroll
        rows = parse_any_csv(text)
        _check_year_months(year, rows, is_current=(year == today.year))
        df = rows_to_dataframe(rows)
        out_file = out_dir / f"paro_municipis_{year}.parquet"
        df.to_parquet(out_file, index=False)
        files.append(out_file.name)
        n_rows += len(df)
        year_last = df["date"].max()
        if last_month is None or year_last > last_month:
            last_month = year_last
            coverage_last_month = int(df.loc[df["date"] == year_last, "ine5"].nunique())
        if pause:
            time.sleep(pause)  # cortesia amb la seu del SEPE (l'avís legal es respecta)

    n_catalog = len(CATALUNYA_INE5)
    if last_month and coverage_last_month != n_catalog:
        print(
            f"[atur_sepe] AVÍS: cobertura del darrer mes ({last_month}) = "
            f"{coverage_last_month}/{n_catalog} municipis del catàleg",
            file=sys.stderr,
        )
    write_provenance(
        SOURCE,
        out_dir,
        row_count=n_rows,
        files=files,
        query={"years": ys, "filtre": "catàleg de Catalunya sencer (947 ine5), mai per província"},
        extra={
            "loader": "requests (CSV anual, ISO-8859-1)",
            "scope": "Catalunya (947 municipis)",
            "darrer_mes": last_month,
            "cobertura_darrer_mes": coverage_last_month,
            "anys_omesos_404": skipped,
            "forats_de_la_font": {
                "2013": "el CSV del SEPE només porta 2013-01…2013-04 (verificat 2026-07-17)",
                "2020": "el CSV del SEPE perd el 2020-12 (verificat 2026-07-17)",
            },
            "doctrina_<5": "interval [1,4]: atur_registrat NULL + min/max + atur_emmascarat",
            "cita_obligada": "Origen de los datos: Servicio Público de Empleo Estatal",
        },
    )
    return {
        "source": SOURCE,
        "rows": n_rows,
        "files": files,
        "darrer_mes": last_month,
        "cobertura_darrer_mes": coverage_last_month,
    }


if __name__ == "__main__":
    print(run())
