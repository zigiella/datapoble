{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5) TO '"
              ~ var('marts_root') ~ "/mart_municipi_bergueda.parquet' (FORMAT PARQUET)"
) }}
-- mart_municipi · 1 fila per municipi (clau: ine5).
-- Columnes segons el contracte (semantic/metrics.yml, table: mart_municipi).
-- Espina = Idescat EMEX (31 municipis del Berguedà). RTC i residus s'uneixen
-- per ine5. Lògica de ràtios reproduïda del prototip verificat.
--
-- Honest boundaries (NULL deliberat, documentat al PR):
--   · IETR, IETR_rank   -> els defineix Talaia (model a part). NULL aquí.
--   · pct_icaen_EFG      -> requereix connector ICAEN (j6ii-t3w2), fora d'aquest PR. NULL.
--   · index_envelliment  -> status: planned al contracte, però el calculem (dades EMEX disponibles).

with emex as (
    select * from {{ ref('stg_idescat_emex') }}
),

rtc as (
    select * from {{ ref('int_rtc_municipi') }}
),

residus as (
    select * from {{ ref('int_residus_latest') }}
),

noms as (
    -- nom oficial: residus té els 31 amb nom net
    select distinct ine5, municipi from {{ ref('stg_residus') }}
)

select
    emex.ine5,
    emex.codi6,
    noms.municipi,
    '{{ var("comarca") }}'                                       as comarca,

    -- Demografia / vivenda (directe EMEX)
    cast(emex.poblacio as integer)                              as poblacio,
    cast(emex.hab_total as integer)                             as hab_total,
    cast(emex.hab_principal as integer)                         as hab_principal,
    cast(emex.hab_noprincipal as integer)                       as hab_noprincipal,

    -- Derivats vivenda
    round(emex.hab_noprincipal / nullif(emex.hab_total, 0) * 100, 2) as pct_noprincipal,
    round(emex.hab_total / nullif(emex.poblacio, 0), 3)             as hab_per_hab,

    -- Índex d'envelliment (65+ per 100 de 0-14)
    round(emex.pob_65_mes / nullif(emex.pob_0_14, 0) * 100, 1)      as index_envelliment,

    -- Turisme (RTC). Sense establiments -> 0, no NULL (absència real).
    coalesce(rtc.rtc_total, 0)                                  as rtc_total,
    coalesce(rtc.rtc_hut, 0)                                    as rtc_hut,
    round(coalesce(rtc.rtc_total, 0) / nullif(emex.poblacio, 0) * 1000, 2) as rtc_per_1000hab,
    round(coalesce(rtc.rtc_total, 0) / nullif(emex.hab_total, 0) * 100, 2) as rtc_per_100hab_viv,

    -- Pressió (residus, darrer any)
    residus.kg_hab_any                                          as kg_hab_any,

    -- Energia (ICAEN) — connector pendent
    cast(null as double)                                        as pct_icaen_EFG,

    -- Índex IETR — el defineix Talaia
    cast(null as double)                                        as IETR,
    cast(null as integer)                                       as IETR_rank,

    -- Traçabilitat del tall temporal
    residus.residus_any                                         as kg_hab_any_year

from emex
left join rtc      on emex.ine5 = rtc.ine5
left join residus  on emex.ine5 = residus.ine5
left join noms     on emex.ine5 = noms.ine5
order by emex.ine5
