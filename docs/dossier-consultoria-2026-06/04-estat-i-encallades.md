# Estat i encallades — datapoble (2026-06-29)

**Data:** 2026-06-29 · **De:** Talaia (coordinació) · **Per a:** Bea (direcció) + Rapaz (consultoria).

> El nucli aguanta i és honest. **No estem encallades per codi: estem encallades per UNA decisió de
> direcció** —l'arquitectura «verificat-primer» vs «costura amb el <1.000 publicat»— de la qual pengen
> gairebé tots els passos següents. Aquest document separa el que **ja és dret** del que **espera una
> frase teva**.

---

## El que SÍ hem fet (i és a `main`, desplegat)

### Fase 0 — congelar abast ✅
- Contracte d'abast en una pàgina: el mapa públic CAT passa de **11 → ~3 indicadors** (gap reenquadrat
  + % habitatge no principal + residus). La resta baixa a Berguedà o a fitxa.
- **Política fora de tot el web** (ruta, blocs, glossari, nav, peu).
- *Gap* reenquadrat com a **hipòtesi** (eix «hi dorm menys/més del que consta»).

### Fase 1 — el nucli epistèmic (el 70% del valor) — fet, llevat d'un pas
- **Calibració honesta**: la banda del 80% cobreix el **78,4%** real en held-out (reliability diagram).
  Sense sobreajust (in-sample = held-out). *La banda diu el que promet.*
- **Partició senyal/soroll**: dels 151 municipis de signe oposat, **8 són senyal real i 142 soroll**.
  El «31% aparent» és, de debò, **~1,6%**. No disfressem el marge d'error de fenomen.
- **Costura al mapa i al beeswarm**: a **≥1.000 hab mana Idescat (ETCA oficial)**; a <1.000, estimació
  pròpia en rang, marcada. **Barcelona surt +6%** (oficial), no el −18% absurd del model.
- **Doble etiqueta** declarada: ETCA (vinculació anual, net) ≠ la nostra pernocta (residu elèctric).

### Passada anti-overpromise (les sis notes de Rapaz) ✅
- **P0 confiança↔validació**: cap municipi sense ETCA mostra «confiança alta» → «sense validació oficial».
- **IETR col·lapsat** a la capçalera de la fitxa: ara lidera la **població de padró** (oficial).
- **/resum eliminat**; fora la paraula «real»; fora el tag de tipologia; «el bessó» marcat experimental.

### Passada de solidesa (avui, 2026-06-29) ✅
- **Diagnòstic multiagent + crítica adversarial**, *verificats al codi un per un*. Lliçó incòmoda: la
  pròpia síntesi automàtica va **sobrepormetre** el problema #1 (deia que la fitxa mostrava «confiança
  alta» sense etiqueta —que ja estava resolt al P0—). Els crítics ho van enxampar; ho vam confirmar
  obrint els fitxers. **Cap síntesi entra sense verificar el fet que la sosté.**
- **#1 · Lede de fitxa honest** (LIVE): el Berguedà manté el lede profund; la resta de Catalunya passa a
  «base oficial + presència estimada **en rang**; profunditat i validació reservades al Berguedà».
- **#3 · Sanejat de dades**: els **20 micromunis** sense estimació de pernocta ja no afirmen confiança
  sobre el no-res (`confianca → null`); **l'IETR intacte** (és independent). Fet des de la font,
  idempotent, amb **nou `--check` a CI** perquè el JSON no torni a derivar.
- **Recomanació + 3 baranes de curació** al repo: [`03-recomanacio-solidesa.md`](03-recomanacio-solidesa.md).

---

## On estem encallades

### 1. EL NUS — i bloqueja gairebé tot: «verificat-primer» vs «costura»
La pregunta de la Bea (2026-06-29): *si només **9 municipis** estan validats, no és millor deixar tota
Catalunya només amb fonts verificades?*

- **Fet dur:** validat de debò = **9 munis** (Berguedà ≥1.000). Però el **verificat és ampli** (oficial
  per als ~947: padró, % no principal, renda, densitat, demografia, residus, RTC + ETCA als 486 de
  ≥1.000); l'**inferit és estret** (la nostra pernocta). El valor exclusiu **només existeix sota 1.000**
  —i és justament on no tenim cap validació externa possible avui.
- **Dues posicions, totes dues defensables:**
  - **Consultora** (`01-reconduccio.md` §3-4): **MANTENIR** l'estimació <1.000 publicada al mapa públic
    CAT, en rang i etiquetada experimental. *«Ensenyar la costura, en comptes de dissimular-la, ÉS la
    declaració de porfoli.»* Target = avaluador tècnic que llegeix metodologia, **no** el ciutadà que
    actuarà sobre la xifra.
  - **Bea** (instint actual): **verificat-primer**. Treure la inferència <1.000 de la vista pública per
    municipi i confinar-la a la **vitrina del Berguedà** + un **laboratori a /metodologia**.
- **Evidència nova que la consultora no tenia quan ho va escriure:** el cas **Barcelona −18%** —un lector
  (la Bea mateixa) llegint la inferència com a fet, malgrat les etiquetes. Suggereix que el supòsit
  «l'etiqueta basta per al lector tècnic» s'esquerda a la pràctica.
- **Estat:** és un **vot narratiu de la Bea** (la reconducció el deixa explícit a §7). **Sense aquesta
  decisió, queden bloquejats:** la costura a la fitxa, el replegar-vs-caveat de la profunditat (#2), les
  banderes data-level (#4, en bona part), el front-0 d'utilitat (#7).

### 2. Vots de la Bea pendents (de la reconducció §7)
- **Enquadrament del *gap*** (la còpia exacta = vot narratiu).
- **Postura política explícita + nota de mètode** sobre usos i límits (esborrar la pestanya no
  despolititza; cal posició deliberada).

### 3. Costura del *gap* a la fitxa
Últim pas escrit de Fase 1. El mapa i el waveform ja apliquen «≥1.000 = ETCA oficial»; **la fitxa
encara no**. Depèn en part del nus #1 (si verificat-primer, la fitxa <1.000 canvia de forma).

### 4. Infracobertura per tipus metropolità
`corona_metropolitana` (n=9) cobreix **55,6%** real a 80% nominal; `litoral_metropolita` (n=7) **57,1%**.
Cal **refer la banda o declarar-ho**, i treure la cobertura per tipus a /metodologia **sempre amb la n
al costat** (a n=7-9 el percentatge és gairebé soroll: publicar-lo com a precís seria falsa precisió).

### 5. El que NO sabem (i ho diem)
El **<1.000 hab no té validació externa possible avui** (Idescat no el cobreix; no hi ha contra què
mesurar). Camí honest per guanyar-se'l: el **test multianual** (a la raw d'ICAEN hi ha 2013–2024; la
pernocta només fa servir un tall). Un *gap* que **persisteix** any rere any és senyal; un que
**parpelleja** és soroll. Seria una **validació interna** que podria justificar publicar el <1.000.

### 6. Deute menor
`/pregunta-li` encara pot respondre malament (Fase 5, opcional): o es desconnecta o s'acota amb negació
honesta. Una falsa promesa viva és pitjor que l'absència.

---

## La decisió que ho destrava

**Una frase de la Bea sobre el nus #1** (verificat-primer o costura) desbloqueja la costura a la fitxa,
el #2, el #4 i el #7. Tota la resta és executable, verificada i de risc baix. No estem aturades per no
saber fer-ho: estem aturades perquè **fer-ho en una direcció o l'altra reconfigura el producte**, i això
és direcció, no tècnica.

— Talaia 🌊 · *detall executable a [`bitacora/next.md`](../../bitacora/next.md); recomanació a [`03-recomanacio-solidesa.md`](03-recomanacio-solidesa.md).*
