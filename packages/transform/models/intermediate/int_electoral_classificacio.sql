-- Intermediate: classifica cada candidatura en blocs polítics (no exclusius).
-- Regles (metodologia Talaia, vegeu bitàcora + _marts.yml). Les sigles ja venen
-- normalitzades (sigla_norm) des de stg_electoral.
--
--   EXTREMA DRETA   = VOX, ALIANÇA CATALANA (ALIANCACAT), PXC, ESPANYA2000, FE/FET.
--   INDEPENDENTISTA = ERC, JUNTS (CATJUNTS/JXCAT/CIU/CDC/PDECAT), CUP*, ALIANCACAT,
--                     ALHORA, SI, FNC.   (Aliança Catalana compta a XD i a INDEP.)
--   ESQUERRA        = PSC, ERC, CUP*, COMUNS* (ECP/PODEM/CATCOMU), PCTC.
--
-- Nota: blocs NO exclusius (ERC i CUP són indep+esquerra; ALIANCACAT és XD+indep).
-- Lectura ecològica (no individual).

with base as (
    select * from {{ ref('stg_electoral') }}
)

select
    id_eleccio,
    nom_eleccio,
    ine5,
    territori_codi,
    territori_nom,
    candidatura_sigles,
    sigla_norm,
    vots,

    (sigla_norm in ('VOX','ALIANCACAT','ALIANCACATALANA','PXC','ESPANYA2000','FE','FET'))
        as is_extrema_dreta,

    (
        sigla_norm in (
            'ERC','CATJUNTS','JXCAT','JUNTS','CIU','CDC','PDECAT',
            'ALIANCACAT','ALIANCACATALANA','ALHORA','SI','FNC'
        )
        or sigla_norm like 'CUP%'
    ) as is_indep,

    (
        sigla_norm in ('PSC','ERC','PCTC')
        or sigla_norm like 'CUP%'
        or sigla_norm like 'COMUNS%'
        or sigla_norm like 'ECP%'
        or sigla_norm like 'PODEM%'
        or sigla_norm like 'CATCOMU%'
    ) as is_esquerra

from base
