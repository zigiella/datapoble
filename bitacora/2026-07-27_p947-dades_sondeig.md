# P-947 · capa de dades: els exports web de govern i tauler, dels 31 als 947 (Sondeig)

**Data:** 2026-07-27 · **Agent:** Sondeig · **Tasca:** P-947 (cua de Bea, 2026-07-27) —
el MATEIX dashboard per a TOTS els municipis de Catalunya, amb rangs per comarca.
**Lliurament:** un PR · **branca:** `sondeig/p947-dades` · **no fusiono jo** (verifica i fusiona Talaia).

## Què s'ha fet

Els dos exports web que fins ara es cenyien al Berguedà (31) ara emeten TAMBÉ els 947:

- **`tools/export_govern_web.py`** → afegeix `data/web/govern.catalunya.json` (947 munis,
  les 7 mètriques de govern amb rang «k de n» LLEGIT del mart contra la comarca del PROPI
  municipi). El monòlit `govern.bergueda.json` (31) es manté **byte-idèntic**.
- **`tools/export_tauler_web.py`** → afegeix `data/web/tauler/<ine5>.json` (947 shards per
  municipi) + `data/web/tauler/_meta.json` (metadades compartides). El monòlit
  `tauler.bergueda.json` (31) es manté **byte-idèntic**.
- **Guarda anti-fuita** (`assert_no_electoral`) cablada als dos exports + test amb dents
  (`tools/tests/test_export_web_antileak.py`) + pas al CI.

El rang comarcal ja el calcula `mart_govern` contra la comarca del propi municipi (43
comarques, verificat: Gombrèn → k de 19 del Ripollès, no dels 31 del Berguedà). Aquí NO es
recalcula res: es re-serialitza el que el mart afirma. Els tres marts (`mart_govern`,
`mart_pols_mensual`, `mart_tendencia`) **ja cobrien els 947** — la feina era d'EXPORT, no de mart.

## DECISIÓ D'ARQUITECTURA — forma del tauler (amb el número a la mà)

El brief avisava: `tauler.bergueda.json` fa ~800 kB per a 31; a 947 seria un blob monolític.
Mesurat de debò abans de decidir:

| Artefacte | Mida a 947 | Veredicte |
|---|---|---|
| **govern** (7 mètriques, sense sèries) | **673 kB** en UN fitxer | un sol fitxer va bé |
| **tauler monòlit** (indent=2) | **24,1 MB** | inacceptable (la fitxa el carregaria sencer) |
| **tauler monòlit** (compacte) | **17,3 MB** | inacceptable (blob al repo + al navegador) |
| **tauler shard/municipi** (compacte) | **~18,7 kB de mediana** × 947 = 16,4 MB total | ✅ triat |
| **tauler `_meta.json`** (sidecar compartit) | **1,3 kB** | ✅ |

**Triat: un fitxer per municipi** (`data/web/tauler/<ine5>.json`) + un sidecar `_meta.json`.
Motius, per ordre de pes:

1. **El navegador.** La fitxa es prerenderitza per municipi (947×2). Amb shards, cada pàgina
   només llegeix el SEU (~19 kB) + el `_meta` (~1 kB); amb el monòlit incrustaria 17-24 MB
   per pintar UN poble. És el problema que el brief demanava no enviar en silenci.
2. **El repo.** El monòlit committejat serien 17 MB que a més **es reescriuen cada mes**
   (l'atur és mensual); un diff de 17 MB no és revisable. Els shards eviten el blob del tot.
3. **Precedent existent.** `copy-data.mjs` ja parteix `municipis.catalunya.json` (1,8 MB) en
   `static/data/muni/<ine5>.json` a build-time. Aquí resolem la mateixa forma **a l'origen**
   (data/web) en comptes de committejar un monòlit 13× més gran que aquell i partir-lo després
   → Mirador només ha de COPIAR el directori (no escriure lògica de split).

**Cost assumit i documentat:** el repo guanya 948 fitxers nous (~16,4 MB) a `data/web/tauler/`,
i el refresc mensual de l'atur (`refresh_atur.py` → `export_tauler_web.py`) els reescriu TOTS
cada mes (l'atur canvia a tots els municipis). És el cost inherent de committejar dada derivada
per municipi; git ho delta bé i cada fitxer és petit i inspeccionable (millor que un blob). El
`--check` compara el conjunt SENCER del directori — inclosos els fitxers **estranys** (un
municipi retirat deixaria un shard orfe que es llegiria com a dada viva), no només els estale.

## Guarda anti-fuita (per a la tranquil·litat de Bea)

`forbidden_metric_keys(contract)` deriva del contracte el conjunt prohibit —tota mètrica
`dimension: politica` **o** `source: electoral` **o** `table: mart_electoral`— i
`assert_no_electoral` peta l'export (write I `--check`) si en trobés cap a la sortida. A dia
d'avui el conjunt prohibit són 4 (`pct_indep`, `pct_esquerra`, `pct_extrema_dreta`, `guanya`),
totes de `mart_electoral`, i **cap** apareix ni a govern (7 mètriques) ni al tauler (21 de
tendència + atur). El test `test_export_web_antileak.py` li dona **dents**: comprova que la
DETECCIÓ troba les 4 del contracte real (si tornés buit, la guarda seria decorativa) i que la
guarda REALMENT peta amb una mètrica injectada. Els marts d'origen (`mart_govern`,
`mart_tendencia`, `mart_pols_mensual`) no porten cap columna electoral; la guarda protegeix
contra un descuit FUTUR (columna nova, canvi de contracte) en obrir-ho a 947.

## Municipis amb buits honestos (i per què) — mai un 0 fabricat

**Govern (947):** els 947 porten les **7 files** senceres (cap fila absent). 21 cel·les de
6.629 surten amb `rang: null` perquè el VALOR és null (secret estadístic), no per omissió:
- **`renda_neta_persona`: 20 munis** sense renda publicada (l'AEAT la suprimeix en poblacions
  petites) — repartits per comarques (Anoia, Moianès, Osona, Lluçanès, Val d'Aran ×2, Noguera,
  Pallars Sobirà, Garrigues, Segarra…), no un patró geogràfic.
- **`index_envelliment`: 1 muni** (43057, Baix Camp) sense el ràtio.
La fila hi és amb `valor: null` + `rang: null`; una absència es llegiria com un zero, un null no.

**Tauler (947):** cobertura **947/947** (cap municipi del territori sense shard), **0** shards
amb sèrie d'atur buida, **0** amb tendència buida. Buits honestos declarats:
- **139 munis** tenen el DARRER mes d'atur (juny 2026) emmascarat «<5» → surt com a interval
  `[1,4]` amb `emmascarat: true`, MAI un zero (doctrina C1 §1.1, intacta a 947).
- Les mètriques de **foto sense sèrie** (edat, `pct_nascuda_estranger`, `pct_noprincipal`,
  `index_envelliment`, `kwh_hab`, `kg_hab_any`…) surten com a `sense_serie` amb el motiu
  escrit EN ELS DOS IDIOMES als 947 (el límit de font que D7 va destapar: EMEX no serveix
  sèrie). L'`invariants()` d'honestedat es va córrer sobre els 947 i **va passar** (cap fletxa
  sense període, cap emmascarat amb valor, cap `sense_serie` sense motiu bilingüe).

## Premisses del brief que he trobat FALSES / matisades

1. **«Emet els 947» ≠ substituir el Berguedà en silenci.** El brief llegeix com un canvi net
   (govern.bergueda → 947). **No es pot fer atòmicament entre jurisdiccions:** el verificador
   `verify-govern.mjs` (Mirador, `npm run verify:govern`, i al CI) i el prebuild `copy-data.mjs`
   LLEGEIXEN `govern.bergueda.json` i `tauler.bergueda.json` de manera **fatal** (el verificador
   peta si falten). Esborrar-los ara trencaria la guarda de Mirador i el build. Per això **mantinc
   els dos monòlits del Berguedà frescos i byte-idèntics** i AFEGEIXO l'abast 947; la migració i la
   retirada dels monòlits és de Mirador (handoff avall). Conseqüència verificada: el meu PR
   **no toca res observable** del Berguedà (verify-govern.mjs → OK 0 errors).
2. **La «mida de fitxer» del tauler no és l'únic risc; el `_meta` compartit també.** El monòlit
   duia `contractVersion` + `abast` + `_meta` (frescor, doctrina, darrer mes) a l'arrel. Duplicar-ho
   a 947 shards serien ~947 kB de text repetit i risc d'incoherència → va a un sidecar `_meta.json`.
3. **`govern.json` «~1-2 MB a 947»** → mesurat **0,67 MB**. Un sol fitxer, confirmat.

## Handoff escrit ➡️ Mirador (obrir la porta del web als 947)

La capa de dades hi és; el que falta és `packages/web` (jurisdicció de Mirador). Perquè la
fitxa renderitzi per a qualsevol dels 947:

- **`packages/web/scripts/copy-data.mjs`:** (a) canviar la font de govern de
  `data/web/govern.bergueda.json` → `data/web/govern.catalunya.json` (name `govern.json`);
  (b) el tauler ja NO és un fitxer: COPIAR el directori `data/web/tauler/` → `static/data/tauler/`
  (947 shards + `_meta.json`), tal com `buildMuniSplit` ja fa amb `muni/`.
- **`packages/web/src/routes/municipi/[slug]/+page.ts`:** (a) treure/eixamplar la porta
  `isBergueda` de govern I tauler (C6 §1.2) perquè carregui per a qualsevol `ine5`; (b) govern
  segueix sent un `fetch('/data/govern.json')` sencer indexat per `ine5` (947, va bé a 0,67 MB);
  (c) el tauler passa de `fetch('/data/tauler.json')` (monòlit) a `fetch('/data/tauler/'+ine5+'.json')`
  (shard) + un sol `fetch('/data/tauler/_meta.json')` per al `taulerMeta` (el sidecar té la mateixa
  forma `{contractVersion, abast, _meta}` que l'arrel del monòlit → `sidecar._meta` == `all._meta`).
- **`packages/web/scripts/verify-govern.mjs`:** quan migri a l'abast 947, apuntar a
  `govern.catalunya.json` + el directori `tauler/`. **Fins llavors NO el toco: llegeix els
  monòlits del Berguedà, que mantinc frescos.**
- **Un cop Mirador hagi migrat copy-data + loader + verify-govern:** es pot retirar l'emissió dels
  monòlits del Berguedà d'aquests dos exports (blocs delimitats al codi: `OUT_BERGUEDA` /
  `render_monolith`). És una tasca de neteja meva, encuada rere la porta de Mirador.

## Verificació LOCAL (el CI per-PR NO corre fins el dia 1 — Bea 2026-07-27)

- `python tools/export_govern_web.py` → OK (31 · 22,0 kB · byte-idèntic; 947 · 672,8 kB).
- `python tools/export_tauler_web.py` → OK (31 · 802,3 kB · byte-idèntic; 947 shards + _meta · 16,4 MB).
- `python tools/export_govern_web.py --check` → **OK** (31 + 947).
- `python tools/export_tauler_web.py --check` → **OK** (monòlit + 947 shards + _meta; detecta estale/absent/estrany).
- `pytest tools/tests/test_export_web_antileak.py -q` → **5 passed**.
- `ruff check` dels 4 fitxers tocats de `tools/` → **All checks passed**.
- `git diff --stat` de `govern.bergueda.json` + `tauler.bergueda.json` → **buit** (byte-idèntics).
- `node packages/web/scripts/verify-govern.mjs` → **OK, 0 errors** (el meu PR no trenca la guarda de Mirador).
- Cobertura: govern 947/947 (7 files c/u) · tauler 947/947 shards, 0 territori sense shard.

**No fusiono jo.** Handoff a Mirador per obrir la porta del web.
