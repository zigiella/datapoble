# Cua — reconducció (rumbo decidit 2026-06-27)

*Mètode: **Cambium Charter v0.5**. Es treballa de dalt a baix; cada tasca = un PR. Cada **fase** és
publicable per si sola.*

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
> **Paràfrasis:** esborrany de 68 (2 per Q, daurades HERETADES del banc congelat, 5 en castellà, fora-de-catàleg
> sense keyword) a `09-parafrasis-adversarials.md` — **NO commitejat**, pendent de congelació de Bea.
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
