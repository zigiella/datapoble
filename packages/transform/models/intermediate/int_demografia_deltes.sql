-- Intermediate: DELTES de població estrangera des de la sèrie municipal (2021→).
-- El «vèrtigen, no la foto»: quant ha canviat el % d'estrangers. Calculat DINS la
-- sèrie homogènia del Cens anual (2021→), MAI travessant la ruptura del 2021 (Padró).
--
-- Honestedat (innegociable):
--   · La sèrie homogènia disponible és 2021→2025 (5 punts del Cens anual; el Padró
--     pre-2021 NO s'usa: ruptura metodològica). Per tant NO hi ha un veritable
--     delta a 10 anys, i el "delta a 5 anys" és en realitat la SÈRIE SENCERA
--     disponible (≈5 anys, 4 intervals 2021→2025). Ho anomenem delta_pct_estrangera_5y
--     PERÒ només quan la finestra cobreix ≥4 anys (els 5 punts) — si no, NULL.
--     I exposem SEMPRE serie_any_inicial/final perquè se sàpiga sobre quins anys és.
--   · delta_..._10y = NULL estructural (no hi ha 10 anys homogenis). Declarat al
--     contracte com a 'planned' amb el caveat de la ruptura; columna no materialitzada.
--   · Si el municipi té secret estadístic (estrangers NULL) en algun extrem de la
--     finestra, el delta surt NULL (no s'inventa). Lectura ECOLÒGICA.

with serie as (
    select * from {{ ref('stg_demografia_estrangera_serie') }}
),

bounds as (
    -- Per municipi: primer i últim any amb % no nul (extrems de la finestra REAL).
    select
        ine5,
        min(any_referencia)                                       as any_min_disp,
        max(any_referencia)                                       as any_max_disp,
        min(any_referencia) filter (where pct_estrangera is not null) as any_min_pct,
        max(any_referencia) filter (where pct_estrangera is not null) as any_max_pct
    from serie
    group by ine5
),

picked as (
    select
        b.ine5,
        b.any_min_pct,
        b.any_max_pct,
        -- % al primer i últim any amb dada
        (select s.pct_estrangera from serie s
          where s.ine5 = b.ine5 and s.any_referencia = b.any_min_pct)         as pct_ini,
        (select s.pct_estrangera from serie s
          where s.ine5 = b.ine5 and s.any_referencia = b.any_max_pct)         as pct_fi,
        -- estrangers absoluts als extrems (per al delta absolut)
        (select s.estrangers_total from serie s
          where s.ine5 = b.ine5 and s.any_referencia = b.any_min_pct)         as estr_ini,
        (select s.estrangers_total from serie s
          where s.ine5 = b.ine5 and s.any_referencia = b.any_max_pct)         as estr_fi
    from bounds b
)

select
    ine5,
    any_min_pct                                                   as serie_any_inicial,
    any_max_pct                                                   as serie_any_final,
    (any_max_pct - any_min_pct)                                   as serie_n_anys,
    pct_ini                                                       as pct_estrangera_inicial,
    pct_fi                                                        as pct_estrangera_final,
    -- delta a 5 anys = delta sobre la sèrie sencera homogènia (2021→2025), que cobreix
    -- ≈5 anys. Només si la finestra té ≥4 anys de marge (els 5 punts del Cens anual);
    -- si no (sèrie escapçada per secret estadístic), NULL. NO travessa la ruptura 2021.
    case when (any_max_pct - any_min_pct) >= 4
         then round(pct_fi - pct_ini, 2) end                      as delta_pct_estrangera_5y,
    -- delta sobre la finestra REAL disponible (primer→últim any amb dada), sempre.
    round(pct_fi - pct_ini, 2)                                    as delta_pct_estrangera_finestra,
    -- delta absolut d'estrangers sobre la finestra (persones).
    cast(estr_fi - estr_ini as integer)                          as delta_estrangers_finestra
from picked
