# Motor de convergència — turisme × sequera (Fase B del cabal)

**Fecha:** 2026-06-06
**Autora:** Cabal
**Para:** Talaia (review)
**Tema:** el **motor de convergència** que creua els dos rastres del cabal
(contractació + sequera) amb el mart de Sondeig (pilar 1) per provar —graduant, no
afirmant— la hipòtesi del nord de *riusdegent*: la pressió turística/segona
residència co-ocorre amb tensió hídrica?
**Status:** entregable / handoff. **Intern** (decisió de Bea: res al web encara).

## Contexto

El cabal tenia ja **dos rastres** a `data/events/`: contractació
(`events_bergueda.parquet`, senyal d'**anticipació**) i sequera
(`events_sequera_bergueda.parquet`, senyal de **realització**, PR #38 a `main`). La
meva entrada anterior (`2026-06-06_sequera-rastre_cabal.md`, secció «Recomanació
per al motor de convergència») deixava el disseny apuntat. Bea ha autoritzat la
**Fase B**. Aquesta entrada documenta el motor i —el més important— **el resultat
honest**.

## Qué hicimos / decidimos

Mòdul nou `packages/signals/datapoble_signals/convergencia.py` (i CLI
`python -m datapoble_signals convergencia`). Tot el pipeline és **una sola consulta
DuckDB declarativa** sobre `read_parquet` (cap estat mutable; els tres parquets
d'entrada són **read-only**). Mètrica (acordada amb Talaia, refinada amb les dades):

1. **Unificació** dels dos rastres: `UNION ALL` sobre `EVENT_COLUMNS` → taula
   `events` única. El motor filtra per `tipus_senyal` el que necessita de cada un.

2. **Exposició a la sequera** per municipi, **reconstruint intervals**: la font és
   un històric de transicions, així que ordeno per `data` dins de cada `ine5` i
   prenc `LEAD(data)` com a fi de l'interval (l'últim estat val fins a
   `PERIODE_FI=2025-05-16`, l'últim canvi observat — no invento futur). Derivo:
   - `sequera_severitat_mitjana` = mitjana de la severitat (la `confianca` ordinal
     de l'escala del Pla) **ponderada per dies** de vigència.
   - `sequera_severitat_pic` = severitat màxima; `sequera_mesos_alerta` = mesos
     (de 30 dies) en severitat ≥ 0.6 (ALERTA+).

3. **Pressió turística**, dos angles independents (convergència de *mètodes*):
   - **primari, ROBUST** — `index_turisme` (0-100) i `gap_pernocta_pct` de
     `mart_municipi.parquet` (Sondeig, hostaleria validada). És el que condueix.
   - **secundari, FEBLE** — events `turisme_cultura_events` de contractació
     (compte + €). **Mut als micromunicipis** (Castellar de n'Hug = 1 hit residual,
     Gósol = 0…): els pobles petits no contracten. Per això NO és el primari.

4. **Lectura de convergència**: `turisme_score` (= `index_turisme`/100) ×
   `sequera_score` (= severitat mitjana) → `convergencia_score`, i un `quadrant`
   amb llindars **ancorats a l'escala** (turisme ≥ 50; severitat ≥ 0.45), **no a la
   mediana de la mostra** (vegeu «Por qué» #2).

5. **Output**: `data/events/convergencia_bergueda.parquet` (1 fila/municipi, 31
   files, materialitzat via DuckDB com `events.py`). Columnes: scores de turisme i
   de sequera, `convergencia_score`, `quadrant`, i **flags honestos**
   (`flag_sequera_per_zona`, `flag_turisme_poc_fiable`,
   `flag_turisme_contractacio_feble`).

### EL RESULTAT: la hipòtesi NO es confirma al Berguedà (un «no» honest)

Repartiment dels 31 municipis pels 4 quadrants:

| quadrant | n | qui |
|---|---|---|
| **alt_turisme · alta_sequera** (la hipòtesi) | **4** | Sagàs, Sta Maria de Merlès, Viver i Serrateix, la Quar |
| alt_turisme · baixa_sequera | 7 | **Gósol, Castellar de n'Hug, Saldes, la Nou, Capolat**, Castellar del Riu… |
| baix_turisme · alta_sequera | 9 | **Berga, Gironella, Avià, Puig-reig**, Casserres, Olvan… |
| baix_turisme · baixa_sequera | 11 | Guardiola, la Pobla de Lillet, Bagà, Cercs… |

- El quadrant de la hipòtesi (alt×alt) recull **només 4 de 31**, i **cap dels 4 és
  fiable**: tots porten `flag_turisme_poc_fiable` (micromunicipis de 44-179 hab on
  `index_turisme` satura a ~100 per N petit, amb confiança baixa/mitjana al mart).
  `convergents_fiables = []`.
- **Correlació de rang turisme↔sequera = Spearman −0,28** (Pearson −0,21; **−0,54
  ponderada per població**). És lleugerament **inversa**.
- **Per què s'inverteix (geografia):** el turisme del Berguedà es concentra a la
  **capçalera del Llobregat (UE 06)** — el Pirineu (Gósol, Castellar de n'Hug,
  Saldes, la Nou, la Pobla de Lillet) — que és precisament la zona que va patir
  **menys** sequera (severitat mitjana 0,364; 14,8 mesos d'alerta+). La sequera
  forta és al **corredor mitjà i baix** (UE 16 Mig Llobregat 0,516 i 32,5 mesos;
  UE 10 Embassament 0,492 amb pic 0,90 = emergència I), on viuen els pobles
  **poblats i poc turístics** (Berga 17.539 hab amb `index_turisme` 26,6;
  Gironella, Avià, Puig-reig). Berga és el cas net (cap flag): molta tensió hídrica,
  poc turisme → `baix_turisme_alta_sequera`.

**No he forçat el resultat bonic** (recordant el *catch* del model de 3 capes): el
motor mesura, i el que diu és que al Berguedà la tensió hídrica del corredor **no
l'explica el turisme**. La hipòtesi del nord podria valer en altres comarques
(costa, Pirineu amb estacions), però **aquí no**.

## Por qué — decisions de disseny

1. **Llindar de sequera per zona, no per municipi (la frontera més important).**
   Verificat sobre les dades: els 31 municipis cauen en **exactament 3 Unitats
   d'Explotació** (06 Capçalera = 18 municipis, 10 Embassament = 5, 16 Mig
   Llobregat = 8) i **dins de cada UE la trajectòria de sequera és IDÈNTICA**
   (mateix nombre de canvis, mateixes dates, mateixa severitat — comprovat: per UE,
   `count(distinct (data,confianca)) == total/n_municipis`). Per tant la sequera
   **no discrimina entre municipis de la mateixa UE**. Ho marco a cada fila amb
   `flag_sequera_per_zona=TRUE` i guardo la UE a `sequera_unitat_explotacio`. La
   sequera aporta el **denominador de tensió de la zona**; la variació fina entre
   municipis ve del turisme. **Ningú ha de llegir la severitat municipal com a
   mesura local independent.**

2. **Quadrant ancorat a l'escala, no a quantils.** La sequera pren només **3
   valors** (un per UE) → la **mediana cauria al mínim** (0,364) i tot quedaria
   classificat «alta sequera» (quadrant degenerat — ho vaig veure al primer
   prototip: 16/15, zero «baixa sequera»). Per això els llindars són **semàntics**:
   turisme ≥ 50 (meitat superior de l'escala 0-100 del mart) i severitat ≥ 0,45
   (entre la capçalera 0,364 i el corredor 0,49-0,52). Decisió explícita, a
   `LLINDAR_TURISME_ALT` / `LLINDAR_SEQUERA_ALTA`, revisable.

3. **`index_turisme` com a primari, contractació com a secundari.** El senyal
   municipal robust és el del mart (hostaleria validada, 0-100). La contractació de
   turisme és **muda als micromunicipis** (només Berga en té volum: 212 events,
   2,5 M€; Consell Comarcal 60; Castellar 1; la resta 0). Si l'hagués fet primari,
   tots els pobles turístics petits sortirien com a «sense turisme» — fals. La
   contractació entra com a context (`turisme_contractacio_n/_eur`) i el seu
   silenci es marca amb `flag_turisme_contractacio_feble`.

4. **Score = producte dels dos eixos normalitzats.** `convergencia_score =
   (index_turisme/100) · severitat_mitjana`. El producte exigeix que **tots dos**
   siguin alts perquè el score ho sigui (un eix baix l'enfonsa) — és la propietat
   que volem per a «co-ocurrència». No és una probabilitat; és un índex ordinal.

5. **El motor és pur i read-only.** No reescriu cap dels tres parquets d'entrada;
   només llegeix. La sortida és un parquet nou. `convergencia` queda **fora d'`all`**
   (que recull *fonts* amb xarxa); és un derivat que opera sobre el ja materialitzat.

## Honest boundaries (disciplina de Talaia)

- **Co-ocurrència, NO causalitat.** El `convergencia_score` gradua una hipòtesi; no
  la prova. Cap afirmació causal al output ni aquí.
- **Sequera per zona (UE), no per municipi** — repetit perquè és el límit dur
  (vegeu «Por qué» #1). Flag a cada fila.
- **Soroll als micromunicipis:** `index_turisme` satura a 100 amb N petit (ràtio
  RTC/habitant amb denominador minúscul). `flag_turisme_poc_fiable` (població < 300
  **o** confiança del mart 'baixa') ho marca. **Els 4 «convergents» en porten tots
  el flag** → el «sí» aparent és, de fet, soroll. Honest: ho dic al resum de `run`
  (`convergents_fiables: []`).
- **El «no» és el resultat, i el deixo dit clar.** La hipòtesi no es confirma al
  Berguedà; s'inverteix lleugerament. No l'he maquillada.
- **`PERIODE_FI` = 2025-05-16** (últim canvi observat). L'última severitat val fins
  aquí; no extrapolo. Si el dataset s'actualitza, cal pujar la constant.
- **Mojibake:** els noms surten nets perquè el motor els **ancora al registre**
  `BERGUEDA_INE5` (no al text de cap font). El `municipi` del mart i l'`objecte` de
  sequera duen `�` a l'origen; no els faig servir per al nom.

## Tests (`tests/test_convergencia.py` — 15 nous; 58 al package, tots verds)

Offline i deterministes (aptes per CI): tres parquets **sintètics** minúsculs
(`fixtures_convergencia.py`, 4 municipis × 2 UEs) on cada quadrant i cada flag és
conegut a mà, executats via `build_sql` amb un registre de municipis injectat.
Cobreixen: el contracte (columnes/ordre, cobertura dels municipis); la
**reconstrucció d'intervals** (severitat ponderada per dies, pic, mesos d'alerta);
la **frontera de zona** (severitat idèntica dins la UE; `flag_sequera_per_zona`);
els **4 quadrants**; el score com a producte normalitzat; els **flags honestos**
(poc fiable per micromunicipi, contractació feble); i el resum (`convergents_fiables`
buit). A més, si el parquet REAL existeix, reaplica invariants + les **àncores
honestes** del Berguedà: 31 municipis, **3 UEs** amb severitat única per UE,
quadrant alt×alt ≤ 6 amb **0 fiables**, i **Berga = baix_turisme_alta_sequera**.

## Pendiente

- [ ] **Repartir el senyal comarcal de contractació als micromunicipis** (la lliçó
  supra): avui el secundari de contractació és mut als pobles petits perquè el
  volum viu al Consell Comarcal (`ambit='comarcal'`, `ine5=NULL`). Es podria
  repartir per població/àrea per donar-los un proxy turístic propi del cabal.
- [ ] **Escala Catalunya:** provar la hipòtesi on la geografia hi juga a favor
  (costa, Pirineu d'estacions). El motor es parametritza canviant els parquets
  d'entrada. Atenció (ja anotat): sequera = només Conques Internes (l'Ebre, CHE).
- [ ] **Refinar `confianca` ↔ severitat** si l'ACA publica codis d'estat nous
  (preemergència/emergència II ja contemplats a `CONF_PER_ESTAT`).
- [ ] **Integració semàntica / web:** quan Bea ho decideixi (avui **intern**). NO
  he tocat `semantic/metrics.yml`, `packages/web`, `packages/ai`, `ci.yml`,
  `.gitignore` (contractes de Talaia).

## Enlaces

- `packages/signals/datapoble_signals/convergencia.py` (el motor)
- `packages/signals/datapoble_signals/__main__.py` (CLI: `convergencia`, fora d'`all`)
- `packages/signals/tests/test_convergencia.py` + `tests/fixtures_convergencia.py`
- `data/events/convergencia_bergueda.parquet` (31 municipis; versionat)
- `packages/signals/README.md` (secció «El motor de convergència»)
- entrada prèvia: `bitacora/2026-06-06_sequera-rastre_cabal.md`
