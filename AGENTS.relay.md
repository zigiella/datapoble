# Contrato Mycelia Relay

Estas reglas complementan el `AGENTS.md` del proyecto. Ante conflicto, mandan las reglas específicas del proyecto y las decisiones explícitas de la dirección.

## Antes de trabajar

1. Abre el issue asignado.
2. Comprueba objetivo, criterio de aceptación, alcance, entorno y política de datos.
3. **Verifica el estado de partida contra el repositorio.** Una tarea puede estar hecha en parte: es lo normal al instalar Relay sobre un proyecto en marcha. Si el issue declara cobertura previa, compruébala en el código antes de escribir; si difiere, corrige el issue **antes** de trabajar, no después. Rehacer trabajo existente, o sustituirlo por otra versión creyendo que partías de cero, es el fallo más caro de esta fase.
4. Confirma que no existe otra escritora activa sobre la misma tarea o rama.
5. Crea o recupera la rama que fije `.relay.yml`. Si tu arnés impone su propio espacio de nombres y no puedes cumplir el patrón, usa el suyo y **declara la rama real en el relevo**: el patrón existe para que la rama se encuentre, no es una ley que justifique no entregar.
6. Si el proyecto usa un grafo de conocimiento, lee **solo** las notas enlazadas desde el issue. Si no lo usa, tus reglas duras y clases de datos viven en el `REGLAS.md` de este repositorio: Relay no necesita grafo.

**El issue es el contrato cuando el trabajo cruza entornos o cambia de manos.** Ahí una instrucción de chat no reflejada en el issue todavía no cambia nada: una agente cloud no oye el chat, y el issue es la única superficie que las dos partes leen. Si una sola agente hace la tarea entera en un entorno, la dirección manda por su canal y el issue se abre cuando hay algo que relevar o algo que recordar.

## Durante el trabajo

- Mantén una sola tarea activa por agente salvo partición expresa.
- Haz cambios pequeños, reversibles y comprobables.
- No toques rutas fuera del alcance sin ampliar el issue o dejar un handoff.
- Publica checkpoints cuando el trabajo pueda perderse o continuar en otro entorno.
- No escribas secretos, credenciales, rutas locales ni datos `local-only`. Y antes de derivar algo de un material, mira sus **derechos** en `data_map`, no solo su clase.
- Declara las comprobaciones reales. Un check no ejecutado se marca como no ejecutado.
- **Clase y derechos son dos ejes, y los derechos viajan con el dato.** La clase dice **dónde** puede estar (`repository`, `cloud-ok`, `local-only`, `synthetic-only`); los derechos dicen **qué puedes hacer con él** (`libre`, `solo-agregado`, `no-reproducir`, `no-sale`), y valen igual aunque la clase no restrinja nada. Un material puede vivir legítimamente en el repositorio y ser obra ajena que se lee pero no se reproduce: eso es `repository` + `no-reproducir`, y si tu esquema no lo admite, el esquema está mal. Cada material, con sus rutas, está en `data_map` de `.relay.yml`.
- **Lo que el proyecto publica deliberadamente no es `local-only`.** Si algo ya está en la web o en un repositorio público, protegerlo como local es una ficción que obliga a despublicar para cumplirla. Lo protegido suele ser la materia prima, no el producto.
- **Ampliar el alcance se declara, no se cuela.** Si descubres que hace falta algo que el issue no pedía, hazlo si es reversible y dilo en la entrega como ampliación; nunca en silencio.

## Cuando no puedes cumplir el entorno declarado

Un issue puede declarar `hybrid` o `either` y tocarte solo una parte (eres local y hay un leg cloud que no puedes invocar, o al revés). Orden de preferencia:

1. **Particiona y entrega tu parte.** Cubre lo que tu entorno permite, entrega, y deja en el relevo qué leg queda pendiente y para qué entorno.
2. **Bloquea solo si tu parte no es separable** (`blocked`, con qué falta y quién puede desbloquear).
3. **Nunca simules el otro entorno.** Un leg cloud fingido desde local, o un relevo imitado con un subagente del mismo arnés, produce evidencia falsa: mismo contexto, misma máquina, ninguna de las condiciones que el relevo quería probar. Vale más un hueco declarado que una prueba inventada.

## Qué produce un leg para estar cumplido

Un leg es la parte de una tarea que ejecuta un entorno. Está cumplido cuando existen las cuatro cosas: **artefacto** en la rama, **verificación ejecutada y declarada** (comando y salida real, o el motivo de no haberla ejecutado), **relevo publicado** con lo pendiente, y **entrega por PR**. Un leg que solo produce conversación no está cumplido, aunque el trabajo intelectual sea bueno.

## Agente local

Antes de cerrar la aplicación o apagar el ordenador:

1. guarda cambios coherentes;
2. ejecuta las comprobaciones posibles;
3. crea commit de checkpoint;
4. haz push de la rama;
5. deja el bloque `HANDOFF` en el issue o PR;
6. cambia el estado a `paused-local` si la tarea no terminó.

Si existen cambios locales sin push, la tarea no es recuperable por el equipo.

## Agente cloud

- No asumas acceso a archivos locales, aplicaciones autenticadas o dispositivos.
- No solicites que se suban datos `local-only` para desbloquearte.
- Si la tarea depende de material local, deja el bloqueo y propone una partición segura.
- Publica commits y PR aunque la sesión cloud prometa conservar memoria.

## Propiedad y relevo

Una tarea tiene una sola escritora activa. El relevo exige:

- checkpoint publicado;
- bloque `HANDOFF`;
- cambio visible de propietaria;
- confirmación de la nueva agente antes de escribir.

La nueva agente continúa en la misma rama cuando el trabajo es lineal. Abre otra rama cuando vaya a competir con una solución anterior.

**Límite declarado:** si todas las agentes actúan bajo la misma cuenta de plataforma, la propiedad es **declarativa, no verificable**, y la firma del commit es el único rastro comprobable. Fírmate con identidad propia (`<Nombre> <nombre@<proyecto>.local>`) y no trates la asignación como prueba.

## Handoff

```text
HANDOFF
Estado: working-local | working-cloud | paused-local | blocked | review
Agente saliente: <nombre y arnés>
Entorno: local | cloud
Rama: <rama real, aunque no siga el patrón>
Último commit: <sha>
Hecho: <resultado verificable>
Comprobado con: <comandos, tests o revisión>
No comprobado: <qué y por qué>
Pendiente: <trabajo concreto>
Datos necesarios: repository | cloud-ok | local-only | synthetic-only
Siguiente acción: <acción ejecutable>
Siguiente propietaria: <agente o sin asignar>
```

El par **Comprobado con / No comprobado** es lo que de verdad sostiene el relevo: el primero es reproducible, el segundo dice a la entrante dónde mirar. No los dejes vacíos.

## Quién integra

**El par de cada proyecto integra el trabajo de su proyecto cuando el merge es rutinario.** No hace falta que lo pulse la dirección ni un tercero: quien conoce el terreno es quien mejor ve si el trabajo está listo, y esperar a otra persona serializa el trabajo sin comprar seguridad.

**No es rutinario, y por tanto escala a la dirección:**

- lo que cruza la membrana: publicar, desplegar, enviar, gastar;
- lo que cambia reglas duras del proyecto o doctrina;
- **lo que toca las comprobaciones o los permisos** (CI, validadores, protección de ramas, secretos): quien controla los checks controla toda la verificación futura;
- lo que barre medio repositorio de una vez.

Y una regla que vale más que la lista, porque la lista nunca está completa: **ante la duda, pregunta.** Preguntar es gratis y no es un reproche; integrar con dudas sí tiene coste, y lo paga el que viene detrás.

## Cierre

El PR incluye alcance, evidencia, limitaciones, impacto sobre Mycelia y pendientes. La tarea termina al integrarse el PR o al cerrarse explícitamente el issue, no cuando una agente dice que ha acabado.

**Un issue con relevo vivo no se cierra.** `Closes #N` solo cuando el criterio de aceptación está completo: si tu PR cubre una parte y el `HANDOFF` deja "Siguiente acción" sin ejecutar, entrega **sin** `Closes` y deja el issue abierto. Si te encuentras un issue **cerrado con relevo vivo** (pasa cuando un merge parcial lo cerró), reábrelo; si no puedes, entrega sin `Closes`, enlaza el issue y dilo en la entrega. Que la plataforma lo marque cerrado no significa que el trabajo esté terminado.
