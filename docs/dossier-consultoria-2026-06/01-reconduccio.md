# Reconducció de datapoble — rumbo decidit

**Data:** 2026-06-27 · **Autora:** Talaia (coordinació) · rumb de Bea (direcció).
**Input:** consultoria externa (27/06/2026), que respon al `00-dossier.md`. El document verbatim de la
consultoria és **input extern no versionat**; aquest fitxer n'és la **síntesi adoptada**, verificada
contra les fonts i conciliada amb el nostre dossier. *El repo és la veritat: aquí queda la decisió.*

> El dossier va posar la pregunta —«què oferim amb més valor?»—. La consultoria la respon amb una
> crítica dura i professional. Aquest document fixa el **rumbo**: target, propòsit, concepte,
> geografia, contracte d'abast i fases. A partir d'aquí, `bitacora/next.md` és la cua executable.

---

## 1. La peça que ho sosté (verificat)

Tota la reconducció pivota sobre un fet que **he comprovat contra Idescat**, perquè era massa important
per donar-lo per bo:

- **Idescat ja publica el present-vs-padró (ETCA) per a TOTS els municipis de ≥1.000 hab** des de la
  **base 2021** (abans només >5.000 hab i capitals de comarca). Font: Idescat, *Estimacions de població
  estacional* (novetats 2022; ampliació de la desagregació territorial a ≥1.000 hab).
- **Barcelona és el municipi #1 en població estacional ETCA absoluta, i en POSITIU**: ETCA total
  ≈ **105,2% del padró** (~+86.000 persones; 1.655.956 padró → 1.742.014 ETCA). Font: Anuari estadístic
  de Barcelona / Idescat 2022.

**Conseqüència.** El nostre *gap* **no és exclusiu** on el model és fort (≥1.000 hab): hi conviu amb una
xifra oficial que l'avaluador informat ja coneix. Només és exclusiu **sota 1.000 hab** —justament on el
model tremola més (micromunicipis, més incertesa)—. I pintar **Barcelona en negatiu** contradiu la font
amb què ens validem, al municipi més visible del país: és un autogol de credibilitat. *La credibilitat
d'un coroplètic la fixa la seva pitjor cel·la, no la millor.*

Fonts: [Idescat — Estimacions de població estacional](https://www.idescat.cat/pub/?id=epe) ·
[Idescat — novetats 2022](https://www.idescat.cat/novetats/?id=4889) ·
[Anuari estadístic de Barcelona — població ETCA](https://ajuntament.barcelona.cat/estadistica/catala/Anuaris/Anuaris/anuari13/cap02/C020301.htm).

## 2. El matís que millora el pla (doble costura)

La verificació afegeix un matís que **reforça** el concepte en comptes de trencar-lo. Mirant la
composició d'ETCA a Barcelona —no-residents presents (+265.344), residents absents (−179.286),
estacional (+86.058)— es veu que **ETCA és un net anual en equivalent-a-temps-complet** (compta feina,
estudi i turisme diürns i resta els residents absents). El nostre *gap* mesura **pernocta** (qui hi
dorm), via residu elèctric domèstic. **Són dues magnituds diferents.**

Per tant, cosir «Idescat a ≥1.000 / la nostra estimació a <1.000» no és una costura de **font**
només: és també una costura de **significat**. I aquí guanya el concepte: «l'observatori que sap el que
no sap» ha de **fer visible i etiquetar** aquesta doble costura (dues capes amb nom propi: *ETCA oficial*
vs *estimació experimental de pernocta*), no fondre-les en un sol «gap» continu. **Amagar-la seria
justament la deshonestedat que el projecte diu combatre.** El matís no és un problema a dissimular: és
la tesi en acció.

---

## 3. La decisió de rumbo

**Target.** L'**avaluador tècnic** que et pot contractar o col·laborar i sap llegir una pàgina de
metodologia. Públic secundari: el generalista espavilat que hi arriba de pas (que no en surti
espantat). **No** el ciutadà que actuarà sobre la xifra ni un client B2G —tots dos exigirien una xifra
municipal ferma que el model no pot sostenir—. Objectiu declarat del projecte: **porfoli i aprenentatge**,
deixant online quelcom mig seriós i defensable.

**Propòsit.** Demostrar **inferència honesta sota incertesa com a ofici**: un sistema que quantifica el
que no sap, integra la font oficial on existeix i es nega a fingir precisió on no la té. **El *gap* és
el ganxo narratiu; l'epistemologia és el producte.**

**Concepte.** **«L'observatori que sap el que no sap».** Híbrid amb jerarquia estricta:
- **Berguedà = nucli validat** als **9 munis ≥1.000 hab** (8,2% vs ETCA, dins de mostra; generalització
  held-out 80%→78,4% — frase canònica al contracte d'abast): la vitrina de fondària.
- **Catalunya = capa de context honesta i curada**, on es veu la **costura** entre el dato oficial
  d'Idescat (≥1.000 hab) i la nostra estimació experimental (només <1.000, etiquetada com a tal).
  Ensenyar la costura, en comptes de dissimular-la, **és** la declaració de porfoli.

És el **Concepte A reenquadrat com a hipòtesi**, sobre l'armadura del **Concepte C** (poble a poble, la
fitxa com a actiu). Confirma i esmola el «híbrid A+C» del dossier.

**Geografia.** Totes dues, amb comandament clar: **Berguedà mana, Catalunya acompanya.** Si el temps
aprieta, es retalla **amplitud** de Catalunya, **mai fondària** de Berguedà. La capa Catalunya pot
viure d'un indicador oficial net + el present-vs-padró cosit, sense necessitar els onze.

---

## 4. Contracte d'abast

**La regla:** només entra al mapa públic de Catalunya **el que sobreviu sense llegenda defensiva**. La
llegenda matisa, mai es disculpa. Si un indicador necessita un paràgraf demanant perdó per no enganyar,
**no entra** (baixa a Berguedà o a context de fitxa). *(Concilia §4 de la consultoria amb §3 del dossier.)*

| Indicador | On viu | Motiu |
|---|---|---|
| **Gent que el padró no veu** (gap) | CAT pública, **reenquadrat** | Estrella. ≥1.000 = ETCA Idescat oficial; <1.000 = estimació experimental. Costura visible. |
| **% habitatge no principal** | CAT pública | Oficial, llegible d'un cop d'ull, directe. |
| **Residus kg/hab/any** | CAT pública amb caveat | Mesura directa (ARC); segon pilar. |
| **Densitat de població** | Només amb **escala log**, si no a fitxa | Barcelona domina l'escala lineal. |
| **Renda neta per persona** | Fitxa (fora del mapa) | Aporta poc al conjunt del mapa; distreu. |
| **IETR** (exposició) | Berguedà / fitxa | No s'entén a escala Catalunya. |
| **Tipologia d'habitança** | **Només Berguedà** | Els llindars no generalitzen fora del Berguedà. |
| **Pressió turística** | Berguedà / fora | El proxy no capta la gran ciutat. |
| **Càrrega per residus** | Fitxa interna / fora | Es confon amb el *gap*; difícil d'explicar. |
| **Densitat de restauració** (OSM) | Fitxa context amb caveat | OSM infra-mapa el rural: mínim observat, no cens. |
| **Contradiccions de senyals** | **Fora** | No s'entén; reconvertir en bandera interna de confiança. |

**Resultat:** el mapa públic de Catalunya queda gairebé en **un indicador net** (% habitatge no
principal) **+ el present-vs-padró cosit** (Idescat ≥1.000 + estimació <1.000) **+ residus amb caveat**.
Tota la resta baixa a Berguedà o a context de fitxa.

---

## 5. Fases (el detall executable viu a `bitacora/next.md`)

Cada fase és **publicable per si sola**. Si falta temps en qualsevol punt, el ja fet queda dret.

- **Fase 0 · congelar abast i matar el que trenca** (~1 set). Treure del mapa públic CAT: tipologia,
  pressió turística, IETR, contradiccions, restauració → reubicar a Berguedà o fitxa (§4). Treure
  política de **totes** les pàgines **+ nota de mètode** amb postura deliberada (esborrar la pestanya
  no despolititza). Escriure el contracte d'abast en una pàgina. Decidir l'enquadrament del *gap*
  (registre d'**hipòtesi**, no de veredicte). → *Demostra criteri: saber tallar.*
- **Fase 1 · el nucli epistèmic** (~2-3 set) · **el 70% del valor**. Produir **intervals predictius
  reals** i comprovar-ne la **calibració** (reliability diagram + taula de cobertura empírica del
  p10–p90 en held-out); **refer la banda** si la cobertura no coincideix amb el que promet. **Cosir la
  capa CAT**: ETCA oficial a ≥1.000, estimació pròpia només a <1.000 (marcada experimental), amb la
  **costura visible** i la **doble etiqueta** (font + significat, §2). Verificar que Barcelona i les
  ciutats denses **les parla Idescat**. Documentar el supòsit causal i els seus **confusors** abans que
  el revisor. → *Demostra quantificació d'incertesa, calibració, integració de font oficial.*
- **Fase 2 · la vitrina Berguedà** (~1-2 set). 31 munis, dades completes, model validat i ben narrat.
  Pàgina de metodologia que aguanti auditoria, amb gràfics de validació. Error per tipus territorial i
  límits declarats (inclòs que **ETCA també és estimació**).
- **Fase 3 · la capa Catalunya honesta** (~1-2 set). Mapa públic amb «% habitatge no principal» + el
  present-vs-padró cosit. Escala log on la densitat ho demani. Llegenda que matisa, no que es disculpa.
- **Fase 4 · la fitxa i la home** (~1-2 set). Fitxa amb jerarquia dura: el *gap* i la seva incertesa
  com a protagonista; la resta col·lapsada, expandible. Treure de la vista per defecte la «maquinària»
  crua. Home: **mapa comarcal agregat + cercador**, amb el waveform del *gap* com a peça-firma.
  Etiquetar «el bessó del teu poble» com a experimental o validar la mètrica de distància.
- **Fase 5 · la capa d'IA honesta** (~1-2 set, opcional). Reescriure «Pregunta-li» com a **text-to-SQL
  acotat al Berguedà**, amb traça (font + consulta). Que **es negui** quan la pregunta surt del catàleg.
  Corregir el cas trencat («té més població Lleida que Girona?» → respon «Barcelona»). → *El «no»
  honest com a funcionalitat, no com a fallada.*

**Criteri de parada:** si només es poguessin fer dues coses, **Fase 1 + Fase 2** (nucli epistèmic +
Berguedà blindat = ja publicable i defensable). La resta eixampla.

---

## 6. La crítica convertida en tasques

Cada risc del diagnòstic es resol en una fase concreta i es prova amb un entregable:

| Risc | Es resol a | Entregable que ho prova |
|---|---|---|
| Idescat ja cobreix ≥1.000 hab | Fase 1 | Capa cosida: oficial a ≥1.000, estimació pròpia a <1.000, costura visible |
| Barcelona amb signe invertit | Fase 1 | La cel·la absurda desapareix: a ≥1.000 parla Idescat |
| R²=0,41 i confusors del residu | Fase 1 | Secció de límits que nomena els confusors abans que el revisor |
| Rang real o cosmètic? | Fase 1 | Reliability diagram + taula de cobertura empírica del p10–p90 |
| Validar model contra model | Fase 2 | Pàgina de mètode auditable; ETCA declarada com a estimació |
| El *gap* és polític | Fase 0 | Decisió d'enquadrament + nota de mètode sobre usos i límits |

---

## 7. Què queda a vot de Bea (no ho tanco jo)

- **Enquadrament del *gap*** com a hipòtesi/experiment (la còpia exacta = vot narratiu).
- **Postura política explícita + nota de mètode** sobre usos i límits (esborrar la pestanya no
  despolititza; cal posició deliberada, no delegada a la tecla d'esborrar).
- **Portar el document verbatim de la consultoria al repo?** Ara és input extern no versionat; aquesta
  síntesi n'és l'artefacte versionat. (Es pot afegir si es vol deixar visible la crítica que ens va
  reconduir.)
- **Per quina fase comencem a EXECUTAR.** Recomanació: **Fase 0** (ja pre-beneïda com a «guany
  estructural sigui quin sigui el concepte»).

---

## 8. Conciliació amb el dossier (honestedat)

- **El concepte coincideix:** el «híbrid A+C» del dossier = «A com a hipòtesi sobre l'armadura C»,
  esmolat. La convergència valida la tria.
- **On el dossier s'equivocava:** afirmava que el *gap* «no ho ofereix ningú més» —**fals per a ≥1.000
  hab** (Idescat sí)— i defensava el Barcelona-negatiu com a «senyal real»; és, com a mínim, **també
  possible artefacte d'extrapolació**, i en tot cas un **cost de credibilitat** que el reenquadrament
  evita. La reconducció és una **millora estricta** del dossier, no una alternativa.

— Talaia 🌊 · *input: consultoria externa, 2026-06-27 (no versionat).*
