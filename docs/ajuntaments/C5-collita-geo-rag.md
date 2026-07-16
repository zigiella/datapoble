# C5 · Collita del RAG-geo cap a producte (`packages/ai`)

**Estat:** contracte per fusionar ABANS del PR de collita (X1).
**Owner:** Talaia (doctrina) · implementa Brúixola (X1).
**Prerequisit:** ✅ complert — la passada oficial generativa està feta i reportada
(#232–#238: 3 passades declarades, FN=0 a totes; annex de re-validació).

---

## 1. Què es cull (dues peces, cap més)

**(i) Els estatuts i les regles de to.** La doctrina de lectura sencera: registres
oficial/senyal/soroll · bandes (el rang és la dada) · col·lisió (la xifra no específica) ·
empat (bandes solapades no s'ordenen) · fora-de-catàleg — amb els **dos silencis diferents**
(soroll: «tinc l'estimació i la desautoritzo amb motiu» ≠ catàleg: «no ho tinc») i la
**precedència** apresa a les tres versions del prompt (primer el tipus de consulta i el
veredicte de comparació, després el registre; la llista de catàleg s'enumera; els veïns es
responen).

**(ii) La gàbia.** Validació dura determinista (cap número a la resposta que no traci a una
cel·la del mart; agregats només si ja vénen comptats; talls marcats) + **validador cec**
(segon model, crida aïllada, context = pregunta+dades+resposta final, mai el raonament).

## 2. La lliçó de l'annex, VINCULANT (E3): la gàbia de producte re-valida

L'annex #238 va demostrar que la comptabilitat d'intervencions **sobreestima** (comptable
170/170 vs verificada 163/170). Per tant, a producte:

- La gàbia **re-valida el text final** (post-intervenció) amb el validador cec abans de
  servir-lo; una intervenció no es «considera» arreglada — **es comprova**.
- Si el text re-validat encara no compleix → **fallback honest al mode determinista**
  (text→SQL amb plantilles, que ja és traçable): el generatiu és un embelliment condicional,
  mai un risc.
- El validador que es cull és el **v2** (`validador-cec-v2-CONGELAT.md`: el fall de la
  comparació desnivellada corregit — amb `distinguishable: true` l'ordre és afirmable i el
  soroll obliga al caveat de la seva xifra, no a negar l'ordre).
- Pressupost: la re-validació és una crida Haiku extra per resposta generativa — dins del
  SpendGuard; si el sostre diari està exhaurit, fallback determinista (mai servir generatiu
  sense gàbia completa).

## 3. Les tres cases de la doctrina (font canònica declarada)

| Casa | Paper | Estat post-collita |
|---|---|---|
| `packages/geo-rag` | **annex de recerca** — l'experiment amb les seves actes literals | CONGELAT (cap canvi; el resultat es cita, no es reescriu) |
| `packages/web/src/lib/contract/distinguish.ts` | candau de UI (ordre/col·lisió al client) | viu, sense canvis |
| `packages/ai` | **casa de producte — FONT CANÒNICA en endavant** | rep la collita |

Qualsevol evolució futura de la doctrina es fa a `packages/ai` i es propaga cap a la UI;
el geo-rag no es reobre (les seves actes són història, no codi viu).

## 4. Adaptacions tècniques (les justes, cap més)

- La gàbia es **re-apunta** del substrat de l'experiment (`bergueda.duckdb`) als **marts**
  que `packages/ai` ja consumeix (warehouse.py, read-only, només `mart_*`).
- El patró existent de Brúixola es MANTÉ: el LLM mai escriu SQL (tria mètrica+intent d'enums;
  el Router construeix l'SQL). La capa generativa s'afegeix DARRERE d'aquest patró: primer la
  resposta determinista traçable, després (opcional, amb gàbia completa) la redacció fluida.
- **Pin d'`openai` alineat:** `packages/ai` mana (>=1.30); el ==2.44.0 del geo-rag era de
  l'experiment i no es propaga.
- La porta política (`politics.py`) queda INTACTA i mana per sobre de tot: cap resposta
  generativa sobre mètriques `dimension: politica`.
- Evals del xat: offline per defecte (fixtures; el CI mai crida APIs) — mateix patró que tot.

## 5. Definició de fet (X1)

- Doctrina i gàbia a `packages/ai` amb tests offline verds.
- Re-validació del text final implementada amb fallback determinista comprovat per test.
- `packages/geo-rag` sense canvis al PR (o només el segell «collit a X1» al README).
- Un eval de mostra end-to-end (pregunta → determinista → generatiu engabiat → re-validat)
  amb fixture, executable offline amb el backend Offline.
