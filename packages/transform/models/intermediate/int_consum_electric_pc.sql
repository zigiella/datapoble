-- Intermediate: consum elèctric DOMÈSTIC per càpita del darrer any amb cobertura
-- plena (var any_corroborador_electric = 2024). Corroborador SECUNDARI de
-- presència per a l'indicador "població real vs padró" (docs/poblacio-real-metode.md §3).
--
-- IMPORTANT (per què NO surt de mart_consum_electric):
--   mart_consum_electric ja DEPÈN de mart_municipi (n'agafa codi6+nom). Si el
--   corroborador de mart_municipi vingués del mart, tindríem una dependència
--   circular. Per això es deriva directament de l'staging (stg_icaen_consum,
--   sector 7) + la sèrie de padró d'Idescat.
--
-- 🔴 BUG DE VINTAGE TANCAT (R-REFERENCIA, 2026-07-31 · el va caçar la recerca de Bea).
-- Fins avui el denominador era `stg_idescat_emex.poblacio`, que és el padró de l'ANY
-- VIGENT (2025) mentre el numerador és el consum de 2024: la mètrica barrejava dos
-- vintages sense declarar-ho (el contracte deia `date: "2024"`, a seques). Efecte
-- MESURAT sobre els 947: el ponderat de Catalunya sortia 1.234,86 kWh/hab quan la
-- xifra que dona la font dividida pel padró del seu propi any és 1.252,10 — un 1,40%
-- per sota (el padró de 2025, 8.124.126, és un 1,3966% més gran que el de 2024,
-- 8.012.231). I NO és un desplaçament uniforme: municipi a municipi l'error va de
-- −11,9% a +12,2% (301 municipis anaven en direcció CONTRÀRIA perquè el seu padró
-- havia baixat), o sigui que també movia els rangs comarcals.
--
-- DENOMINADOR: `stg_demografia_estrangera_serie.poblacio_total` de l'ANY DEL CONSUM.
--   · Font: Idescat, Cens anual de població de l'INE — LA MATEIXA FAMÍLIA que el padró
--     que publiquem a la fitxa (EMEX f321), no un canvi de font: la sèrie 2025 coincideix
--     municipi a municipi (947/947) amb l'EMEX que fèiem servir fins ara.
--   · Sèrie 2021→ (ruptura metodològica documentada a docs/demografia-origen-fonts.md).
--     Amb any_corroborador_electric = 2024 hi ha cobertura 947/947.
--   · Contrastat contra una TERCERA font independent: la població que l'ARC publica al
--     seu propi dataset de residus (stg_residus.poblacio_residus) és IDÈNTICA a aquesta
--     als 947 municipis per a 2023 i 2024 (diferència màxima = 0). Els agregats casen
--     amb les xifres oficials: 8.012.231 (2024) i 8.124.126 (2025).
--
-- El denominador s'EMET (poblacio_kwh) i també l'any (kwh_any): sense el denominador
-- una referència ponderada no es pot recalcular ni auditar (C6 §8.1, procedència).
-- La guarda `assert_consum_electric_vintage` peta si els dos anys divergeixen o
-- si la cobertura no és plena — un forat silenciós aquí tornaria a moure tots els 947.
--
-- Caveat metodològic (§3): l'elèctric està confós per la calefacció (a la
-- muntanya es crema llenya/gas → consum baix malgrat molta presència, p. ex.
-- Castellar de n'Hug). Per això NO es pondera igual que els residus: només puja
-- la CONFIANÇA quan coincideix amb el senyal primari, mai el substitueix.

with dom as (
    -- sector 7 = USOS DOMÈSTICS (l'únic que sobreviu al secret estadístic als
    -- micromunicipis); descartem NULLs per coherència (al sector 7 no n'hi ha).
    select ine5, any_consum, consum_kwh
    from {{ ref('stg_icaen_consum') }}
    where codi_sector = '7'
      and any_consum = {{ var('any_corroborador_electric') }}
      and consum_kwh is not null
),

pob as (
    -- Padró de l'ANY DEL CONSUM (no el vigent). INNER JOIN deliberat: si un any no
    -- tingués sèrie de padró, la fila no surt i la guarda ho fa caure — mai un
    -- per càpita calculat amb el padró d'un altre any.
    select
        ine5,
        cast(any_referencia as integer)  as pob_any,
        cast(poblacio_total as double)   as poblacio
    from {{ ref('stg_demografia_estrangera_serie') }}
    where cast(any_referencia as integer) = {{ var('any_corroborador_electric') }}
      and poblacio_total is not null
)

select
    dom.ine5,
    dom.any_consum                                          as kwh_any,
    pob.pob_any                                             as poblacio_kwh_any,
    cast(pob.poblacio as integer)                           as poblacio_kwh,
    round(dom.consum_kwh / nullif(pob.poblacio, 0), 1)      as kwh_domestic_pc
from dom
join pob on dom.ine5 = pob.ine5
