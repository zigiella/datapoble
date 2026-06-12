# /metodologia · bloc «Validació externa (ETCA)» (Pas 4, PR-2)

**Fecha:** 2026-06-11
**Autora:** Mirador (frontend)
**Para:** Talaia (review/merge) · Bea
**Tema:** publicar al web la validació ETCA que va computar el Sondeig (#100). La part visible del primer pas del Pas 4.
**Status:** fet, verificat (check + build + HTML prerenderitzat ca/es) / handoff

## Què he fet
- **`copy-data.mjs`**: ara copia també `data/web/etca-validacio.json` → `static/data/` (a més del dataset), amb el mateix fallback no-fatal per fitxer.
- **`$lib/contract/etca.ts`** (nou): tipus `EtcaValidacio` (forma de l'artefacte de `tools/validacio_etca.py`).
- **`metodologia/+page.ts`**: carrega l'artefacte ETCA (prerender-safe, opcional: si no hi és, la secció no es renderitza).
- **`metodologia/+page.svelte`**: nou bloc **H · «Validació externa (ETCA)»** amb: intro (per primera vegada ens mesurem contra una xifra oficial independent), un headline (ρ + error medià + veredicte «Passa el llindar»), la **taula** dels 9 munis coberts (Municipi · Padró · ETCA · qui dorm nostre · error), el llindar go/no-go, i una nota honesta de cobertura (9/31; encertem els grans, sobreestimem els petits; els turístics extrems sense ETCA). Font Idescat EPE amb base i any.
- i18n nou (ca/es): `met_block_validacio`, `met_validacio_intro/_nota/_font`, `met_val_rho/_err/_passa/_nopassa/_llindar`, `met_val_th_padro/_etca/_nostra/_error`.

## Verificació
- `npm run check` → **0/0**; `npm run build` → OK (copy-data confirma `etca-validacio.json → static/data/ (8.2 kB)`).
- HTML prerenderitzat `/metodologia` i `/es/metodologia`: secció present; headline amb ρ, «Error medià», «Passa el llindar»; taula amb Berga (17.057 / 17.174 / +0,7%), Cercs (+46,2%), medià 11,9%. Castellar apareix a la pàgina però NO a la taula (correcte: sense ETCA).

## Notes
- La taula NO usa el contracte de mètriques (és un artefacte de validació a part); per això un tipus propi + càrrega pròpia, no `metrics`.
- Cap fetch en viu: tot llegeix l'artefacte committejat (copiat a static al prebuild).

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] Amb això, el primer pas del Pas 4 queda **complet i visible**. Següent: carril dades Catalunya (covariables + Nivell B `tipus_territorial`).

## Enlaces
- `packages/web/src/routes/metodologia/+page.{ts,svelte}` · `$lib/contract/etca.ts` · `scripts/copy-data.mjs` · `messages/{ca,es}.json`
- dada: `bitacora/2026-06-11_pas4-etca-validacio_sondeig.md` (#100) · `data/web/etca-validacio.json`

— Mirador
