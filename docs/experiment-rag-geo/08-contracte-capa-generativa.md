# Capa generativa · el RAG de debò — contracte de disseny (abans de codificar)

**De:** Talaia · **Origen:** contracte de la Rapaz (2-07-2026, OneDrive/CAJON/15) · **Data:** 2026-07-02
**Ordre:** es fusiona **abans** de codificar, com els contractes de les fases 1–3. És **el més important dels quatre**: els anteriors regulaven components que obeeixen per construcció; **aquest regula el primer que pot desobeir**.

> Fins ara la resposta la componia una plantilla governada per política determinista, i per això el 21/21 era un mirall. A partir d'aquí **un model generatiu redacta amb les seves paraules** sobre el context recuperat. El generador voldrà sonar fluid, i **la fluïdesa és enemiga natural del caveat**: esborrarà el «no es distingeix del marge» perquè fa lleig al mig d'una frase, trencarà l'empat perquè un guanyador sona millor, dirà una xifra de soroll amb aplom perquè el seu entrenament premia la seguretat. Tot el que era política, ell ho tractarà com a suggeriment. Aquest contracte existeix perquè **la doctrina sobrevisqui al component que té incentius per ignorar-la**.

## Arquitectura

El generador rep la pregunta i el context recuperat (cada municipi amb el seu **estatut de registre** i la seva **banda**). Redacta la resposta. La sortida passa per **dues validacions en ordre fix** — primer la dura, després la cega:

1. **Validació dura (SQL).** Cada xifra de la resposta **es traça a la seva cel·la del substrat**. Cada agregat **es recomputa**. El que no quadra **es talla o es marca, mai es deixa passar**. El generador **no té autoritat sobre cap número**.
2. **Validació cega (LLM).** Un segon model, que rep la pregunta, la dada i la resposta final **sense veure el raonament del generador**, comprova que el to hereta l'estatut de registre i que els caveats obligats hi són. **La ceguesa al raonament és el que el fa validador**: si veu el camí del primer, s'hi contagia i tens dos models dient-se que sí.

## El que el registre obliga a la redacció

- **Oficial:** xifra amb banda i contrast ETCA. **Prohibida la falsa precisió** del número clavat sense rang.
- **Senyal:** estimació en rang, veu graduada per la σ, esment que **no hi ha validació oficial**.
- **Soroll:** l'abstenció **reconeix que hi ha estimació i la desautoritza amb el motiu**. El «no tinc dada» aquí seria mentir per l'altre costat.
- **Col·lisió:** la xifra compartida **mai es presenta com a específica**; el grup es nomena.
- **Empat de comparació:** **cap guanyador** entre bandes que se solapen; el «probablement» queda **prohibit** mentre la regla de distingibilitat sigui binària.
- **Fora de catàleg:** «no ho tinc», **distingit del silenci de soroll** — són dos silencis diferents i el sistema sap coses diferents en cada cas.

## Les regles anti-trampa (aquí canvien de naturalesa)

**El prompt és sistema i es congela.** El prompt del generador **es versiona al repo com el codi**. Retocar-lo després de veure resultats del banc congelat és **entrenar contra el test**. Per desenvolupar-lo hi ha un **conjunt de desenvolupament separat** (preguntes noves que NO són al banc); el banc congelat **només es toca a la passada oficial**.

**Passades múltiples, distribució sencera.** El component és estocàstic: una passada no és un resultat. Protocol preregistrat: **N passades per pregunta (proposta de partida: 5)** i es reporta **la distribució** (quantes de N passen cada cas). **Prohibit reportar la millor passada.** Un cas que passa 3 de 5 és un cas **inestable**, i la inestabilitat **és resultat**, no soroll a netejar.

**Els errors es classifiquen, no només es compten.** Taxonomia: *xifra inventada o alterada · agregat estimat en comptes de comptat · caveat esborrat · to ferm sobre soroll · empat trencat · col·lisió amagada*. **La taxonomia importa més que el total**, perquè diu on la fluïdesa ataca la doctrina.

**La validació dura no compta com a mèrit del generador.** Si la resposta surt bé perquè el validador ha tallat una xifra falsa, el cas es reporta com a **intervenció**, separat dels casos on el generador va escriure bé de primeres. El número que importa: **quantes vegades el generador respecta la doctrina sol, i quantes el salva la gàbia**.

## La mesura, i el número que de debò es busca

El **mateix banc congelat de 34 preguntes**, més les **paràfrasis adversarials** quan existeixin. El resultat central de tota la fase: **la resta entre el sistema determinista i el generatiu sobre el mateix banc** — 21/21 contra el que surti. Aquesta diferència és **el cost de la fluïdesa, mesurat amb una σ real al darrere**, i és la contribució que ningú més té. Un delta gran seria un resultat excel·lent per publicar; **un delta petit també**. L'únic resultat dolent seria **un delta no cregut**: sortit d'un prompt retocat contra el banc o d'una millor passada triada a dit.

## Nivells d'èxit, fixats abans de veure res

Els fixa **la Bea**, com a la Fase 3, abans de la passada oficial. Amb un matís nou: es fixen **per separat** el nivell **amb gàbia** (validadors actius) i el nivell **sense** (generador nu), perquè **la distància entre tots dos és la mesura de quant la doctrina depèn de la vigilància externa i quant l'ha absorbit el component**.

## Ordre respecte a la resta

1. **Les paràfrasis adversarials del recuperador van PRIMER**: el generador multiplicarà la varietat de frasejos i cal saber si el recuperador ja tremola sense ell.
2. **L'estrella queda independent** i no es bloqueja.
3. **Les fases de graf i temporal segueixen tancades** fins que el delta d'aquesta capa estigui sobre la taula.

## Repartiment de feina (afegit de Talaia, per jurisdicció)

- **Talaia:** paràfrasis adversarials (esborrany → congelació de Bea) · conjunt de desenvolupament del prompt (separat del banc) · validació dura (SQL, determinista) · arnès de passades múltiples + classificador d'errors + separació intervenció/mèrit · esborrany del prompt (que es congela abans de la passada oficial).
- **Bea:** congela les paràfrasis · fixa **N** (proposta 5) · fixa els **nivells d'èxit amb gàbia i sense** (abans de la passada oficial) · tria/consent el **model generador i el validador cec** (decisió d'infra i cost: calen crides a una API d'LLM — el generador i el validador cec han de ser models diferents o com a mínim contextos aïllats; la clau mai al repo).
- **Trazo (si cal):** cablatge de la clau API com a secret local/CI-opcional, mai al repo públic.
