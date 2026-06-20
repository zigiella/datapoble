# ADR-0002 — Des-duplicación del Artículo 5 y adversario para equipo auto-coordinado

- **Estado:** aceptada (sellada en Cambium Charter v0.5)
- **Fecha:** 2026-06-18
- **Autora:** Verabif (custodia del kit). Ratifica Bea (dirección humana).

## Contexto

`adr/0001` (rigor proporcional en la puerta, sellado en v0.4) introdujo el detalle de la mordida temprana y de la delegación acotada del merge **directamente en el Artículo 5** de la carta. El resultado: el Art. 5 llegó a ~366 palabras —la sección más densa de la carta junto a §IV—, dejando de caber en una sola lectura, contra el presupuesto de tamaño del Preámbulo (Minimalismo). `adr/0001` ya anotó en Consecuencias que la delegación quedaba como **principio** en el esqueleto con su detalle operativo destinado al cuerpo, y marcó la densificación como riesgo a vigilar en v0.5. Verificado leyendo `adr/0001` (Decisión puntos 2 y 3 + Reconciliación con el invariante 2): la justificación expandida de la mordida y las condiciones de la delegación (registrada por commit-acta, ratificada, revocable, no transitiva, nunca audita lo que mergea, no programada, crecer-a-código = relevo) **ya viven íntegras allí** —están duplicadas en la carta.

Segundo hueco, independiente: el fallback de adversario del Art. 5 ("en equipo mínimo lo asume la dirección humana o una agente rotada") **no cubre la configuración auto-coordinada (sin cable humano, §III-a)**: cuando no hay ni humana disponible ni una segunda agente, la coordinadora quedaba como juez y parte silencioso, justo lo que el invariante 6 y el Art. 5 ("separar auditor de guardián antes de producir") quieren evitar.

## Decisión

v0.5 es un **release de adelgazamiento**. Dos movimientos sobre el Artículo 5, en la línea principio/implementación de `adr/0001`:

1. **Des-duplicación (carta → `adr/0001`).** Se retira del Art. 5 el detalle ya residente en `adr/0001` (la justificación expandida de la mordida y la mecánica de la delegación), dejando en el esqueleto sólo: el **principio-frase** de cada uno, la **clase regulada estrecha** y la **partición = jurisdicción única (invariante 5) aplicada al merge**. El Art. 5 baja de ~366 a ~286 palabras. **No es recorte: es recolocación** —`adr/0001` pasa a ser la ubicación canónica viva del detalle, no un documento meramente histórico. Lo que **permanece como esqueleto** (no se recoloca): las **cuatro líneas rojas** de la delegación (nunca código, nunca doctrina/`.cambium/`, **nunca la mordida regulada**, nunca la jurisdicción de otra agente), la cláusula **"ningún PR tiene dos autoridades a la vez"** (invariante 2) y **"ratificada por la humana"** (invariante 1, en simetría con §VIII que conserva su ratificación in-charter). La verificación adversarial detectó que "nunca la mordida regulada" **no figura en `adr/0001`**: sacarla de la carta la habría dejado sin casa (vaciar, no recolocar), así que se conserva en el esqueleto.

2. **Adversario para equipo auto-coordinado.** Se añade media frase al fallback del Art. 5: sin humana ni agente rotada, el rol de adversario lo asume una **copia fresca y sin contexto de la propia coordinadora, que verifica y NO mergea**, **por-riesgo antes de salida irreversible**. Es el fallback-del-fallback del invariante 6 en configuración degenerada, no un segundo rol permanente ni una segunda coordinadora: sigue habiendo **exactamente una autoridad de merge** (invariante 2). No cae en el antipatrón "auditar cada acción" (§V): es por-riesgo, no por-acción. El detalle operativo (disparador, guion del turno de la copia fresca, garantía de aislamiento de contexto) vive aquí y en `EJEMPLOS.md`, no en el esqueleto.

## Consecuencias

- El Artículo 5 vuelve a caber en una lectura; v0.5 cumple su mandato de adelgazamiento (carta neta más pequeña).
- `adr/0001` queda confirmado como **ubicación viva** del detalle del Art. 5: la carta lo apunta, no lo repite. El CHANGELOG v0.5 lo registra para que no se lea como histórico.
- El equipo auto-coordinado (§III-a) gana contrapeso adversarial real en vez de juez-y-parte silencioso.
- **Riesgos aceptados conscientemente:**
  - El aislamiento de la "copia fresca" depende de la herramienta: si no puede instanciar una sesión limpia sin heredar contexto, la independencia del adversario es nominal. Condición operativa fijada aquí, no en el esqueleto.
  - "Salida irreversible" debe mantenerse **estrecha** o reintroduce el auditar-casi-cada-acción —misma disciplina, no candado, que la clase regulada de `adr/0001`.
  - **GATE de release:** la media frase del Art. 5 no puede sellarse sin este ADR en el mismo cambio, o el esqueleto apuntaría a un fichero inexistente (el repo es la verdad, invariante 3).

## Alternativas descartadas

- **Dejar el detalle duplicado en el Art. 5 (statu quo v0.4).** Mantiene el artículo por encima de una lectura y duplica lo que ya está en `adr/0001`.
- **Recolocar también las líneas rojas y "ratificada por la humana" a `adr/0001`.** Sería vaciar el esqueleto: las líneas rojas (invariantes 2 y 5) y la ratificación (invariante 1) aterrizan invariantes y deben vivir en la carta, en simetría con §VIII. Verificado además que "nunca la mordida regulada" ni siquiera existe en `adr/0001`.
- **Una copia fresca que además mergea ("es la misma coordinadora").** Rompería el invariante 2 (exactamente una autoridad de merge). El "verifica y NO mergea" lo cierra.
- **Partir el Art. 5 en 5a/5b o crear un sexto artículo.** Contra el minimalismo: el principio cabe des-duplicado en un solo artículo.
