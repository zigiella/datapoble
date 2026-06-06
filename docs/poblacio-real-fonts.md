# Població real vs padró — inventari de proxies de presència (Berguedà)

**Qué es:** inventari **honest** de fonts de dades que podrien servir per estimar la
**presència humana real** d'un municipi i comparar-la amb el **padró oficial** (el
*gap* població real − padró). És *groundwork* per a l'indicador estrella de
riusdegent: no conté l'estimació ni la reclamació final (això és síntesi de Talaia),
només l'inventari verificat de quines fonts existeixen, amb quina granularitat, i com
mapejarien a presència.

**Autora:** Sondeig · **Data:** 2026-06-04 · **Pilot:** Berguedà (31 municipis).
**Mètode:** verificació **en viu** (API SODA/Socrata `analisi.transparenciacatalunya.cat`,
catàleg Socrata, portals ACA/ICAEN/Idescat). El que no s'ha comprovat en viu es marca com a tal.
**Doble de:** `docs/data-sources.md` (Experiment 0, 2026-06-01) — aquell és el registre
general de fonts; **aquest el reenfoca a l'eix presència/padró** i hi afegeix verificació nova
(sobretot **electricitat municipal**, que l'Experiment 0 no tenia tancada).

---

## 0. El concepte (per fixar què comptem)

El **padró** (Idescat, via EMEX — `packages/ingestion/.../idescat_emex.py`) compta
**residents empadronats**. No compta:

- **Segones residències** ocupades a temporades (el seu titular consta empadronat *en un altre lloc*).
- **Excursionistes de dia** (entren i surten sense pernoctar; invisibles al RTC i al padró).
- **Turistes que pernocten** en allotjament reglat o no reglat.
- **Treballadors pendulars** (hi treballen però no hi viuen).

Cap font dóna "persones-dia reals" en absolut. La via realista és **triangular proxies de
presència** (cadascun amb el seu biaix) i ancorar-los contra un padró fiable. La unitat de
join sempre és **`ine5`** (codi INE de 5 dígits), la mateixa de `mart_municipi`.

⚠️ **Trampa de l'escala (de l'Experiment 0).** Castellar de n'Hug (166 hab) = 1 secció
censal; els ràtios per càpita sobre denominadors diminuts són inestables i molts datasets
amaguen valors per **secret estadístic**. L'indicador només té sentit **normalitzat contra
la distribució comarcal** (31 municipis), no municipi a municipi en absolut.

---

## 1. Taula d'inventari per proxy

Llegenda viabilitat: ✅ disponible amb granularitat municipal (`ine5`) · ⚠️ existeix però amb
limitació (granularitat grossa, latència, secret estadístic, o accés no-API) · ❌ no disponible
municipal per al pilot.

| # | Proxy | Viab. | Granularitat | Font / endpoint | Cobertura temporal · latència | Llicència | Com mapeja a presència |
|---|---|---|---|---|---|---|---|
| 1 | **Residus municipals** (kg/hab/any, t/any) | ✅ | **Municipi (`codi_municipi`=ine5)** | ARC · Socrata **`69zu-w48s`** (`/resource/69zu-w48s.json`) · **ja ingerit** (`residus.py`) | **2000–2024** · anual, latència ~1 any (act. 2025-12-12) | Dades Obertes Catalunya (CC BY-like) | **Proxy directe de càrrega real.** La generació total (`generaci_residus_municipal`, t/any) divideix-la per *presència* en lloc de padró; si kg/hab/any >> mitjana comarcal → el denominador (padró) infraestima la població real. Ja és la columna `kg_hab_any` de `mart_municipi`. |
| 2 | **Consum elèctric domèstic** (kWh/any) | ✅ | **Municipi (`cdmun`=ine5) × sector** | ICAEN · Socrata **`8idm-becu`** (`/resource/8idm-becu.json`) | **2013–2024** · anual, latència ~1 any (act. 2025-12-17) | Socrata "Terms of Use" (Dades Obertes) | **El millor proxy nou.** Sector `USOS DOMÈSTICS` = energia residencial. Sobreviu al **secret estadístic fins i tot a Castellar** (sèrie 2013-2024 sencera, vegeu §2). kWh domèstic/padró anòmalament alt → habitatge ocupat per no-empadronats (segona residència activa). Estacionalitat NO captable (és anual). |
| 3 | **Padró continu** (base, denominador) | ✅ | Municipi (i secció) | Idescat EMEX/`pmh` · `idescat_emex.py` (`api.idescat.cat/emex`) | Sèrie anual des de 1998 · latència <1 any | Idescat (reutilització amb atribució) | **És el denominador "oficial"**, no un proxy de presència. Tot el *gap* es mesura contra això. Ja a `mart_municipi.poblacio`. |
| 4 | **Allotjament reglat (RTC/HUT)** | ✅ | Municipi | RTC · Socrata **`t2h3-cgys`** · **ja ingerit** (`rtc.py`) | Mensual · latència baixa | Dades Obertes (conté dades del titular — RGPD) | **Stock, no flux.** Places potencials de pernoctació. A `mart_municipi` com `rtc_total`/`rtc_hut`. Capacitat ≠ ocupació: cota superior de presència turística reglada, no presència real. |
| 5 | **Trànsit / IMD** (aforaments) | ⚠️ | **Estació d'aforament** (no municipi) | Generalitat · Socrata **`xsvx-ym46`** (té `poblaci`, `comarca`, lat/lon, `imd`) | Sèrie ~**2017–2022** · latència alta (act. 2024-04) | Dades Obertes | **Proxy d'accés/corredor, no municipal.** Al Berguedà només ~3 estacions toquen el corredor (C-16 Berga; B-402 cap a Castellar; BV-4031). Útil com a senyal de pressió del corredor turístic, **no** com a sèrie per als 31 municipis. |
| 6 | **Pernoctacions / ocupació** (EOH, turisme rural, càmpings) | ❌ | **Marca turística "Pirineus" / comarca** | Idescat EOH/`turall` (indicadors anuals/conjuntura) | Mensual/anual a nivell marca | Idescat | El flux de pernoctació **NO baixa a municipi** per a aquests: l'enquesta es publica per marca turística (Pirineus) i, com a molt, comarca. Berga i Castellar cauen dins "Pirineus". Sense dada municipal → ❌ per al pilot. |
| 7 | **Taxa turística / IEET** (pernoctacions gravades) | ⚠️ | Comarca (municipal exclou el pilot) | Socrata `q4sr-68c3` (municipi), **`2nmt-74sj`** (comarca) | Semestral | Dades Obertes | El dataset municipal `q4sr-68c3` **exclou explícitament Berga i Castellar** (cauen a "Resta de municipis") — verificat a l'Experiment 0. Només utilitzable a nivell **comarca** (`2nmt-74sj`). Proxy de pernoctació reglada, no de presència total. |
| 8 | **Visitants d'equipaments** (museus, Tren del Ciment) | ⚠️ | Municipal *de facto* (puntual) | Notes de premsa / mNACTEC / FGC-Turistren — **no open data API** | Anual · publicació irregular | Variable (no oberta) | **Excel·lent senyal d'excursionisme** on existeix (Castellar: Tren del Ciment 2024 = 29.019; Museu del Ciment 2024 = 20.846 → ~50.000 visites a un poble de 166). Però és **manual i per a pocs municipis**; no és una sèrie homogènia per als 31. Ancoratge, no pipeline. |
| 9 | **Tren** (validacions Rodalies/FGC) | ❌ | Estació (i el Berguedà gairebé no en té) | FGC / Rodalies | — | — | Sense granularitat municipal oberta i utilitzable. L'única cosa "tren" rellevant al pilot és el **Tren del Ciment** (turístic, → fila 8), no servei de rodalia. ❌ com a proxy general. |
| 10 | **Consum d'aigua / abastament** (volum) | ⚠️/❌ | **Comarca** (volum) · municipi només *estat de sequera* | ACA · portal `aca.gencat.cat` (**`2gws-ubmt`** = consum per **comarques**); Socrata `i5n8-43cw` = **estat** de sequera per municipi (categòric, no volum) | Anual/diari segons producte | Dades Obertes / ACA | **Volum de consum NO és municipal obert**: la sèrie de consum (domèstic/activitats) es publica **per comarca**. El dataset municipal de l'ACA al portal (`i5n8-43cw`) és l'**estat** de sequera (NORMALITAT/ALERTA…), no litres. Hi ha "Observatori del preu de l'aigua per municipis" (preu, no consum). → proxy de presència municipal **no disponible** sense conveni amb l'ens d'abastament. |
| 11 | **Mòbil agregat (mobilitat INE)** | ❌ | Cel·les ≥5.000 hab | INE estudis de mobilitat | — | Gratuït | Castellar no és aïllable (es dilou en una cel·la gran). Berga *potser* té cel·la pròpia (no confirmat). ❌ per a granularitat municipal fiable al pilot. |
| 12 | **Senyals d'interès** (Wikipedia pageviews, Google Trends) | ⚠️ | Article / terme de cerca | API Wikimedia (absolut) · Trends (relatiu) | Diari | Oberta/legal | Proxy d'**interès/estacionalitat**, no de presència física. Wikipedia pageviews = recompte absolut, infrautilitzat. Útil per donar **forma de corba** (quan ve la gent), ancorada contra un dut dur (fila 8). No mapeja a persones absolutes. |

---

## 2. Verificació en viu de les dues fonts noves clau (2026-06-04)

### Electricitat `8idm-becu` — la troballa
Comprovat per API SODA:

- **Columnes:** `any, provincia, comarca, cdmun, municipi, codi_sector, descripcio_sector, consum_kwh, observacions`.
- **`cdmun` = INE5** (p. ex. `08001` Abrera, `08022` Berga, `08052` Castellar) → **join directe amb `ine5`**, sense crosswalk.
- **6 sectors:** PRIMARI, INDUSTRIAL, CONSTRUCCIÓ I OBRES PÚBLIQUES, TRANSPORT, SERVEIS, **USOS DOMÈSTICS**.
- **Cobertura 2013–2024** (12 anys), act. 2025-12-17.
- **Secret estadístic:** els sectors petits en municipis diminuts surten `consum_kwh = null` amb
  `observacions = "Dada subjecta a secret estadístic"` (a Castellar: INDUSTRIAL i CONSTRUCCIÓ
  estan ocults). **Però `USOS DOMÈSTICS` i `SERVEIS` NO** — sèrie sencera fins i tot per a
  Castellar (166 hab). Domèstic Castellar (kWh): 2024≈266.857 · 2023≈273.219 · 2022≈271.939 …
  Berga domèstic 2024≈21.019.904. **Aquesta resistència al secret estadístic és el que fa el
  consum domèstic viable per a micromunicipis** — on el padró és més soroll.

### Aigua — el "no" honest
- `2gws-ubmt` ("Consum d'aigua a Catalunya per comarques") → **comarca**, no municipi.
- `i5n8-43cw` ("Estat de sequera … i municipis") → té `codi_municipi`/`municipi` **però** les
  columnes són d'**estat** (`estat_sequera_hidrol_gic`, `…_pluviom`), categòriques —
  **no volum consumit**. No serveix com a proxy de presència.
- Conclusió: **consum d'aigua municipal (volum) no és dada oberta**. Caldria conveni amb l'ens
  d'abastament (p. ex. mancomunitat/empresa local) — fora de l'abast d'un pipeline obert.

---

## 3. Recomanació — els 3 proxies més viables per al pilot

Prioritzats per: granularitat municipal real (`ine5`) · resistència al secret estadístic ·
latència · que ja en tinguem (o sigui trivial) la ingesta.

1. **Residus municipals (`69zu-w48s`)** — *cornerstone, ja ingerit.* Únic proxy que és
   **directament** càrrega física generada per la presència, municipal, 25 anys de sèrie, i ja
   és `kg_hab_any` a `mart_municipi`. La generació **total** (t/any) dividida per presència (en
   comptes de padró) és la base més neta del *gap*. Validació externa interna: Spearman(IETR,
   kg_hab_any)=0,87 → la càrrega real ja correlaciona amb l'exposició turístico-residencial.

2. **Consum elèctric domèstic (`8idm-becu`)** — *millor afegit nou.* Municipal (`cdmun`=ine5),
   2013-2024, i **sobreviu al secret estadístic a micromunicipis** (clau a Castellar). Senyal
   independent de residus (energia vs massa) → triangula. Limitació honesta: és **anual**, no
   capta estacionalitat; i el consum domèstic també puja amb renda/superfície, no només amb
   presència (cal normalitzar per habitatge, p. ex. kWh/`hab_total`).

3. **Padró Idescat (EMEX)** — *el denominador, ja el tenim.* No és proxy de presència sinó la
   referència "oficial" contra la qual es mesura tot el *gap*. Imprescindible i ja a
   `mart_municipi.poblacio`.

**Quart, com a ancoratge (no pipeline):** **visitants d'equipaments** (Tren del Ciment, Museu del
Ciment) per a Castellar — és l'únic lloc on tenim un nombre dur d'excursionisme que permet
*calibrar* l'escala dels proxies indirectes. No homogeni per als 31 municipis, però insubstituïble
per fixar el factor "població real / padró" allà on l'excursionisme domina.

**Descartats honestament per al pilot:** pernoctacions/EOH (només marca Pirineus), taxa
turística municipal (exclou Berga i Castellar), aigua-volum (només comarca), mòbil INE
(Castellar diluït), tren-rodalia (inexistent), IMD (per estació, no municipi).

---

## 4. Nota de disseny per a la síntesi (Talaia)

- **Dos proxis independents que apuntin al mateix** (residus ↑ i elèctric domèstic ↑ per sobre del
  que justifica el padró) és un senyal molt més robust que un de sol. Suggereixo construir el *gap*
  com a **z-score comarcal** de cada proxy normalitzat per llar/habitatge, no com a valor absolut.
- **No barrejar capes:** tots aquests proxies són 🟢 VISIBLES (no electoral). El *gap* és producte
  públic.
- **El padró és el denominador, no un proxy** — mantenir-lo separat conceptualment perquè el
  numerador (presència) i el denominador (padró) tenen fonts i biaixos diferents.
- La **reclamació final població-real és de Talaia**: aquest doc para deliberadament a l'inventari.

---

# Fonts per a turisme / excursionisme (afinament: pernocta vs dia)

**Autora:** Sondeig · **Data:** 2026-06-06 · **Encàrrec:** Bea (direcció humana) vol
distingir **població que pernocta** d'**excursionistes de dia**: en municipis molt turístics
els residus i el consum no són «població empadronada». Aquesta secció és **investigació de
disponibilitat** (no materialitza res; la síntesi de l'indicador és de Talaia) i respon a **3
preguntes** verificades **en viu** (API SODA Socrata, API EMEX Idescat, Overpass/OSM, portals
Idescat/INE) el **2026-06-06**. Pilot: Berguedà (31 munis).

## T0. Resum executiu (les 3 respostes)

| # | Pregunta | Disponible? | Font / dataset | Granularitat | Cobertura | Separa pernocta/dia? |
|---|---|---|---|---|---|---|
| 1 | **Fraccions de residus (VIDRE)** | ✅ **SÍ, ja la tenim** | ARC `69zu-w48s` (**el mateix que ja ingerim**) — columna `vidre` (+ `paper_i_cartr`, `envasos_lleugers`, `mat_ria_org_nica`, fracció resta) | **Municipal (`codi_municipi`=ine5)**, **anual** | **2000–2024**, 31/31 munis 2024, **zero NULL**, sobreviu al secret estadístic fins a Castellar (164 hab) | **Sí, indirectament.** Vidre/càpita = *proxy* d'hostaleria (ampolles de bar/restaurant) → marca segona residència + turisme de tornada-a-casa. |
| 2 | **Establiments de restauració** | ⚠️ **SÍ amb matís** (cap font 100% neta + open) | (a) **Idescat "Empreses i establiments" `ee`** per CCAE-2009; (b) **OSM/Overpass** `amenity=restaurant\|bar\|cafe` (proxy obert, verificat); (c) EMEX `g170` (només grans sectors, NO aïlla hostaleria) | (a) Municipal × branca CCAE; (b) Punt geocodificat → agregable a munis; (c) Municipal però sector massa ampli | (a) act. 26/02/2026, sèrie llarga; (b) snapshot OSM (Berga=24 locals verificat); (c) ja al pipeline | **Sí (stock).** Densitat de restauració/hab = capacitat d'hostaleria → senyal de turisme de dia + pernocta, no flux. |
| 3 | **Granularitat estacional/mensual** | ❌ **NO a nivell municipal** | ICAEN elèctric `8idm-becu` = **anual**; ARC residus = **anual**; demanda horària `hx6q-ykhb` = **Catalunya global** (sense municipi); EOH/turisme rural (INE/Idescat) = **mensual/trim. però per marca "Pirineus"**, no municipi | Cap sèrie **infra-anual × municipal** per al pilot | — | **Seria el senyal més net** (pics estiu/cap de setmana = 2a residència) **però NO existeix obert per municipi.** El «no» honest principal d'aquesta ronda. |

## T1. Pregunta 1 — Fraccions de residus (VIDRE): ✅ ja disponible, infrautilitzada

**Troballa clau: no cal connector nou.** El dataset ARC `69zu-w48s` que `residus.py` ja
ingereix **conté totes les fraccions de recollida selectiva per municipi**, no només
`kg_hab_any`. Columnes verificades en viu (esquema complet via `/api/views/69zu-w48s.json`):

- **Selectiva per fracció (t/any):** `vidre`, `paper_i_cartr`, `envasos_lleugers`,
  `mat_ria_org_nica` (FORM), `poda_i_jardineria`, `residus_voluminosos_fusta`, `raee`,
  `ferralla`, `olis_vegetals`, `t_xtil`, `runes`, `res_especials_en_petites`, `piles`,
  `medicaments`, `altres_recollides_selectives`, `total_recollida_selectiva`.
- **Fracció resta (t/any):** `resta_a_dip_sit`, `resta_a_incineraci`,
  `resta_a_tractament_mec_nic`, `resta_sense_desglossar`, `suma_fracci_resta`.
- **Ràtios/percentatges:** `kg_hab_any_recollida_selectiva`, `r_s_r_m_total`, `f_r_r_m`,
  `generaci_residus_municipal`, `kg_hab_any`, `kg_hab_dia`.
- **Granularitat:** **municipal** (`codi_municipi` = INE5), **anual**, **2000–2024**.
- **Cobertura del pilot (2024):** **31/31 municipis del Berguedà** amb `vidre` i `paper`
  **no-null** (`count(vidre)=31`). El vidre **sobreviu al secret estadístic fins i tot a
  Castellar de n'Hug (164 hab): 17,66 t** — a diferència dels sectors industrials de l'elèctric.

**Per què el VIDRE és el millor proxy de turisme/hostaleria (verificat numèricament, 2024):**
el vidre per càpita separa nítidament els micromunicipis turístics de la capital estable.

| Municipi | Pob. | Vidre (t) | **kg vidre/hab/any** |
|---|---:|---:|---:|
| Gósol | 214 | 32,0 | **149,4** |
| Gisclareny | 30 | 4,3 | **144,0** |
| Sagàs | 154 | 20,4 | **132,5** |
| Castellar de n'Hug | 164 | 17,7 | **107,7** |
| la Nou de Berguedà | 163 | 14,8 | **90,8** |
| **(mediana comarcal)** | — | — | **49,8** |
| **Berga** (capital) | 17.195 | 475,3 | **27,6** |

> Gósol genera **5,4×** més vidre per habitant que Berga. La signatura és inequívoca:
> pobles petits de muntanya amb molta restauració + segona residència (caps de setmana,
> estiu) generen molt vidre que el padró no «veu». El vidre és **més net que els residus
> totals** perquè la fracció resta domèstica dels residents estables dilueix menys el senyal
> turístic, i més net que `kg_hab_any` global perquè aïlla el consum de begudes (bar/restaurant).

**Com ajuda a separar pernocta/dia:** vidre/càpita alt sense allotjament reglat (RTC baix) →
apunta a **excursionisme de dia + segona residència no reglada**; vidre/càpita alt **amb** RTC
alt → pernocta reglada. Combinat amb el ràtio vidre vs FORM (`mat_ria_org_nica`): l'orgànica
escala més amb residents que pernocten i cuinen; el vidre escala amb consum de begudes puntual
→ **vidre/FORM alt = més pes d'hostaleria de dia**. (Hipòtesi per a Talaia; aquí només
constato que **les dues columnes existeixen i tenen cobertura 31/31**.)

**Limitació honesta:** és **anual** (no capta estacionalitat, vegeu T3) i la recollida pot
variar per *model de gestió* (porta a porta vs contenidor) entre munis — el nivell absolut no
és perfectament comparable, però el **z-score comarcal** (com a la §4) ho neutralitza.

## T2. Pregunta 2 — Establiments de restauració: ⚠️ viable amb matisos

No hi ha **una** font que sigui alhora municipal, neta (només restauració) i 100% oberta sense
fricció. Tres vies, de més «oficial» a més «proxy»:

**(a) Idescat «Empreses i establiments» (`id=ee`) — la via oficial.** Verificat al portal
Idescat: ofereix dades **a nivell de municipi individual** desagregables **per sector i branca
d'activitat econòmica (CCAE-2009)**. La hostaleria és la **secció I** (divisió **55** serveis
d'allotjament + **56** serveis de menjars i begudes). Act. **26/02/2026**, dades a 1 de gener,
sèrie llarga. Descàrrega oberta (**CSV / JSON-stat**). **Matís:** als municipis molt petits
Idescat pot aplicar **secret estadístic** a la branca (pendent de confirmar quants dels 31
munis tenen el detall I/56 publicat); i no separa fàcilment bar vs restaurant. Accés: **no és
Socrata** (l'EMEX a Socrata `6rmk-88zt` és «non-tabular», no s'hi pot fer SoQL); cal el portal
JSON-stat d'Idescat o la descàrrega CSV de l'estadística `ee`.

**(b) EMEX API (`api.idescat.cat/emex`) — NO serveix per a restauració.** Verificat en viu
(Berga `081521`): el grup `g170` «Sectors econòmics» només dóna **grans sectors** (afiliacions
SS i atur a *indústria / construcció / serveis*) i `t182` «Allotjaments turístics» (turisme
rural + places). **«Serveis» engloba hostaleria però no l'aïlla** → no dóna nombre
d'establiments de restauració. El connector `idescat_emex.py` actual (només `f321`, `f122`…) no
porta res d'hostaleria; afegir-ho no resol la pregunta perquè la dada fina no és a l'EMEX.

**(c) OpenStreetMap via Overpass — proxy obert, verificat que funciona.** Query
`amenity=restaurant|bar|cafe|pub|fast_food`. **Verificat en viu (2026-06-06):** Berga (bbox
ciutat) = **24 locals**. És geocodificat → agregable a municipi per punt-en-polígon amb el
límit administratiu. **Cobertura:** depèn de la completesa d'OSM (a pobles petits pot
infraestimar; a Berga sembla raonable). **Gotcha documentada:** el match d'àrea per
`area["name"="Berguedà"]` **no resol** (accent/relació) → cal o bé **bbox**, o bé resoldre la
relació administrativa per `admin_level` i iterar **municipi a municipi** (`admin_level=8`).
Llicència **ODbL** (atribució + share-alike — a tenir en compte si es publica derivat).

**Com ajuda a separar pernocta/dia:** densitat de restauració per habitant (locals/1000 hab)
és **capacitat d'hostaleria** = *stock*, no flux. Alta densitat → municipi orientat a
visitants (de dia o pernocta). **Encreuat amb el vidre** (T1): molts locals + molt vidre =
hostaleria activa real; molts locals + poc vidre = capacitat infrautilitzada/estacional. **No
dóna persones-dia** per si sol.

**Recomanació P2:** per a una sèrie **homogènia i oficial**, **Idescat `ee` (CCAE 56)** és la
millor; per a un *snapshot* ràpid i lliure de fricció d'accés, **OSM/Overpass** com a proxy de
validació. Cap de les dues és flux; són *stock* de capacitat.

## T3. Pregunta 3 — Granularitat estacional/mensual: ❌ el «no» honest

**Cap font municipal oberta del pilot té sèrie infra-anual.** Verificat en viu:

- **ICAEN consum elèctric `8idm-becu`:** esquema = `any, provincia, comarca, cdmun, municipi,
  codi_sector, descripcio_sector, consum_kwh, observacions`. **Només `any`** → **anual**. No
  hi ha mes ni trimestre. (És el que ja sabíem; ara confirmat contra l'esquema.)
- **ARC residus `69zu-w48s`:** dimensió temporal = **`any`** únic → **anual**. No hi ha cap
  dataset ARC de recollida mensual municipal al catàleg Socrata (cerca «residus mensual» = 0
  resultats).
- **Demanda elèctrica horària `hx6q-ykhb`:** **SÍ és infra-anual** (data + h01..h24) **però és
  Catalunya global** (demanda en barres de central de la distribuïdora principal) — **cap
  dimensió municipal**. Inservible per municipi.
- **Gas natural `qvqg-zag8`** (trobat de passada): mateix patró que l'elèctric (municipi ×
  sector) i **anual**. Proxy de calefacció residencial (interessant per a ocupació hivernal de
  2a residència) però **no aporta estacionalitat**.
- **Turisme (pernoctacions/ocupació):** EOH i **enquesta d'ocupació en allotjaments de turisme
  rural** (INE, mensual → trimestral per a Catalunya) **SÍ tenen ritme mensual/trimestral**,
  **però es publiquen per marca turística** — el Berguedà cau dins **«Pirineus»** (9 comarques:
  Alt Urgell, Alta Ribagorça, Berguedà, Cerdanya, Garrotxa, Pallars Jussà, Pallars Sobirà,
  Ripollès, Solsonès). **No baixa a municipi.** (Coherent amb la fila 6/7 de la taula general.)

**Conclusió:** l'estacionalitat — que seria **el senyal més net** de segona residència i
excursionisme (pics juliol-agost i caps de setmana vs vall de febrer) — **no és obtenible a
nivell municipal** amb dades obertes per al pilot. Les úniques sèries infra-anuals són o bé
**no municipals** (demanda horària, EOH-Pirineus) o bé **categòriques** (estat de sequera).

**Vies fora d'abast (no obertes / no municipals), per si Talaia vol futur:**
- Consum elèctric/gas **amb corba de càrrega mensual** existeix a les distribuïdores però **no
  es publica obert per municipi** (caldria conveni).
- **Wikipedia pageviews** (fila 12 de la taula general) dóna **forma de corba diària/mensual**
  per article (p. ex. «Tren del Ciment», «Gósol») — proxy d'**interès/estacionalitat**, no de
  persones; útil només per *donar forma* ancorada a un dur (visitants d'equipaments, fila 8).

## T4. Recomanació d'aquesta ronda (per a la síntesi de Talaia)

1. **Activar el VIDRE ja** (cost ~zero): la columna existeix a la raw que ja descarreguem.
   N'hi ha prou d'**exposar `vidre` (i `mat_ria_org_nica`, `envasos_lleugers`, `paper_i_cartr`)
   a la capa transform** i derivar **vidre/càpita** i **vidre/FORM** com a *features* del
   *gap*. És el proxy d'hostaleria **més directe i amb millor cobertura** (31/31, fins a
   micromunicipis). Stub de connector afegit (no cablejat) — vegeu sota.
2. **Restauració:** si es vol *feature* de capacitat, **Idescat `ee` CCAE-56** (oficial,
   municipal) o **OSM/Overpass** (proxy lliure). Tractar com a *stock*, encreuat amb vidre.
3. **Estacionalitat:** **descartada** per al pilot a nivell municipal (vegeu T3). No invertir-hi
   pipeline; com a molt, Wikipedia pageviews per *forma de corba* en pocs municipis ancorada.

**Disseny suggerit:** el vidre/càpita encaixa exactament al marc de la §4 (z-score comarcal,
normalitzat, capa 🟢 VISIBLE). Dóna a Talaia un **tercer proxy independent** (massa de residus →
energia → **vidre = consum de begudes/hostaleria**) que triangula amb residus totals i elèctric
domèstic, i és **el que més directament separa el component turístic** del residencial estable.

## Pendent
- [x] **Fet (2026-06-05).** Connector `icaen_consum` (`8idm-becu`) cablejat a `all` →
      `data/raw/icaen_consum`; `stg_icaen_consum` + `mart_consum_electric` (sector 7
      USOS DOMÈSTICS, comarca Berguedà, unió per `ine5`) materialitzat a
      `data/marts/mart_consum_electric.parquet`. **Cobertura: 31/31 municipis ×
      2013–2024 (372 files), zero forats.** Castellar 2024 = 266.857 kWh, Berga 2024 =
      21.019.904 kWh (coincideixen amb la verificació en viu del §2). NO normalitzat
      encara (consum brut anual, fidel a la font).
- [ ] Confirmar amb Talaia la normalització del numerador (per llar vs per habitatge vs absolut)
      i la fórmula del *gap*; llavors afegir la columna derivada a `mart_municipi`.
- [x] **Fet (2026-06-06).** Explorat si l'ARC publica sèrie **infra-anual** municipal: **no**
      (residus = anual; cap dataset de recollida mensual al catàleg). La fracció **resta** sí que
      existeix per municipi (`suma_fracci_resta`) però **anual**, no estacional. Vegeu §T3.
- [x] **Fet (2026-06-06).** Investigació turisme/excursionisme (3 preguntes) → secció
      «Fonts per a turisme / excursionisme». Troballa: **el VIDRE (i totes les fraccions) ja és a
      `69zu-w48s`**, municipal 2000–2024, 31/31 cobertura. Stub `residus_fraccions.py` afegit
      (no cablejat a `all`). Restauració = Idescat `ee` CCAE-56 / OSM. Estacionalitat municipal = **no**.
- [ ] **Per a Talaia:** decidir si exposar `vidre`/`mat_ria_org_nica`/`envasos_lleugers` a
      `mart_municipi` i amb quina normalització (vidre/càpita, vidre/FORM, z-score comarcal).

## Enllaços
- `docs/data-sources.md` (Experiment 0 — registre general; aquest doc el reenfoca)
- ARC residus `69zu-w48s` · ICAEN elèctric `8idm-becu` · RTC `t2h3-cgys` · IMD `xsvx-ym46`
- ACA: `aca.gencat.cat/…/dades-obertes` (consum **comarcal** `2gws-ubmt`; estat sequera `i5n8-43cw`)
- Idescat EMEX: `api.idescat.cat/emex/v1/dades.json?id={codi6}`
