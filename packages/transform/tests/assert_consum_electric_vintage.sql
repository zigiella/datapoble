-- GUARDA DEL VINTAGE ELÈCTRIC (R-REFERENCIA, 2026-07-31). Neix el mateix dia que el fix,
-- perquè el bug que tanca era invisible: `kwh_hab` dividia el consum de 2024 pel padró de
-- 2025 i cap test ho mirava. Falla (retorna files) si:
--   · l'any del consum i l'any del padró del denominador divergeixen (la barreja torna), o
--   · la cobertura del domèstic deixa de ser plena (947): el sector 7 no té secret
--     estadístic i si un dia en tingués, ho hem de saber per una guarda, no per un forat.
--   · el padró emprat no és el declarat per la var any_corroborador_electric.
-- El sector SERVEIS NO entra en el recompte: allà el secret estadístic sí que mossega
-- (8 municipis el 2024) i el NULL hi és honest, no un error.

with g as (
    select
        count(*)                                                as n,
        count(distinct kwh_any)                                 as n_anys,
        sum(case when kwh_any <> poblacio_kwh_any then 1 else 0 end) as barreja,
        max(kwh_any)                                            as any_consum,
        sum(case when poblacio_kwh is null or poblacio_kwh <= 0 then 1 else 0 end) as sense_denominador
    from {{ ref('int_consum_electric_pc') }}
)

select *
from g
where n != {{ var('n_municipis_expected') }}
   or n_anys != 1
   or barreja != 0
   or sense_denominador != 0
   or any_consum != {{ var('any_corroborador_electric') }}
