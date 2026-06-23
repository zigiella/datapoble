{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5) TO '"
              ~ var('marts_root') ~ "/mart_municipi.parquet' (FORMAT PARQUET)"
) }}
-- mart_municipi · 1 fila per municipi (clau: ine5). Escala CATALUNYA (F2: unificació del model).
--
-- UNIFICACIÓ (docs/pla-catalunya-profund.md §F2):
--   · Base de presència L1 = base_pred PER MUNI (Nivell C, covariables densitat/renda/gas), via
--     stg_nivellc — substitueix la base fixa 1224. Provada que MILLORA el Berguedà (#161).
--   · z-scores de CONFIANÇA per tipus_territorial (iguals amb iguals), no per comarca.
--   · comarca per muni (de stg_residus), no literal.
--
-- ESPINA (tot Catalunya, ~927 munis amb senyal+covariables): presència/gap, residus, vidre, kwh,
--   IETR, index_turisme, %no principal, confiança/divergència. Honest: rang al web.
--
-- 2A ONADA (Berguedà-pilot fins validar per tipus): tipologia + restauració/serveis (OSM). L'OSM
--   només cobreix el Berguedà → fora d'allà tipologia='pendent' i restauracio/serveis = NULL (no 0:
--   "sense dada" ≠ "zero"). Preserva la tipologia PROVADA del Berguedà (referència = els coberts).
--
-- Munis sense base_pred (sense covariables, ~20): presència NULL (honest, no inventem).

with emex as (
    select * from {{ ref('stg_idescat_emex') }}
),

rtc as (
    select * from {{ ref('int_rtc_municipi') }}
),

residus as (
    select * from {{ ref('int_residus_latest') }}
),

-- Corroborador de presència L1: consum elèctric domèstic per càpita (int_consum_electric_pc).
elec_pc as (
    select * from {{ ref('int_consum_electric_pc') }}
),

-- Senyal L3 (turisme): vidre kg/hab/any (fracció ARC).
vidre as (
    select * from {{ ref('int_residus_fraccions') }}
),

-- OSM (2a onada): restauració i serveis. NOMÉS cobreix el Berguedà → LEFT JOIN deixa NULL la resta.
restauracio as (
    select * from {{ ref('stg_restauracio_osm') }}
),

serveis as (
    select * from {{ ref('stg_serveis_osm') }}
),

-- nom + comarca oficials per muni (de l'staging de residus, que cobreix tot CAT). 1 fila/muni:
-- agrupem per ine5 (el nom de comarca pot tenir variants entre anys → any_value evita el fan-out).
noms as (
    select ine5, any_value(municipi) as municipi, any_value(comarca) as comarca
    from {{ ref('stg_residus') }}
    group by ine5
),

-- PONT Nivell C → dbt: base de presència unificada (base_pred) + grup de referència (tipus_territorial).
nivellc as (
    select ine5, tipus_territorial, base_pred from {{ ref('stg_nivellc') }}
),

-- ind: una fila per municipi amb els ràtios base + la base unificada + el tipus.
ind as (
    select
        emex.ine5,
        emex.codi6,
        noms.municipi,
        noms.comarca,
        nivellc.tipus_territorial,
        nivellc.base_pred,
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
        elec_pc.kwh_domestic_pc                                     as kwh_hab,
        vidre.vidre_hab                                             as vidre_hab,
        vidre.vidre_any                                             as vidre_any,
        -- OSM: NULL fora del Berguedà ("sense dada"), valor real (0 inclòs) dins (la staging té els 31).
        restauracio.restauracio_estab                              as restauracio_estab,
        serveis.serveis_estab                                      as serveis_estab
    from emex
    left join rtc         on emex.ine5 = rtc.ine5
    left join residus     on emex.ine5 = residus.ine5
    left join elec_pc     on emex.ine5 = elec_pc.ine5
    left join vidre       on emex.ine5 = vidre.ine5
    left join restauracio on emex.ine5 = restauracio.ine5
    left join serveis     on emex.ine5 = serveis.ine5
    left join noms        on emex.ine5 = noms.ine5
    left join nivellc     on emex.ine5 = nivellc.ine5
),

-- pres: derivats de presència per muni. Es calculen AQUÍ (no a la SELECT final) perquè els stats
-- (sstats, etc.) hi puguin accedir — i això arregla el build break del model previ. base_pred (L1)
-- per muni; base_residencial (L2 residus) i base_vidre (L3) encara fixes (afinables per tipus, futur).
pres as (
    select
        ind.ine5,
        cast(round(ind.poblacio * ind.kwh_hab / nullif(ind.base_pred, 0)) as integer) as poblacio_pernocta_est,
        cast(round(ind.poblacio * ind.kwh_hab / nullif(ind.base_pred, 0)) - ind.poblacio as integer) as gap_pernocta,
        round((round(ind.poblacio * ind.kwh_hab / nullif(ind.base_pred, 0)) - ind.poblacio)
              / nullif(ind.poblacio, 0) * 100, 1)                  as gap_pernocta_pct,
        cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }} as integer) as carrega_total_est,
        cast(greatest(
            ind.poblacio,
            coalesce(round(ind.poblacio * ind.kwh_hab / nullif(ind.base_pred, 0)), 0),
            coalesce({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }}, 0)
        ) as integer)                                              as carrega_funcional_est,
        round(ind.restauracio_estab / nullif(ind.poblacio, 0) * 1000, 2) as restauracio_per_1000hab,
        round(ind.serveis_estab / nullif(ind.poblacio, 0) * 1000, 2)     as serveis_per_1000hab,
        round(ind.kg_hab_any / {{ var('base_residencial') }}, 2)    as residu_base_ratio,
        round(ind.kwh_hab    / nullif(ind.base_pred, 0), 2)         as kwh_base_ratio,
        round(ind.vidre_hab  / {{ var('base_vidre') }}, 2)          as vidre_base_ratio
    from ind
),

-- vstats + tur: index_turisme GLOBAL (z-score del vidre/hab sobre tot CAT, indicador absolut 0-100).
vstats as (
    select avg(vidre_hab) as vidre_hab_avg, stddev_pop(vidre_hab) as vidre_hab_sd from ind
),

tur as (
    select ind.ine5,
        round((least(greatest((ind.vidre_hab - vstats.vidre_hab_avg)
                              / nullif(vstats.vidre_hab_sd, 0), -2), 2) + 2) / 4.0 * 100, 1) as index_turisme
    from ind cross join vstats
),

-- IETR GLOBAL (min-max winsoritzat p5/p95 sobre tot CAT): exposició turística-residencial comparable
-- entre comarques. Usa RTC (tot CAT) + EMEX (tot CAT) — no depèn d'OSM.
q as (
    select quantile_cont(pct_noprincipal,0.05) p5_np, quantile_cont(pct_noprincipal,0.95) p95_np,
           quantile_cont(hab_per_hab,0.05)     p5_hh, quantile_cont(hab_per_hab,0.95)     p95_hh,
           quantile_cont(rtc_per_1000hab,0.05) p5_r1, quantile_cont(rtc_per_1000hab,0.95) p95_r1,
           quantile_cont(rtc_per_100hab_viv,0.05) p5_r2, quantile_cont(rtc_per_100hab_viv,0.95) p95_r2
    from ind
),

norm as (
    select ind.ine5,
      case when q.p95_np=q.p5_np then 0 else (least(greatest(ind.pct_noprincipal,q.p5_np),q.p95_np)-q.p5_np)/(q.p95_np-q.p5_np)*100 end as n_np,
      case when q.p95_hh=q.p5_hh then 0 else (least(greatest(ind.hab_per_hab,q.p5_hh),q.p95_hh)-q.p5_hh)/(q.p95_hh-q.p5_hh)*100 end as n_hh,
      case when q.p95_r1=q.p5_r1 then 0 else (least(greatest(ind.rtc_per_1000hab,q.p5_r1),q.p95_r1)-q.p5_r1)/(q.p95_r1-q.p5_r1)*100 end as n_r1,
      case when q.p95_r2=q.p5_r2 then 0 else (least(greatest(ind.rtc_per_100hab_viv,q.p5_r2),q.p95_r2)-q.p5_r2)/(q.p95_r2-q.p5_r2)*100 end as n_r2
    from ind cross join q
),

ietr as (
    select ine5, (n_np+n_hh)/2.0 as A_resid, (n_r1+n_r2)/2.0 as B_turis,
           0.5*((n_np+n_hh)/2.0)+0.5*((n_r1+n_r2)/2.0) as IETR
    from norm
),

-- ========================================================================
-- CONFIANÇA — z-scores PER TIPUS_TERRITORIAL (iguals amb iguals). Senyals de presència (kg, kwh,
-- %no-principal) disponibles a tot CAT → confiança/divergència per a TOTS els munis (espina).
-- ========================================================================
med as (
    select tipus_territorial,
        median(kg_hab_any)      as kg_hab_any_med,
        median(pct_noprincipal) as pct_noprincipal_med,
        median(kwh_hab)         as kwh_hab_med
    from ind
    where tipus_territorial is not null
    group by tipus_territorial
),

sstats as (
    select tipus_territorial,
        avg(kg_hab_any)      as kg_avg,  stddev_pop(kg_hab_any)      as kg_sd,
        avg(kwh_hab)         as kwh_avg, stddev_pop(kwh_hab)         as kwh_sd,
        avg(pct_noprincipal) as np_avg,  stddev_pop(pct_noprincipal) as np_sd
    from ind
    where tipus_territorial is not null
    group by tipus_territorial
),

zconf as (
    select i.ine5,
        (i.kg_hab_any      - s.kg_avg)  / nullif(s.kg_sd,0)  as z_kg,
        (i.kwh_hab         - s.kwh_avg) / nullif(s.kwh_sd,0) as z_kwh,
        (i.pct_noprincipal - s.np_avg)  / nullif(s.np_sd,0)  as z_np
    from ind i
    join sstats s using (tipus_territorial)
),

conf as (
    select z.ine5,
        least(100.0, greatest(0.0,
            40.0 * least(1.0, greatest(0.0,
                (ln(nullif(i.poblacio,0)) - ln({{ var('poblacio_min_confianca') }}))
                / (ln({{ var('base_residencial') }}) - ln({{ var('poblacio_min_confianca') }}))))
            + 35.0 * greatest(0.0, 1.0 -
                (greatest(z.z_kg, z.z_kwh, z.z_np) - least(z.z_kg, z.z_kwh, z.z_np)) / 3.0)
            + 15.0 * (
                (case when i.kg_hab_any is not null then 1 else 0 end
               + case when i.kwh_hab    is not null then 1 else 0 end
               + case when i.vidre_hab  is not null then 1 else 0 end
               + case when i.pct_noprincipal is not null then 1 else 0 end
               + case when i.poblacio   is not null then 1 else 0 end) / 5.0)
            - 10.0 * least(1.0, greatest(0.0,
                (greatest(abs(z.z_kg), abs(z.z_kwh), abs(z.z_np)) - 2.0) / 1.0))
        )) as confianca_score,
        round(100.0 * least(1.0, greatest(0.0,
            (greatest(z.z_kg, z.z_kwh, z.z_np) - least(z.z_kg, z.z_kwh, z.z_np)) / 3.0)), 0) as divergencia_senyals
    from zconf z
    join ind i using (ine5)
),

-- ========================================================================
-- TIPOLOGIA — 2a onada. NOMÉS munis amb OSM (Berguedà). Referència = els munis coberts (preserva la
-- classificació PROVADA: Berga=capital_serveis, Castellar=excursio, Gósol=segona_residencia). Fora
-- d'allà → 'pendent' (honest: sense OSM no es pot classificar). z-scores sobre el conjunt cobert.
-- ========================================================================
bstats as (
    select
        avg(p.gap_pernocta_pct)        as gap_avg,  stddev_pop(p.gap_pernocta_pct)        as gap_sd,
        avg(t.index_turisme)           as tur_avg,  stddev_pop(t.index_turisme)           as tur_sd,
        avg(i.pct_noprincipal)         as np_avg,   stddev_pop(i.pct_noprincipal)         as np_sd,
        avg(i.kg_hab_any)              as kg_avg,   stddev_pop(i.kg_hab_any)              as kg_sd,
        avg(i.vidre_hab)               as vid_avg,  stddev_pop(i.vidre_hab)               as vid_sd,
        avg(p.restauracio_per_1000hab) as rest_avg, stddev_pop(p.restauracio_per_1000hab) as rest_sd,
        avg(ln(i.serveis_estab + 1))   as lserv_avg, stddev_pop(ln(i.serveis_estab + 1))  as lserv_sd,
        avg(ln(i.poblacio))            as lpop_avg, stddev_pop(ln(i.poblacio))            as lpop_sd,
        avg(ln(p.carrega_total_est))   as lcar_avg, stddev_pop(ln(p.carrega_total_est))   as lcar_sd
    from ind i
    join pres p using (ine5)
    join tur t using (ine5)
    where i.serveis_estab is not null          -- = munis amb OSM (Berguedà)
),

btipo as (
    select i.ine5,
        (p.gap_pernocta_pct - b.gap_avg) / nullif(b.gap_sd,0)        as z_gap,
        (t.index_turisme    - b.tur_avg) / nullif(b.tur_sd,0)        as z_tur,
        (i.pct_noprincipal  - b.np_avg)  / nullif(b.np_sd,0)         as z_np,
        ((i.kg_hab_any - b.kg_avg)/nullif(b.kg_sd,0)
         + (i.vidre_hab - b.vid_avg)/nullif(b.vid_sd,0)
         + (p.restauracio_per_1000hab - b.rest_avg)/nullif(b.rest_sd,0)) / 3.0 as z_act,
        (ln(i.serveis_estab + 1) - b.lserv_avg) / nullif(b.lserv_sd,0) as z_serv,
        (ln(i.poblacio)          - b.lpop_avg)  / nullif(b.lpop_sd,0) as z_pop,
        (ln(p.carrega_total_est) - b.lcar_avg)  / nullif(b.lcar_sd,0) as z_carr,
        i.poblacio
    from ind i
    join pres p using (ine5)
    join tur t using (ine5)
    cross join bstats b
    where i.serveis_estab is not null
),

tipo as (
    select ine5,
        case
            when poblacio >= 2000 and z_serv >= 0.8 and z_carr >= 0.5 and z_tur <= 0.3
                then 'capital_serveis'
            when z_pop <= -0.5 and z_tur <= -0.3 and z_act <= -0.2 and z_gap <= 0.2 then 'buit_administratiu'
            when z_tur >= 0.6 and z_act >= 0.4 and z_gap <= 0.4 then 'excursio'
            when z_gap >= 0.5 and (z_np >= 0.5 or z_tur >= 0.7) then 'segona_residencia'
            when z_gap >= 0.4 and z_tur <= 0.0 then 'dormitori_invisible'
            else 'indeterminat'
        end as tipologia
    from btipo
)

select
    ind.ine5,
    ind.codi6,
    ind.municipi,
    ind.comarca,
    ind.tipus_territorial,

    -- Demografia / vivenda (directe EMEX)
    ind.poblacio,
    ind.hab_total,
    ind.hab_principal,
    ind.hab_noprincipal,
    ind.pct_noprincipal,
    ind.hab_per_hab,
    ind.index_envelliment,

    -- Turisme (RTC)
    ind.rtc_total,
    ind.rtc_hut,
    ind.rtc_per_1000hab,
    ind.rtc_per_100hab_viv,

    -- Pressió (residus)
    ind.kg_hab_any,

    -- Senyals físics per càpita
    ind.kwh_hab,
    ind.vidre_hab,

    -- OSM (2a onada): NULL fora del Berguedà
    ind.restauracio_estab,
    pres.restauracio_per_1000hab,
    ind.serveis_estab,
    pres.serveis_per_1000hab,

    -- L1 · PRESÈNCIA PERNOCTA (base unificada base_pred). NULL si no hi ha base_pred (honest).
    pres.poblacio_pernocta_est,
    pres.gap_pernocta,
    pres.gap_pernocta_pct,

    -- L2 · CÀRREGA PER RESIDUS (base_residencial fixa)
    pres.carrega_total_est,
    pres.carrega_funcional_est,

    -- BASE-RATIOS
    pres.residu_base_ratio,
    pres.kwh_base_ratio,
    pres.vidre_base_ratio,

    -- L3 · PRESSIÓ TURÍSTICA (index global)
    tur.index_turisme,

    -- Bandera de CONFIANÇA (mediana del SEU tipus territorial)
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

    -- COMPATIBILITAT (model d'una capa): àlies de carrega (residus/base_residencial)
    pres.carrega_total_est                                      as poblacio_real_est,
    cast(pres.carrega_total_est - ind.poblacio as integer)      as gap_abs,
    round((pres.carrega_total_est - ind.poblacio) / nullif(ind.poblacio, 0) * 100, 1) as gap_pct,
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_comarcal')) }} as integer) as poblacio_real_rel,

    -- Energia (ICAEN certificats) — connector pendent
    cast(null as double)                                        as pct_icaen_EFG,

    -- IETR (global)
    round(ietr.IETR, 2)                                         as IETR,
    row_number() over (order by ietr.IETR desc, ind.ine5)       as IETR_rank,
    round(ietr.A_resid, 2)                                      as IETR_stock,
    round(ietr.B_turis, 2)                                      as IETR_impact,

    -- TIPOLOGIA (2a onada): classificació provada al Berguedà; 'pendent' fora (sense OSM).
    coalesce(tipo.tipologia, 'pendent')                         as tipologia,

    -- CONFIANÇA auditable (per tipus) + divergència
    round(conf.confianca_score, 1)                              as confianca_score,
    conf.divergencia_senyals                                    as divergencia_senyals,

    -- base de presència emprada (traçabilitat de la unificació)
    round(ind.base_pred, 0)                                     as base_pred,

    -- Traçabilitat temporal
    ind.kg_hab_any_year,
    ind.vidre_any

from ind
left join pres on ind.ine5 = pres.ine5
left join tur  on ind.ine5 = tur.ine5
left join ietr on ind.ine5 = ietr.ine5
left join tipo on ind.ine5 = tipo.ine5
left join conf on ind.ine5 = conf.ine5
left join med  on ind.tipus_territorial = med.tipus_territorial
order by ind.ine5
