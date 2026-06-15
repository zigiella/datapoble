# Nivell C · primera anàlisi: error del model base (Berguedà) per tipus territorial

**Fecha:** 2026-06-15
**Autora:** Talaia (coord/arquitectura) · carril dades (domini Sondeig)
**Para:** Bea · review
**Tema:** inici de «Catalunya incremental» (decisió Bea). Primer increment del Nivell C: mesurar
QUANT s'equivoca la base endògena del Berguedà per `tipus_territorial`, contra l'ETCA oficial.
**Status:** fet, verificat (dades en viu) / handoff per decidir el següent pas.

## Què he fet
- `tools/nivellc_analisi.py`: estén l'stress-test (que només contrastava ETCA↔tipus) afegint els
  **senyals reals** (elèctric domèstic ICAEN `8idm-becu` sector 7 + residus ARC `69zu-w48s`) i
  l'**estimació del model de 3 capes** amb les bases del Berguedà (elèctric 1.224, residus 410):
  `pernocta_est = kWh_domèstic / base_electric` (el padró es cancel·la). Compara `pernocta_est`
  vs ETCA i agrega l'error per tipus (mediana + Spearman ρ). Go/no-go: ρ≥0,7 i |err|≤15%.
- Mateix lot de 9 munis que l'stress-test (Barcelonès metro + Tarragonès litoral): tipus i ETCA
  ja verificats. Artefacte INTERN `data/territorial/nivellc_analisi.csv` (no publicat).

## Resultat (la tesi, ara en xifres d'error)

| municipi | tipus | ETCA | pernocta_est | err% |
|---|--:|--:|--:|--:|
| Barcelona | litoral_metropolita | 1.784.335 | 1.563.978 | −12,3 |
| Badalona | litoral_metropolita | 208.549 | 177.868 | −14,7 |
| Sant Adrià de Besòs | litoral_metropolita | 36.627 | 30.463 | −16,8 |
| l'Hospitalet | metropolita_dens | 262.223 | 197.382 | **−24,7** |
| Santa Coloma | metropolita_dens | 106.565 | 79.353 | **−25,5** |
| Salou | litoral_vacacional | 62.220 | 51.472 | −17,3 |
| Tarragona | litoral_vacacional | 156.109 | 134.444 | −13,9 |
| Cambrils | litoral_vacacional | 49.656 | 58.726 | +18,3 |
| Vila-seca | litoral_vacacional | 30.960 | 28.473 | −8,0 |

Per tipus (base única → error vs ETCA): litoral_metropolita err_medià 14,7% ρ=1,00 (GO just);
litoral_vacacional 15,6% ρ=0,80 (NO-GO, molt dispers); metropolita_dens 25,1% (n=2, ρ N/D).

## Lectura
1. **La base del Berguedà INFRAESTIMA el metro** (−25% dens, −15% metropolità): el resident urbà
   consum menys kWh domèstic/càpita (pisos petits) → dividir per 1.224 dona menys gent de la que
   l'ETCA diu. Biaix **sistemàtic i consistent en direcció** dins del tipus.
2. **El litoral vacacional és MIXT** (−17% Salou … +18% Cambrils): l'estacionalitat domina i una
   base sola no l'agafa; probablement cal una covariable d'intensitat turística o tractar el flux
   a part (la pernocta elèctrica anual mitjana dilueix el pic estival).
3. **La direcció consistent per tipus** valida que el Nivell B (classificador) és el pivot correcte
   per recalibrar → una **base per tipus** ja milloraria molt el metro. Però…
4. **N massa petita** (2-4 per tipus) per a una regressió estable o un go/no-go fiable → confirma
   «obliga el carril dades»: cal ingerir més comarques per tenir N per tipus.

## Recalibració ràpida — base per tipus (decisió Bea: «recalibració ràpida ja»)
Base per tipus = `base_electric / factor`, factor = mediana(ETCA/pernocta_est). Residual =
error que queda DESPRÉS de centrar (criteri honest amb base per tipus: el residual MÀXIM ≤15%,
no la mediana, que per construcció va a ~0). Artefacte intern `data/territorial/nivellc_bases_tipus.csv`.

| tipus | base/tipus | factor | residual medià | residual màx | go/no-go |
|---|--:|--:|--:|--:|---|
| metropolita_dens | 916 | ×1,34 | 0,5% | 0,5% | **GO** |
| litoral_metropolita | 1.044 | ×1,17 | 2,5% | 2,8% | **GO** |
| litoral_vacacional | 1.089 | ×1,12 | 5,2% | **33,0%** | **NO-GO** |

**Lectura:** una base per tipus **clava** el metro dens i el litoral metropolità (residual <3% →
publicables després de recalibrar, pendent de més N per fixar la base). El resident urbà gasta
~25% menys llum domèstica (base 916 vs 1.224). El **litoral vacacional NO es deixa arreglar amb
una base sola** (Cambrils +33% fins i tot centrat): l'estacionalitat domina → cal una covariable
d'intensitat turística o modelar el flux estival a part. Preliminar: N=2-4 per tipus.

## Pendent (per decidir amb Bea — «comentem»)
- **Opció A (ampliar mostra):** afegir més comarques (litoral sencer + AMB sencera + interior) per
  tenir N≥~10 per tipus → llavors recalibrar base per tipus i/o regressió amb covariables. Cal
  completar les llistes de `tipus_territorial` (COSTANERS/AMB/CAPITALS són parcials).
- **Opció B (covariables):** tapar els buits (renda INE ADRH, gas ICAEN, clima CTE) per a la
  regressió pròpia del Nivell C (no només base per tipus). Renda necessita accés especial INE.
- **Recomanació Talaia:** A primer (créixer N amb el que ja sé ingerir, comarca a comarca,
  verificant), i en paral·lel scoutejar les fonts de B. Tot en silenci fins al go/no-go.

## Enllaços
- `tools/nivellc_analisi.py` · `data/territorial/nivellc_analisi.csv`
- disseny: `bitacora/2026-06-11_pas4-bases-etca-disseny_talaia.md` (§Nivell C)
- previ: `bitacora/2026-06-12_escala-stress-test_sondeig.md`

— Talaia 🌊
