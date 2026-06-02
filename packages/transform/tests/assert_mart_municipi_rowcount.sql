-- El Berguedà té exactament 31 municipis. La mart ha de tenir 31 files.
-- (Escala a Catalunya = aquest test es parametritzaria a ~947.)
select count(*) as n
from {{ ref('mart_municipi') }}
having count(*) != {{ var('n_municipis_expected') }}
