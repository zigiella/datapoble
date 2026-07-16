"""Tests del connector BDNS → fitxa de subvenció (contracte C3, tasca R1).

**100% OFFLINE**: tot corre sobre les fixtures reals arxivades
(`fixtures/bdns_convocatories.json`) i sobre una sessió HTTP falsa que registra
les peticions. Cap test toca la xarxa ni necessita cap clau → deterministes i
aptes per a CI (llistó R1 §3).

Els números de les àncores («867 vs 6.057»…) es van mesurar en viu el 2026-07-16
i viuen documentats al docstring del connector; aquí no es re-mesuren (seria un
test de xarxa): el que es verifica és que **el codi construeix la petició que
evita la trampa**, que és el que pot regressionar.
"""
from __future__ import annotations

import datetime as dt

import pytest

from datapoble_signals import subvencions_bdns as bdns
from datapoble_signals.municipis import BERGUEDA_INE5, VALID_INE5
from datapoble_signals.schema import (
    AMBITS_SUBVENCIO,
    ESTATS_SUBVENCIO,
    SUBVENCIO_COLUMNS,
)

from .fixtures_bdns import BUSQUEDES, CONVOCATORIES, DETALLS, META, per_codi


@pytest.fixture(scope="module")
def fitxes() -> list[dict]:
    """Les 26 fixtures reals normalitzades al contracte C3 (sense xarxa)."""
    return [
        bdns.normalize(c["detall"], c["busqueda"], vist_el="2026-07-16")
        for c in CONVOCATORIES
    ]


# --- El contracte de la fila (C3 §1) -----------------------------------------

def test_fitxa_te_exactament_les_columnes_del_contracte(fitxes):
    # C3 §1: «normalitza a EXACTAMENT aquests camps» — ni un de més (cap columna
    # pròpia del connector) ni un de menys, i en ordre.
    for f in fitxes:
        assert tuple(f.keys()) == SUBVENCIO_COLUMNS


def test_vocabularis_tancats(fitxes):
    for f in fitxes:
        assert f["estat"] in ESTATS_SUBVENCIO
        assert f["ambit_territorial"] in AMBITS_SUBVENCIO


def test_cap_fitxa_sense_procedencia_ni_font_url(fitxes):
    # C3 §8.3: cap fila amb `fonts` buit o `font_url` NULL (disciplina d'events).
    for f in fitxes:
        assert f["fonts"], "fonts MAI buit"
        for p in f["fonts"]:
            assert p["font_url"], "font_url MAI NULL"
            assert p["font_clau"] == "bdns"
            assert p["data_vista"] == "2026-07-16"


def test_enllac_es_la_fitxa_publica_no_urlbasesreguladoras(fitxes):
    """`urlBasesReguladoras` és text lliure, no una URL: no pot ser l'`enllac`.

    Verificat a la font: 3 de 26 fixtures hi porten coses com «Convenio» o
    «www.labisbal.cat» (sense esquema). L'enllaç canònic és la fitxa del portal.
    """
    no_url = [
        d.get("urlBasesReguladoras")
        for d in DETALLS
        if d.get("urlBasesReguladoras")
        and not str(d["urlBasesReguladoras"]).lower().startswith("http")
    ]
    assert no_url, "la fixture ha de conservar el cas real de camp que no és URL"

    for f, d in zip(fitxes, DETALLS):
        assert f["enllac"].startswith(
            "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias/"
        )
        assert f["enllac"].endswith(str(d["codigoBDNS"]))
        assert f["enllac"] != d.get("urlBasesReguladoras")


def test_id_bdns_mai_inventat_i_coincideix_amb_la_busqueda(fitxes):
    # `numeroConvocatoria` (busqueda, pla) == `codigoBDNS` (detall, niuat).
    for f, c in zip(fitxes, CONVOCATORIES):
        assert f["id_bdns"] == str(c["detall"]["codigoBDNS"])
        assert f["id_bdns"] == str(c["busqueda"]["numeroConvocatoria"])


def test_cofinancament_sempre_null_la_font_no_el_publica(fitxes):
    # Frontera honesta: la BDNS no dona cap % a càrrec del beneficiari.
    assert all(f["cofinancament"] is None for f in fitxes)
    assert not any("cofinanc" in k.lower() for d in DETALLS for k in d)


# --- L'estat: el flag de la font mana sobre el termini ------------------------

def test_estat_deriva_d_abierto_no_del_termini(fitxes):
    for f, d in zip(fitxes, DETALLS):
        assert f["estat"] == ("oberta" if d.get("abierto") else "tancada")


def test_cas_real_tancada_amb_termini_futur(fitxes):
    """El conflicte real: `abierto=false` + `fechaFinSolicitud` FUTUR.

    Si deduíssim l'estat del termini, aquestes serien «obertes» i el radar
    prometria una convocatòria a la qual ningú es pot presentar.
    """
    conflictes = [
        (f, d)
        for f, d in zip(fitxes, DETALLS)
        if not d.get("abierto")
        and d.get("fechaFinSolicitud")
        and d["fechaFinSolicitud"] > "2026-07-16"
    ]
    assert len(conflictes) >= 5, "la fixture ha de conservar el conflicte real"
    for f, _d in conflictes:
        assert f["estat"] == "tancada"
        assert f["termini"] is not None  # el termini es guarda, però no mana


def test_termini_null_NO_vol_dir_que_no_hi_hagi_termini(fitxes):
    """⚠️ FRONTERA DEL CONTRACTE (per a R2/R4): `termini` NULL és AMBIGU.

    Mesurat sobre les 26 fixtures reals:
      -  8/26 porten `fechaFinSolicitud` (una data de veritat),
      - 11/26 NO porten data però SÍ `textFin` en **prosa** — i alguna és un
        termini ben concret: «Finaliza el 15 de septiembre de 2026», «15 Dies
        Hàbils», «Vint dies a partir de l'endemà de la publicació al BOPB»,
      -  7/26 no porten ni data ni text.

    El contracte C3 només té `termini: date|NULL`: no hi cap la prosa. Per tant
    `termini=NULL` barreja «no hi ha termini» amb «el termini existeix, escrit en
    lletres». Aquí **no s'inventa cap data** a partir del text (seria inferència
    servida com a fet, i just del camp que decideix si encara s'hi és a temps).
    Queda REPORTAT a Talaia com a possible esmena de C3 — no tapat amb un parser.
    """
    amb_data = [d for d in DETALLS if d.get("fechaFinSolicitud")]
    prosa = [d for d in DETALLS if not d.get("fechaFinSolicitud") and d.get("textFin")]
    assert amb_data and prosa, "la fixture conserva els dos casos reals"

    # Cap data inventada: si la font no dona `fechaFinSolicitud`, `termini` és NULL.
    for f, d in zip(fitxes, DETALLS):
        if not d.get("fechaFinSolicitud"):
            assert f["termini"] is None
        else:
            assert f["termini"] == d["fechaFinSolicitud"][:10]

    # I la prosa NO s'ha colat enlloc de la fitxa (ni al termini ni per la porta del darrere).
    with_text = next(d for d in prosa if "septiembre" in str(d.get("textFin", "")))
    fitxa = bdns.normalize(with_text)
    assert fitxa["termini"] is None
    assert "septiembre" not in str(fitxa["termini"])


def test_bdns_mai_emet_anul·lada(fitxes):
    # La font no té camp d'anul·lació → no l'inventem (queda per a CIDO/R5).
    assert "anul·lada" in ESTATS_SUBVENCIO           # el vocabulari la preveu…
    assert all(f["estat"] != "anul·lada" for f in fitxes)  # …però BDNS no la pot dir


# --- L'àmbit territorial (la BDNS no baixa de NUTS3) -------------------------

def test_ambit_territorial_mapa_nuts():
    def amb(*descripcions):
        return bdns.ambit_territorial(
            {"regiones": [{"descripcion": d} for d in descripcions]}
        )

    assert amb("ES - ESPAÑA ") == "estatal"
    assert amb("ES51 - CATALUÑA") == "CAT"
    assert amb("ES511 - Barcelona") == "provincia"
    assert amb("ES514 - Tarragona") == "provincia"
    # Precedència: el més ample mana.
    assert amb("ES511 - Barcelona", "ES - ESPAÑA ") == "estatal"
    assert amb("ES511 - Barcelona", "ES51 - CATALUÑA") == "CAT"


def test_bdns_mai_emet_ambit_comarcal_ni_municipal(fitxes):
    # Frontera de la font: NUTS3 (província) és el gra més fi que publica.
    assert {"comarca", "municipi"}.issubset(set(AMBITS_SUBVENCIO))
    assert all(f["ambit_territorial"] not in ("comarca", "municipi") for f in fitxes)


def test_les_fixtures_cobreixen_els_tres_ambits(fitxes):
    ambits = {f["ambit_territorial"] for f in fitxes}
    assert {"estatal", "CAT", "provincia"} <= ambits


# --- ⚠️ LA TRAMPA DE LES REGIONS (llistó R1 §4) -------------------------------

class _RespostaFalsa:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _SessioEspia:
    """Sessió HTTP falsa: registra els params i no toca mai la xarxa."""

    def __init__(self, payload=None):
        self.peticions: list[dict] = []
        self._payload = payload or {"content": [], "totalPages": 0, "totalElements": 0}

    def get(self, url, params=None, headers=None, timeout=None):
        self.peticions.append({"url": url, "params": params or {}, "headers": headers or {}})
        return _RespostaFalsa(self._payload)


def test_trampa_regions_no_cascada_la_peticio_enumera_pare_i_fills():
    """La regió pare NO cascada als fills: cal enumerar-los TOTS a la petició.

    Àncora mesurada en viu (2026-07-16, finestra 01/01–30/06/2026):
        regiones=49            → 867 convocatòries
        regiones=49,50,51,52,53 → 6.057   ← la pare sola es menja el 86%
    L'API declara l'arbre (`/api/regiones`: 49 té fills 50/51/52/53) i tot i així
    NO l'aplica al filtre. Aquest test guarda la petició, que és el que regressiona.
    """
    espia = _SessioEspia()
    cli = bdns.BdnsClient(session=espia, pausa=0, backoff=0)
    list(cli.busca(desde=dt.date(2026, 7, 15), fins=dt.date(2026, 7, 15)))

    assert espia.peticions, "s'ha d'haver fet la crida de busqueda"
    regions = espia.peticions[0]["params"]["regiones"].split(",")

    # La pare (Catalunya) NO és suficient: hi han de ser els 4 fills provincials.
    assert "49" in regions, "hi ha de ser Catalunya (ES51)"
    for fill in ("50", "51", "52", "53"):
        assert fill in regions, f"falta la província {fill}: la pare no cascada!"


def test_constants_de_regions_coherents_amb_l_arbre_nuts_verificat():
    # ids verificats a `/api/regiones` (2026-07-16).
    assert bdns.REGIO_CATALUNYA == "49"
    assert bdns.REGIONS_PROVINCIES_CAT == ("50", "51", "52", "53")
    assert set(bdns.REGIONS_R1_SPEC) == {"49", "50", "51", "52", "53"}
    # El default afegeix l'àmbit estatal (decisió documentada al connector).
    assert bdns.REGIO_ESTATAL == "1"
    assert set(bdns.REGIONS_DEFAULT) == {"1", "49", "50", "51", "52", "53"}


def test_estatal_inclos_per_defecte_els_dos_conjunts_son_disjunts():
    """Àncora: 6.057 (catalanes) + 1.275 (estatals) = 7.332 exactes → disjunts.

    Excloure l'estatal deixaria fora convocatòries ministerials a què un
    ajuntament SÍ es pot presentar: un FN de sistema (C4 §1, el pecat greu).
    """
    espia = _SessioEspia()
    cli = bdns.BdnsClient(session=espia, pausa=0, backoff=0)
    list(cli.busca(desde=dt.date(2026, 7, 15), fins=dt.date(2026, 7, 15)))
    regions = espia.peticions[0]["params"]["regiones"].split(",")
    assert "1" in regions, "l'àmbit estatal ha d'entrar a la ingesta (R2 ja filtrarà)"


# --- La trampa de codis (C3 §5): verificada, i inaplicable a BDNS ------------

def test_trampa_codis_la_bdns_no_publica_cap_codi_municipal():
    """C3 §5 demana el test de la trampa de codis a «tot connector (R1 i R5)».

    **Verificat contra les 26 fixtures reals: la BDNS no publica CAP codi
    municipal** (ni INE ni cadastral). El gra més fi és la província (NUTS3). Per
    tant R1 no pot triar malament un codi: no en toca cap. La trampa (08051 vs
    08052; 081666 → 08052…) viu al connector que SÍ que casa municipis — el filtre
    territorial de R2 i el CIDO de R5. Aquí el test que té sentit és la GUARDA
    que ho manté cert: si algun dia la fitxa emetés un codi, aquest test cau.
    """
    claus = set()

    def recorre(o):
        if isinstance(o, dict):
            for k, v in o.items():
                claus.add(k)
                recorre(v)
        elif isinstance(o, list):
            for x in o:
                recorre(x)

    recorre(DETALLS)
    recorre(BUSQUEDES)
    # L'únic «codigo» de la font és el del sector econòmic (p. ex. «93.1») i el
    # `codigoBDNS`/`codigoInvente` de la convocatòria: cap és municipal.
    assert "codigoINE" not in claus and "codigoMunicipio" not in claus
    assert "municipio" not in {k.lower() for k in claus}

    fitxa = bdns.normalize(DETALLS[0], BUSQUEDES[0])
    assert "ine5" not in fitxa and "codi_municipi" not in fitxa


def test_ancores_dels_codis_del_pilot_intactes():
    """Les àncores que R2 heretarà (C3 §5), verificades aquí perquè no derivin."""
    assert BERGUEDA_INE5["08052"] == "Castellar de n'Hug"   # NO 08051 (Cadastre)
    assert BERGUEDA_INE5["08166"] == "la Pobla de Lillet"
    assert "08051" not in VALID_INE5                        # el codi del Cadastre no hi és
    assert "081666"[:5] == "08166"                          # el tall d'Idescat (INE6 → INE5)
    assert "081666" not in VALID_INE5


# --- La clau d'identitat i el dedupe (C3 §2) ---------------------------------

def test_clau_es_bdns_quan_hi_ha_id(fitxes):
    for f in fitxes:
        assert bdns.clau_identitat(f) == f"bdns:{f['id_bdns']}"


def test_clau_es_hash_normalitzat_sense_id():
    base = {
        "id_bdns": None,
        "organisme": "Ajuntament de la Pobla de Lillet",
        "objecte": "Subvencions per a entitats",
        "termini": "2026-09-30",
    }
    k = bdns.clau_identitat(base)
    assert k.startswith("h:") and len(k) == 2 + 16

    # Normalització: accents, majúscules i espais NO fan una fitxa nova.
    variant = {
        **base,
        "organisme": "AJUNTAMENT   de la Pòbla de Lillet",
        "objecte": "Subvencions  per a Entitats",
    }
    assert bdns.clau_identitat(variant) == k

    # Una diferència REAL sí que en fa una altra (C3 §8.2: dedupe conservador).
    assert bdns.clau_identitat({**base, "objecte": "Subvencions per a entitatsX"}) != k

    # Sense termini → el literal del contracte, no un NULL silenciós.
    sense = bdns.clau_identitat({**base, "termini": None})
    assert sense == bdns.clau_identitat({**base, "termini": "sense-termini"})


def test_dedupe_una_convocatoria_dues_vistes_una_fitxa_dues_procedencies():
    """C3 §8.1: la mateixa convocatòria vista dos cops = 1 fitxa amb 2 fonts."""
    c = CONVOCATORIES[0]
    a = bdns.normalize(c["detall"], c["busqueda"], vist_el="2026-07-15")
    b = bdns.normalize(c["detall"], c["busqueda"], vist_el="2026-07-16")
    b["fonts"][0]["font_clau"] = "cido"  # simula la segona font (R5)

    out = bdns.dedupe([a, b])
    assert len(out) == 1
    assert len(out[0]["fonts"]) == 2
    assert {p["font_clau"] for p in out[0]["fonts"]} == {"bdns", "cido"}


def test_dedupe_no_duplica_la_mateixa_procedencia(fitxes):
    # Re-sync (la BDNS corregeix i esborra): re-veure la mateixa fitxa no ha
    # d'inflar `fonts`.
    c = CONVOCATORIES[0]
    a = bdns.normalize(c["detall"], c["busqueda"], vist_el="2026-07-16")
    b = bdns.normalize(c["detall"], c["busqueda"], vist_el="2026-07-16")
    out = bdns.dedupe([a, b])
    assert len(out) == 1 and len(out[0]["fonts"]) == 1


def test_dedupe_conserva_totes_les_fixtures_reals(fitxes):
    # 26 codis BDNS distints → 26 fitxes (cap fusió tova).
    assert len({f["id_bdns"] for f in fitxes}) == len(fitxes)
    assert len(bdns.dedupe(fitxes)) == len(fitxes)


# --- El text: no perdre el català -------------------------------------------

def test_objecte_conserva_el_text_catala_quan_la_font_el_dona(fitxes):
    amb_ca = [
        (f, d) for f, d in zip(fitxes, DETALLS) if d.get("descripcionLeng")
    ]
    assert len(amb_ca) >= 10, "la fixture ha de tenir prou casos amb llengua cooficial"
    for f, d in amb_ca:
        assert d["descripcionLeng"].strip() in f["objecte"]
        assert d["descripcion"].strip() in f["objecte"]


def test_objecte_no_duplica_quan_les_dues_descripcions_son_iguals():
    d = {"descripcion": "Ajuts a entitats", "descripcionLeng": "Ajuts a entitats"}
    assert bdns.normalize(d)["objecte"] == "Ajuts a entitats"


# --- Format de dates (la petició vol dd/MM/yyyy; l'ISO dona 400) -------------

def test_data_peticio_es_dd_mm_yyyy():
    assert bdns.data_peticio(dt.date(2026, 1, 9)) == "09/01/2026"
    assert bdns.data_peticio(dt.date(2026, 12, 31)) == "31/12/2026"


def test_la_peticio_no_envia_mai_dates_iso():
    espia = _SessioEspia()
    cli = bdns.BdnsClient(session=espia, pausa=0, backoff=0)
    list(cli.busca(desde=dt.date(2026, 1, 9), fins=dt.date(2026, 1, 9)))
    p = espia.peticions[0]["params"]
    assert p["fechaDesde"] == "09/01/2026" and p["fechaHasta"] == "09/01/2026"
    assert "2026-01-09" not in (p["fechaDesde"], p["fechaHasta"])  # l'ISO → HTTP 400


def test_dates_de_la_resposta_es_llegeixen_com_a_iso(fitxes):
    for f in fitxes:
        assert dt.date.fromisoformat(f["data_publicacio"])
        if f["termini"]:
            assert dt.date.fromisoformat(f["termini"])


# --- El batch educat ---------------------------------------------------------

def test_la_peticio_porta_vpd_i_user_agent_identificat():
    espia = _SessioEspia()
    cli = bdns.BdnsClient(session=espia, pausa=0, backoff=0)
    list(cli.busca(desde=dt.date(2026, 7, 15), fins=dt.date(2026, 7, 15)))
    pet = espia.peticions[0]
    assert pet["params"]["vpd"] == "GE"
    assert "datapoble" in pet["headers"]["User-Agent"]
    assert "github.com/riusdegent" in pet["headers"]["User-Agent"]


def test_paginacio_spring_base_0_i_para_a_totalpages():
    pagina = {
        "content": [{"numeroConvocatoria": "1"}],
        "totalPages": 3,
        "totalElements": 3,
    }
    espia = _SessioEspia(pagina)
    cli = bdns.BdnsClient(session=espia, pausa=0, backoff=0)
    files = list(cli.busca(desde=dt.date(2026, 7, 15), fins=dt.date(2026, 7, 15)))
    assert len(files) == 3
    assert [p["params"]["page"] for p in espia.peticions] == [0, 1, 2]


def test_fallback_de_miralls_si_el_primer_falla():
    class _SessioTrencada(_SessioEspia):
        def get(self, url, params=None, headers=None, timeout=None):
            self.peticions.append({"url": url, "params": params or {}, "headers": headers or {}})
            if "infosubvenciones.es" in url:
                raise OSError("mirall caigut")
            return _RespostaFalsa({"content": [], "totalPages": 0})

    espia = _SessioTrencada()
    cli = bdns.BdnsClient(session=espia, pausa=0, backoff=0)
    list(cli.busca(desde=dt.date(2026, 7, 15), fins=dt.date(2026, 7, 15)))
    hosts = [p["url"].split("/bdnstrans")[0] for p in espia.peticions]
    assert "https://www.infosubvenciones.es" in hosts       # ha provat el primer…
    assert "https://www.pap.hacienda.gob.es" in hosts       # …i ha caigut al mirall


def test_si_tots_els_miralls_fallen_peta_no_calla():
    """Un silenci que sembli «cap convocatòria» seria el pitjor error possible."""

    class _TotTrencat(_SessioEspia):
        def get(self, url, params=None, headers=None, timeout=None):
            raise OSError("xarxa morta")

    cli = bdns.BdnsClient(session=_TotTrencat(), pausa=0, backoff=0)
    with pytest.raises(RuntimeError, match="miralls han fallat"):
        list(cli.busca(desde=dt.date(2026, 7, 15), fins=dt.date(2026, 7, 15)))


# --- La porta humana (C3 §6) i l'abast de R1 ---------------------------------

def test_el_connector_no_te_cap_sortida_cap_enfora():
    """Llistó R1 §5 + C3 §6: R1 ingesta i prou. El correu és R4 (i només `actiu`)."""
    codi = (bdns.__file__ and open(bdns.__file__, encoding="utf-8").read()) or ""
    for prohibit in ("smtplib", "import email", "sendmail", "send_message"):
        assert prohibit not in codi, f"R1 no pot enviar res: {prohibit!r}"


# --- Materialització (parquet + procedència) ---------------------------------

def test_parquet_tipat_i_consultable(fitxes, tmp_path, monkeypatch):
    import duckdb

    from datapoble_signals import config

    monkeypatch.setattr(config, "SUBVENCIONS_DIR", tmp_path)
    res = bdns.write_subvencions_table(fitxes, parquet_name="t.parquet")
    assert res["rows"] == len(fitxes)
    assert sum(res["by_estat"].values()) == len(fitxes)

    con = duckdb.connect()
    # Els casts del contracte: dates com a DATE, imports com a DOUBLE.
    tipus = dict(
        con.execute(
            "SELECT column_name, column_type FROM (DESCRIBE SELECT * FROM read_parquet(?))",
            [res["parquet"]],
        ).fetchall()
    )
    assert tipus["data_publicacio"] == "DATE"
    assert tipus["termini"] == "DATE"
    assert tipus["import"] == "DOUBLE"
    assert tipus["fonts"].startswith("STRUCT(")

    # C3 §8.3 sobre el parquet real: cap fila sense procedència traçable.
    dolentes = con.execute(
        "SELECT count(*) FROM read_parquet(?) "
        "WHERE len(fonts) = 0 OR fonts[1].font_url IS NULL OR enllac IS NULL",
        [res["parquet"]],
    ).fetchone()[0]
    assert dolentes == 0
    con.close()


# --- Les fixtures són arxiu real (llistó R1 §3, C4 §2) -----------------------

def test_les_fixtures_son_reals_variades_i_suficients():
    assert len(CONVOCATORIES) >= 15, "llistó R1 §3: ≥15 convocatòries"
    nivells = {d["organo"]["nivel1"] for d in DETALLS}
    assert "LOCAL" in nivells, "cal cobrir convocatòries locals catalanes"
    assert len(nivells) >= 3, "cal varietat d'administració convocant"

    obertes = sum(1 for d in DETALLS if d.get("abierto"))
    assert 0 < obertes < len(DETALLS), "cal cobrir obertes i tancades"

    assert META["fetched_at"].startswith("2026-07-16")
    assert "avisolegal" in META["avis_legal_font"]


def test_la_fixture_conserva_l_avis_legal_de_la_font():
    # L'avís legal viatja DINS de cada fitxa (`advertencia`): respectar-lo és part
    # del llistó, i no s'esborra de l'arxiu.
    amb_avis = [d for d in DETALLS if d.get("advertencia")]
    assert amb_avis, "la font emet un avís legal per fitxa: es conserva"
    assert "avisolegal" in amb_avis[0]["advertencia"]


def test_hi_ha_una_convocatoria_amb_regio_pare_catalunya():
    """Les que `regiones=49` SÍ que troba: les etiquetades a l'arrel ES51.

    Són la contrapart de la trampa — la resta (províncies) desapareixen si només
    demanes la pare.
    """
    pare = [
        d for d in DETALLS
        if any((r.get("descripcion") or "").startswith("ES51 -") for r in (d.get("regiones") or []))
    ]
    provincia = [
        d for d in DETALLS
        if any(
            (r.get("descripcion") or "").startswith(("ES511", "ES512", "ES513", "ES514"))
            for r in (d.get("regiones") or [])
        )
    ]
    assert pare and provincia, "la fixture cobreix els dos costats de la trampa"


def test_la_procedencia_no_menteix_sobre_l_abast(tmp_path, monkeypatch):
    """El sidecar per càrrega (C3 §1) ha de dir l'abast REAL de la ingesta.

    `write_provenance` porta per defecte l'scope del pilot de contractació; per a
    subvencions seria fals (aquí s'ingereix Catalunya + estatal). Una procedència
    que menteix sobre l'abast és pitjor que no tenir-ne.
    """
    import json

    from datapoble_signals import config

    monkeypatch.setattr(config, "RAW_DIR", tmp_path)
    monkeypatch.setattr(bdns, "RAW_DIR", tmp_path)
    bdns._save_raw(
        [BUSQUEDES[0]], [DETALLS[0]],
        desde=dt.date(2026, 7, 14), fins=dt.date(2026, 7, 14),
        regions=bdns.REGIONS_DEFAULT,
    )
    rec = json.loads((tmp_path / bdns.SOURCE / "_provenance.json").read_text(encoding="utf-8"))
    assert "Catalunya" in rec["scope"] and "estatal" in rec["scope"]
    assert "Castellar, Berga, Consell Comarcal" not in rec["scope"]  # l'scope d'una altra font
    assert rec["query"]["regiones"] == "1,49,50,51,52,53"
    assert rec["query"]["fechaDesde"] == "14/07/2026"          # dd/MM/yyyy, no ISO
    assert "avisolegal" in rec["llicencia"]                    # la font no té llicència oberta
    assert rec["row_count"] == 1


def test_per_codi_troba_una_fixture_coneguda():
    c = per_codi(DETALLS[0]["codigoBDNS"])
    assert c["detall"]["codigoBDNS"] == DETALLS[0]["codigoBDNS"]
