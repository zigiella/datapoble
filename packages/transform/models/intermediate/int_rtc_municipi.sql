-- Intermediate: agrega RTC a 1 fila per municipi.
-- rtc_total = establiments d'alta (estat='Alta'); rtc_hut = subconjunt HUT.
-- Verificat: Castellar (08052)=30 total / 20 HUT; Berga (08022)=45 / 36 HUT.

with rtc as (
    select * from {{ ref('stg_rtc') }}
    where estat = 'Alta'
)

select
    ine5,
    any_value(codi6)                                  as codi6,
    any_value(municipi)                               as municipi_rtc,
    count(*)                                           as rtc_total,
    count(*) filter (where is_hut)                     as rtc_hut
from rtc
group by ine5
