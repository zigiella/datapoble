-- Intermediate: consum elèctric del sector SERVEIS per càpita, mateix any que el
-- domèstic (var any_corroborador_electric = 2024). R-REFERENCIA (encàrrec de Bea,
-- 2026-07-31): «un polígon, una cimentera o una gran instal·lació poden convertir un
-- municipi en un fals paradís turístic estadístic» → el domèstic i els serveis, separats.
--
-- ⚠️ PREMISSA DEL BRIEF A MATISAR: el sector serveis JA S'INGERIA. `icaen_consum.py`
-- baixa el dataset SENCER (tots els sectors, per fidelitat a la font) des del primer dia;
-- el que faltava era exposar-lo a la capa transform, que filtrava `codi_sector = '7'`.
-- No hi ha connector nou ni cap crida de xarxa en aquest canvi.
--
-- SECTOR 6 = SERVEIS (mateix dataset ICAEN 8idm-becu que el domèstic).
--
-- COBERTURA i NULL HONEST (mesurat sobre la raw, 2024): 939 dels 947 municipis tenen
-- xifra; als altres 8 la font la suprimeix amb `observacions = 'Dada subjecta a secret
-- estadístic'`. Aquests 8 surten SENSE FILA (i per tant NULL al mart), mai un zero:
-- «no publicat» ≠ «no consumeix». Sèrie 2013-2024: entre 3 i 8 supressions per any.
--
-- ⛔ PER QUÈ NO S'EMET UN «TOTAL» (el brief el demanava «si surt gratis» — NO surt gratis).
-- El dataset no publica cap fila de total: només 6 sectors (1 PRIMARI, 3 INDUSTRIAL,
-- 4 CONSTRUCCIÓ, 5 TRANSPORT, 6 SERVEIS, 7 DOMÈSTIC). Sumar-los seria un MÍNIM OBSERVAT,
-- no un total: el 2024 només 46 dels 947 municipis tenen els 6 sectors amb valor —
-- als altres 901 falta almenys un sector, sigui per secret estadístic o perquè la font
-- directament no n'emet la fila. I el que falta sol ser l'INDUSTRIAL, que és justament
-- el sector que pot dominar el total d'un municipi. Un «total» així no seria una
-- frontera honesta sinó una xifra que sembla completa i no ho és → no es publica.
--
-- Denominador: el MATEIX de int_consum_electric_pc (padró de l'any del consum, Idescat
-- Cens anual INE) — perquè domèstic i serveis siguin sumables i comparables entre si.

with serv as (
    select ine5, any_consum, consum_kwh
    from {{ ref('stg_icaen_consum') }}
    where codi_sector = '6'
      and any_consum = {{ var('any_corroborador_electric') }}
      and consum_kwh is not null
),

pob as (
    select
        ine5,
        cast(any_referencia as integer)  as pob_any,
        cast(poblacio_total as double)   as poblacio
    from {{ ref('stg_demografia_estrangera_serie') }}
    where cast(any_referencia as integer) = {{ var('any_corroborador_electric') }}
      and poblacio_total is not null
)

select
    serv.ine5,
    serv.any_consum                                          as kwh_serveis_any,
    cast(pob.poblacio as integer)                            as poblacio_kwh_serveis,
    round(serv.consum_kwh / nullif(pob.poblacio, 0), 1)      as kwh_serveis_pc
from serv
join pob on serv.ine5 = pob.ine5
