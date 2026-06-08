# Feedback de la consultora i re-planificació · riusdegent

*Processat per Talaia · 2026-06-08. Síntesi del feedback d'una consultora externa (anàlisi de dades + open data) sobre el dossier (`docs/dossier-dades-metodologia.md`), i el roadmap re-planificat que en surt. **Aquesta és la base de treball — no confiem en la memòria de sessió: viu aquí.***

## 0. Origen
La consultora va rebre el dossier i va tornar **4 documents** (a `Desktop/CAJON/`):
- `consultoria-dades.md` — revisió metodològica del model (el principal).
- `licitaciones.md` — licitacions com a capa d'**intel·ligència institucional**.
- `nacionalidad.md` — origen/nacionalitat com a **transformació demogràfica**.
- `digital.md` — **maduresa digital + IA** territorial.

Decisions de Bea (2026-06-08): **(1)** arrencar per la Fase 1; **(2)** seccions web noves prioritàries = **Licitacions + Demografia**; **(3)** adoptar el reframe; **(4)** formalitzar-ho aquí.

## 1. El reframe — NORD COMUNICATIU ADOPTAT
> **riusdegent no ven «quanta gent hi ha», sinó «quin denominador hauria de fer servir un municipi per governar-se».**

El padró menteix per omissió. El projecte passa de *comptador de població* a observatori de **metabolisme i capacitat institucional**, amb un eix nou: **pressió vs. capacitat de resposta** (dos pobles amb la mateixa pressió poden invertir-hi o aguantar-la amb cinta aïllant). El filo polític: «qui sosté càrregues de ciutat amb finançament de poble».

## 2. Veredicte de la consultora
- **Valida:** la separació de 3 capes (no una xifra totèmica); el contracte semàntic com a producte; la IA acotada (enums+SQL); els «no» honestos (vidre en comptes de resta, OSM-0 com a «sense dada», convergència que falla i es documenta).
- **Crítica forta (acceptada):** les **bases residencials (410/1224/26,5) són massa endògenes** (surten de viles IETR baix) → **circularitat a escala**. Cal passar de *base fixa* a **base esperada**. → *Matís de Talaia:* per fases (tipològica → covariables); no canviar una base simple per una caixa negra.
- **Ètica validada i empesa:** «no semblar més precís — el contrari: més rangs, més incertesa, més tipologies».

## 3. Bloc 1 — Endurir el model actual (FASE 1, sense fonts noves)
- **Confiança 0-100 auditable** (no només alta/mitjana/baixa): `cobertura × estabilitat_temporal × mida_denominador × concordança_senyals × penalització_outlier × qualitat_join`. Es manté l'etiqueta a la UI.
- **Doble escala** per a `index_turisme`: `turisme_rel_comarca` (posició dins la comarca) + `turisme_abs_cat` (percentil de Catalunya). *(El segon espera dades de Catalunya.)*
- **IETR dual:** `IETR_stock` (exposició estructural: habitatge no principal, HUT, places, restauració) vs `IETR_impact` (pressió realitzada: residus, vidre, elèctric residual, mobilitat). Pesos: publicar **sensibilitat** + variant **empírica** + variant **robusta** (mediana de rànquings sota moltes combinacions).
- **Residus per fracció:** vector de petjada (resto/orgànica/envasos/paper/vidre) → classificar per **PATRÓ**, no per volum.
- **Elèctric com a residu corregit marginal:** `excés_kwh = observat − esperat_residencial`; `pernocta = excés / kwh_persona_nit_MARGINAL` (consum fix vs marginal: no castigar/premiar per mida de llar).
- **Vidre doble lectura:** `vidre_hab_abs` (transparent) + `vidre_hostaleria_residual` (observat − esperat per llars/població; més útil per inferir hostaleria).
- **TIPOLOGIES amb nom** (la joia narrativa): *poble dormitori invisible · poble d'excursió · poble de 2a residència · capital de serveis · municipi buit administratiu*. El mapa diu **quin tipus de pressió**, no «més/menys».
- **`anchors.yml`:** calibratge amb **moltes àncores heterogènies** (visitants d'equipament, aforaments de parking, comptadors de sender, pernoctacions, aigua, esdeveniments), cadascuna amb `unit/conversion/scope/confidence`. Castellar calibra **excursionisme d'equipament**, NO «població real» (visites → persones-hora → hab-equivalents-any, amb rang).
- **Validació discriminant** (no només convergent): un índex de pernocta ha de correlacionar més amb elèctric que amb vidre; un d'excursió més amb vidre/parking que amb elèctric. + controls negatius (munis similars sense atractius turístics coneguts).

## 4. Bloc 2 — Capes / seccions NOVES (web)

### 4.1 🏛️ Licitacions com a intel·ligència institucional *(secció prioritària #1)*
«Una licitació és una **confessió administrativa**.» El cabal evoluciona de *rastre lateral* a *capa de capacitat institucional*.
- **Taxonomia pròpia** (no només CPV): `tema_administratiu`, `fenomen_inferit`, `tipus_accio`, `actiu_afectat`, `poblacio_objectiu`, `escala_impacte`, `confiança`.
- **Caràcter del senyal:** `ordinari | reforç | emergència | transformació | promoció | diagnòstic` (separar metabolisme normal de tensió).
- **Lectura temporal** (seqüència pre/post event → distingir qui **previu** de qui **apaga incendis**).
- **Repartiment supramunicipal DECLARAT:** `allocation_method ∈ {directe_textual, per_poblacio, per_carrega, per_indicador, igualitari, no_assignable}` + confiança. Resol el problema del Consell Comarcal (avui `ine5=NULL`).
- **Arquitectura multi-taula:** `contracts_{raw, normalized, entities, signals, allocated}`.
- **5 indicadors inicials** (no 40): `intensitat_contractacio_turisme_per_carrega` · `intensitat_contractacio_aigua_per_estres` · `dependencia_supramunicipal` · `contractacio_digital_operativa` · `gap_pressio_resposta`.
- **NLP amb morrió** (auditable): normalitzar → entitats → tema → explicació curta → validar mostra → precisió per categoria → regles deterministes per a sensibles. `contract_signal_type ∈ {evidencia_directa, proxy_fort, proxy_feble, només_context}`.
- **Sprint metodològic:** taxonomia 12-15 temes → classificar **300 contractes a mà** → ajustar regles+LLM → mesurar precisió → 5 indicadors. **Ja tenim 1.295 events** (PSCP `ybgg-dgi6`). El més riusgent-native.

### 4.2 👥 Composició i arrelament (origen) *(secció prioritària #2)*
**Transformació demogràfica**, MAI «extranjería» (paraula «podrida de fàbrica»).
- Separa: **nacionalitat** / **país de naixement** / **evolució temporal**.
- Indicadors: `pct_nascuda_estranger` (millor que nacionalitat) · `bretxa_naturalitzacio` · `delta_5/10y` (el vèrtigo, no la foto) · `diversitat_origen` (Shannon) · `rejoveniment_migratori` · `dependencia_migratoria` · `gap_habitanza_vs_origen` (tipologia 2×2).
- **Índex d'arrelament operatiu:** distingir qui **USA** / qui **DORM** / qui **ARRELA** al territori.
- **Dades DISPONIBLES** (INE/Idescat: padró per nacionalitat + lloc de naixement, sèrie municipal; migracions).
- **Frontera IA dura:** bloquejar inferències individuals/causals/ètniques (com la política). Permès: «quins munis han augmentat més la població nascuda fora en 10 anys?». Rebutjat: «els marroquins voten X?». Llindar mínim N + agrupació per grans àrees als micromunicipis.

### 4.3 💻 Maduresa digital + IA *(fase posterior — més inferencial)*
Capes: infraestructura (cobertura SETELECO), administració digital real (**AOC IMD**, fort a Catalunya), economia digital, ciutadania digital, dades obertes/**legibilitat-màquina**, contractació digital/IA (el cabal), exposició laboral IA, formació. Índexs: IMDT, IA probable, automatització pública, **bretxa digital**, legibilitat IA. Pregunta: «quins territoris estan preparats per viure amb màquines, quins només han comprat tecnologia, i quins seran digitalitzats contra la seva població».

### 4.4 🏠 Capa social (vivenda/renda) *(fase posterior — l'aresta política)*
`esforç_lloguer` · `expulsió_jove` (caiguda 25-39 + puja lloguer + augment HUT) · `subfinançament_operatiu` (despesa/càrrega-real vs despesa/padró). «La turistificació no es veu només al vidre; es veu en qui pot quedar-se.»

## 5. Bloc 3 — Escala Catalunya, re-enfocada
**NO** comarca-a-comarca pla → primer **tipologies territorials** (litoral turístic, litoral metropolità, Pirineu, interior rural, capital comarcal, àrea metropolitana, agroindustrial) → **bases jeràrquiques** (Catalunya → tipus → comarca → municipi). La **closca del mapa (Fase 0, en marxa)** és visual/navegació; les **dades a escala** depenen d'aquesta tipologització.

## 6. Les 10 respostes de la consultora (a les preguntes obertes del dossier §10)
1. **Calibratge:** no un factor global d'una àncora → model d'`anchors.yml`. Castellar = excursionisme d'equipament, no població real.
2. **Normalització elèctrica:** 3 vistes (per hab / per llar principal / **residual corregit per clima**). Per a pernocta, només la 3a.
3. **Estacionalitat:** Wikipedia/Trends només com a **forma de corba**, ancorada a un dur, confiança baixa/mitjana; millor per a atractius amb nom propi.
4. **Bases per comarca:** **jeràrquiques** (Catalunya → tipus territorial → comarca → municipi). La comarca sola és massa administrativa.
5. **z-score vs absolut:** mantenir **tots dos** («alt dins el Berguedà» + «percentil X de Catalunya»).
6. **Cabal:** el «no» turisme×sequera no debilita el marc; **provar abans** turisme×residus · 2a-residència×elèctric · excursió×parking/residus · sequera×contractes-aigua · residencial×llicències · centralitat×contractes-supra.
7. **Pesos IETR:** iguals = principi democràtic d'ignorància; publicar sensibilitat + variant empírica.
8. **OSM:** 0 com a «sense dada» correcte + afegir **`osm_completeness_score`** (POIs esperats vs observats).
9. **Política:** incloure amb 3 límits (lectura municipal · avís N petit · bloqueig d'inferències individuals/causals a la IA). *(Ja fet en part: la porta política, PR #52.)*
10. **Llicències:** separar el dataset en capes — **`mart_municipi_core`** (sense OSM; Dades Obertes/Idescat) + **`mart_municipi_osm`** (ODbL, atribució).

## 7. Referents externs a robar sense pudor
França (taux de fonction touristique, llits/hab) · Itàlia (ISPRA població turística equivalent via residus) · Espanya (INE/Dataestur mòbil, com a **validació** agregada, no insum central) · Seül (living population) · EUA (LandScan, OnTheMap població **diürna** — Berga = centralitat comarcal, no tot turisme) · Amsterdam (carrying capacity + **habitabilitat**, quadrants) · Venècia/Dubrovnik (rastre operatiu) · ETIS/UN Tourism (indicadors **socials** de sostenibilitat — al projecte li falta el rastre social).

## 8. Disciplina (innegociable)
- **Poques mètriques sòlides, no 40.** Filtrar per **dada-disponible-municipal-oberta-JA**. Moltes de les ~100 proposades depenen de dades que NO tenim a escala municipal (renda fina, cadastre, mòbil, EDAR) → no córrer.
- Cada capa nova manté la frontera **mesura / inferència / interpretació** + procedència + confiança.
- Les capes derivades d'**OSM**, separades + **ODbL**.

## 9. Roadmap re-planificat (l'ordre acordat amb Bea)
1. **FASE 1 — endurir** *(en marxa)*: confiança 0-100 · doble escala · IETR dual · **TIPOLOGIES** · sensibilitat de bases (leave-one-out, ±10/20 %) · incorporar les 10 respostes a la metodologia pública.
2. **Sprint LICITACIONS** (cabal-intel·ligència) **+ Capa DEMOGRAFIA** (origen/arrelament) — les 2 seccions web noves.
3. **Bases esperades** (tipològiques → covariables) lligat a **escala Catalunya**.
4. **Digital + Social** — després.

— Talaia 🌊
