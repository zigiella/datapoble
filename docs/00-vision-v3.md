# riusdegent — Visió v3 (document constitucional)

**riusdegent · Dades per entendre com s'habita el territori**

> Persones que arriben, marxen, tornen, pernocten, lloguen, compren, hereten, visiten, treballen, voten, ocupen places, omplen segones residències o desapareixen del padró real de la vida quotidiana.

**Estat:** constitució v3 — **supersedeix** l'spec V0.1 (`docs/00-project-spec.md`, preservada com a evidència històrica; no s'esborra).
**Autora:** Talaia · **Decideix la narrativa:** Bea. · **Llengua de treball: català** (a partir d'ara).

---

## 0. El gir
De *"observatori de pressió turística-residencial"* a **observatori de com s'habita el territori**. No és cosmètic: passa del focus en la *pressió* (alarmista, parcial) a la *habitança* (humana, completa — presència **i** absència, flux **i** estoc, els que vénen i els que desapareixen). El nom ho diu: **rius de gent**, el cabal humà que travessa i omple (o buida) cada municipi. L'IETR deixa de ser *el punt* per ser *un indicador* dins d'un observatori més ample.

## 1. La tesi / el nord
**El gap entre el padró oficial i la habitança real.** Fer visible la **població invisible**: els que **no consten però omplen** el territori (excursionistes, segona residència, estacionals) i els que **consten però ja no hi viuen** la vida quotidiana (despoblació, padró fantasma). Aquest gap és el relat que ningú més té — i ja en tenim els proxies per mesurar-lo.

## 2. Els dos pilars

### Pilar 1 — Capes d'habitança (dades estructurades: estoc + flux)
*La forma del riu.* Marts reproduïbles per municipi: vivenda (buit/segona residència), turisme (flux reglat i observat), exposició (IETR, validat r=0,87), política (qui vota), edat (qui envelleix / qui és jove i marxa).
- **Indicador estrella: "població real estimada" vs padró** (proxies: residus = fantasmes, IMD, tren, museu). Un número i un mapa propis.
- **"Rius de gent": el pols estacional** — qui entra i surt de cada municipi al llarg de l'any.

### Pilar 2 — El cabal (intel·ligència territorial des dels rastres)
*El cabal del riu:* el corrent d'activitat en temps real, mesurat pels **rastres** que el territori deixa quan un fenomen no té dataset net. *(El principi dels kg de residus, generalitzat: llegir el "tub d'escapament" administratiu i digital.)*
- **Motor: taula d'esdeveniments + convergència.** Tot (un plec, un tall de trànsit, una notícia, un decret de sequera) → esdeveniment *tipat, datat, geolocalitzat* (`ine5`). La intel·ligència és la **convergència**: senyals independents que coincideixen en municipi+finestra = confiança (el mateix principi que va validar l'IETR contra els residus).
- **Or: licitacions i pressupostos com a indicador *avançat*.** El que un ajuntament contracta revela el que espera. Semi-estructurat, datat, geolocalitzable.
- **Cicle de vida del fenomen:** anticipació (licitacions) → realització (agendes, talls, reforços) → reacció (ordenances, taxes, notícies de queixes).
- **Catàleg de proxies** (receptari: *fenomen → rastre → font → caveat*).
- **Extracció amb LLM ancorada** (via OpenRouter): de text messy a esdeveniment tipat, **citant sempre el fragment font**; si no pot, rebutja. **Dada vs inferència** explícit.
- **Fonts, per ordre de senyal/soroll:** contractació pública + BOPB/DOGC (incl. sequera) primer; agendes, webs i notícies després.
- **Right-sizing:** 2-3 fonts d'alta senyal sobre els 2 pilots + comarca; *després* eixamplar. Legal: butlletins i contractació són reutilitzables per disseny; webs/notícies → robots/ToS, fet+enllaç (no còpia), sense dades personals.

## 3. Principis (reafirmats)
Right-sizing · reproductibilitat · **traçabilitat** (cap número sense font·data·fórmula; dada vs inferència) · disseny com a producte · **honestedat inclosos els "no"** · privacitat (lectura ecològica, no individual) · accessibilitat · obert.

## 4. Què ja tenim (balanç)
Repo viu + equip de 4 agents. **F0 i F1 integrats** (7 PRs): sistema de disseny, pipeline reproduïble amb IETR validat + mart electoral, IA text→SQL traçable, frontend SvelteKit i18n ca/es. Recerca: l'auge de l'extrema dreta a Catalunya mapejat (951 munis) + **tres "no" honestos** (ni edat municipal, ni immigració, ni mida l'expliquen → és geogràfic, el fenomen Aliança) + l'angle del **vot jove** (capa d'enquesta, CEO).

## 5. Arquitectura
Els dos pilars sobre el mateix stack.
- **Pilar 1:** connectors → dbt + DuckDB → marts (clau `ine5`).
- **Pilar 2:** harvest → esquema d'esdeveniment → **extracció LLM (OpenRouter)** → **events table (clau `ine5`)**.
- La events table fa **join** amb els marts: el mateix municipi vist com a *forma* (estoc) i com a *cabal* (senyals).
- Sortides: artefactes estàtics + API IA. Frontend: SvelteKit + MapLibre, scrollytelling, i18n ca/es (en/fr).

## 6. Equip
Talaia (coord + recerca) · Sondeig (dades) · **Cabal** *(nova: senyals/rastres)* · Brúixola (IA) · Mirador (frontend) · Llegenda (art + identitat `riusdegent`). Bea: vet narratiu.

## 7. Full de ruta cap al llançament
- **F2 · Identitat + dades reals:** identitat `riusdegent` (Llegenda) · Mirador amb tokens + marts reals · escala Catalunya (Sondeig).
- **F3 · Cabal (pilar 2):** primer experiment (licitacions com a anticipació, 2 pilots) → events table → convergència.
- **F4 · Indicador estrella:** "població real vs padró" + el pols estacional.
- **F5 · IA en viu** (OpenRouter) + scrollytelling.
- **F6 · Llançament públic** (Cloudflare + domini `riusdegent.cat`).

## 8. Primers encàrrecs
1. **Llegenda:** identitat `riusdegent` (logo, favicon, guia) sobre els tokens ja definits.
2. **Cabal (nova) / Sondeig:** experiment *"licitacions com a anticipació"* — contractació pública de Castellar/Berga + Berguedà, classificada per tema (neteja, aigua, aparcament, turisme, residus, seguretat), buscant la *petjada de despesa* estacional. El "kg de residus" del pilar 2.
3. **Talaia:** l'indicador *"població real vs padró"* amb els proxies que ja tenim.

---
*Supersedeix `docs/00-project-spec.md` (V0.1). Aquest document és el contracte del qual pengen els encàrrecs. Canvis → bitàcola + PR.*
