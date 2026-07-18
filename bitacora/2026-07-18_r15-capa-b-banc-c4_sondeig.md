# R1.5 · Composició de la CAPA B del banc C4 (classe positiva per construcció)

**Fecha:** 2026-07-18
**Autora:** Sondeig (dades/pipeline)
**Para:** Talaia (review/merge) i, quan fusioni, **Bea (etiquetatge A+B juntes)**
**Tema:** cerca dirigida a la BDNS per llista de programes (C4 §2 v2 + R-FUNC §2), 12 mesos enrere;
40 convocatòries reals arxivades SENSE cap pre-etiquetatge; segona taula al full d'etiquetatge.
**Status:** fet, verificat en viu · **CAP judici d'elegibilitat en cap punt** (la guarda mana)

## Contexto
Tasca #1 de la cua de Sondeig (`bitacora/next.md`): la capa B és el denominador del recall i
desbloqueja l'etiquetatge de Bea. Contracte vinculant: **C4 §2 v2** (guarda anti-pre-etiquetatge);
mapa de finançadors: **R-FUNC §2** (re-verificat en viu, vegeu sota). Dial: una tasca i parar.

## Què he fet
- **`packages/signals/tests/fixtures/bdns_capa_b.json`** — 40 convocatòries reals (captura literal
  `busqueda`+`detall`, com la capa A), ordenades per `codigoBDNS` ascendent (mecànic). `_meta` porta:
  les consultes LITERALS per programa (organisme/text/paràmetres), els recomptes, els retalls
  mecànics amb la regex escrita, els «no» del període, els solapaments, les crides API i l'avís
  legal de la font. **Cap camp `golden`/`semafor`/`motiu` enlloc.**
- **`docs/ajuntaments/banc-c4-etiquetatge.md`** — secció «CAPA B» nova amb la **segona taula
  (files 27–66)**, mateix format que la capa A (calibrat columna a columna contra les files reals
  de la #251), generada MECÀNICAMENT de la fixture. Les 3 columnes de la direcció, buides.
- **`packages/signals/tests/fixtures_bdns_capa_b.py`** — loader + `render_fila_taula()`: l'única
  font de veritat del format de la taula (generador i test la comparteixen).
- **`packages/signals/tests/test_capa_b.py`** — **16 tests, 100% offline**: guarda
  anti-pre-etiquetatge (cap camp de judici, columnes buides, ordre mecànic, recomptes
  fixture==_meta) · transcripció mecànica fixtures↔taula (patró `test_parafrasis`: cap fila del
  doc pot divergir) · **la trampa de noms** (vegeu sota) · dedupe inter-capes · finestra ·
  normalització C3 de les 40 · el conflicte registral `abierto=false`+termini futur present a B.

## La composició, consulta a consulta (recompte, no judici)
| Programa (consulta literal a `_meta`) | Arxivades |
|---|---|
| família IDAE (organos=1941; el subprograma «alumbrado» = 0 al període) | 16 |
| patrimoni històric (text «patrimonio historico», totes les paraules) | 7 |
| OSIC línies locals (organos=1174 + regex destinatari local − singulars registrals) | 7 |
| camins (Territori Gencat + «camins») | 2 |
| parcs naturals (Diba + «parques naturales») | 2 |
| digitalització (Presidència Gencat + «digital») | 2 |
| Catàleg Diba → Instrumental cooperació local | 1 |
| digitalització estat → ens locals (Transf. Digital/MPT + «entidades locales») | 1 |
| AOC (organos=1186) | 1 |
| Leader (DARP + «leader») | 1 |
| **Total** | **40** |

**Retall mecànic de l'OSIC, transparent i auditable:** el convocant sencer són **180** en 12 mesos.
La regex de destinatari local declarat AL TÍTOL (municipis, ens locals, biblioteques…) en matxa 37;
d'aquestes, **29 són concessions singulars a UN ens amb nom** («Subvención excluida de concurrencia
pública — Ajuntament de Tortosa»…), excloses per la MARCA REGISTRAL del títol (fet de la font, no
opinió d'encaix); de les 8 restants, la 918352 ja era a la capa A. La regex exacta és a `_meta` i
el test la vigila: si algú la canvia sense regenerar, cau.

## Verificación (àncores mesurades EN VIU, 2026-07-18)
- **La trampa del no-cascada també és a `organos`:** el node pare de la Diba (id=44) sol → **0**;
  amb els fills enumerats (44,720,3632,5939,3633,5279,4090,721) → **15** (gen–feb 2026). I els ids
  ARREL d'un ministeri no troben les convocatòries penjades de subnodes: Vivienda+Transportes per
  organos + «patrimonio historico» → **0**, tot i que la 873847 n'és (convoca la DG de Agenda
  Urbana y Arquitectura, un subnode). Consultes per text quan l'arbre no és fiable.
- **El filtre de text FUNCIONA i es va verificar comptant** (la lliçó de R1: els paràmetres
  desconeguts s'ignoren en silenci): baseline juny 2026 = 1.306; +«subvenciones» = 198;
  +«ajuts» = 65. `descripcionTipoBusqueda`: 0=frase, 1=totes, 2=alguna (llegit del JS de la SPA,
  confirmat comptant). **El matx «frase» NO és estricte**: «parques naturales» retorna també una
  convocatòria d'escoles bressol (871616) — s'arxiva igualment, la consulta mana.
- **Re-verificació del mapa R-FUNC §2:**
  - **Catàleg Diba:** NO publica les finestres com a convocatòries BDNS cercables (organos Diba +
    «catálogo»/«catàleg» = 0). La traça registral del règim és la «CONVOCATÒRIA INSTRUMENTAL 2026.
    ACCIÓ DE COOPERACIÓ LOCAL» (880353, arxivada). El «✅ via BDNS» del R-FUNC per a la Diba és
    cert per a les línies sectorials competitives, **no per als recursos del Catàleg** → l'anticipació
    de finestres (memòria de cicle, R7) puja d'importància.
  - **Leader/ADRCatCentral:** la conv. 2026 del DARP hi és (911751, fi 30/09/2026) — arxivada.
    ⚠️ Fet registral: porta `abierto=false` AMB termini futur (com 8/26 de la capa A): la doctrina
    C3 «abierto mana» té ara exemplars a les dues capes (amb test).
  - **PUOSC:** fora de la finestra i tancat (DOGC 11-02-2025) → memòria de cicle, com deia R-FUNC.
  - **1,5% cultural:** el programa VIU però ha CANVIAT de ministeri — la convocatòria del període
    és l'Orden de 09/12/2025 del **Ministerio de Vivienda y Agenda Urbana** (873847), no del de
    Transportes. El text «1,5% cultural» com a cerca = 0 (i «2% cultural» retorna 83 falsos matxos).
  - **Consell Comarcal del Berguedà** (organos=8292): **0 convocatòries BDNS al període** — el
    forat comarcal que R-FUNC §2 declara, ara re-verificat amb número.
- **Cerca educada:** **100 crides** a l'API en total (51 exploració/verificació + 49 descàrrega),
  pausa ≥1,2 s, User-Agent identificat, backoff del client de R1; cerca històrica feta UNA vegada.
  Els recomptes previs es van fer amb `pageSize=1` (comptar sense descarregar).
- **CI local:** `pytest packages/signals/tests` → **141 passed** (125 previs + 16 nous) ·
  `ruff check packages/signals` → All checks passed.

## Decisions preses (documentades, cap en silenci)
1. **Finestra = 12 mesos** (el màxim del rang 6–12 del contracte): capta la finestra ~gener del
   Catàleg, la conv. de desembre del patrimoni i el Leader. Mateixa finestra per a tots els programes.
2. **IDAE sencer** (16) en lloc de només «alumbrado» (=0): arxivar la família evita que un judici
   meu sobre «quines línies energètiques compten» decideixi la composició. El «no» de l'enllumenat
   queda escrit.
3. **Numeració 27–66** (contínua amb la capa A): una referència unívoca per fila del banc sencer.
4. **El camp `programa` a cada entrada** és la procedència de la CONSULTA (traçabilitat mecànica),
   no un judici. La taula del full NO el mostra (mateix format que la capa A, columnes idèntiques).
5. **Àmbit multiregió honest al render:** la 896067 llista 19 CCAA i `regiones[0]` sola diria
   «Galícia» — la fila mostra «ES11 - GALICIA (+18)». Mecànic, no interpretatiu.

## Pendiente / handoffs
- [ ] **Talaia:** review/merge. Dues coses de la teva jurisdicció:
  1. El full (`## Quan acabis`) encara diu «si el mix queda lluny del 8/8/4 previst pel C4,
     reescalo els llindars» — **la clàusula de reescalar està SUPRIMIDA a C4 §2 v2**; frase residual
     de v1 que no he tocat (prosa teva).
  2. La **918352** (OSIC arts escèniques municipals): la consulta de capa B la troba, però ja és la
     #3 de la capa A i no s'ha duplicat. Si C4 la vol al denominador B, és decisió teva de contracte.
- [ ] **Bea:** quan Talaia fusioni, el full té les DUES capes (66 files) — etiquetatge A+B juntes
  contra el criteri operatiu, i es congela TOT.
- [ ] **R2 (jo, si el dial ho permet):** hereta la trampa de noms amb test (Sant Salvador de
  Guardiola ≠ Guardiola de Berguedà: substring «guardiola» matxa tots dos; casar per nom complet
  normalitzat, mai per substring) i el fet `organos`-no-cascada per si mai filtra per convocant.
- **CAP judici d'elegibilitat meu en aquest lliurament** — ni a les fixtures, ni al full, ni aquí.

## Enlaces
- `packages/signals/tests/fixtures/bdns_capa_b.json` (les consultes literals viuen a `_meta`)
- `packages/signals/tests/fixtures_bdns_capa_b.py` · `packages/signals/tests/test_capa_b.py`
- `docs/ajuntaments/banc-c4-etiquetatge.md` (files 27–66) · `docs/ajuntaments/C4-avaluacio-radar.md` §2 v2
- `docs/ajuntaments/R-FUNC-radar.md` §2 (mapa re-verificat)

— Sondeig
