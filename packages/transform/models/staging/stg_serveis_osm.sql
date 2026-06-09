-- Staging comerç i serveis essencials (OSM/Overpass): 1 fila per municipi (Berguedà).
-- Llegeix la raw (parquet escrit per packages/ingestion/serveis_osm.py), que JA ve
-- agregada per municipi: el connector compta els POIs de comerç (shop=supermarket/
-- convenience/bakery/...) i serveis essencials (amenity=bank/pharmacy/post_office/
-- townhall/...) i els assigna al municipi per PUNT-EN-POLÍGON amb la geometria real
-- dels 31 munis (ine5). Aquí només tipem el total + el desglossament principal.
--
-- serveis_estab = nombre d'establiments de comerç i serveis bàsics mapejats a OSM
-- dins el municipi. És el senyal de CENTRALITAT FUNCIONAL: distingeix el «centre de
-- serveis real» (té supermercat/farmàcia/banc que serveixen els pobles veïns) del
-- «municipi gran sense serveis». El senyal és el COMPTE ABSOLUT (no la densitat): un
-- poble és capçalera per TENIR aquests serveis, independentment de la mida. La
-- densitat per 1000 hab es deriva al mart (context secundari).
--
-- FRONTERA HONESTA: OSM INFRA-MAPEJA el rural → el compte és un MÍNIM observat, no un
-- cens (la completesa varia entre municipis). Vegeu el caveat del contracte
-- (semantic/metrics.yml) i docs/tipologia-municipal.md. A escala Catalunya el senyal
-- s'ha de z-scoritzar PER COMARCA (signatures molt diferents entre tipus territorials).
--
-- El desglossament complet (les 20 columnes n_shop_* / n_amenity_*) viu a la raw per a
-- QA; aquí n'exposem una agregació útil: comerç vs serveis, i alguns ancoratges de
-- capçalera (supermercat, farmàcia, banc) per a inspecció.

with src as (
    select *
    from read_parquet(
        '{{ var("raw_root") }}/serveis_osm/serveis_osm.parquet',
        union_by_name = true
    )
)

select
    lpad(cast(ine5 as varchar), 5, '0')         as ine5,
    lpad(cast(codi6 as varchar), 6, '0')        as codi6,
    municipi,
    cast(serveis_estab as integer)              as serveis_estab,
    -- Agregats de traçabilitat (no exposats al mart; útils per a QA i per a la regla):
    -- comerç quotidià vs serveis essencials, i ancoratges de capçalera.
    cast(
        n_shop_supermarket + n_shop_convenience + n_shop_bakery + n_shop_butcher
      + n_shop_greengrocer + n_shop_hardware + n_shop_doityourself + n_shop_chemist
      + n_shop_kiosk + n_shop_general
    as integer)                                  as serveis_comerc,
    cast(
        n_amenity_bank + n_amenity_pharmacy + n_amenity_post_office + n_amenity_townhall
      + n_amenity_fuel + n_amenity_doctors + n_amenity_clinic + n_amenity_hospital
      + n_amenity_veterinary + n_amenity_school
    as integer)                                  as serveis_amenity,
    cast(n_shop_supermarket as integer)          as n_supermarket,
    cast(n_amenity_pharmacy as integer)          as n_pharmacy,
    cast(n_amenity_bank as integer)              as n_bank
from src
