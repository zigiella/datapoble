{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5, date) TO '"
              ~ var('marts_root') ~ "/mart_pols_mensual.parquet' (FORMAT PARQUET)"
) }}
-- mart_pols_mensual · el pols MENSUAL del municipi (C1 §1.1) — primera taula
-- mensual del catàleg. Format LLARG: 1 fila per (ine5, date), date = "YYYY-MM".
-- Família inaugural: atur_registrat (SEPE, sèrie des de 2006, els 947 municipis).
--
-- Filtre pel CATÀLEG DE CATALUNYA sencer (data/territorial/municipis-catalunya.csv,
-- 947 ine5) — MAI per província ni comarca: Gósol és Lleida (25100) i Gombrèn és
-- Girona (17080). El rang comarcal (D4) es calcula aigües avall contra la comarca
-- del municipi, no aquí.
--
-- Doctrina del «<5» (C1 §1.1, vinculant): des de 2022-01 el SEPE emmascara els
-- valors 1–4. Un '<5' és un INTERVAL [1,4]: atur_registrat NULL + min/max + flag
-- atur_emmascarat. MAI zero, MAI NaN silenciós: tot NULL del punt va acompanyat
-- del seu interval i del flag. La UI el mostra com a «<5».
--
-- Honest boundaries:
--   · El mart NO ref' mart_municipi: l'espina és el REGISTRE versionat dels 947
--     (el mateix catàleg que filtra el connector). Així el refresh mensual només
--     necessita la raw d'atur — cap dependència del lot EMEX.
--   · Municipis desapareguts (fusions) dels anys vells queden FORA (el catàleg
--     és el vigent); mesos on un municipi no surt a la font = cap fila (res
--     d'inventat). La cobertura per mes es declara al verificador, no s'amaga.

with atur as (
    select
        ine5,
        date,
        municipi_sepe,
        total_literal,
        atur_registrat,
        atur_registrat_min,
        atur_registrat_max,
        atur_emmascarat
    from {{ ref('stg_atur_sepe') }}
),

-- Espina canònica: el registre versionat dels 947 (codi6 Idescat + nom oficial).
-- codi6/ine5 com a VARCHAR explícit: read_csv_auto es menjaria els zeros davanters.
munis as (
    select ine5, codi6, nom as municipi
    from read_csv(
        '{{ var("territorial_root") }}/municipis-catalunya.csv',
        header = true,
        delim = ';',
        columns = {'codi6': 'VARCHAR', 'ine5': 'VARCHAR', 'nom': 'VARCHAR'}
    )
)

select
    atur.ine5,
    munis.codi6,
    munis.municipi,               -- nom oficial del registre (no el del SEPE)
    atur.date,                    -- "YYYY-MM" (C1 §1.1: el format queda fixat aquí)
    atur.atur_registrat,          -- NULL si emmascarat (el punt no s'inventa)
    atur.atur_registrat_min,      -- interval [1,4] quan emmascarat; = valor si exacte
    atur.atur_registrat_max,
    atur.atur_emmascarat          -- true = la font servia '<5' (secret estadístic)
from atur
join munis on atur.ine5 = munis.ine5
order by atur.ine5, atur.date
