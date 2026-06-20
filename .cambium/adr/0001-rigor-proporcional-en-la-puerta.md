# ADR-0001 — Rigor proporcional en la puerta

- **Estado:** aceptada (sellada en Cambium Charter v0.4)
- **Fecha:** 2026-06-18
- **Autora:** Verabif (custodia del kit). Ratifica Bea (dirección humana).

## Contexto

La puerta (Artículo 3, invariante 2) era de **altura uniforme**: todo cruza por rama → PR → CI → merge, y solo la coordinadora mergea, nunca a `main` directo. Pero el riesgo de lo que cruza **no** es uniforme, y tres coordinadoras en producción lo expusieron tras adoptar v0.3:

- **Vera (caso-vivo)** hizo ~40 ciclos rama→PR→CI→merge para actualizar `next.md` y bitácoras —**ceremonia sin protección**: son sus propios artefactos no-código, que el CI no verifica de forma útil—. Y a la vez lleva ~76 PRs siendo **juez y parte** (revisa y mergea a su propio equipo, sin adversario independiente) mientras el producto va a servir **citas legales a ciudadanos**: ahí el Artículo 5 ("separar auditor de guardián **antes de producir**") llega tarde.
- **Talaia (Riusdegent)**, coordinadora-autora-portera a la vez, nombró el mismo hueco: la "verificación independiente" se reduce a ella + el CI.

El patrón: la puerta cobraba **demasiado abajo** (lo trivial) y **demasiado poco arriba** (lo regulado). Una sola altura no sirve.

## Decisión

Evolucionar el Artículo 5 "consciente de coste" a **rigor proporcional al riesgo**: barato lo barato, caro lo caro. Tres movimientos (el Art. 3 lo enuncia; §IV y el Art. 5 lo detallan):

1. **Fast-path no-código.** La coordinadora puede commitear **directo a `main`** sus propios artefactos de coordinación que no son código (`next.md`, bitácoras, `.cambium/memoria/`). Sigue siendo la puerta: identity-inline + verificación cero-secretos/cero-rutas **obligatoria aunque no haya CI**. **Tres líneas rojas:** nunca código, nunca doctrina/`.cambium/`, nunca jurisdicción ajena. En la duda, por la puerta completa.
2. **Mordida temprana.** Para la **clase regulada** (citas legales, plazos, importes; declarada **estrecha** en `REGLAS.md`), el auditor revisa fuente y cita **antes de que la afirmación se fije en `main`**, no sobre el artefacto ya publicado.
3. **Delegación acotada del merge.** Si el volumen de PRs de bajo riesgo lo exige, el merge de una clase acotada (p. ej. `docs/**`) puede **particionarse** a otra agente.

**Reconciliación con el invariante 2** (la pieza que justifica este ADR): la delegación **no crea una segunda llave**. Es la **jurisdicción única (invariante 5) aplicada al merge** —ningún PR tiene dos autoridades a la vez; la delegada es la única que mergea su clase y la coordinadora no toca esa clase—. Es **registrada por commit-acta y ratificada por la humana** (como el relevo de §VIII), **revocable**, **no transitiva**, y la delegada **nunca audita lo que mergea** ni es de despertar programado. Si la clase tuviera que crecer hacia código o doctrina, ya no es delegación: es relevo (§VIII).

**Lo que nunca flexiona:** el código, la doctrina/`.cambium/` y la jurisdicción de otra agente cruzan la puerta completa **siempre**; identity-inline y "sin secretos / sin rutas locales" se aplican en **todas** las alturas. Aligerar la ceremonia no es abrir un agujero a `main`.

## Consecuencias

- Mata la ceremonia-sin-protección de los artefactos de coordinación (la cicatriz de Vera).
- Da una respuesta honesta al juez-y-parte en producto regulado **sin** montar un auditor permanente (que sería el antipatrón "por-acción" que el propio Art. 5 prohíbe).
- **Riesgos aceptados conscientemente** (los señaló la verificación adversarial del diseño de v0.4):
  - La frontera "no-código" **depende del proyecto** (un `.md` es código si un build lo ejecuta). Mitigado con "en la duda, por la puerta" + `REGLAS.md` lista qué cuenta como no-código. No resoluble en el esqueleto.
  - La clase regulada **debe mantenerse estrecha** o reintroduce el auditar-casi-cada-acción. Es disciplina, no candado.
  - **§IV se densifica** (es ya la sección más larga de la carta). A vigilar en v0.5 que no se vuelva cajón de sastre.
  - La delegación queda como **principio** en el esqueleto, con el detalle operativo en `REGLAS.md`/`EJEMPLOS.md`; un equipo de tres rara vez la necesita.

## Alternativas descartadas

- **PR-para-todo-siempre (statu quo).** Cobra ceremonia sin protección a los artefactos no-código de la coordinadora y deja la auditoría regulada para "antes de producir", que llega tarde.
- **Mantener "una sola llave" de forma literal (nunca delegar).** Condena a la coordinadora a juez-y-parte en producto regulado de alto volumen. La **partición** preserva el principio real (una autoridad por PR) sin esa rigidez.
- **Auditor independiente permanente.** Coste por-acción: el antipatrón que el Art. 5 ya prohíbe. La mordida **por-riesgo** + la verificación **cruzada** lo cubren a su cadencia.
- **Aligerar la puerta también para código de bajo riesgo.** El código cruza la puerta completa siempre — es la línea roja que mantiene el fast-path honesto.
