{{ config(
    post_hook="COPY (SELECT * FROM {{ this }} ORDER BY ine5, metric, comparacio) TO '"
              ~ var('marts_root') ~ "/mart_tendencia.parquet' (FORMAT PARQUET)"
) }}
-- mart_tendencia · la TENDÈNCIA amb el seu període declarat (E6 de les esmenes de Bea).
-- Format LLARG: 1 fila per (ine5, metric, comparacio).
--
-- LA REGLA (§2 de docs/ajuntaments/tauler-v2-esmenes-bea.md, vinculant):
--   «Cap targeta amb fletxa sense període.» Només es mostra tendència on hi ha SÈRIE
--   REAL, i tota tendència diu CONTRA QUIN PERÍODE compara. Per això aquest mart no té
--   cap fila muda: TOTA mètrica del tauler hi surt, i la que no té sèrie hi surt amb
--   estat = 'sense_serie' + el motiu escrit (`motiu_ca`/`motiu_es`). El front no pot
--   confondre un NULL amb un zero perquè el NULL sempre ve acompanyat de l'estat i del motiu.
--
-- QUI TÉ SÈRIE (i qui no) — l'estat del terreny, no una aspiració:
--   · atur_registrat — SEPE, mensual 2006→. DUES comparacions, no una: el mes anterior
--     i el MATEIX MES DE L'ANY ANTERIOR. L'atur és estacional (a la Pobla de Lillet,
--     2026-06: +4 contra el mes anterior però −3 contra el mateix mes de 2025 — la
--     mateixa xifra puja o baixa segons contra què la miris). Ensenyar-ne només una
--     seria triar la narrativa; s'emeten totes dues i que el lector les vegi.
--   · pct_nacionalitat_estrangera / poblacio_nacionalitat_estrangera — Cens anual,
--     finestra 2021→2025 ja calculada a mart_demografia (no es recalcula aquí). SÈRIE
--     PARCIAL: la font reserva la sèrie a 16 dels 947 (tots els anys) i aquests surten
--     'sense_serie' AMB MOTIU, no absents (vegeu `sense_origen_serie`). Són les úniques
--     dues mètriques del mart amb els DOS estats alhora, i és honest que ho siguin: la
--     cobertura de la font varia per municipi i no ho pot decidir una llista nostra.
--   · TOTA LA RESTA (població, franges d'edat, renda, habitatge, residus, energia, RTC,
--     comerç i restauració) — 'sense_serie'. Població i franges hi són perquè EMEX **no
--     serveix sèrie**: la seva API només té els filtres id/i/tipus, cap de temporal
--     (verificat en viu contra l'API i contra la documentació oficial, 2026-07-20; els
--     paràmetres temporals que es provin s'ignoren en silenci i la resposta torna sempre
--     el darrer període). No és un pendent d'ingesta: és un límit de la font, i es diu.
--
-- D10 · EL CONJUNT ES COMPROVA, NO ES CONFIA. Aquesta llista segueix escrita a mà perquè
-- el MOTIU de cada absència és text editorial: no es pot derivar de res. El que sí que es
-- deriva és la PERTINENÇA: `verify_tendencia.py` llegeix quines mètriques pinta el tauler
-- de la seva autoritat (`packages/web/src/lib/govern/kpis.js`, via `tools/tauler_kpis.py`)
-- i cau si alguna no té fila aquí. Va caldre perquè `serveis_estab` i `restauracio_estab`
-- es pintaven al tauler i NO eren en aquest mart — ni com a 'sense_serie'. Una fila que
-- falta és invisible: el lector no distingeix «no ha canviat» de «no ho sabem».
--
-- D10 · MOTIU EN CA I ES. El motiu és DADA (el front el pinta literal i no el pot
-- traduir sense inventar-se'l), així que surt del mart en els dos idiomes, com `label` i
-- `definicio` al contracte semàntic. Les columnes són `motiu_ca` i `motiu_es`: no hi ha
-- cap `motiu` a seques, precisament perquè no es pugui tornar a colar un idioma implícit.
--
-- V3 · EL MOTIU ES DIU EN LLENGUA DE CIUTADÀ (redisseny v3 §5, vot de Bea 2026-07-29).
-- El lector de la targeta és un alcalde o un veí, no un enginyer: «cap sèrie per API»,
-- «pendent d'ingesta» o «filtres id/i/tipus» són argot que no l'informa. Els literals
-- d'aquest model estan escrits en pla, PERÒ el motiu honest és EXACTAMENT el mateix i
-- la distinció entre casos es continua veient, perquè no són el mateix cas:
--   · LÍMIT DE FONT (EMEX: població, franges, envelliment, lloc de naixement) — la font
--     oficial només publica la dada vigent; l'evolució no la podem ensenyar NOSALTRES
--     ni ningú que en begui. No és culpa nostra i no és arreglable ingerint més.
--   · PENDENT NOSTRE (renda INE, residus/vidre ARC, elèctric ICAEN) — la font SÍ que té
--     la sèrie; som nosaltres que encara no la carreguem. Es diu, perquè és un deute
--     nostre i no un límit del món.
--   · DADA DECENNAL (cens d'habitatge 2021) — no hi ha cap edició anterior comparable.
--   · REGISTRE VIU (RTC) — es llegeix com a foto del dia; no en conservem talls.
--   · MAPA QUE ES COMPLETA (OSM) — una pujada podria ser mapatge nou, no obertures
--     reals: ni guardant talls la diferència es podria llegir com a canvi al terreny.
-- El DETALL TÈCNIC de cada límit (quins filtres té l'API d'EMEX, quan es va verificar
-- en viu, quins camps f69/f72/f73) NO s'ha perdut: viu als comentaris d'aquest model,
-- al contracte semàntic i a /metodologia — que és on el busca qui el necessita.
--
-- DOCTRINA DEL «<5» A LA RESTA (C1 §1.1): quan un dels dos mesos ve emmascarat, la
-- diferència NO és un número, és un INTERVAL. Llavors delta = NULL i s'emeten
-- delta_min = actual_min − anterior_max i delta_max = actual_max − anterior_min, amb
-- delta_emmascarat = true. Restar l'emmascarat com si fos zero seria inventar-se el signe.

with pols as (
    select * from {{ ref('mart_pols_mensual') }}
),

-- Darrer mes disponible a la font (global, no per municipi: el SEPE publica tot el
-- padró de cop; un municipi que falti aquell mes simplement no tindrà fila).
darrer_mes as (
    select max(date) as mes from pols
),

-- Els tres punts que necessiten les dues comparacions de l'atur: el darrer mes, el mes
-- immediatament anterior i el mateix mes de l'any anterior. Es calculen amb aritmètica
-- de dates sobre "YYYY-MM" (strptime → interval) per no dependre de la continuïtat de
-- la sèrie: si el punt de comparació no existeix a la font, el join no lliga i la fila
-- surt sense tendència (honest) en comptes d'agafar «el punt anterior que hi hagi».
periodes as (
    select
        mes                                                                  as mes_actual,
        strftime(strptime(mes, '%Y-%m') - interval 1 month,  '%Y-%m')        as mes_anterior,
        strftime(strptime(mes, '%Y-%m') - interval 12 month, '%Y-%m')        as mes_any_anterior
    from darrer_mes
),

atur_actual as (
    select p.* from pols p, periodes pe where p.date = pe.mes_actual
),

atur_prev_mes as (
    select p.ine5, p.date, p.atur_registrat, p.atur_registrat_min, p.atur_registrat_max, p.atur_emmascarat
    from pols p, periodes pe where p.date = pe.mes_anterior
),

atur_prev_any as (
    select p.ine5, p.date, p.atur_registrat, p.atur_registrat_min, p.atur_registrat_max, p.atur_emmascarat
    from pols p, periodes pe where p.date = pe.mes_any_anterior
),

-- Les dues comparacions de l'atur, en format llarg. `comparacio` diu quina és; els camps
-- de període diuen contra QUÈ (el literal "YYYY-MM" que el front pot pintar tal qual).
atur_tend as (
    select
        a.ine5, a.codi6, a.municipi,
        'atur_registrat'                              as metric,
        'mes_anterior'                                as comparacio,
        a.date                                        as periode_actual,
        b.date                                        as periode_anterior,
        a.atur_registrat                              as valor_actual,
        b.atur_registrat                              as valor_anterior,
        (a.atur_emmascarat or b.atur_emmascarat)      as delta_emmascarat,
        a.atur_registrat_min, a.atur_registrat_max,
        b.atur_registrat_min as prev_min, b.atur_registrat_max as prev_max
    from atur_actual a
    join atur_prev_mes b on a.ine5 = b.ine5

    union all

    select
        a.ine5, a.codi6, a.municipi,
        'atur_registrat'                              as metric,
        'mateix_mes_any_anterior'                     as comparacio,
        a.date                                        as periode_actual,
        b.date                                        as periode_anterior,
        a.atur_registrat                              as valor_actual,
        b.atur_registrat                              as valor_anterior,
        (a.atur_emmascarat or b.atur_emmascarat)      as delta_emmascarat,
        a.atur_registrat_min, a.atur_registrat_max,
        b.atur_registrat_min as prev_min, b.atur_registrat_max as prev_max
    from atur_actual a
    join atur_prev_any b on a.ine5 = b.ine5
),

atur_out as (
    select
        ine5, codi6, municipi, metric, comparacio,
        'amb_serie'                                          as estat,
        cast(null as varchar)                                as motiu_ca,
        cast(null as varchar)                                as motiu_es,
        periode_actual, periode_anterior,
        cast(valor_actual as double)                         as valor_actual,
        cast(valor_anterior as double)                       as valor_anterior,
        -- delta exacte NOMÉS si cap dels dos punts ve emmascarat.
        case when delta_emmascarat then null
             else cast(valor_actual - valor_anterior as double) end   as delta,
        -- interval del delta: sempre emès (amb emmascarament o sense; sense, min=max=delta).
        cast(atur_registrat_min - prev_max as double)        as delta_min,
        cast(atur_registrat_max - prev_min as double)        as delta_max,
        delta_emmascarat,
        'persones'                                           as unitat_delta
    from atur_tend
),

-- ORIGEN · la finestra del Cens anual, JA calculada a mart_demografia (2021→2025).
-- No es recalcula: es re-exposa amb el període explícit al costat, que és el que
-- faltava perquè el tauler pogués pintar la fletxa sense mentir sobre el període.
origen as (
    select
        d.ine5,
        m.codi6,
        d.municipi,
        d.serie_any_inicial,
        d.serie_any_final,
        d.delta_pct_estrangera_finestra,
        d.delta_estrangers_finestra,
        d.pct_nacionalitat_estrangera,
        d.poblacio_nacionalitat_estrangera
    from {{ ref('mart_demografia') }} d
    join {{ ref('mart_municipi') }} m on d.ine5 = m.ine5
),

origen_out as (
    select
        ine5, codi6, municipi,
        'pct_nacionalitat_estrangera'                        as metric,
        'finestra_anual'                                     as comparacio,
        'amb_serie'                                          as estat,
        cast(null as varchar)                                as motiu_ca,
        cast(null as varchar)                                as motiu_es,
        cast(serie_any_final   as varchar)                   as periode_actual,
        cast(serie_any_inicial as varchar)                   as periode_anterior,
        cast(pct_nacionalitat_estrangera as double)          as valor_actual,
        -- valor del període inicial = valor actual − delta (el delta és el que mana:
        -- ve de la sèrie del connector, no d'aquí).
        case when pct_nacionalitat_estrangera is null or delta_pct_estrangera_finestra is null
             then null
             else round(cast(pct_nacionalitat_estrangera - delta_pct_estrangera_finestra as double), 2)
        end                                                  as valor_anterior,
        cast(delta_pct_estrangera_finestra as double)        as delta,
        cast(delta_pct_estrangera_finestra as double)        as delta_min,
        cast(delta_pct_estrangera_finestra as double)        as delta_max,
        false                                                as delta_emmascarat,
        'punts_percentuals'                                  as unitat_delta
    from origen
    -- els municipis SENSE finestra (la font els reserva la sèrie) NO desapareixen: surten
    -- per `sense_origen_serie`, com a 'sense_serie' amb el motiu escrit.
    where serie_any_inicial is not null and serie_any_final is not null

    union all

    select
        ine5, codi6, municipi,
        'poblacio_nacionalitat_estrangera'                   as metric,
        'finestra_anual'                                     as comparacio,
        'amb_serie'                                          as estat,
        cast(null as varchar)                                as motiu_ca,
        cast(null as varchar)                                as motiu_es,
        cast(serie_any_final   as varchar)                   as periode_actual,
        cast(serie_any_inicial as varchar)                   as periode_anterior,
        cast(poblacio_nacionalitat_estrangera as double)     as valor_actual,
        case when poblacio_nacionalitat_estrangera is null or delta_estrangers_finestra is null
             then null
             else cast(poblacio_nacionalitat_estrangera - delta_estrangers_finestra as double)
        end                                                  as valor_anterior,
        cast(delta_estrangers_finestra as double)            as delta,
        cast(delta_estrangers_finestra as double)            as delta_min,
        cast(delta_estrangers_finestra as double)            as delta_max,
        false                                                as delta_emmascarat,
        'persones'                                           as unitat_delta
    from origen
    -- els municipis SENSE finestra (la font els reserva la sèrie) NO desapareixen: surten
    -- per `sense_origen_serie`, com a 'sense_serie' amb el motiu escrit.
    where serie_any_inicial is not null and serie_any_final is not null
),

-- SENSE SÈRIE · files EXPLÍCITES, no absències. Cada mètrica del tauler que avui és una
-- sola foto surt aquí amb el seu motiu escrit, perquè la targeta pugui dir «sense sèrie»
-- en comptes de callar (i perquè un NULL mut no es pugui llegir com un zero).
sense as (
    select m.ine5, m.codi6, m.municipi, s.metric, s.motiu_ca, s.motiu_es, s.valor
    from {{ ref('mart_municipi') }} m
    cross join lateral (
        values
            -- LÍMIT DE FONT · EMEX només publica la dada vigent: la seva API (filtres
            -- id/i/tipus) no té cap paràmetre temporal — verificat en viu 2026-07-20; els
            -- paràmetres temporals que es provin s'ignoren en silenci. La sèrie de població
            -- SÍ que existeix per una altra via oficial (Idescat censph, 1975→) i la seva
            -- ingesta està encuada: per això el motiu de `poblacio` acaba diferent del de
            -- les franges (que no tenen aquesta altra via verificada).
            ('poblacio',
             'La font oficial d''on llegim el padró només publica la dada vigent: no en podem ensenyar l''evolució. La sèrie històrica existeix per una altra via oficial i tenim previst carregar-la.',
             'La fuente oficial de donde leemos el padrón solo publica el dato vigente: no podemos enseñar su evolución. La serie histórica existe por otra vía oficial y tenemos previsto cargarla.',
             cast(m.poblacio as double)),
            ('pob_0_14',
             'La font oficial només publica la dada vigent de cada franja d''edat: no en podem ensenyar l''evolució.',
             'La fuente oficial solo publica el dato vigente de cada franja de edad: no podemos enseñar su evolución.',
             cast(m.pob_0_14 as double)),
            -- (la 15-64 no ve directa de la font: es calcula restant les altres franges)
            ('pob_15_64',
             'Aquesta franja es calcula restant les altres de la població total, i la font oficial només publica la dada vigent: no en podem ensenyar l''evolució.',
             'Esta franja se calcula restando las demás de la población total, y la fuente oficial solo publica el dato vigente: no podemos enseñar su evolución.',
             cast(m.pob_15_64 as double)),
            ('pob_65_84',
             'La font oficial només publica la dada vigent de cada franja d''edat: no en podem ensenyar l''evolució.',
             'La fuente oficial solo publica el dato vigente de cada franja de edad: no podemos enseñar su evolución.',
             cast(m.pob_65_84 as double)),
            ('pob_85_mes',
             'La font oficial només publica la dada vigent de cada franja d''edat: no en podem ensenyar l''evolució.',
             'La fuente oficial solo publica el dato vigente de cada franja de edad: no podemos enseñar su evolución.',
             cast(m.pob_85_mes as double)),
            ('index_envelliment',
             'Aquest índex es calcula a partir de les franges d''edat, i d''aquestes la font oficial només publica la dada vigent: no en podem ensenyar l''evolució.',
             'Este índice se calcula a partir de las franjas de edad, y de estas la fuente oficial solo publica el dato vigente: no podemos enseñar su evolución.',
             cast(m.index_envelliment as double)),
            -- PENDENT NOSTRE · aquestes tres fonts SÍ que tenen sèrie històrica; el
            -- pipeline n'ingereix una sola foto. El motiu ho diu com el que és: un deute
            -- nostre, no un límit del món (ingesta de sèries encuada, vegeu next.md).
            ('renda_neta_persona',
             'La font oficial sí que en té la sèrie històrica; nosaltres encara no la carreguem. De moment n''ensenyem la darrera dada disponible (2023).',
             'La fuente oficial sí tiene la serie histórica; nosotros aún no la cargamos. De momento enseñamos el último dato disponible (2023).',
             cast(m.renda_neta_persona as double)),
            -- DADA DECENNAL · Cens d'habitatge 2021.
            ('pct_noprincipal',
             'És una dada del Cens d''habitatge del 2021, que es fa un cop cada deu anys: no tenim cap edició anterior comparable per ensenyar-ne l''evolució.',
             'Es un dato del Censo de vivienda de 2021, que se hace una vez cada diez años: no tenemos ninguna edición anterior comparable para enseñar su evolución.',
             cast(m.pct_noprincipal as double)),
            ('kg_hab_any',
             'La font oficial (l''Agència de Residus) sí que en té la sèrie històrica; nosaltres encara no la carreguem. De moment n''ensenyem el darrer any tancat.',
             'La fuente oficial (la Agencia de Residuos) sí tiene la serie histórica; nosotros aún no la cargamos. De momento enseñamos el último año cerrado.',
             cast(m.kg_hab_any as double)),
            ('kwh_hab',
             'La font oficial (l''ICAEN) sí que en té la sèrie històrica; nosaltres encara no la carreguem. De moment n''ensenyem el darrer any amb dades completes.',
             'La fuente oficial (el ICAEN) sí tiene la serie histórica; nosotros aún no la cargamos. De momento enseñamos el último año con datos completos.',
             cast(m.kwh_hab as double)),
            ('vidre_hab',
             'La font oficial (l''Agència de Residus) sí que té la sèrie històrica del vidre; nosaltres encara no la carreguem. De moment n''ensenyem el darrer any tancat.',
             'La fuente oficial (la Agencia de Residuos) sí tiene la serie histórica del vidrio; nosotros aún no la cargamos. De momento enseñamos el último año cerrado.',
             cast(m.vidre_hab as double)),
            -- REGISTRE VIU · el RTC no publica edicions: es llegeix com a foto del dia.
            ('rtc_per_1000hab',
             'El Registre de Turisme de Catalunya és un registre viu que llegim com una foto del dia de la càrrega: no en conservem cap tall anterior amb què comparar.',
             'El Registro de Turismo de Cataluña es un registro vivo que leemos como una foto del día de la carga: no conservamos ningún corte anterior con el que comparar.',
             cast(m.rtc_per_1000hab as double)),
            -- D10 · les DUES que faltaven. El tauler les pinta (targeta «comerç i serveis»
            -- del bloc C) i no tenien fila: la targeta callava en comptes de declarar-se.
            -- El motiu NO és «encara no ingerida»: aquí ni tan sols guardant dos talls hi
            -- hauria tendència llegible, i això s'ha de dir sencer.
            -- (tècnicament: OSM via Overpass, ingerit com una sola consulta el dia de la
            --  càrrega, sense talls conservats; OSM infra-mapeja el rural i la completesa
            --  creix amb el temps, així que mapejat nou i obertura real són inseparables)
            ('serveis_estab',
             'El recompte surt d''un mapa obert (OpenStreetMap) que es va completant amb el temps: una pujada podria ser que algú ha dibuixat al mapa una botiga que ja existia, no una obertura real. Per això no n''ensenyem l''evolució: ni guardant fotos successives es podria llegir com un canvi real al poble.',
             'El recuento sale de un mapa abierto (OpenStreetMap) que se va completando con el tiempo: una subida podría ser que alguien ha dibujado en el mapa una tienda que ya existía, no una apertura real. Por eso no enseñamos su evolución: ni guardando fotos sucesivas podría leerse como un cambio real en el pueblo.',
             cast(m.serveis_estab as double)),
            ('restauracio_estab',
             'El recompte surt d''un mapa obert (OpenStreetMap) que es va completant amb el temps: una pujada podria ser que algú ha dibuixat al mapa un bar que ja existia, no una obertura real. Per això no n''ensenyem l''evolució: ni guardant fotos successives es podria llegir com un canvi real al poble.',
             'El recuento sale de un mapa abierto (OpenStreetMap) que se va completando con el tiempo: una subida podría ser que alguien ha dibujado en el mapa un bar que ya existía, no una apertura real. Por eso no enseñamos su evolución: ni guardando fotos sucesivas podría leerse como un cambio real en el pueblo.',
             cast(m.restauracio_estab as double))
    ) as s(metric, motiu_ca, motiu_es, valor)
),

-- SENSE SÈRIE · la capa d'ORIGEN, que viu a mart_demografia i no a mart_municipi.
-- D10 (2a passada): el LLOC DE NAIXEMENT entra al tauler amb D11 i tampoc no tenia fila. El
-- seu límit té DUES meitats i totes dues s'han de dir, perquè la segona és la perillosa:
--   1r · ve d'EMEX (f69/f72/f73), que no serveix sèrie per API — el mateix límit de font que
--        la població i les franges.
--   2n · aquí SÍ que hi ha una sèrie a tocar —la de NACIONALITAT, 2021→2025— i NO es pot
--        fer servir com si fos aquesta: són conjunts diferents. Qui es nacionalitza surt del
--        de nacionalitat estrangera i es queda al de nascuts a l'estranger. Substituir-la
--        seria la confusió que el propi contracte prohibeix, i és pitjor que no tenir-ne cap.
sense_origen as (
    select d.ine5, m.codi6, d.municipi, s.metric, s.motiu_ca, s.motiu_es, s.valor
    from {{ ref('mart_demografia') }} d
    join {{ ref('mart_municipi') }} m on d.ine5 = m.ine5
    cross join lateral (
        values
            -- (tècnicament: EMEX f69/f72/f73, mateix límit d'API que la població; els
            --  localitzadors de camp viuen al contracte com a origin_source des de V3)
            ('poblacio_nascuda_catalunya',
             'La font oficial només publica la dada vigent del lloc de naixement: en tenim la foto d''avui, no l''evolució. I l''evolució que es veu a la targeta de nacionalitat (2021→2025) no serveix aquí: parla d''un altre grup de gent (qui obté la nacionalitat espanyola canvia de grup allà, però no aquí).',
             'La fuente oficial solo publica el dato vigente del lugar de nacimiento: tenemos la foto de hoy, no la evolución. Y la evolución que se ve en la tarjeta de nacionalidad (2021→2025) no sirve aquí: habla de otro grupo de gente (quien obtiene la nacionalidad española cambia de grupo allí, pero no aquí).',
             cast(d.poblacio_nascuda_catalunya as double)),
            ('poblacio_nascuda_resta_espanya',
             'La font oficial només publica la dada vigent del lloc de naixement: en tenim la foto d''avui, no l''evolució. L''evolució de la targeta de nacionalitat (2021→2025) no la substitueix: compta un altre grup de gent.',
             'La fuente oficial solo publica el dato vigente del lugar de nacimiento: tenemos la foto de hoy, no la evolución. La evolución de la tarjeta de nacionalidad (2021→2025) no la sustituye: cuenta a otro grupo de gente.',
             cast(d.poblacio_nascuda_resta_espanya as double)),
            ('poblacio_nascuda_estranger',
             'La font oficial només publica la dada vigent del lloc de naixement: en tenim la foto d''avui, no l''evolució. I compte: l''evolució de la nacionalitat estrangera (2021→2025) no és la d''aquesta xifra — qui obté la nacionalitat espanyola surt d''aquell grup però continua havent nascut a l''estranger.',
             'La fuente oficial solo publica el dato vigente del lugar de nacimiento: tenemos la foto de hoy, no la evolución. Y ojo: la evolución de la nacionalidad extranjera (2021→2025) no es la de esta cifra — quien obtiene la nacionalidad española sale de aquel grupo pero sigue habiendo nacido en el extranjero.',
             cast(d.poblacio_nascuda_estranger as double)),
            ('pct_nascuda_estranger',
             'Aquest percentatge es calcula sobre el lloc de naixement, del qual la font oficial només publica la dada vigent: en tenim la foto, no l''evolució. L''evolució que sí que es veu al costat és la del % de nacionalitat estrangera, i no és la mateixa: mesura un altre grup de gent.',
             'Este porcentaje se calcula sobre el lugar de nacimiento, del cual la fuente oficial solo publica el dato vigente: tenemos la foto, no la evolución. La evolución que sí se ve al lado es la del % de nacionalidad extranjera, y no es la misma: mide a otro grupo de gente.',
             cast(d.pct_nascuda_estranger as double))
    ) as s(metric, motiu_ca, motiu_es, valor)
),

-- SENSE SÈRIE · els municipis on la FONT calla la SÈRIE de nacionalitat (2026-08-01).
-- Fins avui aquestes files no existien: `origen_out` filtrava `where serie_any_inicial is
-- not null` i 16 dels 947 es quedaven SENSE CAP FILA de `pct_nacionalitat_estrangera` ni de
-- `poblacio_nacionalitat_estrangera` — absents, que és el que la doctrina prohibeix («una
-- fila que falta és invisible; un motiu es pot llegir»). Es veia poc mentre el llindar mínim
-- N també els amagava el nivell; retirat el llindar (vot de Bea 2026-08-01) el forat queda
-- a la vista: publiquem el nivell i callem, sense dir-ho, que no en tenim l'evolució.
--
-- El límit és de la FONT i no nostre, i té dues cares que convé no confondre:
--   · la FOTO (Idescat EMEX, Cens anual): la publica per als 947, sense excepcions.
--   · la SÈRIE anual de població estrangera: en reserva 36 dels 947 el 2025 (54 el 2021), i
--     a aquests 16 els la reserva TOTS els anys → no hi ha finestra, ni curta.
-- Són municipis de 25 a 234 habitants. El motiu ho diu sense atribuir a la font cap raó que
-- no hagi declarat: la reserva, i nosaltres no la substituïm per cap càlcul propi.
sense_origen_serie as (
    select d.ine5, m.codi6, d.municipi, s.metric, s.motiu_ca, s.motiu_es, s.valor
    from {{ ref('mart_demografia') }} d
    join {{ ref('mart_municipi') }} m on d.ine5 = m.ine5
    left join {{ ref('int_demografia_deltes') }} k on k.ine5 = d.ine5
    cross join lateral (
        values
            ('pct_nacionalitat_estrangera',
             'Aquest percentatge el podem calcular avui, però la font oficial no publica la sèrie d''anys anteriors d''aquest municipi: la reserva pel secret estadístic. En tenim la foto, no el moviment — i no l''omplim amb cap càlcul nostre.',
             'Este porcentaje lo podemos calcular hoy, pero la fuente oficial no publica la serie de años anteriores de este municipio: la reserva por secreto estadístico. Tenemos la foto, no el movimiento — y no la rellenamos con ningún cálculo nuestro.',
             cast(d.pct_nacionalitat_estrangera as double)),
            ('poblacio_nacionalitat_estrangera',
             'La font oficial publica quantes persones amb nacionalitat estrangera hi viuen avui, però no la sèrie d''anys anteriors d''aquest municipi: la reserva pel secret estadístic. En tenim la foto, no el moviment.',
             'La fuente oficial publica cuántas personas con nacionalidad extranjera viven hoy aquí, pero no la serie de años anteriores de este municipio: la reserva por secreto estadístico. Tenemos la foto, no el movimiento.',
             cast(d.poblacio_nacionalitat_estrangera as double))
    ) as s(metric, motiu_ca, motiu_es, valor)
    where k.serie_any_inicial is null or k.serie_any_final is null
),

sense_out as (
    select
        ine5, codi6, municipi, metric,
        cast(null as varchar)      as comparacio,
        'sense_serie'              as estat,
        motiu_ca,
        motiu_es,
        cast(null as varchar)      as periode_actual,
        cast(null as varchar)      as periode_anterior,
        valor                      as valor_actual,
        cast(null as double)       as valor_anterior,
        cast(null as double)       as delta,
        cast(null as double)       as delta_min,
        cast(null as double)       as delta_max,
        false                      as delta_emmascarat,
        cast(null as varchar)      as unitat_delta
    from (select * from sense
          union all select * from sense_origen
          union all select * from sense_origen_serie)
),

unio as (
    select ine5, codi6, municipi, metric, comparacio, estat, motiu_ca, motiu_es, periode_actual,
           periode_anterior, valor_actual, valor_anterior, delta, delta_min, delta_max,
           delta_emmascarat, unitat_delta
    from atur_out
    union all
    select ine5, codi6, municipi, metric, comparacio, estat, motiu_ca, motiu_es, periode_actual,
           periode_anterior, valor_actual, valor_anterior, delta, delta_min, delta_max,
           delta_emmascarat, unitat_delta
    from origen_out
    union all
    select ine5, codi6, municipi, metric, comparacio, estat, motiu_ca, motiu_es, periode_actual,
           periode_anterior, valor_actual, valor_anterior, delta, delta_min, delta_max,
           delta_emmascarat, unitat_delta
    from sense_out
),

-- comarca des de l'AUTORITAT territorial del web (mateix criteri que mart_govern: mai
-- una llista fixa, mai la comarca dels residus).
terr as (
    with raw as (
        select json(content) as j
        from read_text('{{ var("web_root") }}/municipis-territori.json')
    ),
    keys as (
        select unnest(json_keys(j)) as ine5, j from raw
    )
    select ine5, json_extract_string(j, '$.' || ine5 || '.comarca') as comarca
    from keys
)

select
    u.ine5,
    u.codi6,
    u.municipi,
    t.comarca,
    u.metric,
    u.comparacio,
    u.estat,
    u.motiu_ca,
    u.motiu_es,
    u.periode_actual,
    u.periode_anterior,
    u.valor_actual,
    u.valor_anterior,
    u.delta,
    u.delta_min,
    u.delta_max,
    u.delta_emmascarat,
    u.unitat_delta,
    -- DIRECCIÓ llegible (la fletxa), amb la regla d'honestedat aplicada als tres casos:
    --   · delta exacte        → el seu signe.
    --   · delta EMMASCARAT    → el signe NOMÉS si l'interval no travessa el zero (llavors
    --     està PROVAT: [1,4] puja segur, [-4,-1] baixa segur, encara que el número exacte
    --     sigui secret). Si el travessa ([-3,3]), 'indeterminat' EXPLÍCIT — que és una
    --     resposta, no una absència: el front ha de dir «no es pot dir amb el <5», no callar.
    --   · sense sèrie         → NULL (no hi ha res a comparar; l'estat ja ho diu).
    -- Així cap fletxa surt sense el seu període i sense número (exacte o interval) al darrere.
    case
        when u.estat = 'sense_serie' then null
        when u.delta is not null then
            case when u.delta > 0 then 'puja' when u.delta < 0 then 'baixa' else 'igual' end
        when u.delta_min is null or u.delta_max is null then null
        when u.delta_min > 0 then 'puja'
        when u.delta_max < 0 then 'baixa'
        else 'indeterminat'
    end                                            as direccio
from unio u
left join terr t on u.ine5 = t.ine5
order by u.ine5, u.metric, u.comparacio
