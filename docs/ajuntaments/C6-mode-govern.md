# C6 · Mode govern a `municipi/[slug]` — contracte de disseny

**De:** Talaia (owner) · **Data:** 2026-07-16 · **Font de veritat:** `docs/spec-ajuntaments-v1.md` §3-C6, amb les esmenes del §10 (E1 mana sobre C2 en tot el que toca al web)
**Ordre:** aquest contracte es fusiona **abans** de D4 (`mart_govern`, Sondeig) i D5 (vista, Mirador), que l'implementen. El vot narratiu de Bea és sobre la **vista D5** (com es veu), no sobre aquest contracte (què és vinculant).

> El mode govern **no és una vista privada**. És la mateixa fitxa pública de `municipi/[slug]`, amb una altra ordenació i un altre èmfasi. La fitxa que veu l'alcalde és, xifra per xifra, la que veu el veí i el periodista. Aquesta frase no és retòrica: és el criteri d'acceptació №1.

## 1. Què és (decisions tancades)

1. **Activació:** commutador visible a la fitxa, reflectit a la URL (`?vista=govern`), compartible i enllaçable. Cap autenticació, cap cookie de perfil, cap detecció de qui mira.
2. **Abast v1:** els 31 municipis del Berguedà. Fora del Berguedà, el mode no s'ofereix (la fitxa espina actual no canvia).
3. **Ordenació del mode govern (fixa, no configurable per l'ajuntament):** (1) pols del mes — atur registrat + indicadors interns publicables; (2) KPIs amb rang comarcal; (3) sèries temporals; (4) licitacions del municipi; (5) radar de subvencions — **només** post-porta (§4); (6) bloc de preguntes suggerides cap a `/pregunta-li`. La vista per defecte (veïnal) conserva l'ordre editorial actual de la fitxa.

## 2. Els KPIs (composició tancada)

**12 KPIs** (mínim 10 si una font falla; mai més de 14). Les claus canòniques són les de `semantic/metrics.yml` (C1 mana en el nom; aquesta llista fixa la composició):

| # | KPI | Origen | Naturalesa |
|---|---|---|---|
| 1 | Padró | Idescat (existent) | mesurada |
| 2 | Atur registrat (mensual) | C1 · Observatori del Treball | mesurada |
| 3 | RFDB | C1 · HERMES | mesurada (agregador) |
| 4 | Base imposable IRPF | C1 · HERMES | mesurada (agregador) |
| 5 | Habitatges iniciats | C1 · HERMES | mesurada (agregador) |
| 6 | Habitatges acabats | C1 · HERMES | mesurada (agregador) |
| 7 | Parc de vehicles | C1 · HERMES | mesurada (agregador) |
| 8 | Residus per càpita | existent | mesurada |
| 9 | Energia (ICAEN) | existent | mesurada |
| 10 | Places turístiques (RTC) | existent | mesurada |
| 11 | Pernocta estimada | existent | **estimació amb banda** |
| 12 | Indicador intern municipal | C2, `publicable: true` | mesurada (manual) |

- El KPI 12 mostra un «pendent de l'Ajuntament» genèric mentre no hi hagi cap indicador `publicable: true`; **mai** llista ni insinua què existeix en privat (E1: el web només coneix el que és publicable). Dades sintètiques només a la demo i marcades «demo» de manera visible (D6).
- La capa electoral 🔴 queda fora del mode govern, com de tota aquesta spec.

## 3. Doctrina del percentil (el punt crític d'aquest contracte)

**Un percentil és una afirmació d'ordre.** Afirmar «ets el 4t de 31» és afirmar 30 comparacions. La legitimitat d'aquesta afirmació depèn de la naturalesa de la dada, no del disseny de la pàgina:

1. **Mètriques mesurades** (padró, atur registrat, RFDB, IRPF, habitatges, vehicles, residus, energia, RTC, internes): el percentil comarcal és **legítim** i es publica. Representació canònica: **rang ordinal «k de n»** — amb n=31, el rang és el percentil honest; un «percentil 87» sobre 31 municipis seria cosmètica estadística.
2. **Empats** en mètrica mesurada: rang compartit explícit («7è–9è de 31, empatats»), mai desempat arbitrari.
3. **Municipis sense dada** d'una mètrica: fora del rànquing i el denominador es mostra real («k de 27 amb dada»), mai un 31 fictici.
4. **Direcció neutra:** el rang s'expressa sempre sobre el valor («3r valor més alt de 31»), mai com a judici («3r pitjor»). La lectura la fa el context i la metodologia, no el rang.
5. **Estimacions amb banda** (pernocta, i qualsevol futura): **NO es publica percentil ni rang si la banda del municipi se solapa amb la de cap altre dels 31** (candau `bandsOverlap`, `packages/web/src/lib/contract/distinguish.ts`). En comptes d'un rang fals es mostra: la **banda** sencera i la frase **«no distingible de N municipis de la comarca»** (N = municipis del Berguedà amb banda solapada). La col·lisió exacta (mateixa estimació i banda) manté l'advertiment ja existent de la fitxa (`collisionPeers`). Cas límit: si cap banda se solapa, el rang és legítim també per a l'estimació — la regla és el solapament, no la mena de mètrica.
6. **Un sol candau:** qualsevol ordenació per estimació passa per `bandsOverlap` — no es crea cap mecanisme paral·lel. El candau és el que ja hi ha; aquest contracte l'eleva de doctrina de fitxa a doctrina de mode.

## 4. On es calcula (frontera dura)

- Percentils i rangs de mètriques mesurades: a **transform** (`mart_govern`, D4), amb `rang`, `n_amb_dada` i data de càlcul com a columnes del mart. **Mai al front.** El front només formata.
- El recompte de no-distingibles de les estimacions: al client via `distinguish.ts` (JS pur sobre dades que ja hi viatgen — és el candau establert, no un càlcul de percentil).
- Criteri verificable: el codi de D5 no conté cap funció de rang ni de percentil; la revisió del PR ho comprova per grep i per test.

## 5. Sèries temporals, licitacions i radar

- **Sèries:** tot KPI amb ≥3 punts mostra la sèrie (mensual per a l'atur i les internes; anual per a la resta), reutilitzant components existents (KpiCard/MetricRow + el traç de sèrie que ja hi ha; cap llibreria nova sense right-sizing).
- **Licitacions:** secció que reutilitza dades i components de `/licitacions` filtrades per `ine5`. Res de nou pipeline.
- **Radar:** la secció **només existeix** quan el radar superi la porta del §4 de l'spec (banc C4 aprovat + mes de validació paral·lela + vistiplau de Bea). Fins llavors, **no es renderitza res** — ni «properament», ni feature flag visible. Verificable: cap string del radar al bundle públic abans de la porta.

## 6. Preguntes suggerides (bloc cap a `/pregunta-li`)

- **8 preguntes** (mínim 6 si el catàleg encara no les cobreix), versionades al repo com a contingut i18n ca/es, prefarcides a l'enllaç cap a `/pregunta-li`.
- **7 de dins del catàleg** del xat: cadascuna ha de tenir resposta traçada (font + fórmula) en el moment de publicar-la — mai suggerir una pregunta que provoqui un refús imprevist.
- **1 deliberadament d'abstenció honesta:** una pregunta la resposta correcta de la qual és «no ho puc distingir / no ho tinc», amb motiu. Ensenyar el silenci calibrat és part del producte, no un defecte.
- El contingut de les preguntes és jurisdicció de X3 (Brúixola/Mirador); aquest contracte en fixa el nombre, la composició i el criteri.

## 7. Política editorial (§1.2 de l'spec, escrita aquí i vinculant)

**Cap indicador es retira ni es suavitza perquè incomodi un ajuntament.** Si un número fa mal, s'explica — amb la seva banda quan en té i amb el context comarcal — però no s'amaga, no es reordena per enterrar-lo i no es reformula per estovar-lo. L'ordenació del mode govern és fixa per disseny (§1.3) precisament perquè no hi hagi «treu-me això de la fitxa». Això és condició de credibilitat davant la Diba, no un risc a gestionar.

## 8. i18n, accessibilitat i procedència

- i18n **ca/es** complet (paraglide, com la resta de la fitxa); el commutador i tot text nou, traduïts.
- **AA**: contrast, focus visible, semàntica aria del commutador i de les seccions; navegable per teclat.
- **Enllaç a metodologia per indicador** (glossari/contracte semàntic), punt de procedència (mesurada/inferència/manual) com a la fitxa actual.

### 8.1 · CADA XIFRA AMB LA SEVA FONT O FÓRMULA (regla de ferro, Bea 2026-07-18)

No n'hi ha prou amb el punt de color: **cada KPI del tauler mostra, a la mateixa targeta o a un sol toc/hover, el text de la seva procedència** —
- **mètrica MESURADA** → la seva **font** (organisme + data: «Idescat · 2025», «SEPE · 2026-06»);
- **mètrica INFERIDA/derivada** → la seva **fórmula** llegible (p. ex. «65+ / 0–14 × 100»), i la font de les entrades.

Res es codifica a la UI: **font, data i fórmula surten del contracte** (`semantic/metrics.yml`) via l'export (l'export emet `source`, `date` i, NOU, `formula`). Un KPI que no pot mostrar font O fórmula **no entra al tauler** — és la mateixa condició de credibilitat davant la Diba que la política editorial del §7. Criteri verificable: cap targeta de KPI sense línia de procedència; test que ho comprova a D5.

## 9. Dins / fora

- **Dins:** commutador + ordenació govern, 12 KPIs amb rang comarcal segons §3, sèries, licitacions filtrades, bloc de preguntes, política editorial, i18n/AA.
- **Fora:** sortida impresa (Llegenda, post-v1), butlletí mensual, cartell A4, radar abans de porta, qualsevol personalització per ajuntament més enllà del que fixa §1.3, capa electoral, qualsevol càlcul de rang al front.

## 10. Criteris d'acceptació (llistó de D4/D5 respecte d'aquest contracte)

1. La mateixa URL amb i sense `?vista=govern` mostra les **mateixes xifres** (test de paritat de dades).
2. `mart_govern` porta `rang`, `n_amb_dada` i data per a cada mètrica mesurada; cap rang calculat a D5.
3. La pernocta no mostra mai rang quan `bandsOverlap` és cert amb cap dels 31; mostra banda + «no distingible de N».
4. Empats i denominadors reals visibles tal com fixa §3.2–3.3.
5. i18n ca/es sense claus pendents; auditoria AA del commutador i seccions noves.
6. Cap secció ni string del radar al bundle abans de la porta del §4 de l'spec.
7. **CADA KPI mostra font (mesurada) o fórmula (inferida)** visible o a un toc (§8.1); test que verifica que cap targeta de KPI del mode govern queda sense línia de procedència.
