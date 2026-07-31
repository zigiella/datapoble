-- Intermediate: kg_hab_any del darrer any disponible per municipi.
-- (La sèrie completa viu a staging; aquí ens quedem amb el tall vigent = 2024.)
--
-- S'emet TAMBÉ el denominador (`poblacio_residus`): és la població que l'ARC fa servir
-- per calcular kg_hab_any i vidre_hab, i sense ella la referència PONDERADA d'aquestes
-- dues mètriques (total ÷ habitants, R-REFERENCIA) no es pot ni calcular ni auditar
-- (C6 §8.1). Verificat 2026-07-31: coincideix municipi a municipi (947/947, diferència
-- màxima 0) amb el padró d'Idescat del mateix any 2024, i suma 8.012.231.

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
    any_residus       as residus_any,
    poblacio_residus,
    kg_hab_any
from ranked
where rn = 1
