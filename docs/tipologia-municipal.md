# Mètode — Tipologia d'habitança, confiança auditable i IETR dual (Fase 1)

*Fase 1 del re-plan: **endurir el model SENSE fonts noves**. Tres derivats nous a `mart_municipi`, calculats sobre senyals que JA hi són. Pilot: Berguedà (31 municipis). **Tot el que diu aquí és inferència, no cens** — i la `tipologia` és, a més, una **LECTURA** (la millor narració que encaixa amb els senyals), no una etiqueta oficial. Documenta el que materialitza `packages/transform/models/marts/mart_municipi.sql` (CTEs `sstats`/`zsig`/`zsig2`/`tipo`/`conf`).*

**Estat:** dissenyat, materialitzat i verificat sobre dades reals · 2026-06-08. **Revisió** (mateix dia): `capital_serveis` redefinit de «mida» a **«centre de serveis real»** (senyal de serveis OSM `z_serveis` + sòl de població de 2.000 hab); vegeu §2.

---

## 0. Per què, i la frontera honesta
El model de 3 capes (vegeu `poblacio-real-metode.md`) ja dóna números: població pernocta, càrrega total, pressió turística. La consultora demana **endurir-lo**: que el model **es llegeixi** (no només números) i que **digui quan no se'n pot refiar** — sense afegir cap font nova. Tres derivats:

1. **`tipologia`** — la joia narrativa: classifica cada municipi amb un **NOM** (no «més/menys»).
2. **`confianca_score`** (0-100) — fiabilitat **auditable** que complementa la bandera `confianca`.
3. **IETR dual** (`IETR_stock` + `IETR_impact`) — desglossa l'IETR en els seus dos costats.

Tot surt de columnes que ja són al mart. La **frontera**: cap dada nova, cap número sense procedència, i on no es pot classificar amb confiança → `indeterminat`.

---

## 1. La base estadística: z-scores comarcals
Els tres derivats es recolzen en **z-scores comarcals** dels senyals: `z(x) = (x − mitjana) / desviació` sobre els 31 municipis del Berguedà (desviació poblacional, `stddev_pop`). `z = 0` és el municipi mitjà de la comarca; `z = +1` és una desviació per sobre.

Tres senyals (població, càrrega total i **establiments de serveis**) usen **`ln()` abans del z** perquè la seva distribució és molt asimètrica (Berga 17.539 hab i 53 establiments vs Sant Jaume 25 hab i 1). Un senyal compost, **`z_act`** = mitjana de `z(residus)`, `z(vidre)` i `z(restauració)`, resumeix l'**activitat de dia** (l'empremta de l'excursionista); **`z_serveis`** = `z(ln d'establiments de comerç i serveis essencials, OSM)` resumeix la **centralitat funcional** (l'empremta de la capçalera).

> **Per què comarcal i no absolut.** «Alt» o «baix» només té sentit *contra els veïns*. A escala Catalunya els z-scores seran **per comarca** (com les bases del model de 3 capes), no un sol pool estatal — un micromunicipi del Berguedà no es compara amb Barcelona.

---

## 2. `tipologia` — classificador basat en regles
Sis arquetips. El classificador avalua les regles **en ordre** i assigna la **primera** que encaixa; si cap encaixa amb prou claredat → `indeterminat`.

| Tipus | Narració | Regla (z-scores comarcals) |
|---|---|---|
| **`capital_serveis`** | **Centre de serveis real**: té el comerç i els serveis essencials que serveixen també els pobles veïns. Capçalera, no només vila gran. | `població ≥ 2000` **i** `z_serveis ≥ 0.8` **i** `z_carrega ≥ 0.5` **i** `z_turisme ≤ 0.3` |
| **`buit_administratiu`** | Micromunicipi tranquil a tots els eixos: padró estable, sense pressió. | `z_pop ≤ −0.5` **i** `z_turisme ≤ −0.3` **i** `z_act ≤ −0.2` **i** `z_gap ≤ 0.2` |
| **`excursio`** | Turisme i activitat de **dia** altes, però pernocten poc: vénen, gasten, marxen. | `z_turisme ≥ 0.6` **i** `z_act ≥ 0.4` **i** `z_gap ≤ 0.4` |
| **`segona_residencia`** | Gap de pernocta alt + llits buits que s'omplen (habitatge no principal **o** turisme alts). | `z_gap ≥ 0.5` **i** (`z_noprincipal ≥ 0.5` **o** `z_turisme ≥ 0.7`) |
| **`dormitori_invisible`** | Hi dormen sense constar, amb **poca** hostaleria. | `z_gap ≥ 0.4` **i** `z_turisme ≤ 0` |
| **`indeterminat`** | Senyals ambigus o contradictoris. **No es força una etiqueta.** | cap de les anteriors |

On:
`z_pop` = log-població · `z_carrega` = log-càrrega total · `z_turisme` = `index_turisme` · `z_gap` = `gap_pernocta_pct` · `z_noprincipal` = `pct_noprincipal` · `z_act` = activitat de dia (residus/vidre/restauració) · `z_serveis` = log-establiments de comerç i serveis essencials (OSM).

### La revisió de `capital_serveis`: de «mida» a «serveis»
La primera versió definia `capital_serveis` per **mida** (`z_pop` alt + `z_carrega` alt). Problema real detectat al pilot: hi sortien municipis **grans però sense capçalera de serveis** (Casserres, 1.665 hab, hi entrava només per volum). Una capital de serveis no és «un poble gran»: és el poble on els veïns **van a comprar i a fer gestions**. Per això el senyal **definidor** és ara **`z_serveis`** — el compte d'establiments de comerç quotidià i serveis essencials mapejats a OSM, en **absolut** (la capçalera es nota en el *nombre* de serveis, no en la densitat per habitant) — amb un **sòl de població de 2.000 hab** (una capçalera necessita massa crítica) i turisme no dominant.

Efecte al Berguedà: **Casserres** surt (té pocs serveis per a la seva mida) i **la Pobla de Lillet** (1.106 hab, molt dotada però petita i aïllada) queda **fora pel sòl** — un cas a revisar quan s'escali. El sòl `2000` és **provisional**: es comprovarà per comarca a mesura que s'afegeixin territoris.

> **Calibració per comarca (pendent a escala Catalunya).** El senyal de serveis OSM és un **mínim observat, no un cens**: OSM infra-mapeja el rural i la completesa varia entre municipis. A més, la signatura de «capçalera» és molt diferent segons el tipus territorial (Vallès ≠ Pirineu ≠ costa). Per això, igual que la resta de z-scores, `z_serveis` i el sòl de població s'han de **calibrar per comarca**, no amb un sol pool estatal.

### La distinció clau: `excursio` vs `segona_residencia`
Tots dos tenen turisme alt i molt habitatge no principal. Els separa **el gap de pernocta**:
- **`excursio`** → gap de pernocta **baix** (Castellar de n'Hug: `gap_pernocta_pct` 31 %, però residus i vidre pels núvols). L'excursionista ve **de dia**: deixa residus i ampolles, però no dorm ni encén l'electricitat de casa.
- **`segona_residencia`** → gap de pernocta **alt** (Gósol 87 %, Saldes 86 %). Els llits buits **s'omplen** els caps de setmana i ponts: la gent **hi dorm**.

> **Etiquetes públiques.** Al web, `segona_residencia` es mostra com **«Turisme de pernocta (2a residència i cap de setmana)»** i `excursio` com **«Turisme d'excursió (de dia)»**: tots dos són **turisme**; el que els separa és si **s'hi dorm**. Les claus tècniques no canvien.

### Resultat verificat (31 municipis del Berguedà)

| Tipus | N | Municipis (població) |
|---|---|---|
| **capital_serveis** | 5 | Berga (17.539), Gironella (5.082), Puig-reig (4.558), Avià (2.263), Bagà (2.167) |
| **segona_residencia** | 5 | Saldes (301), Gósol (207), Sagàs (153), Gisclareny (28), Sant Jaume de Frontanyà (25) |
| **excursio** | 2 | Castellar de n'Hug (166), la Nou de Berguedà (163) |
| **buit_administratiu** | 2 | Montclar (133), Fígols (41) |
| **dormitori_invisible** | 1 | Sant Julià de Cerdanyola (234) |
| **indeterminat** | 16 | Casserres (1.665), Cercs, la Pobla de Lillet, Guardiola, Olvan, Montmajor, Borredà, Vilada, Vallcebre, l'Espunyola, Sta Maria de Merlès, Viver i Serrateix, Castellar del Riu, Capolat, Castell de l'Areny, la Quar |

**Ancoratges coneguts (els 3 que demanava el brief):** ✅ **Berga = capital_serveis** · ✅ **Castellar de n'Hug = excursio** · ✅ **Gósol = segona_residencia** (i Saldes també).

> **16 `indeterminat` no és un fracàs: és honestedat.** Són municipis de mida i perfil intermedis (viles mitjanes amb turisme moderat) o micromunicipis amb senyals que es contradiuen. Forçar-los a un calaix seria inventar una narració. La meitat de la comarca és, simplement, **territori mixt** — i el model ho diu.

---

## 3. `confianca_score` (0-100) — fiabilitat auditable
La bandera `confianca` (alta/mitjana/baixa) és binària i, en alguns casos, **massa segura**. El `confianca_score` la **complementa** (no la substitueix) amb una puntuació **auditable**: cada punt ve d'un component explícit.

```
confianca_score =   40 · mida_denominador      (com de gran és el padró)
                  + 35 · concordança_senyals    (els senyals de presència apunten igual?)
                  + 15 · cobertura               (quants senyals tenim, no nuls)
                  − 10 · outlier                 (algun senyal és sospitosament extrem?)
              acotat a [0, 100]
```

| Component | Pes | Com es calcula |
|---|---:|---|
| **Mida del denominador** | 40 | `ln`-escalat entre **75** (micro, soroll de denominador) i **410** (vila «plena», base residencial). Per sota de 75 → 0 punts; a 410 o més → 40. |
| **Concordança** | 35 | Dispersió dels z-scores dels **3 senyals de presència** (residus, elèctric domèstic, % habitatge no principal). `35 · max(0, 1 − amplitud_z / 3)`: si els tres coincideixen → 35; si es dispersen ≥ 3σ → 0. |
| **Cobertura** | 15 | Fracció de senyals presents (no nuls) dels 5 inputs (residus, elèctric, vidre, % no principal, padró). |
| **Outlier** | −10 | Si algun senyal de presència té `|z| > 2` (soroll de denominador o glitch): `−10 · min(1, (max|z| − 2))`. |

**Talls de l'etiqueta derivada** (per a qui vulgui un alta/mitjana/baixa a partir del score):
`< 45` → **baixa** · `45–65` → **mitjana** · `≥ 65` → **alta**.

### La concordança és el que el fa més honest
El component de concordança és la novetat: **marca els municipis on els senyals físics es contradiuen**, cosa que una bandera binària «alta» amagaria. El cas de manual és **Castellar de n'Hug**:

- Bandera `confianca` actual: **alta** (residus alts + un corroborador per sobre de la mediana).
- `confianca_score`: **32,8 → baixa**.

Per què? A Castellar els residus diuen «molta gent» (`z` ≈ +1,1) però l'elèctric domèstic diu «poca» (`z` ≈ −0,4): **calefacció de llenya** a muntanya trenca el senyal elèctric. Els senyals **divergeixen** → l'estimació mereix menys confiança. El score ho veu; el binari no. **Quan divergeixen, el score és el costat honest de la tensió** — i per això es publiquen **tots dos** (l'etiqueta no es retira).

> Aquesta divergència és **intencionada i documentada**: el `confianca_score` no és una còpia de `confianca`, sinó una segona mirada més fina. Coincideixen en els casos clars (viles grans amb senyals coherents → score alt; micromunicipis → score baix) i divergeixen exactament on aporta valor.

---

## 4. IETR dual — desglossar l'índex
L'IETR és `0.5 · A_resid + 0.5 · B_turis` (vegeu `poblacio-real-metode.md` §IETR): barreja **exposició estructural** i **pressió realitzada** en un sol número. La Fase 1 els exposa **per separat** (tots dos ja són 0-100 per construcció — mitjana de dos indicadors winsoritzats 0-100):

| Columna | Què és | Senyals | Lectura |
|---|---|---|---|
| **`IETR_stock`** | Component **estructural/resident** (= `A_resid`) | habitatge no principal + habitatges per habitant | Exposició **latent**: quant de territori està *preparat* per a la pressió, hi hagi activitat o no. |
| **`IETR_impact`** | Component de **pressió realitzada** (= `B_turis`) | RTC per 1000 hab + per 100 habitatges | Pressió **viva**: quanta activitat turística reglada s'està exercint *ara*. |

**Identitat (garantida i verificada):** `round(0.5 · IETR_stock + 0.5 · IETR_impact, 2) == IETR`.

El desglossament revela tensions que l'IETR amaga:
- **Castellar** (IETR 89): stock 100, impact 79 — alt pels dos costats.
- **Gósol** (IETR 72): stock **100**, impact **44** — molta segona residència (stock), menys oferta reglada activa.
- **Capolat** (IETR 61): stock **28**, impact **93** — poc habitatge buit, però molta oferta reglada: pressió sense estructura.

---

## 5. Materialització i reproductibilitat
- **Definició canònica:** `packages/transform/models/marts/mart_municipi.sql` (CTEs `sstats` → `zsig` → `zsig2` → `tipo` / `conf`, i les columnes `IETR_stock`, `IETR_impact`, `tipologia`, `confianca_score`).
- **Contracte:** `semantic/metrics.yml` declara les 4 columnes (labels ca/es, `definicio`, `formula`, `source: datapoble`, `categoria: derived`, `caveat`/`note`).
- **Web:** `tools/export_web_municipis.py` les emet al JSON dels 31 municipis (`--check` verd).
- **Regenerador offline:** com que `data/raw/` és `.gitignore`, `packages/transform/derive_fase1.py` aplica **la mateixa SQL** (mateix motor DuckDB) sobre el parquet ja materialitzat i **prova la identitat** IETR = 0,5·stock + 0,5·impact. Amb raw, `dbt build` dóna el mateix resultat.

## 6. Límits (honestedat)
- La `tipologia` és una **LECTURA ecològica** sobre l'agregat municipal, no un cens ni una classificació oficial; volàtil en micromunicipis → creuar **sempre** amb `confianca` / `confianca_score`.
- Els llindars són **comarcals** (calibrats sobre el Berguedà). A escala Catalunya s'han de recalibrar **per comarca**.
- Cap dada nova: si un senyal d'entrada té un biaix (p. ex. OSM infra-mapeja el rural, llenya trenca l'elèctric), el derivat l'hereta. El `confianca_score` està dissenyat precisament per **fer visible** aquest risc, no per ocultar-lo.
