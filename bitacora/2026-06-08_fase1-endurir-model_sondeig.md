# Fase 1 — endurir el model SENSE fonts noves: tipologia + confianca_score + IETR dual — Sondeig

**Fecha:** 2026-06-08
**Autora:** Sondeig (dades/contracte/pipeline)
**Para:** Talaia (review/merge, gatekeeper del contracte) · Mirador (FYI: 4 columnes noves al JSON, encara NO exposades a la UI) · Brúixola (FYI: 4 mètriques noves al contracte, la IA ja les pot citar) · Cabal (FYI)
**Tema:** afegir 3 derivats a `mart_municipi` sobre dades que JA hi són (feedback de la consultora): una **tipologia** narrativa amb nom, un **confianca_score** 0-100 auditable, i l'**IETR dual** (stock/impact). Cap font nova.
**Status:** fet, verificat / handoff

## Contexto
La consultora demana endurir el model: que es **llegeixi** (no només números) i que **digui quan no se'n pot refiar**, sense afegir cap font. Tres derivats sobre senyals ja al mart (`gap_pernocta_pct`, `index_turisme`, `pct_noprincipal`, `poblacio`, `carrega_total_est`, `kg_hab_any`, `kwh_hab`, `vidre_hab`, `restauracio_per_1000hab`, `IETR`/`A_resid`/`B_turis`). Pilot Berguedà (31 munis). Mètode complet a **`docs/tipologia-municipal.md`**.

## Què he fet (3 derivats = 4 columnes)
1. **`tipologia`** (text) — classificador **basat en regles** sobre **z-scores comarcals** (`stddev_pop`; població i càrrega amb `ln` per l'asimetria). 6 arquetips amb nom + `indeterminat` quan és ambigu (honestedat, no es força). Llindars i regles documentats al doc. Label ca/es al contracte.
2. **`confianca_score`** (0-100) — **complementa**, no substitueix, la bandera `confianca`. Fórmula auditable: `40·mida_denominador(ln 75→410) + 35·concordança(1 − dispersió_z dels 3 senyals de presència / 3) + 15·cobertura(no-nuls/5) − 10·outlier(|z|>2)`, acotat [0,100]. Talls de l'etiqueta derivada: `<45 baixa · 45–65 mitjana · ≥65 alta`.
3. **IETR dual** — `IETR_stock` (= `A_resid`, component estructural/resident, 0-100) i `IETR_impact` (= `B_turis`, pressió realitzada, 0-100). Identitat garantida: `round(0.5·stock + 0.5·impact, 2) == IETR`.

## La tipologia dels 31 (verificat)
| Tipus | N | Municipis |
|---|---|---|
| capital_serveis | 6 | **Berga**, Gironella, Puig-reig, Avià, Bagà, Casserres |
| segona_residencia | 5 | Saldes, **Gósol**, Sagàs, Gisclareny, Sant Jaume de Frontanyà |
| excursio | 2 | **Castellar de n'Hug**, la Nou de Berguedà |
| buit_administratiu | 2 | Montclar, Fígols |
| dormitori_invisible | 1 | Sant Julià de Cerdanyola |
| **indeterminat** | **15** | Cercs, la Pobla de Lillet, Guardiola, Olvan, Montmajor, Borredà, Vilada, Vallcebre, l'Espunyola, Sta Maria de Merlès, Viver i Serrateix, Castellar del Riu, Capolat, Castell de l'Areny, la Quar |

**Ancoratges del brief — tots OK:** Berga=capital_serveis · Castellar=excursio · Gósol(+Saldes)=segona_residencia. La distinció excursio↔segona_residencia la fa el **gap de pernocta** (Castellar 31 % i residus/vidre alts = ve de dia; Gósol/Saldes 86-87 % = hi dormen). Els 15 `indeterminat` són territori mixt genuí (viles mitjanes, micromunicipis amb senyals contradictoris): es deixa honest, no es força.

## Nota d'honestedat: el score POT divergir de `confianca` (i és volgut)
**Castellar de n'Hug**: bandera `confianca='alta'` però `confianca_score=32,8` (baixa). Motiu: els senyals **divergeixen** (residus `z≈+1,1` però elèctric `z≈−0,4` per calefacció de llenya). El score-component de concordança ho **veu**; el binari no. Es publiquen els **dos** (l'etiqueta no es retira): el score és el costat honest de la tensió. Coincideixen en els casos clars (viles grans → score alt; micromunicipis → baix). Documentat al caveat del contracte.

## Materialització / regeneració (sense raw)
`data/raw/` és `.gitignore` → `dbt build` complet no és reproduïble en checkout net (igual que el PR del gap, 2026-06-07). La definició **canònica** viu a `mart_municipi.sql` (CTEs `sstats`/`zsig`/`zsig2`/`tipo`/`conf`). El parquet es regenera amb **`packages/transform/derive_fase1.py`**, que aplica **la mateixa SQL amb el mateix motor (DuckDB)** sobre el parquet ja materialitzat i **prova la identitat** IETR=0,5·stock+0,5·impact (re-deriva A_resid/B_turis amb la winsorització p5/p95 → diff exacte 0,0 abans d'arrodonir). Amb raw, `dbt build` dóna el mateix.

## Verificación
- `dbt parse` → net (template + schema vàlids).
- `python packages/transform/derive_fase1.py --check` → **verd** (parquet al dia, 4 derivats).
- `python packages/transform/verify_marts.py` → **verd** (IETR intacte: Castellar #1 89,4 / Berga #31 0,3; Spearman 0,869). Les 4 columnes són additives: cap valor preexistent canvia.
- `python tools/export_web_municipis.py --check` → **verd** (JSON al dia, 31 munis, **37 mètriques**).
- `pytest` (Brúixola, `packages/ai`) → **115 passed**. Inclou `test_provenance_fields_present_on_contract` (cada mètrica disponible té `formula` + `source`): les 4 noves el passen.
- `npm run check` (svelte-check) → **0 errors, 0 warnings** (998 fitxers). `npm run build` (adapter-static, prerender) → **OK**. Les 4 claus noves al JSON (fora del `MetricKey` de `types.ts`, que NO toco) **no** trenquen el type-check ni el build (el loader fa cast a `MunicipisDataset`; són additives).

## Pendiente / handoffs
- [ ] **Talaia:** review/merge (gatekeeper del contracte). `semantic/metrics.yml` ↔ `mart_municipi.sql` van aparellats. El brief deia "NO toquis la UI" → **no** he tocat `packages/web/src`: les 4 columnes són al JSON i al contracte, llestes per exposar.
- [ ] **Mirador:** quan toqui, exposar `tipologia` (categòrica, té caveat de LECTURA), `confianca_score` (0-100), `IETR_stock`/`IETR_impact` (0-100). `tipologia` necessitarà labels llegibles dels valors (ara són claus snake_case: `capital_serveis`…); valorar un petit diccionari de presentació o afegir-los al contracte si es vol i18n complet dels valors.
- [ ] **Brúixola (FYI):** la IA ja pot citar les 4 (catàleg les carrega; són `visibility: public`, no `planned`). El fixture offline `packages/ai/fixtures/mart_municipi.csv` NO té aquestes columnes → res a fer per als evals actuals.
- Futur (fora d'aquest PR): a escala Catalunya, **recalibrar els z-scores per comarca** (no un sol pool); els llindars de la tipologia estan calibrats sobre el Berguedà.

## Enlaces
- `docs/tipologia-municipal.md` (mètode: regles, llindars, fórmula del score, taula verificada, límits) — NOU
- `packages/transform/models/marts/mart_municipi.sql` (CTEs `sstats`/`zsig`/`zsig2`/`tipo`/`conf` + 4 columnes noves)
- `packages/transform/models/marts/_marts.yml` (descripcions + tests: `accepted_values` tipologia, `between` 0-100)
- `packages/transform/derive_fase1.py` (regenerador offline byte-fidel a la SQL) — NOU
- `semantic/metrics.yml` (4 mètriques: label ca/es, `definicio`, `formula`, `source: datapoble`, `categoria: derived`, `caveat`/`note`)
- `tools/export_web_municipis.py` (+4 claus a METRIC_KEYS/FORMAT_BY_KEY/COL_MUNI; `tipologia` a TEXT_COLS_MUNI) → `data/web/municipis.bergueda.json` (regenerat)
- `data/marts/mart_municipi.parquet` (regenerat: +4 columnes)
