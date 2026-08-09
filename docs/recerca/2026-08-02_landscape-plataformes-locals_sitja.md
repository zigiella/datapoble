# Landscape · cinc plataformes de dades del món local

*Sitja (bifurcació de Talaia per a recerca), 2026-08-02. Encàrrec de Bea: mirar cinc projectes i
veure què podem integrar o aprendre.*

**Res d'això s'ha implementat.** És recerca, i les dues troballes accionables van amb el número
verificat al costat perquè es puguin decidir sense refer la feina.

---

## Resum en una taula

| | Què és | Per a nosaltres |
|---|---|---|
| **XIFRA** (Dip. Girona) | Sistema d'informació estadística local, 228 municipis, ~120 indicadors | **El nostre bessó més proper.** Font d'idees d'indicador, no de dades |
| **SITMUN** (Dip. Girona) | SIG municipal gratuït, WMS/WFS, INSPIRE | Capes que no tenim; **cal sol·licitud formal** |
| **GiroStudi** (Dip. Girona) | Cohort digital de salut, 10 anys, 18 munis | **Paral·lel metodològic**: van caracteritzar TOTS els municipis per triar la mostra |
| **Espai de Dades del Món Local** (AOC + Generalitat + 4 diputacions) | Espai federat de dades locals, en pilotatge | **El que més ens afecta estratègicament** |
| **DigitAldeas** (Dip. Badajoz) | Projecte FEDER, 30 mesos, 858k€, caracterització de llogarets EUROACE | Precedent de finançament i d'enfocament |

---

## 1 · Les dues coses que podem fer demà, amb dades que JA baixem

Això és el més valuós que ha sortit, i no ve de cap plataforma: ve de **comparar el seu catàleg
d'indicadors amb el nostre i anar a mirar la nostra pròpia matèria primera**.

### 1a · L'atur per sexe i edat — el llencem cada mes

XIFRA publica *«Taxa d'atur registral, estimada per sexe»* i *«per edats»*. Nosaltres publiquem el
total i prou.

**El CSV del SEPE que ja ingerim cada mes porta el desglossament sencer.** Capçalera literal:

> `PARO REGISTRADO POR MUNICIPIOS DESGLOSADO POR SEXO, TRAMOS DE EDAD Y SECTOR DE LA ACTIVIDAD`

Columnes que baixem i descartem: `Paro hombre edad <25` · `25-45` · `>=45` · `Paro mujer edad <25` ·
`25-45` · `>=45` · i **cinc sectors** (agricultura, indústria, construcció, serveis, sense ocupació
anterior).

**Cost:** zero d'ingesta nova. És ampliar el connector i el mart. **947 municipis, mensual, des de
2006.**

⚠️ **Amb una trampa que ja coneixem:** el desglossament multiplica les cel·les petites, i el SEPE hi
aplica el «<5». Al fitxer d'exemple ja s'hi veu (`Abla`: `<5` a dues columnes). La doctrina de
l'interval [1,4] hi val igual, però **hi haurà molts més emmascarats** que al total — i als
micromunicipis pot ser que gairebé tot ho estigui. Cal mesurar-ho abans de prometre la targeta.

### 1b · Les PLACES turístiques — la xifra que de veritat mesura la pressió

XIFRA publica *«Places turístiques per 1.000 habitants»*. Nosaltres publiquem **establiments**.

**El RTC que ja ingerim porta `total_places`.** Verificat:

| | |
|---|---|
| Places declarades a Catalunya | **790.212** |
| **la Pobla de Lillet** | **31 establiments · 657 places** |

657 places en un poble de **1.106 habitants** és una capacitat del **59% de la població resident**.
«31 establiments» no diu això, i és exactament el que un alcalde vol saber.

⚠️ **Cobertura parcial i s'ha de dir:** només **32.880 dels 112.964** establiments d'alta (29%)
declaren places. Probablement per tipus d'establiment (els HUT potser no en declaren). **Publicar
una ràtio de places sense saber què falta seria el nostre error clàssic**: cal veure primer si la
cobertura és sistemàtica per tipus, i si ho és, publicar-la **per als tipus que la declaren** i
dir-ho, o no publicar-la.

---

## 2 · XIFRA · el bessó, i on ens diferenciem

228 municipis de Girona, ~120 indicadors, vuit àmbits. Web amb informes i mapes temàtics; **no he
trobat API ni descàrrega oberta** — o sigui que **com a font no ens serveix**, però com a catàleg
d'idees és or.

**Indicadors seus que no tenim i valen la pena** (per ordre del que crec que aporta):

- **Taxa d'habitatges vacants** i **de lloguer** — nosaltres tenim «% no principal», que **barreja
  segona residència i buit**. Són coses diferents i un alcalde les distingeix.
- **Autocontenció i autosuficiència** (mercat de treball): quanta gent que viu al poble hi treballa.
  És *la* pregunta d'un poble dormitori i no la responem.
- **Emissions de CO₂ per càpita**, desglossades (residencial, terciari, residus, transport, indústria).
- **Índex de motorització**, **densitat comercial per superfície**, **taxa de coneixement del català**.
- Un munt d'índexs demogràfics derivats (sobreenvelliment, dependència, recanvi, potencialitat) que
  **no requereixen dada nova**: surten de les franges d'edat que ja tenim.

**On som diferents, i val la pena no perdre-ho:** el seu catàleg és més ample; el nostre aparell
d'honestedat (procedència a cada xifra, interval en comptes de zero, `sense sèrie` amb motiu, rang
comarcal llegit i no calculat, referència del mateix perímetre que el numerador) **no l'he vist
enlloc d'aquests cinc**. No ho dic com a galó: ho dic perquè si algun dia ens comparen, aquesta és
la diferència real, i no el nombre d'indicadors.

---

## 3 · Espai de Dades del Món Local · el que més ens afecta

Promogut per la **Xarxa de Governs Locals Intel·ligents**: Generalitat + **les quatre diputacions** +
Localret + Ajuntament de Barcelona + AOC. En **fase de construcció, pilotatge i posada en producció
progressiva**. Parla de *«federació d'espais de dades»*, infraestructura comuna i marc de governança
únic, amb acompanyament **especialment als ens petits**.

**Per què importa:** és la infraestructura institucional del mateix problema que ataquem. Té dues
lectures i no vull triar-la jo:

- **Com a oportunitat:** si federa dades locals amb estàndard comú, és **la font que ens estalvia
  deu connectors** — i el nostre `data_map` i la doctrina de procedència ens fan un consumidor
  ordenat.
- **Com a risc:** si acaba oferint fitxes municipals, **el nostre producte se solapa amb el d'una
  xarxa que té les quatre diputacions al darrere.**

**El que jo miraria abans de decidir res:** si publiquen catàleg i condicions d'accés per a tercers
no-administració. Datapoble **no és un ens local**, i tot això està pensat per a ens locals.

→ **Decisió de Bea.** No obro cap contacte ni demano res sense el seu vistiplau.

---

## 4 · SITMUN · capes que no tenim, amb porta

SIG web per als municipis de Girona, **gratuït**, WMS/WFS i INSPIRE. Capes: cadastre, classificació
del sòl, xarxes (aigua, clavegueram, enllumenat), **cens d'activitat econòmica**, cens d'habitatge,
**registre d'allotjament turístic** i —m'ha fet gràcia— **nius de vespa asiàtica**.

**El fre:** *«L'entitat interessada ha de formalitzar la sol·licitud del servei»* i s'adreça a **ens
públics**. Nosaltres no ho som. WMS/WFS són sovint oberts encara que el portal sigui tancat, però
**no ho he comprovat i no ho afirmo**.

**El que aprenc, més que el que agafo:** tenen el **cens d'activitat econòmica** per municipi. La
nostra restauració i comerç venen d'**OpenStreetMap**, amb el problema conegut que la completesa del
mapa creix amb el temps i no es pot separar de l'obertura real. Una font administrativa el
resoldria.

---

## 5 · GiroStudi · el paral·lel metodològic

Cohort digital de **10 anys**, ~4.000 persones de 16 a 79 anys, 18 municipis gironins. Lidera la
Diputació de Girona amb ICS, IDIAP, IDIBGI, CSIC i universitats. Comença el **16 de febrer de 2026**.
Recull entrevistes, mostres biològiques, **sensors d'aire interior** i creuament amb **aigües
residuals**.

**El que ens toca de prop no és la salut: és com van triar la mostra.**

> *«S'han caracteritzat tots els municipis gironins en àmbits socials, ambientals i de salut»* per
> triar-ne **dos per comarca, un gran i un petit**.

Això és **exactament la feina de tipologia que fem** (`tipus_territorial`, franges de mida), feta per
una diputació amb equip científic. I la seva estratificació —**per comarca**, amb la mida com a
segon eix— **coincideix amb el que vam mesurar nosaltres**: la comarca explica més variància que la
franja de mida a 8 de 9 mètriques.

**Dues coses per fer, cap urgent:** buscar si publiquen aquella caracterització (seria un contrast
extern de la nostra tipologia, que avui no en té cap), i tenir present que **d'aquí a un any hi
haurà dades de salut municipals** amb les quals el nostre tauler podria dialogar.

---

## 6 · DigitAldeas · el precedent llunyà

Diputació de Badajoz + Universitat d'Extremadura, euroregió EUROACE (Espanya-Portugal). **858.000 €,
75% FEDER, fins al 31/12/2028.** Model digital col·laboratiu per caracteritzar i revitalitzar
llogarets: dades geoespacials, indicadors de la **Nova Bauhaus Europea**, sensors i tallers de
participació.

**El que n'aprenc són dues coses, i cap és tècnica:**

1. **Hi ha finançament europeu per a exactament el que fem** —caracteritzar i planificar pobles
   petits contra la despoblació— i s'articula per diputació + universitat.
2. Barregen **caracterització amb dades** i **participació ciutadana**. Nosaltres som tot el primer.
   No dic que ho canviem: dic que en la mena de convocatòria que finança això, el segon compta.

---

## Què proposo (per ordre de relació valor/cost)

1. **Places turístiques** (§1b) — dada que ja tenim, canvia la lectura d'un poble. **Amb la cobertura
   mesurada primer.**
2. **Atur per sexe i edat** (§1a) — dada que ja baixem. **Amb l'impacte del «<5» mesurat primer.**
3. **Índexs demogràfics derivats** de XIFRA que no necessiten font nova (sobreenvelliment,
   dependència, recanvi).
4. **Separar «buit» de «segona residència»** al parc d'habitatge — avui els barregem.
5. **Mirar l'Espai de Dades del Món Local** amb Bea: font, competència, o totes dues.

**El que NO proposo:** demanar accés a SITMUN (som privats i el servei és per a ens públics: no
malgastem la petició fins que sapiguem què en volem), ni afegir indicadors només per igualar el
catàleg de XIFRA. **Tenim 63 mètriques i les lectures P1/P2 aturades perquè el 70% de les frases no
compleix la nostra pròpia regla d'evidència.** Ampliar abans d'arreglar això seria fer el contrari
del que predica el projecte.
