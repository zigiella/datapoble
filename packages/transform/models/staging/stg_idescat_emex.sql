-- Staging Idescat EMEX: pivota la raw en format llarg (indicator x municipi) a
-- una fila per municipi amb una columna per indicador. La raw ja ve filtrada
-- als indicadors rellevants per a mart_municipi (vegeu packages/ingestion).

with src as (
    select *
    from read_parquet('{{ var("raw_root") }}/idescat_emex/idescat_emex.parquet')
),

pivoted as (
    select
        codi6,
        ine5,
        max(case when indicator = 'poblacio'        then try_cast(value_municipi as double) end) as poblacio,
        max(case when indicator = 'hab_total'       then try_cast(value_municipi as double) end) as hab_total,
        max(case when indicator = 'hab_principal'   then try_cast(value_municipi as double) end) as hab_principal,
        max(case when indicator = 'hab_noprincipal' then try_cast(value_municipi as double) end) as hab_noprincipal,
        max(case when indicator = 'pob_0_14'        then try_cast(value_municipi as double) end) as pob_0_14,
        max(case when indicator = 'pob_65_84'       then try_cast(value_municipi as double) end) as pob_65_84,
        max(case when indicator = 'pob_85_mes'      then try_cast(value_municipi as double) end) as pob_85_mes,
        -- Densitat de població (hab/km², EMEX f262): covariable estructural i indicador de mapa a tot
        -- CAT (F5). ≡ població/superfície de la geometria (r=0,9999 vs el Nivell C).
        max(case when indicator = 'densitat_hab_km2' then try_cast(value_municipi as double) end) as densitat_hab_km2
    from src
    group by codi6, ine5
)

select
    *,
    (coalesce(pob_65_84, 0) + coalesce(pob_85_mes, 0)) as pob_65_mes
from pivoted
