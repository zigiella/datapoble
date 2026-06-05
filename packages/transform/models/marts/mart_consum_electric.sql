{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5, any_consum) TO '"
              ~ var('marts_root') ~ "/mart_consum_electric.parquet' (FORMAT PARQUET)"
) }}
-- mart_consum_electric · sèrie de consum elèctric DOMÈSTIC per municipi × any.
-- Format LLARG: 1 fila per (ine5, any_consum). Berguedà, 2013–2024 → 31×12 = 372.
--
-- Proxy de presència humana real per a l'indicador "població real vs padró"
-- (docs/poblacio-real-fonts.md §2-3). Font: ICAEN 8idm-becu, sector USOS
-- DOMÈSTICS (codi_sector='7'), l'únic que sobreviu al secret estadístic fins i
-- tot a Castellar de n'Hug (166 hab) → sèrie sencera sense forats per als 31.
--
-- Honest boundaries (deliberat, documentat al PR):
--   · Aquest mart NO normalitza (consum brut anual, fidel a la font). La
--     normalització del numerador de presència (kWh/habitatge vs kWh/població)
--     i la fórmula del *gap* població-real són síntesi de Talaia: es decidiran
--     abans d'incorporar una columna derivada a mart_municipi. Aquí només es
--     materialitza la sèrie traçable.
--   · codi6 ve de mart_municipi (espina canònica dels 31). Si un (ine5, any)
--     del domèstic no existís a la font, no apareixeria fila (cap inventat).
--     Verificat 2026-06-05: cobertura completa 31×12, zero forats al sector 7.

with dom as (
    -- Només sector USOS DOMÈSTICS, i descartem files sense valor (secret
    -- estadístic) — al sector 7 del Berguedà no n'hi ha cap, però som explícits.
    select
        ine5,
        municipi,
        comarca,
        any_consum,
        consum_kwh
    from {{ ref('stg_icaen_consum') }}
    where codi_sector = '7'
      and consum_kwh is not null
),

-- Espina canònica: codi6 + nom oficial des de mart_municipi (els 31 del pilot).
munis as (
    select ine5, codi6, municipi from {{ ref('mart_municipi') }}
)

select
    dom.ine5,
    munis.codi6,
    munis.municipi,
    dom.comarca,
    dom.any_consum,
    'USOS DOMESTICS'                                           as sector,
    round(dom.consum_kwh)                                      as consum_kwh_domestic
from dom
join munis on dom.ine5 = munis.ine5
order by dom.ine5, dom.any_consum
