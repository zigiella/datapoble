# R2 · Filtre dur determinista + puntuació de perfil — el cor del radar

**Agent:** Sondeig (dades) · **Data:** 2026-07-18 · **Tasca:** #3 de la cua (R2)
**Contractes complerts:** C3 (sencer: §2bis, §3, §4, §6, §6bis) · C4 §1/§4 · R-FUNC §3/§7/§9.1

## 1 · Què s'ha construït

**`config/municipis/` (E5, la primera convenció declarativa del repo):**
- `08166-lillet.yaml` — des de la proposta del R-FUNC §3, marcat **«PROPOSTA,
  pendent de validació de Bea amb l'Ajuntament»**; `actiu: true` (únic de la v1).
- `08052-castellar.yaml` i `_default.yaml` — **dorments** (`actiu: false`); la
  plantilla `_default` és copiable i el loader la salta (cap herència, C3 §3).
- **§6bis aplicat:** `destinataris: [BEA]` (clau simbòlica). El fitxer del R-FUNC
  §3 deia `destinataris: [<correu de Bea>]` — aquí no hi viu cap adreça.

**`packages/signals/datapoble_signals/perfils.py`** — load amb validació
**fail-fast** (C3 §3/§4/§6bis): camp desconegut → error · `actiu` absent → error ·
`pes` fora de [0,1] → error · una `@` a destinataris → error · INE5 del nom de
fitxer fora de `BERGUEDA_INE5` → error (amb la trampa de codis 08052/08166 escrita).

**`packages/signals/datapoble_signals/subvencions_match.py`** — el filtre:
- **Doctrina (C4 §1, el FN és el pecat greu):** es descarta NOMÉS amb evidència
  positiva d'exclusió; en el dubte, passa (viva, sovint groga). 6 portes en ordre:
  **convocant** (ajuntament aliè · consell d'una altra comarca · diputació d'una
  altra província · AMB · govern d'una altra CCAA — llegint el text COMPLET
  d'`organisme`: el filtre `organos` de la BDNS no cascada) → **beneficiaris**
  (vocabulari tancat BDNS: si cap tipus no és compatible amb un ens públic,
  fora) → **nominatives/directes** (R-FUNC §7) → **restricció de població**
  (regex conservador al text, aplicada amb el **padró citat al perfil** i citada
  al motiu) → **àmbit** (mismatch positiu amb `territori`; `estatal` EXISTEIX i
  passa — decisió R1 ratificada) → **vigència** (a la **data de referència**).
- **§2bis literal:** `termini: NULL` MAI descarta — viva amb «termini per
  confirmar — mira l'enllaç» (mirada humana, no descart).
- **El flag `tancada` només mana si era vigent a la referència** (data_vista ≤
  referència): en el run diari descarta («m'hi puc presentar?» és el que declara
  `abierto`, R1); en mode banc (referència = data_publicacio, C4 §2) el flag és
  posterior al judici → nota, no descart. Sense això, tota la capa B
  tancada-per-edat seria FN de sistema el dia del run oficial.
- **Puntuació que ordena i MAI filtra** (R-FUNC §3): matching lèxic transparent
  (lèxic ca↔es curt, prefix de paraula — «cultura» no dispara dins
  «agricultura») → màx pes de matèria amb match + 0,3 si un projecte en cartera
  encaixa; puntuació 0 = viva igualment, al fons i en groc. Semàfor DETERMINISTA
  (verd només amb lligam fort + termini datat viu + cap dubte) = **stub offline
  de R3** (R-FUNC §9.1: sense clau, filtre dur + stub).
- **Cada descartada, motiu d'UNA línia** (C4: auditables una a una; test que cap
  motiu té salt de línia).

**Dry-run §9.1 (l'ordre única):** `python -m datapoble_signals.subvencions_match
--data <dia> --perfil <ine5> --sortida out/ [--font parquet|json]` → escriu
`radar-<ine5>-<data>.md` (estructura del correu: verdes amb el perquè que cita
el perfil, grogues amb el dubte, descartades amb motiu) + `.json` (veredictes
complets) a `out/` — **gitignorat de nou** (.gitignore). Sense timestamps de
rellotge: mateixos inputs, mateixos bytes (rejugable). El camp
`sortida_autoritzada` replica la porta de C3 §3: castellar (dorment) corre i es
veu al log, però cap sortida real queda autoritzada. **El correu real és R4.**

## 2 · El dev set — EL BANC NO S'HA TOCAT (C4 §4)

- El filtre s'ha desenvolupat contra un **dev set propi**: 12 sintètiques
  dirigides (una regla per cas) + **5 reals de FORA del banc** (BDNS, finestra
  15–31/01/2025, anterior a la composició de la capa B), arxivades crues a
  `tests/fixtures/dev_r2_reals.json` amb la selecció documentada al `_meta`.
- **Guarda mecànica:** `test_dev_set_disjunt_del_banc` verifica que cap id del
  dev set és a `bdns_convocatories.json` (26, capa A) ni a `bdns_capa_b.json`
  (40, capa B). Cap etiqueta llegida ni citada — al repo no n'hi ha cap, i les
  expectatives del dev set estan retolades com a expectatives de DEV de Sondeig,
  no daurades. **El run oficial contra el banc és de Talaia, quan Bea congeli.**
- Reals triades per exercir regles concretes: Dip. **Lleida** memòria democràtica
  (regla de província, tot i matèria del perfil) · Aj. d'**Orís** eficiència
  energètica (la trampa «la matèria encaixa però el convocant és aliè») · Diba
  BCN ×2 i Generalitat NextGen (vives a la seva època, mode banc).

## 3 · Evidència (tot offline, CI-ready)

- **Suite signals: 180 passed** (141 existents + 39 noves) · ruff net.
- Trampes exercides amb test: **«Sant Salvador de Guardiola» (Bages) ≠ Guardiola
  de Berguedà** (descartada per convocant aliè amb el nom complet al motiu, mai
  confosa; i el Consell Comarcal del BERGUEDÀ passa) · àmbit `estatal` passa amb
  el perfil que el porta i es descarta amb un que no (les dues direccions) ·
  restricció «>20.000 habitantes» descartada citant «1106 hab (padró 2025)» ·
  §2bis NULL mai descartat · puntuació 0 no filtra · flag tancada vigent/posterior.
- **Snapshot golden** de l'estructura del dry-run (patró test_parafrasis):
  `tests/fixtures/golden/radar-08166-2026-07-01.md` — el format s'itera pel diff.
- Dry-run demostrat pels DOS camins de font: JSON rejugable i **parquet real**
  (materialitzat amb `write_subvencions_table` de R1 fora del repo): resultats
  idèntics (0 verdes · 3 grogues · 2 descartades a referència 2025-02-01).

## 4 · Fronteres honestes i troballes

- **El matching de matèries és LÈXIC i declarat com a tal** (lèxic ca↔es curt i
  transparent al mòdul): gradua l'ordenació, no pretén semàntica — el judici fi
  és de R3 (Haiku). Un consorci públic aliè (p. ex. Consorcio de la Vivienda de
  Barcelona, vist al dev set real) passa el filtre com a groga: descartar
  consorcis en bloc arriscaria FN (n'hi ha de comarcals on la Pobla és membre);
  és exactament la classe de soroll prudent que C4 §1 tolera i R3 ha de graduar.
- **`termini_text` (C3 §1/§2bis) encara no existeix a la fitxa de R1**
  (`SUBVENCIO_COLUMNS` no el porta): el contracte el preveu però el connector no
  el materialitza. R2 no en depèn (mai descarta per NULL), però R4 el voldrà per
  ensenyar «Finaliza el 15 de septiembre…» literal. **Handoff a: Sondeig mateix
  (R1, esmena petita) — anotat, no tapat aquí** (hauria barrejat connector i filtre).
- El perfil de la Pobla queda com a **proposta**: la validació amb l'Ajuntament
  és de Bea (cua 🟠). Canviar pesos/cartera NO demana tocar codi: només el YAML.

**Handoff a: Talaia** — R2 llest per a la verificació adversarial; el run oficial
contra el banc espera la congelació de les etiquetes de Bea (C4 §2). R3 (Brúixola)
té l'ancoratge: el semàfor determinista d'aquí és l'stub que el seu Haiku refina.
