# X1 · Collita del geo-rag cap a `packages/ai` — la gàbia RE-VALIDA

**Data:** 2026-07-16 · **Agent:** Brúixola · **Contracte:** `docs/ajuntaments/C5-collita-geo-rag.md`
(vinculant) · **Especificació:** `docs/ajuntaments/tasques-especificades.md` §X1
**Barrera:** verificada a `origin/main` abans de treballar (`bitacora/next.md` ▶️ TRET DE
SORTIDA · `tasques-especificades.md` ▶️ EN MARXA). Tret de sortida de Bea (#245).

---

## Què s'ha collit

Les dues peces del C5 §1, i cap més.

**(i) La doctrina** → `src/datapoble_ai/doctrine.py` + `prompts/redactor-v1.md`.
**(ii) La gàbia** → `src/datapoble_ai/cage.py`, amb la RE-VALIDACIÓ del C5 §2.
La capa generativa (`src/datapoble_ai/narrator.py`) va **darrere** de la resposta
determinista: el patró es manté, l'LLM segueix sense escriure SQL, i la línia de
provinença **no la redacta mai el model** — se li enganxa deterministament.

`packages/geo-rag` **no s'ha tocat** (0 fitxers). `politics.py` **intacta** (0 línies).
El pin `openai>=1.30` **inalterat** (`pyproject.toml` sense canvis); cap dependència nova.

## Adaptat als marts, no copiat

El registre de l'experiment era del **municipi** (cobertura ETCA ≥1.000 d'Idescat) sobre un
substrat amb `estimacio`/`rang_baix`/`rang_alt`/`padro`/`etca_oficial`/`collision_group`.
**Els marts no porten cap d'aquests camps.** Copiar el codi hauria estat demanar al model que
inventés columnes. El registre passa a ser de la **cel·la** (mètrica × municipi), llegit del
que el contracte i el mart declaren de veritat:

| Registre | Què vol dir | D'on surt |
|---|---|---|
| `oficial` | xifra mesurada | contracte: sense `categoria: derived` |
| `senyal` | inferència | contracte: `categoria: derived` |
| `soroll` | inferència que el mart mateix desautoritza | mart: `confianca = baixa` |

`confianca` no me l'invento: és una mètrica del contracte («bandera de fiabilitat de les
estimacions») i el seu propi caveat ja diu la doctrina del soroll — *«un buit honest val més
que un fals precís: 'baixa' marca micromunicipis … i casos on els senyals divergeixen»*. La
collita només li dona dents.

**Els dos silencis** es conserven: `soroll` («tinc l'estimació i la desautoritzo amb motiu»)
≠ fora de catàleg («no ho tinc»). El prompt del validador cec **v2** s'ha collit
**byte a byte** (test que ho prova); com que és un prompt que obeeix les DADES, no ha calgut
editar-lo: el que s'adapta és el missatge d'usuari, que li passa `registre`,
`distinguishable` i `caveat_obligat`. Tal com preveia l'especificació.

## El que NO ha sobreviscut la collita (declarat, no amagat)

- **Bandes** («el rang és la dada»): els marts guarden un valor puntual per cel·la i cap
  interval. Una regla de solapament aquí seria **fabricada**. La regla de distingibilitat
  es **degrada a l'empat exacte** — l'única separació que les cel·les del mart poden provar.
- **Col·lisió** («la xifra no és específica del municipi»): és una propietat de
  l'ESTIMADOR repetint xifra entre municipis; el mart no ho registra. No modelat, no endevinat.
  La gàbia tampoc no en fabrica cap postdata: si el validador ho marqués, el text no és
  reparable i cau al fallback.

---

## Dues coses que la collita ha destapat (i que no eren teòriques)

### 1. L'empat: el determinista afirmava guanyadors que les dades no assenyalen

`ORDER BY col DESC LIMIT 1` tria **una fila d'un cim compartit per atzar d'ordre de fila**.
Mesurat al mart real, no hipotètic:

- **47 municipis** comparteixen `index_turisme = 100` → el producte deia *«El municipi amb
  més Pressió turística és Capolat (100)»*.
- **6 municipis** comparteixen `IETR = 100` → deia *«…és Llançà (100)»*.

Són índexs **topats a 100**: el cim és un artefacte del topall, i el sistema el venia com un
fet específic. És exactament l'`empat_trencat` que la doctrina prohibeix.

**Per què ho he arreglat al determinista i no només al generatiu:** el C5 §2 fa del mode
determinista el **fallback** de la gàbia. Un fallback que afirma un guanyador fals no és un
fallback — la premissa de seguretat del contracte no s'aguantava. Ara el rànquing consulta
l'empat abans de nomenar ningú i, si el cim és compartit, ho diu i els enumera.
**Cap eval existent canvia** (la fixture no tenia empats): 13/13 segueixen verds.

### 2. El caveat esborrat, a la capa determinista, abans de cap LLM

`Metric.note()` llegia només `nota:`. El contracte escriu el caveat amb **dues** claus:
`nota:` (5 mètriques) i **`caveat:` (14)**. I les 14 són justament **totes les inferències**
(`poblacio_pernocta_est`, `gap_pernocta`, `confianca`, `carrega_total_est`…). Ningú, enlloc del
codi, llegia `caveat:` (verificat amb grep a tot `packages/`).

Resultat en viu abans de l'esmena: *«Població real estimada (pernocta) de Guardiola de
Berguedà: 852 habitants (est.). Font: … Fórmula: …»* — i **cap caveat**. El text del contracte
que no arribava al lector deia literalment *«INFERÈNCIA, no cens … la xifra es llegeix com a
RANG + confiança … Lectura ECOLÒGICA»*.

La gàbia no pot exigir un caveat obligat que el catàleg es menja. Esmenat a `catalog.py`
(llegeix les dues claus; `nota` mana si mai n'hi hagués dues). Ara el caveat arriba al text.

---

## Evidència

- **187 tests verds** (116 abans + 71 nous), tots **offline**: cap depèn de xarxa ni de claus.
  El redactor i el validador cec són `ScriptedBackend` (la gàbia és el subjecte, no el temps).
- **13/13** evals originals verds (cap regressió) · **7/7** de l'eval nou end-to-end.
- `ruff check src evals tests` net.
- **La porta política sobre el generatiu** (llistó #3): test que, **fins i tot amb l'unlock
  posat i la resposta determinista oberta**, no es crida cap model i `status =
  fallback_political_gate`. El desbloqueig obre dades, mai la prosa d'un model sobre un vot.
- **El fallback comprovat** (llistó #2): cas provocat a `narration_cases.yml` — text que el
  validador cec segueix rebutjant després d'engabiar-lo → el servit és **exactament** el text
  determinista (assert d'igualtat, no de substring).
- **SpendGuard** (llistó #5): la narració es pressuposta **sencera** (redactor + les DUES
  lectures cegues) *abans* de la primera crida; si el sostre no la cobreix, no s'engega —
  mai una gàbia a mitges. Test que compta 3 crides registrades.
- **Fidelitat de la collita**: test que el prompt del validador és byte a byte el congelat, i
  test que el prompt del redactor **no anomena** cap camp que els marts no tenen.

## Detalls d'implementació que valen la pena

- **Els decimals.** El substrat de l'experiment tenia enters (persones); els marts tenen
  floats en convenció ca/es (`74,28`). Portada tal qual, la gàbia hauria llegit `74,28` com
  els enters 74 i 28 i **hauria tallat la seva pròpia dada correcta**. La gramàtica de números
  s'ha reescrit per als marts.
- **Els prompts viuen DINS del paquet** (`src/datapoble_ai/prompts/`): la roda només empaqueta
  `src/datapoble_ai`, i un `prompts/` germà no hi hauria arribat al desplegament. Verificat
  construint la roda i mirant-ne el contingut.
- **La fixture** guanya les columnes de pressió (`kwh_hab`, `poblacio_pernocta_est`,
  `gap_pernocta`, `gap_pernocta_pct`, `confianca`) perquè el registre `soroll` es pugui
  provar offline. `kwh_hab`/`confianca` són **triats**; les derivades es calculen amb les
  fórmules del contracte (internament consistents). Documentat al README de fixtures com a
  **il·lustratiu per a TOTES les files**, `is_real` incloses. Castellar de n'Hug porta
  `confianca: baixa` a posta: és l'exemple del contracte mateix (residus alts, elèctric baix
  per la llenya de muntanya).

## Què queda

- **X2** (activar `render.yaml` dorment) i **X3** (catàleg govern + preguntes suggerides) són
  d'altres; la capa generativa queda **opt-in** (`Agent(narrator=…)`) i **inerta sense clau**:
  sense narrador injectat, el paquet es comporta exactament com abans.
- **Handoff a: Sondeig (dades)** — l'empat massiu és un símptoma de la **saturació dels
  índexs**: 47 municipis a `index_turisme = 100` i 6 a `IETR = 100` no és un empat casual, és
  un **topall** que aplana el cim. El xat ja no menteix, però la pregunta de dades segueix
  oberta: un índex que satura 47 municipis al màxim, informa? (Escala? Winsorització? Un
  altre tall?) No és jurisdicció meva i no ho toco.
- **Handoff a: Talaia (contracte)** — el contracte fa servir **dues** claus per a la mateixa
  cosa (`nota:` i `caveat:`). El codi ja llegeix les dues, així que no urgeix; però unificar-ho
  al contracte estalviaria la propera esquerda d'aquesta família.
- **Handoff a: Mirador (UI)** — `Answer` porta camp nou `narration` (estat de la gàbia,
  intervencions, els dos veredictes) i `metric_b_key`. La UI no els necessita, però hi són per
  si la fitxa vol ensenyar que una resposta ha passat per la gàbia.
- Els pendents propis del geo-rag (banc de confirmació de Bea · ★ · paper) queden **fora**
  (E6), com mana l'spec.

**No fusiono** (Talaia és la guardiana). PR obert per a verificació adversarial.
