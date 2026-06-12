# Pas 4 · Nivell B: classificador `tipus_territorial` (carril dades, en silenci)

**Fecha:** 2026-06-11
**Autora:** Sondeig (dades) — executat per Talaia
**Para:** Talaia (review/merge) · Bea
**Tema:** el «pont» de l'escala (spec §2.2 Nivell B). Primer pas del **carril de dades en silenci** (decisió Bea #99): es prepara offline, NO es publica al web.
**Status:** fet, verificat (classificació + --check + CI) / handoff

## Per què
El Nivell B separa **què ÉS** un municipi (estructura geogràfica estable) de **com s'habita** (la `tipologia` comportamental que ja viu al mart). És el nivell d'agregació amb què, a escala Catalunya, cada municipi heretarà els esperats calibrats del seu tipus (Pas 4 Nivell C + ETCA). Per tant és prerequisit del que ha de corregir la sobreestimació dels petits que va revelar la validació ETCA (#100).

## Què he fet (sense reconstruir el mart; carril offline)
- **Connector EMEX estès** (`idescat_emex.py`): afegits `f258` (altitud), `f261` (superfície), `f262` (densitat) — covariables estructurals, per al pipeline complet.
- **Snapshot committejat** `data/territorial/inputs_bergueda.csv` (altitud/densitat/superfície dels 31, font Idescat EMEX, baixat en viu).
- **Classificador** `tools/tipus_territorial.py`: 8 tipus + flag `micromunicipi` (<250), regles per ordre amb `interior_rural` residual. Llistes de Catalunya (costaners, AMB, corona, capitals comarcals) parametritzades —buides/mínimes al Berguedà, a omplir a escala. Llindars: densitat metro ≥1.500 hab/km², Pirineu ≥800 m. Llegeix snapshot + mart → `data/territorial/tipus_territorial_bergueda.csv`. Té `--check` (offline) i corre al gate de CI.

## Resultat (31 munis del Berguedà)
- **16 `pirineu_alta_muntanya`** (≥800 m: Gósol 1.423, Castellar de n'Hug 1.395, Gisclareny 1.340…).
- **14 `interior_rural`** (Avià, Gironella, Puig-reig, Cercs, Bagà 785 m —just sota el llindar—…).
- **1 `capital_comarcal`** (Berga).
- **15 `micromunicipi`** (flag transversal: Gisclareny 28, Sant Jaume 25, Fígols 41…).
- Tipus litoral/metropolità/corona/agroindustrial: cap al Berguedà (comarca interior) → exerciten el classificador a escala, no al pilot. Honest: el pilot només prova un subconjunt de tipus.

## Notes / decisions
- **Separat de `tipologia`**: són dues columnes/conceptes diferents (estructura vs pressió); no es barregen (risc identificat al disseny).
- Casos límit deterministes i documentats: Bagà 785 m → rural; l'Espunyola 803 m → Pirineu. La regla és la regla.
- `agroindustrial` (pes CCAE) ajornat (dada fina amb secret estadístic als petits) → cau a rural de moment.
- **NO publicat**: artefacte intern a `data/territorial/`, no a `data/web/`. El producte segueix sent Berguedà.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] (carril dades) covariables Nivell C a escala Catalunya (renda INE ADRH, gas, clima) per a la regressió d'esperats; i omplir les llistes (costaners/AMB/capitals) quan s'escali.
- [ ] Integrar `tipus_territorial` com a columna del mart quan es reconstrueixi el pipeline complet (avui artefacte standalone perquè no hi ha `data/raw/`).

## Enlaces
- `tools/tipus_territorial.py` · `packages/ingestion/datapoble_ingestion/idescat_emex.py` · `data/territorial/{inputs_bergueda.csv,tipus_territorial_bergueda.csv}` · `.github/workflows/ci.yml`
- disseny: `bitacora/2026-06-11_pas4-bases-etca-disseny_talaia.md` · validació: `bitacora/2026-06-11_pas4-etca-validacio_sondeig.md`

— Sondeig
