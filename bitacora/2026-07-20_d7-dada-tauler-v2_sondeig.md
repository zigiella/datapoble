# D7 · la dada del tauler v2 — Sondeig (2026-07-20)

Capa de DADES de les esmenes **E4, E5, E6, E11, E12** de
`docs/ajuntaments/tauler-v2-esmenes-bea.md` (vinculant). El web el fa Mirador en paral·lel.

**Resum en una línia:** les franges d'edat ja hi eren i el mart les llençava (ara es
publiquen); l'atur ja hi era i el web no el podia llegir (ara sí, amb sèrie i tendència);
la tendència existeix **només on hi ha sèrie** i la resta ho diu en veu alta; i la frescor
és al contracte —inclòs el fet incòmode que **una sola font de deu té procés de refresc**.

---

## 1. Verificació d'EMEX (E11): **NO hi ha sèrie**. És un límit de la font, no un pendent

L'encàrrec deia «verifica en viu si l'API d'EMEX permet demanar una SÈRIE per municipi o
només l'últim». Resposta verificada: **només l'últim.**

Evidència (2026-07-20), dues vies independents:

1. **Documentació oficial** (`https://www.idescat.cat/dev/api/emex/`) — l'operació `dades`
   declara exactament tres filtres: `id`, `i` i `tipus`. **Cap de temporal.**
2. **Proves en viu** contra `https://api.idescat.cat/emex/v1/dades.json?id=080522&i=f321`
   amb set candidats de paràmetre temporal (`t`, `any`, `periode`, `r`, `tt`,
   `tipus=serie`, `serie`). Els set **s'ignoren en silenci**: el camp `p` de la resposta
   (que fa d'eco dels paràmetres ACCEPTATS) segueix dient només `id=080522;i=f321`, i el
   valor tornat continua sent el de 2025. No donen error — cosa que fa la trampa pitjor:
   qui no comprovi l'eco es pensarà que ha demanat 2020 i estarà publicant 2025.

**Conseqüència honesta:** la població i les franges d'edat surten a `mart_tendencia` amb
estat `sense_serie` i el motiu escrit. No és un TODO disfressat; és el que hi ha.

### La premissa de l'encàrrec era falsa (i era mig-veritat pitjor que una mentida)

L'encàrrec deia «l'ingestor d'EMEX **ja porta `year`** a la fila crua». La **columna** hi
era; **el valor, no**: `year` sortia **NULL a 12 dels 13 indicadors**. Causa: a l'EMEX
l'any de referència (`r`) viu al node de la **taula**, no a la **fulla**, i el recorregut
només llegia `leaf["r"]` — de manera que l'únic indicador amb any era `altitud_m`, que
casualment en porta un de propi.

Esmenat: `_iter_leaves` ara **hereta** l'`r` de l'avantpassat més proper. El que apareix en
arreglar-ho és el moll de l'os de l'E5 — **els vintages no són tots el mateix**:

| Indicadors | `r` real | Què és |
|---|---|---|
| f321 població · f167/f28/f29 franges d'edat | **2025** | Cens de població **anual** |
| f122/f250/f398 habitatges | **2021** | Cens d'**habitatge** (decennal) |

Un tauler que pinti les dues coses amb la mateixa data menteix. Per això `hab_*` porta ara
`actualitzacio: puntual` al contracte encara que la seva font es refresqui cada any.

**No s'ha re-ingerit** la raw en aquest PR: la correcció queda al codi (amb test) i actuarà
a la propera càrrega. Re-ingerir 947 municipis aquí hauria barrejat una deriva de dades
amb un canvi d'estructura, i llavors cap dels byte-match d'aquest PR voldria dir res.

### L'alternativa oficial existeix — verificada, i **encuada**, no muntada

`https://www.idescat.cat/pub/?id=censph&n=538&geo=mun:{codi6}&f=ssv` torna la **sèrie
sencera de població** per municipi (1975→2025, per sexe i total). És el **mateix patró
`f=ssv`** que el repo ja fa servir per a `stg_demografia_estrangera_serie`, o sigui que la
via està provada. Porta la ruptura de font documentada a la capçalera (1975-1986 Padró ·
1991 Cens · 1996 Estadística · 2001-2021 Cens INE · 2022-2025 Cens anual INE) — cosa que
**s'haurà d'etiquetar**, no aplanar. Encuat amb motiu (§5), no fet: l'encàrrec deia
explícitament de no muntar-la sencera aquí.

---

## 2. Franges d'edat (E12) — **quadren**, i s'ha comprovat contra la font

Ja s'ingerien (`pob_0_14`, `pob_65_84`, `pob_85_mes`) i `mart_municipi` les feia servir per
a `index_envelliment` **i les llençava**. Ara s'exposen al mart, al contracte i a l'export web.

La **franja intermèdia (15-64) no la serveix EMEX**: es deriva per resta, i l'encàrrec era
«només si quadra». Quadra, i amb dues comprovacions independents:

- **Partició exacta als 947**: cap NULL a cap franja, cap resta negativa, mínim observat 13.
- **Reconciliació externa**: la suma dels 947 municipis casa **exactament** amb el total de
  Catalunya que serveix la mateixa API — població 8.124.126 · 0-14 1.079.859 · 65-84
  1.356.476 · 85+ 245.511 → **15-64 = 5.442.280**, zero residu d'arrodoniment.

La regla queda **guardada**, no només verificada un cop: `pob_15_64` s'emet NULL si algun
component falta o si la resta surt negativa, i el test
`assert_mart_municipi_franges_edat.sql` fa caure el build si algun dia deixa de quadrar.

Àncora a mà (la Pobla de Lillet): 1106 = 98 + 609 + 322 + 77.

---

## 3. Atur al web (E4) + tendència (E6)

**`mart_tendencia`** (nou, format llarg per `ine5 × metric × comparacio`) i
**`tools/export_tauler_web.py`** → `data/web/tauler.bergueda.json`.

L'export **neix amb `--check` cablat al CI el mateix dia**. No es repeteix el forat de
D4/D5, on el mart existia, el JSON web no, i el `--check` va haver d'arribar en un PR
posterior (#272).

### On hi ha sèrie i on no

| Estat | Mètriques |
|---|---|
| `amb_serie` | `atur_registrat` (**dues** comparacions) · `pct_nacionalitat_estrangera` · `poblacio_nacionalitat_estrangera` |
| `sense_serie` | població · les 4 franges · `index_envelliment` · renda · `pct_noprincipal` · residus · `kwh_hab` · vidre · RTC |

Les 12 `sense_serie` **hi són com a files explícites amb el motiu escrit**, no com a
absències. Una absència es llegeix com un zero; un `sense_serie` amb motiu, no.

### Per què l'atur porta DUES comparacions

Perquè amb una de sola el tauler tria la narrativa. La Pobla de Lillet, juny de 2026:

| Comparació | Períodes | Δ | Direcció |
|---|---|---|---|
| mes anterior | 2026-05 → 2026-06 | 27 → 31 = **+4** | **puja** |
| mateix mes de l'any anterior | 2025-06 → 2026-06 | 34 → 31 = **−3** | **baixa** |

La mateixa xifra puja o baixa segons contra què la miris. S'emeten totes dues.

### El «<5» propagat al Δ

Si un dels dos mesos ve emmascarat, **la diferència no és un número: és un interval**.
`delta = NULL` + `delta_min`/`delta_max`. Restar l'emmascarat com si fos zero seria
inventar-se el signe. Capolat, juny 2026 (emmascarat, [1,4]):

- vs mateix mes any anterior (2025-06 = 0 exacte) → Δ ∈ **[1,4]** → direcció **`puja`**, PROVADA.
- vs mes anterior (també emmascarat) → Δ ∈ **[−3,3]** → **`indeterminat`** explícit.

`indeterminat` és una resposta, no un buit: el front ha de poder dir «amb el <5 no es pot
dir», que és diferent de callar. 329 files amb interval, 217 indeterminades.

### Guardes al CI

`packages/transform/verify_tendencia.py` (offline) — **recalcula A MÀ des de
`mart_pols_mensual` els 1.894 Δ d'atur** (947 × 2 comparacions) i els compara byte a byte
amb el mart, i comprova: cap fletxa sense període · cap `sense_serie` amb Δ ni sense motiu ·
cap Δ exacte sobre un punt emmascarat · cap direcció que l'interval no provi · les àncores
de la Pobla. Les xifres d'origen casen amb les que Bea cita al seu propi document
(**+5,61 punts, +64 persones**, finestra 2021→2025).

---

## 4. Frescor (E5) — al contracte, i l'inventari nu

Tres camps nous a `sources.<font>` de `semantic/metrics.yml`: `actualitzacio`
(`mensual|anual|puntual|irregular`), `darrera_carrega` i `proces_refresc`. Una mètrica pot
sobreescriure `actualitzacio` quan la seva cadència no és la de la font. Arriben al web al
catàleg `metrics` de `municipis.*.json` (camp `frescor`) i al `_meta` del tauler.

### Inventari de processos de refresc — la veritat nua

| Font | Cadència | Darrera càrrega | Procés que la refresca |
|---|---|---|---|
| **sepe** (atur) | mensual | 2026-07-05 | ✅ `.github/workflows/refresh-atur.yml` |
| idescat_emex | anual | 2026-06-21 | ❌ **cap** |
| idescat_pobestr | anual | 2026-06-21 | ❌ **cap** |
| residus (ARC) | anual | 2026-06-21 | ❌ **cap** |
| icaen_consum | anual | 2026-06-21 | ❌ **cap** |
| ine_adrh (renda) | anual | 2026-06-21 | ❌ **cap** |
| rtc | irregular | 2026-06-21 | ❌ **cap** |
| osm_overpass | irregular | 2026-06-27 | ❌ **cap** |
| electoral | puntual | 2026-06-21 | ❌ cap (i no en cal: entre eleccions no canvia) |
| icaen (certificats) | irregular | **mai** | ❌ connector no escrit (`pct_icaen_EFG` = buit declarat) |

**1 de 10 té procés.** `cap` queda escrit al contracte com a declaració, no com a oblit: el
tauler ha de poder dir «anual · darrera càrrega: 2026-06-21 · sense procés automàtic».

### Per què no he afegit cap cron més (i no és peresa)

L'encàrrec deia «si alguna cron és trivial d'afegir, afegeix-la». **Cap ho és**, i la raó és
arquitectònica, verificada:

`refresh-atur.yml` va poder existir perquè **`mart_pols_mensual` està deliberadament
desacoblat** — no fa `ref('mart_municipi')` (ho diu la seva pròpia capçalera), així que
refrescar l'atur només toca la seva branca.

Les altres nou fonts **convergeixen totes a `mart_municipi`**, i refrescar-ne una qualsevol
arrossega: **4 marts** avall (`mart_consum_electric`, `mart_electoral`, `mart_govern`,
`mart_tendencia`) i **7 verificadors/exportadors amb artefacte `--check`** versionat
(`derive_fase1`, `verify_marts`, `validacio_etca`, `tipus_territorial`,
`export_web_municipis`, `export_bergueda_bundle`, `calibracio_intervals`). Una cron per font
que refés només la seva part deixaria la resta de la cadena estale i **posaria el CI en
vermell al PR següent** — exactament el forat que aquest PR tanca per a l'atur.

**El que cal no són cinc crons anuals, sinó UN refresc anual de pipeline sencer.** Encuat
amb el motiu (§5). Dir-ho és més honest que afegir quatre crons que trencarien la porta de main.

---

## 5. Encuat (amb motiu, no oblidat)

1. **Sèrie de població (E11)** — ingerir `censph` via `f=ssv` (via verificada, §1) i
   deixar la sèrie al mart. Cal etiquetar la **ruptura de font** de 1975→2025, no aplanar-la.
   Amb això, població i franges passarien de `sense_serie` a `amb_serie`.
2. **Refresc anual de pipeline sencer** — un workflow que reingereixi les fonts anuals i
   regeneri **tota** la cadena avall (§4). Substitueix les crons per font, que no són viables.
3. **Sèries de residus, ICAEN i renda** — les tres fonts **sí que en tenen**; el pipeline
   n'ingereix una sola foto. Desbloquejaria la tendència de 4 targetes més del tauler.
4. **`mart_electoral` i `mart_consum_electric` versionats estan ESTALE** — troballa
   col·lateral d'aquest PR. Els parquets committejats són de l'època del pilot (31 munis /
   372 files); els seus models ja cobreixen tot Catalunya (947 / 11.364). Reconstruir-los
   **NO s'ha fet aquí**: publicaria dades electorals de 947 municipis com a efecte lateral
   d'una tasca de tauler, i la política editorial d'aquesta capa és de Bea. **Handoff a: Talaia.**

---

## 6. Handoff a: Mirador — què tens de nou i com llegir-ho

**A. Franges d'edat** — a `data/web/municipis.{bergueda,catalunya}.json`, dins
`municipis[ine5].values` i amb entrada al catàleg `metrics`:
`pob_0_14` · `pob_15_64` · `pob_65_84` · `pob_85_mes` · `pob_65_mes`.
⚠️ `pob_15_64` és **derivada** i pot venir `null` si un dia no quadra: tracta-la com a
opcional. Avui no és null enlloc.

**B. Frescor** — cada entrada del catàleg `metrics` porta ara
`frescor: { actualitzacio, darrera_carrega, proces_refresc, font_frescor }`.
`proces_refresc: "cap"` **s'ha de poder mostrar** (és el punt de l'E5): una dada anual
sense procés és honesta si es diu.

**C. Atur + tendència** — fitxer **nou** `data/web/tauler.bergueda.json`:
```
municipis[ine5].atur.darrer      → { date, valor, min, max, emmascarat }
municipis[ine5].atur.serie       → 25 punts (darrer mes + 24 enrere)
municipis[ine5].tendencia[metric] → LLISTA d'entrades (l'atur en té DUES)
_meta.atur.frescor / _meta.atur.darrer_mes
```
Regles de pintat que la dada ja et garanteix:
- `valor: null` + `emmascarat: true` + `min/max` = «<5». **Mai ho pintis com a 0.**
- Tota entrada de tendència amb `direccio` porta `periode_actual` i `periode_anterior`:
  **la fletxa sempre pot dir contra què compara**, i ha de dir-ho.
- `estat: "sense_serie"` → hi ha `motiu` escrit. Pinta el motiu, no una fletxa grisa.
- `direccio: "indeterminat"` → l'interval travessa el zero. Diu «no es pot dir amb el <5».
- `delta: null` amb `delta_emmascarat: true` → mostra l'interval `[delta_min, delta_max]`.

**D. Un fitxer teu que jo NO he tocat** (jurisdicció): `packages/web/src/lib/contract/types.ts`.
`MetricKey` és una unió tancada i li falten les 5 claus noves, i `MetricDef` no declara
`frescor`. **El build NO cau** (el loader fa `as MunicipisDataset`, un cast sense validació
en temps d'execució), però no podràs consumir-ho amb tipus fins que hi afegeixis:
```ts
| 'pob_0_14' | 'pob_15_64' | 'pob_65_84' | 'pob_85_mes' | 'pob_65_mes'
```
i a `MetricDef`:
```ts
frescor?: {
  actualitzacio: string | null;
  darrera_carrega: string | null;
  proces_refresc: string | null;
  font_frescor: string | null;
};
```

---

## 7. Llistó

- CI offline **verd**: ruff net · `dbt parse` · 14 tests atur + **7 tests EMEX nous** ·
  180 tests signals · `verify_marts` · `verify_pols_mensual` · `verify_govern` ·
  **`verify_tendencia` nou** · els 8 `--check` d'export (inclòs el nou).
- **Suite d'ai verda**: 210 tests (llegeix `metrics.yml`, que aquest PR toca).
- **`export_tauler_web.py --check` cablat al CI** el mateix dia que neix l'exportador.
- **Franges**: sumen als 947 i casen amb el total de Catalunya de la font; la regla està
  guardada per un test de dbt, no només verificada.
- **Cap Δ sense període declarat** (guarda al verificador, no només al model).
- **Byte-match de Δ d'atur a mà**: 1.894 recalculats des de `mart_pols_mensual`; àncores
  de la Pobla (+4 / −3) i d'origen (+5,61 / +64) casades amb el document de Bea.
