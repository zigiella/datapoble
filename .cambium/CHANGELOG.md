# Changelog

Todas las versiones de Cambium Charter. Formato: fecha · cambios.

## v0.3.1 — 2026-06-16
- **Procedencia en `.cambium/VERSION` (`upstream:`):** el sello graba también la URL del kit del que se vendorizó. Así, al *actualizar* (§IX), la coordinadora resuelve de dónde re-vendorizar leyendo su propio repo —no hay que decírselo en el latido—. Se graba en la génesis (§III).
- **Latido de actualización mínimo:** con `upstream:` grabado, el latido canónico de la humana se reduce a *«‹Coordinadora›: adopta Cambium Charter vX.Y.»* (la fuente explícita `…desde ‹kit-repo›@vX.Y` queda como *fallback* si no hubiera `upstream:`). Sincronizados §IX, `README` y `plantillas/actualizacion-charter.md`.

## v0.3 — 2026-06-16
- **Coherencia (no rompe principios):** la carta deja de hardcodear su número de versión y remite a `.cambium/VERSION`/`CHANGELOG` (cierra la divergencia v0.2 vs v0.2.3). Se define el **latido** (señal-puntero; no transporta la tarea; el latido inicia, el PR cierra). La **puerta** se declara canónica en `plantillas/PR-checklist.md`. "CI verde" se generaliza a "la verificación que tenga el proyecto" (sin pipeline ≠ sin verificación). Nota al pie de **identity-inline** con el comando. El antipatrón `now()` se explica. Convención de handoff (`Handoff a:`).
- **Invariante 2 reforzado:** la coordinadora coordina y **codifica solo lo mínimo**; **exactamente una autoridad de merge** en todo momento (auditor, humana y agente programada no mergean).
- **`next.md` como cola multi-tarea por agente:** varias tareas en orden, **acumulativas** entre turnos, nunca borradas por reescritura. "Mirar `next.md` siempre" es la primera acción de toda agente; **la asignación va al repo (push) ANTES del latido**.
- **Topología:** matiz al subagente (robusto para el TRABAJO con worktree+PR; frágil para continuidad/multi-tecnología). Nueva cadencia de **despertar programado** (contrato agnóstico; primitiva en `role.md`), con no-op silencioso en vacío y fallo ruidoso al despertar.
- **Memoria de coordinación (opcional):** copia versionada y saneada en `.cambium/memoria/`, bandeja con autoría subordinada al repo, sin secretos, verificada por la puerta.
- **Verificar-o-declarar** + PR no-listo cuando no se puede verificar; la coordinadora monta el camino de verificación. **Camino de producción** = liveness + modos de conexión de dependencias externas (genérico).
- **Artículo 5** (umbral de verificación independiente) y **Artículo 3** (PR de equipo vs externo) afinados. **Ritual de reconstrucción-desde-repo** (§III) y nuevo **§VIII Relevo de coordinación** (reconstrucción + ratificación humana + cambio de llave atómico).
- **Plantillas:** `next.md` y `role.md` reescritas (cola; campos rama/handoff/despertar); nuevas `traspaso-coordinacion.md` y `memoria-coordinadora.md`.
- **Minimalismo** explícito en el preámbulo (presupuesto de tamaño). Descartado por over-engineering/portabilidad: rol steward dedicado, ids `T-NNNN`/poda automática, cerrojos, nombres de proveedores en la doctrina.
- **Génesis "la coordinadora nace primero" (§III):** orden canónico en 5 pasos (spec/idea → crear coordinadora → ayudar a crear el repo online → instalar método → proponer equipo → ratifica la humana). El repo y el equipo nacen DESPUÉS de la coordinadora.
- **Tres configuraciones de equipo (§III):** (a) propio (todas subagentes), (b) manual multi-tecnología (prompt iniciático con "clona el repo"), (c) híbrido (subagentes + manuales, anidables) — con tabla de consulta rápida. El método no cambia entre las tres; cambia el cableado de arranque/relevo.
- **Nuevo §IX — Actualización del método (adopción de versión):** ritual de la coordinadora para adoptar una versión nueva del Charter (re-vendorizar `.cambium/` + sellar `VERSION` → migrar `next.md`/`role.md`/plantillas sin perder la cola → encolar la auto-actualización en el `next.md` de cada agente → despertar según su tipo). Distinguido en §VII de **custodiar** la carta (produce versiones) vs **adoptar** (las consume). Incluye el **latido canónico de la dirección humana** (nombra versión + tag de origen) y la disciplina **sellar = merge + tag**. Plantilla `actualizacion-charter.md`.
- **Artículo 5 consciente de coste:** la verificación independiente **no es por-acción** (antipatrón nuevo); cadencia triple — periódica (por hito) + por-riesgo (antes de público/irreversible) + cruzada entre pares (que la coordinadora sugiere). A más autonomía, más cadencia, no más auditoría por-paso.
- **Adaptadores:** `.cursorrules` reconocido como **4º adaptador** (es dotfile; estaba) y puesto al día con el cuerpo v0.3 + la línea "adopta vX.Y"; los cuatro con cuerpo idéntico.

## v0.2.3 — 2026-06-08
- Instalación ordenada: el método se vendoriza en `.cambium/`; en la raíz del proyecto solo van los adaptadores. El `README` del proyecto no se sobrescribe.
- Adaptadores apuntan a `.cambium/CHARTER.md` y `.cambium/REGLAS.md`.
- Nuevo antipatrón: rutas locales (`C:\…`) en ficheros versionados.

## v0.2.2 — 2026-06-08
- Plantillas de arranque: `arranque-coordinadora.md` y `arranque-agente.md` (el mensaje listo-para-pegar que faltaba).
- §III refuerza tres lecciones de uso real: la coordinadora **instala el método en el repo del proyecto** (no solo lo lee); el prompt de cada agente **incluye el repo**; y los nombres se eligen **cercanos al dominio**, no la metáfora del método.

## v0.2.1 — 2026-06-08
- Plantilla `REGLAS.md` (el hueco de los innegociables, que faltaba) y `CONTRIBUTING.md`.
- README sincronizado.

## v0.2 — 2026-06-08
- Carta **operativa**: añadidos el arranque (génesis) y el bucle (turnos + asignación en `bitacora/next.md`).
- Naming como convención genérica; el *tema* (p. ej. femenino / insectos) es cuerpo, no esqueleto.
- Engram **metabolizado**: principios sobre repo+PR; la herramienta, diferida (bandeja lateral, nunca fuente de verdad).
- Plantilla `next.md` y protocolo del latido en los adaptadores.

## v0.1 — borrador inicial
- Invariantes, doctrina, liturgias, antipatrones, adaptadores y plantillas.
