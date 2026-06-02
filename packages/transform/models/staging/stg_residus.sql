-- Staging residus: una fila per municipi × any (Berguedà, sèrie completa).
-- Deriva ine5 i tipa l'any i kg_hab_any. La selecció de l'any vigent es fa a
-- intermediate/mart (agafem el darrer any disponible per municipi).

with src as (
    select *
    from read_parquet(
        '{{ var("raw_root") }}/residus/residus_municipals/*.parquet',
        union_by_name = true
    )
)

select
    lpad(cast(codi_municipi as varchar), 6, '0')          as codi6,
    left(lpad(cast(codi_municipi as varchar), 6, '0'), 5) as ine5,
    municipi,
    comarca,
    try_cast("any" as integer)                            as any_residus,
    try_cast(poblaci as integer)                          as poblacio_residus,
    try_cast(kg_hab_any as double)                        as kg_hab_any
from src
