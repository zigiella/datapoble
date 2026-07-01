# Embeddings de la Fase 0b — especificació d'infra (local vs API)

**Handoff a: Trazo (IT).** La Talaia especifica què necessita el paquet `packages/geo-rag`; la decisió i l'execució de l'infra són de la Trazo. Fets verificats a la web/màquina el 2026-07-01 (fonts al final). Bea vol el teu criteri abans d'instal·lar res.

## Què necessita la Fase 0b

Generar **embeddings de ~31 descripcions curtes en català** (una per municipi del Berguedà) per fer cerca semàntica, i guardar-los al substrat DuckDB (`packages/geo-rag`). Corpus minúscul; el coll d'ampolla no és el volum sinó **dues restriccions dures** que decideixen la tria:

1. **Sub-experiment estrella (σ real vs σ d'embeddings):** cal **MC-Dropout** — activar les capes de dropout en inferència, fer ~10 passades estocàstiques i prendre la desviació del cosinus. **Cap API allotjada ho permet** (només exposen «text → vector» determinista, sense mode-train ni σ per embedding). És un fet arquitectònic, no de preu.
2. **CI offline + reproduïble sense secrets:** el repo és públic i compromet artefactes deterministes. Una API necessita clau (no pot anar al repo) i crida de xarxa a cada execució → trenca el CI offline i introdueix risc de deprecació del model sota nostre.

Totes dues apunten a un **model local**. L'API queda com a *baseline* opcional de comparació de qualitat, res més.

## Opció A — stack LOCAL (recomanada)

**Paquets** (via `sentence-transformers`): arrossega `torch`, `transformers`, `huggingface-hub`, `tokenizers`, `numpy`, `scipy`, `scikit-learn`, `safetensors` (+ regex, pyyaml, requests, filelock, fsspec, joblib, pillow…).

**Footprint** (verificat des de PyPI):
- `torch` és el gros: **123,0 MB de descàrrega** (`torch-2.12.1-cp312-cp312-win_amd64.whl`; el wheel per defecte de PyPI a Windows **ja és CPU-only**, sense CUDA).
- Stack sencer: **~200–300 MB de descàrrega**, **~600 MB–1 GB en disc** (la xifra en disc de torch és estimació, no verificada a la font).
- Pesos del model: descàrrega **a part** al primer ús (~0,45 GB per al model recomanat), a la cau de HuggingFace.

**Instal·lació** (fixar versions per reproduïbilitat):
```
# el wheel per defecte de Windows ja és CPU; ruta explícita per garantir-ho:
pip install torch==2.12.1 --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers
```
(Usar `--index-url`, no `--extra-index-url`.)

**Particularitats de Windows** (ja resoltes en aquesta màquina, verificat):
- Rutes llargues: `LongPathsEnabled = 0x1` ✅ (ja actiu). Python **3.12.4** ✅. `.venv` normal (no Microsoft-Store) ✅.
- `torch` necessita el **VC++ Redistributable 2015–2022 x64** (habitual a Win11; només si `import torch` falla amb error de DLL).

**Model recomanat:** `intfloat/multilingual-e5-small` — MIT · **384 dim** · 117,7M paràmetres · ~0,45 GB · bi-encoder · català via preentrenament multilingüe (XLM-R/MiniLM) · CPU-friendly. Convenció de prefixos `query:` / `passage:` en codificar.
- **Alternativa més potent** si la qualitat en català es queda curta: `BAAI/bge-m3` (MIT, 1024 dim, ~560M, ~2,2 GB, context 8192) o el punt mig `intfloat/multilingual-e5-base` (768 dim, 278M, ~1,1 GB).
- **Descartat:** no hi ha embedder «drop-in» del **BSC/projecte AINA** — els seus models en català són o bé bases MLM (sense cap de pooling) o bé cross-encoders STS (no donen vectors reutilitzables). Caldria fine-tuning. `paraphrase-multilingual-MiniLM-L12-v2`: el català **no** és a la seva llista oficial de 50 llengües → deprioritzat.

**MC-Dropout** (per a l'estrella): posar el model en `eval()`, reactivar només les capes `Dropout` a mode train, ~10 passades amb `no_grad`, mitjana/desviació del cosinus. Funciona amb qualsevol dels models de dalt (encoders BERT/RoBERTa amb dropout p>0 — **verificar** que el config no porti p=0, o la σ sortiria nul·la).

**Determinisme:** fixar versions + llavor; els embeddings *base* (dropout off) es codifiquen deterministes i es poden commitejar com a artefacte de CI; les passades MC-Dropout són estocàstiques a propòsit (fixar `torch` seed per repetibilitat).

## Opció B — API allotjada (només com a *baseline* opcional)

Cost per a 31 docs: **negligible** (cèntims) → el cost **no** és el factor decisiu. Els factors decisius (MC-Dropout impossible + clau/xarxa + deprecació) sí que ho són.

| Proveïdor | Model | Dim | Preu /1M tok (aprox., verificar) | Català |
|---|---|---|---|---|
| Voyage (recomanat per Anthropic) | voyage-3.5-lite / voyage-multilingual-2 | 1024 | ~$0,02 / ~$0,12 (50M gratis) | sí |
| OpenAI | text-embedding-3-small / -large | 1536 / ≤3072 | ~$0,02 / ~$0,13 | sí |
| Cohere | embed-multilingual-v3.0 | 1024 | ~$0,12 (línia Embed 4; v3 sense confirmar) | sí (100+) |
| Google | gemini-embedding-001 | ≤3072 | ~$0,15 | sí (100+) |
| Mistral | mistral-embed | 1024 | ~$0,10 | sense confirmar |

- **Anthropic no té API d'embeddings pròpia** (recomana Voyage) — confirmat. L'ADR-06 (Anthropic per defecte) aplica a la **generació**, no als embeddings.
- **Cap** exposa dropout en inferència ni σ epistèmica per embedding → **estrella impossible**.
- Requereix clau (`VOYAGE_API_KEY`/`OPENAI_API_KEY`…) **fora del repo** (secret de CI / env local); crida de xarxa a cada execució; el model fixat es pot deprecar sota nostre.

## Recomanació i pregunta per a la Trazo

**Recomanació:** stack **local** (`torch` CPU pin + `sentence-transformers` + `intfloat/multilingual-e5-small`), com a extra opcional del paquet `packages/geo-rag` (p. ex. `pip install -e ".[embeddings]"`), amb versions fixades i els embeddings base commitejats. L'API queda com a *baseline* de comparació si mai volem contrastar qualitat.

**Preguntes per a tu, Trazo:**
1. Hi ha cap objecció a afegir `torch` (CPU) + `sentence-transformers` a la `.venv` del repo (~600 MB–1 GB en disc)? Prefereixes venv/entorn separat per a l'experiment?
2. Política de **fixat de versions** i cau de models (commitejar l'artefacte d'embeddings vs regenerar-lo en CI amb pesos cachejats)?
3. El nou job de CI de `geo-rag` hauria de **descarregar pesos** (xarxa a CI) o córrer sobre l'artefacte d'embeddings **commitejat** (offline pur)? La segona encaixa millor amb el repo.

## Resolució (2026-07-01)

**Trazo (IT) tria LOCAL i implementa l'infra.** Acord de jurisdicció perquè no ens trepitgem (arbre de git compartit):

- **Trazo → infra (un PR):** instal·la l'stack local a la `.venv` del repo (`torch` CPU + `sentence-transformers`), afegeix l'extra opcional `[embeddings]` a `packages/geo-rag/pyproject.toml` amb **versions fixades** (inclou la **revisió HF** del model), i fixa la política de CI (veure resposta 3).
- **Talaia → experiment (un PR, sobre l'stack ja disponible):** Fase 0b — descripcions NL per muni + generació d'embeddings a DuckDB + cerca semàntica; i més endavant la rutina **MC-Dropout** de l'estrella.

**Respostes de Talaia (consumidora de l'stack) a les 3 preguntes:**
1. **Mateixa `.venv`**, com a **extra opcional** `[embeddings]` — no forçat: qui només corre el substrat/tests de 0a no ha de baixar `torch`.
2. **Sí a fixar versions:** `torch`, `sentence-transformers` i la **revisió** del model (commit HF). Lockfile o extras fixats.
3. **CI sobre l'artefacte d'embeddings COMMITEJAT** (offline pur): el job `geo-rag` **no** baixa `torch` ni pesos; la generació d'embeddings és un pas a part (manual/opcional) que produeix un artefacte petit i determinista (31 × 384 floats). Manté el CI ràpid i sense xarxa. *(Mecanisme final: decisió de Trazo.)*

**Model:** `intfloat/multilingual-e5-small` per defecte, llevat que la Trazo prefereixi una altra revisió/model.

## Fonts (verificat 2026-07-01)

- sentence-transformers (PyPI + pyproject) · torch (PyPI, wheel cp312 win_amd64 123 MB) · pytorch.org/whl/cpu · pip long-paths
- Models: HF `intfloat/multilingual-e5-{small,base,large}` (+ arXiv:2402.05672) · `BAAI/bge-m3` · `projecte-aina/roberta-base-ca-cased-sts` · `BSC-LT/roberta-base-ca`
- APIs: Claude/Anthropic docs «Embeddings» (no first-party; recomana Voyage) · Voyage pricing · OpenAI / Cohere / Google / Mistral pricing
