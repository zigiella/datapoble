-- Staging restauració (OSM/Overpass): 1 fila per municipi (Berguedà).
-- Llegeix la raw (parquet escrit per packages/ingestion/restauracio_osm.py), que JA
-- ve agregada per municipi: el connector compta els POIs amb amenity de restauració
-- (restaurant/cafe/bar/fast_food/pub/biergarten/ice_cream) i els assigna al municipi
-- per PUNT-EN-POLÍGON amb la geometria real dels 31 munis (ine5). Aquí només tipem.
--
-- restauracio_estab = nombre de locals de restauració mapejats a OSM dins el
-- municipi. És el 2n proxy d'hostaleria de la capa L3 (capacitat instal·lada),
-- complement del vidre (activitat). La densitat per 1000 hab es deriva al mart
-- (restauracio_estab / poblacio * 1000), coherent amb rtc_per_1000hab.
--
-- FRONTERA HONESTA: OSM INFRA-MAPEJA el rural → el compte és un MÍNIM observat, no un
-- cens (la completesa del mapejat varia entre municipis). Vegeu el caveat del
-- contracte (semantic/metrics.yml) i docs/poblacio-real-fonts.md §T2.

with src as (
    select *
    from read_parquet(
        '{{ var("raw_root") }}/restauracio_osm/restauracio_osm.parquet',
        union_by_name = true
    )
)

select
    lpad(cast(ine5 as varchar), 5, '0')         as ine5,
    lpad(cast(codi6 as varchar), 6, '0')        as codi6,
    municipi,
    cast(restauracio_estab as integer)          as restauracio_estab,
    -- Desglossament per amenity (traçabilitat; no exposat al mart, útil per a QA).
    cast(n_restaurant as integer)               as n_restaurant,
    cast(n_cafe as integer)                      as n_cafe,
    cast(n_bar as integer)                       as n_bar,
    cast(n_fast_food as integer)                 as n_fast_food,
    cast(n_pub as integer)                       as n_pub,
    cast(n_biergarten as integer)                as n_biergarten,
    cast(n_ice_cream as integer)                 as n_ice_cream
from src
