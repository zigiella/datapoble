# Capa generativa · especificació d'infra — per conversar amb la Trazo

**Handoff a: Trazo (IT).** La Talaia especifica què necessita l'arnès generatiu; la decisió i el cablatge d'infra són de la Trazo. El repo és **públic**: cap secret hi pot entrar mai.

> **Correcció (2026-07-03, #229):** la primera versió d'aquesta spec citava `claude-sonnet-4-6` com a generador, «verificat» contra una taula **cachejada del 2026-06-04**. La Trazo va verificar **en viu** i tenia raó: `claude-sonnet-5` és el Sonnet actual (Sonnet 4.6 ja és *legacy*). Lliçó registrada: quan dues verificacions xoquen, mana la font viva — la pròpia verificació també caduca.

## Què s'ha de poder fer

Cridar **dos models d'LLM per API** des de `packages/geo-rag`, en local (mai al CI per-PR):
1. **Generador** — redacta la resposta sobre el context recuperat (estocàstic, N=5 passades per pregunta).
2. **Validador cec** — un segon model que rep pregunta + dada + resposta final (mai el raonament del generador; **crida separada, context aïllat**) i comprova to/caveats.

## Tria de models (proposta de Talaia, verificada)

| Rol | Model (ID exacte) | Preu (in/out per MTok) | Per què |
|---|---|---|---|
| Generador | `claude-sonnet-5` | intro **$2 / $10** fins 31-08-2026, després $3 / $15 | El nivell realista d'un «Pregunta-li» de producció: el Sonnet **actual** (4.6 ja és *legacy*). Mesurar el cost de la fluïdesa sobre un model que de debò faríem servir. Mostreig per defecte (estocàstic; N=5 el captura). |
| Validador cec | `claude-haiku-4-5` | $1 / $5 | **Model diferent** del generador (menys punts cecs correlacionats — «dos models dient-se que sí» es mitiga amb ceguesa + diversitat), barat per a volum, i corre a `temperature=0` (jutge consistent; els models 4.5/4.6 encara accepten `temperature`). |

*Alternativa anotada, no preregistrada:* repetir la passada amb `claude-opus-4-8` ($5/$25) com a generador «premium» seria una segona condició interessant per al paper, però NO es fa ara (multiplicar condicions abans de tenir el primer delta és soroll).

## Volum i cost estimat (honest, amb marge)

- **Passada oficial:** 34 Q × 5 passades = **170 crides de generació** (~2–3,5k tokens d'entrada per crida: prompt congelat + pregunta + context recuperat; ~300–500 de sortida) + **170 crides de validació** (~2k in / ~150 out). ≈ 0,5–0,8 M tokens d'entrada + ~0,1 M de sortida en total → **~2–3 $** la passada oficial amb el preu intro de Sonnet 5 (~3–5 $ amb el preu ple).
- **Desenvolupament del prompt** (dev set ~12 Q × ~10 iteracions): **~3 $**.
- **Total experiment generatiu: < 15 $** amb marge. El cost no és el factor; la governança de la clau sí.

## Governança de la clau (el punt seriós)

- `ANTHROPIC_API_KEY` com a **variable d'entorn local** (o `.env` FORA del repo / ignorat). **Mai** al repo (públic), mai als logs, mai als artefactes commitejats.
- **El CI per-PR no toca l'API**: el job `geo-rag` segueix offline. Els tests que necessiten API es guarden amb un guard d'entorn (skip si no hi ha clau), com el `importorskip("torch")` dels embeddings.
- **La passada oficial és local** i el que es versiona són els **artefactes**: el log per-trial (JSON) i l'informe — com `fase3-resultat.txt`. Els *raw responses* complets a un directori gitignorat.
- SDK: `anthropic` (Python) — Trazo decideix el pinning i si va com a extra opcional del paquet (p. ex. `[generativa]`), seguint la mateixa política que l'extra `[embeddings]` (#218).

## Preguntes per a la Trazo

1. **Clau:** com la proveïm a la màquina (env de sessió, `.env` ignorat, gestor de secrets)? Qui la custodia i la rota?
2. **Extra opcional** `[generativa]` a `packages/geo-rag/pyproject.toml` amb `anthropic` pinnat — mateixa filosofia que `[embeddings]`?
3. **Confirmació** que el job de CI continua offline i que cap workflow del repo públic pot filtrar la clau (cap secret de GitHub Actions per a això — no cal).
4. **Límits:** el volum és trivial (~340 crides/passada) — el retry per defecte de l'SDK (2) és suficient; cap infraestructura addicional.

## Aïllament del validador (requisit d'arquitectura, no d'infra)

La crida del validador **no comparteix conversa ni context** amb la del generador: crida nova, prompt propi, i rep NOMÉS {pregunta, dada del substrat, resposta final}. La ceguesa al raonament és el que el fa validador (contracte 08).
