{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5) TO '"
              ~ var('marts_root') ~ "/mart_municipi.parquet' (FORMAT PARQUET)"
) }}
-- mart_municipi · 1 fila per municipi (clau: ine5).
-- Columnes segons el contracte (semantic/metrics.yml, table: mart_municipi).
-- Espina = Idescat EMEX (31 municipis del Berguedà). RTC i residus s'uneixen
-- per ine5. Lògica de ràtios reproduïda del prototip verificat.
--
-- Honest boundaries (NULL deliberat, documentat al PR):
--   · pct_icaen_EFG      -> requereix connector ICAEN (j6ii-t3w2), fora d'aquest PR. NULL.
--   · index_envelliment  -> status: planned al contracte, però el calculem (dades EMEX disponibles).
--
-- Població real estimada vs padró (INDICADOR ESTRELLA) — mètode de Talaia,
--   docs/poblacio-real-metode.md. Columnes poblacio_real_est / gap_abs / gap_pct /
--   poblacio_real_rel / confianca. presència = padró × kg_hab_any / BASE, amb BASE
--   PARAMETRITZABLE (vars base_residencial=410 absolut, base_comarcal=452 relatiu).
--   És INFERÈNCIA (no cens): es comunica com a rang + caveat (vegeu el contracte).
--   confianca marca 'baixa' sense por als micro-munis i on els senyals divergeixen.
--
-- IETR (Índex d'Exposició Turística-Residencial) — metodologia de Talaia:
--   min-max WINSORITZAT (p5/p95) sobre els 31 municipis, dues dimensions a pesos
--   iguals. Eix A (residencial): pct_noprincipal + hab_per_hab. Eix B (turístic):
--   rtc_per_1000hab + rtc_per_100hab_viv. Cada indicador es normalitza 0-100 contra
--   la seva distribució comarcal; IETR = 0.5*A + 0.5*B. Ancoratges verificats del
--   prototip: Castellar (08052) ≈ 89,4 (#1); Berga (08022) ≈ 0,3 (#31). Validació
--   externa: Spearman(IETR, kg_hab_any) = 0,87 (vegeu verify_marts.py).
--
-- FASE 1 (endurir el model SENSE fonts noves) — 3 derivats sobre dades que JA hi són
--   (CTEs sstats/zsig/zsig2/tipo/conf + columnes al final). Documentat a
--   docs/tipologia-municipal.md. Tot INFERÈNCIA; la tipologia és una LECTURA:
--     · IETR_stock / IETR_impact — desglossament de l'IETR (A_resid / B_turis, 0-100).
--     · tipologia — classificador de regles amb NOM (z-scores comarcals); 'indeterminat'
--       si ambigu. Verificat: Berga=capital_serveis · Castellar=excursio · Gósol=segona_residencia.
--     · confianca_score — 0-100 auditable que COMPLEMENTA la bandera confianca.
--   Sense raw (data/raw és .gitignore), el parquet es regenera amb la MATEIXA SQL via
--   packages/transform/derive_fase1.py (prova la identitat IETR=0.5*stock+0.5*impact).

with emex as (
    select * from {{ ref('stg_idescat_emex') }}
),

rtc as (
    select * from {{ ref('int_rtc_municipi') }}
),

residus as (
    select * from {{ ref('int_residus_latest') }}
),

-- Corroborador secundari de presència (docs/poblacio-real-metode.md §3): consum
-- elèctric domèstic per càpita del darrer any amb cobertura plena. Ve de l'staging
-- (no del mart elèctric) per evitar dependència circular — vegeu int_consum_electric_pc.
elec_pc as (
    select * from {{ ref('int_consum_electric_pc') }}
),

-- Senyal físic de la capa L3 (pressió turística/hostaleria): vidre kg/hab/any
-- del darrer any. Fracció del MATEIX dataset ARC que els residus.
vidre as (
    select * from {{ ref('int_residus_fraccions') }}
),

-- 2n proxy d'hostaleria de la capa L3 (complement del vidre): nombre d'establiments
-- de restauració per municipi (OSM via Overpass, assignats per punt-en-polígon a la
-- geometria real). El vidre mesura ACTIVITAT (ampolles); la restauració, CAPACITAT
-- instal·lada (stock). OSM infra-mapeja el rural → compte = MÍNIM observat, no cens.
restauracio as (
    select * from {{ ref('stg_restauracio_osm') }}
),

-- Senyal de CENTRALITAT FUNCIONAL (centre de serveis real): nombre d'establiments de
-- comerç quotidià (supermercat/forn/carnisseria/ferreteria…) i serveis essencials
-- (banc/farmàcia/correus/ajuntament…) per municipi (OSM via Overpass, assignats per
-- punt-en-polígon a la geometria real). És el senyal que redefineix capital_serveis:
-- un poble és capçalera per TENIR serveis (compte ABSOLUT), no per ser gran. OSM
-- infra-mapeja el rural → compte = MÍNIM observat, no cens.
serveis as (
    select * from {{ ref('stg_serveis_osm') }}
),

noms as (
    -- nom oficial: residus té els 31 amb nom net
    select distinct ine5, municipi from {{ ref('stg_residus') }}
),

-- ind: una fila per municipi amb els ràtios base (inputs de l'IETR i de les 3
-- capes). El senyal de vidre ve d'int_residus_fraccions, materialitzat com a TAULA
-- (no vista) perquè la vista sobre read_parquet+union_by_name resolia vidre_tones
-- com a NULL quan stg_residus es referenciava per múltiples camins en aquesta sentència.
ind as (
    select
        emex.ine5,
        emex.codi6,
        noms.municipi,
        cast(emex.poblacio as integer)                              as poblacio,
        cast(emex.hab_total as integer)                             as hab_total,
        cast(emex.hab_principal as integer)                         as hab_principal,
        cast(emex.hab_noprincipal as integer)                       as hab_noprincipal,
        round(emex.hab_noprincipal / nullif(emex.hab_total, 0) * 100, 2) as pct_noprincipal,
        round(emex.hab_total / nullif(emex.poblacio, 0), 3)             as hab_per_hab,
        round(emex.pob_65_mes / nullif(emex.pob_0_14, 0) * 100, 1)      as index_envelliment,
        coalesce(rtc.rtc_total, 0)                                  as rtc_total,
        coalesce(rtc.rtc_hut, 0)                                    as rtc_hut,
        round(coalesce(rtc.rtc_total, 0) / nullif(emex.poblacio, 0) * 1000, 2) as rtc_per_1000hab,
        round(coalesce(rtc.rtc_total, 0) / nullif(emex.hab_total, 0) * 100, 2) as rtc_per_100hab_viv,
        residus.kg_hab_any                                          as kg_hab_any,
        residus.residus_any                                         as kg_hab_any_year,
        -- Senyal L1 (pernocta): consum elèctric domèstic per càpita. kwh_hab és el
        -- nom de contracte; ve d'int_consum_electric_pc (kwh_domestic_pc).
        elec_pc.kwh_domestic_pc                                     as kwh_hab,
        -- Senyal L3 (turisme): vidre kg/hab/any. NULL→0 no s'aplica (cobertura 31/31).
        vidre.vidre_hab                                             as vidre_hab,
        vidre.vidre_any                                             as vidre_any,
        -- 2n proxy L3 (restauració OSM): compte d'establiments. Absència real → 0,
        -- no NULL (coherent amb rtc_total; un municipi sense locals mapejats és 0).
        coalesce(restauracio.restauracio_estab, 0)                  as restauracio_estab,
        -- Senyal de CENTRALITAT (serveis OSM): compte d'establiments de comerç i
        -- serveis essencials. Absència real → 0, no NULL (com restauracio_estab).
        coalesce(serveis.serveis_estab, 0)                          as serveis_estab
    from emex
    left join rtc         on emex.ine5 = rtc.ine5
    left join residus     on emex.ine5 = residus.ine5
    left join elec_pc     on emex.ine5 = elec_pc.ine5
    left join vidre       on emex.ine5 = vidre.ine5
    left join restauracio on emex.ine5 = restauracio.ine5
    left join serveis     on emex.ine5 = serveis.ine5
    left join noms        on emex.ine5 = noms.ine5
),

-- med: medianes comarcals dels senyals de presència (per a la bandera de
-- confiança, §6). Es calculen sobre els 31 municipis del pilot.
med as (
    select
        median(kg_hab_any)      as kg_hab_any_med,
        median(pct_noprincipal) as pct_noprincipal_med,
        median(kwh_hab)         as kwh_hab_med
    from ind
),

-- vstats: estadístics comarcals del vidre/hab per al z-score de la capa L3
-- (índex de pressió turística). Mitjana i desviació sobre els 31 municipis.
vstats as (
    select
        avg(vidre_hab)        as vidre_hab_avg,
        stddev_pop(vidre_hab) as vidre_hab_sd
    from ind
),

-- tur: capa L3 «pressió turística» (índex per ine5). z-score comarcal del
-- vidre/hab portat a 0–100 (z clampat a [-2,2]; 50 = mitjana comarcal). Es calcula
-- en una CTE pròpia (keyed per ine5, com ietr) i s'uneix per join — no per
-- cross join a la SELECT final — per robustesa de l'optimitzador.
tur as (
    select ind.ine5,
        round(
            (least(greatest((ind.vidre_hab - vstats.vidre_hab_avg)
                            / nullif(vstats.vidre_hab_sd, 0), -2), 2) + 2) / 4.0 * 100,
            1) as index_turisme
    from ind cross join vstats
),

-- q: percentils p5/p95 per a la winsorització (sobre els 31 municipis).
q as (
    select quantile_cont(pct_noprincipal,0.05) p5_np, quantile_cont(pct_noprincipal,0.95) p95_np,
           quantile_cont(hab_per_hab,0.05)     p5_hh, quantile_cont(hab_per_hab,0.95)     p95_hh,
           quantile_cont(rtc_per_1000hab,0.05) p5_r1, quantile_cont(rtc_per_1000hab,0.95) p95_r1,
           quantile_cont(rtc_per_100hab_viv,0.05) p5_r2, quantile_cont(rtc_per_100hab_viv,0.95) p95_r2
    from ind
),

-- norm: cada indicador winsoritzat a [p5,p95] i reescalat 0-100.
norm as (
    select ind.ine5,
      case when q.p95_np=q.p5_np then 0 else (least(greatest(ind.pct_noprincipal,q.p5_np),q.p95_np)-q.p5_np)/(q.p95_np-q.p5_np)*100 end as n_np,
      case when q.p95_hh=q.p5_hh then 0 else (least(greatest(ind.hab_per_hab,q.p5_hh),q.p95_hh)-q.p5_hh)/(q.p95_hh-q.p5_hh)*100 end as n_hh,
      case when q.p95_r1=q.p5_r1 then 0 else (least(greatest(ind.rtc_per_1000hab,q.p5_r1),q.p95_r1)-q.p5_r1)/(q.p95_r1-q.p5_r1)*100 end as n_r1,
      case when q.p95_r2=q.p5_r2 then 0 else (least(greatest(ind.rtc_per_100hab_viv,q.p5_r2),q.p95_r2)-q.p5_r2)/(q.p95_r2-q.p5_r2)*100 end as n_r2
    from ind cross join q
),

-- ietr: eix A (residencial) i B (turístic) a pesos iguals; IETR = 0.5*A + 0.5*B.
--   A_resid i B_turis ja són 0-100 per construcció (mitjana de dos indicadors
--   winsoritzats 0-100). Els exposem PER SEPARAT com IETR_stock / IETR_impact
--   (Fase 1): l'IETR barreja stock estructural i impacte realitzat; el desglossem.
ietr as (
    select ine5, (n_np+n_hh)/2.0 as A_resid, (n_r1+n_r2)/2.0 as B_turis,
           0.5*((n_np+n_hh)/2.0)+0.5*((n_r1+n_r2)/2.0) as IETR
    from norm
),

-- ========================================================================
-- FASE 1 (endurir el model SENSE fonts noves) · 3 derivats sobre dades que
-- JA hi són. Tot és INFERÈNCIA; la tipologia és una LECTURA (vegeu caveats al
-- contracte). Els z-scores són COMARCALS (sobre els 31 municipis del pilot);
-- a escala Catalunya seran per comarca, com les bases del model de 3 capes.
-- ========================================================================

-- sstats: mitjana i desviació poblacional (stddev_pop, ddof=0) dels senyals que
-- alimenten la tipologia i el confianca_score. 1 sola fila (cross join).
sstats as (
    select
        avg(gap_pernocta_pct)        as gap_avg,  stddev_pop(gap_pernocta_pct)        as gap_sd,
        avg(index_turisme)           as tur_avg,  stddev_pop(index_turisme)           as tur_sd,
        avg(pct_noprincipal)         as np_avg,   stddev_pop(pct_noprincipal)         as np_sd,
        avg(kg_hab_any)              as kg_avg,   stddev_pop(kg_hab_any)              as kg_sd,
        avg(kwh_hab)                 as kwh_avg,  stddev_pop(kwh_hab)                 as kwh_sd,
        avg(vidre_hab)               as vid_avg,  stddev_pop(vidre_hab)               as vid_sd,
        avg(restauracio_per_1000hab) as rest_avg, stddev_pop(restauracio_per_1000hab) as rest_sd,
        -- Centralitat de serveis: ln(serveis_estab+1) (compte ABSOLUT, distribució
        -- asimètrica com la població). El +1 evita ln(0) (cap muni té 0, però robust).
        avg(ln(serveis_estab + 1))   as lserv_avg, stddev_pop(ln(serveis_estab + 1))  as lserv_sd,
        avg(ln(poblacio))            as lpop_avg, stddev_pop(ln(poblacio))            as lpop_sd,
        avg(ln(carrega_total_est))   as lcar_avg, stddev_pop(ln(carrega_total_est))   as lcar_sd
    from ind
    join tur using (ine5)
),

-- zsig: z-scores comarcals per municipi. La població i la càrrega usen ln()
-- (distribució molt asimètrica: Berga 17.539 vs Sant Jaume 25). z_act = mitjana
-- dels 3 senyals d'ACTIVITAT de dia (residus, vidre, restauració): l'empremta
-- de l'excursionista. z_kg/z_kwh/z_np = els 3 senyals de PRESÈNCIA que han de
-- concordar per a una estimació fiable (entren al confianca_score).
zsig as (
    select i.ine5,
        (i.gap_pernocta_pct - s.gap_avg) / nullif(s.gap_sd,0)        as z_gap,
        (t.index_turisme    - s.tur_avg) / nullif(s.tur_sd,0)        as z_tur,
        (i.pct_noprincipal  - s.np_avg)  / nullif(s.np_sd,0)         as z_np,
        (i.kg_hab_any       - s.kg_avg)  / nullif(s.kg_sd,0)         as z_kg,
        (i.kwh_hab          - s.kwh_avg) / nullif(s.kwh_sd,0)        as z_kwh,
        (i.vidre_hab        - s.vid_avg) / nullif(s.vid_sd,0)        as z_vid,
        (i.restauracio_per_1000hab - s.rest_avg) / nullif(s.rest_sd,0) as z_rest,
        -- z_serv: centralitat de serveis (ln del compte absolut). Senyal nou que
        -- redefineix capital_serveis com a CENTRE de serveis real (no «muni gran»).
        (ln(i.serveis_estab + 1) - s.lserv_avg) / nullif(s.lserv_sd,0) as z_serv,
        (ln(i.poblacio)          - s.lpop_avg) / nullif(s.lpop_sd,0) as z_pop,
        (ln(i.carrega_total_est) - s.lcar_avg) / nullif(s.lcar_sd,0) as z_carr
    from ind i
    join tur t using (ine5)
    cross join sstats s
),

-- zsig2: deriva el senyal compost d'activitat (mitjana de residus/vidre/restauració).
zsig2 as (
    select *, (z_kg + z_vid + z_rest) / 3.0 as z_act from zsig
),

-- tipologia: classificador BASAT EN REGLES sobre z-scores comarcals (primera
-- regla que encaixa guanya). Documentat a docs/tipologia-municipal.md. Casos
-- coneguts verificats: Berga=capital_serveis · Castellar=excursio · Gósol/Saldes=
-- segona_residencia. On cap regla encaixa amb prou claredat → 'indeterminat'
-- (honestedat: no es força). NO és un judici de valor: és una LECTURA dels senyals.
tipo as (
    select ine5,
        case
            -- capital_serveis = CENTRE DE SERVEIS REAL (no «muni gran»): dotació de
            -- comerç i serveis essencials per sobre de la comarca (z_serv) + càrrega
            -- humana real que els sosté (z_carr) + turisme NO dominant (z_tur), amb un
            -- SÒL DE POBLACIÓ de 2000 hab. El senyal DEFINIDOR és z_serv (capçalera per
            -- TENIR serveis que serveixen els veïns, no per ser gran); el sòl evita que
            -- un micromuni de vall amb dotació alta i aïllada (p.ex. la Pobla de Lillet,
            -- 1106 hab) compti com a capçalera comarcal. A escala Catalunya el sòl i el
            -- z_serv es calibren PER COMARCA. Vegeu docs/tipologia-municipal.md.
            when poblacio >= 2000 and z_serv >= 0.8 and z_carr >= 0.5 and z_tur <= 0.3
                then 'capital_serveis'
            -- buit_administratiu: micromunicipi tranquil a tots els eixos (poc
            -- turisme, poca activitat, gap no alt) → padró estable, sense pressió.
            when z_pop <= -0.5 and z_tur <= -0.3 and z_act <= -0.2 and z_gap <= 0.2 then 'buit_administratiu'
            -- excursio: turisme alt + activitat de DIA alta (residus/vidre/
            -- restauració) però gap de pernocta NO alt → ve de dia, dorm menys
            -- (Castellar de n'Hug: residus/vidre alts, pernocta baixa).
            when z_tur >= 0.6 and z_act >= 0.4 and z_gap <= 0.4 then 'excursio'
            -- segona_residencia: gap de pernocta alt + (habitatge no principal alt
            -- O turisme alt) → s'omplen els llits buits (Gósol, Saldes).
            when z_gap >= 0.5 and (z_np >= 0.5 or z_tur >= 0.7) then 'segona_residencia'
            -- dormitori_invisible: gap de pernocta alt però turisme per sota de la
            -- mitjana → hi dormen sense constar, amb poca hostaleria.
            when z_gap >= 0.4 and z_tur <= 0.0 then 'dormitori_invisible'
            else 'indeterminat'
        end as tipologia
    from zsig2 join ind using (ine5)
),

-- conf: confianca_score 0-100 AUDITABLE (complementa, no substitueix, la bandera
-- `confianca`). Documentat a docs/tipologia-municipal.md. Quatre components:
--   (a) MIDA del denominador (40): ln-escalat entre 75 (micro) i 410 (vila plena).
--   (b) CONCORDANÇA dels 3 senyals de presència (35): com menys es dispersen els
--       z-scores de residus/elèctric/%no-principal, més fiable. spread>=3sd → 0.
--   (c) COBERTURA (15): fracció de senyals presents (no NULL).
--   (d) OUTLIER (−10): penalitza si algun senyal de presència té |z|>2 (soroll de
--       denominador / glitch). max(|z|)>=3sd → −10 ple.
-- La concordança és la que fa el score MÉS honest que la bandera binària: marca
-- els casos de senyals divergents (p. ex. Castellar, calefacció de llenya → residus
-- alts però elèctric baix) que un 'alta' binari amagaria.
conf as (
    select z.ine5,
        least(100.0, greatest(0.0,
            -- (a) mida del denominador
            40.0 * least(1.0, greatest(0.0,
                (ln(i.poblacio) - ln({{ var('poblacio_min_confianca') }}))
                / (ln({{ var('base_residencial') }}) - ln({{ var('poblacio_min_confianca') }}))))
            -- (b) concordança dels 3 senyals de presència (z_kg, z_kwh, z_np)
            + 35.0 * greatest(0.0, 1.0 -
                (greatest(z.z_kg, z.z_kwh, z.z_np) - least(z.z_kg, z.z_kwh, z.z_np)) / 3.0)
            -- (c) cobertura dels senyals
            + 15.0 * (
                (case when i.kg_hab_any is not null then 1 else 0 end
               + case when i.kwh_hab    is not null then 1 else 0 end
               + case when i.vidre_hab  is not null then 1 else 0 end
               + case when i.pct_noprincipal is not null then 1 else 0 end
               + case when i.poblacio   is not null then 1 else 0 end) / 5.0)
            -- (d) penalització d'outlier
            - 10.0 * least(1.0, greatest(0.0,
                (greatest(abs(z.z_kg), abs(z.z_kwh), abs(z.z_np)) - 2.0) / 1.0))
        )) as confianca_score,
        -- DIVERGÈNCIA DELS SENYALS (0-100): el component (b) exposat sol i llegible —
        -- el spread dels 3 z de presència. 0 = concordants · 100 = màxima discrepància.
        round(100.0 * least(1.0, greatest(0.0,
            (greatest(z.z_kg, z.z_kwh, z.z_np) - least(z.z_kg, z.z_kwh, z.z_np)) / 3.0)), 0) as divergencia_senyals
    from zsig2 z
    join ind i using (ine5)
)

select
    ind.ine5,
    ind.codi6,
    ind.municipi,
    '{{ var("comarca") }}'                                       as comarca,

    -- Demografia / vivenda (directe EMEX)
    ind.poblacio,
    ind.hab_total,
    ind.hab_principal,
    ind.hab_noprincipal,

    -- Derivats vivenda
    ind.pct_noprincipal,
    ind.hab_per_hab,

    -- Índex d'envelliment (65+ per 100 de 0-14)
    ind.index_envelliment,

    -- Turisme (RTC). Sense establiments -> 0, no NULL (absència real).
    ind.rtc_total,
    ind.rtc_hut,
    ind.rtc_per_1000hab,
    ind.rtc_per_100hab_viv,

    -- Pressió (residus, darrer any)
    ind.kg_hab_any,

    -- Senyals físics per càpita (inputs de les 3 capes; exposats per traçabilitat)
    ind.kwh_hab,                                                 -- elèctric domèstic kWh/hab (L1)
    ind.vidre_hab,                                               -- vidre kg/hab/any (L3)

    -- 2n proxy d'hostaleria de la capa L3 (CAPACITAT instal·lada, complement del
    -- vidre que mesura ACTIVITAT). Compte d'establiments de restauració (OSM) i la
    -- seva densitat per 1000 hab (numerador OSM / padró Idescat, com rtc_per_1000hab).
    -- És una MESURA (no inferència); OSM infra-mapeja el rural → MÍNIM, no cens.
    ind.restauracio_estab,                                       -- establiments (OSM, mínim)
    round(ind.restauracio_estab / nullif(ind.poblacio, 0) * 1000, 2)
                                                                as restauracio_per_1000hab,

    -- Senyal de CENTRALITAT FUNCIONAL (centre de serveis real): compte d'establiments
    -- de comerç i serveis essencials (OSM) i la seva densitat per 1000 hab. El COMPTE
    -- ABSOLUT és el senyal de capçalera (entra a la regla capital_serveis via z-score
    -- comarcal); la densitat és context. És una MESURA; OSM infra-mapeja el rural →
    -- MÍNIM, no cens (a escala Catalunya, calibrar per comarca).
    ind.serveis_estab,                                           -- establiments comerç+serveis (OSM, mínim)
    round(ind.serveis_estab / nullif(ind.poblacio, 0) * 1000, 2)
                                                                as serveis_per_1000hab,

    -- ===================================================================
    -- INDICADOR ESTRELLA — MODEL DE 3 CAPES (INFERÈNCIA, no cens). Mètode de
    -- Talaia, validat sobre dades. 3 senyals físics INDEPENDENTS, cadascun amb la
    -- seva base residencial (viles IETR<5, pop-pond). Tot es comunica com a RANG +
    -- caveat (semantic/metrics.yml). Lectura ECOLÒGICA (sobre el municipi).
    -- ===================================================================

    -- L1 · POBLACIÓ PERNOCTA («població invisible»): qui DORM al territori sense
    -- constar al padró. Senyal = elèctric domèstic / base_electric (1224 kWh/hab).
    -- És la nova SIGNATURA de població real (substitueix l'antic residus→població).
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kwh_hab', var('base_electric')) }} as integer)
                                                                as poblacio_pernocta_est,
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kwh_hab', var('base_electric')) }} - ind.poblacio as integer)
                                                                as gap_pernocta,
    -- gap_pernocta_pct en % 0-100 (× 100, igual que pct_noprincipal): convenció ÚNICA
    -- del contracte per a totes les mètriques `percent`. El frontend NO ho re-escala
    -- (cap component cuina l'escala): només hi marca el +/− de la desviació.
    round(
        ({{ estimacio_presencia('ind.poblacio', 'ind.kwh_hab', var('base_electric')) }} - ind.poblacio)
        / nullif(ind.poblacio, 0) * 100, 1)                     as gap_pernocta_pct,

    -- L2 · CÀRREGA PER RESIDUS: pressió que suggereixen els residus, inclosos els
    -- visitants de DIA (excursionistes). Senyal = residus / base_residencial (410). NO és
    -- població. ⚠️ NO és un sostre: pot quedar PER SOTA de la pernocta (L1) quan la
    -- recollida és atípica o la base està mal calibrada (passa a 16/31 munis del pilot).
    -- El nom «total» del passat era enganyós; per governar, usa carrega_funcional_est.
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }} as integer)
                                                                as carrega_total_est,

    -- DENOMINADOR FUNCIONAL: max(padró, pernocta L1, càrrega per residus L2). El sostre realista
    -- de càrrega humana — el «denominador per governar» (residus, aigua, neteja, serveis). El
    -- padró és el SÒL: mai per sota dels residents registrats (resol p.ex. Puig-reig, on L1 i L2
    -- queden sota el padró). Resol també la contradicció L2<L1.
    cast(greatest(
        ind.poblacio,
        {{ estimacio_presencia('ind.poblacio', 'ind.kwh_hab', var('base_electric')) }},
        {{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }}
    ) as integer)                                               as carrega_funcional_est,

    -- BASE-RATIOS: pressió ABSOLUTA vs base residencial (no z-score comarcal). >1 = per sobre
    -- del que genera una vila de vall poc turística; comparable entre comarques (a escala
    -- Catalunya, amb la base de la comarca corresponent).
    round(ind.kg_hab_any / {{ var('base_residencial') }}, 2)    as residu_base_ratio,
    round(ind.kwh_hab    / {{ var('base_electric') }}, 2)       as kwh_base_ratio,
    round(ind.vidre_hab  / {{ var('base_vidre') }}, 2)          as vidre_base_ratio,

    -- L3 · PRESSIÓ TURÍSTICA (hostaleria): intensitat d'activitat de visitants, via
    -- vidre/hab (ampolles de bar/restaurant). z-score comarcal del vidre_hab portat
    -- a 0–100 (50 = mitjana comarcal). NO és població. Calculat a la CTE `tur`.
    tur.index_turisme,

    -- Bandera de CONFIANÇA: honestedat abans que precisió falsa.
    --   baixa  = micro-muni (padró < poblacio_min_confianca, secret/soroll) O
    --            els senyals DIVERGEIXEN (residus alt però els altres baixos, o a
    --            l'inrevés) → l'estimació no és fiable.
    --   alta   = residus > mediana comarcal I almenys un altre senyal (elèctric/
    --            càpita O % no principal) també > mediana, I padró prou gran.
    --   mitjana= la resta.
    case
        when ind.poblacio < {{ var('poblacio_min_confianca') }} then 'baixa'
        when (ind.kg_hab_any > med.kg_hab_any_med
              and not (ind.pct_noprincipal > med.pct_noprincipal_med)
              and not (ind.kwh_hab > med.kwh_hab_med))
          or (not (ind.kg_hab_any > med.kg_hab_any_med)
              and ind.pct_noprincipal > med.pct_noprincipal_med
              and ind.kwh_hab > med.kwh_hab_med)
            then 'baixa'
        when ind.kg_hab_any > med.kg_hab_any_med
             and (ind.pct_noprincipal > med.pct_noprincipal_med
                  or ind.kwh_hab > med.kwh_hab_med)
             and ind.poblacio >= {{ var('poblacio_min_confianca') }}
            then 'alta'
        else 'mitjana'
    end                                                         as confianca,

    -- --- COMPATIBILITAT (model anterior d'una capa) ---------------------------
    -- Es CONSERVEN perquè cap consumidor del contracte quedi trencat. poblacio_real_est
    -- és ARA un ÀLIES de carrega_total_est (mateixa fórmula residus/410); reenquadrat:
    -- NO és «població» sinó càrrega total (vegeu L2). gap_abs/gap_pct deriven d'ell.
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }} as integer)
                                                                as poblacio_real_est,
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }} - ind.poblacio as integer)
                                                                as gap_abs,
    round(
        ({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_residencial')) }} - ind.poblacio)
        / nullif(ind.poblacio, 0) * 100, 1)                     as gap_pct,  -- % 0-100 (com gap_pernocta_pct)
    cast({{ estimacio_presencia('ind.poblacio', 'ind.kg_hab_any', var('base_comarcal')) }} as integer)
                                                                as poblacio_real_rel,

    -- Energia (ICAEN certificats) — connector pendent
    cast(null as double)                                        as pct_icaen_EFG,

    -- Índex IETR (metodologia Talaia, min-max winsoritzat p5/p95)
    round(ietr.IETR, 2)                                         as IETR,
    rank() over (order by ietr.IETR desc)                       as IETR_rank,

    -- ===================================================================
    -- FASE 1 · 3 derivats nous (endurir el model SENSE fonts noves).
    -- ===================================================================

    -- IETR DUAL: l'IETR és 0.5*A_resid + 0.5*B_turis (barreja stock + impacte).
    -- L'exposem desglossat. Tots dos ja són 0-100 per construcció (winsoritzats).
    --   IETR_stock  = component ESTRUCTURAL/resident (A_resid): habitatge no
    --                 principal + habitatges per habitant. "Exposició latent".
    --   IETR_impact = component de PRESSIÓ realitzada (B_turis): establiments
    --                 turístics per 1000 hab + per 100 habitatges. "Pressió viva".
    -- Identitat: round(0.5*IETR_stock + 0.5*IETR_impact, 2) == IETR.
    round(ietr.A_resid, 2)                                      as IETR_stock,
    round(ietr.B_turis, 2)                                      as IETR_impact,

    -- TIPOLOGIA: classificació amb NOM (lectura narrativa, no «més/menys»).
    -- Regles sobre z-scores comarcals (CTE tipo); 'indeterminat' on és ambigu.
    -- Verificat: Berga=capital_serveis · Castellar=excursio · Gósol=segona_residencia.
    tipo.tipologia,

    -- CONFIANCA_SCORE 0-100 auditable (CTE conf): complementa la bandera
    -- `confianca`. Components: mida del denominador + concordança dels senyals
    -- físics + cobertura − outlier. Label derivable amb talls documentats
    -- (<45 baixa · 45–65 mitjana · ≥65 alta) al contracte.
    round(conf.confianca_score, 1)                              as confianca_score,
    -- DIVERGÈNCIA dels senyals (0-100): el component de concordança, exposat sol perquè el
    -- bloc de confiança del web sigui auditable (0 concordants · 100 màxima discrepància).
    conf.divergencia_senyals                                    as divergencia_senyals,

    -- Traçabilitat dels talls temporals
    ind.kg_hab_any_year,
    ind.vidre_any

from ind
join ietr on ind.ine5 = ietr.ine5
join tur  on ind.ine5 = tur.ine5
join tipo on ind.ine5 = tipo.ine5
join conf on ind.ine5 = conf.ine5
cross join med
order by ind.ine5
