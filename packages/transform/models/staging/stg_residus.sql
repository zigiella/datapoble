{{ config(materialized='table') }}
-- Staging residus: una fila per municipi × any (Berguedà, sèrie completa).
-- Deriva ine5 i tipa l'any, kg_hab_any i la fracció VIDRE. La selecció de l'any
-- vigent es fa a intermediate/mart (agafem el darrer any disponible per municipi).
--
-- VIDRE (fracció de recollida selectiva, MATEIX dataset ARC 69zu-w48s): ve en
-- TONES/any (p. ex. Berga 2024 ≈ 475 t, Gósol ≈ 32 t). El per càpita es deriva a
-- int_residus_fraccions (vidre*1000/poblaci → kg/hab/any). És el proxy
-- d'hostaleria/turisme de la capa L3 (ampolles de bar/restaurant), el senyal
-- físic més net per separar pressió de visitants de residència estable.
--
-- materialized='table' (excepció a la regla staging=view): mart_municipi
-- referencia stg_residus per TRES camins en una sola sentència (noms, residus,
-- vidre). Amb una vista sobre read_parquet(union_by_name=true), DuckDB podia
-- expandir `*` amb un ordre de columnes inconsistent entre referències → ine5/codi6
-- es vinculaven als valors crus de codi_municipi i el join del vidre fallava.
-- Materialitzar la taixa (775 files) fixa columnes i tipus i ho resol d'arrel.

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
    try_cast(kg_hab_any as double)                        as kg_hab_any,
    try_cast(vidre as double)                             as vidre_tones
from src
