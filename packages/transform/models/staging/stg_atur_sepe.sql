-- Staging atur registrat SEPE (D1): 1 fila per municipi de Catalunya × mes.
-- Font: CSV anual del SEPE «Paro registrado por municipios», ja filtrat al
-- connector pel CATÀLEG sencer (947 ine5) — mai per província ni comarca.
--
-- Doctrina del «<5» (C1 §1.1, vinculant): el connector modela l'emmascarament
-- com a interval [1,4]: atur_registrat NULL + atur_registrat_min/max +
-- atur_emmascarat. Aquí només tipem i passem: la fidelitat ja ve de la raw
-- (total_paro_registrado conserva el literal de la font, '<5' inclòs).

with src as (
    select *
    from read_parquet(
        '{{ var("raw_root") }}/atur_sepe/paro_municipis_*.parquet',
        union_by_name = true
    )
)

select
    lpad(cast(ine5 as varchar), 5, '0')            as ine5,
    cast(date as varchar)                          as date,          -- "YYYY-MM" (C1 §1.1)
    cast(codigo_mes as varchar)                    as codigo_mes,    -- AAAAMM de la font
    cast(municipio as varchar)                     as municipi_sepe, -- nom tal com el serveix el SEPE
    cast(provincia as varchar)                     as provincia,
    cast(total_paro_registrado as varchar)         as total_literal, -- fidelitat: '<5' inclòs
    try_cast(atur_registrat as integer)            as atur_registrat,
    try_cast(atur_registrat_min as integer)        as atur_registrat_min,
    try_cast(atur_registrat_max as integer)        as atur_registrat_max,
    cast(atur_emmascarat as boolean)               as atur_emmascarat
from src
