# Auditoria detallada · datapoble contra quatre plataformes, en quatre municipis

*Sitja, 2026-08-02. Encàrrec de Bea: comparar projecte a projecte amb un municipi de <1.000 i un de
>15.000, dos de Girona i dos del Berguedà.*

**Els quatre triats** (els de Girona, de la mateixa comarca per poder comparar dins de casa; Olot a
més és **de la cohort del GiroStudi**, així que serveix doble):

| | <1.000 | >15.000 |
|---|---|---|
| **Garrotxa (Girona)** | Castellfollit de la Roca · **960** | Olot · **39.516** |
| **Berguedà** | Guardiola de Berguedà · **962** | Berga · **17.539** |

---

## 0 · Les tres coses que aquesta auditoria ha destapat

Abans del detall, perquè no quedin enterrades:

1. **🔴 Un error NOSTRE, viu i publicat.** La fitxa diu que Idescat no publica l'ETCA «per a
   municipis <1.000 hab». **El criteri oficial no és aquest:** Idescat publica per als municipis de
   1.000 habitants o més **«ja sigui població padronal o població ETCA»** — un **O**, no un I. Per
   això **16 municipis de padró <1.000 la tenen** (Colera, 489 habitants, +526 d'estacional) i només
   **1 de ≥1.000 no la té**. Guardiola quadra al dígit: base 951 + 54 = **1.005**; el seu veí Olvan
   (926) queda fora. On l'ETCA falta, estem donant **una explicació que sona bé i no és la certa**.
   *(Verificat sobre els 947. Detall i llista de fitxers a corregir: `…_millores-a-fer_sitja.md`.)*
2. **✅ Validació externa que no teníem.** XIFRA i nosaltres donem **exactament les mateixes xifres**
   d'Olot i Castellfollit (població i estrangeria, al decimal). És el primer contrast independent de
   les nostres dades.
3. **🟡 XIFRA publica sobre 960 habitants coses que nosaltres no gosaríem**, sense cap advertiment:
   un **índex sintètic de fecunditat de 1,17 calculat sobre 6 naixements**, a dos decimals.

---

## 1 · XIFRA · l'única comparable de debò

**Cobertura:** 228 municipis, **només Girona**. Per a Berga i Guardiola, **XIFRA no dona res**: la
comparació només és possible a la meitat gironina de la mostra. (Nosaltres: 947.)

### 1a · On coincidim, xifra a xifra

| | Castellfollit (960) | Olot (39.516) |
|---|---|---|
| Població · XIFRA | 960 | 39.516 |
| Població · datapoble | **960** | **39.516** |
| Estrangers · XIFRA | 107 · 11,15% | 10.979 · 27,78% |
| Estrangers · datapoble | **107 · 11,15%** | **10.979 · 27,78%** |

**Idèntiques.** Val la pena dir-ho perquè és la primera vegada que algú de fora confirma les nostres.

### 1b · El que XIFRA té i nosaltres NO (i és el que un alcalde demanaria abans)

| Bloc | Xifres seves (Castellfollit / Olot) | Nosaltres |
|---|---|---|
| **Finances municipals** | Ingressos 1.694.456 € / 46.910.135 € · **Deute viu** 263.210 € / 17.091.030 € · **Deute per habitant 274 €** | **res** |
| **Població estacional** | 0 (Castellfollit) | *(en tenim l'ETCA, i no per a tots)* |
| Superfície i densitat | 0,73 km² · 1.315 hab/km² | densitat sí, superfície no |
| Homes / dones | 487 / 473 | **no** |
| Edat mitjana | 47,80 | **no** |
| Naixements i defuncions | 6 / 12 | **no** |
| Índex de dependència, de recanvi | 60,54 · 133,96 | **no** *(però surten de les franges que ja tenim)* |
| Edat mitjana dels estrangers | 36,19 | **no** |

**El forat més gros és el pressupost municipal.** «Deute per habitant: 274 €» és, per a un alcalde,
tan central com l'atur — i no en tenim ni una xifra.

### 1c · El que NOSALTRES tenim i XIFRA no

- **Rang comarcal a cada xifra** («8 de 31 al Berguedà») i **dues referències** amb el seu
  denominador. L'informe de XIFRA **no compara amb res**: ni comarca, ni província, ni Catalunya.
  Castellfollit té un índex d'envelliment de 244,76 i el lector no sap si és molt o poc.
- **Procedència per xifra.** XIFRA declara les fonts **una vegada al peu** («Elaboració pròpia a
  partir de les dades de l'IDESCAT, INE i Ministerio de Economía y Hacienda»); nosaltres, **a cada
  targeta**, amb font o fórmula i la seva data.
- **Doctrina de la incertesa.** Cap advertiment de mida a Castellfollit; cap interval; cap
  «sense sèrie amb motiu». Publiquen **la taxa de mortalitat sobre 12 defuncions** i **la fecunditat
  sobre 6 naixements**, a dos decimals, com si fossin la població de Barcelona.

> **La lectura honesta:** XIFRA té **més catàleg**; nosaltres tenim **més aparell d'honestedat**. No
> és una victòria: és una tria diferent, i la nostra només val si la cobrim de contingut. Amb 63
> mètriques i les lectures P1/P2 aturades, avui l'aparell corre més que el catàleg.

### 1d · L'índex d'envelliment: el nostre i el seu no diuen el mateix

| | Castellfollit | Olot | Guardiola | Berga |
|---|---|---|---|---|
| datapoble | **259,6** | **143,4** | 286,8 | 182,0 |
| XIFRA | **244,76** | *(no llegit)* | — | — |

**Discrepen a Castellfollit: 259,6 contra 244,76.** No és arrodoniment. Probablement el
numerador/denominador difereix (65+ contra 0-14 sobre padrons de dates distintes, o franges
diferents). **No ho he resolt** i és exactament la mena de cosa que cal resoldre abans de publicar
una comparació amb ells: si algun dia un alcalde posa les dues pantalles de costat, **hem de saber
per què no quadren**. → tasca.

---

## 2 · SITMUN · el que aporta als quatre

SIG per als municipis **de Girona**: per a Berga i Guardiola, **res**. Gratuït, WMS/WFS, INSPIRE,
però **cal sol·licitud formal i s'adreça a ens públics** — nosaltres no ho som.

**El que ens tocaria de prop si hi arribéssim:**

- **Cens d'activitat econòmica.** El nostre comerç i restauració vénen d'**OpenStreetMap**, i el
  nostre propi caveat diu que la completesa del mapa creix amb el temps. Castellfollit: **5 serveis
  i 2 restaurants** segons OSM. Un cens administratiu diria si això és el poble o és el mapa.
- **Registre d'allotjament turístic** — el tenim (RTC), i millor del que fem servir (vegeu §5).
- Cadastre, sòl, xarxes (aigua, clavegueram, enllumenat).

**El que no faria falta:** no aporta res sobre el Berguedà, que és el nostre nucli. Demanar-hi accés
avui seria gastar una petició per a mitja mostra.

---

## 3 · GiroStudi · el que aprenem sense ser-hi

Cohort de 10 anys, 18 municipis, ~4.000 persones. **Olot no hi és** —m'havia equivocat en triar-lo
per això: la cohort de la Garrotxa són **Besalú i les Preses**. Ni Castellfollit hi és.

**La troballa que val:**

> **La cohort no té CAP municipi de menys de 1.000.** El seu «petit» més petit és **Llívia, 1.572**.

Van triar «un gran i un petit per comarca», i el llindar de «petit» els queda molt per damunt d'on
comencen els nostres problemes. **Els 476 municipis catalans de menys de 1.000 —el 50%— seguiran
sense evidència de salut.** Això no és una crítica al seu disseny (una cohort necessita massa
crítica); és que **el forat que nosaltres estem intentant no amagar, ells no el cobreixen tampoc**.

I el que sí que podem aprofitar: **van caracteritzar TOTS els municipis gironins** en àmbits socials,
ambientals i de salut per triar la mostra. Si publiquen aquella caracterització, seria **el primer
contrast extern de la nostra `tipus_territorial`** — que avui no en té cap. *(Els quatre municipis
d'aquesta auditoria surten com a `interior_rural` els QUATRE, inclosos Olot amb 39.516 habitants i
Berga amb 17.539. Això sol ja diu que la nostra tipologia és grollera al tram alt.)*

---

## 4 · Espai de Dades del Món Local · què canviaria per als quatre

En pilotatge. Hi són **les quatre diputacions**, o sigui que —a diferència de XIFRA i SITMUN—
**cobriria Berga i Guardiola igual que Olot i Castellfollit**. És l'única de les quatre plataformes
que no té el biaix gironí.

Si federa el que les diputacions ja tenen, **el pressupost municipal** (§1b) arribaria per aquí per
als 947, i és el forat més gran que aquesta auditoria destapa.

→ **Decisió de Bea.** No he obert cap contacte.

---

## 5 · El que els quatre municipis ensenyen de NOSALTRES

Posats de costat, els nostres números fan visible una cosa que una taula sola no diu:

| | Castellfollit 960 | Guardiola 962 | Berga 17.539 | Olot 39.516 |
|---|---|---|---|---|
| % habitatge no principal | 25,6 | **41,2** | 24,2 | 18,4 |
| Establiments turístics /1.000 | 14,6 | **45,7** | 2,6 | 3,4 |
| Vidre kg/hab | 25,5 | **53,0** | 27,6 | 17,8 |
| Elèctric domèstic kWh/hab | 1.126 | **1.448** | 1.222 | 1.076 |
| Elèctric de **serveis** kWh/hab | 1.392 | **1.988** | 1.235 | 1.362 |
| Renda neta/persona | 15.597 | 15.580 | 15.449 | 15.213 |

**Dues lectures que surten soles:**

- **Guardiola és el cas de llibre de la pressió turística**: lidera les quatre mètriques de pressió
  alhora (41% d'habitatge no principal, 45,7 establiments per mil, el doble de vidre que Olot, i el
  consum de serveis més alt dels quatre). **Castellfollit, amb població quasi idèntica, no.** La mida
  no ho explica; el turisme sí — que és el que vam mesurar fa dos dies.
- **La renda és pràcticament igual als quatre** (15.213–15.597, un 2,5% de forquilla) mentre tota la
  resta varia el doble o el triple. **Un indicador que no distingeix res entre un poble de 960 i una
  ciutat de 39.516 mereix una mirada**: o és així de plana de veritat, o el nostre és massa gruixut.

---

## 6 · Tasques que en surten, per ordre

| | Què | Qui |
|---|---|---|
| **1** | 🔴 **Corregir el text de l'ETCA**: el criteri és «padró **O** població ETCA ≥1.000». 7 missatges × 2 idiomes + 4 docs + la costura del contracte d'abast | Talaia + Mirador |
| **2** | **Places turístiques** del RTC (informe anterior): Guardiola en seria el cas estrella | Sondeig |
| **3** | **Resoldre la discrepància de l'índex d'envelliment** amb XIFRA (259,6 vs 244,76) abans que ho vegi un tercer | Sondeig |
| **4** | **Pressupost municipal** — el forat més gran. Font oberta: Ministeri d'Hisenda, el mateix que fa servir XIFRA | Sondeig |
| **5** | Índexs demogràfics derivats (dependència, recanvi, sobreenvelliment): **no cal font nova**, surten de les franges | Sondeig |
| **6** | Revisar `tipus_territorial`: **Olot (39.516) i Berga (17.539) surten `interior_rural`** igual que Castellfollit i Guardiola | Talaia |
| **7** | Mirar l'Espai de Dades del Món Local | **Bea** |

**El que segueixo sense proposar:** ampliar catàleg per igualar XIFRA mentre el 70% de les frases de
les nostres lectures no compleixi la nostra pròpia regla d'evidència. Les tasques 1, 3 i 6 són
**arreglar el que ja tenim**, i van abans.
