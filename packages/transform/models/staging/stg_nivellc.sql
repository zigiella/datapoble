-- Staging Nivell C: PONT entre el model de presència (Python, tools/nivellc_regressio.py) i el mart.
--
-- Llegeix data/territorial/nivellc_regressio.csv (versionat, ETCA-validat) amb, per a cada municipi
-- amb senyal elèctric + covariables (927):
--   · base_pred         = base elèctrica per càpita predita per covariables (densitat, renda, gas).
--                         És la base de presència UNIFICADA a tot Catalunya — substitueix la base
--                         fixa del pilot (1224). Provada al Berguedà (millora la validació ETCA, #161).
--   · tipus_territorial = grup de referència honest dels z-scores (iguals amb iguals: rural amb rural,
--                         litoral amb litoral) — reemplaça la comarca dels 31 a escala Catalunya.
--
-- El mart consumeix base_pred (capa L1 «població pernocta») i tipus_territorial (stats per tipus).
-- Vegeu docs/pla-catalunya-profund.md §F2. Cap número sense procedència; estimació ≠ cens (rang al web).

with src as (
    select *
    from read_csv_auto('{{ var("territorial_root") }}/nivellc_regressio.csv', header = true)
)

select
    lpad(cast(ine5 as varchar), 5, '0')  as ine5,
    tipus_territorial,
    cast(base_pred as double)            as base_pred
from src
where base_pred is not null
