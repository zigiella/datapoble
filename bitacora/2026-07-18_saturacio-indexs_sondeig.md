# Saturació dels índexs compostos — anàlisi, declaració del límit i fix del rànquing

**Agent:** Sondeig (dades) · **Data:** 2026-07-18 · **Tasca:** #2 de la cua (handoff de Brúixola, X1)

X1 va destapar que 47 municipis empaten a `index_turisme=100` i 6 a `IETR=100`, i el xat ja
no menteix (detecta l'empat). Quedava la pregunta de dades: **per què saturen, i què fem —
recalibrar o declarar el límit?**

## 1 · Per què saturen (la causa, fórmula per fórmula)

### `index_turisme` — topall dur del clamp

Fórmula (mart_municipi.sql, CTE `tur`): z-score de `vidre_hab` **global sobre tot CAT**,
**clamp a [-2,+2]**, reescalat 0–100. El clamp és un topall dur: tot municipi amb z≥+2
col·lapsa exactament a 100.

Evidència (parquet 2024, 947 munis):
- `vidre_hab`: mitjana 34,9 · sd 20,8 · mediana 29,0 · **màx 149,4 → z=5,5** (cua dreta pesada).
- **47/947 (5,0%) exactament a 100**, abraçant `vidre_hab` de **76,8 a 149,4 kg/hab — el
  topall esborra diferències reals de 2×** (Gósol 149,4 «=» un muni de 76,8).
- Asimètric: el terra −2σ **no arriba a lligar mai** (mín observat: índex 8,1) perquè el
  senyal està fitat per sota i esbiaixat a la dreta. Satura NOMÉS al cim — just on un índex
  de pressió hauria d'informar.

### `IETR` — censura de la winsorització p5/p95

Fórmula (CTEs `q`/`norm`/`ietr`): 4 components min-max **winsoritzats p5/p95** sobre tot CAT
(0,5·A_resid + 0,5·B_turis). Cada component talla el ~5% alt a 100 i el ~5% baix a 0.

Evidència: **6 munis a IETR=100** (tots 4 components ≥p95 alhora) que amaguen un rang real de
**243,8 → 700,0 places RTC/1000 hab (2,9×)** — Naut Aran (700) «=» Urús (244); **8 a IETR=0**.
Components: `IETR_stock` 36 a 100 / 21 a 0 · `IETR_impact` 28 a 100 / 48 a 0.

**Totes dues saturacions són per construcció** (el clamp/winsor hi és perquè un outlier no
comprimeixi la resta d'escala): el preu és que **cap dels dos índexs ordena al cim**.

## 2 · Recalibrar o declarar? — alternatives provades amb dades

| Alternativa | Resultat empíric | Veredicte |
|---|---|---|
| z sobre `ln(vidre_hab)` (mateixa forma, escala log) | **34 munis seguirien >+2σ** (8 per sota de −2σ) | no arregla, només disfressa |
| treure el clamp | el màxim (z=5,5) comprimeix tota l'escala | és la raó de ser del clamp |
| rang percentil 0–100 | discrimina pertot | **traeix la definició** (z-score, distàncies, «50=mitjana») i repinta 947 valors publicats d'un indicador ja fora del tauler |

Conclusió: **no hi ha fórmula que discrimini al cim sense trair la definició** — una escala
fitada 0–100 amb input no fitat i esbiaixat censura en algun punt per força. I l'ecosistema
ja tracta l'empat com a senyal honest (X1): repintar valors desfaria aquella feina.

## 3 · Decisió

**a) `index_turisme` → DECLARAR EL LÍMIT + PROPOSTA DE DEPRECACIÓ (vot pendent).**
És una re-escala **amb pèrdua** d'una sola variable ja publicada (`vidre_hab`, entrada pròpia
del contracte): no afegeix informació i censura el cim. Ja és fora del tauler de govern (vot
de Bea 2026-07-16, substituït per energia/hab). La proposta de retirada queda escrita al
contracte (comentari YAML sobre l'entrada) i aquí; **la decisió és de Talaia/Bea**. Mentre
l'entrada visqui, el caveat declara la saturació.

**b) `IETR` → DECLARAR EL LÍMIT (l'índex es queda).** És una síntesi genuïna (4 senyals,
2 eixos) amb validació externa que aguanta (Spearman IETR↔residus, verify_marts al CI) i
saturació suau al cim (6/947 = 0,6%). El caveat declara la censura p5/p95 i que 0/100 són
terra/sostre compartits.

**c) FIX DE DADES: `IETR_rank` deia una mentida — arreglada.** El `row_number()` repartia
les posicions 1..6 entre els 6 empatats a 100 **per ordre de codi INE** (Llançà «guanyava»
Naut Aran perquè 17092<25025) — ordre fantasma a la capa de dades, la mateixa espècie de
mentida que X1 va treure del xat. Afectava **134 municipis en 61 grups d'empat** per tota la
distribució (73 ranks canvien). Ara: `rank() over (order by round(IETR,2) desc)` — **els
empats comparteixen posició** (els 6 del sostre són tots 1r; el següent, 7è) i es rankeja a
la **precisió publicada** (2 decimals): el que el lector veu igual, el rank no ho distingeix.
El test `unique` d'`IETR_rank` a `_marts.yml` s'ha retirat: la unicitat era l'artefacte del
desempat arbitrari, no una propietat de la dada.

## 4 · Canvis

- `packages/transform/models/marts/mart_municipi.sql` — límits declarats a les CTEs `tur` i
  `q`/`norm`/`ietr`; `IETR_rank` row_number→rank (comentari amb el perquè).
- `packages/transform/derive_fase1.py` — el mirall offline re-deriva també `IETR_rank`
  (pandas `rank(method="min")` == `rank()` SQL) i el `--check` del CI el vigila.
- `packages/transform/models/marts/_marts.yml` — descripcions al dia (escala CAT, no «31
  munis»; fora els ancoratges Castellar #1/Berga #31 que verify_marts ja havia retirat);
  `IETR_rank` sense `unique`.
- `semantic/metrics.yml` — **la declaració al contracte**: `index_turisme` (z GLOBAL de CAT,
  no «comarcal» — mentida heretada de F2 que ningú havia actualitzat; saturació al cim amb
  el número: 47 munis al sostre el 2024; «per ordenar, vidre_hab»; proposta de deprecació en
  comentari), `IETR` (censura p5/p95, 0/100 compartits, empats comparteixen posició),
  `IETR_rank` (semàntica rank + caveat), `IETR_stock`/`IETR_impact` («relatiu a la comarca»
  → distribució catalana + saturació pròpia: 36/28 al sostre).
- Regenerats: `data/marts/mart_municipi.parquet` (només columna IETR_rank),
  `data/web/municipis.catalunya.json` + `municipis.bergueda.json` (ranks + textos del
  contracte). Al Berguedà només es mouen Sagàs (110→109) i Vilada (398→397); les lectures
  (`lectures.bergueda.json`) citen `IETR_rank` només com a CLAU d'evidència, mai el número
  en prosa — verificat, cap regeneració necessària.

## 5 · Verificació (tot en local, offline)

ruff verd · verify_marts verd (Spearman 0,485 > 0,4; invariant IETR=0,5·stock+0,5·impact) ·
`derive_fase1.py --check` verd (ara vigila el rank) · bateria completa de `--check` del CI
verda (etca, tipus, calibració, pernocta, discrepància, sub1000, licitacions, export web
catalunya+bergueda) · suite signals 141 passed · YAML parseja (metrics + _marts).
Post-fix verificat al parquet: 6 munis IETR=100 tots amb rank 1, següent rank 7; 874 ranks
distints = 874 valors IETR distints.

## 6 · Troballes fora d'abast (rastre, no acció)

- **`tools/export_bergueda_bundle.py` ha derivat**: promet «els 31 municipis» però llegeix el
  mart sencer → regenerar-lo avui escriu **947 munis** a `bergueda_*` (i el committejat és
  pre-F2, amb IETR a escala comarcal). No és CI-gated. Ho he regenerat i **revertit** per no
  barrejar; necessita decisió pròpia (filtre Berguedà o rebateig a bundle CAT).
- La fitxa web (`MunicipiCard`) mostra «posició N de 947» — amb ranks compartits el render
  segueix sent correcte (dos munis poden dir «109 de 947»); cap acció de Mirador necessària,
  només FYI.

**Handoff a: Talaia/Bea** — vot sobre la proposta de deprecació d'`index_turisme` (§3a).
