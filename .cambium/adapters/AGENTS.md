<!-- Codex y opencode leen este archivo como AGENTS.md en la raiz del proyecto.
     Es el UNICO fichero del metodo que va en la raiz; el resto vive en .cambium/.
     Copia este archivo a la raiz y rellena <PROYECTO> y <tu-nombre>.
     Cuerpo identico en los 4 adaptadores (CLAUDE/AGENTS/GEMINI/.cursorrules): editalos juntos. -->

Eres parte del equipo de <PROYECTO>. Método: Cambium Charter (instalado en .cambium/).

Antes de actuar:
- Lee .cambium/CHARTER.md y tu docs/equipo/<tu-nombre>_role.md.
- Reglas que no se rompen: .cambium/REGLAS.md.

Al despertar (latido manual o programado) — y SIEMPRE al empezar cualquier sesión o turno:
- git pull → mira tu COLA en bitacora/next.md → trabaja la primera tarea pendiente → abre PR.
- Tu asignación vive en next.md, NO en el chat: míralo aunque no haya llegado un latido (el latido solo acelera).
- Si no hay tarea pendiente: no-op silencioso (no escribas en el repo, no inventes trabajo).
- Si el despertar FALLA (no puedes hacer pull, repo/CI inaccesible): deja ruido (issue/bitácora), nunca en silencio.
- Si tu tarea es "adopta Cambium Charter vX.Y": pull → relee .cambium/CHARTER.md y tu role.md → adopta lo que toque → confirma por escrito (bitácora/commit "adoptada vX.Y"). Es una tarea de cola normal.

Siempre:
- Quédate en tu jurisdicción; fuera de ella: «Handoff a: <agente>» en la bitácora, no edites.
- El repo es la verdad · el PR es tu entrega · identity-inline en cada commit.
- Si una fuente falla, no inventes; el "no" es una respuesta válida.
- El repo se referencia por su URL; nunca escribas rutas locales (C:\…, /home/…) en ficheros versionados.
