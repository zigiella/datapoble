# V3-DADES · els `motiu` de sense_serie, en llengua de ciutadà — Sondeig, 2026-07-30

**Tasca:** bloc V3-DADES del redisseny del tauler v3 (vot de Bea 2026-07-29; doc vinculant
`docs/ajuntaments/redisseny-tauler-v3.md` §5). El tauler pinta ELS MOTIUS LITERALS de
`mart_tendencia` quan una mètrica no té sèrie, i eren argot d'enginyeria («cap sèrie per API»,
«pendent d'ingesta», «filtres id/i/tipus»). S'han reescrit en registre ciutadà **mantenint el motiu
honest exacte i la distinció entre casos**; el detall tècnic no s'ha perdut: viu als comentaris del
model, al contracte i a /metodologia, que és on el busca qui el necessita.

**Diff:** `packages/transform/models/marts/mart_tendencia.sql` (literals + comentaris) ·
`data/marts/mart_tendencia.parquet` · `data/web/tauler.bergueda.json` · `data/web/tauler/*.json`
(947 shards + `_meta`, regenerats per l'exportador existent — el `_meta` no canvia).
**Cap fitxer de `packages/web/`, `semantic/metrics.yml`, `packages/ai/` ni `packages/signals/` tocat**
(Mirador treballa en paral·lel al mateix tauler; el seu front pinta el `motiu` literal i la
reescriptura li arriba sola en fusionar).

---

## Els cinc casos (la distinció es continua veient)

| Cas | Mètriques | La frase que el porta |
|---|---|---|
| **Límit de font** (EMEX) | poblacio, 4 franges, index_envelliment, 4 lloc de naixement | «La font oficial només publica la dada vigent: no en podem ensenyar l'evolució.» |
| **Pendent nostre** | renda_neta_persona, kg_hab_any, kwh_hab, vidre_hab | «La font oficial sí que en té la sèrie històrica; nosaltres encara no la carreguem.» |
| **Dada decennal** | pct_noprincipal | «És una dada del Cens d'habitatge del 2021, que es fa un cop cada deu anys.» |
| **Registre viu** | rtc_per_1000hab | «…que llegim com una foto del dia de la càrrega: no en conservem cap tall anterior.» |
| **Mapa que es completa** (OSM) | serveis_estab, restauracio_estab | «…una pujada podria ser que algú ha dibuixat al mapa una botiga/un bar que ja existia, no una obertura real.» |

El lloc de naixement conserva les seves **dues meitats** (la segona és la perillosa): límit de font
**i** que la sèrie del costat —nacionalitat 2021→2025— NO el substitueix, dit en pla: *«qui obté la
nacionalitat espanyola canvia de grup allà, però no aquí»*.

## Taula abans/després (columna ca; l'es és la traducció fidel, fila a fila)

| Mètrica | Abans | Després |
|---|---|---|
| `poblacio` | «EMEX serveix només el darrer període: la seva API (filtres id/i/tipus) no té cap paràmetre temporal — verificat en viu 2026-07-20. Sèrie oficial disponible per una altra via (Idescat censph), ingesta encuada.» | «La font oficial d'on llegim el padró només publica la dada vigent: no en podem ensenyar l'evolució. La sèrie històrica existeix per una altra via oficial i tenim previst carregar-la.» |
| `pob_0_14` / `pob_65_84` / `pob_85_mes` | «Franja d'edat d'EMEX: mateix límit de font que la població (cap sèrie per API).» | «La font oficial només publica la dada vigent de cada franja d'edat: no en podem ensenyar l'evolució.» |
| `pob_15_64` | «Franja d'edat derivada d'EMEX: mateix límit de font que la població (cap sèrie per API).» | «Aquesta franja es calcula restant les altres de la població total, i la font oficial només publica la dada vigent: no en podem ensenyar l'evolució.» |
| `index_envelliment` | «Es deriva de franges d'EMEX, que no tenen sèrie per API.» | «Aquest índex es calcula a partir de les franges d'edat, i d'aquestes la font oficial només publica la dada vigent: no en podem ensenyar l'evolució.» |
| `renda_neta_persona` | «INE ADRH: s'ingereix una sola foto (2023). Sèrie disponible a la font però encara no ingerida.» | «La font oficial sí que en té la sèrie històrica; nosaltres encara no la carreguem. De moment n'ensenyem la darrera dada disponible (2023).» |
| `pct_noprincipal` | «Cens d'habitatge 2021: dada decennal, no hi ha període anterior comparable ingerit.» | «És una dada del Cens d'habitatge del 2021, que es fa un cop cada deu anys: no tenim cap edició anterior comparable per ensenyar-ne l'evolució.» |
| `kg_hab_any` | «Residus (ARC): s'ingereix el darrer any tancat. Sèrie disponible a la font però encara no ingerida.» | «La font oficial (l'Agència de Residus) sí que en té la sèrie històrica; nosaltres encara no la carreguem. De moment n'ensenyem el darrer any tancat.» |
| `kwh_hab` | «Consum elèctric domèstic (ICAEN): s'ingereix el darrer any de cobertura plena. Sèrie disponible a la font però encara no ingerida.» | «La font oficial (l'ICAEN) sí que en té la sèrie històrica; nosaltres encara no la carreguem. De moment n'ensenyem el darrer any amb dades completes.» |
| `vidre_hab` | «Fracció vidre (ARC): s'ingereix el darrer any tancat. Sèrie disponible a la font però encara no ingerida.» | «La font oficial (l'Agència de Residus) sí que té la sèrie històrica del vidre; nosaltres encara no la carreguem. De moment n'ensenyem el darrer any tancat.» |
| `rtc_per_1000hab` | «Registre de Turisme de Catalunya: és un registre viu, es llegeix com a foto del dia de la càrrega; no se'n conserva cap tall anterior.» | «El Registre de Turisme de Catalunya és un registre viu que llegim com una foto del dia de la càrrega: no en conservem cap tall anterior amb què comparar.» |
| `serveis_estab` | «OpenStreetMap (Overpass): cartografia col·laborativa que canvia contínuament i sense calendari, ingerida com una sola consulta […] OSM infra-mapeja el rural i la seva completesa creix amb el temps, així que el mapejat nou i l'obertura real d'un establiment no es poden separar.» | «El recompte surt d'un mapa obert (OpenStreetMap) que es va completant amb el temps: una pujada podria ser que algú ha dibuixat al mapa una botiga que ja existia, no una obertura real. Per això no n'ensenyem l'evolució: ni guardant fotos successives es podria llegir com un canvi real al poble.» |
| `restauracio_estab` | (com serveis_estab, variant «obertures i tancaments») | (com serveis_estab, amb «un bar» en comptes d'«una botiga») |
| `poblacio_nascuda_catalunya` | «Lloc de naixement d'EMEX (f69): mateix límit de font que la població — cap sèrie per API. I la sèrie que hi ha a la vora, la de NACIONALITAT (2021→2025), NO serveix per a aquesta: són conjunts diferents […]» | «La font oficial només publica la dada vigent del lloc de naixement: en tenim la foto d'avui, no l'evolució. I l'evolució que es veu a la targeta de nacionalitat (2021→2025) no serveix aquí: parla d'un altre grup de gent (qui obté la nacionalitat espanyola canvia de grup allà, però no aquí).» |
| `poblacio_nascuda_resta_espanya` | «Lloc de naixement d'EMEX (f72): […] La sèrie de NACIONALITAT (2021→2025) no la substitueix: mesura un altre conjunt de gent. Foto, no evolució.» | «La font oficial només publica la dada vigent del lloc de naixement: en tenim la foto d'avui, no l'evolució. L'evolució de la targeta de nacionalitat (2021→2025) no la substitueix: compta un altre grup de gent.» |
| `poblacio_nascuda_estranger` | «Lloc de naixement d'EMEX (f73): […] Compte amb la sèrie del costat: la de NACIONALITAT estrangera (2021→2025) NO és l'evolució d'aquesta xifra, perquè qui es nacionalitza en surt i aquí es queda.» | «La font oficial només publica la dada vigent del lloc de naixement: en tenim la foto d'avui, no l'evolució. I compte: l'evolució de la nacionalitat estrangera (2021→2025) no és la d'aquesta xifra — qui obté la nacionalitat espanyola surt d'aquell grup però continua havent nascut a l'estranger.» |
| `pct_nascuda_estranger` | «Es deriva del lloc de naixement d'EMEX, que no té sèrie per API. La variació que sí que existeix és la del % de NACIONALITAT estrangera (2021→2025), i no és la mateixa cosa […]» | «Aquest percentatge es calcula sobre el lloc de naixement, del qual la font oficial només publica la dada vigent: en tenim la foto, no l'evolució. L'evolució que sí que es veu al costat és la del % de nacionalitat estrangera, i no és la mateixa: mesura un altre grup de gent.» |

Detalls que s'han MOGUT (no perdut), tots als comentaris del model: filtres id/i/tipus i «verificat
en viu 2026-07-20» (EMEX) · els localitzadors f69/f72/f73 (des de V3-CONTRACTE viuen a
`origin_source` del contracte) · «Overpass», «infra-mapeja el rural» (OSM) · «Idescat censph» (la
via alternativa de la sèrie de població, encuada a next.md).

## Troballes

- **Cap motiu antic era fals.** Verificat contra el que el repo ja sap: el límit d'EMEX es va
  comprovar en viu el 2026-07-20 (D7) · les sèries d'ARC/ICAEN/INE existeixen a la font i la seva
  ingesta és a la cua (next.md, encuats de D7) · la via censph de la sèrie de població està
  verificada i encuada · el RTC és un registre viu sense talls conservats. La reescriptura no ha
  hagut d'estovar ni corregir res: només canviar el registre.
- **⚠️ RISC DE MÈTODE, EXERCIT (el #5 de next.md, «instal·lació editable compartida»):** en córrer
  `pytest packages/ingestion/tests/test_idescat_emex.py` en aquest worktree, `datapoble_ingestion`
  es resolia a **l'arbre d'un altre agent** (worktree `agent-ac46a8c…`), amb l'`_iter_leaves`
  d'abans de D7 → 6 errors que NO eren d'aquest arbre. Vist per la ruta del traceback (com la
  vegada anterior). Re-executat amb `PYTHONPATH` forçat al paquet d'AQUEST arbre: **7/7 verds**.
  El pendent de Talaia «a tancar abans del proper paral·lel de tres» segueix obert i acaba de
  mossegar per segona vegada.

## Com s'ha regenerat el parquet (mateix mètode que D10, fidelitat provada abans)

`data/raw/` és gitignored: no hi ha `dbt build` possible en un checkout net. `mart_tendencia` només
beu de tres marts versionats, així que s'ha reconstruït executant el SQL del model amb els `ref()`
apuntats als parquets versionats. **Abans de tocar res**, la reconstrucció del model *sense canvis*
reprodueix el parquet committejat **valor a valor** (`DataFrame.equals` → True, 20.802 files,
mateixes columnes i dtypes). Després del canvi: **20.802 files exactes** (cap fila nova ni perduda:
només canvien literals de `motiu_ca`/`motiu_es`).

## Verificació LOCAL (Actions avall fins el dia 1; el CI no ha corregut)

Job `data` sencer, en aquest worktree:
- `ruff check packages/transform packages/ingestion packages/signals` — net.
- `verify_contracte` (61 mètriques) · `verify_pols_mensual` (224.439 files, 9 àncores byte-match) ·
  `verify_govern` (6.629 files) · `verify_marts` — OK.
- **`verify_tendencia.py` — OK**: 20.802 files, 947 municipis, 3 mètriques amb sèrie + 18 sense
  (cadascuna amb motiu en ca I es, no copiats — la guarda de paritat d'idiomes segueix verda),
  1.894 Δ d'atur recalculats a mà byte-match, cap fletxa sense període.
- `dbt parse` — OK.
- Tots els `--check`: `derive_fase1` · `validacio_etca` · `tipus_territorial` ·
  `calibracio_intervals` · `export_pernocta_catalunya` · `discrepancia_etca_pernocta` ·
  `senyal_sub1000` · `export_licitacions` · `export_web_municipis` (catalunya + bergueda) ·
  `export_govern_web` · **`export_tauler_web`** (monòlit 31 + 947 shards + `_meta`, invariants
  d'honestedat + guarda anti-fuita electoral) — tots OK.
- `pytest`: antileak 5/5 · EMEX 7/7 (amb el paquet d'aquest arbre, vegeu troballa) · signals 182/182.
- **`node scripts/verify-govern.mjs` (la guarda de Mirador, sobre la dada nova) — OK**: 21 mètriques
  amb tendència, cap `sense_serie` sense motiu, 4/4 lloc de naixement amb el límit declarat.
- Ocular: shard de la Pobla (08166) amb els motius nous en ca i es.

**Lliurament:** PR `sondeig/v3-dades-motius` → `main`. **No fusiono jo.**
