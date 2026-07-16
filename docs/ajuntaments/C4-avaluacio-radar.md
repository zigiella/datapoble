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

## 2. El banc (composició congelada abans de cap sortida)

- **20 convocatòries reals arxivades** (BDNS + CIDO, període 2025–2026), guardades com a
  fixtures literals al repo (el CI les consumeix offline).
- Mix: **8 elegibles clares** per al perfil de la Pobla · **8 descartables clares** ·
  **4 casos frontera** (elegibles-però-dubtoses o descartables-però-atractives).
- **Idioma segons la font real:** la BDNS publica majoritàriament en castellà — el banc manté
  la distribució real (≈2/3 [es], ≈1/3 [ca] via CIDO), no la llengua còmoda del desenvolupador.
- **Criteri d'etiquetatge ESCRIT ABANS d'etiquetar:** Bea rep una pàgina amb la definició
  operativa d'«elegible» (beneficiari municipal vàlid + àmbit territorial que inclou la Pobla +
  matèria dins del perfil + termini obert en la data de referència) i etiqueta CONTRA el
  criteri, no d'intuïció. El criteri es congela amb el banc.
- Cada entrada del banc: la fitxa normalitzada C3 + `golden: elegible|descartable` +
  `motiu_daurat` (una línia de Bea) + per a les elegibles, `semafor_esperat: verd|groc`.
- **Congelació:** data + commit al doc; després de veure QUALSEVOL sortida del sistema, el
  banc no es toca. Guarda mecànica: test que verifica que el JSON del banc coincideix amb el
  doc congelat (mateix patró que `test_parafrasis.py`).

## 3. Els nivells, DINS del contracte (no a la mesura d'èxit)

Congelats aquí, abans de cap run:

| Nivell | Condició (sobre el banc de 20) |
|---|---|
| **HONEST** | recall d'elegibles = **12/12** (les 8 clares + les 4 frontera etiquetades elegibles… el denominador exacte surt de les etiquetes de Bea) **i** FP ≤ 3 dels 8 descartables |
| **DECEBEDOR** | recall ≥ 10/12 amb cap FN d'elegible CLARA (els FN frontera es toleren, es documenten) |
| **NO FUNCIONA** | qualsevol FN d'una elegible clara |

*(Si les etiquetes finals de Bea canvien el repartiment 8/8/4, els llindars es reescalen a la
mateixa proporció ABANS de la primera passada — mai després.)*

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

El report oficial del banc es versiona (`data/` del paquet que R2/R3 decideixin) amb: 2×2 +
recall + nivell + per-convocatòria (id, daurada, sortida del pipeline amb el punt exacte de
decisió — filtre o semàfor — i motiu) + cost + provenance. Mateix estàndard d'acta que el
geo-rag: el número es reporta tal com surt.
