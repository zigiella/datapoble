-- Staging electoral: una fila per (convocatòria × municipi × candidatura).
-- Llegeix la raw (parquet escrit per packages/ingestion via dlt, nivell Municipi,
-- Berguedà). Deriva:
--   · ine5  -> aplica el crosswalk territori_codi→ine5 (identitat al Berguedà;
--             Gósol=25100 coincideix amb mart_municipi, vegeu el seed). Així el
--             join amb mart_municipi queda explícitament documentat.
--   · sigla_norm -> sigles normalitzades (majúscules, sense accents/espais/punts)
--             per a la classificació en blocs (int_electoral_classificacio).
-- Lectura ECOLÒGICA: agregat per municipi, mai individual.

with src as (
    select *
    from read_parquet(
        '{{ var("raw_root") }}/electoral/electoral_vots/*.parquet',
        union_by_name = true
    )
),

cw as (
    select cast(territori_codi as varchar) as territori_codi, cast(ine5 as varchar) as ine5
    from {{ ref('crosswalk_electoral_ine5') }}
)

select
    src.id_eleccio,
    src.nom_eleccio,
    -- crosswalk: si el codi té entrada al seed l'usa; si no, identitat.
    coalesce(cw.ine5, cast(src.territori_codi as varchar))           as ine5,
    cast(src.territori_codi as varchar)                              as territori_codi,
    src.territori_nom,
    src.candidatura_sigles,
    -- normalització: NFKD→ASCII (strip_accents), majúscules, només alfanumèric.
    regexp_replace(upper(strip_accents(src.candidatura_sigles)), '[^A-Z0-9]', '', 'g') as sigla_norm,
    try_cast(src.vots as integer)                                    as vots
from src
left join cw on cast(src.territori_codi as varchar) = cw.territori_codi
