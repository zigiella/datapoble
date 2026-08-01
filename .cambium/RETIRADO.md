# ⛔ RETIRAT el 2026-08-01

Aquest directori conté **Cambium Charter**, el mètode que va governar datapoble del 2026-06 al
2026-08-01. **Ja no és vigent.** El mètode viu ara a `AGENTS.relay.md` + `.relay.yml` (Mycelia
Relay v0.5) i les regles dures a `REGLAS.md`, a l'arrel.

## Per què

L'aparell de Cambium està pensat per a **diverses agents amb contextos separats**: cua assignada,
latido, torns, porta de set punts, jurisdiccions tancades. A datapoble hi ha **una coordinadora amb
subagents propis**, i aquell aparell cobrava cerimònia que ja no resolia res: la cua me l'escrivia
a mi mateixa i el latido me'l donava jo.

El que sí que segueix fent mal —i Relay resol— és que **el meu jo de demà recuperi el fil**, que la
direcció pugui deixar un encàrrec des del mòbil, i que **estigui escrit què pot veure un agent al
núvol** quan entri.

## No s'esborra res

Això és **invalidar, no esborrar**. El contingut és història i és dada:

- `CHARTER.md`, `REGLAS.md`, `VERSION`, plantilles: es queden tal com estaven.
- Les **bitàcoles** (`bitacora/`) tampoc es toquen; `bitacora/next.md` queda marcat com a retirat
  al seu propi capçal, amb la cua migrada a Issues (#302–#314).

## Què en va sobreviure

Les **regles de producte i seguretat**, senceres i sense suavitzar, a `REGLAS.md` de l'arrel:
la 7 (procedència de les xifres), la **9** (carril de dades en silenci, amb el seu go/no-go), la 9b
(pressupost = límit, no silenci), la **10** (secrets mai al repo) i l'11 (working dir compartit).
Numeració i català intactes.

L'única que **canvia de contingut** és la **3**: la jurisdicció rígida passa a propietat de sentit
comú, reclamada i temporal — el que cuida la qualitat és la verificació, no la tanca.

Els `docs/equipo/*_role.md` **es queden on són**: segueixen sent el planter dels fronts.

El detall sencer, a `docs/adr/0001-de-cambium-a-relay.md`.
