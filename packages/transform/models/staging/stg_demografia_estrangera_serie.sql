-- Staging SÈRIE de població estrangera (Idescat "Població estrangera", Cens anual
-- INE, 2021→). Una fila per municipi × any. Font de veritat dels DELTES.
--
-- RUPTURA metodològica respectada: la raw NOMÉS porta 2021→ (Cens anual), no el
-- Padró 2000-2020 (canvi de font el 2021). Vegeu docs/demografia-origen-fonts.md.
-- El secret estadístic dels micromunicipis ve com a NULL des de la font (els
-- estrangers de pobles diminuts surten '(..)') → es conserva NULL (honestedat).

select
    codi6,
    ine5,
    cast(year as integer)                 as any_referencia,
    poblacio_total,
    estrangers_total,
    pct_estrangera,                        -- % estrangers sobre població (0-100, decimal)
    estrangers_var_abs,                    -- variació absoluta interanual
    estrangers_var_rel                     -- variació relativa interanual (%)
from read_parquet('{{ var("raw_root") }}/demografia_origen/estrangera_serie.parquet')
