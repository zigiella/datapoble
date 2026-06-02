-- Staging RTC: una fila per establiment d'allotjament (Berguedà).
-- Llegeix la raw (parquet escrit per packages/ingestion via dlt).
-- Deriva ine5 = 5 primers dígits del codi Idescat de 6.
-- NOTA RGPD: descartem aquí les columnes de titular (nom/cognoms/cif); la mart
-- només necessita recomptes, i així no propaguem dades personals aigües avall.

with src as (
    select *
    from read_parquet(
        '{{ var("raw_root") }}/rtc/rtc_establiments/*.parquet',
        union_by_name = true
    )
)

select
    lpad(cast(codi_municipi_idescat as varchar), 6, '0')              as codi6,
    left(lpad(cast(codi_municipi_idescat as varchar), 6, '0'), 5)     as ine5,
    municipi,
    codi_comarca_idescat                                             as comarca_codi,
    tipus_establiment,
    estat,
    -- normalitzem el flag HUT (habitatge d'ús turístic)
    (tipus_establiment = 'Habitatges d''ús turístic')                as is_hut,
    try_cast(total_places as integer)                               as total_places
from src
