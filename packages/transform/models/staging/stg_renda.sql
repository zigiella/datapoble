-- Staging renda: renda neta per persona (INE — Atlas de distribució de renda, ADRH 2023), de
-- `data/territorial/renda_municipi_cat.csv` (versionat). És indicador territorial publicable I
-- covariable de la base del model de presència (F5). Per muni (ine5); NULL on l'INE no en publica.

with src as (
    select *
    from read_csv_auto('{{ var("territorial_root") }}/renda_municipi_cat.csv', header = true)
)

select
    lpad(cast(ine5 as varchar), 5, '0')          as ine5,
    cast(renda_neta_persona_2023 as double)      as renda_neta_persona
from src
where renda_neta_persona_2023 is not null
