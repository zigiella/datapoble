-- Intermediate: CONTEXT comarcal i de Catalunya (lectura ecològica). L'EMEX serveix el mateix
-- indicador per al municipi, la SEVA comarca i Catalunya al camp v. Aquí materialitzem els nivells
-- supramunicipals perquè el mart pugui dir «X% al municipi vs Y% a la SEVA comarca vs Z% a Catalunya».
-- Honestedat: el municipi no es llegeix mai sol.
--
-- Escala Catalunya (F5): el context de comarca és PER MUNI (cada `ine5` amb el valor de la seva
-- comarca, que ve a la seva pròpia resposta EMEX) — NO un sol escalar. El de Catalunya sí que és
-- únic (mateix valor a totes les respostes). El mart uneix `com` per `ine5` i fa broadcast de `cat`.

with com as (
    select
        ine5,
        max(case when indicator='nascuda_estranger'   then value end) as com_nascuda_estranger,
        max(case when indicator='pob_lloc_naix_total' then value end) as com_pob_lloc_naix_total,
        max(case when indicator='nac_estrangera'      then value end) as com_nac_estrangera,
        max(case when indicator='pob_nac_total'       then value end) as com_pob_nac_total
    from read_parquet('{{ var("raw_root") }}/demografia_origen/origen_snapshot.parquet')
    where nivell = 'comarca'
    group by ine5
),

cat as (
    select
        max(case when indicator='nascuda_estranger'   then value end) as cat_nascuda_estranger,
        max(case when indicator='pob_lloc_naix_total' then value end) as cat_pob_lloc_naix_total,
        max(case when indicator='nac_estrangera'      then value end) as cat_nac_estrangera,
        max(case when indicator='pob_nac_total'       then value end) as cat_pob_nac_total
    from read_parquet('{{ var("raw_root") }}/demografia_origen/origen_snapshot.parquet')
    where nivell = 'catalunya'
)

-- Una fila per muni (context de la seva comarca) + columnes de Catalunya per broadcast (un escalar).
-- El mart uneix per `ine5`.
select com.*, cat.*
from com cross join cat
