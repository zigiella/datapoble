# next.md — cola de tareas por agente

> La coordinadora ESCRIBE aquí la cola de cada agente y hace push ANTES de pasar
> el latido por chat: el latido es un puntero a este fichero, no la asignación.
> Cada agente MIRA su bloque SIEMPRE al empezar (con latido o sin él) y trabaja
> la primera tarea pendiente. El orden de la cola = prioridad. El repo es la verdad:
> si el chat dice otra cosa, gana esto.
>
> Reglas de la cola:
> - Varias tareas por agente, en orden. La primera `[ ]` es la siguiente a coger.
> - ACUMULATIVA: una tarea solo sale de la cola cuando su PR está mergeado
>   (pasa a `### Hecho`) o la coordinadora la cancela CON MOTIVO (`### Cancelada`).
>   Nunca se borra por reescritura; si un turno no corrió, lo pendiente sobrevive.
> - Marcas: `[ ]` pendiente · `[~]` en curso (= turno de quien la tomó) · `[x]` hecho.
> - La agente solo cambia el estado de SUS tareas; la coordinadora añade y prioriza.
> - `[x]` solo cuando hay PR mergeado (la señal de fin es el PR, no la marca).
> - Cola vacía = no-op: no inventes trabajo; reporta y vuelve a esperar.

## <Agente>

### Cola (en orden; trabaja de arriba a abajo)
- [ ] **<entregable concreto>** · jurisdicción: <carpeta/función> · depende-de: <— | tarea previa> · hecho cuando: <criterio> + PR abierto · ref: <ADR/bitácora>
- [~] **<entregable en curso>** · rama: `feat/<agente>-<tema>` · hecho cuando: <criterio>

### Hecho
- [x] **<entregable>** · PR #<n> mergeado <AAAA-MM-DD>

### Cancelada (con motivo)
- ~~**<entregable>**~~ · cancelada <AAAA-MM-DD> · motivo: <por qué>
