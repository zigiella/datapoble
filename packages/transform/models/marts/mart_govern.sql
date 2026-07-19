{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5, metric) TO '"
              ~ var('marts_root') ~ "/mart_govern.parquet' (FORMAT PARQUET)"
) }}
-- mart_govern · el tauler de govern amb PROCEDÈNCIA (D4). Format LLARG: 1 fila per
-- (ine5, metric). Per a cada municipi de Catalunya i cada KPI OFICIAL i MESURAT del
-- tauler (gorra-alcalde-pobla.md §3), emet: el valor, el rang «k de n» CONTRA LA
-- COMARCA DEL MUNICIPI, n_amb_dada (el denominador honest) i la data (vintage).
--
-- EL RANG ES CALCULA AQUÍ, MAI AL FRONT (C6 §4). El front rep k/n ja fets; així un
-- municipi de qualsevol comarca es compara amb els SEUS iguals (Gombrèn → k de 19 del
-- Ripollès, no dels 31 del Berguedà), sense cap llista fixa cablejada.
--
-- COMARCA = AUTORITAT municipis-territori.json (data/web, 947 munis) — MAI una llista
-- fixa ni la comarca derivada dels residus: la partició del rang ha de venir del mapa
-- territorial canònic. read_text→json_keys extreu ine5→comarca de l'objecte JSON.
--
-- SELECCIÓ DE MÈTRIQUES (gorra §3 «que siguin oficials I mesurades»). S'inclouen els 7
-- KPIs que són (a) MESURA d'una font OFICIAL i (b) transversals i comparables entre els
-- municipis d'una comarca. Es DEIXEN FORA, amb motiu (frontera honesta, no oblit):
--   · KPI 3 origen/«nova població» — nota narrativa VINCULANT de Bea (gorra §3): cap
--     rang públic d'aquest KPI abans del seu vot; a més viu a mart_demografia. Handoff.
--   · KPI 4 ETCA — presència oficial però ABSOLUTA i ESCASSA (falta a molts <1.000);
--     el seu rang comarcal duplicaria el de població i no viu en aquest pipeline. La
--     fitxa ja el mostra com a dada oficial.
--   · KPI 8 atur — MENSUAL i EMMASCARAT («<5» = interval [1,4], C1 §1.1): un interval
--     no es pot rankejar honestament. Viu a mart_pols_mensual (la seva llar).
--   · KPI 10 serveis/restauració — OSM, NO oficial («mínim observat, no cens») i NULL
--     fora del Berguedà. No entra a un rang oficial.
--   · KPI 11 radar / KPI 12 licitacions — no són mètriques mesurades del mart (tracks R/cabal).
-- El model de pernocta i els índexs compostos (IETR/index_turisme) queden fora per
-- construcció: el tauler de govern va NOMÉS amb dada oficial i consolidada (gorra §1).
--
-- CONVENCIÓ DEL RANG: rank() DESCENDENT pel valor (1 = el valor més alt de la comarca),
-- els EMPATS comparteixen posició i el següent salta (com IETR_rank, #263) — mai ordre
-- fabricat dins l'empat. Reprodueix byte a byte els rangs de la gorra (Pobla: envelliment
-- 6/31, padró 8/31, %no-principal 10/31, renda 19/31, residus 24/31). NULL honest: on el
-- municipi no té la dada, rang = NULL (no es rankeja) i n_amb_dada l'exclou del denominador.

with terr as (
    -- ine5 → comarca des de l'objecte JSON {"08001": {"comarca": …}, …}. read_text llegeix
    -- el fitxer sencer com a una fila; json_keys en treu els 947 ine5; json_extract_string
    -- la comarca de cadascun. És l'autoritat territorial del web (mai la del mart de residus).
    with raw as (
        select json(content) as j
        from read_text('{{ var("web_root") }}/municipis-territori.json')
    ),
    keys as (
        select unnest(json_keys(j)) as ine5, j from raw
    )
    select ine5, json_extract_string(j, '$.' || ine5 || '.comarca') as comarca
    from keys
),

-- Valors dels 7 KPIs des de mart_municipi (tota Catalunya). Cast a DOUBLE per unificar
-- els tipus al format llarg. La comarca ve de terr (JSON), no de mart_municipi.
base as (
    select
        m.ine5,
        m.codi6,
        m.municipi,
        t.comarca,
        cast(m.index_envelliment  as double) as index_envelliment,
        cast(m.poblacio           as double) as poblacio,
        cast(m.pct_noprincipal    as double) as pct_noprincipal,
        cast(m.rtc_per_1000hab    as double) as rtc_per_1000hab,
        cast(m.kwh_hab            as double) as kwh_hab,
        cast(m.renda_neta_persona as double) as renda_neta_persona,
        cast(m.kg_hab_any         as double) as kg_hab_any
    from {{ ref('mart_municipi') }} m
    join terr t on m.ine5 = t.ine5
),

-- Format llarg per UNION ALL (explícit: control total del NULL — a diferència d'UNPIVOT,
-- que descarta els nuls per defecte i ens faria perdre les files «sense dada»). La `data`
-- (vintage) de cada KPI és la del contracte semantic/metrics.yml, citada al costat.
long as (
    select ine5, codi6, municipi, comarca, 'index_envelliment'  as metric, index_envelliment  as valor, '2025' as data from base
    union all
    select ine5, codi6, municipi, comarca, 'poblacio'           as metric, poblacio           as valor, '2025' as data from base  -- Idescat EMEX
    union all
    select ine5, codi6, municipi, comarca, 'pct_noprincipal'    as metric, pct_noprincipal    as valor, '2021' as data from base  -- Cens INE
    union all
    select ine5, codi6, municipi, comarca, 'rtc_per_1000hab'    as metric, rtc_per_1000hab    as valor, '2026' as data from base  -- RTC (Generalitat)
    union all
    select ine5, codi6, municipi, comarca, 'kwh_hab'            as metric, kwh_hab            as valor, '2024' as data from base  -- ICAEN
    union all
    select ine5, codi6, municipi, comarca, 'renda_neta_persona' as metric, renda_neta_persona as valor, '2023' as data from base  -- INE ADRH
    union all
    select ine5, codi6, municipi, comarca, 'kg_hab_any'         as metric, kg_hab_any         as valor, '2024' as data from base  -- ARC residus
),

-- Rang «k de n» DINS la comarca del municipi. nulls last → les files amb valor rankegen
-- 1..n_amb_dada primer; la CASE anul·la el rang de les files sense dada. n_amb_dada =
-- count(valor) = municipis de la comarca amb la dada (el denominador honest).
ranked as (
    select
        ine5, codi6, municipi, comarca, metric, valor, data,
        case
            when valor is null then null
            else rank() over (partition by comarca, metric order by valor desc nulls last)
        end                                                    as rang,
        count(valor) over (partition by comarca, metric)       as n_amb_dada
    from long
)

select
    ine5,
    codi6,
    municipi,
    comarca,
    metric,
    valor,
    rang,
    cast(n_amb_dada as integer) as n_amb_dada,
    data
from ranked
order by ine5, metric
