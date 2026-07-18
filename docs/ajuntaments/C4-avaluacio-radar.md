# C4 · Avaluació del radar de subvencions — el número que ven la demo

**Estat:** contracte per fusionar ABANS de cap codi del track R que produeixi sortides puntuables.
**Owner:** Talaia (doctrina i verificació) · **etiquetes daurades:** Bea, a mà, MAI un model.
**Hereta:** la doctrina de banc del geo-rag (contractes 06/07/10) **amb les lliçons apreses**
(§10-E2 de l'spec): el que va costar tres passades d'aprendre allà, aquí entra de sèrie.

---

## 1. Què mesura aquest banc (i què no)

El número de la demo és el **recall d'elegibles del PIPELINE SENCER**: BDNS/CIDO → filtre dur
(R2) → semàfor (R3). **No** és el recall del classificador sol: una convocatòria elegible
clara que el filtre dur mata abans que el classificador la vegi és un **FN greu del sistema**,
encara que Haiku no l'hagi vist mai. El banc puntua l'extrem a extrem.

Els dos errors, amb nom (la 2×2 del geo-rag):
- **FN — deixar passar una elegible** (el radar calla quan tocava avisar): **el pecat greu.**
  Un ajuntament que confia en el radar i perd una convocatòria per culpa nostra és el pitjor
  resultat possible del producte.
- **FP — avisar d'una no-elegible** (soroll a la safata): el pecat **prudent**. Cansa, però
  no fa perdre res. Es mesura i es reporta, amb llindar més tou.

## 2. El banc — DUES CAPES (v2, 2026-07-18: objecció de Marea ACCEPTADA, ratificada per Bea)

**Per què v2:** la v1 d'aquest contracte manava un mix 8/8/4 però el full d'etiquetatge (#251) va
deixar que les candidates sortissin del flux cru d'un dia de BDNS — i el recompte de Marea sobre les
26 va donar **0 elegibles clares** (el feed diari és 90–95% soroll trivial: nominatives, persones
físiques, convocatòries d'altres ajuntaments per als seus veïns). Un recall sobre denominador ≈0 és
un titular buit («detector d'incendis avaluat 26 dies sense cap incendi»), i la clàusula de reescalar
era el símptoma, no la solució: **reescalar no crea elegibles**. L'error era del full, no del
contracte: el banc del geo-rag (06/07) es va COMPOSAR, no mostrejar — aquesta v2 hi torna.

- **Capa A — el flux cru (26 convocatòries reals d'un dia, les de R1, tal qual).** La seva virtut és
  NO estar triada a dit: mesura el **FP-rate del pipeline i el filtre dur** sobre la distribució
  real que el radar veurà cada matí, i la **taxa de descartades-amb-motiu-erroni**. Inclou els
  paranys de nom reals (#9–10 «Sant Salvador de Guardiola» és del BAGES — test obligat del filtre).
  **Cap titular de recall surt d'aquesta capa.**
- **Capa B — la classe positiva, COMPOSADA (el denominador del recall i el número de la demo).**
  Cerca dirigida a BDNS/CIDO **6–12 mesos enrere** per obtenir **8 elegibles clares + 4–6 fronteres
  reals** del perfil de la Pobla. **Guarda anti-pre-etiquetatge (vinculant):** la cerca es defineix
  per LLISTA DE PROGRAMES/FINANÇADORS (R-FUNC §2: Catàleg Diba, OSIC, Leader/ADRCatCentral,
  IDAE/enllumenat, patrimoni, camins…), i s'arxiven **TOTES les convocatòries d'aquests programes
  del període** — no una selecció per «sembla elegible». Qui compon (Sondeig, tasca R1.5) llista
  programes i arxiva; **qui etiqueta és NOMÉS Bea**, sobre el conjunt sencer A+B. Així la composició
  garanteix que la classe positiva EXISTEIX sense que cap agent pre-etiqueti res.
- Les convocatòries de capa B poden tenir `estat: tancada` (són de mesos enrere): el banc avalua el
  JUDICI del pipeline (elegibilitat/semàfor), no la vigència — la data de referència de cada fitxa
  és la seva `data_publicacio`, i el filtre de termini s'avalua contra aquella data, no contra avui.
- **Solapament A∩B (decisió tancada):** si una convocatòria del flux cru (A) també la troba la
  consulta de programes (B), s'etiqueta UNA sola vegada; l'etiqueta compta al denominador B (si és
  elegible/frontera) i al FP-rate d'A alhora. Mai doble etiquetatge, mai doble recompte dins d'una
  mateixa mètrica.
- **Idioma segons la font real:** la BDNS publica majoritàriament en castellà — el banc (les dues
  capes) manté la distribució real, no la llengua còmoda del desenvolupador.
- **Criteri d'etiquetatge ESCRIT ABANS d'etiquetar:** Bea rep una pàgina amb la definició
  operativa d'«elegible» (beneficiari municipal vàlid + àmbit territorial que inclou la Pobla +
  matèria dins del perfil + termini obert en la data de referència) i etiqueta CONTRA el
  criteri, no d'intuïció. El criteri es congela amb el banc.
- Cada entrada del banc: la fitxa normalitzada C3 + `golden: elegible|descartable` +
  `motiu_daurat` (una línia de Bea) + per a les elegibles, `semafor_esperat: verd|groc`.
- **Congelació:** data + commit al doc; després de veure QUALSEVOL sortida del sistema, el
  banc no es toca. Guarda mecànica: test que verifica que el JSON del banc coincideix amb el
  doc congelat (mateix patró que `test_parafrasis.py`).

## 3. Els nivells, DINS del contracte (no a la mesura d'èxit) — sobre la CAPA B

Congelats aquí, abans de cap run. **El recall i els nivells s'apliquen NOMÉS a la capa B** (la
classe positiva composada); la capa A reporta FP-rate i descartades-amb-motiu, sense nivell.

| Nivell | Condició (sobre la capa B) |
|---|---|
| **HONEST** | recall = **totes les elegibles de B detectades** (clares + fronteres que Bea etiqueti elegibles) **i, a la capa A,** FP ≤ 3 |
| **DECEBEDOR** | cap FN d'elegible CLARA de B (els FN de frontera es toleren i es documenten un a un) |
| **NO FUNCIONA** | qualsevol FN d'una elegible clara de B |

*(El denominador exacte surt de les etiquetes de Bea sobre B; si la composició no arriba a 8 clares
reals, es reporta el denominador tal com sigui — mai s'infla amb fronteres reetiquetades. La clàusula
de reescalar de la v1 queda SUPRIMIDA: la composició B és la solució, no el reescalat.)*

A més del 2×2: **taxa de descartades-amb-motiu-erroni** (una descartada correcta amb motiu
equivocat és un defecte de transparència, no d'acció) — es reporta, sense nivell.

## 4. El banc mesura, no entrena (també el filtre)

- **Dev set separat** per desenvolupar TANT el filtre dur (R2) com el prompt del semàfor (R3):
  convocatòries reals DIFERENTS de les 20 del banc, triades per Talaia, mai al report oficial.
- El prompt del classificador és sistema: es versiona, i la passada oficial **es nega a córrer**
  si el fitxer del prompt no porta `CONGELAT` al nom (guarda heretada de `generativa.py`).
- **Si hi ha més d'una passada oficial al banc, TOTES es declaren** al report (la lliçó de les
  tres passades del geo-rag), i a partir de la segona, el resultat només és titular amb un
  **banc de confirmació fresc** (5–8 convocatòries noves etiquetades per Bea, una sola passada).
- Config de la crida (R3): Haiku via OpenRouter, `temperature=0`, proveïdor fixat Anthropic,
  provenance per crida (id + model + proveïdor servit), SpendGuard amb sostre diari.

## 5. La validació paral·lela (el mes)

Un mes natural amb el radar corrent en paral·lel al mètode manual (Bea/consulta directa):
- **Denominador definit ABANS:** totes les convocatòries del període que el mètode manual
  identifiqui com a elegibles per a la Pobla (no les que el radar trobi — seria circular).
- Es reporta: recall del mes **tal com surti**, FP/setmana, i les descartades-amb-motiu al
  correu (auditables una a una).
- Objectiu del §9 de l'spec (recall ≥ 0,9) **avaluat contra aquest mes**, no contra el banc.

## 6. Portes (recordatori vinculant)

Cap sortida pública del radar (anunci, JSON públic, perfil nou actiu) abans de: banc C4
aprovat al nivell HONEST o DECEBEDOR-documentat + mes de validació reportat + vistiplau
narratiu de Bea. Els correus del període experimental van NOMÉS a Bea.

## 7. Traçabilitat del report

El report oficial del banc es versiona (`data/` del paquet que R2/R3 decideixin) amb: 2×2 de la
capa B + recall + nivell · FP-rate i descartades-amb-motiu de la capa A · **dies de marge** de cada
elegible detectada en la seva data de referència (mètrica d'utilitat del R-FUNC §8: l'objectiu ≥30
dies es reporta, sense nivell) · per-convocatòria (id, daurada, capa, sortida del pipeline amb el
punt exacte de decisió — filtre o semàfor — i motiu) + cost + provenance. Mateix estàndard d'acta
que el geo-rag: el número es reporta tal com surt.
