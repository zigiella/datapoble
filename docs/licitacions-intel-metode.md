# Licitacions com a intel·ligència institucional — mètode (PAS 1)

*Cabal (pilar 2, el cabal) · 2026-06-08. Capa d'intel·ligència institucional de
contractació. Base de feina: `docs/feedback-consultora-i-roadmap.md` §4.1.*

> «Una licitació és una **confessió administrativa**.» El cabal passa de *rastre
> lateral* a **capa de capacitat institucional**: no preguntem només *quant es
> gasta*, sinó *què revela un contracte sobre el metabolisme i la dependència d'un
> municipi*.

Aquest document és **el mètode del PAS 1**: la taxonomia territorial, la
classificació heurística dels 1.295 events, el repartiment supramunicipal declarat
i el primer indicador. **NO** és l'sprint sencer: l'LLM sobre `altres`, la
validació manual de 300 contractes i els altres 4 indicadors són el **PAS 2**.

## 0. Què hi ha i d'on surt

Partim dels **1.295 events de contractació** ja materialitzats a
`data/events/events_bergueda.parquet` (connector `ybgg-dgi6`, PSCP; contracte de la
taula `events` intacte). La capa nova és **derivada i offline** (com el motor de
convergència): no descarrega res, llegeix el parquet d'events + el mart de Sondeig
(per a la població) i **escriu sortides noves sense tocar el contracte original**.

| sortida | fitxer | gra |
|---|---|---|
| Events enriquits | `data/events/licitacions_enriquit_bergueda.parquet` | 1 fila = 1 contracte (1.295) |
| Repartiment supra | `data/events/licitacions_repartiment_bergueda.parquet` | 1 fila = (event comarcal × municipi) (16.325) |
| Indicador dependència | `data/events/licitacions_dependencia_bergueda.parquet` | 1 fila = 1 municipi (31) |

Codi: `packages/signals/datapoble_signals/licitacions_taxonomy.py` (taxonomia pura)
+ `licitacions.py` (pipeline). CLI: `python -m datapoble_signals licitacions`.

## 1. Taxonomia territorial pròpia (no només CPV)

El CPV (Common Procurement Vocabulary) diu *què es compra*, però no *què revela*
d'un territori. Hi afegim **tres lectures pròpies**, cadascuna amb `confianca` i el
`metode` que la justifica. Tot és **heurística** (CPV fort + paraules clau febles).

### 1.1 `tema_administratiu` — l'àrea de govern (15 temes)

`residus · aigua · turisme · cultura · mobilitat · habitatge · urbanisme ·
manteniment · energia · social · educacio · salut · seguretat · digitalitzacio ·
administracio · altres`. Més fi i més **territorial** que les 6 famílies del
`tipus_senyal` del contracte.

**Regla** (a `tema_administratiu()`), per ordre de força:
1. **CPV específic** (prefix ≥ 3 dígits) → tema, confiança **0,9**, mètode `cpv`.
2. **CPV de 2 dígits (família)** + paraula clau d'**override** d'un altre tema →
   tema de la paraula, conf **0,7**, mètode `cpv+kw`. Resol els CPV **intrínsecament
   ambigus** del sector públic local: CPV `60` (transport) amb «escolar» → `educacio`
   (no `mobilitat`); CPV `45` (obra) amb «abastament d'aigua» → `aigua` (no
   `urbanisme`); CPV `79` (serveis empresarials) amb «promoció turística» → `turisme`.
3. **CPV de 2 dígits** sense override → tema de la família, conf **0,8**, mètode `cpv`.
4. **Paraula clau** sobre l'objecte (sense CPV temàtic) → conf **0,55**, mètode `keyword`.
5. **Res** → `altres`, conf **0,3**, mètode `cap`.

Famílies CPV → tema (les principals; vegeu `_CPV_TEMA`): `90`→residus · `65/41`→aigua
· `92`→cultura · `80`→educacio · `85`→salut · `66/71/79/75/98`→administracio ·
`72/48/64/30/32`→digitalitzacio · `60/63/34`→mobilitat · `50/39/31`→manteniment ·
`45/44`→urbanisme · `55/15`→educacio/social (càtering i menjadors escolars). Els
prefixos específics (`9252`→cultura-museus, `7995`→turisme-events, `45233`→mobilitat-vials,
`45232`→aigua-canonades, `7525`→seguretat-socorrisme…) tenen prioritat sobre la família.

### 1.2 `caracter_senyal` — metabolisme normal vs tensió/aposta

`ordinari · reforç · emergencia · transformacio · promocio · diagnostic`. Separa el
que un municipi gasta **cada any per existir** del que **delata un problema o una
aposta**. Es deriva del **verb de l'objecte**, no del CPV (a `caracter_senyal()`,
prioritat: emergencia > diagnostic > promocio > transformacio > reforç; per defecte
`ordinari`, conf 0,45; si un verb casa, conf 0,6).

- `emergencia` — «urgència», «dany del temporal», «filtracions», «avaria»: qui
  **apaga incendis** (no preveu).
- `diagnostic` — «estudi», «redacció del projecte», «pla operatiu», «auditoria»:
  entendre abans d'actuar.
- `promocio` — «campanya», «màrqueting», «projecció exterior»: aposta de visibilitat.
- `transformacio` — «construcció», «creació d'un», «adquisició d'un»: inversió nova.
- `reforç` — «servei extraordinari», «ampliació del servei»: més del mateix.
- `ordinari` — la resta: el metabolisme recurrent.

### 1.3 `contract_signal_type` — força com a senyal TERRITORIAL

`evidencia_directa · proxy_fort · proxy_feble · nomes_context`. No tots els
contractes parlen del territori: comprar material d'oficina és context administratiu
pur; contractar **socorrisme** fluvial és **evidència directa** d'ús recreatiu de
l'aigua. (A `contract_signal_type()`):
- `administracio` o `altres` → `nomes_context` (no diu res del territori).
- tema territorial + paraula d'evidència física (socorrisme, visitants, recollida,
  abastament…) → `evidencia_directa`.
- tema territorial amb CPV temàtic (`cpv`/`cpv+kw`) → `proxy_fort`.
- tema territorial només per paraula (`keyword`) → `proxy_feble`.

## 2. Cobertura de la classificació (honestedat sobre el `altres`)

Sobre els **1.295 events**:

| dimensió | resultat |
|---|---|
| **classificats** (tema ≠ `altres`) | **95,4 %** (1.235) |
| **`altres`** (cap senyal; a propòsit) | **4,6 %** (60) |
| per CPV (conf alta) | 74,9 % `cpv` + 12,0 % `cpv+kw` |
| per paraula clau (conf feble) | 8,4 % `keyword` |

L'`altres` cau de **~38 %** (el calaix del `tipus_senyal` del contracte, que només
té 6 famílies) a **4,6 %** perquè la taxonomia és més fina i combina CPV específic +
família + override + paraula. **Però segueix sent heurística**: 1 de cada 5 events
es classifica només per paraula clau (sorollós), i no validem encara cap etiqueta a
mà. La precisió per categoria és **PAS 2** (validació de 300 contractes + LLM).

**Distribució per tema** (els grans reflecteixen qui és la font: el Consell
Comarcal porta 695 dels 1.295, amb molt **transport i menjador escolar** →
`mobilitat`/`educacio`, i molta **cultura/promoció** de comarca):

| tema | n | % |    | tema | n | % |
|---|--:|--:|---|---|--:|--:|
| mobilitat | 195 | 15,1 % | | social | 62 | 4,8 % |
| administracio | 194 | 15,0 % | | altres | 60 | 4,6 % |
| educacio | 193 | 14,9 % | | residus | 43 | 3,3 % |
| cultura | 155 | 12,0 % | | aigua | 37 | 2,9 % |
| urbanisme | 94 | 7,3 % | | turisme | 32 | 2,5 % |
| digitalitzacio | 87 | 6,7 % | | salut | 31 | 2,4 % |
| manteniment | 86 | 6,6 % | | seguretat | 18 | 1,4 % |
|  |  |  | | energia | 8 | 0,6 % |

**Caràcter:** ordinari 71,6 % · transformacio 14,9 % · diagnostic 5,1 % · promocio
4,3 % · emergencia 3,9 % · reforç 0,2 %. **Tipus de senyal:** proxy_fort 58,1 % ·
proxy_feble 20,1 % · nomes_context 19,6 % · evidencia_directa 2,2 %.

## 3. Repartiment supramunicipal DECLARAT

**El problema:** 695 dels 1.295 events són del **Consell Comarcal del Berguedà**
(`ambit='comarcal'`, `ine5=NULL`). Avui són **inútils a `ine5=NULL`**: no es poden
creuar amb cap municipi. *Però un contracte comarcal és senyal per als
micromunicipis de la comarca* (la lliçó de Talaia: els pobles petits no contracten
els seus serveis; viuen del Consell).

**La solució (declarada, no «la veritat»):** repartim cada event comarcal als 31
municipis amb un `allocation_method` **explícit** + confiança. Cada mètode és una
**hipòtesi de repartiment**, no una mesura. Comencem **simple** (a propòsit):

| `allocation_method` | quan | repartiment | conf base |
|---|---|---|---|
| `directe_textual` | l'objecte **nomena un sol municipi** | 100 % a ell | 0,85 |
| `per_poblacio` | serveis a persones (social, educacio, salut, residus, seguretat, digitalitzacio, habitatge) | quota poblacional (mart) | 0,6 |
| `igualitari` | serveis territorials (turisme, cultura, mobilitat, urbanisme, aigua, energia) + `altres` | parts iguals (1/31) | 0,45 (0,3 per `altres`) |
| `no_assignable` | funcionament intern del Consell (`administracio`) | a ningú (ine5=NULL, share 0) | 0,7 |
| `per_carrega` · `per_indicador` | (reservats per al PAS 2: repartir per càrrega real o per un indicador del mart) | — | — |

La detecció textual de municipi (`_detect_municipi`) és **conservadora**: requereix
un nom prou llarg (≥ 5 caràcters, sense accents ni apòstrofs) i que **no n'aparegui
cap altre** (si en nomena dos, no és repartiment directe net → cau al mètode per
tema). El repartiment **conserva l'import**: la suma d'`import_assignat` d'un event
== el seu `import_total` (verificat: 19.419.168 € totals ≈ 19.419.169 € assignats,
diferència d'arrodoniment).

**Resultat** (695 events comarcals → 16.325 files de repartiment):

| mètode | events | € repartits |
|---|--:|--:|
| `per_poblacio` | 261 | 7.714.092 € |
| `igualitari` | 260 | 7.118.152 € |
| `directe_textual` | 111 | 4.586.924 € |
| `no_assignable` | 63 | 513.608 € (es queda al Consell) |

Els 111 `directe_textual` nomenen sobretot Berga (46), Gironella (12), Puig-reig
(11), Guardiola (10) — obres i projectes amb el municipi a l'objecte (col·lector de
Puig-reig, pista d'atletisme de Gironella…). Detecció verificada a mà sobre mostra.

## 4. Indicador inicial: `dependencia_supramunicipal`

Per municipi:

```
dependencia_supramunicipal = import_serveis_comarcals_assignables / import_municipal_directe
```

- **numerador** — € comarcals assignats al municipi (exclou `no_assignable` per
  construcció: tenen `ine5=NULL`).
- **denominador** — € que el municipi contracta **ell mateix** (`ambit='municipal'`).

**El resultat al Berguedà és contundent:** **només 2 dels 31 municipis** contracten
res propi en aquest dataset.

| municipi | hab | propi (€) | comarcal assignable (€) | ràtio | lectura |
|---|--:|--:|--:|--:|---|
| **Berga** | 17.539 | 21.280.508 | 4.166.575 | **0,20** | `autonom` |
| **Castellar de n'Hug** | 166 | 1.198.604 | 260.457 | **0,22** | `autonom` |

Els **altres 29 municipis** (inclosos **Gironella 5.082 hab** i **Puig-reig 4.558
hab**!) tenen **0 contractes propis** en aquest feed → ràtio indefinida, lectura
**`no_contracta_propi`**. Els que més reben de dalt: Gironella (3,08 M€), Puig-reig
(1,15 M€), Cercs (1,05 M€), Guardiola (1,0 M€), Casserres (0,72 M€).

**Frontera honesta (innegociable):**
- **No contractar ≠ no necessitar.** Per als 29 municipis sense contractació pròpia,
  la ràtio és NULL **a propòsit** (no és 0, no és ∞): el numerador (el que els
  arriba de dalt) **ÉS, precisament, el rastre de la seva dependència institucional**.
  La lectura `no_contracta_propi` ho diu sense inventar una ràtio.
- **El denominador té un biaix de font.** Que Gironella o Puig-reig surtin amb 0
  contractes propis probablement vol dir que **publiquen la seva contractació en un
  altre lloc** (o per sota del llindar d'aquest feed agregat `ybgg-dgi6`), no que no
  contractin gens. La ràtio s'ha de llegir **dins d'aquest dataset**, no com a
  finançament real total. El PAS 2 (creuar amb pressupostos municipals / altres
  feeds) ho corregirà.
- **El numerador és inferència declarada** (depèn del repartiment del §3): cada
  euro assignat porta el seu `allocation_method` i confiança. La `confianca` de
  l'indicador és composta i modesta (0,5 si hi ha denominador; 0,35 si no).

Aquest indicador fa **mesurable** la lliçó del micromunicipi: la capacitat
institucional del Berguedà està **fortament centralitzada al Consell**, i els pobles
—fins i tot els mitjans— en depenen.

## 5. Què queda per al PAS 2

- **LLM sobre `altres`** (60 events) + refinament dels `keyword` (sorollosos) →
  pujar la precisió i reduir el residual amb traçabilitat (cita o rebutja).
- **Validació manual de 300 contractes** → precisió per categoria (la taxonomia és
  heurística; encara no té mètrica de qualitat).
- **Repartiment fi** (`per_carrega`, `per_indicador`): substituir l'`igualitari` i
  el `per_poblacio` plans per repartiments per càrrega real o per indicadors del
  mart (km de via, places turístiques, alumnes…), on existeixin.
- **Els altres 4 indicadors** (creuen amb `mart_municipi`): `gap_pressio_resposta`,
  `intensitat_contractacio_turisme_per_carrega`, `intensitat_contractacio_aigua_per_estres`,
  `contractacio_digital_operativa`.
- **Lectura temporal** (qui **preveu** vs qui **apaga incendis**): seqüència
  pre/post event amb el `caracter_senyal` ja derivat.
- **Corregir el biaix del denominador** de la dependència creuant amb una font de
  contractació/pressupost municipal més completa.

## Frontera (resum)

La classificació és **heurística** (cobertura parcial; `altres` 4,6 % a propòsit; 1
de 5 events només per paraula). Els repartiments són **inferència declarada** (cada
fila amb mètode + confiança; cap és «la veritat»). L'indicador barreja un denominador
amb biaix de font i un numerador inferit → es llegeix com a **senyal de centralització
institucional dins d'aquest dataset**, no com a finançament real. Tot derivat i
read-only: no toca el contracte de la taula `events`.
