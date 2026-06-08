# gap_pernocta_pct / gap_pct en % 0-100 (convenció única del contracte) — Sondeig

**Fecha:** 2026-06-07
**Autora:** Sondeig (dades/contracte/pipeline) · amb la meitat de frontend de Mirador (acoblada)
**Para:** Talaia (review/merge, gatekeeper del contracte) · Mirador (la seva meitat de `packages/web`) · Cabal (FYI convergència) · Brúixola (FYI IA)
**Tema:** els dos gaps de població es materialitzaven com a FRACCIÓ 0-1 tot i tenir `format: percent` (escala 0-100 al contracte). Ho corregeixo a l'arrel (mart + contracte) i trec el ×100 que el frontend hi posava a sobre.
**Status:** fet, verificat / handoff

## Contexto — el símptoma
`gap_pernocta_pct` i `gap_pct` sortien del mart com a fracció (`gap / poblacio`, p. ex.
Castellar 0,313) però amb `unit: "%"` i `format: percent`. La regla de format del contracte
(`packages/web/src/lib/format.ts`, `formatPercent`) tracta `percent` com a **escala 0-100**
(divideix per 100). Eren les ÚNIQUES dues mètriques `percent` sense `* 100` a la fórmula
(`pct_noprincipal`, `pct_indep`, `rtc_per_100hab_viv`… totes el porten).

Per compensar-ho, el frontend re-escalava els gaps amb **×100 a DOS llocs** (`classify.ts →
makeMetricFormatter`, per al mapa; i una còpia a `resum/+page.svelte → fmt()`). Funcionava a la
vista, però:
- trencava la disciplina **"cap component cuina números"** (×100 dispers, fràgil);
- qualsevol consumidor nou pel camí genèric (`formatMetric`) mostraria "0,3%" en lloc de "+31%";
- la incoherència és **AIGUA AMUNT** (el mart guarda fracció on el contracte espera 0-100), no
  al frontend.

## Decisió — opció 1 (arrel, no pedaç)
Fixar-ho a l'ORIGEN i deixar el frontend net:

1. **Pipeline** (`mart_municipi.sql`): `gap_pernocta_pct` i `gap_pct` ara `… / poblacio * 100`
   (round a 1 decimal), igual que `pct_noprincipal`.
2. **Contracte** (`semantic/metrics.yml`): fórmula amb `* 100` i caveat actualitzat (ja no
   "Fracció (0,12 = +12%)" → "Percentatge sobre el padró (+12 = +12%)"), ca + es. Tests
   (`_marts.yml`): descripcions al dia.
3. **Frontend** (Mirador, acoblat): tret el ×100 de `makeMetricFormatter` i de `resum/fmt()`. Es
   **CONSERVA el signe +/−** (la desviació es llegeix "+31 %", "−2 %"): el signe és presentació
   legítima; el ×100 era cuinar l'escala. `SIGNED_RATIO_PCT_KEYS` → `SIGNED_PCT_KEYS` (ja no són
   ràtios 0-1).
4. **Regeneració**: mart (transformació DuckDB equivalent — recomputo els 2 percentatges des dels
   enters `gap_pernocta`/`gap_abs`/`poblacio` que ja són al parquet, byte-fidel a la SQL nova; no
   hi ha `data/raw/` per a `dbt build`) + JSON (`export_web_municipis.py`, `--check` verd).

**Per què l'arrel i no el pedaç:** el contracte és la font única (el consumeixen pipeline + IA +
frontend). Deixar la fracció i només pedaçar el frontend mantindria la IA (Brúixola, text-to-SQL
sobre el mart) retornant 0-1. Amb l'arrel, mart + contracte + IA + web parlen tots 0-100. I treure
el ×100 i la SQL alhora és obligat: si només toqués les dades, el frontend faria **doble ×100**
("3 130 %") perquè ja compensava.

## Verificació
- `python tools/export_web_municipis.py --check` → **verd** (JSON al dia, 31 munis, 33 mètriques).
- `dbt parse` → net (template vàlid; `dbt build` no corre sense raw, documentat des del 2026-06-05).
- `npm run check` (svelte-check) → **0 errors, 0 warnings** (998 fitxers); cobreix el renombrament.
- `/resum` (fitxes «Dos extrems»): Castellar **+31 %**, Berga **−2 %** (abans 0,313 / -0,021).
  `pct_noprincipal` intacte (74,3 % / 24,2 %). Sense errors de consola.
- `/mapa` llegenda «Població invisible (%)»: rangs signats sensats (-17 % … +189 %), **no**
  inflats ×100.
- Valors: Castellar gap_pernocta_pct 0,313→31,3 · gap_pct 1,392→139,2 ; Berga -0,021→-2,1 ·
  0,119→11,9. La resta de columnes del mart, intactes.

## Pendiente / handoffs
- [ ] **Talaia:** review/merge (gatekeeper del contracte). El canvi de `semantic/metrics.yml` va
      aparellat amb el pipeline (han de coincidir).
- [ ] **Mirador:** la meitat de `packages/web` (`classify.ts` + `resum`) és la teva zona; revisa-la.
      L'he feta jo perquè el canvi de dades i el ×100 del frontend estan **ACOBLATS** (separar-los
      deixaria l'arbre amb doble ×100 i la verificació de /resum fallaria).
- [ ] **Cabal:** `convergencia.py` passa `gap_pernocta_pct` del mart a la columna
      `turisme_gap_pernocta_pct` (ara 0-100). Els SCORES/quadrants NO depenen del gap (usen
      `index_turisme`) → la lògica no canvia; però el parquet versionat
      `data/events/convergencia_bergueda.parquet` té la columna en l'escala vella. Regenera quan vagi bé.
- [ ] **Brúixola (FYI):** la IA consulta el mart real → els gaps ara surten 0-100 (més correcte). El
      fixture offline `packages/ai/fixtures/mart_municipi.csv` NO té columnes de gap → res a fer.
- Idea futura (fora d'aquest PR): elevar "percentatge amb signe" a un `format` del contracte (en
  lloc d'un set de claus al frontend), perquè el signe també vingui del contracte i no de Mirador.

## Enlaces
- `packages/transform/models/marts/mart_municipi.sql` (gap_pernocta_pct/gap_pct: `* 100`, round 1)
- `packages/transform/models/marts/_marts.yml` (descripcions dels tests al dia)
- `semantic/metrics.yml` (fórmula + caveat, ca/es)
- `tools/export_web_municipis.py` (comentari) → `data/web/municipis.bergueda.json` (regenerat)
- `data/marts/mart_municipi.parquet` (regenerat: 2 columnes)
- `packages/web/src/lib/map/classify.ts` (`SIGNED_PCT_KEYS`, `makeMetricFormatter` sense ×100)
- `packages/web/src/routes/resum/+page.svelte` (`fmt()` sense ×100)
