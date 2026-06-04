{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5) TO '"
              ~ var('marts_root') ~ "/mart_municipi.parquet' (FORMAT PARQUET)"
) }}
-- mart_municipi · 1 fila per municipi (clau: ine5).
-- Columnes segons el contracte (semantic/metrics.yml, table: mart_municipi).
-- Espina = Idescat EMEX (31 municipis del Berguedà). RTC i residus s'uneixen
-- per ine5. Lògica de ràtios reproduïda del prototip verificat.
--
-- Honest boundaries (NULL deliberat, documentat al PR):
--   · pct_icaen_EFG      -> requereix connector ICAEN (j6ii-t3w2), fora d'aquest PR. NULL.
--   · index_envelliment  -> status: planned al contracte, però el calculem (dades EMEX disponibles).
--
-- IETR (Índex d'Exposició Turística-Residencial) — metodologia de Talaia:
--   min-max WINSORITZAT (p5/p95) sobre els 31 municipis, dues dimensions a pesos
--   iguals. Eix A (residencial): pct_noprincipal + hab_per_hab. Eix B (turístic):
--   rtc_per_1000hab + rtc_per_100hab_viv. Cada indicador es normalitza 0-100 contra
--   la seva distribució comarcal; IETR = 0.5*A + 0.5*B. Ancoratges verificats del
--   prototip: Castellar (08052) ≈ 89,4 (#1); Berga (08022) ≈ 0,3 (#31). Validació
--   externa: Spearman(IETR, kg_hab_any) = 0,87 (vegeu verify_marts.py).

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
),

-- ind: una fila per municipi amb els ràtios base (inputs de l'IETR).
ind as (
    select
        emex.ine5,
        emex.codi6,
        noms.municipi,
        cast(emex.poblacio as integer)                              as poblacio,
        cast(emex.hab_total as integer)                             as hab_total,
        cast(emex.hab_principal as integer)                         as hab_principal,
        cast(emex.hab_noprincipal as integer)                       as hab_noprincipal,
        round(emex.hab_noprincipal / nullif(emex.hab_total, 0) * 100, 2) as pct_noprincipal,
        round(emex.hab_total / nullif(emex.poblacio, 0), 3)             as hab_per_hab,
        round(emex.pob_65_mes / nullif(emex.pob_0_14, 0) * 100, 1)      as index_envelliment,
        coalesce(rtc.rtc_total, 0)                                  as rtc_total,
        coalesce(rtc.rtc_hut, 0)                                    as rtc_hut,
        round(coalesce(rtc.rtc_total, 0) / nullif(emex.poblacio, 0) * 1000, 2) as rtc_per_1000hab,
        round(coalesce(rtc.rtc_total, 0) / nullif(emex.hab_total, 0) * 100, 2) as rtc_per_100hab_viv,
        residus.kg_hab_any                                          as kg_hab_any,
        residus.residus_any                                         as kg_hab_any_year
    from emex
    left join rtc      on emex.ine5 = rtc.ine5
    left join residus  on emex.ine5 = residus.ine5
    left join noms     on emex.ine5 = noms.ine5
),

-- q: percentils p5/p95 per a la winsorització (sobre els 31 municipis).
q as (
    select quantile_cont(pct_noprincipal,0.05) p5_np, quantile_cont(pct_noprincipal,0.95) p95_np,
           quantile_cont(hab_per_hab,0.05)     p5_hh, quantile_cont(hab_per_hab,0.95)     p95_hh,
           quantile_cont(rtc_per_1000hab,0.05) p5_r1, quantile_cont(rtc_per_1000hab,0.95) p95_r1,
           quantile_cont(rtc_per_100hab_viv,0.05) p5_r2, quantile_cont(rtc_per_100hab_viv,0.95) p95_r2
    from ind
),

-- norm: cada indicador winsoritzat a [p5,p95] i reescalat 0-100.
norm as (
    select ind.ine5,
      case when q.p95_np=q.p5_np then 0 else (least(greatest(ind.pct_noprincipal,q.p5_np),q.p95_np)-q.p5_np)/(q.p95_np-q.p5_np)*100 end as n_np,
      case when q.p95_hh=q.p5_hh then 0 else (least(greatest(ind.hab_per_hab,q.p5_hh),q.p95_hh)-q.p5_hh)/(q.p95_hh-q.p5_hh)*100 end as n_hh,
      case when q.p95_r1=q.p5_r1 then 0 else (least(greatest(ind.rtc_per_1000hab,q.p5_r1),q.p95_r1)-q.p5_r1)/(q.p95_r1-q.p5_r1)*100 end as n_r1,
      case when q.p95_r2=q.p5_r2 then 0 else (least(greatest(ind.rtc_per_100hab_viv,q.p5_r2),q.p95_r2)-q.p5_r2)/(q.p95_r2-q.p5_r2)*100 end as n_r2
    from ind cross join q
),

-- ietr: eix A (residencial) i B (turístic) a pesos iguals; IETR = 0.5*A + 0.5*B.
ietr as (
    select ine5, (n_np+n_hh)/2.0 as A_resid, (n_r1+n_r2)/2.0 as B_turis,
           0.5*((n_np+n_hh)/2.0)+0.5*((n_r1+n_r2)/2.0) as IETR
    from norm
)

select
    ind.ine5,
    ind.codi6,
    ind.municipi,
    '{{ var("comarca") }}'                                       as comarca,

    -- Demografia / vivenda (directe EMEX)
    ind.poblacio,
    ind.hab_total,
    ind.hab_principal,
    ind.hab_noprincipal,

    -- Derivats vivenda
    ind.pct_noprincipal,
    ind.hab_per_hab,

    -- Índex d'envelliment (65+ per 100 de 0-14)
    ind.index_envelliment,

    -- Turisme (RTC). Sense establiments -> 0, no NULL (absència real).
    ind.rtc_total,
    ind.rtc_hut,
    ind.rtc_per_1000hab,
    ind.rtc_per_100hab_viv,

    -- Pressió (residus, darrer any)
    ind.kg_hab_any,

    -- Energia (ICAEN) — connector pendent
    cast(null as double)                                        as pct_icaen_EFG,

    -- Índex IETR (metodologia Talaia, min-max winsoritzat p5/p95)
    round(ietr.IETR, 2)                                         as IETR,
    rank() over (order by ietr.IETR desc)                       as IETR_rank,

    -- Traçabilitat del tall temporal
    ind.kg_hab_any_year

from ind
join ietr on ind.ine5 = ietr.ine5
order by ind.ine5
