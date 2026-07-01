# Handoff a: Sondeig (dades · model Nivell C) — la col·lisió d'estimacions

**De:** Talaia (geo-rag) · **Origen:** nota de la Rapaz (30-06-2026, OneDrive/CAJON/11) · **Data:** 2026-07-01

## El fet, dit amb precisió

El model Nivell C dona estimacions de pernocta + rang **idèntiques** a municipis diferents. A tota Catalunya hi ha **54 grups** de munis amb `(estimacio, rang_baix, rang_alt)` idèntics, alguns triples. No és soroll aleatori; és **estructura** (la resolució del model toca fons en algun punt: dos llocs cauen a la mateixa cel·la d'alguna graella interna). S'assembla al règim dens, on el consum per càpita baix empenyia tot cap al mateix valor.

**El cas greu (registre oficial, nucli validat):** Guardiola de Berguedà i la Pobla de Lillet reben la mateixa estimació (852, rang 726–1037) tot i tenir ETCA oficials **diferents** (1005 i 1121). Tots dos són **oficial** (≥1.000 amb ETCA), no soroll. L'etiqueta oficial promet «aquí el model es pot contrastar amb la font»; quan contrastes, **la font els separa i el model no**. L'etiqueta promet més del que la dada fa, dins el nucli validat. Això no reforça la tesi de «l'observatori que sap el que no sap» — la **complica**.

## La pregunta que importa (per a Sondeig)

> **Quantes estimacions del registre oficial són números repetits que el model no distingeix, i que el registre oficial presenta com si fossin específics del municipi?**

Subpreguntes que la resposta necessita:
1. Dels **54 grups**, quants toquen munis del registre **oficial** (≥1.000 amb ETCA) i quants són només **soroll**. Al soroll l'empat és coherent amb l'etiqueta; a l'oficial la contradiu.
2. Quina és la **causa estructural** de la col·lisió al Nivell C: hi ha una graella, un arrodoniment o una covariable que col·lapsa municipis diferents al mateix valor?
3. On la font (ETCA) separa dos munis que el model iguala, **quin senyal mana** per a la xifra pública? Doctrina: als ≥1.000 mana Idescat. Si la costura ja hi és, potser la col·lisió queda **tapada per l'ETCA a la vista pública** i el problema és intern, no de cara — **cal comprovar-ho**.

## Dades ja calculades (Berguedà, per arrencar)

Dels 31 munis del Berguedà, **12 estan en col·lisió**:

| Registre | Munis en col·lisió | Detall |
|---|---|---|
| **oficial** | 2 | **Guardiola de Berguedà ↔ la Pobla de Lillet** (est=852). L'esquerda: ETCA 1005 vs 1121, model 852=852. |
| **senyal** | 2 | Sagàs (est=247) i Santa Maria de Merlès (est=238), cadascun amb 1 muni de fora del Berguedà. |
| **soroll** | 8 | Gósol (grup 3), Saldes (grup 3), Montclar, Montmajor, la Nou de Berguedà, Sant Julià de Cerdanyola, Vallcebre, Viver i Serrateix (grups de 2). |

Recompte recalculable: vegeu `packages/geo-rag/src/datapoble_geo_rag/descriptions.py` (`_collision_groups`) sobre `data/web/pernocta-catalunya.json`.

## Què ha fet la geo-rag (i el principi)

La Fase 0b **no ha creat** la col·lisió (renderitza el substrat fidelment) però **és qui la posa davant de l'usuari**. Per tant: les descripcions dels 12 munis afectats porten una **advertència honesta** (el parell oficial es nomena mútuament i cita els ETCA que els separen; la resta indica que el número el comparteixen N munis i no és específic). El principi de la Rapaz: *renderitzar fidelment un error de la font no et fa responsable de l'error, però sí de propagar-lo nu o amb advertència. La honestedat no és només no introduir mentides; és no propagar en silenci les que trobes pel camí.*

La **resolució de fons** (per què col·lapsa el Nivell C, i l'abast a l'oficial a tota Catalunya) és de Sondeig.
