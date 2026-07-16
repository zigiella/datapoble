# Cua — reconducció (rumbo decidit 2026-06-27)

*Mètode: **Cambium Charter v0.5**. Es treballa de dalt a baix; cada tasca = un PR. Cada **fase** és
publicable per si sola.*

> **🏛️ TRACK ACTIU (2026-07-16): datapoble per a ajuntaments — `docs/spec-ajuntaments-v1.md`**
> (direcció de Bea, redacció Marea #239, ADOPTADA amb esmenes per Talaia — §10 de l'spec és vinculant).
> Demo Magda (Diba) set 6–8. **El que ven la demo és el número** (recall del radar + KPI d'abstenció del xat),
> verificat per Talaia — mai un titular sense el seu caveat.
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
> - **D0 (Talaia)** — contractes C1 (mètriques noves + camp `visibilitat`, E4) + C2 (dades internes:
>   `publicable:false` MAI al repo públic, E1) + C6 (mode govern, vot narratiu de Bea) → després
>   D1 (atur Socrata) · D2 (HERMES selectiu) · D3 (municipal_csv) · D4 (mart_govern) · D5 (vista
>   govern, Mirador) · D6 (CSV real de la Pobla, Bea).
> - **X1 (Brúixola)** — collita C5: doctrina + gàbia RE-VALIDANT (E3, validador v2) cap a
>   `packages/ai` · X2 (activar render.yaml dorment, Trazo) · X3 (catàleg govern + preguntes suggerides).
> **El geo-rag NO es toca** (congelat com a annex de recerca fins a X1); els seus pendents propis
> (banc de confirmació de Bea · ★ · paper) queden fora d'aquesta spec (E6), seqüenciats post-demo.

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
