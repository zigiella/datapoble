# Pas 4 · primer pas: validació externa contra ETCA (Idescat)

**Fecha:** 2026-06-11
**Autora:** Sondeig (dades) — executat per Talaia
**Para:** Talaia (review/merge) · Bea
**Tema:** primer pas del Pas 4 (spec §2.3): comparar la nostra inferència de presència amb la **Població ETCA** oficial d'Idescat. Primera validació EXTERNA discriminant (fins ara l'única era Spearman(IETR, residus), gairebé circular: L2 *són* residus).
**Status:** fet, verificat (artefacte + go/no-go + CI --check) / handoff. La VISUALITZACIÓ a /metodologia va a PR-2.

## El resultat (pernocta vs ETCA, 9 munis coberts)

| municipi | padró | ETCA | pernocta nostra | error |
|---|--:|--:|--:|--:|
| Berga | 17.539 | 17.057 | 17.174 | **+0,7%** |
| Puig-reig | 4.558 | 4.313 | 4.343 | **+0,7%** |
| Gironella | 5.082 | 4.760 | 5.245 | +10,2% |
| Pobla de Lillet, la | 1.106 | 1.121 | 1.243 | +10,9% |
| Guardiola de Berguedà | 962 | 1.005 | 1.125 | +11,9% |
| Bagà | 2.167 | 2.305 | 2.780 | +20,6% |
| Avià | 2.263 | 1.990 | 2.684 | +34,9% |
| Casserres | 1.665 | 1.571 | 2.225 | +41,6% |
| Cercs | 1.236 | 1.130 | 1.652 | +46,2% |

**Spearman ρ = 1,000** (ordenem els municipis EXACTAMENT com l'ETCA) · **error medià = 11,9%** → **PASSA el go/no-go** (ρ≥0,7 i error≤15%) per a la pernocta. La `carrega_funcional_est` també té ρ=1,0 però error medià 15,1% (NO passa per poc — sobreestima perquè inclou visitants de dia). **Lectura honesta:** clavat als grans i estables (Berga, Puig-reig <1%), però sobreestimem força els petits (Cercs +46%, Casserres +42%, Avià +35%) → la validació cobreix el cas FÀCIL; els turístics extrems (<1.000: Castellar, Gósol, Saldes) NO tenen ETCA municipal i queden sense àncora directa, com el disseny anticipava.

## Què he fet (sense reconstruir el mart — `data/raw/` no hi és)
- **Connector EMEX estès** (`idescat_emex.py`): afegits `f342`/`f343`/`f344` (ETCA estacional / Població ETCA / %) al dict INDICATORS → quan corri el pipeline complet (amb dades crues), l'ETCA s'ingerirà sol per als munis que en tenen.
- **Snapshot committejat** `data/etca/etca_bergueda.csv` (+ `_provenance.json`): ETCA dels 31 munis del Berguedà (9 amb dada, 22 NULL honest), font Idescat EPE base 2021, any 2024 (p). És la dada «ingerida» materialitzada directament (slice), ja que no puc córrer dbt sense el raw.
- **Script de validació** `tools/validacio_etca.py`: llegeix snapshot + `mart_municipi.parquet`, calcula per municipi (pernocta/càrrega vs ETCA + error) i el resum comarcal (Spearman + error medià + go/no-go), escriu `data/web/etca-validacio.json`. Té `--check` (offline-reproduïble) i corre al **gate de CI**.

## Verificació
- `python tools/validacio_etca.py` → artefacte escrit; `--check` verd; afegit a `.github/workflows/ci.yml` (job data).
- Cap fetch en viu al build/CI: tot llegeix snapshot + mart committejats.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] **PR-2 (web):** bloc «validació externa (ETCA)» a /metodologia que llegeixi `etca-validacio.json` (taula + ρ + error + nota honesta de cobertura). Cal afegir-lo a `copy-data.mjs` i renderitzar-lo.
- [ ] **Carril dades (decisió Bea):** seguir amb les covariables de Catalunya (INE ADRH renda, altitud, gas, CTE) + classificador `tipus_territorial` (Nivell B) — en silenci, offline.
- [ ] Correcció al disseny: el 9è muni cobert és **la Pobla de Lillet** (≥1.000); i la llista correcta és Guardiola de Berguedà, **no Olvan**.

## Enlaces
- `packages/ingestion/datapoble_ingestion/idescat_emex.py` · `tools/validacio_etca.py` · `data/etca/etca_bergueda.csv` · `data/web/etca-validacio.json` · `.github/workflows/ci.yml`
- disseny: `bitacora/2026-06-11_pas4-bases-etca-disseny_talaia.md`

— Sondeig
