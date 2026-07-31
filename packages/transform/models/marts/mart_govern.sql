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
-- SELECCIÓ DE MÈTRIQUES (gorra §3 «que siguin oficials I mesurades»). S'inclouen els 9
-- KPIs que són (a) MESURA d'una font OFICIAL i (b) transversals i comparables entre els
-- municipis d'una comarca. Es DEIXEN FORA, amb motiu (frontera honesta, no oblit):
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
-- W3 (2026-07-31) · LES DUES QUE ARRIBEN TARD, cadascuna amb la seva autorització:
--   · `vidre_hab` — esmena de Bea («vidre kg/hab/any no té rang»). Mateixa font i
--     mateix denominador que kg_hab_any (ARC 2024, població de residus), cobertura
--     947/947 sense cap forat: rankejable sense cap reserva.
--   · `pct_nacionalitat_estrangera` — VIU A mart_demografia, no a mart_municipi. Fins
--     avui aquest capçal deia «cap rang públic abans del vot de Bea» (nota narrativa de
--     la gorra §3); **el vot ja va arribar**: esmena E9 de
--     `docs/ajuntaments/tauler-v2-esmenes-bea.md` (2026-07-19, vinculant i que MANA
--     sobre la gorra §3) — «Rang comarcal al % nacionalitat estrangera … estava retingut
--     esperant el vot, ara s'hi posa». El que NO va arribar mai és el rang: el front va
--     quedar-se amb `pendingRank` perquè el mart no el calculava. Aquesta línia el tanca.
--     La nota narrativa segueix viva per a TOT el que és copy (etiqueta, frase, com es
--     llegeix un «1r de 27») — això és de Bea, no d'aquest model.
--     Cobertura 938/947 (9 NULL pel llindar mínim N de mart_demografia, secret/soroll
--     als micromunicipis): el rang els exclou i n_amb_dada ho diu (Berguedà: 27 de 31).
--
-- W4 (2026-07-31) · VALOR DE REFERÈNCIA = LA MEDIANA DE LES NOSTRES DADES. La targeta
-- vol un «consum de referència» al costat del rang. ⚠️ NO es fan servir les constants
-- base_residencial (410) / base_electric (1224) / base_vidre (26,5) de dbt_project.yml:
-- són les BASES DEL MODEL DE PERNOCTA APARCAT (capes L1/L2/L3) i posar-les en una
-- targeta viva reintroduiria el model per la porta del darrere. La referència honesta
-- es MESURA de la nostra pròpia dada: la mediana dels municipis amb dada. S'emeten LES
-- DUES (la de la seva comarca i la de Catalunya) per a TOTES les mètriques del mart —
-- surten del MATEIX partition by que el rang, no costen res i no fabriquen res; QUINA
-- es pinta és decisió editorial (Bea), i servint-les totes dues no la bloquegem.
-- Procedència (C6 §8.1): la mediana comarcal es calcula sobre `n_amb_dada` municipis
-- (el MATEIX denominador honest del rang) i la catalana sobre `n_mediana_catalunya`.
--
-- R-REFERENCIA (2026-07-31) · DUES REFERÈNCIES NOVES AL COSTAT DE LES MEDIANES DE W4.
-- Bea va portar les xifres oficials i la comparació va destapar que la mediana respon una
-- pregunta («com és un municipi típic») i el titular oficial una altra («quant li toca a
-- cada habitant»). S'emeten les dues perquè decidir quina es pinta és editorial:
--
--   1) PONDERADA (`ponderada_comarca` / `ponderada_catalunya`) = TOTAL ÷ HABITANTS, que és
--      l'equivalent exacte de com publiquen la xifra l'ARC, l'ICAEN i l'Idescat. NO és una
--      mitjana de mitjanes: cada mètrica es pondera pel SEU PROPI DENOMINADOR (`pes_ponderada`),
--      i així la ponderada és aritmèticament idèntica al quocient dels totals —
--      pct_noprincipal es pondera per hab_total, index_envelliment per pob_0_14, kg_hab_any i
--      vidre_hab per poblacio_residus (el padró que fa servir l'ARC), kwh_hab per poblacio_kwh
--      (el padró de l'any del consum). Ponderar-ho tot per `poblacio` hauria estat un número
--      que s'assembla al bo però no és el bo.
--      ⚠️ `poblacio` NO en té: la ponderada d'una població per la població no és una
--      referència, és una altra pregunta (la mida del municipi on viu el català mitjà).
--      Surt NULL amb `pes_ponderada` NULL — forat declarat, no oblidat.
--      `hab_ponderada_*` porta el denominador (habitants), que és la procedència que
--      C6 §8.1 exigeix: una mediana es diu «sobre n municipis»; una ponderada, «sobre n habitants».
--
--      ⚠️ LA REFERÈNCIA HA DE SORTIR DE LA MATEIXA FONT QUE EL NUMERADOR, i aquí es veu per què:
--      per als residus, la nostra ponderada de 2024 dona 476,85 kg/hab i el titular d'Idescat
--      per a Catalunya ~500. La diferència NO és un error de ningú: el propi dataset de l'ARC
--      porta una fila «No territorialitzable» amb 175.115,55 t (residus que no s'atribueixen a
--      cap municipi); amb ella el total fa 3.995.724 t = 498,70 kg/hab, que és el titular. Si
--      poséssim el 500 al costat de xifres municipals que sumen 476,85, TOTS els municipis
--      semblarien un 4,4% millors del que són.
--
--   2) ESTRATIFICADA PER FRANJA DE POBLACIÓ (`mediana_franja`, sobre `n_franja` municipis de
--      TOT Catalunya de la mateixa franja). Talls de Bea: <250 · 250-499 · 500-999 ·
--      1.000-4.999 · 5.000-19.999 · ≥20.000, sobre el padró vigent (el que es pinta a la fitxa).
--      ⚠️ ES SERVEIX PER A LES NOU, PERÒ NO EXPLICA IGUAL DE BÉ TOTES NOU — i això no ho pot
--      dir el SQL, ho ha de saber qui pinta. Mesurat sobre els 947 (variància explicada
--      ajustada pels graus de llibertat, bitàcola 2026-07-31): la franja explica el 9,5% del
--      consum elèctric i el 16,5% del vidre (gradients monòtons, defensables) però NOMÉS EL
--      4,0% dels residus, on el gradient ni tan sols és monòton (554 → 479 → 428 → 438 → 502
--      → 447). Als residus la mida NO explica res: qui més hi explica és la COMARCA (33,1%),
--      que és justament la partició que el rang i la mediana comarcal ja fan servir.

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

-- L'ÚNICA columna que ve de mart_demografia (W3). Se'n pren NOMÉS ine5 + el valor:
-- mart_demografia també porta `comarca`, però la seva ve de stg_residus i aquí la
-- partició del rang l'ha de fixar terr (municipis-territori.json) i NOMÉS terr — si es
-- colés l'altra, dos KPIs del mateix tauler podrien rankejar contra dues particions
-- diferents sense que res petés. 1 fila per ine5 (947, clau del mart): el left join no
-- pot multiplicar files, i verify_govern ho comprova (947 × 9 exactes).
dem as (
    select ine5, cast(pct_nacionalitat_estrangera as double) as pct_nacionalitat_estrangera
    from {{ ref('mart_demografia') }}
),

-- Valors dels 9 KPIs (tota Catalunya). Cast a DOUBLE per unificar els tipus al format
-- llarg. La comarca ve de terr (JSON), no de mart_municipi ni de mart_demografia.
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
        cast(m.kg_hab_any         as double) as kg_hab_any,
        cast(m.vidre_hab          as double) as vidre_hab,
        d.pct_nacionalitat_estrangera        as pct_nacionalitat_estrangera,
        -- DENOMINADORS de cada mètrica (pesos de la ponderada). No són mètriques noves:
        -- són el denominador que la mètrica ja fa servir, exposat per poder auditar.
        cast(m.hab_total          as double) as pes_hab_total,
        cast(m.pob_0_14           as double) as pes_pob_0_14,
        cast(m.poblacio_residus   as double) as pes_poblacio_residus,
        cast(m.poblacio_kwh       as double) as pes_poblacio_kwh
    from {{ ref('mart_municipi') }} m
    join terr t on m.ine5 = t.ine5
    left join dem d on m.ine5 = d.ine5
),

-- Format llarg per UNION ALL (explícit: control total del NULL — a diferència d'UNPIVOT,
-- que descarta els nuls per defecte i ens faria perdre les files «sense dada»). La `data`
-- (vintage) de cada KPI és la del contracte semantic/metrics.yml, citada al costat.
-- `pes` = el DENOMINADOR PROPI de cada mètrica i `pes_ponderada` el seu nom (procedència
-- llegible). `franja` = franja de població del municipi (talls de Bea), sobre el padró vigent.
long as (
    select ine5, codi6, municipi, comarca, 'index_envelliment'  as metric, index_envelliment  as valor, '2025' as data,
           pes_pob_0_14 as pes, 'pob_0_14' as pes_ponderada, poblacio from base
    union all
    select ine5, codi6, municipi, comarca, 'poblacio'           as metric, poblacio           as valor, '2025' as data,  -- Idescat EMEX
           cast(null as double) as pes, cast(null as varchar) as pes_ponderada, poblacio from base
    union all
    select ine5, codi6, municipi, comarca, 'pct_noprincipal'    as metric, pct_noprincipal    as valor, '2021' as data,  -- Cens INE
           pes_hab_total as pes, 'hab_total' as pes_ponderada, poblacio from base
    union all
    select ine5, codi6, municipi, comarca, 'rtc_per_1000hab'    as metric, rtc_per_1000hab    as valor, '2026' as data,  -- RTC (Generalitat)
           poblacio as pes, 'poblacio' as pes_ponderada, poblacio from base
    union all
    select ine5, codi6, municipi, comarca, 'kwh_hab'            as metric, kwh_hab            as valor, '2024' as data,  -- ICAEN
           pes_poblacio_kwh as pes, 'poblacio_kwh' as pes_ponderada, poblacio from base
    union all
    select ine5, codi6, municipi, comarca, 'renda_neta_persona' as metric, renda_neta_persona as valor, '2023' as data,  -- INE ADRH
           poblacio as pes, 'poblacio' as pes_ponderada, poblacio from base
    union all
    select ine5, codi6, municipi, comarca, 'kg_hab_any'         as metric, kg_hab_any         as valor, '2024' as data,  -- ARC residus
           pes_poblacio_residus as pes, 'poblacio_residus' as pes_ponderada, poblacio from base
    union all
    select ine5, codi6, municipi, comarca, 'vidre_hab'          as metric, vidre_hab          as valor, '2024' as data,  -- ARC residus (fracció vidre)
           pes_poblacio_residus as pes, 'poblacio_residus' as pes_ponderada, poblacio from base
    union all
    select ine5, codi6, municipi, comarca, 'pct_nacionalitat_estrangera' as metric,
           pct_nacionalitat_estrangera as valor, '2025' as data,  -- Idescat (Cens anual)
           poblacio as pes, 'poblacio' as pes_ponderada, poblacio from base
),

-- FRANJA DE POBLACIÓ (talls de Bea, R-REFERENCIA 2026-07-31). Sobre `poblacio` (padró
-- vigent), que és el número que la fitxa pinta: si la franja es calculés amb un padró
-- diferent del que es llegeix a la targeta, el lector no podria refer el càlcul.
franjat as (
    select
        long.*,
        case
            when poblacio is null      then null
            when poblacio <    250     then '<250'
            when poblacio <    500     then '250-499'
            when poblacio <   1000     then '500-999'
            when poblacio <   5000     then '1.000-4.999'
            when poblacio <  20000     then '5.000-19.999'
            else '>=20.000'
        end as franja_poblacio
    from long
),

-- Rang «k de n» DINS la comarca del municipi. nulls last → les files amb valor rankegen
-- 1..n_amb_dada primer; la CASE anul·la el rang de les files sense dada. n_amb_dada =
-- count(valor) = municipis de la comarca amb la dada (el denominador honest).
--
-- W4 · les DUES medianes surten del MATEIX partition by que el rang (la comarcal) i
-- d'un de global (la catalana). median() ignora els NULL, així que el seu denominador
-- és exactament el del rang: n_amb_dada per a la comarcal, n_mediana_catalunya per a la
-- catalana. NO S'ARRODONEIX aquí: es va provar amb round(…,2) i es va retirar perquè
-- DuckDB i pandas trenquen els empats del .005 amb regles diferents (18-19 dels 387
-- grups discrepaven en 0,01) i el verificador hauria hagut de replicar una regla
-- d'implementació del motor en comptes de recalcular la mediana. Sense arrodonir, la
-- mediana de DuckDB i la de pandas coincideixen BIT A BIT als 387 grups comarcals i als
-- 9 catalans, i verify_govern.py les compara amb igualtat exacta. Arrodonir per pintar
-- és feina de la targeta, no del mart.
--
-- R-REFERENCIA · les PONDERADES surten del mateix partition by. `sum(valor*pes)` ignora els
-- NULL, i el denominador ha d'ignorar EXACTAMENT les mateixes files: per això és
-- `sum(case when valor is not null then pes end)` i no `sum(pes)` — si no, un municipi sense
-- dada hi posaria habitants sense posar-hi numerador i la referència sortiria baixa.
-- No s'arrodoneix (mateixa raó que W4: DuckDB i pandas trenquen els empats del .005 diferent
-- i el verificador ha de poder comparar amb igualtat EXACTA). Arrodonir per pintar és de la targeta.
ranked as (
    select
        ine5, codi6, municipi, comarca, metric, valor, data, pes_ponderada, franja_poblacio,
        case
            when valor is null then null
            else rank() over (partition by comarca, metric order by valor desc nulls last)
        end                                                    as rang,
        count(valor) over (partition by comarca, metric)       as n_amb_dada,
        median(valor) over (partition by comarca, metric)      as mediana_comarca,
        median(valor) over (partition by metric)               as mediana_catalunya,
        count(valor) over (partition by metric)                as n_mediana_catalunya,

        sum(valor * pes) over (partition by comarca, metric)
          / nullif(sum(case when valor is not null then pes end)
                   over (partition by comarca, metric), 0)     as ponderada_comarca,
        sum(case when valor is not null then pes end)
          over (partition by comarca, metric)                  as hab_ponderada_comarca,
        sum(valor * pes) over (partition by metric)
          / nullif(sum(case when valor is not null then pes end)
                   over (partition by metric), 0)              as ponderada_catalunya,
        sum(case when valor is not null then pes end)
          over (partition by metric)                           as hab_ponderada_catalunya,

        median(valor) over (partition by metric, franja_poblacio) as mediana_franja,
        count(valor) over (partition by metric, franja_poblacio)  as n_franja
    from franjat
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
    data,
    -- W4 · valor de referència MESURAT de la nostra pròpia dada (mai les bases del model
    -- de pernocta aparcat). La comarcal es calcula sobre n_amb_dada municipis.
    mediana_comarca,
    mediana_catalunya,
    cast(n_mediana_catalunya as integer) as n_mediana_catalunya,
    -- R-REFERENCIA · la ponderada (= total ÷ habitants, l'equivalent del titular oficial)
    -- amb el nom del pes i el nombre d'habitants que hi ha al denominador (procedència).
    pes_ponderada,
    ponderada_comarca,
    hab_ponderada_comarca,
    ponderada_catalunya,
    hab_ponderada_catalunya,
    -- R-REFERENCIA · l'estratificada per mida (mediana de la franja a TOT Catalunya).
    franja_poblacio,
    mediana_franja,
    cast(n_franja as integer) as n_franja
from ranked
order by ine5, metric
