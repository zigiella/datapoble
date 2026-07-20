# Cua — reconducció (rumbo decidit 2026-06-27)

*Mètode: **Cambium Charter v0.5**. Es treballa de dalt a baix; cada tasca = un PR. Cada **fase** és
publicable per si sola.*

> **🏛️ TRACK ACTIU (2026-07-16): datapoble per a ajuntaments — `docs/spec-ajuntaments-v1.md`**
> (direcció de Bea, redacció Marea #239, ADOPTADA amb esmenes per Talaia — §10 de l'spec és vinculant).
> **Demo Magda (Diba): SENSE DATA (decisió de Bea, 2026-07-16)** — es valorarà presentar-la **quan sigui
> online i funcionant**, no contra un calendari. Guió i prerequisits a `docs/ajuntaments/demo-diba.md`.
> **El que ven la demo és el número** (recall del radar + KPI d'abstenció del xat), verificat per Talaia
> — mai un titular sense el seu caveat.
> **NO-OBJECTIUS VINCULANTS d'aquesta v1:** butlletí mensual · cartell A4 · radar per a entitats ·
> fases 4–5 del geo-rag · escala Catalunya · cap personalització que amagui indicadors incòmodes.
> Qualsevol excepció passa per Bea.
>
> **Track R (radar) i Track D (dashboard) corren EN PARAL·LEL; Track X (xat) seqüenciat rere el
> tancament de la passada generativa del geo-rag — que JA ESTÀ FET (#232–#238): X1 desbloquejada.**
> - **R0 (Talaia)** — contractes C3 (fitxa subvenció + perfil `actiu:`) + C4 (banc del radar: 20
>   convocatòries, etiquetes de Bea, nivells congelats DINS el contracte, recall del pipeline sencer,
>   E2 de l'spec) → després R1 (BDNS, Sondeig) · R2 (filtre, Sondeig) · R3 (semàfor Haiku, Brúixola) ·
>   R4 (workflow correu — destinataris: Bea) · R5 (CIDO) · R6 (memòria on-demand). Experimental NOMÉS
>   la Pobla (08166) via `actiu:`; Castellar (08052) i `_default` dorments. Porta de sortida: banc C4
>   aprovat + 1 mes validació paral·lela + vistiplau de Bea.
> - **D0 (Talaia)** ✅ — contractes C1 + C2 + C6 fusionats (#242) → després **D1** (atur SEPE, Sondeig) ·
>   **D2** (HERMES selectiu) · **D4** (mart_govern + percentils) · **D5** (vista govern, Mirador).
>   **DECISIÓ DE BEA (2026-07-16): v1 va NOMÉS amb dades públiques.** `D3` (connector municipal_csv) i
>   `D6` (CSV real de la Pobla) → **FASE 2**: primer ensenyem valor amb el que tenim, després demanem
>   dades a l'Ajuntament. C2 queda com a contracte llest i **dorment** (no es toca; ja serveix per a la fase 2).
>   La selecció dels 12 KPIs (que C6 deixava oberta) és a **`docs/ajuntaments/gorra-alcalde-pobla.md`**
>   — triats per decisió que suporten, amb els números reals i els rangs comarcals. **Vot de Bea pendent.**
> - **X1 (Brúixola)** — collita C5: doctrina + gàbia RE-VALIDANT (E3, validador v2) cap a
>   `packages/ai` · X2 (activar render.yaml dorment, Trazo) · X3 (catàleg govern + preguntes suggerides).
> **El geo-rag NO es toca** (congelat com a annex de recerca fins a X1); els seus pendents propis
> (banc de confirmació de Bea · ★ · paper) queden fora d'aquesta spec (E6), seqüenciats post-demo.
>
> **ESTAT (2026-07-16): contractes C1–C6 FUSIONATS (#240–#243). Primeres tasques ESPECIFICADES amb
> àncores verificades en viu a `docs/ajuntaments/tasques-especificades.md`:**
> - **R1 (Sondeig)** — connector BDNS: API verificada (endpoint real, paginació, trampa de les
>   regions NUTS que NO cascada — sempre 49,50,51,52,53), mapa complet a la fitxa C3, fixtures→banc C4.
> - **D1 (Sondeig)** — connector atur: **FONT ESMENADA a C1 §1.1** — el Socrata de l'spec NO EXISTEIX
>   (verificat en viu); font real = CSV mensual del SEPE, amb la doctrina del «<5» = interval [1,4]
>   (mai zero silenciós) i zero-pad de codis INE.
> - **X1 (Brúixola)** — ✅ **FETA, PR obert** (bitàcola: `2026-07-16_x1-collita-geo-rag_bruixola.md`).
>   Doctrina + gàbia RE-VALIDANT a `packages/ai` (validador v2 collit byte a byte, fallback
>   determinista provat); geo-rag i politics.py intactes; pin `openai>=1.30` inalterat.
>   187 tests offline verds · 13/13 evals originals · 7/7 eval nou end-to-end.
>   **Dos forats destapats i esmenats:** (a) l'`empat` — el rànquing determinista afirmava
>   guanyadors que les dades no assenyalen (**47 municipis** empatats a `index_turisme=100`,
>   6 a `IETR=100`), i era el *fallback* de la gàbia; (b) el **caveat esborrat** — `catalog.py`
>   llegia `nota:` i el contracte escriu `caveat:` a 14 mètriques (**totes les inferències**),
>   així que «INFERÈNCIA, no cens» no arribava mai al lector.
>   **➡️ Handoff a: Sondeig** — l'empat massiu és **saturació dels índexs** (topall a 100):
>   un índex que aplana 47 municipis al cim, informa? (dades, no jurisdicció meva).
>   **➡️ Handoff a: Talaia** — el contracte fa servir dues claus per al caveat (`nota:`/`caveat:`);
>   el codi ja llegeix les dues, però unificar-ho estalviaria la propera esquerda.
> **▶️ EN MARXA (tret de sortida de Bea, 2026-07-16).** **R1 ✅ (#247, Sondeig)** · **X1 ✅ (#248, Brúixola)** —
> verificats adversarialment per Talaia i fusionats. Les tres decisions de R1, **RATIFICADES** (§ bitàcola).
>
> **🔴 COLA DE SONDEIG (per ordre; un latido = una tasca):**
> 1. **R1.5 — COMPOSICIÓ DE LA CAPA B DEL BANC C4** (nova, URGENT: desbloqueja l'etiquetatge de Bea;
>    C4 §2 v2 + R-FUNC §2). Cerca dirigida a BDNS (i CIDO si cal) **6–12 mesos enrere** per LLISTA DE
>    PROGRAMES — Catàleg Diba · OSIC/Cultura · Leader/ADRCatCentral (conv. 2026 oberta) · IDAE/
>    enllumenat · patrimoni (1,5% cultural) · camins/natura · digitalització ens locals — i **arxiu de
>    TOTES les convocatòries d'aquests programes del període** com a fixtures reals (l'objectiu és que
>    hi hagi ≥8 elegibles clares i 4–6 fronteres PER EXISTÈNCIA, no per selecció): **guarda
>    anti-pre-etiquetatge de C4 §2 — Sondeig llista programes i arxiva, NO etiqueta res; qui etiqueta
>    és NOMÉS Bea (A+B juntes)**. Re-verifica en viu les fonts del R-FUNC §2 en compondre (PUOSC
>    tancat→memòria de cicle; ADRCatCentral oberta). Afegeix les fitxes al full d'etiquetatge (segona
>    taula). Test nou de la trampa de noms: «Sant Salvador de Guardiola» (Bages) ≠ «Guardiola de
>    Berguedà» (#9–10 de la capa A ho exerceixen).
> 2. **Saturació dels índexs** (handoff de Brúixola, X1): 47 municipis empatats a `index_turisme=100`,
>    6 a `IETR=100`. `index_turisme` ja és FORA del tauler (vot de Bea) i el xat ja no menteix; la
>    pregunta de dades queda: recalibrar o declarar el límit dels índexs compostos.
> 3. **R2** — filtre dur + puntuació de perfil (C3 + §2bis + **§6bis nou**: destinataris = claus
>    simbòliques, mai correus; validació @→error). El perfil `08166-lillet.yaml` parteix de la
>    PROPOSTA del R-FUNC §3 (pesos i cartera de Marea; la llista de projectes la valida Bea amb
>    l'Ajuntament — mentre no arribi, marcada com a proposta). `_default` i `08052-castellar`
>    dorments. NO es pot descartar per `termini: NULL`. **Requisits de dev del R-FUNC §9.1**:
>    dry-run local a directori gitignorat, fixtures rejugables, snapshot test del correu (patró
>    test_parafrasis), correu real només via workflow_dispatch [DEV].
> 4. **Esmena L1/L3 al contracte** (handoff de Mirador, #256): les notes de kwh/vidre/restauració a
>    `semantic/metrics.yml` encara citen «capa L1/L3» (el model aparcat) — reescriure-les en termes
>    oficials.
> 5. **D4 — `mart_govern` + PROCEDÈNCIA (dashboard niquelat, prioritat de Bea 2026-07-18):**
>    (a) `mart_govern` amb rangs «k de n» per LA COMARCA DEL MUNICIPI (via municipis-territori.json;
>    C6 §3; mai llista fixa; `rang`+`n_amb_dada`+data per mètrica). (b) **REGLA DE FERRO DE BEA
>    (C6 §8.1): cada xifra amb la seva font O fórmula** — l'export web (`export_web_municipis.py`)
>    ha d'EMETRE el camp `formula` del contracte (avui emet source/date/definicio/note però NO
>    formula); afegir-lo a build_metrics + al tipus MetricDef. (c) **Acabar la deprecació
>    d'`index_turisme`** (ja marcat `status: deprecated` al contracte per Talaia): treure'l dels
>    PUBLICADORS (METRIC_KEYS de l'export web + export_indicadors_cat + eval_writer) i regenerar —
>    el mart pot seguir calculant-lo. (d) **Esmena L1/L3** al contracte (handoff de Mirador, #256):
>    les notes de kwh/vidre/restauració citen «capa L1/L3» (model aparcat) → termes oficials.
>    · **D2** (HERMES selectiu, C1 §1.2) queda DARRERE de D4.
> 6. **D7 — la dada del tauler v2 ✅ FUSIONADA (#276, Sondeig 2026-07-20).** Capa de dades de les
>    esmenes E4/E5/E6/E11/E12. Bitàcola: `2026-07-20_d7-dada-tauler-v2_sondeig.md`.
>    *Verificació adversarial de Talaia abans de fusionar: els 1.894 Δ d'atur recomputats a mà des de
>    `mart_pols_mensual` (1.894/1.894 coincideixen, cap sense origen) · partició d'edat exacta (suma de
>    franges = població total als 947, residu 0; la Pobla 98+609+322+77=1.106) · 0 fletxes sense període,
>    0 «sense sèrie» sense motiu, 0 deltes colats en files sense sèrie · `--check` del nou exportador
>    present al CI (comprovat al YAML, no confiat) · cap ruta local ni secret al diff.*
>    Franges d'edat exposades (quadren als 947 i casen amb el total de CAT) · `mart_tendencia` nou
>    (Δ amb període declarat; «sense sèrie» explícit amb motiu; «<5» propagat com a interval) ·
>    `export_tauler_web.py` amb `--check` **cablat al CI el mateix dia** · frescor al contracte
>    (`actualitzacio`/`darrera_carrega`/`proces_refresc`) · `refresh-atur.yml` ampliat aigües avall.
>    **⛔ TROBALLA QUE TOMBA UNA PREMISSA: EMEX NO SERVEIX SÈRIE** (verificat en viu + doc oficial:
>    l'operació `dades` només admet `id`/`i`/`tipus`; els paràmetres temporals s'ignoren EN SILENCI).
>    Població i franges surten `sense_serie`, no per pendent d'ingesta sinó per límit de font.
>    També: el `year` de la raw d'EMEX era NULL a 12 dels 13 indicadors (l'`r` viu al node pare) →
>    esmenat al connector amb test; en surt que els vintages NO són iguals (població 2025 vs
>    habitatges 2021), que és la base de l'E5.
> 7. **Sèrie de població (desbloqueja E11 del tot)** — encuada per D7 amb la via JA VERIFICADA:
>    `idescat.cat/pub/?id=censph&n=538&geo=mun:{codi6}&f=ssv` (sèrie 1975→2025, mateix patró `f=ssv`
>    que `stg_demografia_estrangera_serie`). Cal **etiquetar la ruptura de font** (Padró/Cens/Cens
>    anual), no aplanar-la.
> 8. **UN refresc anual de pipeline sencer** (no una cron per font) — encuat per D7 amb el motiu
>    verificat: les 9 fonts anuals convergeixen a `mart_municipi`, i refrescar-ne una arrossega 4
>    marts avall + 7 verificadors/exports amb artefacte `--check`. Una cron per font deixaria la
>    cadena estale i posaria el CI en vermell. `refresh-atur.yml` va poder ser trivial només perquè
>    `mart_pols_mensual` està desacoblat a propòsit.
>    · Encuades també: sèries de residus/ICAEN/renda (les tres fonts en tenen; el pipeline n'ingereix
>      una sola foto) → desbloquejaria la tendència de 4 targetes més.
> **🚨 E7/E8 — LES LECTURES P1/P2, AUDITADES PER TALAIA (2026-07-20). La sospita de Bea es queda
> curta.** Bea: «que no estiguin basades en mètriques de les antigues». Comptat sobre
> `data/web/lectures.bergueda.json`, que és el que se serveix ARA:
> - **532 frases amb evidència · 310 (58%) citen una mètrica aparcada, deprecada o inexistent · 31
>   municipis de 31 afectats.**
> - **260 frases** citen el **model de pernocta APARCAT** (`gap_pernocta_pct` 138, `poblacio_pernocta_est`
>   104, `carrega_funcional_est` 88). Al contracte encara consten com a **vives**: el vot d'aparcar de
>   Bea (2026-07-16) va sortir de la vista de govern però **mai va baixar al contracte** → forat de
>   Talaia.
> - **32 frases** citen **`index_turisme`**, que Bea va votar deprecar i que ja és fora del tauler.
> - **110 frases** citen **claus que NO existeixen al contracte**: `pernocta_rang` (92), `etca_idescat`
>   (16), `tipus_territorial` (8). Això no és una mètrica antiga: és una **evidència fantasma**. La
>   promesa de la fitxa és «cada frase traçable fins a la font»; per a aquestes, qui estiri el fil no
>   troba res.
> **Ordre de treball (la doctrina va primer, la regeneració després):**
> - **E7a (Talaia)** — baixar al contracte el que ja s'havia decidit a la vista: marcar el model de
>   pernocta com a aparcat i resoldre les 3 claus fantasma (o existeixen i s'escriuen, o no es poden
>   citar). Definir la **regla**: *una lectura només pot citar com a evidència una mètrica viva i
>   publicable del contracte*.
> - **E7b (Sondeig, `tools/gen_fitxa.py`)** — regenerar P1/P2 sobre mètriques oficials + **guarda**
>   que faci caure el CI si una lectura cita una clau que no compleix la regla. *Sense la guarda això
>   torna: és el mateix patró que el `caveat` esborrat i que els `--check` absents.*
> - **E8 (dins de la regeneració)** — «Confiança mitjana» tal com surt avui no diu res a un lector
>   normal (esmena de Bea): el text ha d'explicar de què és la confiança i què vol dir que sigui
>   mitjana.
>
> **⚠️ D11 (Mirador) — E11 és MÉS possible del que D9 va concloure. Verificat per Talaia 2026-07-20.**
> Mirador va tancar E11 dient «el mart només té **nacionalitat**, i Bea demana nascuts fora / nascuts
> a l'estranger». **Això no és cert:** el contracte i el web JA serveixen les quatre mètriques de
> **lloc de naixement** (dimensió `origen`, totes vives): `poblacio_nascuda_catalunya`,
> `poblacio_nascuda_resta_espanya`, `poblacio_nascuda_estranger`, `pct_nascuda_estranger`.
> La Pobla, avui, a `data/web/municipis.bergueda.json`: **846 nascuts a Catalunya · 126 a la resta
> d'Espanya · 134 a l'estranger (12,12%)**. El tauler **no en pinta cap** (comprovat a `kpis.js`),
> perquè D9 va donar per fet que no hi eren.
> **La distinció importa i és exactament la que Bea demana:** 134 nascuts a l'estranger vs 9,58% de
> nacionalitat estrangera (~106 persones) NO són el mateix conjunt — qui es nacionalitza surt d'un i
> es queda a l'altre. Confondre-les és el marc que el propi contracte prohibeix.
> **Feina de D11:** pintar el lloc de naixement al bloc «Qui hi ha (i qui hi haurà)» **com a NIVELL**,
> amb la seva font. **Límit honest a declarar a la targeta:** l'**evolució** només existeix per a
> nacionalitat (finestra 2021→2025); del lloc de naixement en tenim la foto, no la sèrie — i la sèrie
> de nacionalitat **no** es pot presentar com si fos la del lloc de naixement.
> 9. **D10 — els quatre serrells que D9 ha destapat** (handoffs de Mirador, tots de dada):
>    (a) el `motiu` de `mart_tendencia` és **només en català** → ha de ser `{ca,es}` com `label`/
>    `definicio`; Mirador no el tradueix al front (seria inventar dada, i fa bé).
>    (b) **5 mètriques amb `frescor.actualitzacio: null`** i una és targeta del tauler
>    (`rtc_per_1000hab`): no és bug de l'export sinó `origin_source` absent al contracte.
>    (c) `serveis_estab` i `restauracio_estab` **no són a `mart_tendencia` ni com a `sense_serie` amb
>    motiu** — i això sí que trenca la regla: una fila que falta és INVISIBLE, un motiu es pot llegir.
>    *Verificat per Talaia: 15 mètriques al mart, aquestes dues absents. La meva verificació de D7 va
>    comprovar «cap `sense_serie` sense motiu» però no «cap mètrica del tauler sense fila» — el forat
>    era del meu test, i el va trobar Mirador.*
>    (d) **`atur_registrat` cap al catàleg servit al front.** *Esmena a l'enunciat del handoff: Mirador
>    m'ho va passar com «no és al contracte semàntic», i SÍ que hi és (`semantic/metrics.yml` L1223,
>    amb caveat i doctrina del «<5»). El que passa és que **no arriba a `data/web/municipis.*.json`**,
>    així que l'etiqueta i la font de la targeta d'atur són les dues úniques cadenes del tauler
>    escrites al codi i no llegides del contracte.* Fix: `atur_registrat` als `METRIC_KEYS` de
>    l'export web (Sondeig) → després Mirador les llegeix del catàleg (dues línies).
> **➡️ Handoff a: Talaia — RESOLT (2026-07-20), amb una troballa pitjor que l'estale.**
> `mart_electoral` i `mart_consum_electric` versionats són de l'època del pilot (31 munis / 372 files)
> i els seus models ja cobreixen 947. Sondeig no els va reconstruir a propòsit (publicaria dades
> electorals de 947 municipis com a efecte lateral d'una tasca de tauler) i **va fer bé**. Estirant el
> fil, Talaia:
> - **Consum elèctric: no s'ha de tocar.** El KPI viu del tauler no en beu (ve per `int_consum_electric_pc`,
>   desacoblat a posta) i aquest parquet és el **substrat congelat del geo-rag**, on 31 munis és
>   l'abast CORRECTE. No és estale: és pilot volgut. Cal **documentar-ho** perquè ningú el «arregli».
> - **Electoral: el problema no és l'estale.** No arriba al web (comprovat als tres JSON: cap mètrica
>   electoral), **però `mart_electoral` SÍ que és al catàleg del xat** i 3 de les seves 4 mètriques no
>   tenen `status`, o sigui que compten com a vives. El xat pot respondre preguntes electorals contra
>   un parquet de 31 municipis: per als altres 916 tornaria buit, i un buit per artefacte estale es
>   llegeix igual que un buit per «no ho sabem». Ja existeix el mecanisme per tancar-ho: la dimensió
>   `origen` està **retinguda de l'agent** amb test de regressió; l'electoral no té aquesta porta.
>   **Recomanació de Talaia a Bea: mateixa porta que `origen`, i NO reconstruir el mart** — tanca el
>   forat avui i deixa a Bea la decisió editorial de fons (**vol que el xat pugui respondre preguntes
>   electorals?**; si sí, cal decidir a part si publiquem agregats dels 947 en un repo públic).
>   **Pendent del vot de Bea; mentrestant Talaia no toca aquesta capa.** Executor: Brúixola.
>
> **🟡 COLA DE MIRADOR — D9 ✅ FETA (PR obert, 2026-07-20).** Capa de WEB de les esmenes
> E4/E5/E6/E11/E12: el tauler ja ensenya el que D7 (#276) servia i ningú veia. Bitàcola:
> `bitacora/2026-07-20_d9-superficie-tauler_mirador.md`.
> **E4** atur real (darrer mes o interval «<5», sparkline de 25 mesos i les **DUES** comparacions
> —la Pobla, juny 2026: +4 vs maig i −3 vs juny 2025—) · **E6** cap fletxa sense període, i els
> períodes surten de la dada: es RETIRA `gov_nova_delta_label` («variació 2021→»), que portava el
> període escrit al copy · **E5** frescor PER TARGETA (cadència · darrera càrrega · procés o la
> seva absència; 1 font de 10 en té) · **E12** les 4 franges d'edat al bloc A (sense `pob_65_mes`:
> és 65-84 + 85+, seria comptar la mateixa gent dues vegades) · **E11** motiu literal del mart on
> no hi ha sèrie. Tipus ampliats (5 claus + `MetricDef.frescor?`), `nomCanonic()` per al serrell
> del nom, `verify-govern.mjs` ampliat amb les regles de pintura (cau si algun dia l'atur pinta
> UNA sola comparació). `npm run check` 0/0 · build verd · verificat al HTML prerenderitzat propi.
> **⛔ DUES PREMISSES DEL BRIEF, FALSES:** (a) `docs/equipo/mirador_role.md` **no existeix** (a
> `docs/equipo/` només hi ha `talaia_role.md`) — reconstrucció feta des de CHARTER+REGLAS+
> CONTRIBUTING §1; **➡️ Handoff a: Talaia**, o s'escriuen els `role.md` o el ritual de
> reconstrucció del Charter §III no es pot complir. (b) **la tasca D9 no era a `next.md`**: va
> arribar pel latido i no pel repo (antipatró nomenat al Charter §IV). Aquesta línia ho esmena.
> **➡️ Handoff a: Sondeig** (dada, no pintura): 1) el `motiu` de `mart_tendencia` és **només en
> català** → hauria de ser `{ca,es}` com `label`/`definicio`; 2) **5 mètriques amb
> `frescor.actualitzacio: null`**, i una és targeta del tauler (`rtc_per_1000hab`) — no és bug de
> l'export sinó `origin_source` absent al contracte (`rtc_per_1000hab`/`rtc_per_100hab_viv` → `rtc`;
> `hab_per_hab` → `idescat_emex`; a `IETR`/`IETR_rank` el null és honest); 3) `serveis_estab` i
> `restauracio_estab` **no són a `mart_tendencia`** ni com a `sense_serie` amb motiu; 4) **E11 només
> es pot complir a mitges**: Bea demana «nascuts fora / nascuts a l'estranger» i el mart només té
> **nacionalitat** — confondre-les és el marc que el propi contracte prohibeix; `pct_nascuda_estranger`
> no té cap fila de tendència. **➡️ Handoff a: Talaia** — `atur_registrat` no és al contracte
> semàntic: la seva etiqueta i la seva font són les dues úniques cadenes del tauler que no surten
> del contracte.
>
> **[HISTÒRIC] Mirador D5 ✅ FUSIONAT (#271) — DASHBOARD NIQUELAT.** Mode govern viu (?vista=govern):
> 12 KPIs amb rang comarcal LLEGIT del mart (mai calculat al front), cada targeta amb font O fórmula
> (regla de Bea §8.1), pernocta aparcada, política editorial. **➡️ Handoff a Sondeig:** el pont
> `tools/export_govern_web.py` + `data/web/govern.bergueda.json` el va CREAR Mirador (D4 emetia parquet
> però cap JSON servible — forat de D4); és jurisdicció de `tools/`/dades: revisar-ne la propietat i
> el disseny (idealment D4 hauria emès aquest JSON). Talaia ja n'ha cablat el `--check` al CI (#272).
> **Multi-municipi** (Gombrèn/gorra §5): la vista es limita al Berguedà (C6 §1.2); obrir-la = exportar
> el mart sencer + obrir la porta isBergueda — deixat escrit, no fet (costat conservador). **Atur al
> tauler:** targeta «pendent» fins que hi hagi export web de mart_pols_mensual.
> **[HISTÒRIC] Mirador D5 (ara fet):**
> **D5 · la vista de govern** (`?vista=govern` a `municipi/[slug]`, C6+gorra): els 12 KPIs amb el
> **rang comarcal «k de n»** que D4 ja calcula al mart (`mart_govern` — es LLEGEIX, mai es recalcula
> al front, C6 §4), sèries, licitacions filtrades per ine5, bloc de preguntes suggerides.
> **REGLA DE FERRO C6 §8.1: cada targeta de KPI mostra font (mesurada) o FÓRMULA (inferida)** — el
> camp `formula` ja arriba al JSON (49/49) i `MetricDef.formula?` ja és al tipus (D4); test que cap
> KPI queda sense línia de procedència. Petits: treure `index_turisme` del tipus `MetricKey`
> (metodologia ja net, #269) · serrell B3: el copy del refús del xat diu «(Berguedà)» i el mart és
> Catalunya-947 · loader que embeu pernocta sencer per l'ETCA.
> **🔵 COLA DE BRÚIXOLA:** **deprecated-refús** (handoff de Sondeig #268: `is_available()` a `packages/ai`
> només exclou `planned`, no `deprecated` — el xat encara serviria `index_turisme` si el pregunten;
> ha d'excloure també `deprecated`) · X3 (catàleg govern + 8 preguntes curades, darrere D4✅) · **B3 ✅ (PR
> obert)** — xips de /pregunta-li re-basats en 6 KPIs oficials (ca+es, copy pendent de vot de Bea),
> provats contra fixtures I marts reals; de passada, 3 forats del router tancats (mes arbitrari del
> pols, topònims amb article INE, variant «per habitant» que robava la mètrica) — bitàcola
> `2026-07-18_b3-xips-kpis-oficials_bruixola.md` · serrell nou: copy del refús diu «(Berguedà)» i el
> mart ja és Catalunya-947.
> **🟣 TALAIA (2026-07-20):** ✅ **forat de mètode tancat** — hi havia **un sol `role.md`** (el meu)
> per a un equip de sis. Escrits `mirador_role.md`, `sondeig_role.md`, `bruixola_role.md`,
> `cabal_role.md` i `llegenda_role.md` (dorment, amb la frontera amb Mirador escrita ABANS de
> despertar-lo), i **esmenat el meu**: deia que jo «encarnava» els fronts i que no eren agents
> separats en execució, cosa que va deixar de ser certa el dia que vaig començar a despatxar-los com
> a subagents reals — i no ho vaig escriure. Per això Mirador no va trobar el seu i no va poder
> complir el ritual de reconstrucció del §III. També hi consta la meva segona falta del mateix dia:
> **vaig llençar el latido de D9 amb el PR de la cua encara obert**, així que Mirador va fer pull i va
> trobar «D5 fusionat» — el latido com a tasca, l'antipatró que el Charter §IV nomena.
> **Patró que ja va per tres i cal tallar:** guardes que existeixen i no corren (`--check` de D4/D5
> absent fins a #272 · `verify-govern.mjs` des de D8 sense córrer fins a D9 · cap test de `signals` al
> CI quan el `per_poblacio` es va diluir ×196). Encuat: una meta-guarda que faci caure el CI si un
> verificador versionat no és invocat per cap workflow.
> **🟣 TALAIA:** ✅ nota:/caveat: unificat (#252/#253) · ✅ C4 v2 dues capes + C3 §6bis · ✅ regla de
> procedència C6 §8.1 + `index_turisme` marcat deprecat + bundle orfe fora (#267) · vot de copy de
> Mirador presentat a Bea.
> **🟠 BEA (decisions 2026-07-18):** ✅ deprecar index_turisme · ✅ copy tot OK (xips B3 + aparcaments
> Mirador validats) · 🔑 ETIQUETANT el banc (A+B, es congela quan digui «etiquetat») · pendents:
> validar amb l'Ajuntament la llista de
> projectes del perfil (R-FUNC §3) · crear el repo PRIVAT de sortides del radar (fase dev de l'espai
> del radar, R-FUNC §9.2 — p. ex. datapoble-radar-out; el workflow R4 hi escriurà).
> **📅 ENCUAT NOU (del R-FUNC #258, adoptat):** R7 memòria de cicle (calendari-finestres.yaml +
> anticipacions al correu de divendres — POST-R4, barat) · R8 espai del radar fase pilot (ruta /radar
> a Render amb token per municipi + refresca/envia'm — POST-X2, amb Trazo; anti-relay per §6bis) ·
> agregats públics amb retard + arxiu de tancades (R-FUNC §9, quan surti de l'experimental).
>
> **📦 ENTREGAT (2026-07-17, cicle «tira amb la resta»):** #252/#253 (caveat unificat + exports) ·
> #254 (D1: atur SEPE 2006–2026 × 947 munis, doctrina <5 amb NULL+interval, cron refresh-atur.yml,
> Gósol 25100 i Gombrèn 17080 a la sèrie) · #255 (el vermell de main: per_poblacio diluït ×196 quan
> F2 va escalar a 947 — 7,67 M€ recuperats; suite sencera al CI) · #256 (aparcaments A1–A10: el model
> fora de la vista, −3.310 línies; ETCA o «sense dada oficial»; glossari 21 honest; metodologia
> etiquetada annex de recerca). Verificació adversarial de Talaia a tots quatre.
>
> **⚡ FASE NOVA (Bea, 2026-07-16): tot al dashboard útil + radar; el model de pernocta APARCAT del
> mode govern (dades oficials i consolidades); multi-municipi des d'ara (radar segueix només la Pobla);
> KPI «nova població» amb cura narrativa (vot de Bea al copy). Inventari d'aparcaments i mancances:
> `docs/ajuntaments/fase-nova-aparcaments.md` — les retirades VISIBLES (A1–A10) esperen el vot de Bea
> peça a peça; les regeneracions (B1–B3) es faran als fronts que toquin. Sorpreses de l'auditoria:
> el web JA és online (riusdegent.cat) i X2 JA està fet de facto (Render viu) — la cua de Trazo es
> buida (queda higiene de comentaris rancis «DORMENT»). Riscos oberts: Render free s'adorm (always-on
> ~7$/mes, decisió Bea pre-demo) · noindex actiu · drift render.yaml↔Dashboard · cap workflow refresca
> dades (cron mensual nou al llistó de D1) · D1 esmenada: filtre per BERGUEDA_INE5, MAI província
> (Gósol és Lleida, 25100).**
>
> **🔵 COLA DE BRÚIXOLA:** X3 (catàleg govern) queda darrere de D1/D4 (necessita les mètriques noves) ·
> B3 ✅ entregada (2026-07-18, vegeu la cua vigent més amunt).
> **🟡 COLA DE MIRADOR — DESBLOQUEJADA (vot de Bea 2026-07-16: «sentit comú — el que s'ha d'aparcar,
> s'ha d'aparcar»):** 1) executar els aparcaments A1–A10 (`fase-nova-aparcaments.md` §A; criteri =
> el doc + sentit comú; el /mapa es decideix allà mateix) · 2) D5 (vista govern, C6 + gorra — 12 KPIs
> definitius amb energia en lloc de l'índex de turisme) DARRERE de D4.
> **Decisions noves de Bea (2a tanda):** «Gobrem» = **GOMBRÈN (17080, Ripollès/Girona)** → el tauler
> és per a QUALSEVOL municipi de Catalunya; D1 passa a carregar Catalunya sencera (esmena a
> tasques-especificades) i D4 calcula rangs contra la comarca del municipi · `index_turisme` FORA del
> tauler (satura; substituït per energia/hab) · Render ja era STARTER (drift tancat a render.yaml) ·
> noindex ES QUEDA fins que el mode govern doni valor · **full d'etiquetatge del banc C4 LLEST per a
> Bea: `docs/ajuntaments/banc-c4-etiquetatge.md`** (26 candidates, criteri operatiu, 3 columnes).
>
> **🟣 TALAIA:** unificar `nota:`/`caveat:` al contracte semàntic (X1 va destapar que **el codi llegia
> `nota:` i el contracte escriu `caveat:` a 14 mètriques — TOTES les inferències**: producció servia les
> inferències sense el seu caveat obligat, «852 habitants (est.)» inclòs. X1 ja llegeix les dues claus;
> unificar estalvia la propera esquerda) · esmena C3 §2 bis (termini ambigu) ✅ · etiquetatge del banc C4
> quan Bea vulgui (26 fixtures reals de R1 esperant, **sense cap golden posat per un agent**).
> **DIAL: UNA tasca per front i para** (mode segur per torns). Talaia verifica adversarialment i fusiona.

> **🧪 TRACK ACTIU (2026-07-01): experiment RAG geoespacial honest (Berguedà).** Carta a
> `docs/experiment-rag-geo/00-arrencada.md`. Decisions de Bea: **DuckDB-first** (avisar Rapaz de la
> desviació vs Postgres del brief) · **posicionament a decidir més tard**. KPI = calibració de
> l'abstenció. Fases 0–3 = nucli de valor; 4–5 tancades darrere la porta de la Fase 3. Direcció sota
> `strategic-director-role`: Talaia dissenya+delega+verifica adversarialment; Bea vot narratiu + pont Rapaz.
> **Fase 0a ✅ fusionada (#215)** — substrat DuckDB dels 31 munis; repartiment real del Berguedà:
> oficial 9 · senyal_mes 3 · senyal_menys 1 · **soroll 18**.
> **Fase 0b (embeddings) · Trazo va implementar l'infra (#218); Talaia l'experiment.** Stack local
> (`multilingual-e5-small`, revisió fixada), artefacte d'embeddings commitejat, cerca semàntica torch-free.
> **➡️ Handoff a: Sondeig (dades)** — `docs/experiment-rag-geo/02-handoff-sondeig-collisio.md`: **col·lisió
> d'estimacions** del Nivell C (54 grups a CAT; 12/31 al Berguedà; l'esquerda greu = parell OFICIAL
> Guardiola↔Pobla de Lillet, que Idescat separa i el model no). La 0b hi posa advertència honesta a les
> descripcions; la causa estructural + l'abast a l'oficial són de Sondeig. Pregunta clau: quantes estimacions
> del registre oficial són números repetits presentats com a específics del municipi?
> **Fase 1 ✅ fusionada (#221)** — recuperador espacial (filtre dur → híbrid RRF → detecció d'empat).
> Contracte `03-fase1-recuperador.md`. Eval 8/8; abstenció d'ordenar 4/4 (col·lisió oficial + soroll reportades com a empat).
> **Fase 2 ✅ fusionada (#223)** — herència d'estatut: una regla de distingibilitat (solapament de bandes) per
> als dos usos (modulació per σ + comparació). Contracte `04-fase2-distingibilitat.md`. eval2 5/5.
> **Fase 3 EN MARXA (KPI d'abstenció · l'única fase que pot dir que ens equivoquem)** — contracte
> `docs/experiment-rag-geo/06-fase3-kpi-abstencio.md`. Tres coses congelades abans de veure cap número:
> composició del banc (30–50 Q, ≥1/3 abstenció amb les tres menes de no distingibilitat + contestables + fora de
> catàleg), **etiquetatge daurat de Bea a mà (mai un model)**, i nivells d'èxit fixats per endavant. Mètrica:
> abstention recall/precision/F1 + els dos errors separats. **Es prefereix un negatiu honest a un positiu fabricat.**
> **BANC CONGELAT (2026-07-02)** a `07-fase3-banc.md` (34 Q, daurades de Bea, nivells fixats). **RUN OFICIAL
> (2026-07-02): recall d'abstenció 21/21 (1,000) · de-menys (greu) 0/21 · de-més (prudent) 0/13 · selective
> accuracy 13/13 → NIVELL HONEST.** Q22/23/29 (parell oficial) PASS amb la declaració de col·lisió + ETCA al text.
> Resultat literal a `packages/geo-rag/data/fase3-resultat.txt`. Verificació adversarial de Talaia: doctrina
> intacta, banc intacte, cap literal del banc al codi (sondes inventades → abstenció genèrica), determinista,
> 2×2 recomptada a mà. **Caveat de mirall (escrit al banc):** les daurades deriven de la mateixa doctrina que el
> sistema implementa → el 21/21 demostra que la canonada APLICA la doctrina sense fuites d'extrem a extrem, no
> que la doctrina sigui certa; per endurir-lo: paràfrasis adversarials del banc + segon etiquetador + l'estrella.
> **Nucli de valor (fases 0–3) TANCAT.**
> **CAPA GENERATIVA (contracte de la Rapaz, 2026-07-02)** — `08-contracte-capa-generativa.md`, fusionat abans de
> codificar. El primer component que POT DESOBEIR: generador LLM + validació dura (SQL, cap autoritat sobre números)
> + validació cega (2n model sense veure el raonament). Prompt = sistema congelat (dev set separat; el banc només a
> la passada oficial) · N passades (proposta 5), distribució sencera, mai la millor · errors CLASSIFICATS (taxonomia
> de com la fluïdesa ataca la doctrina) · intervencions de la gàbia ≠ mèrit del generador. **El número: el DELTA
> determinista (21/21) vs generatiu — el cost de la fluïdesa amb σ real.** Nivells de Bea AMB gàbia i SENSE, abans
> de la passada oficial. **ORDRE:** 1) paràfrasis adversarials del recuperador PRIMER (Talaia esborrany → Bea
> congela) · 2) capa generativa · ★ estrella independent (no es bloqueja) · fases 4–5 tancades fins al delta.
> **Preregistrat (2026-07-02):** **N=5 (Bea)** · protocol + nivells a `10-generativa-protocol-i-nivells.md`
> (nivells delegats per Bea a Talaia, justificats: **nu** = la MATEIXA vara que el determinista (recall ≥0,90 +
> FRR ≤0,15) perquè el delta es llegeixi directe; **gàbia** = recall ≥0,98 perquè una fuga amb gàbia és fallada
> triple; esmenables només ABANS de la passada oficial) · spec d'infra per a Trazo a `11-generativa-spec-infra.md`
> (generador `claude-sonnet-5` — intro $2/$10 fins 31-08-2026, després $3/$15 · validador cec `claude-haiku-4-5`
> $1/$5 a temp 0 — model diferent + context aïllat; ~340 crides/passada, ~2–3 $ l'oficial; clau NOMÉS local,
> el CI segueix offline).
> **Infra generativa ✅ fusionada (#229, Trazo):** extra `[generativa]` (`anthropic==0.116.0`), `.env` hygiene,
> CI offline confirmat 5/5. **Correcció de Trazo acceptada:** la spec inicial de Talaia citava `sonnet-4-6` des
> d'una taula cachejada (2026-06-04); la doc EN VIU confirma `claude-sonnet-5` actual i 4.6 *legacy*. Lliçó:
> quan dues verificacions xoquen, mana la font viva — la pròpia verificació també caduca.
> **Accés VIA OPENROUTER (decisió de Bea, 2026-07-03):** la clau `OPENROUTER_API_KEY` ja existeix (secret de
> GitHub) i `packages/ai` ja usa el mateix patró (SDK `openai` + base_url d'OpenRouter). Slugs verificats en viu:
> `anthropic/claude-sonnet-5` $2/$10 · `anthropic/claude-haiku-4.5` $1/$5 (preus passats tal qual). Extra
> `[generativa]` → `openai==2.44.0`. Requisits: proveïdor FIXAT a Anthropic (`allow_fallbacks=false`, també el
> serveixen Vertex/Bedrock), provenance = id de generació + model + proveïdor, i el secret NO es cableja al CI
> per-PR (passada oficial local amb `.env`; si mai des d'Actions, `workflow_dispatch` manual).
> **PARÀFRASIS CONGELADES (Bea, 2026-07-03) + RUN OFICIAL del determinista — EL RECUPERADOR TREMOLA:**
> 68 paràfrasis (daurades heretades; JSON generat MECÀNICAMENT del doc congelat, guardat per test de fidelitat).
> Resultat tal com surt (`fase3-parafrasis-resultat.txt`): recall 38/42 (0,905) però **FRR 7/26 (0,269)** ·
> selective accuracy 14/19 · **bloc C (comparacions reformulades) 0/6 · bloc B 1/6** · **12 silencis equivocats**
> («no tinc l'indicador» menjant-se el silenci de dada/ordre) · **4 FN greus**: P32a/P34a responen PERNOCTA a
> preguntes de RENDA/HABITATGE amb to ferm (el «Barcelona −18%» en conversa) i P26a/P27b trenquen l'empat F
> responent UN muni. [es] 4/5. Parell oficial: 3/6 PASS. **Lectura honesta:** el 21/21 del banc era aplicació
> de doctrina amb frasejos que ecoen; la capa d'INTENCIÓ del router (patrons per paraula clau) és la juntura
> fluixa — exactament on el generador multiplicarà la pressió. Següent proposat: endurir la capa d'intenció
> (v2 transparent, banc+paràfrasis segueixen congelats) ABANS de la capa generativa.
> **ROUTER ENDURIT (v2, 2026-07-03) + RE-RUN — el tremolor s'atura:** fix ESTRUCTURAL, no per strings (precedència:
> gent sola ja no activa valor; menció-nua estricta; comparació estructural = 2 munis + comparatiu/« o »; famílies
> de presència ca+es; bug «frontere»→«fronter»). **v2: recall 42/42 (1,000) · FN 0 · FRR 1/26 (0,038) · selective
> accuracy 25/25 · TOTS els blocs nets · [es] 5/5 · 0 silencis equivocats · parell oficial 6/6 PASS.** Residu honest:
> P7b («està més buit del que consta als papers») → «no reconec la consulta» — fall PRUDENT que no es persegueix
> (seria overfitting per string). Baranes: **banc congelat segueix 34/34 IDÈNTIC** (regressió byte a byte) + 6 sondes
> de generalització amb frasejos NOUS (no dels 68) en verd + caveat de circularitat escrit al codi. v1 preservat a
> `fase3-parafrasis-resultat-v1-router-inicial.txt`. **Camí lliure per a la capa generativa.**
> **★ PASSADA OFICIAL DE LA CAPA GENERATIVA (2026-07-04) — EL DELTA:** prompt CONGELAT (generador-v1),
> Sonnet 5 (mostreig per defecte) + validador cec Haiku (temp 0), N=5, proveïdor Anthropic a les 170/170 trials,
> $1,16 en total. **Recall d'abstenció 105/105 = 1,000 · FN greus 0 · FP prudents 10 · FRR 10/65 = 0,154.**
> Trial-correcte: **NU 154/170 (0,906) · GÀBIA 160/170 (0,941)**. DELTA vs determinista (170/170): **NU 16 · GÀBIA 10**.
> **Nivell (llindar preregistrat doc 10, recall≥0,90 I FRR≤0,15): «RECALL HONEST PERÒ FRR > LLINDAR»** — el recall
> és perfecte però l'FRR passa el llindar per 0,004. **Tot l'FRR ve de DUES preguntes conceptualment bessones**
> (Q10 «de quins pobles no ens refiem» → va llistar els 18 correctes però etiquetà ABSTENIR; Q13 Casserres vs
> Sant Jaume de Frontanyà, bandes disjuntes per un abisme → es va abstenir perquè una banda és soroll): **un mode
> de fall NOU del generador = sobre-aplicar el reflex «soroll→abstenir» a una llista de catàleg i a una comparació
> desnivellada. Sempre erra cap a la prudència (FP), MAI cap al risc (FN=0).** La gàbia recupera 6 trials inestables
> (empat_trencat/caveat a Q12/27/28/29) però NO pot arreglar Q10/Q13 (són errors d'ACCIÓ, que la gàbia no reinterpreta).
> Incidència: la clau d'OpenRouter va topar el límit setmanal a Q27 a la 1a passada → l'arnès ara AVORTA net davant
> un 403 (mai compta un avortament d'infra com a silenci fallit: seria un fals «no funciona») i sap REPRENDRE; la
> passada es va completar amb `--resume` sobre el MATEIX prompt/model congelats. **Pendent: vot narratiu de Bea sobre
> com expliquem un resultat que frega el llindar per prudència; decidir si volem una v2 transparent del prompt
> (regla: catàleg-de-sorolls i comparació-desnivellada NO disparen l'abstenció) o si el número queda tal com surt.**
> **★ v2 DEL PROMPT + RE-PASSADA (2026-07-04, Bea: «jo faria v2»):** fix de PRECEDÈNCIA (primer intent/veredicte de
> comparació, després registre), derivat de doctrina congelada, desenvolupat sobre el dev (ampliat +D13/14/15 nous);
> validador cec SENSE tocar (estricte en contra nostra); v1 preservada com a acta. **Re-passada oficial v2: recall
> d'abstenció 105/105=1,000 · FN 0 · FP 3 · FRR 0,046 (<0,15) → NIVELL HONEST (nu i gàbia) · nu 156/170 (0,918) ·
> gàbia 167/170 (0,982) · DELTA nu 14 / gàbia 3.** Proveïdor Anthropic 170/170. **PERÒ honestedat: l'FP no es va
> esvair, es va MOURE — v1 fallava Q10+Q13 (10 FP); v2 els arregla i destapa un forat LATENT a Q8 («quins municipis
> toquen Berga», intent `veins`): 3/5 passades s'absté perquè el prompt no té doctrina per a `veins` i la seva frase
> de cobertura exclou la geografia, tot i que el substrat SÍ serveix veïns (i el context ja porta la resposta). v1
> feia Q8 5/5 per sort de mostreig. Q13 ara respon les 5 (acció arreglada) però nu 0/5 pel validador estricte —
> ens penalitza, no ens infla; la gàbia ho recupera.** Ja són DUES passades al banc (avís de comparacions múltiples).
> **Decisió de Bea: (a) tancar amb v2 documentant Q8 com a límit conegut i l'FP-que-es-mou, o (b) v3 amb doctrina de
> `veins` (3a passada — afebleix el preregistre). Recomanació de Talaia: (a).**
> **★ v3 (Bea: «v3») + 3a PASSADA — L'FP CAU A ZERO, i aquest cop NO es mou:** doctrina nova per a l'intent `veins`
> (adjacència espacial = servei del substrat, derivable de la Fase 1; la cobertura de valor no exclou geografia).
> Desenvolupat al dev (+D16 `veins` nou, 3/3). v2 preservada com a acta. **3a passada oficial (Anthropic 170/170,
> $1,85): recall 105/105=1,000 · FN 0 · FP 0 · FRR 0,000 · nu 160/170 (0,941) · GÀBIA 170/170 (1,000) · DELTA nu 10
> / gàbia 0.** Q8 estabilitzat a 5/5, i cap FP nou enlloc: el bony no s'ha mogut, ha desaparegut. Els 10 nu-fails
> restants són TOTS l'estrictesa del validador cec (Q13 comparació desnivellada de soroll + Q27/Q28 empats): acció
> correcta, gàbia els recupera. **CAVEAT PER AL PAPER (imprescindible): són TRES passades oficials al mateix banc;
> l'FRR 0,154→0,046→0,000 és en part comparacions múltiples. El que ÉS robust (no un tir afortunat) és el recall
> d'abstenció: 105/105, FN 0, a LES TRES passades — la propietat de seguretat (mai respondre quan s'ha de callar) no
> va tremolar mai. La headline honesta NO és «170/170 gàbia» sinó «FN=0 robust + 3 fixos de doctrina principiats +
> les 3 passades declarades».** Cada fix (precedència v2, veïns v3) desenvolupat al dev, mai al banc; validador cec
> intacte a totes. Actes v1/v2/v3 totes versionades. **PR #235 llest per fusionar (verificat).**
> **★ AUTO-AUDITORIA (2026-07-10) + PUNT 2 i 3 EXECUTATS.** Auditoria completa (metodologia/tècnica/procés/web);
> la bretxa greu —la web publicava NU el número que l'experiment va demostrar no-específic— tancada a #237 (avís de
> col·lisió a la fitxa + doctrina al glossari + candau distinguish.ts, vot de copy de Bea). **ANNEX DE RE-VALIDACIÓ**
> (revalidacio.py, CAP output regenerat; integritat: la reconstrucció reprodueix l'acta 160/170+170/170 abans de cap
> crida): (1) la gàbia COMPTABLE (170/170) sobreestimava — el text engabiat REAL passa el validador **163/170 (v1) /
> 159/170 (v2)**: en 7–11 trials la intervenció no arreglava de veritat; el valor verificat de la gàbia és ~163/170.
> (2) El validador v2 (fall de la comparació desnivellada corregit, congelat a part; el v1 i el número oficial
> INTACTES) llegeix el NU igual: **160/170 amb ELS DOS instruments** — v2 perdona part del càstig desnivellat
> (Q13 5→3, Q27 4→3) però destapa caveats omesos que v1 no veia (Q12/Q22/Q25): arreglar l'instrument NO va inflar
> el número, va redistribuir els motius. Docs al dia (README amb resultats+annex, DATA_CARD amb tots els artefactes
> post-F2, docstring parafrasis aclarit, TODO preus 2026-08-31), paper respatllat a OneDrive/CAJON, neteja
> (%TEMP%, peu juliol 2026, launch.json versionat). **Pendents de Bea: banc de confirmació fresc (meitat [es],
> etiquetes seves) · tret de sortida del ★.**
> **ARNÈS GENERATIU CONSTRUÏT + PROMPT v0.1 MADUR AL DEV SET (2026-07-03):** `generativa.py` (OpenRouter amb
> proveïdor FIXAT a Anthropic —verificat a cada crida—, context de DADES CRUES —la prosa determinista mai arriba
> al generador—, validació dura amb tall ⟦xifra no verificada⟧, validador cec haiku a temp 0, nu/gàbia dels
> mateixos outputs, intervencions a part, taxonomia, pressupost de crides, i el mode oficial ES NEGA a córrer
> sense prompt «CONGELAT» al nom). Dev set de 12 preguntes NOVES + prompts v0 (generador + validador).
> Iteració v0→v0.1 amb 3 falls reals: max_tokens 500 ofegava el raonament per defecte de Sonnet 5 (D4) → 1200;
> mal-atribució estimació→«ETCA» (D6) → regla d'atribució per camp al prompt; «31 municipis» tallat (D9) →
> constant doctrinal. **Dev final: 12/12 nu · 12/12 gàbia · 0 intervencions · taxonomia neta (~0,08 $/passada).**
> Router v2.1 (destapat pel dev): «fa vida»/«moviment» com a marc feble; «té més» amb UN sol muni ja no és
> comparació. Regressions: banc 34/34 IDÈNTIC · paràfrasis 67/68 IDÈNTIC. **Pendent: congelar el prompt
> (generador-v1-CONGELAT) + PASSADA OFICIAL (34×5, nu i gàbia, ~2–3 $) → EL DELTA vs 21/21.**
> **El draft del paper** (`05-paper-esborrany.md`) NO es commiteija encara (Bea el llegeix).

> **🧭 RUMBO DECIDIT (2026-06-27).** Després de l'arc «fer-ho bé» (dada honesta a tot CAT) i del dossier
> de consultoria, la **consultoria externa** ha reconduït el projecte. Decisió a
> `docs/dossier-consultoria-2026-06/01-reconduccio.md`. Concepte: **«l'observatori que sap el que no
> sap»** (Berguedà = nucli validat als 9 munis ≥1.000 —frase canònica a `docs/contracte-abast.md`— ·
> Catalunya = context honest i curat, amb la **costura visible**
> entre Idescat ≥1.000 hab i la nostra estimació <1.000). **El gap és el ganxo; l'epistemologia és el
> producte.** Es treballa per **fases (0→5)**. **Fase 0 ✅ completa · Fase 1 EN MARXA** (calibració ✅
> #187: la banda és honesta, 80%→78,4%). Criteri de parada: si només dues, **Fase 1 + Fase 2**.

> **Vot de Bea pendent**: la **postura política + nota de mètode** sobre usos i límits del *gap*
> (l'únic fleco obert de Fase 0). L'enquadrament del *gap* com a hipòtesi el va decidir el brief de home.

---

## Fase 0 · congelar abast i matar el que trenca · *demostra criteri* — ✅ COMPLETA
- [x] Treure del **mapa públic CAT**: tipologia, pressió, IETR, contradiccions, restauració, densitat, renda (#183).
- [x] Reubicar: ja hi viuen (IETR/renda/restauració a **fitxa**, tipologia al **Berguedà**); n'hi havia prou de no pintar-les al mapa CAT.
- [x] Treure **política** de tot el web (#184 chrome · #185 ruta/blocs/glossari). *Falta la nota de mètode amb postura deliberada — vot de Bea.*
- [x] **Contracte d'abast** en una pàgina (#186, `docs/contracte-abast.md`).
- [x] Enquadrament del *gap* com a **hipòtesi** — decidit pel brief de home (s'aplica a la home, Fase 4).

## Fase 1 · el nucli epistèmic · *el 70% del valor* — EN MARXA
- [x] **Intervals predictius reals + calibració** (#187): banda LOO p10–p90 per tipus.
- [x] **Reliability diagram + taula** de cobertura empírica del p10–p90 en held-out (#187,
      `data/territorial/calibracio_intervals.csv`): l'interval del 80% cobreix el **78,4%** real → **ben calibrat**.
- [ ] **Refer la banda** dels tipus infracoberts (corona/litoral metropolità, n petita) — *en públic ho cobreix la costura* (≥1.000 = Idescat); sobretot afecta l'auditoria interna.
- [ ] **Cosir la capa CAT**: ETCA oficial (Idescat) a ≥1.000 hab · estimació pròpia només a <1.000
      (marcada experimental) · **costura visible** + **doble etiqueta** (ETCA = net anual ETC ≠ la nostra
      pernocta). ← **peça gran següent** (desbloqueja el brief de home, Blocs 2 i 5).
- [ ] Verificar que **Barcelona i les ciutats denses les parla Idescat** (desapareix el negatiu absurd) — part de la costura.
- [ ] **Treure la calibració a /metodologia** (reliability diagram visible) + documentar el **supòsit causal i els confusors** (R²=0,41).

### Passada de solidesa (2026-06-29) · *tancar ENSENYAR↔VALIDAR* — recomanació a `docs/dossier-consultoria-2026-06/03-recomanacio-solidesa.md`
*Diagnòstic multiagent + crítica adversarial + verificació manual. Lliçó: cap síntesi entra sense
verificar el fet que la sosté (la pròpia síntesi va sobrepormetre el #1; la confiança ja estava capada).*
**Tres baranes per a tota curació de dades:** (1) regenerar des de la font, mai editar el JSON a mà
(idempotent via `--check`); (2) overlay no destructiu, registrar afectats; (3) banderes **tri-estat**
amb `no_classificable`, mai default booleà (survivorship bias).
- [x] **#1 · `muni_lede` honest** (fora «la mateixa riquesa… per a qualsevol municipi»; lede condicional Berguedà vs resta). #200, desplegat.
- [x] **#3 · sanejar `confianca` sense estimació**: `pernocta_est null ⇒ confiança null` a l'exportador (els 20 = forat 947→927); `IETR` intacte; + `export_web_municipis --check` a CI. #201, desplegat.

### Vot dels tres registres (2026-06-29) · *el nus «verificat-primer vs costura», RESOLT* — `docs/dossier-consultoria-2026-06/05-vot-tres-registres.md`
*No es vota arquitectura: es mira el número. **99 dels 441 <1.000** passen el llindar (interval exclou el
padró) → tercera via. La frontera no és la població del municipi, és si la nostra estimació es distingeix
del nostre error. La magnitud va al **to**, no al llindar (sense ETCA no hi ha segona porta).*
- [x] **Eina auditable** `tools/senyal_sub1000.py` (`--check` + CSV, com els 151) + a CI. El 99 és recalculable.
- [x] **Costura a la fitxa amb els tres registres** (banda real + veu graduada; soroll replegat). #204, desplegat. *Tanca l'últim pas de Fase 1.*
- [x] **#5 · cobertura per tipus a /metodologia** amb la **n** al costat (corona n=9 i litoral n=7 → «n massa petita», no un % de falsa precisió). #205.
- [x] **Publicar el fet «nucli validat = 9 municipis»** (callout destacat a /metodologia). #206.
- [x] **ETCA lidera el gap als ≥1.000 a la fitxa** (registre oficial: Idescat lidera + nostra estimació de contrast + doble etiqueta). #206.
- [ ] **Reconciliar la font de PADRÓ** — **DECIDIT** (Rapaz, 2026-07-01): la font canònica és **la que Idescat fa servir per a l'ETCA** (`pernocta.padro` / nivellc), per coherència amb la vara de validació, no per bellesa del número. Unificar fitxa + `senyal_sub1000.py` + export a aquesta font (afecta el «99», els 151, l'etcaPct de la fitxa). **0 flips al Berguedà** → baix risc; **obert i no-bloquejant** (llest per implementar).

### Directrius de tancament (Rapaz, 2026-07-01) — FET
- [x] **Pregunta-li** fora del menú superior (escriptori + drawer) → viu al peu, marcat **«experimental»** (badge a la capçalera + al peu), fins que l'experiment el reconstrueixi.
- [x] **Callout «9»** només a /metodologia (mai a la home) i **mai sense el 78,4%** que l'acompanya (afegit a la frase).
- [x] **Waveform: soroll = absència** (no un tercer color): oficial + senyal a la tinta; el soroll no es dibuixa (927→585 punts).
- [ ] **Purga total de política** (`mart_electoral` + porta d'IA + bundle offline): **diferida a l'experiment**, amb el residu escrit perquè sigui higiene i no sorpresa. El **vot polític** segueix sent de Bea.
- [ ] **#4 · banderes data-level** (`regim_dens`, `soroll`/`senyal`, `outlier`) tri-estat; `confianca`→`confianca_model`. *(En part absorbit pels tres registres a la fitxa.)*
- [ ] **Reclassificat — test multianual** (ICAEN 2013–2024): de «oportunitat futura» a **via de validació dels 99** (gap que persisteix = comprovat en el temps). No s'executa ara; canvia d'estatut.

## Fase 2 · la vitrina Berguedà · *rigor de punta a punta*
- [ ] 31 munis, dades completes; model validat contra ETCA als **9 munis ≥1.000** (no els 31), honest amb els 22 sense validació oficial (frase canònica a `docs/contracte-abast.md`).
- [ ] Pàgina de **metodologia auditable** amb gràfics de validació.
- [ ] Error per **tipus territorial** i límits declarats (inclòs que **ETCA també és estimació**).

## Fase 3 · la capa Catalunya honesta · *saber quan NO ensenyar*
- [ ] Mapa públic amb **% habitatge no principal** + el **present-vs-padró cosit**.
- [ ] **Escala log** on la densitat ho demani.
- [ ] Llegenda que **matisa, no que es disculpa**.

## Fase 4 · la fitxa i la home · *producte per a consum humà*
- [ ] Fitxa amb **jerarquia dura**: el *gap* i la seva incertesa, protagonista; la resta col·lapsada.
- [ ] Treure de la vista per defecte la «**maquinària**» crua.
- [ ] Home: **mapa comarcal agregat + cercador**, amb el **waveform del *gap*** com a peça-firma.
- [ ] Etiquetar «**el bessó del teu poble**» com a experimental o validar la mètrica de distància.
- *(Absorbeix el brief de fitxa §5 i la nav/UI §6 del dossier: canvas vertical, zoom CAT, treure menú
  sobrant, Resum→Comarca.)*

## Fase 5 · la capa d'IA honesta · *opcional, el «no» com a funcionalitat* · **(IA)**
- [ ] «Pregunta-li» com a **text-to-SQL acotat al Berguedà**, amb traça (font + consulta SQL).
- [ ] Que **es negui** quan la pregunta surt del catàleg.
- [ ] Corregir el cas trencat («té més població Lleida que Girona?» → respon «Barcelona»).

---

## Transversal / llançament (quan el nucli aguanti)
- **Ops de llançament** (Talaia+Mirador): treure noindex ×3 (`app.html`, `robots.txt`, `_headers`);
  `og:image`; deploy verd al domini; comprovació final. *(El sitemap ja hi és, #150.)*
- **a11y AA** (Llegenda+Mirador): teclat al mapa, contrast, `axe-core` a CI.
- **Llengües** aranès + anglès (Brúixola+Talaia) **(IA)**: repàs còpia ca/es → Apertium/AINA (oc) + en.
- **Viz pendents** (Mirador): Dorling, slider, embedding 2D de secció (PCA/MDS), dades obertes (/dades,
  xifra citable, embeds, kit premsa). *Subordinades al nucli; entren si sumen.*

---

## Històric — arc «fer-ho bé» (F1–F5) + llançament P0/P1 · **FET** (a `main`)
*Detall a la bitàcola i als PR; aquí només el resum perquè la cua viva sigui la reconducció.*
- **P0/P1 llançament** (juny 2026): Nivell C a tot CAT (#152) · cercador 947 (#146) · prerender 947
  (#146) · licitacions «en construcció» (#147) · missatge d'abast (#148) · sitemap (#150) · espina +
  comarca/vegueria (#151,#158) · beeswarm/constel·lació del gap (#155,#157).
- **Arc «fer-ho bé» (F1–F5)** (`docs/pla-catalunya-profund.md`): dataset profund estès als 947 amb
  model unificat i honest; els **11 indicadors es pintaven a tot CAT**; fitxes uniformes; **guardó ETCA
  Berguedà 8,2%/ρ=0,967** preservat. PRs #161–#179. Dossier de consultoria #181.
- **⚠️ La reconducció REENQUADRA tot això:** dels 11 indicadors, el mapa públic CAT en conserva
  ~**3** (gap reenquadrat + %no-principal + residus); la resta baixa a Berguedà o fitxa (§4). No és
  feina perduda: és la matèria primera que ara es **cura**.

## Diferit a Fase 2 (del projecte, no del pla)
Licitacions de veritat (menors → majors/diputació) · fonts noves.

## Futur · per a qui continuï (documentat, no per executar ara)
- **Pernocta multianual (sèrie temporal).** A la raw d'ICAEN hi ha **2013–2024 anual**; la pernocta
  només fa servir **un tall (2024)**. Calcular-la any a any donaria (a) una **tendència** de la població
  invisible al llarg d'una dècada i (b) un **test d'estabilitat = senyal vs soroll en el temps**: un gap
  que **persisteix** any rere any és senyal; un que **parpelleja** és soroll (la mateixa partició dels
  151, però en l'eix del temps). Reforçaria la calibració amb evidència nova. Bon material per a Fase 2/3.
