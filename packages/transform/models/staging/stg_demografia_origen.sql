-- Staging COMPOSICIÓ I ARRELAMENT (origen) — la FOTO del darrer any (EMEX 2025).
-- Pivota la raw en format llarg (municipi×nivell×indicador) a una fila per
-- municipi amb una columna per indicador, NOMÉS del nivell 'municipi' (la comarca
-- i Catalunya es guarden a part per al contrast — vegeu int_demografia_origen).
--
-- Lectura ECOLÒGICA: són recomptes municipals, mai individus. Els micromunicipis
-- poden tenir valors molt petits → el llindar mínim N i l'agrupació es gestionen
-- al mart (no aquí: fidelitat a la font).

with src as (
    select *
    from read_parquet('{{ var("raw_root") }}/demografia_origen/origen_snapshot.parquet')
    where nivell = 'municipi'
),

pivoted as (
    select
        codi6,
        ine5,
        max(year)                                                              as any_referencia,
        -- Per lloc de naixement
        max(case when indicator = 'nascuda_catalunya'     then value end)      as nascuda_catalunya,
        max(case when indicator = 'nascuda_resta_espanya' then value end)      as nascuda_resta_espanya,
        max(case when indicator = 'nascuda_estranger'     then value end)      as nascuda_estranger,
        max(case when indicator = 'pob_lloc_naix_total'   then value end)      as pob_lloc_naix_total,
        -- Per nacionalitat
        max(case when indicator = 'nac_espanyola'         then value end)      as nac_espanyola,
        max(case when indicator = 'nac_estrangera'        then value end)      as nac_estrangera,
        max(case when indicator = 'pob_nac_total'         then value end)      as pob_nac_total
    from src
    group by codi6, ine5
)

select * from pivoted
