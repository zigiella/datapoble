# Indicador estrella materialitzat: població real estimada vs padró — Sondeig

**Fecha:** 2026-06-05
**Autora:** Sondeig
**Para:** Talaia (review/merge) · Mirador (consumeix el JSON) · Brúixola (FYI fixtures IA)
**Tema:** materialitzar el mètode de Talaia (`docs/poblacio-real-metode.md` §7): afegir a `mart_municipi` les columnes de població real vs padró (BASE parametritzable), declarar-les al contracte semàntic amb caveat, i regenerar el JSON web.
**Status:** avance / handoff

## Contexto
Talaia havia validat i escrit el mètode de l'indicador estrella de *riusdegent*
(fer visible la població invisible) a `docs/poblacio-real-metode.md`, amb la spec de
materialització a §7. Les dades ja hi eren (`mart_municipi`: residus/padró/habitatge;
`mart_consum_electric`: consum domèstic 2013–2024). Calia convertir el mètode en
columnes reals, contracte i JSON web, **sense fingir precisió** (§6 honestedat).

## Qué hicimos / decidimos

### 1 · Columnes noves a `mart_municipi` (dbt), BASE parametritzable
- **5 columnes** segons §7: `poblacio_real_est` (tall absolut, base residencial=410),
  `gap_abs`, `gap_pct`, `poblacio_real_rel` (tall relatiu comarcal=452), `confianca`.
- **BASE parametritzable** via **vars dbt** (`dbt_project.yml`), documentades:
  `base_residencial: 410`, `base_comarcal: 452`, `poblacio_min_confianca: 75`,
  `any_corroborador_electric: 2024`. A escala Catalunya la base serà **per comarca**
  (§8) → només cal canviar la var. Fórmula encapsulada al **macro `poblacio_real()`**
  (`macros/poblacio_real.sql`).
- **Corroborador elèctric SENSE dependència circular.** `mart_consum_electric` ja
  depèn de `mart_municipi` (n'agafa codi6+nom). Si el corroborador de confiança
  vingués del mart, seria circular. Per això vaig crear l'intermediate
  **`int_consum_electric_pc`** que deriva el kWh domèstic/càpita (2024) directament de
  l'**staging** (`stg_icaen_consum`, sector 7) + població d'EMEX. El número és idèntic.
- **Regla de `confianca` (§6), honesta sense por:**
  - `baixa` si `poblacio < 75` (micro-muni, secret estadístic/soroll) **O** si els
    senyals divergeixen (residus alt però elèctric/càpita **i** %no-principal tots dos
    baixos, o al revés).
  - `alta` si `kg_hab_any > mediana comarcal` **I** almenys un corroborador
    (elèctric/càpita 2024 **O** %no-principal) també > mediana **I** `poblacio >= 75`.
  - `mitjana` la resta.

### 2 · Contracte semàntic (`semantic/metrics.yml`)
- Les **5 mètriques** declarades amb `label`+`label_ca`/`label_es`, `definicio` ca/es,
  `formula`, `source: datapoble` + `origin_source: residus` + **`font`** llegible
  (ARC residus + Idescat padró [+ ICAEN per a confianca]), **`categoria: derived`**,
  `visibility: public`, i un camp **`caveat`** ca/es que resumeix §6 (inferència no
  cens, rang no decimal, base sensible = sostre/terra del gap, lectura ecològica,
  caveat de l'elèctric per calefacció de llenya). Respecta l'estructura del fitxer.

### 3 · JSON web (`tools/export_web_municipis.py` → `data/web/municipis.bergueda.json`)
- Afegides les 5 claus a `METRIC_KEYS`/`FORMAT_BY_KEY`/`COL_MUNI`. `confianca` és
  **text** (no numèric) → tractament dedicat (`TEXT_COLS_MUNI`) perquè no es perdi al
  cast a None. Catàleg ara amb **24 mètriques** (eren 19), 31 municipis.
- El catàleg segueix sortint del contracte (label/unit/note/date/dimension/status de
  `metrics.yml`), frontera honesta intacta. `--check` (gate CI futur) **verd**.

### Verificació
- `dbt parse` net (manifest 77 nodes, inclou `int_consum_electric_pc` + els 8 tests
  nous del mart, entre ells `accepted_values` de `confianca`). `dbt compile` de
  `mart_municipi` renderitza la SQL esperada (macro expandit, `cross join med`).
- **No hi ha `data/raw/` al repo** (gitignored): el `dbt build` complet des de la raw
  no corre aquí (i CI no l'executa: el job python segueix sent TODO). Per regenerar
  l'artefacte versionat **`data/marts/mart_municipi.parquet`** vaig executar en DuckDB
  la **transformació equivalent** sobre els parquets versionats (mateixes fórmules que
  el model). Quan torni a haver-hi raw, `dbt build` produeix el mateix parquet.
- **Tots els data_tests passen** (rèplica directa contra el parquet: not_null, between,
  `accepted_values` confianca, rowcount=31, ine5 unique → 0 files fallides).
- `verify_marts.py` **OK** (Castellar/Berga cuadren, Spearman IETR↔residus=0,869): la
  regeneració va preservar exactament les columnes existents.
- **Warehouse de `packages/ai` NO trencat:** carrega `mart_municipi` (parquet real, no
  fixture) i **consulta les columnes noves** (`poblacio_real_est`, `gap_pct`,
  `confianca`) sense error. El catàleg IA només referencia `mart_municipi`+
  `mart_electoral`; les noves mètriques hi apunten i són consultables.

## Por qué
- Separar el **corroborador** del mart elèctric (via staging) evita una dependència
  circular i manté la regla de Talaia: l'elèctric **no es pondera igual** que els
  residus (només puja la confiança quan coincideix; §3). El cas Castellar de n'Hug ho
  il·lustra: elèctric baix (calefacció de llenya) però residus + 2a residència alts →
  `alta` per corroboració no-elèctrica, exactament com prediu el mètode.
- **BASE com a var** (no màgic al SQL) perquè l'escalat a Catalunya és canviar un
  número per comarca, no reescriure el model.
- `confianca` com a **bandera explícita** materialitza "un buit honest val més que un
  fals precís": 9/31 munis queden marcats `baixa` sense maquillatge.

## Distribució de `confianca` (pilot Berguedà)
| Bandera | N | Lectura |
|---|--:|---|
| **alta** | 10 | residus + (elèctric/càpita o 2a res) per sobre de mediana, padró≥75. Inclou els hotspots del gap: Saldes, Gósol, Vallcebre, Castellar de n'Hug, Borredà, Montmajor… |
| **mitjana** | 12 | viles de vall i casos sense corroboració clara. Inclou Berga (residus ≈ mediana; el seu gap_abs gran és artefacte d'escala, §4). |
| **baixa** | 9 | micro-munis (<75 hab: Sant Jaume de Frontanyà, Gisclareny, Fígols, la Quar, Castell de l'Areny) + divergents (Sta Maria de Merlès, Montclar, Castellar del Riu, St Julià de Cerdanyola). |

Agregat comarcal: BASE=410 → **+10,3%** sobre el padró (coincideix amb el mètode,
"~+10–13%"); BASE=452 → +0,1% (≈ suma zero, tall relatiu, coherent).

## Decisiones para Talaia (revisión)
1. **Berga té el gap_abs absolut més gran (+2087)** però surt `mitjana`: el seu
   per-càpita de residus és ~mediana i el gap és efecte de la seva mida (els seus
   residus porten comerç, §4 = sostre de la base). Crec que és el comportament correcte
   (no és un hotspot de presència oculta), però **decideix tu** si vols capar/anotar el
   gap a la capital al frontend.
2. **Fixtures IA (Brúixola):** `packages/ai/fixtures/mart_municipi.csv` **no** té les
   columnes noves i **no l'he tocat** (jurisdicció de Brúixola). Cap eval offline les
   consulta avui → `ai-evals` no s'afecta. Si voleu que la IA respongui sobre la
   població real en mode offline, Brúixola hauria d'afegir-les al fixture.
3. **`data/raw` i CI:** el parquet versionat l'he regenerat amb la transformació
   equivalent (no `dbt build`, perquè no hi ha raw al repo i el job python de CI
   segueix comentat). Quan s'activi el job python + es publiqui la raw, val la pena que
   `dbt build` + `verify_marts.py` + `export --check` siguin el gate (el JSON ja és
   idempotent).
4. **Tall relatiu (`poblacio_real_rel`)** materialitzat com a opcional (§7): és vista
   espacial (suma zero). Si al mapa només voleu un indicador de presència, el principal
   és `poblacio_real_est` (absolut); el relatiu serveix per a "qui acull més dins la
   comarca".

## Pendiente
- [ ] **Talaia:** validar la regla de `confianca` i la decisió sobre Berga (punt 1).
- [ ] **Mirador:** els 5 nous indicadors ja són al JSON com a seleccionables; pintar
      `confianca` (text/banderola) i mostrar el `caveat` al peu (procedència morada =
      inferència).
- [ ] **Brúixola (opcional):** afegir les columnes al fixture IA si es vol cobertura
      offline de la població real.
- [ ] **Escala Catalunya (§8):** `base_residencial` per comarca (var → mapa de bases).

## Enlaces
- `packages/transform/models/marts/mart_municipi.sql` (+5 columnes, macro, med, corroborador)
- `packages/transform/macros/poblacio_real.sql` (fórmula encapsulada, BASE param)
- `packages/transform/models/intermediate/int_consum_electric_pc.sql` (corroborador, sense circularitat)
- `packages/transform/dbt_project.yml` (vars base_residencial/base_comarcal/…)
- `packages/transform/models/marts/_marts.yml` (columnes + tests, accepted_values confianca)
- `semantic/metrics.yml` (5 mètriques derived amb caveat)
- `tools/export_web_municipis.py` → `data/web/municipis.bergueda.json` (24 mètriques, 31 munis)
- `data/marts/mart_municipi.parquet` (regenerat amb les columnes noves)
- `docs/poblacio-real-metode.md` (mètode de Talaia, materialitzat)
