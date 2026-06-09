-- Intermediate: CONTEXT comarcal i de Catalunya (lectura ecològica). L'EMEX serveix
-- el mateix indicador per al municipi, la seva comarca i Catalunya al camp v. Aquí
-- materialitzem els nivells supramunicipals com a ESCALARS (1 fila) perquè el mart
-- pugui dir «X% al municipi vs Y% a la comarca vs Z% a Catalunya». Honestedat: el
-- municipi no es llegeix mai sol.

with src as (
    select indicator, nivell, max(value) as value
    from read_parquet('{{ var("raw_root") }}/demografia_origen/origen_snapshot.parquet')
    where nivell in ('comarca', 'catalunya')
    group by indicator, nivell
)

select
    -- Comarca
    max(case when nivell='comarca'   and indicator='nascuda_estranger'   then value end) as com_nascuda_estranger,
    max(case when nivell='comarca'   and indicator='pob_lloc_naix_total' then value end) as com_pob_lloc_naix_total,
    max(case when nivell='comarca'   and indicator='nac_estrangera'      then value end) as com_nac_estrangera,
    max(case when nivell='comarca'   and indicator='pob_nac_total'       then value end) as com_pob_nac_total,
    -- Catalunya
    max(case when nivell='catalunya' and indicator='nascuda_estranger'   then value end) as cat_nascuda_estranger,
    max(case when nivell='catalunya' and indicator='pob_lloc_naix_total' then value end) as cat_pob_lloc_naix_total,
    max(case when nivell='catalunya' and indicator='nac_estrangera'      then value end) as cat_nac_estrangera,
    max(case when nivell='catalunya' and indicator='pob_nac_total'       then value end) as cat_pob_nac_total
from src
