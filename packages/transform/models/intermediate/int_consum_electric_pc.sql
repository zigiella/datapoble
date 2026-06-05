-- Intermediate: consum elèctric DOMÈSTIC per càpita del darrer any amb cobertura
-- plena (var any_corroborador_electric = 2024). Corroborador SECUNDARI de
-- presència per a l'indicador "població real vs padró" (docs/poblacio-real-metode.md §3).
--
-- IMPORTANT (per què NO surt de mart_consum_electric):
--   mart_consum_electric ja DEPÈN de mart_municipi (n'agafa codi6+nom). Si el
--   corroborador de mart_municipi vingués del mart, tindríem una dependència
--   circular. Per això es deriva directament de l'staging (stg_icaen_consum,
--   sector 7) + població d'EMEX. El número és idèntic: kWh domèstic / padró.
--
-- Caveat metodològic (§3): l'elèctric està confós per la calefacció (a la
-- muntanya es crema llenya/gas → consum baix malgrat molta presència, p. ex.
-- Castellar de n'Hug). Per això NO es pondera igual que els residus: només puja
-- la CONFIANÇA quan coincideix amb el senyal primari, mai el substitueix.

with dom as (
    -- sector 7 = USOS DOMÈSTICS (l'únic que sobreviu al secret estadístic als
    -- micromunicipis); descartem NULLs per coherència (al sector 7 no n'hi ha).
    select ine5, consum_kwh
    from {{ ref('stg_icaen_consum') }}
    where codi_sector = '7'
      and any_consum = {{ var('any_corroborador_electric') }}
      and consum_kwh is not null
),

pob as (
    select ine5, poblacio from {{ ref('stg_idescat_emex') }}
)

select
    dom.ine5,
    round(dom.consum_kwh / nullif(pob.poblacio, 0), 1) as kwh_domestic_pc
from dom
join pob on dom.ine5 = pob.ine5
