"""Files crues de mostra de ``i5n8-43cw`` (ACA) per a tests offline (deterministes).

Mostres reals (files públiques de l'històric del Berguedà; no afegim res) que
cobreixen els casos del normalitzador de sequera:
  - municipi del Berguedà amb estat fort (Berga, EXCEPCIONALITAT) → confiança alta.
  - mateix municipi, canvi a un estat més suau (ALERTA) → confiança menor.
  - estat de base (NORMALITAT) → confiança mínima (no és senyal de pressió).
  - municipi micro (Gósol, 25100) → ine5 correcte des d'INE6.
  - mateix municipi + data, canvi NOMÉS pluviomètric (hidrològic igual) →
    event_id distint (els dos eixos entren a la clau).
  - codi de municipi INE6 → ine5 = [:5] (clau de join amb mart_municipi).
"""
from __future__ import annotations

SAMPLE_RAW: list[dict] = [
    {
        # Berga, pic de la crisi: EXCEPCIONALITAT (estat fort → confiança alta).
        "data_canvi_estat_sequera": "2023-05-11T00:00:00.000",
        "codi_unitat_explotaci": "16",
        "unitat_explotaci": "Mig Llobregat",
        "codi_estat_sequera_hidrol": "00007",
        "estat_sequera_hidrol_gic": "EXCEPCIONALITAT",
        "codi_estat_sequera_pluviom": "00003",
        "estat_sequera_pluviom_tric": "SEQUERA EXTREMA",
        "codi_municipi": "080229",
        "municipi": "Berga",
    },
    {
        # Berga, recuperació: baixa a ALERTA (estat més suau → confiança menor).
        "data_canvi_estat_sequera": "2024-07-29T00:00:00.000",
        "codi_unitat_explotaci": "16",
        "unitat_explotaci": "Mig Llobregat",
        "codi_estat_sequera_hidrol": "00006",
        "estat_sequera_hidrol_gic": "ALERTA",
        "codi_estat_sequera_pluviom": "00001",
        "estat_sequera_pluviom_tric": "NORMALITAT",
        "codi_municipi": "080229",
        "municipi": "Berga",
    },
    {
        # Berga torna a NORMALITAT (estat de base → confiança mínima).
        "data_canvi_estat_sequera": "2025-03-26T00:00:00.000",
        "codi_unitat_explotaci": "16",
        "unitat_explotaci": "Mig Llobregat",
        "codi_estat_sequera_hidrol": "00004",
        "estat_sequera_hidrol_gic": "NORMALITAT",
        "codi_estat_sequera_pluviom": "00001",
        "estat_sequera_pluviom_tric": "NORMALITAT",
        "codi_municipi": "080229",
        "municipi": "Berga",
    },
    {
        # Gósol (25100): micromunicipi amb INE6 '251001' → ine5 '25100'.
        "data_canvi_estat_sequera": "2023-05-11T00:00:00.000",
        "codi_unitat_explotaci": "06",
        "unitat_explotaci": "Capçalera del Llobregat",
        "codi_estat_sequera_hidrol": "00007",
        "estat_sequera_hidrol_gic": "EXCEPCIONALITAT",
        "codi_estat_sequera_pluviom": "00003",
        "estat_sequera_pluviom_tric": "SEQUERA EXTREMA",
        "codi_municipi": "251001",
        "municipi": "Gósol",
    },
    {
        # Castellar de n'Hug, mateixa data que el següent, canvi NOMÉS pluviomètric
        # (hidrològic PREALERTA es manté): event_id ha de ser distint del següent.
        "data_canvi_estat_sequera": "2022-01-28T00:00:00.000",
        "codi_unitat_explotaci": "06",
        "unitat_explotaci": "Capçalera del Llobregat",
        "codi_estat_sequera_hidrol": "00005",
        "estat_sequera_hidrol_gic": "PREALERTA",
        "codi_estat_sequera_pluviom": "00002",
        "estat_sequera_pluviom_tric": "SEQUERA SEVERA",
        "codi_municipi": "080522",
        "municipi": "Castellar de n'Hug",
    },
    {
        # Castellar de n'Hug, mateixa data i hidrològic, però pluviomètric distint
        # (EXTREMA) → és una fila distinta a la font → event_id distint.
        "data_canvi_estat_sequera": "2022-01-28T00:00:00.000",
        "codi_unitat_explotaci": "06",
        "unitat_explotaci": "Capçalera del Llobregat",
        "codi_estat_sequera_hidrol": "00005",
        "estat_sequera_hidrol_gic": "PREALERTA",
        "codi_estat_sequera_pluviom": "00003",
        "estat_sequera_pluviom_tric": "SEQUERA EXTREMA",
        "codi_municipi": "080522",
        "municipi": "Castellar de n'Hug",
    },
]
