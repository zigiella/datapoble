-- Intermediate: VIDRE per càpita del darrer any disponible per municipi.
-- (La sèrie completa de fraccions viu a staging; aquí ens quedem amb el tall
-- vigent = 2024, igual que int_residus_latest fa per a kg_hab_any.)
--
-- vidre_hab = vidre_tones * 1000 / poblacio  → kg de vidre per habitant i any.
-- Es divideix per la població del MATEIX dataset de residus (poblacio_residus),
-- coherent amb com l'ARC calcula kg_hab_any (no per EMEX), perquè vidre i kg_hab
-- comparteixin denominador i el ràtio vidre/residus sigui net.
--
-- És el senyal físic de la capa L3 (pressió turística/hostaleria): les ampolles
-- de bar i restaurant escalen amb els visitants, no amb els residents. Verificat
-- 2024: Gósol 149 kg/hab, Castellar de n'Hug 108 (micromunicipis turístics) vs
-- Berga 28, Puig-reig 28 (viles estables) → mediana comarcal ≈ 50. Cobertura
-- 31/31 sense forats (sobreviu al secret estadístic fins a Castellar, 164 hab).

-- Mirall EXACTE del patró d'int_residus_latest (select * + row_number) perquè la
-- resolució de columnes per nom sobre la vista stg_residus (read_parquet +
-- union_by_name) sigui estable: una llista explícita de columnes dins el ranked
-- feia que ine5/codi6 es resolguessin als valors crus del codi_municipi.
with ranked as (
    select
        *,
        row_number() over (partition by ine5 order by any_residus desc) as rn
    from {{ ref('stg_residus') }}
    where vidre_tones is not null
      and poblacio_residus is not null
      and poblacio_residus > 0
)

select
    ine5,
    codi6,
    any_residus                                          as vidre_any,
    vidre_tones,
    round(vidre_tones * 1000.0 / poblacio_residus, 1)    as vidre_hab
from ranked
where rn = 1
