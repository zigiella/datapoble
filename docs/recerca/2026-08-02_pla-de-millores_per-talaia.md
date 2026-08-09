# Pla de millores de riusdegent · ordre de treball per a Talaia

*Preparat per Sitja (bifurcació de recerca), 2026-08-02. Surt del landscape de cinc plataformes, de
l'auditoria de quatre municipis i de la verificació de l'ETCA amb Bea.*

**Com llegir això.** Cada fitxa porta **on** es toca, **com es verifica** i **la trampa** que hi vaig
trobar. El que està verificat ho diu; el que és hipòtesi també. **Res d'això s'ha implementat.**

**Regla que demano que es respecti:** cap fitxa del bloc **C** (fonts noves) abans d'**A6** (les
lectures P1/P2). Motiu al final.

---

## 0 · El criteri de l'ETCA, tancat

Bea el va encertar de primer intent i la font el confirma.

> Idescat publica l'ETCA per als municipis de **1.000 habitants o més**, i el llindar es compleix
> **si s'hi arriba en població resident O en població ETCA**. Així des de la **base 2021**; abans,
> només >5.000 habitants i capitals de comarca.
> Àmbits publicats: **Catalunya → comarques i Aran → municipis ≥1.000**.

Font: [Idescat · Estimacions de població estacional](https://www.idescat.cat/pub/?id=epe) ·
[Anuari estadístic, sèrie ETCA](https://www.idescat.cat/indicadors/?id=aec&n=15961)

**És un O, no un I.** Verificat sobre els 947:

| | |
|---|---|
| Municipis amb ETCA | **486** |
| …amb padró **<1.000** | **16** |
| Municipis de padró ≥1.000 **sense** ETCA | **1** (l'Aleixar, 1.026 — vintage del padró) |

**El cas que ho demostra, i és del Berguedà:**

| | padró (base Idescat) | estacional | població ETCA | publicat |
|---|---|---|---|---|
| **Guardiola de Berguedà** | 951 | **+54** | **1.005** | ✅ per la branca ETCA |
| **Olvan** | 926 | negatiu | <1.000 | ❌ per cap de les dues |

**Guardiola és un dels 9 municipis coberts del Berguedà** — o sigui que el missatge
`ca.js:2098` («Idescat només publica ETCA per a pobles de ≥1.000 habitants: 9 dels 31») **es
contradiu ell mateix**: el primer dels 9 que llista té 962 habitants.

### ⚠️ Rebaixa de gravetat que vaig comprovar després

Ho vaig marcar 🔴 pensant que podia ser un bug. **No ho és.** No hi ha cap llindar de 1.000 cablat
al codi de producció: el front fa `data.etca ?? null` —presència de dada, no de població— i cap
model ni exportador filtra per `poblacio >= 1000`. **El producte no calcula res malament: ho explica
malament.** Segueix sent un error publicat i doctrinal, però no toca cap xifra.

### El que sí vaig dir malament

«ETCA 1.016» i «mínim 901», del primer informe, sortien de sumar **el nostre** padró al delta
estacional. La base bona és la d'Idescat (Guardiola: **951**, no 962). Amb la base correcta el
criteri encaixa net; amb la nostra, semblava que no n'hi hagués cap. **Corregit al document
d'auditoria.**

---

## A · Correccions · coses que avui diuen alguna cosa falsa o imprecisa

### A1 · El criteri de l'ETCA ✅ CORREGIT

**On, exactament** (línies idèntiques als dos idiomes, verificat):

| Fitxer | Línies |
|---|---|
| `packages/web/src/lib/paraglide/messages/ca.js` | **2458** (la targeta) · 686 · 2050 · 2058 · 2098 · 2202 |
| `packages/web/src/lib/paraglide/messages/es.js` | **les mateixes sis, en mirall** |
| `packages/web/src/routes/municipi/[slug]/+page.svelte` | 13 · 68 *(comentaris)* |
| `docs/contracte-abast.md` | 22 · 45 · 46 · 65 |
| `docs/analisi-escala-nivellc.md` | 22 · 149 · 183 |
| `docs/article-riusdegent.md` | 96 |
| `bitacora/2026-06-10_etca-epe-validacio-externa_talaia.md` | 14 |

**Redacció proposada** (curta, per a la targeta 2458):

> **ca** — «Idescat la publica per als municipis de 1.000 habitants o més, comptant el padró **o bé**
> la població ETCA. Aquí no s'arriba per cap de les dues.»
> **es** — «Idescat la publica para los municipios de 1.000 habitantes o más, contando el padrón **o
> bien** la población ETCA. Aquí no se llega por ninguna de las dos.»

**No és cosmètic:** `docs/contracte-abast.md` fa servir el llindar com a **costura de model**
(«≥1.000 → ETCA oficial · <1.000 → estimació nostra»). La costura real és **«té ETCA / no en té»**,
que no és el mateix conjunt. Això és doctrina i el vot final és de Bea.

**Verificació:** `verify-docs.mjs` verd · cap ocurrència de `≥1.000 hab` lligada a l'ETCA en
`grep -rn` sobre `packages/web/src` i `docs/`.

**Cost:** mig dia · **Qui:** Talaia (doctrina) + Mirador (còpia).

> #### Correcció (Talaia, 2026-08-09) · el diagnòstic era bo, i es quedava curt per tres bandes
>
> **1 · Les rutes no servien.** La taula «On, exactament» apunta a
> `packages/web/src/lib/paraglide/messages/*.js`, que és **sortida del compilador i està al
> `.gitignore`**. La font són `packages/web/messages/ca.json` i `es.json`. Sis claus, no sis línies:
> `gov_pres_etca_absent` (la targeta), `met_validacio_nota`, `met_valid_canon`,
> `met_valid_canon_curt`, `met_val_nucli_fet`, `met_rang_2`.
>
> **2 · Faltaven dos fitxers** que el `grep` de l'auditoria no va agafar:
> `docs/metodologia-presencia-catalunya.md` i `docs/pla-llancament-2026-06.md`.
>
> **3 · El criteri té una peça més.** [Idescat, metodologia de les
> EPE](https://www.idescat.cat/pub/?id=epe&m=m): *«els municipis de 1.000 habitants o més (ja sigui
> població resident o població ETCA)»* — l'**o bé** que deies — **i a més**: *«Si un any la població
> d'un municipi supera els 1.000 habitants, en els anys posteriors es difonen dades encara que no
> superi aquesta xifra.»* És a dir, hi ha **arrossegament**: un cop dins, s'hi queda.
>
> **La prova ja era a casa nostra, i és més forta que Guardiola.** Els nostres propis docs diuen
> «els **≥1.000 hab** (486) es validen contra l'ETCA». Però **només 471** municipis catalans arriben
> a 1.000 de padró. **486 − 471 = 15 municipis** amb ETCA que no arriben al llindar de padró. El
> nombre que fèiem servir per il·lustrar el criteri era el que el desmentia.
>
> I la conseqüència és tranquil·litzadora: **486 + 441 = 927**, o sigui que el codi **ja partia
> correctament per «té ETCA / no en té»**. L'error era només l'etiqueta. **No s'ha tocat cap càlcul
> ni cap xifra**: s'ha anomenat bé el conjunt.
>
> **El que NO he tocat, perquè és el teu vot i no el meu:** la costura del *model* a
> `docs/contracte-abast.md` (22, 45, 46) i `met_regim_cap` («a ≥1.000 hab deixem parlar Idescat. El
> límit, el marquem nosaltres»). Aquestes descriuen on cedim la paraula nosaltres, no on publica
> Idescat, i canviar-les és canviar doctrina. Tenies raó a marcar-ho com a decisió de la direcció.

---

### A2 · L'índex d'envelliment no quadra amb XIFRA ✅ RESOLT

| | Castellfollit de la Roca |
|---|---|
| datapoble | **259,6** |
| XIFRA (Diputació de Girona) | **244,76** |

**No és arrodoniment: és un 6%.** Hipòtesis per ordre: vintage del padró diferent · franges d'edat
diferents (65+/0-14 no és universal) · numerador o denominador d'una altra data.

**Per què importa ara:** és la **primera vegada que una xifra nostra no quadra amb una font externa**
—la població i l'estrangeria sí que quadren al decimal (§apèndix)— i **A3 i B3 en depenen**: si els
índexs derivats es construeixen sobre franges que ja discrepen, tots naixeran discrepants.

**Verificació:** recalcular a mà des de `mart_municipi` i comparar amb el mètode declarat per XIFRA.
Si no es pot resoldre, **es diu al glossari** i s'acaba: el «no ho sabem» és resposta vàlida.

**Cost:** 1 dia · **Qui:** Sondeig.

> #### Resolució (Talaia, 2026-08-09) · no és un error nostre: són franges diferents
>
> **Cap de les tres hipòtesis, i alhora la segona.** No és vintage: les nostres franges surten de
> l'API d'Idescat EMEX amb `any=2025` i coincideixen al dígit (0-14 = 99 · 65-84 = 211 · 85+ = 46 ·
> total 960). El que no coincideix és **on parteix la franja**.
>
> XIFRA té el **mateix numerador** que nosaltres (257) i un denominador de **105**. Es resol amb el
> segon índex que dona el §B3:
>
> | | nosaltres (0-14 / 15-64) | XIFRA (0-15 / 16-64) | XIFRA publica |
> |---|---|---|---|
> | envelliment | 257/99 = **259,60** | 257/105 = **244,7619** | **244,76** ✔ |
> | dependència | 356/604 = **58,94** | 362/598 = **60,5351** | **60,54** ✔ |
>
> Dos índexs independents, les mateixes franges inferides, i **105 + 598 + 257 = 960**, la població
> exacta. No és casualitat: XIFRA parteix la infància a 0-15 i l'edat activa a 16-64.
>
> **Qui té raó: nosaltres**, i no per criteri propi sinó perquè és la definició de la font.
> [Idescat, metodologia dels indicadors demogràfics](https://www.idescat.cat/pub/?id=inddt&m=m):
> *«Població de 65 anys i més per cada 100 habitants de menys de 15 anys.»* La nostra fórmula és
> aquesta, literal. **No es toca cap xifra.** El que faltava era el `caveat`, i s'ha escrit al
> contracte: qui compari amb XIFRA ha de saber per què surt un 6% de diferència.
>
> **B3 queda desbloquejat, i a mitges.** Amb les franges que tenim (0-14 / 15-64 / 65-84 / 85+) i les
> definicions literals d'Idescat en surten **dos dels quatre** índexs, sense font nova i sense cap
> divisió per zero a 947 municipis: **dependència global** `(0-14 + 65+)/15-64` i
> **sobreenvelliment** `85+/65+` (Castellfollit: 58,94 i 17,90). Els altres dos **no**, i cal dir-ho:
> el **recanvi d'actius** demana 60-64 i 15-19, i la **potencialitat** demana dones per edat —
> franges que avui no baixem. Publicar-ne dos i declarar per què falten els altres dos és la
> resposta honesta; inventar-los amb franges aproximades, no.
>
> **Un cas límit trobat pel camí:** **1 municipi de 947 té zero habitants de 0 a 14 anys.** L'índex
> d'envelliment hi és una divisió per zero — no un infinit ni un 0. Ha d'anar a `sense_dada` amb
> motiu, i qualsevol índex derivat que es construeixi ha de portar la mateixa guarda.

---

### A3 · `tipus_territorial` és grollera al tram alt

Els **quatre** municipis de l'auditoria surten `interior_rural`:

| | població |
|---|---|
| Castellfollit de la Roca | 960 |
| Guardiola de Berguedà | 962 |
| Berga | **17.539** |
| Olot | **39.516** |

Una tipologia que posa a la mateixa cel·la un poble de 960 i una ciutat de 39.516 **no informa de
res**, i s'usa per triar banda de model.

**Trampa a evitar:** no partir per franja de mida sense mesurar-ho. Ja vam mesurar que **la comarca
explica més variància que la franja a 8 de 9 mètriques**; el que falla aquí és la *tipologia*, no
l'elecció comarca-vs-mida.

**Cost:** 1 dia · **Qui:** Talaia (és contracte).

---

### A4 · «Habitatge no principal» barreja dues coses

Avui una sola xifra conté **habitatge buit** i **segona residència**. Un alcalde les distingeix i
són polítiques oposades. XIFRA les publica separades.

**Mínim honest si no es poden separar:** que l'etiqueta i el `caveat` diguin que hi caben totes dues.
**Millor:** separar-les si la font ho permet.

**Cost:** mig dia (etiqueta) · **Qui:** Talaia + Sondeig.

---

### A5–A7 · Ja obertes

| | Issue | Què |
|---|---|---|
| **A5** | [#303](https://github.com/zigiella/datapoble/issues/303) | Delta sobre finestra de zero anys (14 municipis). Una fletxa sense període és el que la doctrina prohibeix |
| **A6** | [#302](https://github.com/zigiella/datapoble/issues/302) | **E7b · regenerar les lectures P1/P2** sobre mètriques citables. **El deute més gran del producte** |
| **A7** | [#311](https://github.com/zigiella/datapoble/issues/311) | El hero de la fitxa porta `947` escrit a mà |

---

## B · Dada que JA tenim i no fem servir · cost d'ingesta zero

**El bloc més rendible de tota la llista.** Cap font nova, cap permís, cap conveni: és matèria
primera que ja baixem i llencem.

### B1 · Places turístiques, no només establiments

| | verificat |
|---|---|
| Places declarades a Catalunya al RTC | **790.212** |
| la Pobla de Lillet | **31 establiments = 657 places** sobre 1.106 habitants → **59% de la població resident** |
| Guardiola de Berguedà | el cas estrella de l'auditoria (45,7 establiments/1.000 hab) |

«31 establiments» no diu el que diu «657 places», i és el que un alcalde vol saber.

> ⚠️ **La trampa, i és seriosa.** Només **32.880 de 112.964** establiments d'alta (**29%**) declaren
> places. **Primer cal mesurar si la manca és sistemàtica per tipus** (sospita: els HUT no en
> declaren). Si ho és → publicar-ho **només per als tipus que la declaren**, dient-ho. Si no ho és →
> **no publicar**. Publicar una ràtio sense saber què falta seria el nostre error clàssic.

**Qui:** Sondeig · **Dependència:** la mesura de cobertura va abans que la targeta.

---

### B2 · Atur per sexe i per trams d'edat

El CSV del SEPE que **ja ingerim cada mes** porta el desglossament sencer. Capçalera literal:

> `PARO REGISTRADO POR MUNICIPIOS DESGLOSADO POR SEXO, TRAMOS DE EDAD Y SECTOR DE LA ACTIVIDAD`

Columnes que baixem i **descartem**: home <25 / 25-45 / ≥45 · dona <25 / 25-45 / ≥45 · **i cinc
sectors** (agricultura, indústria, construcció, serveis, sense ocupació anterior). **947 municipis,
mensual, des de 2006.**

> ⚠️ **La trampa:** el desglossament multiplica les cel·les petites i el **«<5» del SEPE s'hi
> dispara**. Als micromunicipis pot ser que **gairebé tot quedi emmascarat**. La doctrina de
> l'interval [1,4] hi val igual, però **cal mesurar quants municipis queden llegibles abans de
> prometre la targeta**.

**Qui:** Sondeig.

---

### B3 · Índexs demogràfics derivats · sense font nova

Dependència · recanvi · sobreenvelliment · potencialitat. **Surten de les franges d'edat que ja
tenim.** XIFRA els dona (Castellfollit: dependència 60,54 · recanvi 133,96).

> ~~⚠️ **Bloquejat per A2.** Si el nostre envelliment ja discrepa amb el seu, els derivats també ho
> faran, i multiplicarem la discrepància per quatre.~~
>
> ✅ **Desbloquejat (A2 resolt, 2026-08-09), i a mitges.** La discrepància era de franges, no de
> dada: la nostra fórmula és la literal d'Idescat. Amb les franges d'avui en surten **dos** dels
> quatre — **dependència global** i **sobreenvelliment** — i **dos no**: el **recanvi** demana 60-64
> i 15-19, i la **potencialitat** demana dones per edat. Es publiquen els dos que es poden sostenir
> i es declara per què falten els altres dos. Guarda obligatòria: **1 municipi té 0 habitants de
> 0-14** i qualsevol quocient que el prengui de denominador va a `sense_dada` amb motiu.

**Qui:** Sondeig · ~~**Dependència: A2.**~~ lliure.

---

### B4–B5

| | Què |
|---|---|
| **B4** | **Homes/dones i edat mitjana** — bàsiques, XIFRA les té i nosaltres no |
| **B5** | [#308](https://github.com/zigiella/datapoble/issues/308) **Sèrie de població via censph** — desbloqueja l'evolució de població i de franges, que avui no tenim |

---

## C · Fonts noves · per ordre de valor

> **Cap d'aquestes abans d'A6.** Vegeu el tancament.

| | Què | Per què | Font |
|---|---|---|---|
| **C1** 🟠 | **Pressupost municipal**: ingressos, despeses, **deute viu, deute per habitant** | **El forat més gran que ha destapat l'auditoria.** XIFRA dona «deute per habitant: 274 €» a Castellfollit i «17.091.030 € de deute viu» a Olot. Per a un alcalde això és tan central com l'atur i **no en tenim ni una xifra** | **Ministeri d'Hisenda**, oberta. És la que fa servir XIFRA |
| **C2** | **Superfície** (tenim densitat, no superfície) i **altitud** | barates i les demana tothom | INE · ICGC |
| **C3** | **Naixements i defuncions** | habiliten els índexs vitals | Idescat |
| **C4** | **Cens administratiu d'activitat econòmica** | comerç i restauració vénen d'**OSM**, i el nostre caveat ja diu que la completesa creix amb el temps. Castellfollit: **5 serveis, 2 restaurants**. Un cens diria si això és el poble o és el mapa | SITMUN (només Girona) o IAE |
| **C5** | **Autocontenció i autosuficiència laboral** | *la* pregunta d'un poble dormitori, i no la responem | Idescat |
| **C6** | **CO₂ per càpita** desglossat · **motorització** · **coneixement del català** | catàleg de XIFRA que val la pena | diverses |

---

## D · Producte i estructura · totes obertes

| | Issue | Què |
|---|---|---|
| **D1** | [#312](https://github.com/zigiella/datapoble/issues/312) | Partir la pàgina de comarca com s'han partit el govern i el tauler |
| **D2** | [#310](https://github.com/zigiella/datapoble/issues/310) | `/comarca/[slug]` no enllaça els seus 9 llistats |
| **D3** | [#307](https://github.com/zigiella/datapoble/issues/307) | Retirar els monòlits del Berguedà |
| **D4** | [#306](https://github.com/zigiella/datapoble/issues/306) | `n_comarca` a la cel·la de `mart_govern` (recompte duplicat al web) |

**D5 · El que NO s'ha de perdre en ampliar.** El nostre avantatge real sobre XIFRA **no és el nombre
d'indicadors**: és el **rang comarcal a cada xifra**, la **doble referència amb el seu denominador**
i la **procedència per targeta**. L'informe de XIFRA **no compara amb res** —ni comarca, ni
província, ni Catalunya— i declara les fonts **una sola vegada al peu**. Cada indicador nou ha de
néixer amb rang i procedència o no néixer.

---

## E · Guardes i pipeline · totes obertes

| | Issue | Què | Per què |
|---|---|---|---|
| **E1** | [#304](https://github.com/zigiella/datapoble/issues/304) | Meta-guarda: el CI ha de caure si un verificador versionat no l'invoca cap workflow | *«una guarda que no s'executa decora, no protegeix»* — el patró ens ha mossegat cinc vegades |
| **E2** | [#305](https://github.com/zigiella/datapoble/issues/305) | `export_indicadors_cat.py` emet artefacte versionat sense `--check` | mateixa família |
| **E3** | [#309](https://github.com/zigiella/datapoble/issues/309) | Un refresc anual del pipeline sencer, no una cron per font | |

---

## F · Decisions de Bea · no s'ha obert cap contacte

| | Què |
|---|---|
| **F1** | **Espai de Dades del Món Local** (AOC + Generalitat + les 4 diputacions, en pilotatge). **L'única de les cinc sense biaix gironí**: cobriria Berga i Guardiola igual que Olot. Si federa el que les diputacions ja tenen, **C1 arribaria per aquí per als 947**. Doble lectura: font que ens estalvia deu connectors, **o** competidor amb quatre diputacions al darrere |
| **F2** | [#313](https://github.com/zigiella/datapoble/issues/313) `mart_electoral` versionat és estale (31 files, el model n'emet 947) — decisió editorial |
| **F3** | [#314](https://github.com/zigiella/datapoble/issues/314) PR #287 R-RUBRICA, el radar com a rúbrica única configurable |
| **F4** | **SITMUN: recomano NO demanar accés ara.** És per a ens públics, som privats, i **no cobreix el Berguedà**. Gastaríem la petició per a mitja mostra |

---

## Apèndix · xifres verificades, perquè no s'hagin de tornar a derivar

**Validació externa contra XIFRA — quadrem al decimal:**

| | XIFRA | datapoble |
|---|---|---|
| Olot · població | 39.516 | **39.516** |
| Olot · estrangers | 10.979 · 27,78% | **10.979 · 27,78%** |
| Castellfollit · estrangers | 107 · 11,15% | **107 · 11,15%** |

És el **primer contrast independent** que té el projecte. L'única discrepància trobada és A2.

**Els 9 municipis del Berguedà amb ETCA** (padró → ETCA): Guardiola de Berguedà 962→**1.005** · la
Pobla de Lillet 1.106→1.121 · Cercs 1.236→1.130 · Casserres 1.665→1.571 · Bagà 2.167→2.305 · Avià
2.263→1.990 · Puig-reig 4.558→4.313 · Gironella 5.082→4.760 · Berga 17.539→17.057.

**Els quatre municipis de l'auditoria, de costat:**

| | Castellfollit 960 | Guardiola 962 | Berga 17.539 | Olot 39.516 |
|---|---|---|---|---|
| % habitatge no principal | 25,6 | **41,2** | 24,2 | 18,4 |
| Establiments turístics /1.000 | 14,6 | **45,7** | 2,6 | 3,4 |
| Vidre kg/hab | 25,5 | **53,0** | 27,6 | 17,8 |
| kWh domèstic/hab | 1.126 | **1.448** | 1.222 | 1.076 |
| kWh serveis/hab | 1.392 | **1.988** | 1.235 | 1.362 |
| Renda neta/persona | 15.597 | 15.580 | 15.449 | 15.213 |

Dues lectures que en surten: **Guardiola lidera les quatre mètriques de pressió alhora i
Castellfollit —població quasi idèntica— no**, o sigui que la mida no ho explica i el turisme sí. I
**la renda és plana als quatre** (2,5% de forquilla) mentre la resta varia el doble o el triple:
un indicador que no distingeix un poble de 960 d'una ciutat de 39.516 mereix una mirada.

**Un apunt que no és tasca.** Idescat **no publica ni un zero exacte** en 486 municipis (312 són
negatius) i **no publica Castellfollit**; XIFRA hi imprimeix **«població estacional: 0»**. Tot apunta
a un buit convertit en zero —el pecat capital de la nostra doctrina, imprès en un informe oficial.
**No ho he pogut confirmar amb ells i no ho afirmo.**

---

## Per què C va després d'A6

XIFRA té **més catàleg que nosaltres** i publica sobre 960 habitants coses que nosaltres no gosaríem
—un índex sintètic de fecunditat de **1,17 calculat sobre sis naixements**, a dos decimals, sense cap
advertiment. La nostra tria és l'altra: menys catàleg, més aparell d'honestedat.

**Aquesta tria només val si l'aparell es cobreix de contingut.** Avui tenim 63 mètriques i les
lectures P1/P2 **ocultes** perquè el 70% de les frases no compleix la nostra pròpia regla
d'evidència. Ampliar fonts abans d'arreglar-ho seria fer exactament el contrari del que el projecte
predica — i seria el primer que ens retrauria qualsevol que ens comparés amb ells.
