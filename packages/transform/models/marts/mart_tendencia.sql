{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5, metric, comparacio) TO '"
              ~ var('marts_root') ~ "/mart_tendencia.parquet' (FORMAT PARQUET)"
) }}
-- mart_tendencia · la TENDÈNCIA amb el seu període declarat (E6 de les esmenes de Bea).
-- Format LLARG: 1 fila per (ine5, metric, comparacio).
--
-- LA REGLA (§2 de docs/ajuntaments/tauler-v2-esmenes-bea.md, vinculant):
--   «Cap targeta amb fletxa sense període.» Només es mostra tendència on hi ha SÈRIE
--   REAL, i tota tendència diu CONTRA QUIN PERÍODE compara. Per això aquest mart no té
--   cap fila muda: TOTA mètrica del tauler hi surt, i la que no té sèrie hi surt amb
--   estat = 'sense_serie' + `motiu` escrit. El front no pot confondre un NULL amb un zero
--   perquè el NULL sempre ve acompanyat de l'estat i del motiu.
--
-- QUI TÉ SÈRIE (i qui no) — l'estat del terreny, no una aspiració:
--   · atur_registrat — SEPE, mensual 2006→. DUES comparacions, no una: el mes anterior
--     i el MATEIX MES DE L'ANY ANTERIOR. L'atur és estacional (a la Pobla de Lillet,
--     2026-06: +4 contra el mes anterior però −3 contra el mateix mes de 2025 — la
--     mateixa xifra puja o baixa segons contra què la miris). Ensenyar-ne només una
--     seria triar la narrativa; s'emeten totes dues i que el lector les vegi.
--   · pct_nacionalitat_estrangera / poblacio_nacionalitat_estrangera — Cens anual,
--     finestra 2021→2025 ja calculada a mart_demografia (no es recalcula aquí).
--   · TOTA LA RESTA (població, franges d'edat, renda, habitatge, residus, energia, RTC)
--     — 'sense_serie'. Població i franges hi són perquè EMEX **no serveix sèrie**: la
--     seva API només té els filtres id/i/tipus, cap de temporal (verificat en viu contra
--     l'API i contra la documentació oficial, 2026-07-20; els paràmetres temporals que
--     es provin s'ignoren en silenci i la resposta torna sempre el darrer període). No
--     és un pendent d'ingesta: és un límit de la font, i es diu.
--
-- DOCTRINA DEL «<5» A LA RESTA (C1 §1.1): quan un dels dos mesos ve emmascarat, la
-- diferència NO és un número, és un INTERVAL. Llavors delta = NULL i s'emeten
-- delta_min = actual_min − anterior_max i delta_max = actual_max − anterior_min, amb
-- delta_emmascarat = true. Restar l'emmascarat com si fos zero seria inventar-se el signe.

with pols as (
    select * from {{ ref('mart_pols_mensual') }}
),

-- Darrer mes disponible a la font (global, no per municipi: el SEPE publica tot el
-- padró de cop; un municipi que falti aquell mes simplement no tindrà fila).
darrer_mes as (
    select max(date) as mes from pols
),

-- Els tres punts que necessiten les dues comparacions de l'atur: el darrer mes, el mes
-- immediatament anterior i el mateix mes de l'any anterior. Es calculen amb aritmètica
-- de dates sobre "YYYY-MM" (strptime → interval) per no dependre de la continuïtat de
-- la sèrie: si el punt de comparació no existeix a la font, el join no lliga i la fila
-- surt sense tendència (honest) en comptes d'agafar «el punt anterior que hi hagi».
periodes as (
    select
        mes                                                                  as mes_actual,
        strftime(strptime(mes, '%Y-%m') - interval 1 month,  '%Y-%m')        as mes_anterior,
        strftime(strptime(mes, '%Y-%m') - interval 12 month, '%Y-%m')        as mes_any_anterior
    from darrer_mes
),

atur_actual as (
    select p.* from pols p, periodes pe where p.date = pe.mes_actual
),

atur_prev_mes as (
    select p.ine5, p.date, p.atur_registrat, p.atur_registrat_min, p.atur_registrat_max, p.atur_emmascarat
    from pols p, periodes pe where p.date = pe.mes_anterior
),

atur_prev_any as (
    select p.ine5, p.date, p.atur_registrat, p.atur_registrat_min, p.atur_registrat_max, p.atur_emmascarat
    from pols p, periodes pe where p.date = pe.mes_any_anterior
),

-- Les dues comparacions de l'atur, en format llarg. `comparacio` diu quina és; els camps
-- de període diuen contra QUÈ (el literal "YYYY-MM" que el front pot pintar tal qual).
atur_tend as (
    select
        a.ine5, a.codi6, a.municipi,
        'atur_registrat'                              as metric,
        'mes_anterior'                                as comparacio,
        a.date                                        as periode_actual,
        b.date                                        as periode_anterior,
        a.atur_registrat                              as valor_actual,
        b.atur_registrat                              as valor_anterior,
        (a.atur_emmascarat or b.atur_emmascarat)      as delta_emmascarat,
        a.atur_registrat_min, a.atur_registrat_max,
        b.atur_registrat_min as prev_min, b.atur_registrat_max as prev_max
    from atur_actual a
    join atur_prev_mes b on a.ine5 = b.ine5

    union all

    select
        a.ine5, a.codi6, a.municipi,
        'atur_registrat'                              as metric,
        'mateix_mes_any_anterior'                     as comparacio,
        a.date                                        as periode_actual,
        b.date                                        as periode_anterior,
        a.atur_registrat                              as valor_actual,
        b.atur_registrat                              as valor_anterior,
        (a.atur_emmascarat or b.atur_emmascarat)      as delta_emmascarat,
        a.atur_registrat_min, a.atur_registrat_max,
        b.atur_registrat_min as prev_min, b.atur_registrat_max as prev_max
    from atur_actual a
    join atur_prev_any b on a.ine5 = b.ine5
),

atur_out as (
    select
        ine5, codi6, municipi, metric, comparacio,
        'amb_serie'                                          as estat,
        cast(null as varchar)                                as motiu,
        periode_actual, periode_anterior,
        cast(valor_actual as double)                         as valor_actual,
        cast(valor_anterior as double)                       as valor_anterior,
        -- delta exacte NOMÉS si cap dels dos punts ve emmascarat.
        case when delta_emmascarat then null
             else cast(valor_actual - valor_anterior as double) end   as delta,
        -- interval del delta: sempre emès (amb emmascarament o sense; sense, min=max=delta).
        cast(atur_registrat_min - prev_max as double)        as delta_min,
        cast(atur_registrat_max - prev_min as double)        as delta_max,
        delta_emmascarat,
        'persones'                                           as unitat_delta
    from atur_tend
),

-- ORIGEN · la finestra del Cens anual, JA calculada a mart_demografia (2021→2025).
-- No es recalcula: es re-exposa amb el període explícit al costat, que és el que
-- faltava perquè el tauler pogués pintar la fletxa sense mentir sobre el període.
origen as (
    select
        d.ine5,
        m.codi6,
        d.municipi,
        d.serie_any_inicial,
        d.serie_any_final,
        d.delta_pct_estrangera_finestra,
        d.delta_estrangers_finestra,
        d.pct_nacionalitat_estrangera,
        d.poblacio_nacionalitat_estrangera
    from {{ ref('mart_demografia') }} d
    join {{ ref('mart_municipi') }} m on d.ine5 = m.ine5
),

origen_out as (
    select
        ine5, codi6, municipi,
        'pct_nacionalitat_estrangera'                        as metric,
        'finestra_anual'                                     as comparacio,
        'amb_serie'                                          as estat,
        cast(null as varchar)                                as motiu,
        cast(serie_any_final   as varchar)                   as periode_actual,
        cast(serie_any_inicial as varchar)                   as periode_anterior,
        cast(pct_nacionalitat_estrangera as double)          as valor_actual,
        -- valor del període inicial = valor actual − delta (el delta és el que mana:
        -- ve de la sèrie del connector, no d'aquí).
        case when pct_nacionalitat_estrangera is null or delta_pct_estrangera_finestra is null
             then null
             else round(cast(pct_nacionalitat_estrangera - delta_pct_estrangera_finestra as double), 2)
        end                                                  as valor_anterior,
        cast(delta_pct_estrangera_finestra as double)        as delta,
        cast(delta_pct_estrangera_finestra as double)        as delta_min,
        cast(delta_pct_estrangera_finestra as double)        as delta_max,
        false                                                as delta_emmascarat,
        'punts_percentuals'                                  as unitat_delta
    from origen
    where serie_any_inicial is not null and serie_any_final is not null

    union all

    select
        ine5, codi6, municipi,
        'poblacio_nacionalitat_estrangera'                   as metric,
        'finestra_anual'                                     as comparacio,
        'amb_serie'                                          as estat,
        cast(null as varchar)                                as motiu,
        cast(serie_any_final   as varchar)                   as periode_actual,
        cast(serie_any_inicial as varchar)                   as periode_anterior,
        cast(poblacio_nacionalitat_estrangera as double)     as valor_actual,
        case when poblacio_nacionalitat_estrangera is null or delta_estrangers_finestra is null
             then null
             else cast(poblacio_nacionalitat_estrangera - delta_estrangers_finestra as double)
        end                                                  as valor_anterior,
        cast(delta_estrangers_finestra as double)            as delta,
        cast(delta_estrangers_finestra as double)            as delta_min,
        cast(delta_estrangers_finestra as double)            as delta_max,
        false                                                as delta_emmascarat,
        'persones'                                           as unitat_delta
    from origen
    where serie_any_inicial is not null and serie_any_final is not null
),

-- SENSE SÈRIE · files EXPLÍCITES, no absències. Cada mètrica del tauler que avui és una
-- sola foto surt aquí amb el seu motiu escrit, perquè la targeta pugui dir «sense sèrie»
-- en comptes de callar (i perquè un NULL mut no es pugui llegir com un zero).
sense as (
    select m.ine5, m.codi6, m.municipi, s.metric, s.motiu, s.valor
    from {{ ref('mart_municipi') }} m
    cross join lateral (
        values
            ('poblacio',           'EMEX serveix només el darrer període: la seva API (filtres id/i/tipus) no té cap paràmetre temporal — verificat en viu 2026-07-20. Sèrie oficial disponible per una altra via (Idescat censph), ingesta encuada.', cast(m.poblacio as double)),
            ('pob_0_14',           'Franja d''edat d''EMEX: mateix límit de font que la població (cap sèrie per API).', cast(m.pob_0_14 as double)),
            ('pob_15_64',          'Franja d''edat derivada d''EMEX: mateix límit de font que la població (cap sèrie per API).', cast(m.pob_15_64 as double)),
            ('pob_65_84',          'Franja d''edat d''EMEX: mateix límit de font que la població (cap sèrie per API).', cast(m.pob_65_84 as double)),
            ('pob_85_mes',         'Franja d''edat d''EMEX: mateix límit de font que la població (cap sèrie per API).', cast(m.pob_85_mes as double)),
            ('index_envelliment',  'Es deriva de franges d''EMEX, que no tenen sèrie per API.', cast(m.index_envelliment as double)),
            ('renda_neta_persona', 'INE ADRH: s''ingereix una sola foto (2023). Sèrie disponible a la font però encara no ingerida.', cast(m.renda_neta_persona as double)),
            ('pct_noprincipal',    'Cens d''habitatge 2021: dada decennal, no hi ha període anterior comparable ingerit.', cast(m.pct_noprincipal as double)),
            ('kg_hab_any',         'Residus (ARC): s''ingereix el darrer any tancat. Sèrie disponible a la font però encara no ingerida.', cast(m.kg_hab_any as double)),
            ('kwh_hab',            'Consum elèctric domèstic (ICAEN): s''ingereix el darrer any de cobertura plena. Sèrie disponible a la font però encara no ingerida.', cast(m.kwh_hab as double)),
            ('vidre_hab',          'Fracció vidre (ARC): s''ingereix el darrer any tancat. Sèrie disponible a la font però encara no ingerida.', cast(m.vidre_hab as double)),
            ('rtc_per_1000hab',    'Registre de Turisme de Catalunya: és un registre viu, es llegeix com a foto del dia de la càrrega; no se''n conserva cap tall anterior.', cast(m.rtc_per_1000hab as double))
    ) as s(metric, motiu, valor)
),

sense_out as (
    select
        ine5, codi6, municipi, metric,
        cast(null as varchar)      as comparacio,
        'sense_serie'              as estat,
        motiu,
        cast(null as varchar)      as periode_actual,
        cast(null as varchar)      as periode_anterior,
        valor                      as valor_actual,
        cast(null as double)       as valor_anterior,
        cast(null as double)       as delta,
        cast(null as double)       as delta_min,
        cast(null as double)       as delta_max,
        false                      as delta_emmascarat,
        cast(null as varchar)      as unitat_delta
    from sense
),

unio as (
    select ine5, codi6, municipi, metric, comparacio, estat, motiu, periode_actual,
           periode_anterior, valor_actual, valor_anterior, delta, delta_min, delta_max,
           delta_emmascarat, unitat_delta
    from atur_out
    union all
    select ine5, codi6, municipi, metric, comparacio, estat, motiu, periode_actual,
           periode_anterior, valor_actual, valor_anterior, delta, delta_min, delta_max,
           delta_emmascarat, unitat_delta
    from origen_out
    union all
    select ine5, codi6, municipi, metric, comparacio, estat, motiu, periode_actual,
           periode_anterior, valor_actual, valor_anterior, delta, delta_min, delta_max,
           delta_emmascarat, unitat_delta
    from sense_out
),

-- comarca des de l'AUTORITAT territorial del web (mateix criteri que mart_govern: mai
-- una llista fixa, mai la comarca dels residus).
terr as (
    with raw as (
        select json(content) as j
        from read_text('{{ var("web_root") }}/municipis-territori.json')
    ),
    keys as (
        select unnest(json_keys(j)) as ine5, j from raw
    )
    select ine5, json_extract_string(j, '$.' || ine5 || '.comarca') as comarca
    from keys
)

select
    u.ine5,
    u.codi6,
    u.municipi,
    t.comarca,
    u.metric,
    u.comparacio,
    u.estat,
    u.motiu,
    u.periode_actual,
    u.periode_anterior,
    u.valor_actual,
    u.valor_anterior,
    u.delta,
    u.delta_min,
    u.delta_max,
    u.delta_emmascarat,
    u.unitat_delta,
    -- DIRECCIÓ llegible (la fletxa), amb la regla d'honestedat aplicada als tres casos:
    --   · delta exacte        → el seu signe.
    --   · delta EMMASCARAT    → el signe NOMÉS si l'interval no travessa el zero (llavors
    --     està PROVAT: [1,4] puja segur, [-4,-1] baixa segur, encara que el número exacte
    --     sigui secret). Si el travessa ([-3,3]), 'indeterminat' EXPLÍCIT — que és una
    --     resposta, no una absència: el front ha de dir «no es pot dir amb el <5», no callar.
    --   · sense sèrie         → NULL (no hi ha res a comparar; l'estat ja ho diu).
    -- Així cap fletxa surt sense el seu període i sense número (exacte o interval) al darrere.
    case
        when u.estat = 'sense_serie' then null
        when u.delta is not null then
            case when u.delta > 0 then 'puja' when u.delta < 0 then 'baixa' else 'igual' end
        when u.delta_min is null or u.delta_max is null then null
        when u.delta_min > 0 then 'puja'
        when u.delta_max < 0 then 'baixa'
        else 'indeterminat'
    end                                            as direccio
from unio u
left join terr t on u.ine5 = t.ine5
order by u.ine5, u.metric, u.comparacio
