-- Staging consum elèctric ICAEN (8idm-becu): 1 fila per municipi × any × sector
-- del Berguedà, sèrie completa 2013–2024. Deriva ine5 i tipa any/consum.
--
-- La raw guarda TOTS els sectors (fidelitat a la font). La selecció del sector
-- USOS DOMÈSTICS (codi_sector='7'), que és el proxy de presència i l'únic que
-- sobreviu al secret estadístic a micromunicipis, es fa a int/mart, no aquí.
-- A la raw, els sectors ocults per secret estadístic vénen amb consum_kwh NULL.

with src as (
    select *
    from read_parquet(
        '{{ var("raw_root") }}/icaen_consum/consum_electric_municipal/*.parquet',
        union_by_name = true
    )
)

select
    lpad(cast(cdmun as varchar), 5, '0')                  as ine5,
    municipi,
    comarca,
    try_cast("any" as integer)                            as any_consum,
    cast(codi_sector as varchar)                          as codi_sector,
    descripcio_sector,
    try_cast(consum_kwh as double)                        as consum_kwh
from src
