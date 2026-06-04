{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5) TO '"
              ~ var('marts_root') ~ "/mart_electoral.parquet' (FORMAT PARQUET)"
) }}
-- mart_electoral · 1 fila per municipi (clau: ine5), columnes amb sufix de
-- convocatòria (A20241 = Parlament 2024, A20211 = 2021). Berguedà.
--
-- ⚠️ LECTURA ECOLÒGICA — NO INDIVIDUAL.
-- Els percentatges són quotes del vot vàlid AGREGAT del municipi; NO es poden
-- atribuir a persones (falàcia ecològica). Volàtil en micromunicipis (N petit:
-- p. ex. Sant Jaume de Frontanyà ~14 vots) — interpretar amb cura.
--
-- Columnes (per convocatòria CCC):
--   vots_valids_CCC        suma de vots de totes les candidatures (= vot vàlid)
--   pct_extrema_dreta_CCC  % VOX + Aliança Catalana + PxC… sobre vot vàlid
--   pct_indep_CCC          % bloc independentista sobre vot vàlid
--   pct_esq_CCC            % bloc d'esquerra sobre vot vàlid
--   guanya_CCC             sigla de la candidatura més votada (argmax vots)
--
-- Classificació de blocs: int_electoral_classificacio (regles de Talaia).
-- Clau de join amb mart_municipi: ine5 (crosswalk aplicat a stg_electoral;
-- Gósol=25100 coincideix, vegeu seeds/crosswalk_electoral_ine5.csv).

with cls as (
    select * from {{ ref('int_electoral_classificacio') }}
),

-- Agregats per municipi × convocatòria.
agg as (
    select
        ine5,
        id_eleccio,
        any_value(territori_nom)                                    as territori_nom,
        sum(vots)                                                   as vots_valids,
        round(100.0 * sum(case when is_extrema_dreta then vots else 0 end) / nullif(sum(vots), 0), 2) as pct_extrema_dreta,
        round(100.0 * sum(case when is_indep         then vots else 0 end) / nullif(sum(vots), 0), 2) as pct_indep,
        round(100.0 * sum(case when is_esquerra      then vots else 0 end) / nullif(sum(vots), 0), 2) as pct_esquerra
    from cls
    group by ine5, id_eleccio
),

-- Guanyadora per municipi × convocatòria (argmax vots; desempat alfabètic estable).
guanya as (
    select ine5, id_eleccio, candidatura_sigles as guanya
    from (
        select
            ine5, id_eleccio, candidatura_sigles,
            row_number() over (
                partition by ine5, id_eleccio
                order by vots desc, candidatura_sigles
            ) as rn
        from cls
    )
    where rn = 1
),

-- Espina: tots els municipis del Berguedà (de mart_municipi) per garantir 31 files
-- encara que alguna convocatòria no tingui dades d'algun municipi.
munis as (
    select ine5, municipi from {{ ref('mart_municipi') }}
)

select
    munis.ine5,
    munis.municipi,

    -- Parlament 2024 (A20241)
    a24.vots_valids                                             as vots_valids_A20241,
    a24.pct_extrema_dreta                                       as pct_extrema_dreta_A20241,
    a24.pct_indep                                              as pct_indep_A20241,
    a24.pct_esquerra                                           as pct_esq_A20241,
    g24.guanya                                                 as guanya_A20241,

    -- Parlament 2021 (A20211)
    a21.vots_valids                                             as vots_valids_A20211,
    a21.pct_extrema_dreta                                       as pct_extrema_dreta_A20211,
    a21.pct_indep                                              as pct_indep_A20211,
    a21.pct_esquerra                                           as pct_esq_A20211,
    g21.guanya                                                 as guanya_A20211

from munis
left join agg    a24 on munis.ine5 = a24.ine5 and a24.id_eleccio = 'A20241'
left join guanya g24 on munis.ine5 = g24.ine5 and g24.id_eleccio = 'A20241'
left join agg    a21 on munis.ine5 = a21.ine5 and a21.id_eleccio = 'A20211'
left join guanya g21 on munis.ine5 = g21.ine5 and g21.id_eleccio = 'A20211'
order by munis.ine5
