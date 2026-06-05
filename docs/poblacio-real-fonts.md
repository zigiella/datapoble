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
- [ ] Explorar si l'ARC publica fracció **RESTA** estacional (no comprovat) — donaria senyal intra-anual que el total anual amaga.

## Enllaços
- `docs/data-sources.md` (Experiment 0 — registre general; aquest doc el reenfoca)
- ARC residus `69zu-w48s` · ICAEN elèctric `8idm-becu` · RTC `t2h3-cgys` · IMD `xsvx-ym46`
- ACA: `aca.gencat.cat/…/dades-obertes` (consum **comarcal** `2gws-ubmt`; estat sequera `i5n8-43cw`)
- Idescat EMEX: `api.idescat.cat/emex/v1/dades.json?id={codi6}`
