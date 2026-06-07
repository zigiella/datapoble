# Dossier de dades i metodologia · riusdegent

*Document de treball per a revisió externa (anàlisi de dades + open data). Redactat per Talaia (coordinació metodològica del projecte). Pilot: **Berguedà**, 31 municipis. Versió 2026-06-07.*

> **Per a qui revisa:** aquest dossier és deliberadament **exhaustiu i autocrític**. No amaga les inferències darrere de números bonics: marca a cada xifra si és **mesura** o **inferència**, quines en són les limitacions, i recull al final les **preguntes obertes** on més valorem el teu criteri. Si alguna cosa et grinyola, probablement tens raó — digue-ho.

---

## 0. Resum executiu

**riusdegent** és un observatori obert de **com s'habita el territori**. El seu nord és el desajust entre el **padró oficial** i la **habitança real**: fer visible la població que no consta però omple un municipi (segona residència, estacionals, excursionistes) i la que consta però ha marxat.

Es construeix sobre **dos pilars**:

1. **Capes d'habitança** — marts estructurats (vivenda, turisme, energia, l'indicador estrella de població real, índex IETR, política), tot ancorat a fonts oficials obertes.
2. **El cabal** — intel·ligència territorial a partir de **rastres administratius** (contractació pública, declaracions de sequera…): quan un fenomen no té dataset net, el seu *rastre* sí que existeix.

**Principi rector innegociable:** *cap xifra sense procedència, cap inferència disfressada de mesura.* Tot indicador porta fórmula, font, data i la frontera **dada/inferència** explícita. On no tenim dada fiable, ho diem (un buit honest val més que un fals precís).

**Què ens agradaria que critiquessis** (desenvolupat al §10): el calibratge de les estimacions de població contra un senyal extern conegut; la normalització del proxy elèctric; l'absència d'estacionalitat municipal; l'estratègia de bases per comarca a escala Catalunya; i el tractament de la lectura ecològica i la capa política.

---

## 1. Tesi i principis metodològics

### 1.1 El problema
El **padró** (Idescat) compta **residents empadronats**. No compta: segones residències ocupades per temporades, excursionistes de dia, turistes que pernocten, ni treballadors pendulars. Cap font pública dóna «persones-dia reals». La via realista és **triangular *proxies* de presència** —cadascun amb el seu biaix— i ancorar-los contra el padró.

I, sobretot: **«qui omple» un municipi no és una sola cosa.** En un poble molt turístic, l'augment de residus pot ser **excursionistes de dia**, no població. Anomenar-ho «població» seria fals. Per això no estimem un sol número, sinó **capes** que separen fenòmens diferents (vegeu §5).

### 1.2 Principis
- **Procedència sempre.** El contracte semàntic exigeix font + fórmula + data per a cada mètrica.
- **Mesura vs inferència, explícit.** Cada indicador es marca com a *mesurat* (dada oficial directa) o *derivat/inferència* (càlcul propi). A la UI es codifica amb color (slate = mesura, porpra = inferència).
- **Lectura ecològica.** Tots els indicadors parlen del **municipi**, mai d'individus. La falàcia ecològica es declara on aplica (sobretot a la capa política).
- **Rang, no punt.** Les estimacions es comuniquen com a rang + una **bandera de confiança**.
- **Un buit honest > un fals precís.** Als micromunicipis (secret estadístic, soroll de denominador) marquem confiança baixa en comptes d'inventar.
- **Refús com a *feature*** (a la IA): el que és fora del catàleg es rebutja amb un motiu llegible, mai s'al·lucina.

---

## 2. Arquitectura, contracte i reproductibilitat

### 2.1 El contracte semàntic (font de veritat)
`semantic/metrics.yml` és el **contracte únic** que defineix cada indicador (label ca/es, definició, fórmula, font, data, dimensió, procedència, caveat). El consumeixen **els tres** consumidors, de manera que cap número es codifica a mà enlloc:

- el **pipeline** de dades (transform) hi declara la columna de destí (`table`/`column`);
- la **IA** (Brúixola) en deriva el catàleg de mètriques i les seves fonts;
- el **web** (Mirador) hi llegeix labels, unitats, fonts i procedència.

### 2.2 *Stack* i flux
```
Fonts obertes (API SODA/Socrata, EMEX, Overpass)
   │  packages/ingestion  (connectors Python; raw + sidecar de procedència)
   ▼
dbt + DuckDB             (packages/transform; staging → marts)
   ▼
data/marts/*.parquet     (mart_municipi, mart_electoral, …)
   │  semantic/metrics.yml (contracte)
   ├──► data/web/*.json    → web estàtic (SvelteKit, riusdegent.cat)
   └──► IA (FastAPI)        → text→SQL traçable (Brúixola)
```
- **Determinista i reproduïble:** els connectors són idempotents; la materialització dels parquets via DuckDB fa *cast* explícit; re-córrer reescriu sense efectes col·laterals.
- **Clau de *join*: `ine5`** (codi INE de 5 dígits) a tot arreu.
- **La IA mai escriu SQL.** Tria una mètrica + una intenció d'uns enums derivats del contracte; un *router* determinista construeix la consulta parametritzada *read-only* i n'adjunta la procedència. Les *guardrails* (només `SELECT`/`WITH`, només taules `mart_*`, mai `raw`) es mantenen sigui quin sigui el *backend*.

### 2.3 Dues trampes d'integritat (verificar SEMPRE abans de *joins*)
- **Gósol `25100` ≠ `25101`** (que és la Granadella). Codis veïns, municipis diferents.
- **`81014` és un codi de *comarca*, no de municipi** (el Consell Comarcal del Berguedà). `codi[:5]` d'un òrgan supramunicipal NO és un municipi → es detecta per nom de l'òrgan, no pel codi (rellevant al cabal, §7).

### 2.4 Reproductibilitat per a open data
- Totes les fonts primàries són **dades obertes** (Dades Obertes de Catalunya, Idescat, OpenStreetMap). Cap dada privada ni PII al producte.
- Cada indicador derivat documenta el seu `origin_source` (la font oficial de la qual penja).
- **Llicències:** la majoria són Dades Obertes de Catalunya (reutilització amb atribució); OpenStreetMap és **ODbL** (atribució + compartir-igual) → a tenir en compte en publicar derivats. Vegeu §3.

---

## 3. Catàleg de fonts

| Font (clau) | Organisme | Producte | Dataset / accés | Granularitat | Cobertura | Llicència |
|---|---|---|---|---|---|---|
| `idescat_emex` | Idescat | El municipi en xifres (EMEX) / Cens 2021 | `api.idescat.cat/emex/v1/dades.json?id={codi6}` | Municipi (i secció) | Padró anual des de 1998; Cens 2021 | Idescat, atribució |
| `residus` | Agència de Residus de Catalunya (ARC) | Estadístiques de residus municipals (**totes les fraccions**, inclòs vidre) | Socrata `69zu-w48s` | **Municipi** (`codi_municipi`=ine5) | **2000–2024**, anual | Dades Obertes Catalunya |
| `icaen_consum` | ICAEN | Consum elèctric per municipis i sectors | Socrata `8idm-becu` | **Municipi × sector** (`cdmun`=ine5) | **2013–2024**, anual | Dades Obertes Catalunya |
| `icaen` | ICAEN | Certificats d'eficiència energètica | Socrata `j6ii-t3w2` | Municipi | — | Dades Obertes Catalunya |
| `rtc` | Generalitat (Registre de Turisme) | Establiments d'allotjament turístic | Socrata `t2h3-cgys` | Municipi | Mensual | Dades Obertes (conté dades de titular → RGPD) |
| `osm_overpass` | OpenStreetMap | POIs de restauració (`amenity=restaurant\|bar\|cafe\|...`) | Overpass API (`overpass-api.de`, sense auth) | Punt → municipi (punt-en-polígon) | *snapshot* | **ODbL** (atribució + compartir-igual) |
| `ACA` (cabal) | Agència Catalana de l'Aigua | Estat de sequera per unitat d'explotació i municipi | Socrata `i5n8-43cw` | **Municipi / unitat d'explotació** | **2021–2025** | Dades Obertes Catalunya |
| `contractació` (cabal) | Sector públic (PSCP) | Contractes menors / adjudicacions | Socrata `ybgg-dgi6` | Òrgan (municipal/comarcal) | — | Dades Obertes Catalunya |
| `electoral` | Generalitat | Processos electorals — vots | Socrata `ntc4-rnwr` | Municipi | Parlament 2017–2024 | Dades Obertes Catalunya |

**Fonts explorades i descartades honestament per al pilot** (no municipals o no obertes): pernoctacions EOH (només marca turística «Pirineus»); taxa turística municipal `q4sr-68c3` (exclou explícitament Berga i Castellar); consum d'aigua en volum (`2gws-ubmt`, només comarcal); mobilitat mòbil INE (cel·les ≥5.000 hab, Castellar es dilueix); IMD de trànsit (per estació d'aforament, no municipi); visitants d'equipaments (Tren del Ciment, Museu del Ciment — dada dura però manual i només per a pocs municipis → s'usa com a **ancoratge de calibratge**, no com a sèrie).

---

## 4. Pilar 1 — catàleg d'indicadors (mart_municipi / mart_electoral)

Tots a `mart_municipi` tret de la política (`mart_electoral`). Procedència: **M** = mesura oficial directa · **D** = derivat/inferència propi (amb `origin_source`).

### 4.1 Demografia i vivenda
| Indicador | Def. | Fórmula | Font | Proc. |
|---|---|---|---|---|
| `poblacio` | Població empadronada | directe | Idescat EMEX (2025) | M |
| `hab_total` | Parc total d'habitatges (Cens 2021) | directe | Idescat (2021) | M |
| `hab_principal` | Habitatges de residència habitual | directe | Idescat (2021) | M |
| `hab_noprincipal` | Secundàries + buides (senyal de 2a residència) | directe | Idescat (2021) | M |
| `pct_noprincipal` | % no principal sobre el total | `hab_noprincipal/hab_total*100` | Idescat | D |
| `hab_per_hab` | Sobredimensió del parc / població | `hab_total/poblacio` | Idescat | D |
| `index_envelliment` *(planned)* | 65+ per 100 de 0-14 | `pob_65/pob_0_14*100` | Idescat | M |

### 4.2 Turisme
| Indicador | Def. | Fórmula | Font | Proc. |
|---|---|---|---|---|
| `rtc_total` | Allotjaments turístics reglats | directe | RTC (2026) | M |
| `rtc_hut` | Habitatges d'ús turístic | directe | RTC | M |
| `rtc_per_1000hab` | Intensitat turística reglada/càpita | `rtc_total/poblacio*1000` | — | D |
| `rtc_per_100hab_viv` | Penetració en el parc | `rtc_total/hab_total*100` | — | D |
| `restauracio_estab` | Locals de restauració (CCAE-56) mapejats a OSM | compte de POIs (punt-en-polígon) | OSM/Overpass (2026) | M* |
| `restauracio_per_1000hab` | Densitat de restauració/càpita | `restauracio_estab/poblacio*1000` | OSM | D |

\* `restauracio_estab` és una **mesura** (compte real), però OSM **infra-mapeja el rural** → és un **mínim observat, no un cens** (vegeu §5.6 i §8).

### 4.3 Senyals físics de pressió (inputs de les capes)
| Indicador | Def. | Fórmula | Font | Proc. |
|---|---|---|---|---|
| `kg_hab_any` | Residus per habitant empadronat (càrrega real) | directe | ARC (2024) | M |
| `kwh_hab` | Elèctric domèstic/hab (senyal de pernocta, L1) | `consum_domestic/poblacio` | ICAEN (2024) | M |
| `vidre_hab` | Vidre/hab (proxy d'hostaleria, L3) | `vidre_t*1000/poblacio` | ARC (2024) | M |

### 4.4 Energia
| `pct_icaen_EFG` | % certificats E-G (potencial de rehabilitació) | `EFG/total*100` | ICAEN | D |

### 4.5 Índex IETR (vegeu §6)
| `IETR` | Exposició turística-residencial 0–100 | `0.5*A_resid + 0.5*B_turis` (min-max winsoritzat) | datapoble | D |
| `IETR_rank` | Posició (1 = màxima) | `rank(IETR desc)` | datapoble | D |

### 4.6 Indicador estrella — model de 3 capes (vegeu §5)
L1 (pernocta): `poblacio_pernocta_est`, `gap_pernocta`, `gap_pernocta_pct` · L2 (càrrega): `carrega_total_est` · L3 (turisme): `index_turisme` · bandera: `confianca`. Més claus de **compatibilitat** (model anterior d'una sola capa, conservades i reenquadrades): `poblacio_real_est` (= càrrega), `gap_abs`, `gap_pct`, `poblacio_real_rel`.

### 4.7 Política (`mart_electoral`, lectura ecològica)
| Indicador | Def. | Font | Proc. |
|---|---|---|---|
| `pct_indep` | % bloc independentista / vot vàlid | electoral (2024) | M |
| `pct_esquerra` | % bloc d'esquerra / vot vàlid | electoral (2024) | M |
| `pct_extrema_dreta` *(planned)* | % extrema dreta (Vox + Aliança Cat. + PxC) | electoral (2017–2024) | M |
| `guanya` | Candidatura més votada | electoral (2024) | M |

> **Nota política:** la lectura és **estrictament ecològica** (sobre el municipi, mai sobre persones; falàcia ecològica declarada) i **volàtil als micromunicipis** (N petit). Al web públic, aquestes mètriques **no es destaquen al Resum** (decisió editorial de no editorialitzar); es documenten de forma neutra a la metodologia. Vegeu la pregunta oberta §10.9.

---

## 5. L'indicador estrella — el model de 3 capes

### 5.1 La volta de rosca
El padró no veu qui omple un municipi sense constar-hi; però «qui l'omple» no és una sola cosa. **Tres senyals físics independents** capten coses diferents:

| Senyal | Font | Què capta |
|---|---|---|
| **Residus** kg/hab/any | ARC | càrrega **TOTAL** (residents + 2a residència + pernocta + **excursionistes de dia** + part de comerç) |
| **Elèctric domèstic** kWh/hab | ICAEN | qui hi **DORM** (l'excursionista de dia no fa servir l'electricitat de casa) |
| **Vidre** kg/hab/any | ARC (fracció) | activitat d'**hostaleria** (ampolles de bar/restaurant = visitants) |

### 5.2 Les bases residencials
La **base** és la generació/consum d'un resident «normal», calculada de les **viles de vall poc turístiques** (IETR < 5, ponderada per població):
`BASE_residus = 410 kg/hab` · `BASE_elèctric = 1.224 kWh/hab` · `BASE_vidre = 26,5 kg/hab`. (Parametritzables: a escala Catalunya, **una base per comarca** — vegeu §10.4.)

### 5.3 Les tres capes
- **L1 · Població real estimada (qui pernocta)** — *la signatura «població invisible»*
  `poblacio_pernocta_est = round(padró × kWh_hab / 1224)` ; `gap_pernocta = poblacio_pernocta_est − padró` ; `gap_pernocta_pct = gap_pernocta / padró`.
  El *gap* és la gent que **dorm** al territori sense constar: residents no registrats, segones residències, turisme que pernocta. **Això sí que és «població».**
- **L2 · Càrrega humana total**
  `carrega_total_est = round(padró × kg_residus_hab / 410)`.
  La pressió humana **total**, **inclosos els excursionistes de dia** i part del comerç. **No en diem «població» — en diem «càrrega».** Sempre ≥ L1.
- **L3 · Pressió turística (hostaleria)**
  `index_turisme = z-score comarcal de (vidre_hab) → escala 0–100` (50 = municipi mitjà del Berguedà).
  Intensitat d'**activitat de visitants**. **No és població; és pressió turística**, i és **relativa a la comarca**.

### 5.4 Validació sobre dades reals (2024)
| Municipi | Padró | L1 pernocta | L2 càrrega | L3 turisme | Lectura |
|---|--:|--:|--:|--:|---|
| **Gósol** | 207 | **+87 %** | 535 | **100** | hi dorm molta gent (2a res.) **i** màxima hostaleria → poble turístic ple |
| **Castellar de n'Hug** | 166 | +31 % | 397 | 84 | vidre alt però menys pernocta → **el poble d'excursió de dia** |
| **Saldes** | 301 | +86 % | 681 | 71 | segona residència + hostaleria |
| **Berga** | 17.539 | ≈ 0 % | 19.626 | ~27 | capital: població de residents |

### 5.5 El *catch* (rigor abans que la xifra bonica)
Vam provar de fer la capa turística com a simple **resta** (càrrega − pernocta), però als extrems donava disbarats: a **Berga** sortia +2.454 (és **residu COMERCIAL** de botigues, no excursionistes) i a les viles de vall sortia negatiu (artefacte de bases). Per això la capa turística surt del **vidre** (senyal net d'hostaleria), **no de la resta**.

### 5.6 Validació externa de L3 amb un 2n proxy independent (restauració)
El vidre mesura **activitat** (ampolles consumides); la restauració, **capacitat** instal·lada (stock de locals). Són dos senyals de naturalesa diferent. Recompte d'**OSM/Overpass** (assignat al municipi per **punt-en-polígon** amb la geometria real), validat:
- **Spearman(restauració/1000 hab, vidre_hab) = 0,544** (p<0,01, N=31).
- **Spearman(restauració/1000 hab, index_turisme) = 0,539** (p<0,01).
- Coincideixen als extrems esperats: Gósol 29,0/1000 i Castellar 18,1 a dalt; **Berga #1 absolut** (28 locals) però **#24/31 per càpita** (1,60).

**El límit, sense maquillar:** OSM **infra-mapeja el rural** → **6 micromunicipis surten amb 0 locals** tot i tenir vidre alt; és **buit de mapejat, no absència real**. Idescat (CCAE-56) oficial **no és municipal per API oberta** (secret estadístic). Per honestedat cartogràfica, al mapa aquests 0 es pinten com a **«sense dada»**, no com la classe més baixa.

### 5.7 Honestedat de la capa (innegociable)
- Tot és **inferència, no cens** → es comunica com a **rang** + procedència porpra.
- L'**elèctric** està confós per la **calefacció de llenya/gas** a muntanya (consum baix malgrat presència → p. ex. Castellar de n'Hug surt amb confiança baixa), per la mida de la llar i per l'eficiència → no es pondera igual que els residus (és **corroborador**, no senyal primari).
- Els **residus** de les viles porten part de comerç (sostre de la base).
- El **vidre** és un *proxy* d'hostaleria, **relatiu** (z-score), i **anual** (no capta estacionalitat).
- **Bandera `confianca`** (`alta`/`mitjana`/`baixa`): baixa als micromunicipis (<75 hab) i on els senyals **divergeixen**.

---

## 6. L'índex IETR (exposició turística-residencial)

- **Què és:** exposició **estructural** (stock) a la pressió turística-residencial, relativa a la distribució (0 = mín, 100 = màx). **No** és pressió realitzada.
- **Fórmula:** `0.5 × A_resid + 0.5 × B_turis`, components min-max **winsoritzats**, **pesos iguals**.
- **Validació externa:** **Spearman(IETR, residus kg/hab/any) = 0,87** sobre 31 municipis — la càrrega física real correlaciona fort amb l'exposició estructural. Castellar de n'Hug #1 (89,4); Berga #31 (0,3).
- **Robustesa:** Spearman > 0,97 a canvis de normalització i de pesos.
- **Límit:** és relatiu a la distribució (no un valor absolut) i estructural (capacitat, no ocupació).

---

## 7. Pilar 2 — el cabal (rastres administratius)

**Tesi:** quan un fenomen no té dataset net, el seu **rastre** sí que existeix — algú ha hagut de *contractar* el servei, *declarar* una restricció. És el principi dels *kg de residus* (proxy de població fantasma) **generalitzat a qualsevol rastre**. Tot es normalitza a una taula única d'**events** (una fila = un senyal), amb la frontera **dada/inferència** explícita (`categoria = fet` vs `inferencia`; `confianca` 0–1 sobre el tema inferit).

### 7.1 Rastre 1 — contractació pública
- Font: PSCP via Socrata `ybgg-dgi6` → **1.295 events** al pilot (Berga 577, Castellar 23, **Consell Comarcal 695**).
- Tema (`tipus_senyal`) inferit per **taxonomia CPV** (codi oficial; confiança 0,9) amb *fallback* per paraules clau (0,6); ~48 % dels contractes no porten CPV → el calaix `altres` és gran a propòsit (no inventem tema; refinament fi = feina d'LLM, pendent).
- **Lliçó supramunicipal:** els micromunicipis **no contracten** els seus serveis (Castellar té 23 contractes i cap de turisme propi, tot i ~50.000 visites/any a 166 hab); el seu rastre viu al Consell. Es marca `ambit` (`municipal`/`comarcal`/`supramunicipal`) perquè la convergència pugui repartir el senyal comarcal als micromunicipis.

### 7.2 Rastre 2 — sequera (ACA)
- Font: ACA `i5n8-43cw` → **398 events** al pilot. Cada **canvi d'estat** de sequera (normalitat → prealerta → alerta → excepcionalitat → emergència) per municipi/data és un rastre administratiu net (l'administració declara una restricció).
- **Granularitat municipal completa:** **31/31** municipis del Berguedà; INE6→INE5 net (cas Gósol verificat). `confianca` **ordinal per severitat** (normalitat 0,1 → emergència 1,0). Arc de Berga verificat (excepcionalitat mai-23 → normalitat mar-25).
- **Frontera dura:** la sequera es declara per **unitat d'explotació (UE)** — al Berguedà, **3 UEs**. Dins d'una mateixa UE la trajectòria de severitat és **idèntica** → la sequera **no discrimina entre municipis de la mateixa UE**. Aporta el *denominador de tensió de la zona*, no la variació municipal fina.

### 7.3 Motor de convergència — i un «no» honest
Idea: creuar els dos rastres (contractació = **anticipació**; sequera = **realització**) amb el senyal turístic validat (`index_turisme`) per municipi, per provar la hipòtesi que la **pressió turística co-ocorre amb tensió hídrica**.

**Resultat: la hipòtesi NO es confirma al Berguedà**, i no l'hem forçada:
- Quadrant «alt turisme × alta sequera»: només **4/31**, i **cap fiable** (tots micromunicipis amb `index_turisme` saturat i confiança baixa).
- **Spearman(turisme, sequera) = −0,28** (−0,54 ponderada per població) → s'**inverteix** lleugerament.
- **Per què (geografia):** el turisme es concentra a la **capçalera del Llobregat** (Pirineu: Gósol, Castellar, Saldes), justament **on neix l'aigua i menys sequera hi va haver**; la sequera forta és al **corredor mitjà i baix** (pic d'emergència), on viuen els pobles **poblats i poc turístics** (Berga, Gironella, Avià, Puig-reig). **Berga és el cas net:** molta tensió hídrica, poc turisme.

L'enginy és **reutilitzable** (es reaprofita canviant els parquets d'entrada); el «no» és una troballa sobre el Berguedà, no necessàriament sobre altres comarques (costa, Pirineu d'estacions). Aquest output és **intern** de moment (no es publica al web).

---

## 8. Fronteres honestes (transversal)

- **Inferència vs mesura:** els senyals físics (residus, elèctric, vidre, recompte de locals) són **mesures**; les capes de població/càrrega/turisme i els *gaps* són **inferències** graduades. Es marca a cada xifra.
- **Lectura ecològica:** tot parla del municipi, mai d'individus. La falàcia ecològica es declara (capa política especialment).
- **Secret estadístic:** als micromunicipis molts datasets amaguen valors; el consum elèctric domèstic és notable perquè **hi sobreviu** fins a Castellar (166 hab), a diferència d'altres sectors.
- **Bandera de confiança:** baixa als micromunicipis i on els senyals divergeixen.
- **Infra-mapeig d'OSM:** el recompte de restauració és un **mínim observat**, no un cens.
- **Gaps com a ràtio amb signe:** `gap_pernocta_pct`/`gap_pct` són **fraccions 0–1 amb signe** (Castellar +0,31 = +31 %; Berga pot ser negatiu), no escala 0–100 — es formaten amb signe explícit (`+31 %`, `−2 %`).
- **Estacionalitat:** **no existeix** sèrie infra-anual × municipal oberta per al pilot (residus i elèctric són anuals; les pernoctacions només per marca «Pirineus»). És el «no» honest principal de l'eix presència.
- **Mètriques de compatibilitat:** les claus del model anterior d'una sola capa (`poblacio_real_est`, `gap_abs`, `gap_pct`, `poblacio_real_rel`) es conserven **reenquadrades** (ara són càrrega, no població) per no trencar consumidors; estan marcades com a tals.

---

## 9. Reproductibilitat i accés

- **Repositori:** monorepo públic (`packages/{ingestion,transform,ai,web,design-system,signals}`, `semantic/metrics.yml`, `data/{marts,events}`, `docs/`).
- **Web:** **riusdegent.cat** — Resum comarcal, Mapa (coroplètic MapLibre, 7 indicadors), Metodologia pública, **Glossari** (generat des del contracte: cada terme amb definició, font, procedència i caveat) i **Pregunta-li** (IA traçable, en preparació). *(Pre-llançament: `noindex` actiu fins a obrir-ho.)*
- **IA traçable:** una pregunta en llenguatge natural → SQL parametritzat *read-only* sobre els marts → resposta + **procedència** (font, data, fórmula i **la consulta SQL exacta**) o un **refús** amb motiu. Provada *offline* sobre dades reals (p. ex. «Quina relació hi ha entre l'IETR i els residus?» → Spearman 0,87, amb fórmula i font).

---

## 10. Preguntes obertes (on volem el teu criteri)

1. **Calibratge extern.** Les estimacions de població són *proxies* sense ancoratge dur. L'únic nombre dur d'excursionisme que tenim és el de **visitants d'equipaments** (Castellar: Tren del Ciment ~29.000 + Museu del Ciment ~21.000 el 2024, a un poble de 166 hab). Com construiries un **factor de calibratge** «població real / padró» a partir d'un sol ancoratge dur, i com el validaries?
2. **Normalització del proxy elèctric.** `kwh_hab` divideix per habitant; però el consum domèstic també puja amb renda, superfície i nombre de llars, i baixa amb calefacció no elèctrica. Normalitzaries per **habitatge** (`kwh/hab_total`) en comptes de per habitant? Com separaries «més presència» de «llars més grans/riques»?
3. **Estacionalitat absent.** No hi ha cap sèrie infra-anual municipal oberta. És defensable fer servir **Wikipedia pageviews / Google Trends** només per a la **forma de la corba** (quan ve la gent), ancorada a un dur? O és afegir soroll?
4. **Bases per comarca (escala Catalunya).** Les bases residencials (410/1224/26,5) surten de les viles de vall del Berguedà amb IETR<5. A escala Catalunya pensem en **una base per comarca**. Com fixaries aquestes bases de manera robusta i comparable entre comarques molt diferents (costa vs Pirineu vs àrea metropolitana)?
5. **z-score comarcal vs absolut (L3).** `index_turisme` és relatiu a la comarca (50 = municipi mitjà). Això fa que **no sigui comparable entre comarques**. Val la pena una versió absoluta (vidre/BASE_VIDRE)? Com comunicaries que «50» vol dir coses diferents a comarques diferents?
6. **El marc de convergència (cabal).** El «no» de turisme×sequera, és senyal que el **marc** de convergència és fluix, o només que la **geografia del Berguedà** l'inverteix? Quines parelles de rastres tindrien més sentit provar primer?
7. **Pesos de l'IETR.** 0,5/0,5 (resident/turístic). És robust a pesos (Spearman>0,97), però hi ha una justificació millor que «pesos iguals per defecte»?
8. **Tractament de l'infra-mapeig d'OSM.** Pintar el 0 d'OSM com a «sense dada» (no com a mínim de l'escala) és la decisió honesta? Hi ha una manera millor de comunicar «mínim observat»?
9. **Lectura ecològica i capa política.** Com comunicaries responsablement indicadors electorals municipals (amb la falàcia ecològica i la volatilitat de N petit) en un observatori obert? Els inclouries a una IA de preguntes obertes, o els refusaries?
10. **Llicències i derivats.** Barregem fonts amb llicències diferents (Dades Obertes de Catalunya amb atribució; **OSM amb ODbL, compartir-igual**). Quines obligacions de llicència té el *dataset derivat* (`mart_municipi`) i com el publicaries net?

---

*riusdegent · «Dades per entendre com s'habita el territori». Aquest dossier és viu: cada esmena teva el millora. Gràcies per mirar-lo amb ulls crítics — és exactament el que necessita.*
