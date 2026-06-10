# Fix: denominador funcional inclou el padró + corregeix la nota de l'IETR

**Fecha:** 2026-06-10
**Autora:** Sondeig (dades/contracte)
**Para:** Talaia (review/merge, gatekeeper del contracte) · Mirador (FYI: `carrega_funcional_est` de Puig-reig canvia 4343→4558 al JSON; valor additiu) · Brúixola (FYI: nota/definició de l'IETR corregides al contracte)
**Tema:** dos bugs de correcció detectats pel triatge del `vuelta-tuerca`.
**Status:** fet, verificat / handoff

## Contexto
El triatge (workflow de Talaia, 2026-06-10) va trobar dos bugs vius a `main`:
1. **Denominador funcional sense el padró.** `carrega_funcional_est = greatest(L1_pernocta, L2_residus)` **no** incloïa el padró → 1/31 munis (Puig-reig, 08175) tenia `carrega_funcional_est=4343 < padró=4558`. Un «denominador per governar» **per sota dels residents registrats** és defectuós (la consultora el defineix com `max(padró, L1, L2)`).
2. **Nota del contracte de l'IETR falsa.** `metrics.yml` deia «És exposició estructural (stock), no pressió realitzada» — però `IETR = 0,5·stock + 0,5·impact`. És l'exemple exacte de la consultora; risc que la IA el citi malament. A més afirmava «robust a pesos (Spearman>0,97)» sense verificar.

## Què he fet
1. Afegit `poblacio` (padró) al `greatest()` als **dos llocs sincronitzats**: `mart_municipi.sql` (model canònic) i `derive_fase1.py` (mirall offline que regenera el parquet). Ara `carrega_funcional_est = max(padró, L1, L2)` → mai per sota del padró.
2. Actualitzat el contracte (`metrics.yml`): `formula`, `definicio` i `caveat` de `carrega_funcional_est`.
3. Corregida la nota i la definició de l'**IETR**: ara diu que és una **SÍNTESI** (0,5·stock + 0,5·impact), no només stock; remet a `IETR_stock`/`IETR_impact` per al desglossament. Tret el claim no verificat «Spearman>0,97 robust a pesos» (honest boundaries; el test de robustesa a pesos queda com a pendent del triatge).
4. Regenerat `data/marts/mart_municipi.parquet` (`derive_fase1`) i `data/web/municipis.bergueda.json` (`export_web_municipis`).

## Verificación (venv, PYTHONUTF8=1)
- `derive_fase1.py` → parquet reescrit; `--check` → **OK**.
- `verify_marts.py` → **OK** (Spearman 0,869; Castellar/Berga quadren; cap ancoratge tocat).
- `export_web_municipis.py --check` → **OK** (31 munis).
- `dbt parse` → **OK** (el canvi del model no trenca el templating).
- Query directa: munis amb `carrega_funcional_est < padró` = **0** (abans 1); Puig-reig **4343→4558**.
- Diff net: parquet (1 valor) + JSON (1 valor + 3 textos de contracte propagats) + 3 fonts. Cap altra dada moguda.

## Pendiente
- [ ] **Talaia:** review/merge (toca el contracte → gatekeeper).
- [ ] (triatge) test de robustesa del ranking IETR a pesos (substitueix el claim retirat) + test invariant `carrega_funcional_est == greatest(padró, L1, L2)`.
- [ ] Docs (dossier/metodologia) si esmenten la fórmula vella de `carrega_funcional_est` — revisar (no bloqueja).

## Enlaces
- `packages/transform/models/marts/mart_municipi.sql` · `packages/transform/derive_fase1.py` · `semantic/metrics.yml`
- `bitacora/2026-06-10_restauracio-talaia_talaia.md` (el triatge que ho va destapar)

— Sondeig
