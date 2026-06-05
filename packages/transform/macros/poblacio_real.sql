{# ---------------------------------------------------------------------------
   Macros de l'indicador estrella "població real estimada vs padró".
   Mètode validat per Talaia: docs/poblacio-real-metode.md (§2 principi, §4 base,
   §7 materialització). Tot el que produeixen és INFERÈNCIA, no cens.

   Principi (§2): la generació de residus per habitant és un termòmetre de
   presència humana real. Si un municipi genera residus com si tingués el doble
   d'habitants, és que n'hi ha (aprox.) el doble de presents:

       presència_estimada = padró × (kg_residus_per_hab / BASE)

   on BASE = generació per càpita d'un resident "normal". La BASE és
   PARAMETRITZABLE (var dbt) perquè a escala Catalunya serà per comarca (§8).
--------------------------------------------------------------------------- #}

{# poblacio_real(base): estimació de presència amb tall de BASE arbitrari.
   round() perquè és una estimació de persones (enter), no un decimal fals. #}
{% macro poblacio_real(poblacio_col, kg_col, base) -%}
    round({{ poblacio_col }} * {{ kg_col }} / {{ base }})
{%- endmacro %}
