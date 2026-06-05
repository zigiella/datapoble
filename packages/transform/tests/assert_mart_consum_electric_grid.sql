-- mart_consum_electric ha de ser una graella completa municipi × any:
-- 31 municipis × 12 anys (2013–2024) = 372 files, sense forats ni duplicats.
-- (Escala a Catalunya = n_municipis_expected canvia; els anys segueixen sent 12.)
-- Falla (retorna files) si el recompte no quadra o si hi ha (ine5, any) repetit.

with g as (
    select
        count(*)                              as n_rows,
        count(distinct ine5)                  as n_munis,
        count(distinct any_consum)            as n_anys,
        count(distinct (ine5, any_consum))    as n_parelles
    from {{ ref('mart_consum_electric') }}
)
select *
from g
where n_rows  != {{ var('n_municipis_expected') }} * 12
   or n_munis != {{ var('n_municipis_expected') }}
   or n_anys  != 12
   or n_parelles != n_rows
