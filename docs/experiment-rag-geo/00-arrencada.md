# Experiment · RAG geoespacial honest (Berguedà) — arrencada

**Estat:** arrencat 2026-07-01 · **Naturalesa:** experiment d'aprenentatge, no producte (si deixa de ser útil o divertit, es para i el que s'ha après queda) · **Àmbit:** Berguedà (31 municipis), terra ferma i estable.

La idea-força és la **cel·la buida** del brief de la Rapaz: el camp del RAG tracta el dubte de *recuperació* i el d'*al·lucinació*; gairebé ningú tracta el **dubte de la FONT** quan el número recuperat és ell mateix una **estimació amb σ coneguda i desigual** pel territori. Nosaltres ja tenim aquesta σ mesurada (la banda p10–p90). No s'hi afegeix RAG: es **connecta** la incertesa ja mesurada a un recuperador geoespacial. *«El RAG-UQ previ estima la incertesa del SISTEMA; nosaltres heretem la de la DADA.»*

## Veredicte del brief (verificat a la literatura, 2026-07-01)

| Afirmació | Veredicte | Matís |
|---|---|---|
| La «cel·la buida» (heretar σ de la font) és nova | ⚠️ amb asterisc (confiança **mitjana**, cerca només anglès) | El **mecanisme + avaluació** està buit i és defensable; el **concepte** ja està *anomenat* com a limitació oberta (Bayesian-RAG finances). Reclamar el mecanisme d'extrem a extrem, no el concepte. Distingir de RA-RAG «source reliability» (pes de credibilitat, no barra d'error). |
| Spatial-RAG: filtre dur primer | ✅ amb asterisc | Filtre-primer correcte; rànquing final real = Pareto multiobjectiu amb pesos dinàmics de l'LLM. Preprint arXiv 2502.18470. |
| RRF híbrid +15–25% | ⚠️ | RRF sòlid (Cormack 2009, `1/(60+rank)`). El +15–25% **varia** (+3%…+40% segons corpus). Reportar el *nostre* delta mesurat. |
| `S = μ − λ·σ` | ⚠️ | Real però **no nova**: mean-variance de Markowitz (1952). El nostre gir defensable: σ = **banda de fiabilitat real**, no variància introspectiva. |
| KPI = calibració de l'abstenció | ✅ **sòlid** | AbstentionBench (Meta/FAIR, arXiv 2506.09038) i RefusalBench (arXiv 2510.10390) reals. Recall/precision/F1 adoptables a N=30–50. |
| Postgres com a única peça | ⚠️ | Real i natiu a Postgres, però aquesta màquina no en té res i el repo va triar DuckDB (ADR-01). → decisió d'infra, sota. |
| Graphiti/GraphRAG «guanyen» al vector | ⚠️ | Bi-temporal és avantatge genuí; xifres *scoped*/auto-reportades. Fases 4–5, lluny del valor. |

**Correcció d'abast (auditoria):** el «99/342 (o /441) munis <1000 senyal» és de *tota Catalunya*, NO del Berguedà (31 munis en total: ~9 ≥1.000 amb ETCA = nucli validat; la resta <1.000, repartits senyal/soroll). El repartiment exacte del Berguedà es recalcula a la Fase 0.

## Decisions d'arrencada (Bea, 2026-07-01)

- **Infra — DuckDB-first.** Fases 0–3 (el ~70% del valor) sobre DuckDB (extensió `spatial` ja en ús al repo + `fts` + vectors), amb RRF compost en SQL. Zero servei nou, zero admin, honra l'**ADR-01** («el dato es pequeño; Postgres innecessari fora de concurrència d'escriptura»). Es construeix en un paquet **aïllat** (`packages/geo-rag`); NO es toca `packages/ai`.
  - **Trigger per «guanyar-se» Postgres:** només si una fase (4–5, graf/temporal) supera de debò el que DuckDB pot expressar, **o** si estar sobre l'stack canònic (PostGIS+pgvector) és part de la credibilitat de la peça publicada. En aquest punt: un sol `docker-compose.yml` + `psycopg3` + migració d'un ordre des dels Parquet. (BM25 real requeriria `pg_search`; el `tsvector` natiu no té IDF.)
- **Posicionament — a decidir més tard.** Es construeix ja com a capacitat/aprenentatge, mantenint el claim de novetat **ben acotat** (mecanisme+avaluació). Si algun dia es decideix publicar com a nota tècnica, ABANS es fa una segona recerca més profunda (incloent no-anglès i termes com *error-in-variables retrieval*, *noisy-label RAG*, *measurement-error-aware QA*).
- **Embeddings (call de Talaia, revisable):** model **local multilingüe** (sentence-transformers) per reproductibilitat, cost zero i CI offline, i un sol stack compartit amb el sub-experiment estrella (que necessita dropout local que cap API exposa). Si el pes local resulta massa a la màquina, alternativa: API (Voyage/OpenAI). Generació de text: Anthropic per defecte (ADR-06).

### Nota per a la Rapaz (desviació d'infra, per reenviar)

> Arrenquem sobre **DuckDB**, no Postgres, per una raó honesta: aquesta màquina no té ni Postgres ni Docker, i el repo ja va decidir DuckDB+Parquet (ADR-01) perquè la dada és petita (31→947 files) i DuckDB ja fa els *joins* espacials. Reproduïm íntegre el patró que demanes —filtre espacial dur primer, híbrid vector+full-text fusionat amb RRF— sense muntar cap servei. Ens **guanyem** el pas a PostGIS+pgvector si una fase el necessita de debò, o si estar sobre l'stack canònic és part de la peça que deixem online. Res es perd: la migració des dels Parquet és d'un ordre. Si prefereixes Postgres des del minut u per credibilitat, ho fem; només volíem no cremar dies de plumbing abans del primer aprenentatge.

## KPI · calibració de l'abstenció (banc petit fet a mà)

Banc de N≈30–50 preguntes territorials, cada una etiquetada `should_abstain ∈ {0,1}` (1 = la resposta correcta és «no ho sé / no em refio d'aquesta xifra»: muni soroll, premissa falsa, intenció infraespecificada, mètrica fora de cobertura). Es registra `acció ∈ {abstain, answer}` i, si respon, `correct ∈ {0,1}`. Classe positiva = `should_abstain`.

- **Titular:** `recall = TP/(TP+FN)` (el número de seguretat: un abstenir-se fallat = mentida confiada) · `precision = TP/(TP+FP)` (guarda contra abstenir-se de tot) · `F1`.
- **Cop d'ull:** `coverage = respostes/N` · `selective_accuracy = encerts/respostes`. Parell honest: `MRR = FN/(TP+FN) = 1−recall`, `FRR = FP/(FP+TN)`.
- **NO** ECE/AUROC/risk-coverage-AUC a aquesta N (bins buits, soroll). Etiquetatge humà (no LLM-jutge).
- **La hipòtesi, en aquesta mètrica:** abstenir-se guiat pel **registre/σ de la DADA** dona millor recall/F1 que abstenir-se guiat per la confiança introspectiva del model. *Aquesta comparació és el KPI.*

## Pla per fases (llistó + control adversarial)

- **Fase 0a — substrat (sense embeddings).** Paquet `packages/geo-rag`; build a DuckDB dels 31 munis des de fitxers ja al repo (geometria + `estimacio`/`rang_baix`/`rang_alt`/`σ` + registre + bessons + sèrie ICAEN), extensions `spatial`+`fts`, filtre espacial dur + cerca de noms, *smoke test* + *data card*. **Llistó:** 31/31 amb tots els camps, valors que tracen als fitxers font, test verd, `packages/ai` intacte, corre sense Docker. **Adversarial:** 3 munis a l'atzar (oficial/senyal/soroll) byte-match amb la font; repartiment del Berguedà recalculat; cap diff a `packages/ai`.
- **Fase 0b — semàntica.** Descripcions NL per muni + embeddings locals a DuckDB; cerca vectorial. Parada jugable del brief (cerca semàntica+exacta).
- **Fase 1 — recuperador espacial (híbrid+RRF).** Filtre dur → 3 llistes (distància `1/(1+d)`, cosinus, noms FTS) → RRF `1/(60+rank)`. **Llistó:** guany híbrid reportat com a **mesurat** (no el +15–25% manllevat).
- **Fase 2 — herència d'estatut.** Cada resposta hereta registre + banda; to per registre; `S=μ−λσ` amb crèdit a Markowitz. **Llistó:** cap muni soroll emet mai una xifra puntual sense el marge.
- **Fase 3 — abstenció honesta + KPI (el resultat).** Política d'abstenció + banc etiquetat + scorer → informe de calibració. **Porta:** aquest número s'entrega ABANS d'obrir 4–5.
- **Fase 4 (graf/bessó) i 5 (temporal ICAEN 2013–2024)** — **tancades** darrere la porta de la Fase 3.
- **★ Sub-experiment estrella** (la joia, genuïnament nou): σ real (ja al disc) vs σ d'embeddings (MC-Dropout, ~10 passades amb dropout) — quina prediu millor l'error sobre el banc de Fase 3. Reportar honestament encara que la σ real perdi o empatin.

## Fonts verificades (per a la peça honesta)

- Spatial-RAG — Yu et al. 2025, arXiv:2502.18470
- GeoAgentic-RAG — Liang et al. 2026, doi:10.1016/j.jag.2026.105195
- Bayesian RAG (S=μ−λσ, MC-Dropout) — Ngartera, Nadarajah, Koina, Frontiers in AI 2026 · risc-variància: Markowitz 1952; Sani et al., NeurIPS 2012
- RRF — Cormack, Clarke, Buettcher, SIGIR 2009
- AbstentionBench — Kirichenko et al. (Meta/FAIR) 2025, arXiv:2506.09038 · RefusalBench — Muhamed et al. 2025, arXiv:2510.10390
- GraphRAG — Edge et al. (Microsoft) 2024, arXiv:2404.16130 · Graphiti/Zep — Rasmussen et al. 2025, arXiv:2501.13956
- RA-RAG (source reliability, a distingir) — arXiv:2410.22954 · límits del RAG-UQ — arXiv:2505.07459
