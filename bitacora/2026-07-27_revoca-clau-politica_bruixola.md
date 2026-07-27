# 2026-07-27 — Revoca la clau política (P-POL) · Brúixola

**Decisió de Bea (vinculant, 2026-07-27):** *«Revocar la clau. Tot el que és vot
polític va fora.»* Fins ara la dimensió `politica` (`mart_electoral`) estava
**retinguda però amb una clau de runtime** (`AI_POLITICS_UNLOCK` → `PoliticsGate`;
`KEYED_DIMENSIONS = {politica}`). Bea revoca la clau del tot: cap paraula secreta,
cap variable d'entorn, cap via ha de poder tornar a servir una mètrica de vot.

Jurisdicció: **només `packages/ai/`**. `semantic/metrics.yml` NO tocat (és de
Talaia; deprecar l'electoral al contracte seria un error de disseny — vegeu la
subtilesa més avall). `packages/geo-rag/`, `packages/signals`, web i dades: intactes.

## Decisió d'implementació: ELIMINAR, no inertitzar

Seguint la preferència de Talaia al brief (*«eliminar-los, perquè no quedi cap
clau latent»*), he **eliminat** tot el mecanisme en comptes de deixar-lo inert.
El cablejat era mecànic i verificable en local; deixar-lo inert hauria deixat una
clau dormint. Ara no existeix cap `PoliticsGate`, cap `KEYED_DIMENSIONS`, cap
`AI_POLITICS_UNLOCK`: no hi ha res que activar.

## Què he eliminat

- **`politics.py`**: fora `PoliticsGate` sencer (`from_env`, `is_unlocked`,
  `strip_unlock`, `has_unlock_configured`, `_unlock_pattern`, `_contains_unlock`),
  la constant `UNLOCK_ENV_VAR` i els imports `os`/`re`/`normalize` que en depenien.
  **Conservat:** `POLITICS_DIMENSION` i `is_political_metric` — el predicat que
  dispara el refús discret. El mòdul queda en ~10 línies efectives.
- **`catalog.py`**: fora `KEYED_DIMENSIONS`, la propietat `Metric.is_keyed` i el
  mètode `Catalog.keyed_metrics()`. `tables()` ara serveix només
  `available_metrics()` → `mart_electoral` **surt de l'allow-list de SQL** (com ja
  hi era `mart_demografia`/`origen`). Cap camí de SQL pot tocar un mart de vot.
  `politica` es queda a `HELD_BACK_DIMENSIONS` → **retinguda INCONDICIONAL**, com
  `origen`. Docstrings actualitzats amb la decisió de Bea.
- **`router.py`**: fora l'atribut `politics_gate`, el mètode `_is_eligible` i el
  paràmetre `include_keyed` (de `match_metric` i `_matched_metrics_by_position`);
  fora el paràmetre `unlocked` de `parse()`, `ask()` i `execute_intent()`. Els
  matchers tornen a filtrar per `metric.is_available()` net.
- **`llm.py`**: fora el bloc de desbloqueig a `ask()` (llegir la clau + `strip`),
  i el paràmetre `unlocked` de `parse`/`execute_intent`/`_dispatch`.
- **`__init__.py`**: `PoliticsGate` fora de l'API pública (import + `__all__`).
- **`README.md`**: fora la fila `AI_POLITICS_UNLOCK` de la taula d'env vars i tota
  la secció *Team unlock*; la secció *Political gate* ara diu que la clau és
  revocada i que `politica` és retinguda incondicional.
- **`i18n.py`**: tret el comentari «(Còpia pendent del vot narratiu de Bea.)» de
  `refusal_deprecated` — ratificada per Bea (2026-07-27), com deia el brief.

## Com s'ha CONSERVAT el refús discret (la subtilesa crítica)

Hi ha DOS refusos i només un és segur per a una pregunta de vot:
- **discret** (`refusal_political_gated`, `POLITICAL_GATED`): *«Aquest observatori
  no respon preguntes sobre orientació de vot.»* — no anomena res.
- **de mètrica retirada/pendent** (`refusal_deprecated` / `refusal_planned`):
  **ANOMENA** la mètrica.

Una mètrica `politica` és **retinguda** (`is_held_back` → `is_available()==False`),
mai `deprecated`. El camí per a una pregunta de vot és:
1. `match_metric` no la considera (retinguda) → `None`.
2. `_match_any_metric` la troba; `is_available()==False`.
3. `is_political_metric(any_metric)` → **`POLITICAL_GATED` (discret)** *abans* de
   `_unserved_reason` (que l'anomenaria).

I a `execute_intent` la guarda `is_political_metric` corre **incondicionalment i
ABANS** de la re-comprovació de disponibilitat, així que una mètrica de vot
resolta (p. ex. via el backend LLM) també pren la porta discreta, mai la que
l'anomena. Per això **NO s'ha tocat `semantic/metrics.yml`**: deprecar l'electoral
allà faria caure la pregunta de vot al refús que ANOMENA la mètrica → filtraria la
seva existència. El mecanisme correcte és retingut incondicional + clau revocada.

## Guarda de regressió nova

`tests/test_politics.py` reescrit. Retirats els tests que asserten que la clau
OBRE (unit del `PoliticsGate`, `test_unlock_word_lets_vote_question_through`,
`test_openrouter_backend_unlocks_with_word`, etc.). Afegit:
- `test_env_var_cannot_unlock_a_vote_question` — posar `AI_POLITICS_UNLOCK` (i
  incrustar la vella paraula) NO obre res: refús discret, sense query, sense
  anomenar la mètrica ni fer eco de la paraula.
- `test_the_key_machinery_no_longer_exists` — **cap clau latent**: `PoliticsGate`,
  `UNLOCK_ENV_VAR`, `KEYED_DIMENSIONS`, `keyed_metrics`, `Metric.is_keyed` han de
  ser inexistents. Si tornen, el camí que serveix un vot rere una paraula torna
  amb ells i aquest test cau primer.
- `test_electoral_mart_is_out_of_the_sql_allow_list` — cap camí de SQL toca el mart
  de vot.
- `test_vote_question_is_always_gated` / discreció ca+es (assert que «planned» i
  «deprecat» NO apareixen mai al text).
- `test_catalog.py`: `test_both_held_back_dimensions_are_unconditional` (les dues
  dimensions són ara la mateixa porta, sense clau); `mart_electoral` **fora** de
  `tables()`.
- `test_narrator.py`: invertit el test del vot (amb la clau morta el vot es
  refusa, cap model escriu prosa) + `test_narrator_refuses_to_dress_a_political_answer`
  (defensa en profunditat: la guarda pròpia del narrador es manté encara que el
  flux normal ja no hi arribi).
- `test_router.py`: el test que arribava a la resposta política via la clau ara
  verifica que el caveat de `pct_indep` MAI arriba al lector (està cobert per a
  mètriques d'inferència no polítiques a `test_doctrine.py`).

## Verificació LOCAL (el CI no corre fins el dia 1)

- `pytest` complet de `packages/ai`: **218 passed** (21 a `test_politics.py`).
- `ruff check .`: **All checks passed!**
- `ruff format` NO és la porta del projecte (26/32 fitxers, inclosos els que no he
  tocat, «would reformat»); la porta de lint (`ruff check`) és verda.
- Diff confinat a `packages/ai/` (11 fitxers). `semantic/metrics.yml` intacte.

## Premisses del brief i notes de mètode

- **Cap premissa del brief era falsa.** Les línies del router citades (`is_political_metric`
  ~L328-339, `deprecated` ~L379) i l'existència de `include_keyed`/`PoliticsGate`/
  `KEYED_DIMENSIONS` eren exactes.
- **⚠️ Nota de mètode confirmada (avís del brief):** l'install editable de
  `datapoble_ai` apunta al worktree d'un ALTRE agent (`agent-ac46a8c30778e0b6a`),
  no al meu. Les sondes ad-hoc `python -c` importen d'allà. **`pytest` NO hi cau**
  (`pythonpath=["src"]` al `pyproject` prepèn el MEU `src`) — ho he verificat
  explícitament abans de fiar-me de cap resultat. Tota la verificació d'aquest PR
  és contra el meu worktree.

## Handoff

- **➡️ Mirador** (ja encuat abans, segueix vigent): a `packages/web/src/lib/ask/api.ts`
  la unió `RefusalReason` no té `political_gated` ni `metric_deprecated` → cauen al
  `default` genèric. Degrada bé, però el refús discret perd el seu to. No és
  jurisdicció meva.
