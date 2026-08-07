# Totes les millores a fer · llista consolidada

*Sitja, 2026-08-02. Encàrrec de Bea després de l'auditoria. Consolida el landscape de cinc
plataformes, l'auditoria de quatre municipis, la troballa de l'ETCA i els 13 issues oberts.*

**No s'ha implementat res.** Cada línia porta cost i qui la faria. L'ordre és el meu criteri; el vot
és de Bea.

---

## L'ETCA: la hipòtesi de Bea és el criteri oficial

> *«és possible que si l'ETCA és >=1000 sí que tingui encara que la població sigui <1000?»* — **Sí.
> Exactament això.**

Criteri literal d'Idescat:

> resultats per a tots els municipis de **1.000 habitants o més (ja sigui població padronal o
> població ETCA)**

És un **O**, no un **I**. I quadra al dígit:

| | padró (Idescat) | + estacional | = població ETCA | publicat? |
|---|---|---|---|---|
| **Guardiola de Berguedà** | 951 | **+54** | **1.005** | ✅ per la branca ETCA |
| **Olvan** | 926 | *(negatiu)* | **<1.000** | ❌ cap de les dues branques |

Dos municipis del Berguedà de mida quasi idèntica, un dins i l'altre fora, **i el que ho decideix és
l'ETCA, no el padró**. Sobre els 947: **486 amb ETCA · 16 d'ells amb padró <1.000** (Colera, 489
habitants, n'és el cas extrem: +526 d'estacional) **i només 1 municipi de ≥1.000 sense ETCA**
(l'Aleixar, 1.026 — probablement per la vintage del padró).

**Ho vaig dir malament abans:** vaig llegir «ETCA 1.016» i «mínim 901» sumant el NOSTRE padró al
delta. El correcte és la base pròpia d'Idescat (Guardiola: 951, no 962). Amb la base bona, el
criteri encaixa; amb la nostra, no.

### El que cal corregir, i on

La frase **«Idescat només la publica per a municipis ≥1.000 hab»** no és el criteri. Apareix a:

| Fitxer | Línia |
|---|---|
| `packages/web/src/lib/paraglide/messages/ca.js` | **2458** (la targeta), 686, 2050, 2058, 2098, 2202 |
| `…/messages/es.js` | els mateixos, en mirall |
| `packages/web/src/routes/municipi/[slug]/+page.svelte` | 13, 68 (comentaris) |
| `docs/contracte-abast.md` | 22, 45, 46, 65 |
| `docs/analisi-escala-nivellc.md` | 22, 149, 183 |
| `docs/article-riusdegent.md` | 96 |
| `bitacora/2026-06-10_etca-epe-validacio-externa_talaia.md` | 14 |

**Redacció proposada:** *«Idescat la publica per als municipis de 1.000 habitants o més, comptant o
bé el padró o bé la població ETCA. Aquí no arriba a cap de les dues.»*

**No és cosmètic.** Avui li diem a un poble de 962 habitants que no té ETCA «perquè és petit», quan
**el seu veí de 951 sí que en té**. I la frase apuntala una decisió de disseny sencera: la costura
Idescat≥1.000 / estimació nostra <1.000 del contracte d'abast **no és el llindar real**, i això toca
`docs/contracte-abast.md`, que és doctrina.

---

## A · Correccions — coses que avui diuen alguna cosa falsa o imprecisa

| | Què | Cost | Qui |
|---|---|---|---|
| **A1** | 🔴 **El criteri de l'ETCA** (a dalt): 7 missatges × 2 idiomes + 4 docs + doctrina del contracte d'abast | mig dia | Talaia (doctrina) + Mirador (còpia) |
| **A2** | 🔴 **Índex d'envelliment: no quadrem amb XIFRA.** Castellfollit: nosaltres **259,6**, ells **244,76**. No és arrodoniment. Cal saber per què (franges? vintage del padró?) abans que ho posi ningú de costat | 1 dia | Sondeig |
| **A3** | **`tipus_territorial` és grollera al tram alt**: Olot (39.516) i Berga (17.539) surten `interior_rural` igual que Castellfollit (960) i Guardiola (962). Una tipologia que no distingeix 960 de 39.516 no informa res | 1 dia | Talaia |
| **A4** | **`% habitatge no principal` barreja buit i segona residència.** Són coses diferents i un alcalde les distingeix. Avui la nostra etiqueta no diu que hi caben totes dues | mig dia | Talaia + Sondeig |
| **A5** | **[#303] Delta sobre finestra de zero anys** (14 municipis) — una fletxa sense període és exactament el que la doctrina prohibeix | ja obert | Sondeig |
| **A6** | **[#302] E7b · regenerar les lectures P1/P2** sobre mètriques citables. **És el deute més gran del producte**: per això P1/P2 estan ocultes | ja obert | Brúixola |
| **A7** | **[#311] El hero de la fitxa porta '947' escrit a mà** — un número codificat és un número que envellirà mentint | ja obert | Mirador |

---

## B · Dada que JA tenim i no fem servir — cost d'ingesta zero

Això és el més rendible de tota la llista: **no cal cap font nova, ni cap permís, ni cap conveni.**

| | Què | Verificat | Trampa que cal mesurar abans |
|---|---|---|---|
| **B1** | **Places turístiques** en comptes de només establiments. El RTC porta `total_places` | **790.212 places** a Catalunya · la Pobla de Lillet **31 establiments = 657 places sobre 1.106 habitants (59%)**. Guardiola en seria el cas estrella de l'auditoria | ⚠️ **només 32.880 de 112.964 establiments (29%) declaren places.** Si la manca no és sistemàtica per tipus, **no es publica** |
| **B2** | **Atur per sexe i per trams d'edat.** El CSV del SEPE que baixem cada mes ja porta home/dona × <25 / 25-45 / ≥45 **i cinc sectors**, i ho llencem | capçalera literal del fitxer; 947 municipis, mensual, des de 2006 | ⚠️ el desglossament multiplica les cel·les petites i el «<5» s'hi dispara. **Als micromunicipis pot ser que gairebé tot quedi emmascarat** — mesurar-ho abans de prometre la targeta |
| **B3** | **Índexs demogràfics derivats** que XIFRA publica i nosaltres no: dependència, recanvi, sobreenvelliment, potencialitat. **Surten de les franges d'edat que ja tenim** | XIFRA els dona per Castellfollit (dependència 60,54 · recanvi 133,96) | ⚠️ **fer A2 primer**: si el nostre envelliment ja no quadra amb el seu, els derivats tampoc quadraran |
| **B4** | **Homes / dones i edat mitjana** — dades bàsiques que XIFRA té i nosaltres no | | |
| **B5** | **[#308] Sèrie de població via censph** — desbloqueja l'evolució de població i de franges, que avui no tenim | ja obert | |

---

## C · Fonts noves, per ordre de valor

| | Què | Per què | Font |
|---|---|---|---|
| **C1** | 🟠 **Pressupost municipal** — ingressos, despeses, **deute viu i deute per habitant**. *El forat més gran que ha destapat l'auditoria* | «Deute per habitant: 274 €» a Castellfollit. Per a un alcalde això és tan central com l'atur, **i no en tenim ni una xifra** | **Ministeri d'Hisenda**, oberta. És la que fa servir XIFRA |
| **C2** | **Superfície municipal** (tenim densitat, no superfície) i **altitud** | barates i les demana tothom | INE / ICGC |
| **C3** | **Naixements i defuncions** | permeten els índexs vitals | Idescat |
| **C4** | **Cens administratiu d'activitat econòmica** | la nostra restauració i comerç vénen d'**OSM**, i el nostre propi caveat diu que la completesa creix amb el temps. Castellfollit: **5 serveis i 2 restaurants**. Un cens diria si això és el poble o és el mapa | SITMUN (Girona) o IAE |
| **C5** | **Autocontenció i autosuficiència laboral** — quanta gent que viu al poble hi treballa | *la* pregunta d'un poble dormitori, i no la responem | Idescat |
| **C6** | **Emissions de CO₂ per càpita** desglossades · **índex de motorització** · **coneixement del català** | catàleg de XIFRA que val la pena | diverses |

---

## D · Producte i estructura

| | Què | Estat |
|---|---|---|
| **D1** | **[#312] Partir la pàgina de comarca** com s'han partit el govern i el tauler | ja obert |
| **D2** | **[#310] `/comarca/[slug]` no enllaça els seus 9 llistats** | ja obert |
| **D3** | **[#307] Retirar els monòlits del Berguedà** (`govern.bergueda.json`, `tauler.bergueda.json`) | ja obert |
| **D4** | **[#306] `n_comarca` a la cel·la de `mart_govern`** — avui el web duplica el recompte | ja obert |
| **D5** | **Rang comarcal i doble referència són el nostre avantatge real** sobre XIFRA (el seu informe **no compara amb res**: dona un envelliment de 244,76 i el lector no sap si és molt o poc). No és una millora: és no perdre-ho quan ampliem catàleg | doctrina |

---

## E · Guardes i pipeline

| | Què | Per què importa |
|---|---|---|
| **E1** | **[#304] Meta-guarda: el CI ha de caure si un verificador versionat no l'invoca cap workflow** | *«una guarda que no s'executa decora, no protegeix»* — el patró ens ha mossegat 5 vegades |
| **E2** | **[#305] `export_indicadors_cat.py` emet artefacte versionat sense `--check`** | mateixa família |
| **E3** | **[#309] Un refresc anual del pipeline sencer**, no una cron per font | |

---

## F · Decisions que són de Bea

| | Què | Per què t'ho passo |
|---|---|---|
| **F1** | **Espai de Dades del Món Local** (AOC + Generalitat + 4 diputacions, en pilotatge). **És l'única de les cinc plataformes sense biaix gironí**: cobriria Berga i Guardiola igual que Olot. Si federa el que les diputacions ja tenen, **el pressupost municipal (C1) arribaria per aquí per als 947** | pot ser la font que ens estalvia deu connectors **o** un competidor amb quatre diputacions al darrere. **No he obert cap contacte** |
| **F2** | **[#313] `mart_electoral` versionat és estale** (31 files, el model n'emet 947) | decisió editorial teva |
| **F3** | **[#314] PR #287 R-RUBRICA**, el radar com a rúbrica única configurable | |
| **F4** | **SITMUN: proposo NO demanar-hi accés ara.** És per a ens públics, som privats, i **no cobreix el Berguedà**. Gastaríem la petició per a mitja mostra | recomanació, no decisió |

---

## Un apunt que no és una tasca

XIFRA imprimeix **«població estacional: 0»** a Castellfollit. Idescat **no publica ETCA per a
Castellfollit**, i sobre els 486 municipis que sí que en tenen **no hi ha ni un sol zero exacte**
(312 són negatius). Tot apunta que XIFRA converteix un buit en un zero — el pecat capital de la
nostra doctrina, imprès en un informe oficial d'una diputació. **No ho he pogut confirmar amb ells i
no ho afirmo**, però és exactament per això que l'aparell d'honestedat val la pena.

I la contrapartida honesta: **XIFRA té més catàleg que nosaltres.** El nostre aparell només val si
el cobrim de contingut, i avui corre més que el catàleg. **Per això A6 (les lectures P1/P2) va abans
que tota la secció C.**
