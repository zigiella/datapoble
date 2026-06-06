{# ---------------------------------------------------------------------------
   Macros de l'indicador estrella — MODEL DE 3 CAPES (mètode de Talaia, validat
   sobre dades). Tot el que produeixen és INFERÈNCIA, no cens.

   Principi: cada senyal físic per habitant és un termòmetre d'un tipus de
   presència. Si un municipi consum/genera com si tingués el doble d'habitants,
   és que n'hi ha (aprox.) el doble de presents:

       presència_estimada = padró × (senyal_per_hab / BASE)

   on BASE = el valor d'aquest senyal per a un resident "normal" (viles de vall
   poc turístiques, IETR<5, pop-ponderades). PARAMETRITZABLE (var dbt) perquè a
   escala Catalunya serà per comarca (§8). Les 3 capes usen senyals INDEPENDENTS:
     · L1 «població pernocta»  → ELÈCTRIC domèstic / base_electric  (qui DORM)
     · L2 «càrrega humana total» → RESIDUS / base_residencial       (inclou dia)
     · L3 «pressió turística»  → VIDRE (z-score comarcal, vegeu el mart)

   El macro estima L1 i L2 (mateixa forma: padró × senyal/base). round() perquè
   és una estimació de persones (enter), no un decimal fals.
--------------------------------------------------------------------------- #}

{# estimacio_presencia(poblacio, senyal_per_hab, base): capa de presència amb
   tall de BASE arbitrari. Reanomenat des de l'antic poblacio_real per encaixar
   amb el model de 3 capes (el principi és idèntic). #}
{% macro estimacio_presencia(poblacio_col, senyal_col, base) -%}
    round({{ poblacio_col }} * {{ senyal_col }} / {{ base }})
{%- endmacro %}

{# Àlies de compatibilitat: poblacio_real == estimacio_presencia. Es manté perquè
   cap referència històrica quedi trencada; els nous usos criden el nom nou. #}
{% macro poblacio_real(poblacio_col, kg_col, base) -%}
    {{ estimacio_presencia(poblacio_col, kg_col, base) }}
{%- endmacro %}
