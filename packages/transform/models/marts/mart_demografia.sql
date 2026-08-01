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
--   · LLINDAR MÍNIM N: RETIRAT (vot de Bea, 2026-08-01 — doctrina vinculant al capçal de
--     `semantic/metrics.yml`, bloc «LLINDAR MINIM N DE LA CAPA ORIGEN: RETIRAT»). Fins avui
--     els percentatges d'origen es deixaven NULL sota `demografia_min_n` habitants. Es
--     retira perquè la FONT no en calla res: 0 dels 947 municipis arriben sense
--     `nac_estrangera` i cap sense `pob_nac_total` (verificat sobre stg_demografia_origen,
--     2026-08-01), o sigui que suprimir la DIVISIÓ de dues xifres que Idescat publica
--     obertament no protegia ningú — només treia el municipi del rang. La var
--     `demografia_min_n` NO desapareix: segueix marcant `confianca_origen = 'baixa'`.
--     MARCAR NO ÉS SUPRIMIR.
--   · La precaució que sí que val —un percentatge sobre 44 persones és imprecís— és de
--     PRECISIÓ, no de privacitat, i té el seu lloc al caveat de micromunicipi (E13) i a
--     `confianca_origen`, no en un NULL.
--   · El secret estadístic de la font (estrangers '(..)' als micromunicipis) ja
--     arriba com a NULL i es propaga: on la font calli, seguim callant. Avui la foto
--     d'EMEX no en calla cap; la SÈRIE anual sí (36 dels 947 el 2025), i per això hi ha
--     municipis amb nivell publicat i sense delta — que és el que toca.
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
    -- nom + comarca oficials per muni (stg_residus cobreix tot CAT). 1 fila/muni (any_value evita
    -- el fan-out si el nom de comarca té variants entre anys).
    select ine5, any_value(municipi) as municipi, any_value(comarca) as comarca
    from {{ ref('stg_residus') }}
    group by ine5
),

calc as (
    select
        o.ine5,
        o.codi6,
        noms.municipi,
        noms.comarca                                                    as comarca,
        o.any_referencia                                                as any_referencia,

        -- Recomptes bruts (directe EMEX). Públics fins i tot als micromunicipis
        -- (un total no és secret; el que se suprimeix són els percentatges fins).
        cast(o.pob_nac_total as integer)                                as poblacio,
        cast(o.nac_estrangera as integer)                               as poblacio_nacionalitat_estrangera,
        cast(o.nascuda_estranger as integer)                            as poblacio_nascuda_estranger,
        cast(o.nascuda_catalunya as integer)                            as poblacio_nascuda_catalunya,
        cast(o.nascuda_resta_espanya as integer)                        as poblacio_nascuda_resta_espanya,

        -- Llindar mínim N: JA NO SUPRIMEIX (vot de Bea 2026-08-01). Sobreviu com a
        -- bandera de CONFIANÇA: sota `demografia_min_n` habitants el percentatge és
        -- imprecís (1 persona el mou >2 pp) i es marca `confianca_origen = 'baixa'`.
        (o.pob_nac_total >= {{ var('demografia_min_n') }})              as supera_min_n,

        -- ===== MÈTRIQUES NUCLI (percentatges) =====
        -- Es calculen i S'EMETEN SEMPRE que hi hagi numerador i denominador. Si la FONT
        -- calla el numerador, el NULL ve d'ella i es propaga (no és una decisió nostra).
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
    left join ctx       on o.ine5 = ctx.ine5   -- context de la SEVA comarca (per-muni) + CAT (broadcast)
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
    -- pct_nacionalitat_estrangera: % amb passaport no espanyol. Es publica per a TOTS els
    -- municipis que tinguin numerador i denominador (llindar retirat). Lectura ecològica.
    pct_nac_estr_raw                                                as pct_nacionalitat_estrangera,

    -- pct_nascuda_estranger: % nascuda fora d'Espanya. MILLOR proxy d'origen que la
    -- nacionalitat (no depèn de l'estatus jurídic, que la naturalització esborra).
    pct_nasc_estr_raw                                               as pct_nascuda_estranger,

    -- bretxa_naturalitzacio = pct_nascuda_estranger − pct_nacionalitat_estrangera.
    -- Mesura quanta gent nascuda fora JA TÉ passaport espanyol (arrelament jurídic):
    -- positiva = comunitat assentada que s'ha naturalitzat; ~0 = arribada recent.
    round(pct_nasc_estr_raw - pct_nac_estr_raw, 2)                  as bretxa_naturalitzacio,

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
    -- Amb el llindar retirat, aquesta bandera és l'ÚNIC senyal de precisió que queda a la
    -- capa d'origen: abans deia «a més, t'he suprimit el percentatge»; ara diu «te'l dono,
    -- i llegeix-lo amb aquesta precaució». Marcar no és suprimir.
    -- baixa  = micromunicipi (poblacio < min_n: 1 persona mou el % més de 2 pp) O la font
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
