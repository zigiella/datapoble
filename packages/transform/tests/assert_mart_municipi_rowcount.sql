-- Escala Catalunya (F2): mart_municipi cobreix tots els municipis amb senyal EMEX
-- (n_municipis_expected = 947). Abans era 31 (pilot Berguedà).
select count(*) as n
from {{ ref('mart_municipi') }}
having count(*) != {{ var('n_municipis_expected') }}
