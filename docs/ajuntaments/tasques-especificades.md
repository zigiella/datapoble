# Tasques especificades — track ajuntaments (R1 · D1 · X1)

**Estat: ⏸ EN ESPERA DEL TRET DE SORTIDA DE BEA — cap front comença fins al latido.**
Especificades per Talaia (2026-07-16) amb **àncores verificades en viu** (cap URL de documentació
caducada). Contractes vinculants fusionats: C1–C6 a `docs/ajuntaments/`. Cada tasca = 1 PR;
verificació adversarial de Talaia abans de fusionar.

---

## R1 · Connector BDNS (Sondeig) — `packages/signals/datapoble_signals/subvencions_bdns.py`

**Contractes:** C3 (fitxa + clau d'identitat) · C4 §2 (les fixtures que arxivis serveixen per al banc).

**API verificada en viu (2026-07-16, 6 crides reals, JSON, sense clau):**
- Llistat/cerca: `https://www.infosubvenciones.es/bdnstrans/api/convocatorias/busqueda` — paràmetre
  **obligatori** `vpd=GE`; paginació Spring (`page` base 0, `pageSize`, `order=fechaRecepcion`,
  `direccion=desc`; resposta `content[]`, `totalElements`).
- Fitxa completa: `…/api/convocatorias?vpd=GE&numConv=<codigoBDNS>`.
- Filtres verificats: `fechaDesde`/`fechaHasta` (**format petició `dd/MM/yyyy`; resposta `yyyy-MM-dd`** —
  no els confonguis) · `regiones=` ids NUTS.
- ⚠️ **TRAMPA VERIFICADA — la regió pare NO cascada als fills:** `regiones=49` (Catalunya) sol retorna
  ~1/4 de les convocatòries reals. **Sempre `regiones=49,50,51,52,53`** (CAT+BCN+GIR+LLE+TAR).
  Test obligatori que ho cobreixi.
- Mapa a la fitxa C3: `codigoBDNS`→id · `organo.nivel1/2/3`→organisme · `descripcion` +
  **`descripcionLeng`** (sovint en català — guarda'l)→objecte · `tiposBeneficiarios[]`→beneficiaris ·
  `regiones[]`→àmbit · `presupuestoTotal`→import · `fechaRecepcion`/`fechaInicioSolicitud`/
  `fechaFinSolicitud`/`abierto`→dates i estat · `urlBasesReguladoras` + fitxa pública
  `https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias/<codigoBDNS>`→enllaç.
- El filtre `tiposBeneficiario` és massa gruixut (5 tipus genèrics; cap «ajuntaments») — **el filtre fi
  és feina de R2**, no d'aquest connector. `tipoAdministracion=L` filtra qui CONVOCA, no qui rep:
  no els confonguis a la fitxa.

**Llistó (criteris d'acceptació):**
1. Batch diari educat: `busqueda` amb `fechaDesde=fechaHasta=ahir` + les 5 regions + detall per novetat;
   poques crides, backoff, User-Agent identificat. (La resposta porta un avís legal contra l'abús:
   respectar-lo és part del llistó.) Fallback entre els 4 hosts mirall (`infosubvenciones.es`,
   `pap.hacienda.gob.es`, `subvenciones.gob.es`, `infosubvenciones.gob.es`).
2. Dedupe per la clau C3 (`bdns:<codigoBDNS>`); re-sync per `codigoBDNS` (la BDNS corregeix i ESBORRA
   a posteriori — cap assumpció d'immutabilitat).
3. Fixtures reals arxivades al repo (≥15 convocatòries variades, incloent-ne de locals catalanes) —
   CI 100% offline sobre fixtures; **aquestes fixtures són candidates al banc C4** (tria'n de bones).
4. Test de la trampa de codis (C3 §5) + test de la trampa de regions.
5. Cap sortida (correu/JSON públic): això és R4, i només per a perfils `actiu: true`.

---

## D1 · Connector atur mensual (Sondeig) — `packages/ingestion/datapoble_ingestion/atur_sepe.py`

**Contractes:** C1 §1.1 **ESMENAT** (la font Socrata de l'spec era falsa — verificat en viu; llegeix
la secció sencera abans de començar).

**Font verificada en viu:** SEPE «Paro registrado por municipios», CSV anual-amb-mesos:
`https://sede.sepe.gob.es/es/portaltrabaja/resources/sede/datos_abiertos/datos/Paro_por_municipios_<ANY>_csv.csv`
(des de 2006; sense clau; camps: `Código mes` AAAAMM · `Codigo Provincia` · `Codigo Municipio` ·
`total Paro Registrado` + desagregació sexe×edat i per sector).

**Llistó:**
1. Descàrrega completa + filtre local `Codigo Provincia=8` → sèrie mensual dels 31 municipis del
   Berguedà → `mart_pols_mensual` (camp `date` `"YYYY-MM"`, C1 §1.1).
2. **Doctrina del «<5» (C1, vinculant):** els valors emmascarats `<5` es modelen com a interval [1,4] —
   MAI zero, MAI NaN silenciós; el mart els porta com a interval i la UI els mostra «<5». Test amb un
   municipi petit real que en tingui.
3. **Zero-pad del codi INE a 5** (el SEPE els serveix sense zeros) + test de la trampa de codis
   (08052/08166; Idescat 6 dígits amb control → tall `[:5]`).
4. Byte-match de 3 municipis contra el CSV font (llistó del contracte).
5. Fixture arxivada (mes real, retallada a la província 8) — CI offline; refresh al workflow existent
   (`daily-report` o equivalent), MAI al CI de PR.
6. Bloc `sources:` de `metrics.yml` complet (organisme, producte, URL patró, llicència verificada
   literalment) abans que cap mètrica citi `source: sepe`.

---

## X1 · Collita C5 (Brúixola) — `packages/ai`

**Contracte:** C5 sencer (vinculant, llegir abans de res). Prerequisit ✅ (X0 fet: actes a
`packages/geo-rag/data/`).

**Abast del PR:**
1. **Doctrina** d'estatuts i to a `packages/ai`: oficial/senyal/soroll · bandes (el rang és la dada) ·
   col·lisió · empat · fora-de-catàleg — els DOS silencis diferents; la precedència apresa (primer el
   tipus de consulta i el veredicte de comparació, després el registre; catàleg s'enumera; veïns es
   responen). Font: `packages/geo-rag` (router/compare/distinguish) — **adaptat als marts, no copiat**
   (els camps del mart no són el substrat de l'experiment).
2. **Gàbia amb RE-VALIDACIÓ** (C5 §2, la lliçó de l'annex #238): validació dura determinista (cap
   número que no traci a cel·la del mart; agregats només si ja vénen comptats; talls marcats) →
   validador cec **v2** (`prompts/validador-cec-v2-CONGELAT.md` del geo-rag — el prompt de sistema NO
   s'edita; si el context del mart difereix, s'adapta el missatge d'usuari) → si el text final no
   compleix, **fallback determinista** (text→SQL traçable). Mai servir generatiu sense gàbia completa.

**Llistó:**
1. Tests offline verds amb `OfflineBackend`; cap test depèn de xarxa ni de claus.
2. Eval end-to-end amb fixture: pregunta → resposta determinista → generatiu engabiat → re-validat →
   (cas de fall provocat) → fallback comprovat per test.
3. `politics.py` INTACTA + **test nou que la porta política mana sobre el generatiu** (cap resposta
   generativa sobre `dimension: politica`).
4. Pin `openai>=1.30` (el `==2.44.0` del geo-rag NO es propaga); cap dependència de torch/duckdb de
   l'experiment.
5. SpendGuard cobreix la crida extra de re-validació; sostre exhaurit → fallback determinista.
6. `packages/geo-rag` sense canvis (opcional: segell «collit a X1» al README) — les actes són història.
