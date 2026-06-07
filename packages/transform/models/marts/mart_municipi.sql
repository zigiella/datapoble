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
-- Població real estimada vs padró (INDICADOR ESTRELLA) — mètode de Talaia,
--   docs/poblacio-real-metode.md. Columnes poblacio_real_est / gap_abs / gap_pct /
--   poblacio_real_rel / confianca. presència = padró × kg_hab_any / BASE, amb BASE
--   PARAMETRITZABLE (vars base_residencial=410 absolut, base_comarcal=452 relatiu).
--   És INFERÈNCIA (no cens): es comunica com a rang + caveat (vegeu el contracte).
--   confianca marca 'baixa' sense por als micro-munis i on els senyals divergeixen.
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

-- Corroborador secundari de presència (docs/poblacio-real-metode.md §3): consum
-- elèctric domèstic per càpita del darrer any amb cobertura plena. Ve de l'staging
-- (no del mart elèctric) per evitar dependència circular — vegeu int_consum_electric_pc.
elec_pc as (
    select * from {{ ref('int_consum_electric_pc') }}
),

-- Senyal físic de la capa L3 (pressió turística/hostaleria): vidre kg/hab/any
-- del darrer any. Fracció del MATEIX dataset ARC que els residus.
vidre as (
    select * from {{ ref('int_residus_fraccions') }}
),

-- 2n proxy d'hostaleria de la capa L3 (complement del vidre): nombre d'establiments
-- de restauració per municipi (OSM via Overpass, assignats per punt-en-polígon a la
-- geometria real). El vidre mesura ACTIVITAT (ampolles); la restauració, CAPACITAT
-- instal·lada (stock). OSM infra-mapeja el rural → compte = MÍNIM observat, no cens.
restauracio as (
    select * from {{ ref('stg_restauracio_osm') }}
),

noms as (
    -- nom oficial: residus té els 31 amb nom net
    select distinct ine5, municipi from {{ ref('stg_residus') }}
),

-- ind: una fila per municipi amb els ràtios base (inputs de l'IETR i de les 3
-- capes). El senyal de vidre ve d'int_residus_fraccions, materialitzat com a TAULA
-- (no vista) perquè la vista sobre read_parquet+union_by_name resolia vidre_tones
-- com a NULL quan stg_residus es referenciava per múltiples camins en aquesta sentència.
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
        residus.residus_any                                         as kg_hab_any_year,
        -- Senyal L1 (pernocta): consum elèctric domèstic per càpita. kwh_hab és el
        -- nom de contracte; ve d'int_consum_electric_pc (kwh_domestic_pc).
        elec_pc.kwh_domestic_pc                                     as kwh_hab,
        -- Senyal L3 (turisme): vidre kg/hab/any. NULL→0 no s'aplica (cobertura 31/31).
        vidre.vidre_hab                                             as vidre_hab,
        vidre.vidre_any                                             as vidre_any,
        -- 2n proxy L3 (restauració OSM): compte d'establiments. Absència real → 0,
        -- no NULL (coherent amb rtc_total; un municipi sense locals mapejats és 0).
        coalesce(restauracio.restauracio_estab, 0)                  as restauracio_estab
    from emex
    left join rtc         on emex.ine5 = rtc.ine5
    left join residus     on emex.ine5 = residus.ine5
    left join elec_pc     on emex.ine5 = elec_pc.ine5
    left join vidre       on emex.ine5 = vidre.ine5
    left join restauracio on emex.ine5 = restauracio.ine5
    left join noms        on emex.ine5 = noms.ine5
),

-- med: medianes comarcals dels senyals de presència (per a la bandera de
-- confiança, §6). Es calculen sobre els 31 municipis del pilot.
med as (
    select
        median(kg_hab_any)      as kg_hab_any_med,
        median(pct_noprincipal) as pct_noprincipal_med,
        median(kwh_hab)         as kwh_hab_med
    from ind
),

-- vstats: estadístics comarcals del vidre/hab per al z-score de la capa L3
-- (índex de pressió turística). Mitjana i desviació sobre els 31 municipis.
vstats as (
    select
        avg(vidre_hab)        as vidre_hab_avg,
        stddev_pop(vidre_hab) as vidre_hab_sd
    from ind
),

-- tur: capa L3 «pressió turística» (índex per ine5). z-score comarcal del
-- vidre/hab portat a 0–100 (z clampat a [-2,2]; 50 = mitjana comarcal). Es calcula
-- en una CTE pròpia (keyed per ine5, com ietr) i s'uneix per join — no per
-- cross join a la SELECT final — per robustesa de l'optimitzador.
tur as (
    select ind.ine5,
        round(
            (least(greatest((ind.vidre_hab - vstats.vidre_hab_avg)
                            / nullif(vstats.vidre_hab_sd, 0), -2), 2) + 2) / 4.0 * 100,
            1) as index_turisme
    from ind cross join vstats
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

    -- Senyals físics per càpita (inputs de les 3 capes; exposats per traçabilitat)
    ind.kwh_hab,                                                 -- elèctric domèstic kWh/hab (L1)
    ind.vidre_hab,                                               -- vidre kg/hab/any (L3)

    -- 2n proxy d'hostaleria de la capa L3 (CAPACITAT instal·lada, complement del
    -- vidre que mesura ACTIVITAT). Compte d'establiments de restauració (OSM) i la
    -- seva densitat per 1000 hab (numerador OSM / padró Idescat, com rtc_per_1000hab).
    -- És una MESURA (no inferència); OSM infra-mapeja el rural → MÍNIM, no cens.
    ind.restauracio_estab,                                       -- establiments (OSM, mínim)
    round(ind.restauracio_estab / nullif(ind.poblacio, 0) * 1000, 2)
                                                                as restauracio_per_1000hab,

    -- ===================================================================
    -- INDICADOR ESTRELLA — MODEL DE 3 CAPES (INFERÈNCIA, no cens). Mètode de
    -- Talaia, validat sobre dades. 3 senyals físics INDEPENDENTS, cadascun amb la
    -- seva base residencial (viles IETR<5, pop-pond). Tot es comunica com a RANG +
    -- caveat (semantic/metrics.yml). Lectura ECOLÒGICA (sobre el municipi).
    -- ===================================================================

    -- L1 · POBLACIÓ PERNOCTA («població invisible»): qui DORM al territori sense
    -- constar al padró. Senyal = elèctric domèstic / base_electric (1224 kWh/hab).
    -- És la nova SIGNATURA de població real (substitueix l'antic residus→població).
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kwh_hab', var('base_electric')) }} as integer)
                                                                as poblacio_pernocta_est,
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kwh_hab', var('base_electric')) }} - ind.poblacio as integer)
                                                                as gap_pernocta,
    round(
        ({{ estimacio_presencia('ind.poblacio', 'ind.kwh_hab', var('base_electric')) }} - ind.poblacio)
        / nullif(ind.poblacio, 0), 3)                           as gap_pernocta_pct,

    -- L2 · CÀRREGA HUMANA TOTAL: pressió total inclosos els visitants de DIA
    -- (excursionistes). Senyal = residus / base_residencial (410). NO és població:
    -- els residus de les viles porten part de comerç. Era l'antic poblacio_real_est.
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }} as integer)
                                                                as carrega_total_est,

    -- L3 · PRESSIÓ TURÍSTICA (hostaleria): intensitat d'activitat de visitants, via
    -- vidre/hab (ampolles de bar/restaurant). z-score comarcal del vidre_hab portat
    -- a 0–100 (50 = mitjana comarcal). NO és població. Calculat a la CTE `tur`.
    tur.index_turisme,

    -- Bandera de CONFIANÇA: honestedat abans que precisió falsa.
    --   baixa  = micro-muni (padró < poblacio_min_confianca, secret/soroll) O
    --            els senyals DIVERGEIXEN (residus alt però els altres baixos, o a
    --            l'inrevés) → l'estimació no és fiable.
    --   alta   = residus > mediana comarcal I almenys un altre senyal (elèctric/
    --            càpita O % no principal) també > mediana, I padró prou gran.
    --   mitjana= la resta.
    case
        when ind.poblacio < {{ var('poblacio_min_confianca') }} then 'baixa'
        when (ind.kg_hab_any > med.kg_hab_any_med
              and not (ind.pct_noprincipal > med.pct_noprincipal_med)
              and not (ind.kwh_hab > med.kwh_hab_med))
          or (not (ind.kg_hab_any > med.kg_hab_any_med)
              and ind.pct_noprincipal > med.pct_noprincipal_med
              and ind.kwh_hab > med.kwh_hab_med)
            then 'baixa'
        when ind.kg_hab_any > med.kg_hab_any_med
             and (ind.pct_noprincipal > med.pct_noprincipal_med
                  or ind.kwh_hab > med.kwh_hab_med)
             and ind.poblacio >= {{ var('poblacio_min_confianca') }}
            then 'alta'
        else 'mitjana'
    end                                                         as confianca,

    -- --- COMPATIBILITAT (model anterior d'una capa) ---------------------------
    -- Es CONSERVEN perquè cap consumidor del contracte quedi trencat. poblacio_real_est
    -- és ARA un ÀLIES de carrega_total_est (mateixa fórmula residus/410); reenquadrat:
    -- NO és «població» sinó càrrega total (vegeu L2). gap_abs/gap_pct deriven d'ell.
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }} as integer)
                                                                as poblacio_real_est,
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }} - ind.poblacio as integer)
                                                                as gap_abs,
    round(
        ({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }} - ind.poblacio)
        / nullif(ind.poblacio, 0), 3)                           as gap_pct,
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_comarcal')) }} as integer)
                                                                as poblacio_real_rel,

    -- Energia (ICAEN certificats) — connector pendent
    cast(null as double)                                        as pct_icaen_EFG,

    -- Índex IETR (metodologia Talaia, min-max winsoritzat p5/p95)
    round(ietr.IETR, 2)                                         as IETR,
    rank() over (order by ietr.IETR desc)                       as IETR_rank,

    -- Traçabilitat dels talls temporals
    ind.kg_hab_any_year,
    ind.vidre_any

from ind
join ietr on ind.ine5 = ietr.ine5
join tur  on ind.ine5 = tur.ine5
cross join med
order by ind.ine5
