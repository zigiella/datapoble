# Actualización del método — adopción de Cambium Charter vX.Y

> Checklist de la coordinadora cuando la humana dice «equipo TAL, actualizad el charter [a vX.Y]».
> Es un cambio versionado en el REPO + una cola de auto-actualización por agente, NO un mensaje de chat.
> Reutiliza piezas que ya existen: re-vendorizado (§III), cola en next.md con push antes del latido (§IV),
> reconstrucción-desde-repo (§III). Doctrina: CHARTER §IX. No es relevo (§VIII) ni génesis (§III).
> Adoptar una versión ≠ custodiar la carta (§VII): aquí solo se CONSUME una versión ya sellada.

## Latido de la dirección humana (cómo arranca)

*«‹Coordinadora›: adopta Cambium Charter vX.Y.»* — basta nombrar la versión; tú resuelves **de dónde** re-vendorizar leyendo `upstream:` en tu `.cambium/VERSION` (grabado en la génesis). `vX.Y` debe ser un **tag sellado** del kit. Si `upstream:` faltara, el latido nombra la fuente (`…desde ‹kit-repo›@vX.Y`). Si el equipo está en una versión **pre-§IX**, el primer salto se hace a mano (re-vendorizar ya trae §IX); de ahí en adelante basta este latido.

## Orden obligatorio (no se salta)

### 1. Re-vendorizar `.cambium/` (PR que mergea SOLO la coordinadora)
- [ ] `CHARTER.md` traído de la versión nueva.
- [ ] Plantillas nuevas o cambiadas (`plantillas/…`).
- [ ] `REGLAS.md` SOLO si el kit cambió algo que afecte a la plantilla (los innegociables del proyecto NO se pisan).
- [ ] **`.cambium/VERSION` sellado al nuevo número** (`Cambium Charter vX.Y`).
- [ ] Si el **cuerpo del adaptador** cambió (CLAUDE/AGENTS/GEMINI/.cursorrules): actualizar también el adaptador en la raíz.
- [ ] Pasa la **puerta** (verificación verde · sin secretos · sin rutas locales) y **mergea solo la coordinadora** (invariante 2): la versión vieja y la nueva no conviven a medias en `main`.

### 2. Migrar lo que la versión nueva toque (mismo PR o uno seguido)
- [ ] `bitacora/next.md` al formato nuevo si cambió, **conservando la cola acumulada** (invariante 6 — la cola NO se pierde en la migración).
- [ ] Cada `docs/equipo/<nombre>_role.md` al formato nuevo (campos nuevos: *despertar*/*rama*/*handoff*/*configuración*…), conservando el contenido vivo.
- [ ] Carpetas nuevas que el método introduzca (p. ej. `.cambium/memoria/`) solo si el equipo las va a usar.
- [ ] Registrar el cambio donde corresponda (CHANGELOG del proyecto / ADR si fue decisión).

### 3. Encolar la auto-actualización en el `next.md` de CADA agente (push ANTES del latido, §IV)
Ítem de cola idéntico y autocontenido para todas:

```
- [ ] **Adopta Cambium Charter vX.Y** · jurisdicción: la tuya ·
      git pull → relee .cambium/CHARTER.md (versión nueva) → relee tu role.md si cambió →
      adopta lo que toque a tu jurisdicción/cadencia → confirma por escrito (bitácora/commit "adoptada vX.Y")
      · hecho cuando: confirmación escrita en el repo
```
- [ ] Es tarea de cola normal: acumulativa, no se borra, sale solo cuando está confirmada.

### 4. Despertar a cada agente según su tipo (las tres configuraciones, §III)
- [ ] **Subagente (config a, o las de c):** la coordinadora la orquesta **en el acto**; tras el pull adopta y confirma sin esperar relevo.
- [ ] **Manual / otra tecnología (config b, o las de c):** pásale el **latido** (puntero a su cola); ella, en su contexto/herramienta, hace pull y se auto-actualiza. Asume que ya tiene el repo clonado (su prompt iniciático lo garantizó). **Si una agente manual aún no existe: no se actualiza, se CREA** con `arranque-agente.md` ya en la versión nueva.
- [ ] **Híbrido (c):** aplica a cada agente el trato de su tipo; un agente manual con subagentes propios re-vendoriza/propaga hacia los suyos igual que la coordinadora hace con el equipo.

### 5. Cierre
- [ ] Verificar que **todas confirmaron** la adopción (cola en *Hecho*).
- [ ] Reportar a la humana: *«equipo en vX.Y»*.
- [ ] Dejar en bitácora qué versión corría antes y qué se migró.
- [ ] Una agente que **no puede** adoptar (no pulla, formato roto) **deja ruido** (issue/bitácora); nunca falla en silencio (invariante 6).

## Recordatorios
- La versión vive en `.cambium/VERSION`, **no en el chat**: si el chat dice vX.Y y el repo dice otra, gana el repo (invariante 3).
- Antipatrón: decir «ya estamos en vX.Y» por chat sin re-vendorizar ni sellar `VERSION`; encolar la auto-actualización sin push antes del latido; perder la cola acumulada al migrar (§V).
