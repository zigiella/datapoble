# Fase 1 · el recuperador espacial — contracte de disseny (abans de codificar)

**De:** Talaia · **Origen:** nota de la Rapaz (30-06-2026, OneDrive/CAJON/12) · **Data:** 2026-07-01

> Endavant amb la Fase 1. Però la col·lisió (12 dels 31 comparteixen estimació) canvia què vol dir **recuperació correcta**, i això s'ha de definir **abans** de codificar el rànquing. Un recuperador que sempre retorna un guanyador net quan la dada té empats **menteix amb confiança** — el pecat de sempre vestit de rànquing.

## El principi (la mateixa abstenció, a tres altures)

La incapacitat de distingir apareix a tres nivells, i el sistema honest hi fa **el mateix gest**:

| Altura | Nom | Gest |
|---|---|---|
| Dada | **soroll** | «no distingeixo aquest número del meu marge» |
| Municipi | **col·lisió** | «no distingeixo aquest poble d'aquell» |
| Recuperació | **empat** | «no distingeixo quin document va primer» |

La Fase 1 és on aquest gest arriba a la recuperació. **El recuperador no trenca empats que la dada no permet trencar; els reporta.** L'empat no trencable és una forma d'**abstenció — l'abstenció d'ordenar** — i connecta amb el KPI de calibració d'abstenció ja definit: no és una mètrica nova, és **el mateix KPI a un altre nivell**.

## Definició de «recuperació correcta» (el que es fixa abans d'optimitzar)

1. El resultat correcte **pot ser un empat** («aquests van junts»). Un recuperador que mai empata sobre dades amb empats és incorrecte per construcció.
2. Quan diversos municipis comparteixen estimació i **la consulta no els separa per cap altre camí** (geografia, nom, tipus), el recuperador **retorna el grup i ho diu**, en comptes de triar-ne un per diferències de frasejat que no volen dir res.
3. **Cap desempat arbitrari** presentat com si fos una tria informada.

## Arquitectura (la resta del pla, sense canvis)

1. **Filtre espacial dur PRIMER** (DuckDB `spatial`): comarca (tots 31) i veïnatge (`ST_Intersects` / `ST_DWithin`) acoten el conjunt de candidats abans de cap puntuació semàntica. Per a consultes de proximitat/ordre, **mana el SQL espacial**; la semàntica és per a la intenció difusa.
2. **Tres llistes ordenades** sobre els candidats: (a) distància espacial `1/(1+d)`; (b) cosinus semàntic sobre els embeddings de la 0b; (c) noms propis per FTS/trigram.
3. **Fusió RRF** `score = Σ 1/(60+rank)` (Cormack 2009) — fusiona **rangs**, no scores crus.
4. **Detecció d'empat** (l'única addició al pla): abans de retornar un guanyador net, el rànquing s'atura si la dada no permet ordenar.

## Regla d'empat (concreta)

- **Empat de dada (col·lisió):** si el/els candidats capdavanters pertanyen a un **grup de col·lisió** (mateixa `estimacio`+rang) i la consulta **no aporta senyal separador** (ni geografia, ni nom concret, ni tipus que els distingeixi), es retorna **el grup sencer marcat com a empat**, amb l'advertència que el número no és específic (i, si són oficials, que Idescat sí els separa).
- **Empat de score RRF:** si diversos candidats tenen `|Δscore| < ε`, es marquen com a **empatats**, no s'ordenen per soroll de frasejat.

## Criteris de correcció (pass/fail)

**PASSA (honest):** reconeix que el municipi comparteix estimació i ho reporta · nomena els municipis del grup o almenys diu que el número no és específic · cap desempat arbitrari.

**NO PASSA (fallada):** retorna un municipi del grup com a guanyador net amagant l'empat · ordena el grup per diferències de frasejat de la descripció · presenta la xifra compartida com si fos específica del municipi consultat.

## Banc de consultes de la Fase 1 (el cas de col·lisió hi entra el dia 1)

- Consultes **normals** amb resposta clara (recuperació temàtica i espacial): p. ex. proximitat (`veïns de Berga`), intenció difusa.
- **Cas de col·lisió OFICIAL (el més exigent):** una consulta sobre **Guardiola de Berguedà** o **la Pobla de Lillet** formulada **sense àncora** de geografia ni nom que els separi (p. ex. «quina presència nocturna estimada té {muni}») → ha de reportar l'empat i que **Idescat sí els distingeix** (ETCA 1005 vs 1121). L'etiqueta oficial promet «contrastable» i l'empat la desmenteix.
- **Cas de col·lisió SOROLL:** una consulta sobre un grup soroll en col·lisió (p. ex. Gósol o Saldes, grups de 3) → ha de reportar que el número el comparteixen N municipis.

## Mètrica

- **Recall / precisió de la recuperació espacial** (que el filtre dur funcioni).
- **Calibració de l'abstenció, aplicada a l'ordenació:** un empat ben reportat compta com a **encert d'abstenció**; un desempat fals (guanyador net amagant l'empat) compta com a **fallada**. És el mateix KPI de la Fase 3, un nivell més amunt.

## Parada jugable

Un cercador geoespacial en llenguatge natural sobre el Berguedà que **s'atura quan la dada no permet ordenar** — no un rànquing que sempre inventa un guanyador.
