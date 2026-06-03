"""Files crues de mostra de ``ybgg-dgi6`` per a tests offline (deterministes).

Mostres reals (anonimitzades en el sentit que no afegim res; són files públiques)
que cobreixen els casos límit del normalitzador:
  - municipal amb CPV fort (Berga, cultura) → ine5 + confiança alta.
  - municipal amb CPV de via (Castellar) → mobilitat_via.
  - supramunicipal (Consell Comarcal) → ambit comarcal, ine5 NULL.
  - sense CPV, rescatat per paraula clau → confiança feble.
  - sense CPV ni paraula clau → altres, confiança mínima.
  - lot (mateix expedient, numero_lot diferent) → event_id distint.
  - sense data d'adjudicació → fallback a data de publicació/anunci.
  - sense enllaç → font_url cau a la URL del dataset (mai NULL).
"""
from __future__ import annotations

SAMPLE_RAW: list[dict] = [
    {
        "codi_ine10": "0802200001",
        "nom_organ": "Ajuntament de Berga",
        "codi_expedient": "EXP-CULT-1",
        "codi_dir3": "L01080222",
        "codi_organ": "1001",
        "codi_cpv": "92312130-1",
        "objecte_contracte": "Serveis tècnics per als actes de La Patum",
        "data_adjudicacio_contracte": "2024-05-12T00:00:00.000",
        "import_adjudicacio_sense": "18000.00",
        "enllac_publicacio": {"url": "https://contractaciopublica.cat/detall/aaa"},
    },
    {
        "codi_ine10": "0805200001",
        "nom_organ": "Ajuntament de Castellar de n'Hug",
        "codi_expedient": "EXP-VIA-1",
        "codi_dir3": "L01080522",
        "codi_organ": "1002",
        "codi_cpv": "45233140-2",
        "objecte_contracte": "Obres de pavimentació del camí d'accés",
        "data_adjudicacio_contracte": "2022-11-22T00:00:00.000",
        "import_adjudicacio_sense": "69500.00",
        "enllac_publicacio": {"url": "https://contractaciopublica.cat/detall/bbb"},
    },
    {
        "codi_ine10": "8101410007",
        "nom_organ": "Consell Comarcal del Berguedà",
        "codi_expedient": "EXP-COM-1",
        "codi_dir3": "L06090832",
        "codi_organ": "3001",
        "codi_cpv": "79952000-2",
        "objecte_contracte": "Organització d'activitats de promoció turística comarcal",
        "data_adjudicacio_contracte": "2021-07-27T00:00:00.000",
        "import_adjudicacio_sense": "134183.23",
        "enllac_publicacio": {"url": "https://contractaciopublica.cat/detall/ccc"},
    },
    {
        # Sense CPV; rescatat per paraula clau 'neteja' → confiança feble.
        "codi_ine10": "0802200001",
        "nom_organ": "Ajuntament de Berga",
        "codi_expedient": "EXP-NETEJA-1",
        "codi_dir3": "L01080222",
        "codi_organ": "1001",
        "codi_cpv": None,
        "objecte_contracte": "Servei de neteja viària i recollida de residus",
        "data_adjudicacio_contracte": "2023-03-01T00:00:00.000",
        "import_adjudicacio_sense": "42000.00",
        "enllac_publicacio": {"url": "https://contractaciopublica.cat/detall/ddd"},
    },
    {
        # Sense CPV ni paraula clau → altres, confiança mínima. Sense enllaç →
        # font_url ha de caure a la URL del dataset (mai NULL).
        "codi_ine10": "0802200001",
        "nom_organ": "Ajuntament de Berga",
        "codi_expedient": "EXP-MISC-1",
        "codi_dir3": "L01080222",
        "codi_organ": "1001",
        "codi_cpv": None,
        "objecte_contracte": "Subministrament de material divers d'oficina",
        "data_adjudicacio_contracte": "2023-09-10T00:00:00.000",
        "import_adjudicacio_sense": "0",
        "enllac_publicacio": None,
    },
    {
        # Lot A d'una licitació partida (mateix expedient que el següent).
        "codi_ine10": "8101410007",
        "nom_organ": "Consell Comarcal del Berguedà",
        "codi_expedient": "EXP-LOT-9",
        "codi_dir3": "L06090832",
        "codi_organ": "3001",
        "numero_lot": "1",
        "codi_cpv": "60130000-8",
        "objecte_contracte": "Transport escolar — lot 1",
        "data_adjudicacio_contracte": "2023-07-20T00:00:00.000",
        "import_adjudicacio_sense": "7983.98",
        "enllac_publicacio": {"url": "https://contractaciopublica.cat/detall/eee"},
    },
    {
        # Lot B: tot igual excepte numero_lot → event_id ha de ser distint.
        "codi_ine10": "8101410007",
        "nom_organ": "Consell Comarcal del Berguedà",
        "codi_expedient": "EXP-LOT-9",
        "codi_dir3": "L06090832",
        "codi_organ": "3001",
        "numero_lot": "3",
        "codi_cpv": "60130000-8",
        "objecte_contracte": "Transport escolar — lot 1",
        "data_adjudicacio_contracte": "2023-07-20T00:00:00.000",
        "import_adjudicacio_sense": "22198.48",
        "enllac_publicacio": {"url": "https://contractaciopublica.cat/detall/eee"},
    },
    {
        # Sense data d'adjudicació (fase oberta) → fallback a publicació.
        "codi_ine10": "0802200001",
        "nom_organ": "Ajuntament de Berga",
        "codi_expedient": "EXP-OBERT-1",
        "codi_dir3": "L01080222",
        "codi_organ": "1001",
        "codi_cpv": "90910000-9",
        "objecte_contracte": "Servei de neteja d'edificis municipals",
        "data_adjudicacio_contracte": None,
        "data_publicacio_contracte": "2022-10-14T11:12:00.000",
        "import_adjudicacio_sense": None,
        "enllac_publicacio": {"url": "https://contractaciopublica.cat/detall/fff"},
    },
]
