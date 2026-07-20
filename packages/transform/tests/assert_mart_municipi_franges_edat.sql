-- FRANGES D'EDAT (E12) · les quatre franges han de PARTIR la població, no aproximar-la.
--
-- La franja intermèdia (15-64) NO ve d'EMEX: es deriva per resta. L'encàrrec de Bea és
-- explícit — «deriva-la NOMÉS si quadra; si no quadra, digue-ho i no la publiquis». Aquest
-- test és la guarda d'aquella regla, i falla el build si es trenca:
--
--   (a) on pob_15_64 ES PUBLICA (no NULL), la partició ha de ser EXACTA:
--       0-14 + 15-64 + 65-84 + 85+ = poblacio. Zero tolerància: són recomptes sencers
--       de la mateixa taula EMEX i el mateix vintage; qualsevol residu voldria dir que
--       hem barrejat anys o fonts, i llavors la xifra no s'ha de publicar.
--   (b) pob_15_64 només pot ser NULL si HI HA MOTIU: algun component NULL o resta
--       negativa. Un NULL sense motiu seria un forat silenciós.
--   (c) pob_65_mes ha de ser exactament 65-84 + 85+ (el rollup que menja index_envelliment).
--
-- Estat verificat el 2026-07-20 sobre els 947: quadra a tot arreu (cap NULL, cap negatiu,
-- mínim de la intermèdia = 13) i la suma dels 947 casa amb el total de Catalunya que
-- serveix la mateixa API. Si un dia deixa de quadrar, aquest test ho crida.

select
    ine5,
    poblacio,
    pob_0_14,
    pob_15_64,
    pob_65_84,
    pob_85_mes,
    pob_65_mes
from {{ ref('mart_municipi') }}
where
    -- (a) partició exacta quan es publica
    (pob_15_64 is not null
     and coalesce(pob_0_14, -1) + pob_15_64 + coalesce(pob_65_84, -1) + coalesce(pob_85_mes, -1)
         != poblacio)
    -- (b) NULL només amb motiu
    or (pob_15_64 is null
        and poblacio is not null and pob_0_14 is not null
        and pob_65_84 is not null and pob_85_mes is not null
        and poblacio - pob_0_14 - pob_65_84 - pob_85_mes >= 0)
    -- (c) rollup 65+ coherent
    or (pob_65_mes is not null
        and pob_65_mes != coalesce(pob_65_84, 0) + coalesce(pob_85_mes, 0))
