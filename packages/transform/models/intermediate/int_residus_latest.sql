-- Intermediate: kg_hab_any del darrer any disponible per municipi.
-- (La sèrie completa viu a staging; aquí ens quedem amb el tall vigent = 2024.)

with ranked as (
    select
        *,
        row_number() over (partition by ine5 order by any_residus desc) as rn
    from {{ ref('stg_residus') }}
    where kg_hab_any is not null
)

select
    ine5,
    codi6,
    any_residus    as residus_any,
    kg_hab_any
from ranked
where rn = 1
