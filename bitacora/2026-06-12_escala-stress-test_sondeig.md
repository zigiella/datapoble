# Stress-test de l'escala: Barcelonès + Tarragonès turístic vs ETCA

**Fecha:** 2026-06-12
**Autora:** Sondeig (dades) — executat per Talaia
**Para:** Talaia (review/merge) · Bea
**Tema:** «començar l'escala» (decisió Bea): incorporar Barcelonès + Salou i testejar. Prova del disseny §11.2 (Barcelonès trenca tots els supòsits; Salou = litoral extrem). Carril dades en silenci (intern, no publicat).
**Status:** fet, verificat (classificació + ETCA) / handoff

## Què he fet
- **Classificador `tipus_territorial` ampliat** amb el primer lot d'escala: llistes AMB (Barcelonès) + costaners (BCN/Badalona/Sant Adrià + Salou/Cambrils/Vila-seca/Tarragona) + Tarragona capital. Afinada la regla litoral: metropolità (AMB) vs vacacional (resta) — la densitat sola no distingeix un resort dens (Salou) d'una ciutat metro. (El Berguedà no canvia: `--check` verd.)
- **`tools/stress_test_escala.py`**: baixa ETCA (Idescat) + altitud/densitat (EMEX) dels 9 munis, classifica i contrasta. Artefacte intern `data/territorial/stress_test_escala.csv`.

## Resultat (la tesi confirmada)

| municipi | tipus_territorial | ETCA% | densitat |
|---|---|--:|--:|
| Salou | litoral_vacacional | **204%** | 2.050 |
| Cambrils | litoral_vacacional | 135% | 1.053 |
| Vila-seca | litoral_vacacional | 129% | 1.116 |
| Tarragona | litoral_vacacional | 111% | 2.475 |
| Barcelona | litoral_metropolita | 106% | 16.904 |
| Sant Adrià | litoral_metropolita | 95% | 10.204 |
| l'Hospitalet | metropolita_dens | 93% | 23.561 |
| Badalona | litoral_metropolita | 92% | 10.890 |
| Santa Coloma | metropolita_dens | 88% | 17.607 |

- **El Nivell B tipa correctament** els dos tipus nous (metro dens vs litoral), que al Berguedà no apareixen → el «pont» de l'escala funciona.
- **Cap base endògena única encaixa**: el litoral vacacional es **dobla** (Salou +104%) i el metro residencial **baixa** (Santa Coloma −12%: hi viu menys gent de la que consta, surten a treballar). Exactament el «mapa de clima i renda disfressat» que el disseny adverteix → **confirma que cal el Nivell C** (esperats per tipus + calibratge ETCA per tipus).

## Notes
- Bug trobat i corregit: el meu `_num` (format català de l'SSV) corrompia els decimals d'EMEX (que usa «.»): les densitats sortien ×10. La classificació no se'n veia afectada (va per AMB), però la dada de l'artefacte sí — corregit.
- L'estimació del model (base Berguedà) per a aquests munis (per quantificar l'error, no només l'ETCA) necessita els senyals (ICAEN kWh, ARC residus) → següent pas del carril, cap a la regressió Nivell C.
- Llistes AMB/costaners PARCIALS (el lot de prova); a completar amb les oficials senceres a escala.

## Pendiente
- [ ] **Talaia:** review/merge.
- [ ] Nivell C: ingerir covariables (renda INE ADRH, gas, clima) + senyals d'aquests munis → regressió d'esperats; calibrar el coeficient senyal→persones per tipus contra ETCA (go/no-go per tipus).

## Enlaces
- `tools/stress_test_escala.py` · `tools/tipus_territorial.py` (llistes) · `data/territorial/stress_test_escala.csv`
- disseny: `bitacora/2026-06-11_pas4-bases-etca-disseny_talaia.md` (§11.2) · Nivell B: `…pas4-tipus-territorial_sondeig.md`

— Sondeig
