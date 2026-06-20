# Changelog

Todas las versiones de Cambium Charter. Formato: fecha · cambios.

## v0.5 — 2026-06-18

- **Release de ADELGAZAMIENTO: el Artículo 5 vuelve a caber en una lectura (≈366→286 palabras).** Des-duplicación pura, no recorte: el detalle de la **mordida temprana** (justificación expandida) y de la **delegación acotada del merge** (mecánica: commit-acta, revocable, no transitiva, nunca audita lo que mergea, no programada, crecer→relevo, condiciones operativas) se recoloca a `adr/0001`, que pasa a ser su **ubicación canónica viva** —la carta lo apunta, no lo repite—. Permanecen en el esqueleto los principios-frase, la clase regulada estrecha, **"ratificada por la humana"** (invariante 1) y las **cuatro líneas rojas** de la delegación (nunca código, doctrina/`.cambium/`, **la mordida regulada** ni la jurisdicción ajena) + "ningún PR tiene dos autoridades a la vez" (invariante 2). Razonado en `adr/0002`.
- **Adversario para equipo auto-coordinado (Art. 5, fallback):** sin humana ni agente rotada, el rol de adversario lo asume una **copia fresca y sin contexto de la propia coordinadora que verifica y NO mergea**, por-riesgo antes de salida irreversible (invariantes 2 y 6; no es por-acción, §V). Detalle en `adr/0002` y `EJEMPLOS.md`.
- **Coste = tercera lectura del Dial de autonomía (§IV · §V):** el Dial es también **tope de gasto** —agotar el crédito asignado se **escala** y se **reporta**, no se agota en silencio (invariantes 1 y 6)—; inyectado en la cláusula de escalado existente, sin perilla ni frase nueva. Contadores y umbrales en `REGLAS.md`. Antipatrón de §V ampliado: morir por presupuesto es fallar en silencio.
- **Iniciativa fractal de toda agente (Nota al invariante 2):** coletilla, no viñeta nueva en §IV — toda agente, al cerrar un turno **con trabajo**, anota **ideas, mejoras y candidatas a siguiente tarea** en su bitácora; la coordinadora las tría hacia `next.md` o las escala (**propone, no actúa**, invariante 5); un turno vacío sigue siendo no-op silencioso (§V). Generaliza la coordinadora-proactiva de v0.4 sin engordar §IV.
- **Neto: la carta encoge (≈15 palabras menos).** El adelgazamiento del Art. 5 (des-duplicación a `adr/0001`) supera lo añadido por el adversario auto-coordinado, el tope de gasto y la iniciativa fractal, todos mantenidos como injertos/coletillas (cero secciones o viñetas nuevas). §IV no crece más allá de la cláusula del Dial (se respeta el aviso de `adr/0001`: §IV no se vuelve cajón de sastre).

## v0.4 — 2026-06-18
- **El despertar drena la cola lista (§IV):** un despertar ya no cierra tras una tarea; encadena tareas listas re-leyendo `next.md` entre cada una (manda el orden vigente tras el pull) **hasta el tope del Dial de autonomía** —que se reusa como límite del bucle, no es perilla nueva—. Por defecto, sin Dial fijado, drena **una sola tarea y para** (el modo seguro por turnos no cambia). Salta las bloqueadas sin reordenarlas; el drenaje largo hereda la cadencia de contrapeso del Art. 5 (más tareas seguidas → más verificación periódica/cruzada, no por-acción).
- **Coordinadora proactiva, no integradora pasiva (Nota al invariante 2 · §III):** la coordinadora **propone** arquitectura, estrategia y la siguiente jugada sin esperar a que se las pidan —par de **iniciativa**, no de autoridad—. **Propone, no decide**: el qué/por qué los ratifica la humana y el silencio no es ratificación (invariante 1). El texto del invariante 2 no cambia (se descartó "tech-lead" por redundante con "arquitecta").
- **§VIII pasa a "familia de relevo":** además del **relevo de coordinación** (A, intacto), se formaliza la **reasignación de agente** (B): la coordinadora mueve trabajo/jurisdicción entre dueñas **ya ratificadas** vía `next.md`+`role.md` sin tocar la llave de merge; redibujar el mapa de jurisdicciones se escala a la humana (invariante 1); el `role.md` de la saliente se cierra en el **mismo cambio** que abre el de la entrante (sin doble dueña, invariante 5); el rol de coordinación **nunca** se reasigna por aquí (eso es A).
- **Rigor proporcional al riesgo en la puerta (Art. 3 · §IV · Art. 5):** *fast-path no-código* para los propios artefactos de coordinación de la coordinadora (`next.md`, bitácoras, `.cambium/memoria/`) —commit directo con identity-inline y verificación anti-secretos/rutas obligatoria aunque no haya CI; tres líneas rojas: nunca código, nunca doctrina, nunca jurisdicción ajena—; *mordida temprana* del auditor antes de que la afirmación se fije en `main` para la clase regulada (citas legales, plazos, importes; declarada estrecha en `REGLAS.md`); y el **principio** de delegación acotada del merge por **partición** (jurisdicción única aplicada al merge; nunca código/doctrina; registrada y ratificada por la humana, revocable, sin sub-delegar, la delegada nunca audita lo que mergea) — las condiciones operativas viven en `REGLAS.md`/`EJEMPLOS.md`, no en el esqueleto. Razonado en `adr/0001`.
- **Visibilidad solo-lectura de producción (§IV, Camino de producción):** se añade el punto (c) — el estado vivo (base gestionada, API, inventario) no vive en el repo ni debe; la coordinadora necesita un camino de **lectura honesta** (endpoint de salud, consulta read-only o un **puntero —no credencial—** que da la humana, invariante 1); observa, no toca, y lo observado no se commitea como verdad (invariante 3); si no hay camino, se **declara la ceguera** (verificar-o-declarar, invariante 6).

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
