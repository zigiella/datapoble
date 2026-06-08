{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5) TO '"
              ~ var('marts_root') ~ "/mart_demografia.parquet' (FORMAT PARQUET)"
) }}
-- mart_demografia · 1 fila per municipi (clau: ine5). COMPOSICIÓ I ARRELAMENT
-- (origen) com a TRANSFORMACIÓ DEMOGRÀFICA — MAI «extranjería».
-- Columnes segons el contracte (semantic/metrics.yml, table: mart_demografia).
-- Espina = Idescat (Cens anual de població): EMEX (foto 2025) + Població estrangera
-- (sèrie 2021→). S'uneix per ine5 a mart_municipi (no en depèn).
--
-- TRES LENTS separades a propòsit (la gent les confon):
--   · nacionalitat (espanyola/estrangera) — passaport, NO arrelament.
--   · lloc de naixement (Catalunya/resta Espanya/estranger) — biografia (millor proxy).
--   · evolució temporal (deltes) — el vèrtigen, no la foto.
--
-- HONESTEDAT (innegociable):
--   · Lectura ECOLÒGICA: recomptes municipals, MAI individus.
--   · LLINDAR MÍNIM N (var demografia_min_n): per sota, els percentatges d'origen
--     són soroll / secret estadístic → es marquen confianca_origen='baixa' i NO es
--     publiquen els percentatges fins (es deixen NULL; el recompte brut sí, és públic).
--   · El secret estadístic de la font (estrangers '(..)' als micromunicipis) ja
--     arriba com a NULL i es propaga.
--   · El desglossament per PAÍS/grans àrees (UE/Magreb/…) NO és viable a escala
--     municipal per API oberta (secret estadístic sota província) → diversitat_origen
--     i rejoveniment_migratori queden 'planned' al contracte (vegeu el doc de fonts).

with origen as (
    select * from {{ ref('stg_demografia_origen') }}
),

deltes as (
    select * from {{ ref('int_demografia_deltes') }}
),

ctx as (
    select * from {{ ref('int_demografia_context') }}
),

noms as (
    -- nom oficial net: residus té els 31 amb nom
    select distinct ine5, municipi from {{ ref('stg_residus') }}
),

calc as (
    select
        o.ine5,
        o.codi6,
        noms.municipi,
        '{{ var("comarca") }}'                                          as comarca,
        o.any_referencia                                                as any_referencia,

        -- Recomptes bruts (directe EMEX). Públics fins i tot als micromunicipis
        -- (un total no és secret; el que se suprimeix són els percentatges fins).
        cast(o.pob_nac_total as integer)                                as poblacio,
        cast(o.nac_estrangera as integer)                               as poblacio_nacionalitat_estrangera,
        cast(o.nascuda_estranger as integer)                            as poblacio_nascuda_estranger,
        cast(o.nascuda_catalunya as integer)                            as poblacio_nascuda_catalunya,
        cast(o.nascuda_resta_espanya as integer)                        as poblacio_nascuda_resta_espanya,

        -- Llindar mínim N: per sota, els percentatges d'origen no es publiquen.
        (o.pob_nac_total >= {{ var('demografia_min_n') }})              as supera_min_n,

        -- ===== MÈTRIQUES NUCLI (percentatges) =====
        -- Es calculen sempre, però s'EMETEN NULL si no superen el llindar N (sota).
        round(o.nac_estrangera   / nullif(o.pob_nac_total, 0) * 100, 2) as pct_nac_estr_raw,
        round(o.nascuda_estranger / nullif(o.pob_lloc_naix_total, 0) * 100, 2) as pct_nasc_estr_raw,

        -- Context comarcal i de Catalunya (mateix indicador, nivells superiors).
        round(ctx.com_nac_estrangera    / nullif(ctx.com_pob_nac_total, 0) * 100, 2)      as pct_nacionalitat_estrangera_comarca,
        round(ctx.cat_nac_estrangera    / nullif(ctx.cat_pob_nac_total, 0) * 100, 2)      as pct_nacionalitat_estrangera_catalunya,
        round(ctx.com_nascuda_estranger / nullif(ctx.com_pob_lloc_naix_total, 0) * 100, 2) as pct_nascuda_estranger_comarca,
        round(ctx.cat_nascuda_estranger / nullif(ctx.cat_pob_lloc_naix_total, 0) * 100, 2) as pct_nascuda_estranger_catalunya,

        -- Deltes (de la sèrie 2021→).
        d.serie_any_inicial,
        d.serie_any_final,
        d.delta_pct_estrangera_5y,
        d.delta_pct_estrangera_finestra,
        d.delta_estrangers_finestra
    from origen o
    left join deltes d on o.ine5 = d.ine5
    left join noms      on o.ine5 = noms.ine5
    cross join ctx
)

select
    ine5,
    codi6,
    municipi,
    comarca,
    any_referencia,

    -- Recomptes bruts (públics)
    poblacio,
    poblacio_nacionalitat_estrangera,
    poblacio_nascuda_estranger,
    poblacio_nascuda_catalunya,
    poblacio_nascuda_resta_espanya,

    -- ===== MÈTRIQUES NUCLI =====
    -- pct_nacionalitat_estrangera: % amb passaport no espanyol. Es publica només si
    -- supera el llindar N (si no, NULL: secret/soroll). Lectura ecològica.
    case when supera_min_n then pct_nac_estr_raw else null end      as pct_nacionalitat_estrangera,

    -- pct_nascuda_estranger: % nascuda fora d'Espanya. MILLOR proxy d'origen que la
    -- nacionalitat (no depèn de l'estatus jurídic, que la naturalització esborra).
    case when supera_min_n then pct_nasc_estr_raw else null end     as pct_nascuda_estranger,

    -- bretxa_naturalitzacio = pct_nascuda_estranger − pct_nacionalitat_estrangera.
    -- Mesura quanta gent nascuda fora JA TÉ passaport espanyol (arrelament jurídic):
    -- positiva = comunitat assentada que s'ha naturalitzat; ~0 = arribada recent.
    case when supera_min_n
         then round(pct_nasc_estr_raw - pct_nac_estr_raw, 2)
         else null end                                              as bretxa_naturalitzacio,

    -- Context (ecològic): el municipi mai sol.
    pct_nacionalitat_estrangera_comarca,
    pct_nacionalitat_estrangera_catalunya,
    pct_nascuda_estranger_comarca,
    pct_nascuda_estranger_catalunya,

    -- ===== EVOLUCIÓ (deltes, sèrie 2021→) =====
    serie_any_inicial,
    serie_any_final,
    delta_pct_estrangera_5y,
    delta_pct_estrangera_finestra,
    delta_estrangers_finestra,

    -- ===== BANDERA DE CONFIANÇA (honestedat abans que precisió) =====
    -- baixa  = micromunicipi (poblacio < min_n: percentatges suprimits) O la font
    --          ja ha suprimit els estrangers (secret estadístic).
    -- mitjana= supera el llindar però amb pocs efectius estrangers (<25) → els
    --          percentatges ballen molt amb 1-2 persones.
    -- alta   = denominador i numerador prou grans.
    case
        when not supera_min_n or poblacio_nacionalitat_estrangera is null then 'baixa'
        when poblacio_nacionalitat_estrangera < 25 then 'mitjana'
        else 'alta'
    end                                                             as confianca_origen

from calc
order by ine5
