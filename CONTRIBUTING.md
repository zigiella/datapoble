# Contribuir a datapoble — manual operativo del equipo

Método de coordinación multiagente (adoptado del oficio Cambium / TRANSFER_KIT). Detalle ampliado en `docs/team-method.md`.

## 1. Roles y jurisdicción
Cada agente decide **en su frente** y escala lo que cruza frentes. Nadie edita código fuera de su zona sin *handoff*. Talaia coordina e integra; **Bea tiene el voto narrativo final** (marca, copy, qué se publica).

| Frente | Agente | Zona |
|---|---|---|
| Datos / pipeline | Sondeig | `packages/ingestion`, `packages/transform` |
| IA / semántica | Brúixola | `packages/ai`, `semantic/` |
| Frontend | Mirador | `packages/web` |
| Arte | Llegenda | `packages/design-system` |
| Coord + investigación | Talaia | `docs/`, `semantic/` (contrato), integración |

## 2. Git
- **Nunca trabajar sobre `main`.** Ramas: `feat/<agente>-<tema>`, `fix/…`, `docs/…`.
- **Identity-inline en cada commit** (clone/worktree compartido):
  ```bash
  git -c user.name="Talaia" -c user.email="talaia@datapoble.local" commit -m "..."
  ```
  Nunca `git config --global`. Tabla de identidades en `docs/team-method.md`.
- **Triple-verify pre-commit:** `git status` + `git branch --show-current` + `git stash list`.
- Stash con prefijo `[agente]`. Nada de `push --force` a `main`. Nada de `--no-verify` sin permiso de Bea.
- **Worktrees por agente** (un `.git`, una carpeta+rama cada una).

## 3. PRs
- PR contra `main` con `Closes #N`. **Ningún merge con CI en rojo.** Talaia es *gatekeeper* de `main`.
- Review como conversación, con cita concreta. Sin sycophancy. Lo narrativo se escala a Bea.

## 4. Bitácora-as-contract
Las decisiones viven en `bitacora/YYYY-MM-DD_<tema>_<agente>.md`, no en el chat. **Si chat y bitácora divergen, gana la bitácora.** No se borran (evidencia de proceso). Plantilla en `bitacora/README.md`.

## 5. Idiomas
- Interfaz del producto: **ca + es** siempre; **en + fr** ampliables.
- README/CONTRIBUTING: bilingüe ca/es. `docs/`: canonical ca **o** es. `bitacora/`: libre ca/es. Commits/issues/PRs: libres.

## 6. Honest boundaries
Cada claim marca categoría: **validado** / **contrato demostrado** / **roadmap**. Nunca "soporta X" sin matiz. Los resultados negativos se publican.

## 7. Lo que NO va al repo
Secretos (la key de OpenRouter es un secreto), binarios >50 MB (→ Releases), scratch personal (`CAJON/`, `_scratch/`).
