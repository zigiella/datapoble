# Traspaso de coordinación — <saliente> → <entrante> · AAAA-MM-DD

> El relevo es RECONSTRUCCIÓN (ritual de §III) + RATIFICACIÓN de la humana + CAMBIO DE LLAVE.
> Es atómico: antes del commit de ratificación manda la saliente; después, la entrante.
> Nunca dos autoridades de merge a la vez (invariante 2). Cero secretos aquí: punteros, no valores.

## 1. La saliente deja el repo al día (último acto con la llave)
- [ ] Cola de `bitacora/next.md` actualizada y coherente.
- [ ] Decisiones vivas y por qué (con ancla a ADR/PR/commit).
- [ ] Cicatrices y trampas conocidas.
- [ ] Qué NO está hecho y por qué (honestidad, invariante 6).
- [ ] Punteros a lo sensible (los secretos los sostiene la humana, invariante 1).
- [ ] Si versiona memoria: `.cambium/memoria/coordinadora.md` commiteada y saneada.

## 2. La humana ratifica (invariante 1 — voto final)
- [ ] <humana> aprueba el relevo y nombra a <entrante> coordinadora.
  (Commit firmado por la humana. Sin esta marca NO hay relevo; ese commit es el instante exacto.)

## 3. La entrante se reconstruye DESDE EL REPO (no del chat)
- [ ] Adaptador en la raíz → `.cambium/CHARTER.md` + `REGLAS.md` → su `role.md` →
      última bitácora + `bitacora/next.md` (+ `.cambium/memoria/` si existe).
- [ ] Verifica CI/verificación verde y cola coherente.
- [ ] Confirma por escrito: commit "asumo la coordinación".

## 4. La llave cambia de manos (trazable, exclusiva)
- [ ] La saliente DEJA de mergear desde el commit de ratificación.
- [ ] Si el forge lo permite (Artículo 3): mover el permiso de merge de <saliente> a <entrante>
      en las reglas de protección de rama (prueba dura).
- [ ] Si no: la llave es por disciplina; el commit de ratificación de la humana es el acta.
- [ ] (Recomendado) la entrante audita lo que la saliente mergeó sin auditor independiente (Art. 5).
